#Requires -Version 5.1
<#
.SYNOPSIS
Спільне для двох планувальників ноутбука — `gemini_run.ps1` (під `gemini`: смуги Codex і `agy`) і `claude_run.ps1` (під
власником: смуга Claude Code): позначки черги з пріоритетом і строком, смуги й слоти, межі з файла даних, атомарне узяття
позначки, чекання скидання квоти, замок GPU, окрема робоча копія й окремий процес на наряд.

.DESCRIPTION
Підвантажується крапкою (`. queue_lanes.ps1`) після блоку параметрів скрипта; власних параметрів нема. Читає змінні
скрипта: $RepoDir, $GitExe, $LaneDir, $script:NoHooks, $script:StateDir, $script:SlotDir, $script:SelfPath, $script:Bound,
і функцію журналу Write-Log. Два облікові записи розведено жорстко, тож планувальників два; спільні між ними лише замок
GPU та бюджет перевірок PR (тека $LaneDir — `C:\Users\Public\gemini\lanes`, де пишуть і INTERACTIVE, і BATCH) і рядок стану ноутбука.

Позначка: `gemini-queue/<наряд>/<модель>/<спроба>[/<умови>]`; умови — до трьох лексем через `-` у будь-якому порядку:
`p<0-9>` — пріоритет (0 — найвищий; без лексеми — 5), `d<РРРРММДДГГхх>` — строк у UTC, `gpu` — наряд займає відеокарту.
Порядок узяття: пріоритет, строк (без строку — останні), час першої появи позначки на ноутбуці, час коміту, назва.
Смуга — за моделлю: `cc-…` — Claude, `gpt-…` — Codex, решта — `agy`.
#>

. (Join-Path $PSScriptRoot 'wrapper_health.ps1')

$script:QueuePrefix = 'refs/remotes/origin/gemini-queue/'
$script:TaskDir = 'аудит/наряди/'
$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}\z'
$script:SlugCore = $script:SlugPattern -replace '^\^|\\z$', ''
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
$script:CondPattern = '^(?:p[0-9]|d20[0-9]{10}|gpu)(?:-(?:p[0-9]|d20[0-9]{10}|gpu)){0,2}$'
$script:LanesPath = 'аудит/адаптери/gemini/смуги.json'
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -ne 'Core') -or [bool](Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)

# Кількість слотів задає смуги.json; 64 — захист від помилки в даних, не виміряна межа ноутбука.
# Решта меж також під хешем; значення поза ними обрізаються. Параметр задачі власника не обрізаємо.
$script:Ceil = @{
    slots = @(0, 64); poll_minutes = @(1, 5); usage_minutes = @(5, 60); quota_wait_minutes = @(15, 1440)
    agy_total_minutes = @(30, 600); agy_turn_minutes = @(10, 600); codex_stall_minutes = @(10, 240); claude_hang_minutes = @(30, 240)
    min_free_gb = @(5, 500)
}
$script:Defaults = @{
    poll_minutes = 2; usage_minutes = 15; quota_wait_minutes = 60
    agy_total_minutes = 180; agy_turn_minutes = 120; codex_stall_minutes = 60; claude_hang_minutes = 120
    min_free_gb = 30
}
# Місце однієї задачі: робоча копія слота — відстежувані файли main, 1,35 ГБ (вимір 29.10), з запасом. Задачі, чиї копії
# ще створюються (у будь-якому процесі й проході), записані в спільний облік, тож вільне місце для наступної позначки
# зменшується на це число за кожну. Запис без зняття втрачає силу за DiskReserveMinutes.
$script:TaskDiskGb = 1.5
$script:DiskReserveMinutes = 20
# Останній вимір диска перед узяттям позначки (Reserve-DiskRoom): Free, Min, Low — для стану ноутбука.
$script:Disk = $null
# Тека задачі в процесі наряду (Enter-TaskDir) — для промпта.
$script:TaskDirPath = ''
$script:LaneDefaults = [ordered]@{ codex = 2; agy = 2; claude = 2 }
# Скільки разів відмова за квотою повертає ту саму позначку в чергу: далі — кінець із кодом квоти, як до смуг.
$script:MaxRetakes = 5
# Код виходу процесу наряду: слот чи GPU зайняті до старту — позначку не взято, вона лишається в черзі.
$script:WorkerSlotBusy = 3
$script:WorkerGpuBusy = 4
# Спільний рухомий бюджет публічного REST: половина 60/год лишається іншим читачам.
$script:ReviewApiLimit = 30
$script:ReviewApiWindow = 3600
$script:ReviewApiBackoff = 120

# --- процеси й файли ----------------------------------------------------------------------------------------------

function Get-Sha256Hex([string]$Text) {
    <# SHA-256 рядка UTF-8 шістнадцятковими малими. #>
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { -join ($sha.ComputeHash($script:Utf8.GetBytes($Text)) | ForEach-Object { $_.ToString('x2') }) }
    finally { $sha.Dispose() }
}

function Write-FileAtomic([string]$Path, [string]$Text) {
    <# Запис через тимчасовий файл і заміну: читач не бачить половини.

    Спільні файли (стан, heartbeat, кеш квоти) пишуть водночас планувальник і процеси нарядів: зайнята ціль — кілька
    спроб, а не виняток посеред наряду. #>
    $tmp = $Path + '.' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.part'
    [System.IO.File]::WriteAllText($tmp, $Text, $script:Utf8)
    for ($i = 0; $i -lt 20; $i++) {
        try {
            if ([System.IO.File]::Exists($Path)) { [System.IO.File]::Replace($tmp, $Path, [NullString]::Value) } else { [System.IO.File]::Move($tmp, $Path) }
            return
        } catch {
            if ($i -eq 19) { Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; throw }
            Start-Sleep -Milliseconds 50
        }
    }
}

function Get-UtcStamp([datetime]$When) {
    <# Час у UTC рядком ISO з Z. #>
    $When.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
}

function ConvertTo-ArgString([string[]]$Items) {
    <# Рядок аргументів за правилами CommandLineToArgvW.

    .NET Framework не має ArgumentList, а вбудований виклик PowerShell 5.1 губить лапки всередині аргументів. #>
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

function New-StartInfo([string]$Exe, [string[]]$Arguments, [string]$Dir, [switch]$NoRedirect) {
    <# Процес без вікна, UTF-8, git без питань про вхід; -NoRedirect — потоки успадковано (процес наряду). #>
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = ConvertTo-ArgString $Arguments
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    if (-not $NoRedirect) {
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.StandardOutputEncoding = $script:Utf8
        $psi.StandardErrorEncoding = $script:Utf8
    }
    if ($Dir) { $psi.WorkingDirectory = $Dir }
    $psi.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $psi.EnvironmentVariables['GCM_INTERACTIVE'] = 'never'
    $psi
}

function Stop-Tree($Proc) {
    <# Зупинка процесу з усім деревом нащадків. #>
    if ($null -eq $Proc) { return }
    try {
        if (-not $Proc.HasExited) {
            if ($script:OnWindows) { & taskkill.exe /PID $Proc.Id /T /F *> $null }
            else { $Proc.Kill($true) }
        }
        [void]$Proc.WaitForExit(15000)
    } catch { Write-Log "зупинка процесу: $($_.Exception.Message)" }
}

function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$Dir = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) {
    <# Запуск із межею часу (по межі — зупинка дерева) і необов'язковим stdin; повертає код, ознаку межі й обидва потоки. #>
    $psi = New-StartInfo $Exe $Arguments $Dir
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
        $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $script:Utf8)
        $w.Write($StdIn)
        $w.Close()
    }
    $until = [datetime]::UtcNow.AddMinutes($TimeoutMinutes)
    while (-not $p.WaitForExit(1000) -and [datetime]::UtcNow -lt $until) { Invoke-HealthBeat }
    $timedOut = -not $p.HasExited
    if ($timedOut) { Stop-Tree $p } else { $p.WaitForExit() }
    [pscustomobject]@{ Code = $(if ($timedOut) { -1 } else { $p.ExitCode }); TimedOut = $timedOut; Out = $out.Result; Err = $err.Result }
}

