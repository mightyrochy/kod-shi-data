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
}
$script:Defaults = @{
    poll_minutes = 2; usage_minutes = 15; quota_wait_minutes = 60
    agy_total_minutes = 180; agy_turn_minutes = 120; codex_stall_minutes = 60; claude_hang_minutes = 120
}
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
            if ($pr.user.login -cne 'mightyrochy' -or $null -eq $pr.head.repo -or $pr.head.repo.full_name -cne 'mightyrochy/kod-shi-data' -or $pr.base.repo.full_name -cne 'mightyrochy/kod-shi-data' -or $pr.base.ref -cne 'main' -or $pr.head.ref -match '/авто(перевірка|живий)-') { return 'STALE' }
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

function Step-FailedStart($M, [string]$StatePath) {
    <# Відмова до STARTED (робоча копія, запуск процесу наряду) — та сама ланка claim -> STARTED, що й квота: рахується
    тим самим лічильником `retakes` і тією самою межею MaxRetakes. 'NONE' — claim уже звільнено (слот чи GPU зайняті,
    кінець, чекання) або є STARTED; 'RETRY' — claim звільнено, позначка в черзі (стан WAIT, група START, без чекання);
    'LIMIT' — межа: чекання не записано, claim лишається, викликач закриває позначку кінцевим станом і рядком. #>
    $t = ''
    if (Test-Path -LiteralPath $StatePath) { try { $t = [System.IO.File]::ReadAllText($StatePath, $script:Utf8) } catch { $null = $_ } }
    if ($t.StartsWith('STARTED ') -or -not (Test-Path -LiteralPath (Get-ClaimPath $StatePath))) { return 'NONE' }
    # Голова гілки попереднього чекання за квотою — для продовження — не губиться.
    $head = ''
    if ($t.StartsWith('WAIT {')) { try { $head = [string](Get-JsonProp ($t.Substring(5) | ConvertFrom-Json) 'head') } catch { $null = $_ } }
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
        if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Recurse -Force }
        [void](New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path))
        [void](Invoke-Git @('worktree', 'add', '-q', '-f', '--detach', $Path, $Commit))
    }
    $Path
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
    if ($Slug -cmatch '^автоживий-[0-9a-f]{40}$') { return 'аудит/наряди/автоживий.md' }
    $script:TaskDir + $Slug + '.md'
}

function Add-AutoTaskContext([string]$Slug, [string]$Text, [string]$BuildMain = '') {
    <# Числа та SHA із перевіреної позначки стають даними шаблону, текст PR не стає промптом. #>
    if ($Slug -cmatch '^автоперевірка-([1-9][0-9]{0,8})-([0-9a-f]{40})$') { return $Text + "`nДАНІ ПОЗНАЧКИ: PR #$($Matches[1]); голова $($Matches[2]); наряд $Slug.`n" }
    if ($Slug -cmatch '^автоживий-([0-9a-f]{40})$') {
        $stamp = $Matches[1]
        if ($BuildMain -cnotmatch '^[0-9a-f]{40}$') { throw 'AUTO_BUILD' }
        return $Text + "`nДАНІ ПОЗНАЧКИ: злитий коміт джерел $stamp; штамп build.txt $stamp; коміт збірки $BuildMain. Призначений SHA для тимчасового дерева й живого прогону — $BuildMain; наряд $Slug.`n"
    }
    $Text
}
