#Requires -Version 5.1
<#
.SYNOPSIS
Обгортка Gemini (наряд М.2), сторона власника: бандл із теки обміну -> пуш `gemini/<наряд>` -> рядок диспетчерові.

.DESCRIPTION
Задача планувальника під власником; запускається з копії поза клоном, яку власник оновлює рукою.
Усе в теці обміну пише `gemini` — це недовірені байти: звідти лише читаються файли, нічого не запускається.
  1. Стан `<id>.json` — лише коди й числа; наряд, модель і спробу звіряє з позначкою черги на GitHub, тож назву
     гілки задає диспетчер, а не агент.
  2. Бандл копіюється у власну теку, `git bundle verify`, рівно одна гілка `refs/heads/gemini/<наряд>` із заявленим
     SHA, `git fetch` у карантинне посилання голого клону власника: без checkout, без хуків, без `safe.directory`.
  3. Пуш лише `gemini/<наряд>`, лише fast-forward і лише коли зміни до `main` (і в кожному коміті) без `.github/` і
     без файлів обгортки; інакше — не пушити, причина — кодом.
  4. Рядок диспетчерові (`claude -p <рядок> --cloud <id з аудит/СТАН.md>`) — лише обчислене тут, жодного тексту агента.
Налаштування — `НАЛАШТУВАННЯ.md` поруч.
#>
[CmdletBinding()]
param(
    [string]$WorkDir = (Join-Path $env:USERPROFILE 'gemini-publish'),
    [string]$OutDir = 'C:\Users\Public\gemini\out',
    [string]$RepoUrl = 'https://github.com/mightyrochy/kod-shi-data.git',
    [string]$GitExe = 'git',
    [string]$ClaudeExe = 'claude',
    [string]$GeminiUser = 'gemini',
    [string]$WrapperDir = 'аудит/адаптери/gemini/',
    [int]$MaxBundleMB = 512,
    [int]$MaxSendAttempts = 12,
    [int]$MaxPushRetries = 12,
    [string]$Retry = '',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}$'
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
$script:IdPattern = '^[0-9]{8}-[0-9]{6}-[0-9a-f]{12}$'
$script:ShaPattern = '^[0-9a-f]{40}$'
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -ne 'Core') -or [bool](Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)

# Коди сторони gemini -> слова рядка. Інше значення — відмова, а не пересилання.
$script:RunCodes = @{
    DONE = 'звіт агента: ГОТОВО'; BLOCKED = 'звіт агента: ЗАБЛОКОВАНО'
    NO_REPORT = 'агент без звіту після всіх догонок'; TIMEOUT = 'межа часу прогону'
    AGY_ERROR = 'agy закінчився з помилкою'; MODEL_INVALID = 'agy не знає моделі з позначки'
    QUOTA = 'квота моделі (429)'; AUTH = 'agy під gemini без входу'
    NOT_ON_MAIN = 'коміт позначки не з main'; NO_TASK_FILE = 'нема файлу наряду на коміті позначки'
    TASK_TOO_LONG = 'наряд довший за 30 тис. знаків'; CRASH = 'збій обгортки gemini'
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
    $p = [System.Diagnostics.Process]::Start($psi)
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
        if ((Invoke-Git @('bundle', 'verify', '-q', $copy) -AllowFail).Code -ne 0) { return @('BUNDLE_INVALID', 0) }
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
    GITHUB_DIR = 'зміни в .github/'; WRAPPER_FILES = 'зміни у файлах обгортки'; NOT_FF = 'не fast-forward до опублікованої гілки'
    PUSH_FAILED = 'пуш не вдавався годину (журнал publish.log; після входу git — gemini_publish.ps1 -Retry <id>)'
}

# Перший раз — $false і позначка; далі — $true. Тека gemini не може засипати диспетчера рядками: на позначку
# черги — один рядок і одна публікація, на ізоляцію чи кривий стан — один рядок на добу.
function Test-Seen([string]$Key) {
    $path = Join-Path (Join-Path $WorkDir 'seen') ((Get-Sha256Hex $Key) + '.txt')
    if (Test-Path -LiteralPath $path) { return $true }
    Write-FileAtomic $path $Key
    $false
}

