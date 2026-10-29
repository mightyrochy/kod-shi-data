#Requires -Version 5.1
<#
.SYNOPSIS
Спільне для двох планувальників ноутбука — `gemini_run.ps1` (під `gemini`: смуги Codex і `agy`) і `claude_run.ps1` (під
власником: смуга Claude Code): позначки черги з пріоритетом і строком, смуги й слоти, межі з файла даних, атомарне узяття
позначки, чекання скидання квоти, замок GPU, копія задачі без тек-архівів і окремий процес на наряд.

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
    <# Число з JSON, обрізане до стелі [min, max]; не число — $null (тоді діє попереднє прийняте чи значення з коду). #>
    if ($Value -isnot [int] -and $Value -isnot [long] -and $Value -isnot [double] -and $Value -isnot [decimal]) { return $null }
    [Math]::Min([double]$Range[1], [Math]::Max([double]$Range[0], [double]$Value))
}

# Джерело межі (п.11): «власник ДД.ММ …» чи «вимір: …» з датою ДД.ММ і ще хоч одним числом (10970).
$script:LimitDateRx = '(?<![0-9])(?:0[1-9]|[12][0-9]|3[01])\.(?:0[1-9]|1[0-2])(?![0-9])'

function Test-LimitSource([string]$Text) {
    <# $true — у межі є джерело за форматом; інакше межа без джерела. Той самий розбір — у перевірка/перевірити_хеші.py. #>
    if ($Text.Length -gt 300 -or $Text -cmatch '[\x00-\x1f]') { return $false }
    if ($Text -cmatch ('\Aвласник ' + $script:LimitDateRx + '(?:[^0-9].*)?\z')) { return $true }
    if ($Text -cnotmatch '\Aвимір: ') { return $false }
    $d = [regex]::Match($Text, $script:LimitDateRx)
    $d.Success -and $Text.Remove($d.Index, $d.Length).Substring(6) -match '[0-9]'
}

function Get-LimitFields {
    <# Усі межі файла даних: слоти смуг і решта, у сталому порядку. #>
    @($script:LaneDefaults.Keys | ForEach-Object { "slots.$_" }) + @($script:Defaults.Keys | Sort-Object)
}

