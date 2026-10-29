#Requires -Version 5.1
<#
.SYNOPSIS
Обгортка Gemini (наряд М.2), сторона власника: бандл із теки обміну -> пуш `gemini/<наряд>` -> рядок диспетчерові.

.DESCRIPTION
Задача планувальника під власником; після одноразового встановлення читає перевірену версію з active.txt.
Усе в теці обміну пише `gemini` — це недовірені байти: звідти лише читаються файли, нічого не запускається.
  1. Стан `<id>.json` — лише коди й числа; наряд, модель і спробу звіряє з позначкою черги на GitHub, тож назву
     гілки задає диспетчер, а не агент.
  2. Бандл копіюється у власну теку, `git bundle verify`, рівно одна гілка `refs/heads/gemini/<наряд>` із заявленим
     SHA, `git fetch` у карантинне посилання голого клону власника: без checkout, без хуків, без `safe.directory`.
  3. Пуш лише `gemini/<наряд>`, лише fast-forward і лише коли зміни до `main` (і в кожному коміті) без `.github/` і
     без файлів обгортки; інакше — не пушити, причина — кодом.
  4. Кінець прогону — рядок за шаблоном (`GEMINI ОБГОРТКА: ГОТОВО|ЗАБЛОКОВАНО <гілка> <SHA|КОД>`) кладеться в теку
     вихідних; звідти ж, з рядками інших скриптів власника, його доставляє `Send-Line` (`claude -p --cloud <id з
     аудит/СТАН.md>`) з повтором і станом «надіслано / спроби». Пересилається лише рядок, що повністю збігся з одним
     із шаблонів; інший файл — у карантин, диспетчеру йде лише код причини.
Налаштування — `НАЛАШТУВАННЯ.md` поруч.
#>
[CmdletBinding()]
param(
    [string]$WorkDir = (Join-Path $env:USERPROFILE 'gemini-publish'),
    [string]$OutDir = 'C:\Users\Public\gemini\out',
    [string]$RepoUrl = 'https://github.com/mightyrochy/kod-shi-data.git',
    [string]$GitExe = 'git',
    [string]$GitHubRepo = 'mightyrochy/kod-shi-data',
    [string]$UpdateRoot = 'C:\ProgramData\gemini-wrapper',
    [string]$ClaudeExe = 'claude',
    [string]$GhExe = 'gh',
    [int]$MaxFallbackAttempts = 12,
    [string]$GeminiUser = 'gemini',
    [string]$WrapperDir = 'аудит/адаптери/gemini/',
    [int]$MaxBundleMB = 512,
    [string]$OutboxDir = '',
    [int]$MaxSendAttempts = 60,
    [int]$SendRetries = 3,
    [int]$SendRetryDelaySeconds = 20,
    [int]$MaxPushRetries = 12,
    [string]$Retry = '',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'wrapper_health.ps1')
. (Join-Path $PSScriptRoot 'wrapper_update.ps1')
. (Join-Path $PSScriptRoot 'wrapper_chain.ps1')
$script:CloudAuthFailed = $false
$script:CloudUnavailable = $false

$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}\z'
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
# Умови позначки — той самий шаблон, що в queue_lanes.ps1 (публікація підвантажує лише себе).
$script:CondPattern = '^(?:p[0-9]|d20[0-9]{10}|gpu)(?:-(?:p[0-9]|d20[0-9]{10}|gpu)){0,2}$'
# Імена моделей у рядку ПУЛИ (9740): родини gemini/claude/gpt, до 6 імен — вільного тексту з pools.json (пише gemini) нема.
$script:PoolModelPattern = '^(gemini|claude|gpt)-[a-z0-9.-]{1,36}$'
# Шляхи й вміст, яких у гілці gemini/* бути не може (9739); вміст — ERE для `git log -G` по кожному коміту.
$script:SecretPathPattern = '(^|/)auth\.json$|(^|/)\.codex(/|$)|(^|/)\.config/gh(/|$)'
$script:SecretContentPattern = 'eyJ[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|refresh_token|BEGIN [A-Z ]*PRIVATE KEY'
$script:IdPattern = '^[0-9]{8}-[0-9]{6}-[0-9a-f]{12}$'
$script:ShaPattern = '^[0-9a-f]{40}$'
$script:Utf8Strict = New-Object System.Text.UTF8Encoding($false, $true)
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -ne 'Core') -or [bool](Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)

# Коди сторони gemini -> слова рядка. Інше значення — відмова, а не пересилання.
$script:RunCodes = @{
    QUOTA_ZERO = 'квота групи моделі 0 %: позначка чекає скидання, ту саму візьме та сама смуга'
    DONE = 'звіт агента: ГОТОВО'; BLOCKED = 'звіт агента: ЗАБЛОКОВАНО'
    NO_REPORT = 'агент без звіту після всіх догонок'; TIMEOUT = 'межа часу прогону'
    AGY_ERROR = 'agy закінчився з помилкою'; MODEL_INVALID = 'agy не знає моделі з позначки'
    QUOTA = 'квота моделі (429)'; AUTH = 'agy під gemini без входу'
    EFFORT_INVALID = 'codex exec не приймає зусилля з позначки'; STALL = 'Codex без нових подій довше за поріг (завислість)'
    NOT_ON_MAIN = 'коміт позначки не з main'; NO_TASK_FILE = 'нема файлу наряду на коміті позначки'
    TASK_TOO_LONG = 'наряд довший за 30 тис. знаків'; ENGINE_MISSING = 'рушія моделі нема на ноутбуці'; CRASH = 'збій обгортки gemini'
    STALE = 'PR закритий, голова змінилася або це автозвіт'; REVIEW_API = 'не вдалося звірити PR через API'
    INTERRUPTED = 'прогін перервано (вимкнення чи сон ноутбука)'
}
$script:IsolationChecks = @{
    WHOAMI = 'задача працює не під gemini'; NET_SESSION = 'gemini має права адміністратора'
    PROFILES = 'gemini бачить чужий профіль'; DRIVES = 'gemini бачить інший диск'
    ENV = 'у змінних середовища gemini є KEY/TOKEN/SECRET/PASSWORD'
}

function Write-WrapperLog([string]$Text) {
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Text
    [System.IO.File]::AppendAllText((Join-Path $WorkDir 'publish.log'), $line + "`n", $script:Utf8)
}

function Write-FileAtomic([string]$Path, [string]$Text) {
    $tmp = $Path + '.part'
    [System.IO.File]::WriteAllText($tmp, $Text, $script:Utf8)
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    Move-Item -LiteralPath $tmp -Destination $Path
}