function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail, [double]$TimeoutMinutes = 10, [string]$Dir = '') {
    <# git у клоні ($RepoDir) чи в робочій копії слота (-Dir) без входу й без гачків. #>
    $d = $(if ($Dir) { $Dir } else { $RepoDir })
    $all = @('-C', $d, '-c', "core.hooksPath=$script:NoHooks", '-c', 'credential.helper=', '-c', 'core.quotepath=false') + $GitArgs
    $r = Invoke-Native $GitExe $all '' $TimeoutMinutes
    if ($r.Code -ne 0 -and -not $AllowFail) { throw "git $($GitArgs -join ' ') -> $($r.Code): $($r.Err.Trim())" }
    $r
}

function Get-RefSha([string]$Ref) {
    <# SHA коміту посилання або ''. #>
    $r = Invoke-Git @('rev-parse', '-q', '--verify', "$Ref^{commit}") -AllowFail
    if ($r.Code -ne 0) { return '' }
    $r.Out.Trim()
}

# --- межі з файла даних ---------------------------------------------------------------------------------------------

function Get-JsonProp($Obj, [string]$Name) {
    <# Властивість об'єкта з JSON або $null. #>
    if ($null -eq $Obj -or $Obj -is [string] -or $Obj -is [ValueType]) { return $null }
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p) { return $null }
    $p.Value
}

function ConvertTo-Bounded($Value, $Range) {
    <# Число з JSON, обрізане до стелі [min, max]; не число — $null (тоді діє значення з коду). #>
    if ($Value -isnot [int] -and $Value -isnot [long] -and $Value -isnot [double] -and $Value -isnot [decimal]) { return $null }
    [Math]::Min([double]$Range[1], [Math]::Max([double]$Range[0], [double]$Value))
}

function Get-Limits {
    <# Межі смуг: `смуги.json` з origin/main (не з робочої копії агента), обрізаний стелями; нема чи кривий — код.

    Зміна файла в main міняє паралельність і межі на наступному проході без перевстановлення копій: читається він
    після `git fetch`, який перезаписує й origin/main, змінений у клоні. #>
    $l = @{ slots = [ordered]@{}; source = 'код' }
    foreach ($k in $script:LaneDefaults.Keys) { $l.slots[$k] = $script:LaneDefaults[$k] }
    foreach ($k in $script:Defaults.Keys) { $l[$k] = $script:Defaults[$k] }
    $r = Invoke-Git @('cat-file', 'blob', "refs/remotes/origin/main:$script:LanesPath") -AllowFail
    if ($r.Code -ne 0 -or $r.Out.Length -gt 4096) { return $l }
    try { $doc = $r.Out | ConvertFrom-Json } catch { Write-Log 'смуги.json не читається як JSON — межі з коду'; return $l }
    $l.source = 'origin/main'
    foreach ($k in $script:Defaults.Keys) {
        $v = ConvertTo-Bounded (Get-JsonProp $doc $k) $script:Ceil[$k]
        if ($null -ne $v) { $l[$k] = $v }
    }
    $s = Get-JsonProp $doc 'slots'
    foreach ($lane in @($script:LaneDefaults.Keys)) {
        $v = ConvertTo-Bounded (Get-JsonProp $s $lane) $script:Ceil.slots
        if ($null -ne $v) { $l.slots[$lane] = [int][Math]::Floor($v) }
    }
    $l
}

function Get-Limit($Limits, [string]$Param, [string]$Key) {
    <# Значення межі: параметр, заданий явно (задача планувальника, стенд), сильніший за файл даних. #>
    if ($script:Bound.ContainsKey($Param)) { return [double]$script:Bound[$Param] }
    if ($null -eq $Limits) { return [double]$script:Defaults[$Key] }
    [double]$Limits[$Key]
}

# --- позначки ------------------------------------------------------------------------------------------------------

function Get-Lane([string]$Model) {
    <# Смуга за назвою моделі з позначки. #>
    if ($Model.StartsWith('cc-')) { return 'claude' }
    if ($Model -cmatch '^gpt-') { return 'codex' }
    'agy'
}

function ConvertTo-Marker([string]$Line) {
    <# Рядок for-each-ref (посилання, SHA, час коміту) -> позначка; Valid=$false — назва не за форматом. #>
    $f = $Line -split "`t"
    $rest = $f[0].Substring($script:QueuePrefix.Length)
    $parts = @($rest -split '/')
    $m = [pscustomobject]@{ Ref = $f[0]; Name = 'gemini-queue/' + $rest; Sha = $f[1]; Time = [long]$f[2]
        Slug = ''; Model = ''; N = ''; Cond = ''; Prio = 5; Deadline = ''; Gpu = $false; Lane = ''; Seen = [long]0; Valid = $false }
    if ($parts.Count -lt 3 -or $parts.Count -gt 4) { return $m }
    if ($parts[0] -notmatch $script:SlugPattern -or $parts[0].Contains('..') -or $parts[0].EndsWith('.lock')) { return $m }
    if ($parts[1] -notmatch $script:ModelPattern -or $parts[2] -notmatch '^[1-9][0-9]{0,2}$') { return $m }
    if ($parts.Count -eq 4) {
        if ($parts[3] -cnotmatch $script:CondPattern) { return $m }
        $kinds = @{}
        foreach ($t in ($parts[3] -split '-')) {
            $k = $t.Substring(0, 1)
            if ($kinds.ContainsKey($k)) { return $m }
            $kinds[$k] = 1
            if ($t -eq 'gpu') { $m.Gpu = $true }
            elseif ($k -eq 'p') { $m.Prio = [int]$t.Substring(1) }
            else {
                $dt = [datetime]::MinValue
                if (-not [datetime]::TryParseExact($t.Substring(1), 'yyyyMMddHHmm', [cultureinfo]::InvariantCulture, 'None', [ref]$dt)) { return $m }
                $m.Deadline = $t.Substring(1)
            }
        }
        $m.Cond = $parts[3]
    }
    $m.Slug = $parts[0]; $m.Model = $parts[1]; $m.N = $parts[2]; $m.Lane = Get-Lane $parts[1]; $m.Valid = $true
    $m
}