function Get-Sha256Hex([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $bytes = $sha.ComputeHash($script:Utf8.GetBytes($Text)) } finally { $sha.Dispose() }
    -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

function Get-BadLine([string]$Id, [string]$Why) {
    if (Test-Seen ('bad ' + (Get-Date -Format 'yyyyMMdd'))) { return $null }
    "GEMINI ОБГОРТКА: стан $Id $Why — не опубліковано (далі такі — лише в журналі до завтра)."
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
        if (Test-Seen ('isolation ' + $check + ' ' + (Get-Date -Format 'yyyyMMdd'))) { return $null }
        return "GEMINI ОБГОРТКА: ізоляція не пройшла перевірку ($check — $($script:IsolationChecks[$check])); прогони Gemini стоять, потрібна дія власника."
    }
    if (-not $script:RunCodes.ContainsKey($code)) { return Get-BadLine $Id 'з невідомим кодом' }
    $slug = [string](Get-Prop $s 'slug'); $model = [string](Get-Prop $s 'model'); $n = [string](Get-Prop $s 'n')
    $marker = [string](Get-Prop $s 'marker'); $head = [string](Get-Prop $s 'head')
    if ($slug -notmatch $script:SlugPattern -or $slug.Contains('..') -or $model -notmatch $script:ModelPattern -or
        $n -notmatch '^[1-9][0-9]{0,2}$' -or $marker -notmatch $script:ShaPattern -or ($head -and $head -notmatch $script:ShaPattern)) {
        return Get-BadLine $Id 'не за форматом'
    }
    $queue = "gemini-queue/$slug/$model/$n"
    # Назву гілки дає лише позначка диспетчера на GitHub, а не стан з теки gemini.
    if ((Get-RefSha "refs/remotes/origin/$queue") -ne $marker) {
        return Get-BadLine $Id 'не відповідає жодній позначці черги на GitHub'
    }
    if (Test-Seen ("$queue $marker")) { return $null }
    $turns = [int](Get-Prop $s 'turns'); $minutes = [int](Get-Prop $s 'minutes'); $ahead = [int](Get-Prop $s 'ahead')
    $reason = $script:RunCodes[$code]
    if ($code -eq 'MODEL_INVALID') {
        $models = @(@(Get-Prop $s 'models') | ForEach-Object { [string]$_ } | Where-Object { $_ -cmatch $script:ModelPattern } | Select-Object -First 20)
        if ($models.Count -gt 0) { $reason += ' (agy models: ' + ($models -join ', ') + ')' }
    }
    $run = "$reason; ходів $turns, хв $minutes; черга $queue"
    if (-not (Get-Prop $s 'bundle')) {
        $tail = $(if (Test-Path -LiteralPath (Join-Path $OutDir ($Id + '.tail.txt'))) { "; кінець виводу агента — $OutDir\$Id.tail.txt" } else { '' })
        return "GEMINI ОБГОРТКА: НЕ ЗАВЕРШЕНО gemini/$slug — $run; комітів нема$tail."
    }
    $res = Publish-Bundle $s $Id
    $pc = $res[0]; $files = $res[1]
    if ($pc -eq 'PUSH_FAILED') {
        $retry = Join-Path (Join-Path $WorkDir 'seen') ((Get-Sha256Hex "retry $queue $marker") + '.txt')
        $n = 0
        if (Test-Path -LiteralPath $retry) { $n = [int][System.IO.File]::ReadAllText($retry) }
        if ($n -lt $MaxPushRetries) {
            Write-FileAtomic $retry ([string]($n + 1))
            Remove-Item -LiteralPath (Join-Path (Join-Path $WorkDir 'seen') ((Get-Sha256Hex "$queue $marker") + '.txt')) -Force
            return 'RETRY'
        }
    }
    if ($pc -eq 'OK') {
        $what = $(if ($DryRun) { 'ПЕРЕВІРЕНО (без пушу)' } else { 'ОПУБЛІКОВАНО' })
        return "GEMINI ОБГОРТКА: $what gemini/$slug $head; комітів $ahead, файлів до main $files; без .github/ і файлів обгортки; $run."
    }
    "GEMINI ОБГОРТКА: НЕ ОПУБЛІКОВАНО gemini/$slug $head — $($script:PublishCodes[$pc]); $run; бандл $OutDir\$Id.bundle."
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
    $key = "gemini-queue/$(Get-Prop $s 'slug')/$(Get-Prop $s 'model')/$(Get-Prop $s 'n') $(Get-Prop $s 'marker')"
    foreach ($k in @($key, "retry $key")) {
        Remove-Item -LiteralPath (Join-Path (Join-Path $WorkDir 'seen') ((Get-Sha256Hex $k) + '.txt')) -Force -ErrorAction SilentlyContinue
    }
    Write-WrapperLog "стан $Id забуто рукою власника — повтор"
}