function Get-Limits {
    <# Межі смуг: `смуги.json` v2 з origin/main (не з робочої копії агента), обрізаний стелями.

    v2 — кожна межа `{"n": число, "джерело": "власник ДД.ММ …" | "вимір: … ДД.ММ"}`. Межа без джерела, v1 (міграція: числа
    без джерел), нема файла, кривий чи невідомий формат — попереднє прийняте значення (стан limits.json; нема — з коду), а
    поле — в unsourced для рядка «межа без джерела» стану ноутбука. Зміна файла в main діє на наступному проході без
    перевстановлення копій: читається він після `git fetch`, який перезаписує й origin/main, змінений у клоні. #>
    $l = @{ slots = [ordered]@{}; source = 'код'; unsourced = @() }
    foreach ($k in $script:LaneDefaults.Keys) { $l.slots[$k] = $script:LaneDefaults[$k] }
    foreach ($k in $script:Defaults.Keys) { $l[$k] = $script:Defaults[$k] }
    # Без теки стану (читач меж поза планувальником) попереднє не зберігається.
    $sd = $(try { [string]$script:StateDir } catch { '' })
    $prevPath = $(if ($sd) { Join-Path $sd 'limits.json' } else { '' })
    $prev = $null
    if ($prevPath -and (Test-Path -LiteralPath $prevPath)) { try { $prev = [System.IO.File]::ReadAllText($prevPath, $script:Utf8) | ConvertFrom-Json } catch { $null = $_ } }
    $doc = $null
    $r = Invoke-Git @('cat-file', 'blob', "refs/remotes/origin/main:$script:LanesPath") -AllowFail
    if ($r.Code -eq 0 -and $r.Out.Length -le 8192) {
        try { $doc = $r.Out | ConvertFrom-Json } catch { Write-Log 'смуги.json не читається як JSON — попередні межі' }
    }
    if ($null -ne $doc) { $l.source = 'origin/main' }
    $v2 = $null -ne $doc -and [string](Get-JsonProp $doc 'v') -eq '2'
    $accepted = [ordered]@{}
    foreach ($f in @(Get-LimitFields)) {
        $lane = $(if ($f.StartsWith('slots.')) { $f.Substring(6) } else { '' })
        $range = $(if ($lane) { $script:Ceil.slots } else { $script:Ceil[$f] })
        $node = $null
        if ($v2) { $node = $(if ($lane) { Get-JsonProp (Get-JsonProp $doc 'slots') $lane } else { Get-JsonProp $doc $f }) }
        $v = $null
        if (Test-LimitSource ([string](Get-JsonProp $node 'джерело'))) { $v = ConvertTo-Bounded (Get-JsonProp $node 'n') $range }
        if ($null -eq $v) {
            $l.unsourced += $f
            $v = ConvertTo-Bounded (Get-JsonProp $prev $f) $range
        }
        if ($null -eq $v) { continue }
        $accepted[$f] = $v
        if ($lane) { $l.slots[$lane] = [int][Math]::Floor($v) } else { $l[$f] = $v }
    }
    $text = $accepted | ConvertTo-Json -Compress
    $old = $(if ($prevPath -and (Test-Path -LiteralPath $prevPath)) { [System.IO.File]::ReadAllText($prevPath, $script:Utf8) } else { '' })
    if ($prevPath -and $accepted.Count -gt 0 -and $text -cne $old) { Write-FileAtomic $prevPath $text }
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

# --- здоров'я машини (лише показ, узяття не гейтить) ----------------------------------------------------------------

function Get-DirBytes([string]$Path) {
    <# Розмір названої теки без переходу за точками з'єднання (профіль має петлі); недоступні теки — лічбою Skipped. #>
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Container)) { return $null }
    $bytes = 0L; $skipped = 0
    $stack = New-Object System.Collections.Stack
    $stack.Push((New-Object System.IO.DirectoryInfo $Path))
    while ($stack.Count -gt 0) {
        $d = $stack.Pop()
        try {
            foreach ($e in $d.EnumerateFileSystemInfos()) {
                if ($e.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { continue }
                if ($e -is [System.IO.DirectoryInfo]) { $stack.Push($e) } else { $bytes += $e.Length }
            }
        } catch { $skipped++ }
    }
    [pscustomobject]@{ Bytes = $bytes; Skipped = $skipped }
}