function Get-Markers {
    <# Усі позначки черги з origin (після fetch), і криві — з Valid=$false. #>
    $fmt = '%(refname)%09%(objectname)%09%(committerdate:unix)'
    $r = Invoke-Git @('for-each-ref', "--format=$fmt", $script:QueuePrefix)
    @(foreach ($line in ($r.Out -split "`n")) { if ($line.Trim()) { ConvertTo-Marker $line.Trim() } })
}

function Get-TaskSource($M) {
    <# Усі наряди використовують спільне визначення шляху шаблону. #>
    Get-AutoTaskPath $M.Slug
}

function Get-NightlyMarker([datetime]$Now = [datetime]::UtcNow) {
    <# Після 02:00 UTC читає лише датований дозвіл із GitHub; локальний стан не дає прав. #>
    $utc = $Now.ToUniversalTime()
    if ($utc.Hour -lt 2) { return }
    $date = $utc.ToString('yyyyMMdd')
    $ref = $script:QueuePrefix + 'Е1-нічний-живий-' + $date + '/gpt-6.1-sol-high/1/gpu-p8'
    $sha = Get-RefSha $ref
    if ($sha -cnotmatch '^[0-9a-f]{40}$') { return }
    $main = Get-RefSha 'refs/remotes/origin/main'
    if ($main -cnotmatch '^[0-9a-f]{40}$' -or
        (Invoke-Git @('merge-base', '--is-ancestor', $sha, $main) -AllowFail).Code -ne 0) { return }
    $template = 'аудит/наряди/автоживий.md'
    $build = (Invoke-Git @('cat-file','blob',"${sha}:build.txt") -AllowFail).Out.Trim()
    if ($build -cmatch '^[0-9a-f]{40}$' -and (Invoke-Git @('for-each-ref','--format=%(refname)',($script:QueuePrefix + "автоживий-$build/"))).Out.Trim()) { return }
    if ((Invoke-Git @('cat-file', '-e', "${sha}:$template") -AllowFail).Code -ne 0) { return }
    $dir = Join-Path $RunsDir 'nightly'
    [void](New-Item -ItemType Directory -Force -Path $dir)
    $file = Join-Path $dir ($date + '.json')
    if (Test-Path -LiteralPath $file) {
        $saved = [System.IO.File]::ReadAllText($file, $script:Utf8) | ConvertFrom-Json
        if ($saved.date -cne $date -or $saved.sha -cnotmatch '^[0-9a-f]{40}$' -or
            [string]$saved.time -cnotmatch '^[0-9]{10}$') { throw 'Хибний стан нічного прогону' }
        if ($saved.sha -cne $sha) { return }
    } else {
        $stamp = ([DateTimeOffset]$utc).ToUnixTimeSeconds()
        $saved = [pscustomobject]@{ date = $date; sha = $sha; time = $stamp }
        Write-FileAtomic $file ($saved | ConvertTo-Json -Compress)
    }
    ConvertTo-Marker ($ref + "`t" + $saved.sha + "`t" + $saved.time)
}

function Get-MarkerKey($M) { "$($M.Ref) $($M.Sha)" }

function Get-StatePath([string]$Key) { Join-Path $script:StateDir ((Get-Sha256Hex $Key) + '.txt') }

function Get-ClaimPath([string]$StatePath) { $StatePath -replace '\.txt$', '.claim' }

function Add-FirstSeen($Markers) {
    <# Час першої появи позначки на ноутбуці (файл `<ключ>.seen`) — «час постановки» для рівних за пріоритетом і строком. #>
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    foreach ($m in $Markers) {
        $p = (Get-StatePath (Get-MarkerKey $m)) -replace '\.txt$', '.seen'
        $t = 0L
        if (Test-Path -LiteralPath $p) { [void][long]::TryParse([System.IO.File]::ReadAllText($p).Trim(), [ref]$t) }
        if ($t -le 0) { $t = $now; Write-FileAtomic $p ([string]$now) }
        $m.Seen = $t
    }
}

function Get-OrderedMarkers($Markers) {
    <# Порядок узяття: пріоритет, строк (без строку — після всіх), перша поява, час коміту, назва.

    Sort-Object, а не [Array]::Sort(ключі, позначки): PowerShell передає масив позначок методу копією, і сортувалися лише
    ключі (стенд смуг, 26.10). #>
    Add-FirstSeen $Markers
    @($Markers | Sort-Object @{ Expression = { $_.Prio } }, @{ Expression = { if ($_.Deadline) { $_.Deadline } else { '999999999999' } } },
        @{ Expression = { $_.Seen } }, @{ Expression = { $_.Time } }, @{ Expression = { $_.Name } })
}