function Get-DispatcherId {
    $r = Invoke-Git @('cat-file', 'blob', 'refs/remotes/origin/main:аудит/СТАН.md') -AllowFail
    if ($r.Code -ne 0) { return '' }
    foreach ($line in ($r.Out -split "`n")) {
        if ($line -match '^\|\s*диспетчер\s*\|\s*(session_[A-Za-z0-9]+)') { return $Matches[1] }
    }
    ''
}

function Send-Line([string]$Line) {
    if ($DryRun) { Write-WrapperLog "DryRun, рядок не надіслано: $Line"; return $true }
    $sid = Get-DispatcherId
    if (-not $sid) { Write-WrapperLog 'нема адреси диспетчера в аудит/СТАН.md'; return $false }
    # Рядок — через stdin: `claude` буває `.cmd`, і тоді аргумент розбирав би cmd.exe.
    $r = Invoke-Native (Resolve-Exe $ClaudeExe) @('-p', '--cloud', $sid, '--output-format', 'json') $WorkDir 3 $Line
    $ok = $false
    try { $ok = [bool]((($r.Out -split "`n" | Where-Object { $_.Trim().StartsWith('{') }) | Select-Object -Last 1 | ConvertFrom-Json).ok) }
    catch { Write-WrapperLog "відповідь claude не JSON: $($_.Exception.Message)" }
    if (-not $ok) { Write-WrapperLog "claude --cloud $sid -> $($r.Code): $($r.Out.Trim()) $($r.Err.Trim())" }
    $ok
}

function Main {
    foreach ($d in @($WorkDir, (Join-Path $WorkDir 'state'), (Join-Path $WorkDir 'inbox'), (Join-Path $WorkDir 'seen'))) { [void](New-Item -ItemType Directory -Force -Path $d) }
    if (-not (Test-OwnerUser)) { Write-WrapperLog "запуск під $GeminiUser — відмова"; return 1 }
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
        if ($Retry) { Reset-State $Retry }
        $files = @(Get-ChildItem -LiteralPath $OutDir -Filter '*.json' -File -ErrorAction SilentlyContinue | Sort-Object Name)
        foreach ($f in $files) {
            $id = $f.BaseName
            if ($id -notmatch $script:IdPattern) { continue }
            $statePath = Join-Path (Join-Path $WorkDir 'state') ($id + '.json')
            if (Test-Path -LiteralPath $statePath) { continue }
            $line = Get-Line $id
            if ($line -eq 'RETRY') { continue }
            if ($null -eq $line) {
                Write-WrapperLog "стан $id — повтор, рядка нема"
                Write-FileAtomic $statePath (([ordered]@{ line = ''; sent = $true; attempts = 0 }) | ConvertTo-Json -Compress)
                continue
            }
            Write-WrapperLog $line
            Write-FileAtomic $statePath (([ordered]@{ line = $line; sent = $false; attempts = 0 }) | ConvertTo-Json -Compress)
        }
        foreach ($sf in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File | Sort-Object Name)) {
            $st = [System.IO.File]::ReadAllText($sf.FullName, $script:Utf8) | ConvertFrom-Json
            if ($st.sent -or $st.attempts -ge $MaxSendAttempts) { continue }
            $sent = Send-Line ([string]$st.line)
            $new = [ordered]@{ line = [string]$st.line; sent = $sent; attempts = [int]$st.attempts + 1 }
            Write-FileAtomic $sf.FullName ($new | ConvertTo-Json -Compress)
        }
        0
    } catch {
        Write-WrapperLog "збій: $($_.Exception.Message)"
        1
    } finally {
        $lockFile.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Main) }