function ConvertTo-ArgString([string[]]$Items) {
    $parts = foreach ($a in $Items) {
        if ($a -eq '') { '""'; continue }
        if ($a -notmatch '[\s"]') { $a; continue }
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.Append('"')
        $bs = 0
        foreach ($ch in $a.ToCharArray()) {
            if ($ch -eq '\') { $bs++; continue }
            if ($ch -eq '"') { [void]$sb.Append('\' * ($bs * 2 + 1)); [void]$sb.Append('"'); $bs = 0; continue }
            if ($bs -gt 0) { [void]$sb.Append('\' * $bs); $bs = 0 }
            [void]$sb.Append($ch)
        }
        [void]$sb.Append('\' * ($bs * 2))
        [void]$sb.Append('"')
        $sb.ToString()
    }
    $parts -join ' '
}

function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDirectory = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = ConvertTo-ArgString $Arguments
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8
    $psi.StandardErrorEncoding = $script:Utf8
    if ($WorkDirectory) { $psi.WorkingDirectory = $WorkDirectory }
    $psi.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $psi.EnvironmentVariables['GCM_INTERACTIVE'] = 'never'
    $psi.RedirectStandardInput = ($null -ne $StdIn)
    # .NET Framework створює StandardInput з AutoFlush: BOM пишеться вже під час Start.
    $stdinEncoding = [Console]::InputEncoding
    try {
        [Console]::InputEncoding = $script:Utf8
        $p = [System.Diagnostics.Process]::Start($psi)
    } finally { [Console]::InputEncoding = $stdinEncoding }
    $out = $p.StandardOutput.ReadToEndAsync()
    $err = $p.StandardError.ReadToEndAsync()
    if ($null -ne $StdIn) {
        # Власний UTF-8 без BOM поверх потоку: StandardInput у .NET Framework кодує кодовою сторінкою консолі.
        $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $script:Utf8)
        $w.Write($StdIn)
        $w.Close()
    }
    if (-not $p.WaitForExit([int]($TimeoutMinutes * 60000))) {
        if ($script:OnWindows) { & taskkill.exe /PID $p.Id /T /F *> $null } else { $p.Kill($true) }
        [void]$p.WaitForExit(15000)
        return [pscustomobject]@{ Code = -1; Out = ''; Err = 'межа часу' }
    }
    $p.WaitForExit()
    [pscustomobject]@{ Code = $p.ExitCode; Out = $out.Result; Err = $err.Result }
}

function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
    $all = @('--git-dir', $script:Repo, '-c', "core.hooksPath=$script:NoHooks", '-c', 'core.quotepath=false') + $GitArgs
    $r = Invoke-Native $GitExe $all $WorkDir
    if ($r.Code -ne 0 -and -not $AllowFail) { throw "git $($GitArgs -join ' ') -> $($r.Code): $($r.Err.Trim())" }
    $r
}

function Get-RefSha([string]$Ref) {
    $r = Invoke-Git @('rev-parse', '-q', '--verify', "$Ref^{commit}") -AllowFail
    if ($r.Code -ne 0) { return '' }
    $r.Out.Trim()
}

function Test-OwnerUser {
    $name = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    ($name -split '\\')[-1] -ne $GeminiUser
}

function Get-Prop($Obj, [string]$Name) {
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p) { return $null }
    $p.Value
}

function Get-Paths([string[]]$GitArgs) {
    @((Invoke-Git $GitArgs).Out -split "`0" | Where-Object { $_ })
}

# Бандл -> перевірки -> пуш. Повертає [код, число файлів]; код OK — опубліковано (чи DryRun).
function Publish-Bundle($S, [string]$Id) {
    $src = Join-Path $OutDir ($Id + '.bundle')
    if ((Get-Prop $S 'bundle') -ne ($Id + '.bundle') -or -not (Test-Path -LiteralPath $src -PathType Leaf)) { return @('BUNDLE_MISSING', 0) }
    if ((Get-Item -LiteralPath $src).Length -gt $MaxBundleMB * 1MB) { return @('BUNDLE_TOO_BIG', 0) }
    # Копія у власну теку: gemini не підмінить файл між перевіркою й fetch.
    $copy = Join-Path (Join-Path $WorkDir 'inbox') ($Id + '.bundle')
    Copy-Item -LiteralPath $src -Destination $copy -Force
    try {
        $verify = Invoke-Git @('bundle', 'verify', $copy) -AllowFail
        if ($verify.Code -ne 0) {
            Write-WrapperLog "бандл $Id — git bundle verify -> $($verify.Code): $($verify.Out.Trim()) $($verify.Err.Trim())"
            return @('BUNDLE_INVALID', 0)
        }
        $heads = @((Invoke-Git @('bundle', 'list-heads', $copy)).Out -split "`n" | Where-Object { $_.Trim() })
        $slug = [string](Get-Prop $S 'slug')
        $want = (Get-Prop $S 'head') + ' refs/heads/gemini/' + $slug
        if ($heads.Count -ne 1 -or $heads[0].Trim() -ne $want) { return @('REF_MISMATCH', 0) }
        $q = "refs/quarantine/$Id"
        [void](Invoke-Git @('-c', 'transfer.fsckObjects=true', 'fetch', '-q', '--no-tags', $copy, "+refs/heads/gemini/${slug}:$q"))
        try {
            $head = Get-RefSha $q
            $main = Get-RefSha 'refs/remotes/origin/main'
            if ($head -ne (Get-Prop $S 'head')) { return @('REF_MISMATCH', 0) }
            if ((Invoke-Git @('merge-base', '--is-ancestor', $head, $main) -AllowFail).Code -eq 0) { return @('EMPTY', 0) }
            $mb = (Invoke-Git @('merge-base', $main, $head) -AllowFail).Out.Trim()
            if (-not $mb) { return @('NO_BASE', 0) }
            $net = @(Get-Paths @('diff', '--name-only', '--no-renames', '-z', $mb, $head))
            $each = @(Get-Paths @('log', '--format=', '--name-only', '--no-renames', '--no-merges', '-z', "$main..$head"))
            $all = @($net) + @($each)
            if (@($all | Where-Object { $_ -like '.github/*' -or $_ -like '.github' }).Count -gt 0) { return @('GITHUB_DIR', $net.Count) }
            if (@($all | Where-Object { $_.StartsWith($WrapperDir) }).Count -gt 0) { return @('WRAPPER_FILES', $net.Count) }
            # Секрети (9739): токен Codex/gh лежить у профілі gemini, модель його читає — у відкритий репозиторій він не йде.
            if (@($all | Where-Object { $_ -match $script:SecretPathPattern }).Count -gt 0) { return @('SECRET', $net.Count) }
            if ((Invoke-Git @('log', '--no-merges', '--format=%H', '-G', $script:SecretContentPattern, "$main..$head")).Out.Trim()) { return @('SECRET', $net.Count) }
            $remote = Get-RefSha "refs/remotes/origin/gemini/$slug"
            if ($remote -and (Invoke-Git @('merge-base', '--is-ancestor', $remote, $head) -AllowFail).Code -ne 0) { return @('NOT_FF', $net.Count) }
            if ($DryRun) { return @('OK', $net.Count) }
            $dst = "refs/heads/gemini/$slug"
            if (-not $dst.StartsWith('refs/heads/gemini/') -or $dst.StartsWith('refs/heads/gemini-queue/')) { throw 'ціль пушу поза gemini/*' }
            $push = Invoke-Git @('push', '-q', '--no-verify', 'origin', "${head}:$dst") -AllowFail
            if ($push.Code -ne 0) { Write-WrapperLog "пуш $dst -> $($push.Code): $($push.Err.Trim())"; return @('PUSH_FAILED', $net.Count) }
            return @('OK', $net.Count)
        } finally {
            [void](Invoke-Git @('update-ref', '-d', $q) -AllowFail)
        }
    } finally {
        Remove-Item -LiteralPath $copy -Force -ErrorAction SilentlyContinue
    }
}

$script:PublishCodes = @{
    BUNDLE_MISSING = 'бандла нема'; BUNDLE_TOO_BIG = 'бандл більший за межу'; BUNDLE_INVALID = 'бандл не проходить git bundle verify'
    REF_MISMATCH = 'гілка чи SHA бандла не ті, що в стані'; EMPTY = 'нових комітів до main нема'; NO_BASE = 'нема спільної бази з main'
    SECRET = 'шлях чи вміст схожі на токен/секрет (auth.json, .codex/, .config/gh/, eyJ…, sk-, ghp_, refresh_token)'; GITHUB_DIR = 'зміни в .github/'; WRAPPER_FILES = 'зміни у файлах обгортки'; NOT_FF = 'не fast-forward до опублікованої гілки'
    PUSH_FAILED = 'пуш не вдавався годину (журнал publish.log; після входу git — gemini_publish.ps1 -Retry <id>)'
}

# Перший раз — $false і позначка; далі — $true. Тека gemini не може засипати диспетчера рядками: на позначку
# черги — по рядку на код і одна публікація, на ізоляцію чи кривий стан — один рядок на добу.
function Get-SeenPath([string]$Key) { Join-Path (Join-Path $WorkDir 'seen') ((Get-Sha256Hex $Key) + '.txt') }

function Test-Seen([string]$Key) {
    $path = Get-SeenPath $Key
    if (Test-Path -LiteralPath $path) { return $true }
    Write-FileAtomic $path $Key
    $false
}

# Число зі стану: інше значення — 0, а не виняток, що зупинив би обробку всієї теки.
function Get-Int($Obj, [string]$Name) {
    $v = [string](Get-Prop $Obj $Name)
    if ($v -match '^[0-9]{1,6}$') { return [int]$v }
    0
}

function Get-Sha256Hex([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $bytes = $sha.ComputeHash($script:Utf8.GetBytes($Text)) } finally { $sha.Dispose() }
    -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

function Get-BadLine([string]$Id, [string]$Why) {
    Write-WrapperLog "стан $Id $Why — не опубліковано"
    if (Test-Seen ('bad ' + (Get-Date -Format 'yyyyMMdd'))) { return $null }
    [pscustomobject]@{ Outbox = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/невідомо STATE_INVALID' }
}

# Один стан -> рядок диспетчерові. Усе в рядку — з переліків цього файлу, перевірених назв і чисел.
# 'RETRY' — пуш не вдався: той самий стан ще раз на наступному запуску, рядок — лише після години невдач.
function Get-Line([string]$Id) {
    $path = Join-Path $OutDir ($Id + '.json')
    if ((Get-Item -LiteralPath $path).Length -gt 65536) { return Get-BadLine $Id 'завеликий' }
    try { $s = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json }
    catch { return Get-BadLine $Id 'не читається як JSON' }
    $code = [string](Get-Prop $s 'code')
    if ((Get-Prop $s 'v') -ne 1 -or (Get-Prop $s 'id') -ne $Id) { return Get-BadLine $Id 'не за форматом' }
    if ($code -eq 'ISOLATION') {
        $check = [string](Get-Prop $s 'check')
        if (-not $script:IsolationChecks.ContainsKey($check)) { return Get-BadLine $Id 'з невідомою перевіркою ізоляції' }
        Add-HealthAlert 'ISOLATION' $check
        if (Test-Seen ('isolation ' + $check + ' ' + (Get-Date -Format 'yyyyMMdd'))) { return $null }
        Write-WrapperLog "ізоляція не пройшла перевірку ($check — $($script:IsolationChecks[$check])); прогони Gemini стоять, потрібна дія власника"
        return [pscustomobject]@{ Outbox = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/невідомо ISOLATION_FAILED' }
    }
    if (-not $script:RunCodes.ContainsKey($code)) { return Get-BadLine $Id 'з невідомим кодом' }
    $slug = [string](Get-Prop $s 'slug'); $model = [string](Get-Prop $s 'model'); $n = [string](Get-Prop $s 'n')
    $marker = [string](Get-Prop $s 'marker'); $head = [string](Get-Prop $s 'head'); $cond = [string](Get-Prop $s 'cond')
    if ($slug -notmatch $script:SlugPattern -or $slug.Contains('..') -or $model -notmatch $script:ModelPattern -or
        $n -notmatch '^[1-9][0-9]{0,2}$' -or $marker -notmatch $script:ShaPattern -or ($head -and $head -notmatch $script:ShaPattern) -or
        ($cond -and $cond -cnotmatch $script:CondPattern)) {
        return Get-BadLine $Id 'не за форматом'
    }
    # Умови позначки (пріоритет, строк, gpu) — четвертий сегмент назви; без нього назва як до смуг.
    $queue = "gemini-queue/$slug/$model/$n$(if ($cond) { '/' + $cond })"
    # Назву гілки дає лише позначка диспетчера на GitHub, а не стан з теки gemini.
    if ((Get-RefSha "refs/remotes/origin/$queue") -ne $marker) {
        return Get-BadLine $Id 'не відповідає жодній позначці черги на GitHub'
    }
    # Стан пише gemini, тож будь-який стан може бути підробленим: опублікована позначка закрита для всіх наступних,
    # а неопублікований результат займає лише свій код — підроблений ранній стан не забирає місця справжньої публікації.
    if (Test-Path -LiteralPath (Get-SeenPath "published $queue $marker")) { return $null }
    $turns = Get-Int $s 'turns'; $minutes = Get-Int $s 'minutes'; $ahead = Get-Int $s 'ahead'
    # Лише слова цього файлу: поля стану поза переліками (зокрема `models`) у рядок не потрапляють.
    if ($code -eq 'AUTH') { Add-HealthAlert 'AUTH' $(if ($model -like 'gpt-*') { 'CODEX' } else { 'AGY' }) }
    if ($code -eq 'ENGINE_MISSING') { Add-HealthAlert 'ENGINE' $(if ($model -like 'gpt-*') { 'CODEX' } else { 'AGY' }) }
    $reason = $script:RunCodes[$code]
    $quotaLeft = [string](Get-Prop $s 'quota')
    $quotaNote = $(if ($quotaLeft -match '^[0-9]{1,3}$') { "; залишок квоти групи моделі — $quotaLeft %" } else { '' })
    $run = "$reason; ходів $turns, хв $minutes; черга $queue$quotaNote"
    $branch = "gemini/$slug"
    if ($code -eq 'QUOTA_ZERO') {
        $g = [string](Get-Prop $s 'qgroup'); $r = [string](Get-Prop $s 'qreset')
        if ($g -cnotmatch '^[A-Z0-9]{1,16}$' -or ($r -and $r -notmatch '^[0-9]{1,6}$')) { return Get-BadLine $Id 'не за форматом' }
        $kod = 'QUOTA0_' + $g + $(if ($r) { '_M' + [int]$r } else { '' })
        if (Test-Seen "$queue $marker $kod") { return $null }
        Write-WrapperLog "кінець $Id — $run; група $g, скидання через $(if ($r) { "$r хв" } else { 'невідомо' })"
        return [pscustomobject]@{ Outbox = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО $branch $kod" }
    }
    if (-not (Get-Prop $s 'bundle')) {
        if (Test-Seen "$queue $marker $code") { return $null }
        $tail = $(if (Test-Path -LiteralPath (Join-Path $OutDir ($Id + '.tail.txt'))) { "; кінець виводу агента — $OutDir\$Id.tail.txt" } else { '' })
        Write-WrapperLog "кінець $Id — НЕ ЗАВЕРШЕНО $branch — $run; комітів нема$tail"
        return [pscustomobject]@{ Outbox = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО $branch $code" }
    }
    $res = Publish-Bundle $s $Id
    $pc = $res[0]; $files = $res[1]
    if ($pc -eq 'PUSH_FAILED') {
        $retry = Join-Path (Join-Path $WorkDir 'seen') ((Get-Sha256Hex "retry $queue $marker") + '.txt')
        $n = 0
        if (Test-Path -LiteralPath $retry) { $n = [int][System.IO.File]::ReadAllText($retry) }
        if ($n -lt $MaxPushRetries) {
            Write-FileAtomic $retry ([string]($n + 1))
            return 'RETRY'
        }
    }
    if ($pc -eq 'OK') {
        [void](Test-Seen "published $queue $marker")
        $what = $(if ($DryRun) { 'ПЕРЕВІРЕНО (без пушу)' } else { 'ОПУБЛІКОВАНО' })
        Write-WrapperLog "кінець $Id — $what $branch $head; комітів $ahead, файлів до main $files; без .github/ і файлів обгортки; $run"
        # ГОТОВО — лише звіт агента ГОТОВО з опублікованою головою; решта опублікованого — код прогону з _PUBLISHED.
        if ($code -eq 'DONE' -and $head) {
            Save-DraftRequest $branch $head ([string](Get-Prop $s 'actual'))
            # Квота групи (рішення диспетчера 9611): суфікс лише коли стан має групу й відсоток 0–100.
            $qg = [string](Get-Prop $s 'qgroup')
            $qs = $(if ($quotaLeft -match '^(?:100|[1-9]?[0-9])$' -and $qg -cmatch '^[A-Z0-9]{2,16}$') { " КВОТА $qg $quotaLeft" } else { '' })
            # Фактична модель (каскад за пулом може відрізнятися від моделі позначки): лише за ModelPattern.
            $am = [string](Get-Prop $s 'actual')
            $ms = $(if ($am -cmatch $script:ModelPattern) { " МОДЕЛЬ $am" } else { '' })
            return [pscustomobject]@{ Outbox = "GEMINI ОБГОРТКА: ГОТОВО $branch $head$qs$ms" }
        }
        return [pscustomobject]@{ Outbox = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО $branch $(if ($code -eq 'DONE') { 'NO_HEAD' } else { $code })_PUBLISHED" }
    }
    if (Test-Seen "$queue $marker refused $pc") { return $null }
    Write-WrapperLog "кінець $Id — НЕ ОПУБЛІКОВАНО $branch $head — $($script:PublishCodes[$pc]); $run; бандл $OutDir\$Id.bundle"
    [pscustomobject]@{ Outbox = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО $branch $pc" }
}

# Шлях до виконуваного: .NET із UseShellExecute=false дописує лише .exe, а CLI з npm — це .cmd.
function Resolve-Exe([string]$Name) {
    if (Test-Path -LiteralPath $Name -PathType Leaf) { return $Name }
    $cmds = @(Get-Command $Name -All -CommandType Application -ErrorAction SilentlyContinue)
    foreach ($ext in @('\.exe$', '\.cmd$', '')) {
        $hit = @($cmds | Where-Object { $_.Source -match $ext })
        if ($hit.Count -gt 0) { return $hit[0].Source }
    }
    throw "$Name не знайдено в PATH"
}

# Рука власника після виправленого входу git: забути стан <id> і його позначку — наступний прохід повторить публікацію.
function Reset-State([string]$Id) {
    if ($Id -notmatch $script:IdPattern) { throw "не id стану: $Id" }
    Remove-Item -LiteralPath (Join-Path (Join-Path $WorkDir 'state') ($Id + '.json')) -Force -ErrorAction SilentlyContinue
    $s = [System.IO.File]::ReadAllText((Join-Path $OutDir ($Id + '.json')), $script:Utf8) | ConvertFrom-Json
    $cond = [string](Get-Prop $s 'cond')
    $key = "gemini-queue/$(Get-Prop $s 'slug')/$(Get-Prop $s 'model')/$(Get-Prop $s 'n')$(if ($cond -cmatch $script:CondPattern) { '/' + $cond }) $(Get-Prop $s 'marker')"
    foreach ($k in @("retry $key", "$key refused PUSH_FAILED")) {
        Remove-Item -LiteralPath (Join-Path (Join-Path $WorkDir 'seen') ((Get-Sha256Hex $k) + '.txt')) -Force -ErrorAction SilentlyContinue
    }
    Write-WrapperLog "стан $Id забуто рукою власника — повтор"
}

# --- тека вихідних -------------------------------------------------------------------------------------------------
# Один файл — один рядок, UTF-8 без BOM, ім'я <yyyyMMdd-HHmmss>-<12 hex>.txt; пише будь-який скрипт власника атомарно
# (тимчасове ім'я без .txt, потім перейменування). Обгортка пересилає лише рядок, що повністю збігся з шаблоном нижче.

$script:OutboxNamePattern = '^[0-9]{8}-[0-9]{6}-[0-9a-f]{12}\.txt$'
$script:SlugCore = $script:SlugPattern -replace '^\^|\\z$', ''
$script:OutboxTemplates = @(
    '^GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_[A-Z_]{1,32}\z',
    '^GEMINI ОБГОРТКА: ОНОВЛЕНО [0-9a-f]{40} СЕКУНД [0-9]{1,12}\z',
    '^GEMINI ОБГОРТКА: ОНОВЛЕННЯ [0-9a-f]{40} UPDATE_[A-Z_]{1,32}\z',
    "\AGEMINI ОБГОРТКА: ГОТОВО (?:gemini|codex|claude)/$script:SlugCore [0-9a-f]{40}(?: КВОТА [A-Z0-9_]{2,40} (?:100|[1-9]?[0-9]))?(?: МОДЕЛЬ [a-z0-9][a-z0-9.-]{1,63})?\z"
    '\AGEMINI ОБГОРТКА: ПУЛИ V=(?:[0-9]+(?:\.[0-9]+){1,3}|-)(?: G=[A-Z0-9]{1,16}:(?:100|[1-9]?[0-9]):(?:[0-9]{1,6}|-)){0,6}(?: Q=\?)? M=(?:-|(?:gemini|claude|gpt)-[a-z0-9.-]{1,36}(?:,(?:gemini|claude|gpt)-[a-z0-9.-]{1,36}){0,5})\z'
    "\AGEMINI ОБГОРТКА: ЗАБЛОКОВАНО (?:gemini|codex|claude)/$script:SlugCore [A-Z0-9_]{2,40}\z"
    '\AGEMINI ОБГОРТКА: ТРИВОГА (?:AUTH (?:AGY|CODEX|CLAUDE|CLOUD)|ISOLATION (?:WHOAMI|NET_SESSION|PROFILES|DRIVES|ENV)|DISK FULL|ENGINE (?:AGY|CODEX|CLAUDE))\z'
    '\AGEMINI ОБГОРТКА: ВИМКНЕНО [0-9a-f]{40}\z'
    '\AСПОСТЕРІГАЧ КОМЕНТАР #[0-9]{1,12} [0-9]{1,20} (?:mightyrochy|chatgpt-codex-connector\[bot\]) (?:новий|змінено)\z'
    '\AСПОСТЕРІГАЧ CI #[0-9]{1,12} [0-9a-f]{40} (?:success|failure|cancelled|timed_out|action_required|neutral|skipped|pending)\z'
    "\AСПОСТЕРІГАЧ ПЕРЕНЕСЕНО (?<n>$script:SlugCore) codex/\k<n> [0-9a-f]{40} #[0-9]{1,12}\z"
    "\AСПОСТЕРІГАЧ НЕ ПЕРЕНЕСЕНО $script:SlugCore [A-Z0-9_]{2,40}\z"
)
$script:QuarantineCodes = @('BAD_SIZE', 'EMPTY', 'BOM', 'BAD_UTF8', 'NOT_ONE_LINE', 'BAD_CHARS', 'NO_TEMPLATE', 'UNREADABLE')

# Порожній рядок — рядок збігся з шаблоном; інакше код причини.
function Test-OutboxLine([string]$Line) {
    if ($Line.Contains('..')) { return 'NO_TEMPLATE' }
    foreach ($t in $script:OutboxTemplates) { if ($Line -cmatch $t) { return '' } }
    'NO_TEMPLATE'
}

# [рядок, код]: код порожній — файл прийнято.
function Read-OutboxFile([string]$Path) {
    try {
        $bytes = [System.IO.File]::ReadAllBytes($Path)
        if ($bytes.Length -eq 0) { return @('', 'EMPTY') }
        if ($bytes.Length -gt 1024) { return @('', 'BAD_SIZE') }
        if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) { return @('', 'BOM') }
        try { $text = $script:Utf8Strict.GetString($bytes) } catch { return @('', 'BAD_UTF8') }
    } catch { return @('', 'UNREADABLE') }
    if ($text.EndsWith("`r`n")) { $text = $text.Substring(0, $text.Length - 2) } elseif ($text.EndsWith("`n")) { $text = $text.Substring(0, $text.Length - 1) }
    if ($text.Contains("`n") -or $text.Contains("`r")) { return @('', 'NOT_ONE_LINE') }
    if ($text -cmatch '[\x00-\x1f\x7f]') { return @('', 'BAD_CHARS') }
    $code = Test-OutboxLine $text
    if ($code) { return @('', $code) }
    @($text, '')
}

# Файл вихідних із заданим іменем: вдруге те саме ім'я не пишеться (стан прогону має ім'я = свій id).
function Add-OutboxLine([string]$Name, [string]$Line) {
    if ($Name -cnotmatch $script:OutboxNamePattern) { throw "ім'я файлу вихідних не за форматом: $Name" }
    $path = Join-Path $OutboxDir $Name
    if ((Test-Path -LiteralPath $path) -or (Test-Path -LiteralPath (Join-Path (Join-Path $OutboxDir 'done') $Name))) { return }
    Write-FileAtomic $path ($Line + "`n")
}

function Move-Outbox([string]$Name, [string]$Sub) {
    $dir = Join-Path $OutboxDir $Sub
    [void](New-Item -ItemType Directory -Force -Path $dir)
    Move-Item -LiteralPath (Join-Path $OutboxDir $Name) -Destination (Join-Path $dir $Name) -Force
}

# pools.json від gemini (версія agy, групи квоти, назви моделей) -> рядок ПУЛИ у вихідні. Недовірений файл: у рядок
# іде лише те, що збіглося з шаблонами; не частіше за раз на 3 години й лише коли рядок змінився.
function Add-PoolsLine {
    $path = Join-Path $OutDir 'pools.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return }
    if ((Get-Item -LiteralPath $path).Length -gt 8192) { Write-WrapperLog 'pools.json завеликий — пропущено'; return }
    try { $p = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json }
    catch { Write-WrapperLog 'pools.json не читається як JSON — пропущено'; return }
    $ver = [string](Get-Prop $p 'agy')
    $parts = @('V=' + $(if ($ver -cmatch '^[0-9]+(\.[0-9]+){1,3}$') { $ver } else { '-' }))
    foreach ($g in @(@(Get-Prop $p 'groups') | Where-Object { $null -ne $_ } | Select-Object -First 6)) {
        $c = [string](Get-Prop $g 'g'); $l = [string](Get-Prop $g 'left'); $r = [string](Get-Prop $g 'reset')
        if ($c -cmatch '^[A-Z0-9]{1,16}$' -and $l -cmatch '^(?:100|[1-9]?[0-9])$') {
            $parts += "G=${c}:${l}:" + $(if ($r -cmatch '^[0-9]{1,6}$') { $r } else { '-' })
        }
    }
    $models = @(@(Get-Prop $p 'models') | Where-Object { $null -ne $_ } | ForEach-Object { [string]$_ } | Where-Object { $_ -cmatch $script:PoolModelPattern } | Select-Object -First 6)
    if ((Get-Prop $p 'unknown') -eq $true) { $parts += 'Q=?' }
    $parts += 'M=' + $(if ($models.Count -gt 0) { $models -join ',' } else { '-' })
    $line = 'GEMINI ОБГОРТКА: ПУЛИ ' + ($parts -join ' ')
    if ($line.Length -gt 300) { Write-WrapperLog 'рядок ПУЛИ довший за 300 знаків — пропущено'; return }
    if ((Test-OutboxLine $line) -ne '') { Write-WrapperLog 'рядок ПУЛИ не збігся з шаблоном — пропущено'; return }
    $last = Join-Path $WorkDir 'pools_last.txt'
    if ((Test-Path -LiteralPath $last) -and [System.IO.File]::ReadAllText($last, $script:Utf8) -eq $line) { return }
    $now = Get-Date
    if (Test-Seen ('pools ' + $now.ToString('yyyyMMdd') + '-' + [int][Math]::Floor($now.Hour / 3))) { return }
    Write-FileAtomic $last $line
    Add-OutboxLine ('{0:yyyyMMdd-HHmmss}-{1}.txt' -f $now, (Get-Sha256Hex $line).Substring(0, 12)) $line
}

# Файли вихідних -> стан <o-id>.json: рядок на відправлення або карантин із повідомленням лише кодом (не більше 3 на добу).
function Receive-Outbox {
    foreach ($f in @(Get-ChildItem -LiteralPath $OutboxDir -File -ErrorAction SilentlyContinue | Sort-Object Name)) {
        if ($f.Name -cnotmatch $script:OutboxNamePattern) { continue }
        $statePath = Join-Path (Join-Path $WorkDir 'state') ('o-' + $f.BaseName + '.json')
        if (Test-Path -LiteralPath $statePath) { Move-Outbox $f.Name 'done'; continue }
        $r = Read-OutboxFile $f.FullName
        if ($r[1]) {
            $notice = ''
            foreach ($i in 1..3) {
                if (-not (Test-Seen ('quarantine ' + (Get-Date -Format 'yyyyMMdd') + " $i"))) {
                    $notice = "GEMINI ОБГОРТКА: КАРАНТИН ВИХІДНИХ $($f.BaseName) $($r[1]) — рядок не переслано (текст — лише в теці quarantine власника)."
                    break
                }
            }
            Write-WrapperLog "вихідні $($f.Name): карантин $($r[1])"
            Write-FileAtomic $statePath (([ordered]@{ line = $notice; sent = ($notice -eq ''); attempts = 0 }) | ConvertTo-Json -Compress)
            Move-Outbox $f.Name 'quarantine'
            continue
        }
        Write-WrapperLog "вихідні $($f.Name): $($r[0])"
        Write-FileAtomic $statePath (([ordered]@{ line = $r[0]; sent = $false; attempts = 0 }) | ConvertTo-Json -Compress)
        Move-Outbox $f.Name 'done'
    }
    # Прийняті файли старші за 30 діб — зайві; карантин лишається до руки власника.
    foreach ($old in @(Get-ChildItem -LiteralPath (Join-Path $OutboxDir 'done') -File -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-30) })) {
        Remove-Item -LiteralPath $old.FullName -Force -ErrorAction SilentlyContinue
    }
}

function Get-DispatcherId {
    $r = Invoke-Git @('cat-file', 'blob', 'refs/remotes/origin/main:аудит/СТАН.md') -AllowFail
    if ($r.Code -ne 0) { return '' }
    foreach ($line in ($r.Out -split "`n")) {
        if ($line -match '^\|\s*диспетчер\s*\|\s*(session_[A-Za-z0-9]+)') { return $Matches[1] }
    }
    ''
}

# Коди ЗАБЛОКОВАНО, після яких диспетчерові нічого робити: обгортка бере ту саму позначку сама чи позначка вже даремна.
# Кожен інший код (зокрема невідомий) будить — безпечне за замовчуванням. Доказ — у тілі коміту «тихі пробудження».
$script:QuietBlockedCodes = '^(?:QUOTA0_[A-Z0-9]{1,16}(?:_M[0-9]{1,6})?|STALE|REVIEW_API)$'
$script:LocalLinesCap = 64

function Test-DispatcherAction([string]$Line) {
    <# Диспетчер прокидається лише за станом, що чекає його дії; решта йде зведенням при наступному пробудженні. #>
    if ($Line -cmatch '^GEMINI ОБГОРТКА: ЗАБЛОКОВАНО \S+ (\S+)$') { return $Matches[1] -cnotmatch $script:QuietBlockedCodes }
    if ($Line -cmatch '^GEMINI ОБГОРТКА: (?:ЗАБЛОКОВАНО|ТРИВОГА|ЛАНЦЮГ) ') { return $true }
    if ($Line -cmatch '^GEMINI ОБГОРТКА: ГОТОВО (?:gemini|claude|codex)/(?:автоперевірка-|перевірка-|pachka-|автоживий-|Е1-нічний-живий-)') { return $true }
    $false
}

function Get-LocalLines {
    $path = Join-Path $WorkDir 'local-lines.json'
    if (-not (Test-Path -LiteralPath $path)) { return @() }
    @(ConvertFrom-Json ([IO.File]::ReadAllText($path, $script:Utf8)))
}

function Save-LocalLine([string]$Line) {
    <# Рядок лишається у журналі та стані для #1856 без мережевої доставки; кожна подія — окремий запис (для зведення). #>
    Write-WrapperLog "локально, без пробудження: $Line"
    $lines = @(Get-LocalLines | Select-Object -Last ($script:LocalLinesCap - 1))
    Write-FileAtomic (Join-Path $WorkDir 'local-lines.json') (ConvertTo-Json -InputObject @($lines + @(@{utc=[datetime]::UtcNow.ToString('o');line=$Line;delivered=$false})) -Compress)
}

function Get-DigestText {
    <# Зведення накопичених недоставлених локальних рядків: кількість і самі рядки обгортки, без тексту агента. #>
    $pending = @(Get-LocalLines | Where-Object { (Get-Prop $_ 'delivered') -ne $true })
    if ($pending.Count -eq 0) { return '' }
    "ЗВЕДЕННЯ БЕЗ ПРОБУДЖЕННЯ: $($pending.Count)`n" + (($pending | ForEach-Object { [string]$_.line }) -join "`n")
}

function Set-DigestDelivered {
    <# Після підтвердженої доставки листа зі зведенням накопичене позначається доставленим. #>
    $all = @(Get-LocalLines)
    if (@($all | Where-Object { (Get-Prop $_ 'delivered') -ne $true }).Count -eq 0) { return }
    $done = foreach ($e in $all) { @{utc=[string]$e.utc;line=[string]$e.line;delivered=$true} }
    Write-FileAtomic (Join-Path $WorkDir 'local-lines.json') (ConvertTo-Json -InputObject @($done) -Compress)
}

function Add-DigestToLine([string]$Line) {
    $digest = Get-DigestText
    if ($digest) { $Line + "`n" + $digest } else { $Line }
}

function Send-Line([string]$Line) {
    if (-not (Test-DispatcherAction $Line)) { Save-LocalLine $Line; return $true }
    if ($DryRun) { Write-WrapperLog "DryRun, рядок не надіслано: $Line"; return $true }
    $sid = Get-DispatcherId
    if (-not $sid) { Write-WrapperLog 'нема адреси диспетчера в аудит/СТАН.md'; return $false }
    # Рядок — через stdin: `claude` буває `.cmd`, і тоді аргумент розбирав би cmd.exe.
    $r = Invoke-Native (Resolve-Exe $ClaudeExe) @('-p', '--cloud', $sid, '--output-format', 'json') $WorkDir 3 (Add-DigestToLine $Line)
    $ok = $false
    try { $ack = (($r.Out -split "`n" | Where-Object { $_.Trim().StartsWith('{') }) | Select-Object -Last 1 | ConvertFrom-Json).ok; $ok = $r.Code -eq 0 -and $ack -is [bool] -and $ack -eq $true }
    catch { Write-WrapperLog "відповідь claude не JSON: $($_.Exception.Message)" }
    if (-not $ok -and (($r.Out + $r.Err) -match '\b401\b|authentication_error|[Nn]ot logged in')) {
        $script:CloudAuthFailed = $true
        Add-HealthAlert 'AUTH' 'CLOUD'
    }
    if (-not $ok) { Write-WrapperLog "claude --cloud $sid -> $($r.Code): $($r.Out.Trim()) $($r.Err.Trim())" }
    $ok
}

# До $SendRetries спроб за прохід (пауза між ними), не більше, ніж лишилось до $MaxSendAttempts; Tries іде в «спроби».
function Send-LineRetry([string]$Line, [int]$Done) {
    $tries = 0
    while ($true) {
        $tries++
        if (Send-Line $Line) { return [pscustomobject]@{ Ok = $true; Tries = $tries } }
        if ($script:CloudAuthFailed -or $tries -ge $SendRetries -or ($Done + $tries) -ge $MaxSendAttempts) { return [pscustomobject]@{ Ok = $false; Tries = $tries } }
        if (-not $DryRun -and $SendRetryDelaySeconds -gt 0) { Start-Sleep -Seconds $SendRetryDelaySeconds }
    }
}

function Receive-HealthAlerts {
    <# Недовірені тривоги Gemini: лише пара з переліку; загальний формат файлів не розширюється. #>
    $dir = Join-Path $OutDir 'alerts'
    foreach ($f in @(Get-ChildItem -LiteralPath $dir -Filter '*.txt' -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -cmatch $script:OutboxNamePattern -and -not (Test-Path -LiteralPath (Get-SeenPath ('health-import ' + $_.Name))) } | Select-Object -First 64)) {
        if ($f.Name -cnotmatch $script:OutboxNamePattern) { continue }
        $r = Read-OutboxFile $f.FullName
        if (-not $r[1] -and (Test-HealthAlert $r[0])) {
            $parts = $r[0] -split ' '
            Add-HealthAlert $parts[-2] $parts[-1]
        } else { Write-WrapperLog 'тривогу Gemini відкинуто за форматом' }
        Write-FileAtomic (Get-SeenPath ('health-import ' + $f.Name)) '1'
    }
}

function Send-Fallback([string]$Line) {
    if (-not (Test-DispatcherAction $Line)) { Save-LocalLine $Line; return $true }
    <# Той самий рядок у #1690 через stdin JSON; ні оболонки, ні тексту агента в аргументах. #>
    if ($DryRun) { return $true }
    $body = ([ordered]@{ body = (Add-DigestToLine $Line) }) | ConvertTo-Json -Compress
    try {
        $r = Invoke-Native (Resolve-Exe $GhExe) @('api', '-X', 'POST', 'repos/mightyrochy/kod-shi-data/issues/1690/comments', '--input', '-') $WorkDir 1 $body
        $id = 0L
        $ok = $r.Code -eq 0 -and [long]::TryParse([string](Get-Prop ($r.Out | ConvertFrom-Json) 'id'), [ref]$id) -and $id -gt 0
        if (-not $ok) { Write-WrapperLog 'запасний канал gh: немає підтвердження id' }
        return $ok
    } catch { Write-WrapperLog 'запасний канал gh: збій'; return $false }
}

function Send-Pending([System.IO.FileInfo]$File) {
    <# Стан доставки збережено перед мережею; рядок лишається після вичерпання обох бюджетів. #>
    $st = [System.IO.File]::ReadAllText($File.FullName, $script:Utf8) | ConvertFrom-Json
    if ($st.sent -or (Get-Prop $st 'exhausted') -eq $true) { return }
    if (-not (Test-DispatcherAction ([string]$st.line))) {
        Save-LocalLine ([string]$st.line)
        Write-FileAtomic $File.FullName ((@{line=[string]$st.line;sent=$true;attempts=[int]$st.attempts;channel='local'}) | ConvertTo-Json -Compress)
        return
    }
    $first = [string](Get-Prop $st 'first_failure_utc')
    if (-not $first) { $first = $File.CreationTimeUtc.ToString('o') }
    $new = [ordered]@{ line = [string]$st.line; sent = $false; attempts = [int]$st.attempts
        first_failure_utc = $first; fallback_attempts = [int](Get-Prop $st 'fallback_attempts'); channel = ''; exhausted = $false; cloud_auth = ((Get-Prop $st 'cloud_auth') -eq $true) }
    Write-FileAtomic $File.FullName ($new | ConvertTo-Json -Compress)
    if (-not $script:CloudAuthFailed -and -not $script:CloudUnavailable -and $new.attempts -lt $MaxSendAttempts) {
        try { $res = Send-LineRetry $new.line $new.attempts }
        catch { Write-WrapperLog 'канал claude: збій'; $res = [pscustomobject]@{ Ok = $false; Tries = 1 } }
        $new.attempts += $res.Tries
        $new.sent = $res.Ok
        if ($res.Ok) { $new.channel = 'claude' } else { $script:CloudUnavailable = $true }
    }
    $new.cloud_auth = $new.cloud_auth -or $script:CloudAuthFailed
    $age = ([DateTimeOffset]::UtcNow - [DateTimeOffset]::Parse($first)).TotalMinutes
    if (-not $new.sent -and ($new.cloud_auth -or $age -ge 10) -and $new.fallback_attempts -lt $MaxFallbackAttempts) {
        $new.fallback_attempts++
        if (Send-Fallback $new.line) { $new.sent = $true; $new.channel = 'gh' }
    }
    if ($new.sent) { Set-DigestDelivered }
    $new.exhausted = -not $new.sent -and ($new.cloud_auth -or $new.attempts -ge $MaxSendAttempts) -and $new.fallback_attempts -ge $MaxFallbackAttempts
    if ($new.exhausted) { Write-WrapperLog "спроби доставки вичерпано: $($File.Name); рядок збережено у стані" }
    Write-FileAtomic $File.FullName ($new | ConvertTo-Json -Compress)
}

function Write-DeliveryStatus {
    <# Підсумок доставки для читача стану ноутбука, без вмісту рядків. #>
    $pending = 0; $exhausted = 0
    foreach ($f in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File)) {
        $s = [System.IO.File]::ReadAllText($f.FullName, $script:Utf8) | ConvertFrom-Json
        if (-not $s.sent) { $pending++; if ((Get-Prop $s 'exhausted') -eq $true) { $exhausted++ } }
    }
    Write-FileAtomic (Join-Path $WorkDir 'delivery.json') (([ordered]@{ read_utc = [datetime]::UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'"); pending = $pending; exhausted = $exhausted }) | ConvertTo-Json -Compress)
}

function Main {
    if (-not $OutboxDir) { $script:OutboxDir = Join-Path (Split-Path -Parent $WorkDir) 'gemini-outbox' }
    foreach ($d in @($WorkDir, (Join-Path $WorkDir 'state'), (Join-Path $WorkDir 'inbox'), (Join-Path $WorkDir 'seen'), $OutboxDir)) { [void](New-Item -ItemType Directory -Force -Path $d) }
    if (-not (Test-OwnerUser)) { Write-WrapperLog "запуск під $GeminiUser — відмова"; return 1 }
    $script:HealthAlertDir = $OutboxDir
    $script:Repo = Join-Path $WorkDir 'repo.git'
    $script:NoHooks = Join-Path ([System.IO.Path]::GetTempPath()) ('no-hooks-' + [guid]::NewGuid().ToString('N'))
    $lockFile = $null
    try { $lockFile = [System.IO.File]::Open((Join-Path $WorkDir 'lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { return 0 }
    try {
        if (-not (Test-Path -LiteralPath (Join-Path $script:Repo 'HEAD'))) {
            [void](Invoke-Native $GitExe @('init', '-q', '--bare', $script:Repo) $WorkDir)
            [void](Invoke-Git @('config', 'remote.origin.url', $RepoUrl))
        }
        [void](Invoke-Git @('fetch', '-q', '--prune', '--no-tags', 'origin',
                '+refs/heads/main:refs/remotes/origin/main',
                '+refs/heads/gemini/*:refs/remotes/origin/gemini/*',
                '+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
        if (Test-Path -LiteralPath (Join-Path $UpdateRoot 'selfupdate.ready')) { Invoke-WrapperUpdate $UpdateRoot }
        Invoke-WrapperChain
        if ($Retry) { Reset-State $Retry }
        $files = @(Get-ChildItem -LiteralPath $OutDir -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name)
        foreach ($f in $files) {
            $id = $f.BaseName
            if ($id -notmatch $script:IdPattern) { continue }
            $statePath = Join-Path (Join-Path $WorkDir 'state') ($id + '.json')
            if (Test-Path -LiteralPath $statePath) { continue }
            try { $line = Get-Line $id }
            catch { Write-WrapperLog "стан ${id}: $($_.Exception.Message)"; $line = Get-BadLine $id 'не обробився' }
            if ($line -is [string] -and $line -eq 'RETRY') { continue }
            if ($line -isnot [string] -and $null -ne $line) {
                # Кінець прогону: рядок — у теку вихідних під id стану; доставка — з неї, як для рядків інших скриптів.
                Add-OutboxLine ($id + '.txt') $line.Outbox
                Write-FileAtomic $statePath (([ordered]@{ line = ''; sent = $true; attempts = 0; outbox = ($id + '.txt') }) | ConvertTo-Json -Compress)
                continue
            }
            if ($null -eq $line) {
                Write-WrapperLog "стан $id — повтор, рядка нема"
                Write-FileAtomic $statePath (([ordered]@{ line = ''; sent = $true; attempts = 0 }) | ConvertTo-Json -Compress)
                continue
            }
            Write-WrapperLog $line
            Write-FileAtomic $statePath (([ordered]@{ line = $line; sent = $false; attempts = 0 }) | ConvertTo-Json -Compress)
        }
        Add-PoolsLine
        Receive-HealthAlerts
        Receive-Outbox
        $processed = @{}
        # Другий прохід підхоплює тривогу CLOUD, створену під час першої спроби доставки.
        foreach ($round in 1..2) {
            foreach ($sf in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File | Sort-Object Name)) {
                if ($processed.ContainsKey($sf.Name)) { continue }
                Send-Pending $sf
                $processed[$sf.Name] = $true
            }
            Receive-Outbox
        }
        Write-DeliveryStatus
        0
    } catch {
        Write-WrapperLog "збій: $($_.Exception.Message)"
        1
    } finally {
        $lockFile.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Main) }