function Get-ReviewTime {
    <# Поточна секунда UTC; стенд підміняє годинник без реального чекання. #>
    [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
}

# Спільна політика потрібна й при самостійному завантаженні бібліотеки черги.
if (-not (Get-Command Test-ReviewBranch -ErrorAction SilentlyContinue)) { . (Join-Path $PSScriptRoot 'wrapper_health.ps1') }

function Get-AutoReviewState([string]$Slug) {
    <# Звіряє PR один раз безпосередньо перед моделлю, лише у вже вільному слоті.

    Спільний файл під замком обох облікових записів обмежує всі три смуги 30 запитами за рухому годину.
    Успішний LIVE не кешується: кожен справжній запуск отримує свіжий стан PR. #>
    if ($Slug -cnotmatch '^автоперевірка-([1-9][0-9]{0,8})-([0-9a-f]{40})$') { return 'LIVE' }
    $number = $Matches[1]; $head = $Matches[2]
    $lock = $null
    try {
        $lock = Open-Lock (Join-Path $LaneDir 'review-api.lock')
        if ($null -eq $lock) { return 'REVIEW_API' }
        $path = Join-Path $LaneDir 'review-api.json'
        $now = Get-ReviewTime
        $calls = @(); $until = 0L
        if (Test-Path -LiteralPath $path) {
            $saved = [IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json
            # Пошкоджений бюджет не дозволяє непорахованих запитів.
            if ($null -eq $saved.calls -or $null -eq $saved.until) { return 'REVIEW_API' }
            $calls = @($saved.calls | Where-Object { [long]$_ -gt ($now - $script:ReviewApiWindow) })
            $until = [long]$saved.until
        }
        if ($now -lt $until -or $calls.Count -ge $script:ReviewApiLimit) { return 'REVIEW_API' }
        # Резервуємо запит до мережі: 403/429, тайм-аут і падіння процесу також входять у бюджет.
        $budget = [ordered]@{calls=@($calls) + @($now);until=0L}
        Write-FileAtomic $path ($budget | ConvertTo-Json -Compress)
        try {
            $pr = Invoke-RestMethod -Uri "https://api.github.com/repos/mightyrochy/kod-shi-data/pulls/$number" -Method Get -TimeoutSec 20 -MaximumRedirection 0 -Headers @{Accept='application/vnd.github+json'; 'User-Agent'='kod-shi-wrapper'}
            if ([string]$pr.number -cne $number -or $pr.state -cnotin @('open','closed') -or [string]$pr.head.sha -cnotmatch '^[0-9a-f]{40}$') { throw 'REVIEW_RESPONSE' }
            if ($pr.state -cne 'open' -or $pr.head.sha -cne $head) { return 'STALE' }
            if ($pr.user.login -cne 'mightyrochy' -or $null -eq $pr.head.repo -or $pr.head.repo.full_name -cne 'mightyrochy/kod-shi-data' -or $pr.base.repo.full_name -cne 'mightyrochy/kod-shi-data' -or $pr.base.ref -cne 'main' -or (Test-ReviewBranch ([string]$pr.head.ref))) { return 'STALE' }
            'LIVE'
        } catch {
            $budget.until = $now + $script:ReviewApiBackoff
            Write-FileAtomic $path ($budget | ConvertTo-Json -Compress)
            'REVIEW_API'
        }
    } catch { 'REVIEW_API' }
    finally { if ($null -ne $lock) { $lock.Dispose() } }
}

function Enter-ReviewWait($M, [string]$Head = '') {
    <# Повертає позначку після відмови REST чи вичерпання бюджету без збільшення retakes і кінцевого звіту. #>
    [void](Set-MarkerWait $M ((Get-ReviewTime) + $script:ReviewApiBackoff) @{group='REVIEW_API';head=$Head})
    Write-Log "позначка $($M.Name): REVIEW_API; спроба збережена, повтор у черзі"
}

function Get-MarkerState($M) {
    <# NEW — не бачили; TAKEN — узята (файл `.claim`); WAIT — чекає скидання квоти (Wait.until, unix); DONE — інше. #>
    $sp = Get-StatePath (Get-MarkerKey $M)
    if (Test-Path -LiteralPath (Get-ClaimPath $sp)) { return [pscustomobject]@{ Kind = 'TAKEN'; Wait = $null } }
    if (-not (Test-Path -LiteralPath $sp)) { return [pscustomobject]@{ Kind = 'NEW'; Wait = $null } }
    $t = [System.IO.File]::ReadAllText($sp, $script:Utf8)
    if ($t.StartsWith('WAIT {')) {
        try { return [pscustomobject]@{ Kind = 'WAIT'; Wait = ($t.Substring(5) | ConvertFrom-Json) } } catch { $null = $_ }
    }
    [pscustomobject]@{ Kind = 'DONE'; Wait = $null }
}

function Test-MarkerReady($State) {
    <# Позначку можна брати: нова або час чекання квоти минув. #>
    if ($State.Kind -eq 'NEW') { return $true }
    $State.Kind -eq 'WAIT' -and [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -ge [long]$State.Wait.until
}

function New-Claim($M, [string]$Id) {
    <# Атомарне узяття: файл `.claim` створюється лише якщо його нема (CreateNew) — дві смуги чи два слоти одну позначку
    не візьмуть. $true — узято цим викликом. #>
    $p = Get-ClaimPath (Get-StatePath (Get-MarkerKey $M))
    try { $fs = [System.IO.File]::Open($p, 'CreateNew', 'Write', 'None') } catch { return $false }
    try { $b = $script:Utf8.GetBytes($Id); $fs.Write($b, 0, $b.Length) } finally { $fs.Dispose() }
    $true
}

function Remove-Claim([string]$StatePath) {
    <# Звільнити узяття позначки (після кінця чи переходу в чекання квоти). #>
    Remove-Item -LiteralPath (Get-ClaimPath $StatePath) -Force -ErrorAction SilentlyContinue
}

function Get-Retakes([string]$StatePath) {
    <# Скільки разів позначку вже повернули в чергу за квотою: лічильник `retakes` несуть і WAIT, і STARTED (запуск не
    стирає його — інакше кожна відмова рахувалась би першою і межа MaxRetakes була б недосяжна). #>
    if (-not (Test-Path -LiteralPath $StatePath)) { return 0 }
    $t = [System.IO.File]::ReadAllText($StatePath, $script:Utf8)
    if ($t -match '^(WAIT|STARTED) .*"retakes":\s*([0-9]{1,3})') { return [int]$Matches[2] }
    0
}

function Set-MarkerWait($M, [long]$Until, [hashtable]$Extra) {
    <# Позначка чекає скидання квоти до $Until (unix): спроба не спалена, ту саму позначку візьме та сама смуга.
    Повертає число повернень у чергу; понад MaxRetakes — $null (чекання не записано, далі кінець із кодом квоти). #>
    $sp = Get-StatePath (Get-MarkerKey $M)
    $n = Get-Retakes $sp
    if ($Extra.ContainsKey('retake') -and $Extra.retake) { $n++ }
    if ($n -gt $script:MaxRetakes) { return $null }
    $j = [ordered]@{ until = $Until; until_utc = (Get-UtcStamp ([DateTimeOffset]::FromUnixTimeSeconds($Until).UtcDateTime)); marker = $M.Name; retakes = $n }
    foreach ($k in $Extra.Keys) { if ($k -ne 'retake') { $j[$k] = $Extra[$k] } }
    Write-FileAtomic $sp ('WAIT ' + ($j | ConvertTo-Json -Compress))
    Remove-Claim $sp
    $n
}

function Clear-UnstartedClaim([string]$StatePath) {
    <# Узяття без запуску: помилка до STARTED (робоча копія, запуск процесу наряду) не лишає позначку вилученою з черги —
    claim звільняється, стан (NEW чи WAIT) зберігається. Позначку з STARTED закриває Resume-Interrupted. #>
    $t = ''
    if (Test-Path -LiteralPath $StatePath) { try { $t = [System.IO.File]::ReadAllText($StatePath, $script:Utf8) } catch { $null = $_ } }
    if ($t.StartsWith('STARTED ')) { return }
    Remove-Claim $StatePath
}

function Step-FailedStart($M, [string]$StatePath, [switch]$Storage) {
    <# Відмова до STARTED (робоча копія, запуск процесу наряду) — та сама ланка claim -> STARTED, що й квота: рахується
    тим самим лічильником `retakes` і тією самою межею MaxRetakes. 'NONE' — claim уже звільнено (слот чи GPU зайняті,
    кінець, чекання) або є STARTED; 'RETRY' — claim звільнено, позначка в черзі (стан WAIT, група START, без чекання);
    'LIMIT' — межа: чекання не записано, claim лишається, викликач закриває позначку кінцевим станом і рядком;
    'KEEP' — минущий збій сховища (-Storage, Test-StorageFault): позначка не вада й не згоряє до CRASH, поки диск повний —
    чекає наступного проходу (WAIT, група DISK, без ліку retakes; без чекання збій, що не минає, крутився б без паузи). #>
    $t = ''
    if (Test-Path -LiteralPath $StatePath) { try { $t = [System.IO.File]::ReadAllText($StatePath, $script:Utf8) } catch { $null = $_ } }
    if ($t.StartsWith('STARTED ') -or -not (Test-Path -LiteralPath (Get-ClaimPath $StatePath))) { return 'NONE' }
    # Голова гілки попереднього чекання за квотою — для продовження — не губиться.
    $head = ''
    if ($t.StartsWith('WAIT {')) { try { $head = [string](Get-JsonProp ($t.Substring(5) | ConvertFrom-Json) 'head') } catch { $null = $_ } }
    if ($Storage) {
        $until = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + [long](60 * (Get-Limit $script:Limits 'PollMinutes' 'poll_minutes'))
        [void](Set-MarkerWait $M $until @{ group = 'DISK'; head = $head })
        Write-Log "позначка $($M.Name): збій сховища до запуску — чекає наступного проходу без ліку відмов"
        return 'KEEP'
    }
    $n = Set-MarkerWait $M ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) @{ retake = $true; group = 'START'; head = $head }
    if ($null -eq $n) { return 'LIMIT' }
    Write-Log "позначка $($M.Name): відмова до запуску, повернено в чергу ($n із $script:MaxRetakes)"
    'RETRY'
}

function Clear-OrphanClaims([string]$RunsRoot) {
    <# Claim, чий процес наряду зник до STARTED (вимкнення між узяттям і запуском): старший за 10 хв, стану STARTED нема,
    замок слота (з worker.json теки прогону `<id>`) вільний — звільнити. Живий наряд тримає замок слота, свіжий claim
    ще не дійшов до запуску. #>
    foreach ($c in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.claim' -File -ErrorAction SilentlyContinue)) {
        if (((Get-Date) - $c.LastWriteTime).TotalMinutes -lt 10) { continue }
        $sp = $c.FullName -replace '\.claim$', '.txt'
        $id = ''; try { $id = [System.IO.File]::ReadAllText($c.FullName, $script:Utf8).Trim() } catch { continue }
        if ($id -notmatch '^[0-9]{8}-[0-9]{6}-[0-9a-f]{12}$') { continue }
        $wf = Join-Path (Join-Path $RunsRoot $id) 'worker.json'
        if (Test-Path -LiteralPath $wf) {
            $slot = ''; try { $slot = [string](Get-JsonProp ([System.IO.File]::ReadAllText($wf, $script:Utf8) | ConvertFrom-Json) 'slot') } catch { continue }
            if (-not (Test-SlotName $slot) -or -not (Test-LockFree (Join-Path $script:SlotDir "$slot.lock"))) { continue }
        }
        Write-Log "узяття $id без запуску — звільнено"
        Clear-UnstartedClaim $sp
    }
}

function Get-WaitingMarkers {
    <# Позначки в чеканні квоти (для стану): назва, до коли (UTC), група. #>
    @(foreach ($f in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.txt' -File -ErrorAction SilentlyContinue)) {
        $t = [System.IO.File]::ReadAllText($f.FullName, $script:Utf8)
        if (-not $t.StartsWith('WAIT {')) { continue }
        try { $j = $t.Substring(5) | ConvertFrom-Json } catch { continue }
        [pscustomobject]@{ Marker = [string]$j.marker; Until = [string]$j.until_utc; Group = [string](Get-JsonProp $j 'group') }
    })
}

# --- слоти, GPU, процес наряду -------------------------------------------------------------------------------------

function Test-SlotCount([string]$Value) {
    <# Ціла кількість слотів у спільному діапазоні; недовірені значення відкидаємо, не обрізаємо. #>
    $n = 0
    [regex]::IsMatch($Value, '\A(?:0|[1-9][0-9]*)\z') -and [int]::TryParse($Value, [ref]$n) -and
        $n -ge $script:Ceil.slots[0] -and $n -le $script:Ceil.slots[1]
}

function Test-SlotName([string]$Name, [string[]]$Lanes = @($script:LaneDefaults.Keys)) {
    <# Назва слота дозволеної смуги з додатним номером у спільному діапазоні.

    Номер не обмежуємо поточним N: після зменшення смуги вже запущені наряди мають завершитися. #>
    $m = [regex]::Match($Name, '\A([a-z]+)-([1-9][0-9]*)\z')
    $m.Success -and $Lanes -ccontains $m.Groups[1].Value -and (Test-SlotCount $m.Groups[2].Value)
}

function Open-Lock([string]$Path) {
    <# Винятковий замок-файл (FileShare None) або $null — зайнято. Звільняє ОС, коли процес-власник завершився. #>
    try { [System.IO.File]::Open($Path, 'OpenOrCreate', 'ReadWrite', 'None') } catch { $null }
}

function Test-LockFree([string]$Path) {
    <# Замок вільний зараз (відкрито й одразу закрито). #>
    $l = Open-Lock $Path
    if ($null -eq $l) { return $false }
    $l.Dispose()
    $true
}

function Get-GpuLockPath { Join-Path $LaneDir 'gpu.lock' }

function Get-BusySlots([string]$Lane, $Workers) {
    <# Зайняті слоти смуги: свій живий процес наряду або чужий замок слота (наряд попереднього проходу ще йде). #>
    @(for ($k = 1; $k -le $script:Ceil.slots[1]; $k++) {
        $id = "$Lane-$k"
        $own = @($Workers | Where-Object { $_.Slot -eq $id -and -not $_.Proc.HasExited }).Count -gt 0
        if ($own -or -not (Test-LockFree (Join-Path $script:SlotDir "$id.lock"))) { $id }
    })
}

function Get-FreeSlot([string]$Lane, [int]$N, $Workers) {
    <# Вільний слот смуги, коли зайнятих менше за N з файла даних; інакше ''. #>
    $busy = @(Get-BusySlots $Lane $Workers)
    if ($busy.Count -ge $N) { return '' }
    for ($k = 1; $k -le $script:Ceil.slots[1]; $k++) { if ($busy -notcontains "$Lane-$k") { return "$Lane-$k" } }
    ''
}

function Get-FreeDiskGb([string]$Dir) {
    <# Вільне місце (ГБ) на диску теки; не прочиталось — $null. #>
    try { [Math]::Round(([System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot([System.IO.Path]::GetFullPath($Dir)))).AvailableFreeSpace / 1GB, 1) }
    catch { $null }
}

function Get-DiskLedgerDir { Join-Path $LaneDir 'disk' }

function Open-DiskLedger {
    <# Замок обліку місця: спільний для claude-run, gemini-run і всіх їхніх проходів (теки смуг одна на ноутбук); чекаємо
    до 15 с, не вийшло — $null (позначку не беруть, наступний прохід спробує знову). #>
    $until = (Get-Date).AddSeconds(15)
    do {
        $l = Open-Lock (Join-Path $LaneDir 'disk.lock')
        if ($null -ne $l) { return $l }
        Start-Sleep -Milliseconds 100
    } while ((Get-Date) -lt $until)
    $null
}

function Reserve-DiskRoom([string]$Dir, [string]$Id) {
    <# Диск вміщає ще одну задачу: вільне мінус місце, уже обіцяне копіям, що ще створюються (файли обліку
    `lanes\disk\<id>` усіх процесів і проходів), мінус ця задача — не менше порогу min_free_gb. Так — задача записана в
    облік (під замком: перевірка й запис не розриваються між процесами); ні — позначку не беруть: без claim, без ліку
    відмов, вона чекає. Облік знімає Release-DiskRoom, коли копія створена (вільне вже її враховує) чи задача не
    запустилась; запис старший за DiskReserveMinutes — зірваний процес — не рахується. Вимір — у $script:Disk (стан
    ноутбука). Місця не прочитано — не стримуємо. #>
    $min = Get-Limit $script:Limits 'MinFreeGb' 'min_free_gb'
    $ledger = Get-DiskLedgerDir
    $lock = Open-DiskLedger
    if ($null -eq $lock) { return $false }
    try {
        [void](New-Item -ItemType Directory -Force -Path $ledger)
        $live = 0
        foreach ($f in @(Get-ChildItem -LiteralPath $ledger -File -ErrorAction SilentlyContinue)) {
            if ($f.LastWriteTimeUtc -lt (Get-Date).ToUniversalTime().AddMinutes(-$script:DiskReserveMinutes)) { Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue }
            elseif ($f.Name -ne $Id) { $live++ }
        }
        $free = Get-FreeDiskGb $Dir
        $left = $(if ($null -ne $free) { $free - ($live + 1) * $script:TaskDiskGb } else { $null })
        $low = ($null -ne $left) -and $left -lt $min
        if ($low -and -not ($null -ne $script:Disk -and $script:Disk.Low)) { Write-Log "диск: вільно $left ГБ < поріг $min ГБ — позначок не беру" }
        $script:Disk = [pscustomobject]@{ Free = $free; Min = $min; Low = $low }
        if (-not $low) { [System.IO.File]::WriteAllText((Join-Path $ledger $Id), "$PID", $script:Utf8) }
        -not $low
    } finally { $lock.Dispose() }
}