function Get-MarkerKind([string]$Slug) {
    <# Вид позначки за назвою наряду — для лічби в стані. #>
    if ($Slug -cmatch '^автоперевірка-') { return 'автоперевірка' }
    if ($Slug -cmatch '^автоживий-') { return 'автоживий' }
    if ($Slug -cmatch '^Е1-нічний-живий-') { return 'нічний живий' }
    if ($Slug -cmatch '^перевірка-') { return 'перевірка' }
    if ($Slug -cmatch '^pachka-') { return 'пачка' }
    if ($Slug -ceq 'ВИМКНИ-НОУТБУК') { return 'вимкнення' }
    'наряд'
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

# Теки `аудит/` від третього рівня з відстежуваними файлами від 8 МіБ — архіви прогонів, проб і перевірок: копія задачі
# їх не викладає (main 29.10: 29 тек, у копії 247 МБ із 1353). Тека, названа в наряді, лишається; іншу сесія додає
# сама — `git sparse-checkout add '/<тека>/'`.
$script:ArchiveDirBytes = 8MB
$script:TaskCopy = $null

function Get-ArchiveDirs([string]$Commit, [string]$TaskText) {
    <# Теки-архіви коміту згори вниз; частковий клон не міряємо: `ls-tree -l` довантажив би всі об'єкти. #>
    if ((Invoke-Git @('config', '--get', 'remote.origin.promisor') -AllowFail).Out.Trim() -eq 'true') { return }
    $r = Invoke-Git @('ls-tree', '-r', '-l', '-z', $Commit, '--', 'аудит') -AllowFail
    if ($r.Code -ne 0) { return }
    $size = New-Object 'System.Collections.Generic.Dictionary[string,long]' ([StringComparer]::Ordinal)
    foreach ($e in $r.Out.Split([char]0)) {
        if ($e -notmatch '^[0-7]{6} blob [0-9a-f]{40,64} +([0-9]+)\t(.+)$') { continue }
        $bytes = [long]$Matches[1]; $path = $Matches[2]; $i = -1; $depth = 0
        while (($i = $path.IndexOf('/', $i + 1)) -ge 0) {
            $depth++
            if ($depth -lt 3) { continue }
            $d = $path.Substring(0, $i); $v = 0L
            [void]$size.TryGetValue($d, [ref]$v); $size[$d] = $v + $bytes
        }
    }
    $named = @(foreach ($m in [regex]::Matches($TaskText, '`([^`\r\n]+)`')) { (($m.Groups[1].Value.Trim() -replace '\\', '/') -replace '^\./', '').TrimEnd('/') })
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($d in @($size.Keys | Where-Object { $size[$_] -ge $script:ArchiveDirBytes } | Sort-Object { $_.Split('/').Count }, { $_ })) {
        $keep = $false
        foreach ($x in $out) { if ($d.StartsWith($x + '/', [StringComparison]::Ordinal)) { $keep = $true } }
        foreach ($n in $named) { if ($n -ceq $d -or $n.StartsWith($d + '/', [StringComparison]::Ordinal)) { $keep = $true } }
        if (-not $keep) { $out.Add($d) }
    }
    $out
}

function ConvertTo-SparseSkip([string]$Dir) {
    <# Шаблон sparse-checkout (синтаксис .gitignore), що не викладає теку; спецсимволи шаблону екрановано. #>
    '!/' + ($Dir -replace '([\\*?\[])', '\$1') + '/'
}

function New-TaskCopy([string]$Dir, [string]$Commit, [string]$TaskText) {
    <# Тека задачі: `repo` — git worktree клону (спільні об'єкти й посилання) без тек-архівів, `tmp` — TEMP і TMP процесу
    наряду та його нащадків. Далі git і рушій працюють у копії ($RepoDir); повертає її шлях, закриває Close-TaskCopy. #>
    $repo = Join-Path $Dir 'repo'; $tmp = Join-Path $Dir 'tmp'
    [void][IO.Directory]::CreateDirectory($tmp)
    $script:TaskCopy = @{ Dir = $Dir; Clone = $RepoDir; Temp = $env:TEMP; Tmp = $env:TMP }
    [void](Invoke-Git @('worktree', 'prune') -AllowFail)
    [void](Invoke-Git @('worktree', 'add', '-q', '-f', '--no-checkout', '--detach', $repo, $Commit))
    # sparse-checkout у worktree лише з git 2.36: раніший писав `core.sparseCheckout` у спільний конфіг клону, а
    # `--no-cone` з'явився в 2.35. Старіший git — копія повна, але так само прибирається після доставки.
    $v = [regex]::Match([string](Invoke-Git @('version') -AllowFail).Out, '([0-9]+)\.([0-9]+)')
    $skip = @()
    if ($v.Success -and [int]$v.Groups[1].Value * 1000 + [int]$v.Groups[2].Value -ge 2036) {
        $skip = @(Get-ArchiveDirs $Commit $TaskText)
        $sp = Invoke-Git (@('sparse-checkout', 'set', '--no-cone', '/*') + @(foreach ($d in $skip) { ConvertTo-SparseSkip $d })) -AllowFail -Dir $repo
        if ($sp.Code -ne 0) {
            Write-Log "копія задачі: sparse-checkout не вдався — повна ($($sp.Err.Trim()))"
            [void](Invoke-Git @('sparse-checkout', 'disable') -AllowFail -Dir $repo)
            $skip = @()
        }
    } else { Write-Log "копія задачі: git до 2.36 — повна ($([string]$v.Value))" }
    [void](Invoke-Git @('reset', '-q', '--hard') -Dir $repo)
    Set-Variable -Scope Script -Name RepoDir -Value $repo
    $env:TEMP = $tmp; $env:TMP = $tmp
    Write-Log "копія задачі $repo ($Commit): тек-архівів не викладено — $($skip.Count)"
    $repo
}

function Get-TaskDirText([string]$TaskDir) {
    <# Рядок промпту про теку задачі (без теки — ''). #>
    if (-not $TaskDir) { return '' }
    "Тека задачі — ``$TaskDir``: робоча копія ``repo`` (поточна тека) і ``tmp`` (туди вже вказують TEMP і TMP). Клонів`n" +
    "і копій репозиторію поза нею не роби; теки-архіви ``аудит/`` не викладено — потрібну додай ``git sparse-checkout add '/<тека>/'``.`n" +
    "Після кінця прогону обгортка теку прибирає: лишається лише закомічене."
}

function Close-TaskCopy([string[]]$Delivered) {
    <# Після доставки: $RepoDir і TEMP/TMP — як до копії, копія — геть (Remove-TaskCopy). Повертає шлях теки, що
    лишилась із недоставленими комітами, або ''. #>
    $c = $script:TaskCopy
    if ($null -eq $c) { return '' }
    $script:TaskCopy = $null
    Set-Variable -Scope Script -Name RepoDir -Value $c.Clone
    $env:TEMP = $c.Temp; $env:TMP = $c.Tmp
    Remove-TaskCopy $c.Dir $Delivered
}

function Remove-TaskCopy([string]$Dir, [string[]]$Delivered) {
    <# Тека задачі чи давня робоча копія слота — геть, коли голова не несе комітів поза $Delivered (`rev-list --not`).
    Несе — тека лишається з `kept.txt`, гілку звільнено, повертає шлях теки; інакше ''. #>
    $repo = $(if (Test-Path -LiteralPath (Join-Path $Dir '.git')) { $Dir } else { Join-Path $Dir 'repo' })
    if (Test-Path -LiteralPath (Join-Path $repo '.git')) {
        $n = 0
        $r = Invoke-Git (@('rev-list', '--count', 'HEAD', '--not') + $Delivered) -AllowFail -Dir $repo
        if ($r.Code -eq 0 -and [int]::TryParse($r.Out.Trim(), [ref]$n) -and $n -gt 0) {
            [void](Invoke-Git @('checkout', '-q', '--detach') -AllowFail -Dir $repo)
            [IO.File]::WriteAllText((Join-Path $Dir 'kept.txt'), "недоставлених комітів голови: $n`n", $script:Utf8)
            Write-Log "копія задачі $Dir лишається: недоставлених комітів голови $n"
            return $Dir
        }
        [void](Invoke-Git @('worktree', 'remove', '-f', '-f', $repo) -AllowFail)
    }
    if (Test-Path -LiteralPath $Dir) {
        try { Remove-Item -LiteralPath $Dir -Recurse -Force -ErrorAction Stop } catch { Write-Log "копія задачі $Dir не прибрана: $($_.Exception.Message)" }
    }
    [void](Invoke-Git @('worktree', 'prune') -AllowFail)
    ''
}

function Clear-TaskCopies([string]$Root, [string[]]$Delivered) {
    <# Накопичене під $Root: копії задач і давні робочі копії слотів, яких не тримає зайнятий слот (замок і `copy` у
    `<слот>.json`) і без `kept.txt`, — геть за Remove-TaskCopy. Теки читаються до замків: нова копія з'являється вже
    після запису `<слот>.json`. #>
    $dirs = @(Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue)
    $busy = @{}
    foreach ($l in @(Get-ChildItem -LiteralPath $script:SlotDir -Filter '*.lock' -File -ErrorAction SilentlyContinue)) {
        if (Test-LockFree $l.FullName) { continue }
        $slot = [IO.Path]::GetFileNameWithoutExtension($l.Name)
        $busy[$slot] = $true
        try {
            $copy = [string](Get-JsonProp ([IO.File]::ReadAllText((Join-Path $script:SlotDir "$slot.json"), $script:Utf8) | ConvertFrom-Json) 'copy')
            if ($copy) { $busy[(Split-Path -Leaf $copy)] = $true }
        } catch { $null = $_ }
    }
    foreach ($d in $dirs) {
        if ($busy.ContainsKey($d.Name) -or (Test-Path -LiteralPath (Join-Path $d.FullName 'kept.txt'))) { continue }
        Write-Log "накопичене: $($d.FullName) прибирається"
        [void](Remove-TaskCopy $d.FullName $Delivered)
    }
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