function Release-DiskRoom([string]$Id) {
    <# Зняти задачу з обліку місця: копія створена (чи задача не запустилась). #>
    if ($Id) { Remove-Item -LiteralPath (Join-Path (Get-DiskLedgerDir) $Id) -Force -ErrorAction SilentlyContinue }
}

function Read-SlotInfo([string]$Lane) {
    <# Що йде в слотах смуги зараз: файли `<слот>.json` при зайнятому замку слота. #>
    @(for ($k = 1; $k -le $script:Ceil.slots[1]; $k++) {
        $id = "$Lane-$k"; $j = Join-Path $script:SlotDir "$id.json"
        if (-not (Test-Path -LiteralPath $j)) { continue }
        if (Test-LockFree (Join-Path $script:SlotDir "$id.lock")) { continue }
        try { [System.IO.File]::ReadAllText($j, $script:Utf8) | ConvertFrom-Json } catch { $null = $_ }
    })
}

function Test-SlugBusy([string]$Slug, [string[]]$Lanes) {
    <# Той самий наряд уже йде в одному зі слотів: дві спроби одного наряду водночас не беремо (одна гілка). #>
    foreach ($ln in $Lanes) { foreach ($s in @(Read-SlotInfo $ln)) { if ([string]$s.slug -ceq $Slug) { return $true } } }
    $false
}

function Get-WorkerCommand([string]$File) {
    <# Команда процесу наряду: той самий скрипт тим самим PowerShell з -WorkerFile (стенд підміняє). #>
    @{ Exe = (Get-Process -Id $PID).Path; Args = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $script:SelfPath, '-WorkerFile', $File) }
}

function Start-Worker([hashtable]$Job, [string]$Dir) {
    <# Наряд — окремим процесом зі своїм слотом, текою запуску й робочою копією; параметри скрипта — ті самі. #>
    $Job.params = $script:Bound
    $file = Join-Path $Dir 'worker.json'
    Write-FileAtomic $file ($Job | ConvertTo-Json -Compress -Depth 6)
    $c = Get-WorkerCommand $file
    $p = [System.Diagnostics.Process]::Start((New-StartInfo $c.Exe $c.Args '' -NoRedirect))
    [pscustomobject]@{ Slot = $Job.slot; Slug = $Job.slug; Gpu = [bool]$Job.gpu; Marker = $Job.name; Proc = $p }
}

function Read-WorkerJob([string]$File) {
    <# Завдання процесу наряду; параметри скрипта з нього стають змінними скрипта (як у планувальника). #>
    $job = [System.IO.File]::ReadAllText($File, $script:Utf8) | ConvertFrom-Json
    $p = Get-JsonProp $job 'params'
    $script:Bound = @{}
    if ($null -ne $p) {
        foreach ($x in $p.PSObject.Properties) { Set-Variable -Scope Script -Name $x.Name -Value $x.Value; $script:Bound[$x.Name] = $x.Value }
    }
    $job
}

function Wait-Workers($Workers, [double]$Minutes) {
    <# Чекати, доки скінчиться будь-який свій наряд або мине інтервал опитування. #>
    $alive = @($Workers | Where-Object { -not $_.Proc.HasExited }).Count
    $until = (Get-Date).AddMinutes($Minutes)
    while ((Get-Date) -lt $until) {
        if (@($Workers | Where-Object { -not $_.Proc.HasExited }).Count -lt $alive) { return }
        Invoke-HealthBeat
        Start-Sleep -Milliseconds 500
    }
}

function Enter-WorkTree([string]$Path, [string]$Commit) {
    <# Робоча копія слота: git worktree клону (спільні об'єкти й посилання, свої індекс і тека); нема — створюється. #>
    [void](Invoke-Git @('worktree', 'prune') -AllowFail)
    if (-not (Test-Path -LiteralPath (Join-Path $Path '.git'))) {
        if (Test-Path -LiteralPath $Path) { Remove-Tree $Path }
        [void](New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path))
        [void](Invoke-Git @('worktree', 'add', '-q', '-f', '--detach', $Path, $Commit))
    }
    $Path
}

function Remove-Tree([string]$Path) {
    <# Тека з шляхами понад 260 знаків: Remove-Item на них падає, `rd` з префіксом \\?\ — ні. #>
    try { Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop }
    catch {
        if (-not $script:OnWindows) { throw }
        & cmd.exe /d /c "rd /s /q `"\\?\$([System.IO.Path]::GetFullPath($Path))`"" 2>$null
        if (Test-Path -LiteralPath $Path) { throw }
    }
}

function Remove-WorkTree([string]$Path, [string]$Clone) {
    <# Робоча копія слота після прогону — геть із диска й з обліку клону $Clone: на диску лише копії задач у роботі
    (1,35 ГБ кожна), а не по копії на кожен слот, що колись працював. Не вийшло — лишається, Enter-WorkTree
    перевикористає її. Коміти не губляться: гілки й об'єкти — спільні з клоном. #>
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return }
    $r = Invoke-Git @('worktree', 'remove', '--force', $Path) -AllowFail -Dir $Clone
    # Недостворена копія (збій посеред `worktree add`) git-у не відома — тека без обліку.
    if ($r.Code -ne 0 -and -not (Test-Path -LiteralPath (Join-Path $Path '.git'))) { try { Remove-Tree $Path } catch { $null = $_ } }
    if (Test-Path -LiteralPath $Path) { Write-Log "робоча копія $Path не прибрана: $($r.Err.Trim())" }
    [void](Invoke-Git @('worktree', 'prune') -AllowFail -Dir $Clone)
}

function Clear-IdleWorkTrees([string]$Root, [string]$Clone, [string[]]$Lanes) {
    <# Копії слотів без наряду (замок слота вільний): накопичене до цієї версії й лишене зірваними прогонами. Кличе
    планувальник до запуску своїх нарядів; живий наряд тримає замок свого слота, тож його копію не чіпаємо. #>
    foreach ($d in @(Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue)) {
        if (-not (Test-SlotName $d.Name $Lanes) -or -not (Test-LockFree (Join-Path $script:SlotDir "$($d.Name).lock"))) { continue }
        Remove-WorkTree $d.FullName $Clone
    }
}

function Clear-RunDir([string]$Dir) {
    <# Тека завершеного прогону тримає журнал і стан (result.json, worker.json, журнали рушія, вихідні ходів); копії
    промпта — наряд і контекст із git, наступна спроба складе їх знову — геть. #>
    foreach ($f in @(Get-ChildItem -LiteralPath $Dir -File -ErrorAction SilentlyContinue)) {
        if ($f.Name -match '\A(prompt\.(txt|md)|turn[0-9]+\.md)\z') { Remove-Item -LiteralPath $f.FullName -Force -ErrorAction SilentlyContinue }
    }
}

function Enter-TaskDir([string]$RunDir) {
    <# Тека задачі для дерев, клонів і виводу — у теці прогону; TEMP/TMP процесу наряду, а отже рушія й усіх його
    нащадків, — туди ж. Що задача створила, обгортка прибирає разом із прогоном (Clear-TaskDir), а не лишається в корені
    профілю й системному TEMP (#2181). Шлях — у промпті ($script:TaskDirPath). #>
    $d = Join-Path $RunDir 'task'
    [void](New-Item -ItemType Directory -Force -Path $d)
    $script:TaskDirPath = $d
    $env:TEMP = $d; $env:TMP = $d
    $d
}

function Clear-TaskDir([string]$Dir) {
    <# Після прогону тека задачі — геть. Лишається, коли git у ній має незапушені коміти (HEAD поза origin; у
    самостійному клоні — і гілки): тоді рядок у журнал і тривога TASKDIR UNPUSHED диспетчерові. #>
    if (-not $Dir -or -not (Test-Path -LiteralPath $Dir)) { return }
    foreach ($g in @(Get-ChildItem -LiteralPath $Dir -Recurse -Depth 3 -Force -Filter '.git' -ErrorAction SilentlyContinue)) {
        $repo = $(if ($g.PSIsContainer) { $g.Parent.FullName } else { $g.DirectoryName })
        $range = $(if ($g.PSIsContainer) { @('--branches', 'HEAD') } else { @('HEAD') })
        $r = Invoke-Git (@('log', '--oneline', '-n', '1') + $range + @('--not', '--remotes')) -AllowFail -Dir $repo
        if ($r.Code -eq 0 -and $r.Out.Trim()) {
            Write-Log "тека задачі $Dir лишається: незапушене в $repo ($($r.Out.Trim()))"
            Add-HealthAlert 'TASKDIR' 'UNPUSHED'
            return
        }
    }
    try { Remove-Tree $Dir } catch { Write-Log "тека задачі $Dir не прибрана: $($_.Exception.Message)" }
}

function Reset-WorkTree([string]$Dir) {
    <# Чиста робоча копія: перервані операції, замок індексу, незакомічене й зайве — геть. #>
    foreach ($op in @('merge', 'rebase', 'cherry-pick', 'revert')) { [void](Invoke-Git @($op, '--abort') -AllowFail -Dir $Dir) }
    $lock = (Invoke-Git @('rev-parse', '--git-path', 'index.lock') -Dir $Dir).Out.Trim()
    if (-not [System.IO.Path]::IsPathRooted($lock)) { $lock = Join-Path $Dir $lock }
    if (Test-Path -LiteralPath $lock) { Remove-Item -LiteralPath $lock -Force }
    [void](Invoke-Git @('reset', '-q', '--hard') -Dir $Dir)
    [void](Invoke-Git @('clean', '-q', '-ffd') -Dir $Dir)
}

function Get-AutoTaskPath([string]$Slug) {
    <# Лише два закриті шаблони нарядів із main; довільний slug лишається звичайним нарядом. #>
    if ($Slug -cmatch '^автоперевірка-[1-9][0-9]{0,8}-[0-9a-f]{40}$') { return 'аудит/наряди/автоперевірка.md' }
    if ($Slug -cmatch '^(?:автоживий-[0-9a-f]{40}|Е1-нічний-живий-[0-9]{8})$') { return 'аудит/наряди/автоживий.md' }
    $script:TaskDir + $Slug + '.md'
}

function Get-AutoPublicItems([string]$Path) {
    <# Пагінує публічний GET; збій не стає порожнім успішним входом. #>
    for ($page = 1; $page -le 100; $page++) {
        $separator = if ($Path.Contains('?')) { '&' } else { '?' }
        $data = Invoke-RestMethod -Uri ("https://api.github.com/repos/mightyrochy/kod-shi-data/$Path" + $separator + "per_page=100&page=$page") -Method Get -TimeoutSec 20 -MaximumRedirection 0 -Headers @{Accept='application/vnd.github+json'; 'User-Agent'='kod-shi-wrapper'}
        $items = @($data)
        foreach ($item in $items) { $item }
        if ($items.Count -lt 100) { return }
    }
    throw 'AUTO_PAGES'
}

function Get-AutoReviewInput([string]$Number) {
    <# Рецензії та inline зауваження лише Codex; відповідь чужому не входить. #>
    $result = @()
    foreach ($item in @(Get-AutoPublicItems "pulls/$Number/reviews")) {
        if ($item.user.login -ceq 'chatgpt-codex-connector[bot]') {
            $result += @{kind='review';id=$item.id;body=$item.body;commit=$item.commit_id}
        }
    }
    $comments = @(Get-AutoPublicItems "pulls/$Number/comments")
    foreach ($item in $comments) {
        if ($item.user.login -cne 'chatgpt-codex-connector[bot]') { continue }
        $reply = $item.PSObject.Properties['in_reply_to_id']
        if ($null -ne $reply -and $reply.Value) {
            $parent = @($comments | Where-Object { $_.id -eq $reply.Value -and $_.user.login -cin @('mightyrochy','chatgpt-codex-connector[bot]') })
            if (-not $parent.Count) { continue }
        }
        $result += @{kind='inline';id=$item.id;path=$item.path;body=$item.body;commit=$item.commit_id}
    }
    ConvertTo-Json -InputObject @($result) -Depth 6 -Compress
}

function Get-AutoLivePlan([string]$BuildMain) {
    <# Один план для автоживого й Е1: сцена один раз, питання всіх злитих довірених PR. #>
    $pulls = @(Get-AutoPublicItems 'pulls?state=all&sort=updated&direction=desc' | Where-Object {
        $_.user.login -ceq 'mightyrochy' -and $null -ne $_.head.repo -and $_.head.repo.full_name -ceq 'mightyrochy/kod-shi-data' -and
        $_.base.repo.full_name -ceq 'mightyrochy/kod-shi-data' -and $_.base.ref -ceq 'main'
    })
    $until = [datetimeoffset]::Parse((Invoke-Git @('show','-s','--format=%cI',$BuildMain)).Out.Trim())
    # Час звіту не визначає склад прогону: PR міг злитися, поки модель ще працювала.
    $history = @{}
    $rank = 0
    foreach ($commit in ((Invoke-Git @('rev-list','--topo-order',$BuildMain,'--')).Out -split "`n")) {
        if ($commit.Trim()) { $history[$commit.Trim()] = $rank; $rank++ }
    }
    $checked = ''
    foreach ($report in $pulls) {
        if ([string]$report.head.ref -cnotmatch '^(?:gemini|claude|codex)/(?:автоживий-([0-9a-f]{40})|Е1-нічний-живий-[0-9]{8})$') { continue }
        $stamp = [string]$Matches[1]
        $declared = [regex]::Matches([string]$report.body, '(?m)^ПЕРЕВІРЕНО ЗБІРКУ: ([0-9a-f]{40})\r?$')
        if ($declared.Count -gt 1) { continue }
        $candidate = if ($declared.Count -eq 1) { $declared[0].Groups[1].Value } else { $stamp }
        # Старий нічний звіт без SHA не може відсікти неперевірений код.
        if ($candidate -and $history.ContainsKey($candidate) -and
            (-not $checked -or $history[$candidate] -lt $history[$checked])) { $checked = $candidate }
    }
    $since = [datetimeoffset]::MinValue
    $covered = @{}
    if ($checked) {
        $since = [datetimeoffset]::Parse((Invoke-Git @('show','-s','--format=%cI',$checked)).Out.Trim())
        foreach ($commit in ((Invoke-Git @('rev-list',$checked,'--')).Out -split "`n")) {
            if ($commit.Trim()) { $covered[$commit.Trim()] = $true }
        }
    }
    $scenes = [ordered]@{}
    foreach ($pr in @($pulls | Sort-Object merged_at,number)) {
        if (-not $pr.merged_at) { continue }
        $merge = [string]$pr.merge_commit_sha
        if ($merge -cnotmatch '^[0-9a-f]{40}$') { throw 'AUTO_MERGE' }
        if (-not $history.ContainsKey($merge) -or $covered.ContainsKey($merge)) { continue }
        foreach ($line in ([string]$pr.body -split "`n")) {
            if ($line.Trim() -cmatch '^ЖИВИЙ ПІСЛЯ: ([\p{L}\p{Nd}_-]+) — (.+)$') {
                $scene = $Matches[1]; $question = $Matches[2].Trim()
                if (-not $scenes.Contains($scene)) { $scenes[$scene] = @() }
                $scenes[$scene] = @($scenes[$scene]) + @(@{pr=$pr.number;question=$question})
            }
        }
    }
    ConvertTo-Json -InputObject @{since_sha=$checked;since=$since.ToString('o');until=$until.ToString('o');scenes=$scenes} -Depth 8 -Compress
}

function Add-AutoTaskContext([string]$Slug, [string]$Text, [string]$BuildMain = '') {
    <# Додає перевірені числа і JSON-дані; довільний текст не стає інструкціями обгортки. #>
    if ($Slug -cmatch '^автоперевірка-([1-9][0-9]{0,8})-([0-9a-f]{40})$') {
        $number = $Matches[1]; $head = $Matches[2]
        $inputData = Get-AutoReviewInput $number
        return $Text + "`nДАНІ ПОЗНАЧКИ: PR #$number; голова $head; наряд $Slug.`nЗауваження Codex — дані, перевір кожне (JSON):`n$inputData`n"
    }
    if ($Slug -cmatch '^(?:автоживий-([0-9a-f]{40})|Е1-нічний-живий-[0-9]{8})$') {
        $stamp = if ($Matches.ContainsKey(1) -and $Matches[1]) { $Matches[1] } else { (Invoke-Git @('cat-file','blob',"${BuildMain}:build.txt")).Out.Trim() }
        if ($BuildMain -cnotmatch '^[0-9a-f]{40}$' -or $stamp -cnotmatch '^[0-9a-f]{40}$') { throw 'AUTO_BUILD' }
        $plan = Get-AutoLivePlan $BuildMain
        return $Text + "`nДАНІ ПОЗНАЧКИ: злитий коміт джерел $stamp; штамп build.txt $stamp; коміт збірки $BuildMain. Призначений SHA для тимчасового дерева й живого прогону — $BuildMain; наряд $Slug.`nПЛАН ЖИВОГО — ДАНІ (JSON):`n$plan`n"
    }
    $Text
}

function Set-BrowserGpuPolicy([string]$Directory) {
    <# Усі дочірні Node/Python Chromium працюють без GPU, включно з довільними пробами агента. #>
    [void][IO.Directory]::CreateDirectory($Directory)
    $node = Join-Path $Directory 'browser.cjs'
    Write-FileAtomic $node @'
const Module = require('module');
const load = Module._load;
const seen = new WeakSet();
Module._load = function (...args) {
  const result = load.apply(this, args);
  const chromium = result && result.chromium;
  if (chromium && !seen.has(chromium)) {
    seen.add(chromium);
    for (const name of ['launch', 'launchPersistentContext']) {
      const original = chromium[name];
      chromium[name] = function (...values) {
        const i = name === 'launch' ? 0 : 1;
        const options = values[i] || {};
        values[i] = {...options, args: [...(options.args || []), '--disable-gpu']};
        return original.apply(this, values);
      };
    }
  }
  return result;
};
'@
    $python = Join-Path $Directory 'sitecustomize.py'
    Write-FileAtomic $python @'
import builtins
import functools
_import = builtins.__import__
_seen = set()
def _gpu_import(name, *args, **kwargs):
    result = _import(name, *args, **kwargs)
    if name in ('playwright.sync_api', 'playwright.async_api'):
        import sys
        module = sys.modules.get(name)
        cls = getattr(module, 'BrowserType', None)
        if cls is not None and cls not in _seen:
            _seen.add(cls)
            for method in ('launch', 'launch_persistent_context'):
                original = getattr(cls, method)
                def decorate(fn):
                    @functools.wraps(fn)
                    def launch(*a, **kw):
                        kw['args'] = [*(kw.get('args') or []), '--disable-gpu']
                        return fn(*a, **kw)
                    return launch
                setattr(cls, method, decorate(original))
    return result
builtins.__import__ = _gpu_import
'@
    $env:NODE_OPTIONS = ($env:NODE_OPTIONS + ' --require "' + $node.Replace('\','/') + '"').Trim()
    $env:PYTHONPATH = $Directory + [IO.Path]::PathSeparator + $env:PYTHONPATH
}

function Test-ExternalGpuFree {
    <# Сторонній обчислювальний процес лишає GPU-наряд у черзі, без кінцевого блокера. #>
    $exe = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($null -eq $exe) { return $true }
    $r = Invoke-Native $exe.Source @('--query-compute-apps=pid','--format=csv,noheader') '' 1
    $r.Code -eq 0 -and -not $r.Out.Trim()
}
