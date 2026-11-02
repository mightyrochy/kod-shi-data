#Requires -Version 5.1
<# Стенд наряду «обгортка-GPU-простій» (29.10): хибне «GPU зайнята», стенд без Main (main.cpl), мовчазний запобіжник.
Справжні функції обгортки; підмінено лише nvidia-smi, перелік позначок і замки. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('prostii-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$utf = New-Object Text.UTF8Encoding($false)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
$exeDir = Split-Path -Parent $SourceDir
$sideDir = Join-Path $SourceDir 'перевірка'

# --- (а) відеокарта зайнята за нестачі VRAM ----------------------------------------------------------------
Scenario 'а GPU' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    function Get-Command { [pscustomobject]@{ Source = 'nvidia-smi' } }
    function Get-GpuCounterRows { <# Запасне джерело — nvidia-smi; лічильник процесів міряє сценарії_gpu_процеси.ps1. #> $null }
    function Invoke-Native { param($Exe, $Arguments)
        [pscustomobject]@{ Code = $script:SmiCode; Out = "16376, $script:SmiFree, $script:SmiPercent" } }
    function Test-LockFree { $true }
    $LaneDir = $tmp
    $script:SmiCode = 0; $script:SmiFree = 16319; $script:SmiPercent = 0
    Check 'а AvastUI 57 MiB без обчислень — GPU вільна' ((Test-ExternalGpuFree) -and (Get-GpuBusyReason @()) -eq '')
    $script:SmiFree = 16376
    Check 'а порожня карта — вільна' (Test-ExternalGpuFree)
    $script:SmiFree = 2000
    $why = Get-GpuBusyReason @()
    Check "а бракує памʼяті — зайнята, причина числом: «$why»" (-not (Test-ExternalGpuFree) -and $why -match 'вільно 2000 з потрібних 8925 MiB')
    $script:SmiFree = 14000; $script:SmiPercent = 74
    $why = Get-GpuBusyReason @()
    Check 'а обчислення за достатньої памʼяті не блокують' ($why -eq '' -and (Test-ExternalGpuFree))
    $script:SmiCode = 9
    $why = Get-GpuBusyReason @()
    Check 'а nvidia-smi не відповів — зайнята, причина названа' ($why -match 'nvidia-smi' -and $script:GpuHoldReason -ceq 'nvidia-smi не відповів')
}

# --- (б) стенд без Main не викликає main.cpl --------------------------------------------------------------------------
Scenario 'б стенди' {
    $stub = Join-Path $tmp 'stub'
    [void][IO.Directory]::CreateDirectory($stub)
    $marker = Join-Path $tmp 'main-called.txt'
    # Заглушка Main у PATH: Windows знаходить її за PATHEXT (.CMD), як main.cpl; на Linux — виконуваний файл Main.
    [IO.File]::WriteAllText((Join-Path $stub 'Main.cmd'), ('@echo ran>"' + $marker + '"' + "`r`n"), [Text.Encoding]::ASCII)
    [IO.File]::WriteAllText((Join-Path $stub 'Main'), "#!/bin/sh`necho ran > '$marker'`n", $utf)
    if (-not $IsWindows -and $PSVersionTable.PSEdition -eq 'Core') { & chmod +x (Join-Path $stub 'Main') }
    $sep = [IO.Path]::PathSeparator
    $env:PATH = $stub + $sep + $env:PATH
    # Файл, що падає на завантаженні (параметр не конвертується) — як у стенді 29.10; файл без Main — так само.
    $broken = Join-Path $tmp 'зламаний.ps1'
    [IO.File]::WriteAllText($broken, "param([int]`$X)`nfunction Main { 0 }`n", $utf)
    $noMain = Join-Path $tmp 'безмейн.ps1'
    [IO.File]::WriteAllText($noMain, "param([string]`$Y)`n`$z = 1`n", $utf)
    $ps = (Get-Process -Id $PID).Path
    foreach ($side in @('side.ps1', 'side_claude.ps1', 'side_watch.ps1')) {
        foreach ($case in @(@('не завантажився', $broken, '{"X":"abc"}'), @('не визначив Main', $noMain, '{}'))) {
            Remove-Item -LiteralPath $marker -Force -ErrorAction SilentlyContinue
            $err = Join-Path $tmp 'err.txt'
            $argList = @('-NoProfile', '-NonInteractive')
            if ($env:OS -eq 'Windows_NT') { $argList += @('-ExecutionPolicy', 'Bypass') }
            $argList += @('-File', (Join-Path $sideDir $side), '-Script', $case[1], '-ArgsJson', $case[2])
            # Аргументи з лапками (JSON) дістаються процесу лише з екрануванням, інакше стенд бачить "{X:abc}".
            $argList = @($argList | ForEach-Object { '"' + ([string]$_ -replace '"', '\"') + '"' })
            $p = Start-Process -FilePath $ps -ArgumentList $argList -NoNewWindow -Wait -PassThru -RedirectStandardError $err -RedirectStandardOutput (Join-Path $tmp 'out.txt')
            $text = [IO.File]::ReadAllText($err, $utf)
            Check "б $side ($($case[0])) — провал з причиною, код $($p.ExitCode)" ($p.ExitCode -ne 0 -and $text.Contains($case[0]))
            Check "б $side ($($case[0])) — заглушка Main (main.cpl) не викликана" (-not (Test-Path -LiteralPath $marker))
        }
    }
}

# --- (в) запобіжник, що тримає позначки, сам пише один рядок -----------------------------------------------------------
Scenario 'в сигнал' {
    $work = Join-Path $tmp 'cr'; $box = Join-Path $tmp 'box'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir $box -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", $box, "$tmp/lanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"; $script:Limits = $null
    $send = { param($l) Add-Line $l }
    $rows = { @(Get-ChildItem -LiteralPath $box -Filter '*.txt' -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() }) }
    $age = { param([long]$Sec)
        $f = "$work/state/holds.json"
        $o = [IO.File]::ReadAllText($f, $utf) | ConvertFrom-Json
        foreach ($k in @($o.PSObject.Properties.Name)) { $o.$k.since = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - $Sec }
        [IO.File]::WriteAllText($f, ($o | ConvertTo-Json -Compress), $utf) }
    $held = { param($why, [int]$n) $h = @{}; for ($i = 0; $i -lt $n; $i++) { Add-Hold $h 'GPU' $why "gemini-queue/н$i/cc-m/1" }; $h }

    Update-HoldSignals (& $held 'процес chrome.exe' 2) $send
    Check 'в утримання щойно почалось (менше порога) — рядка нема' (@(& $rows).Count -eq 0)
    & $age 4000
    Update-HoldSignals (& $held 'процес chrome.exe' 2) $send
    $r = @(& $rows)
    Check "в понад поріг — рівно один рядок: $($r -join ' | ')" ($r.Count -eq 1 -and $r[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: процес chrome.exe, позначок 2')
    Update-HoldSignals (& $held 'процес chrome.exe' 2) $send
    Update-HoldSignals (& $held 'процес chrome.exe' 3) $send
    Check 'в повторний прохід (навіть з іншою кількістю позначок) — нових рядків нуль' (@(& $rows).Count -eq 1)
    Update-HoldSignals (& $held 'замок GPU іншого наряду' 1) $send
    Check 'в зміна причини — другий рядок' (@(& $rows).Count -eq 2)
    Update-HoldSignals @{} $send
    Check 'в утримання зникло — запис знято' (-not (Test-Path -LiteralPath "$work/state/holds.json"))
    Update-HoldSignals (& $held 'процес chrome.exe' 1) $send
    & $age 4000
    Update-HoldSignals (& $held 'процес chrome.exe' 1) $send
    Check 'в нове утримання після зняття сигналить знову' (@(& $rows).Count -eq 3)
    $h = @{}; Add-Hold $h 'SLOTS' 'слоти зайняті' 'gemini-queue/н/cc-m/1'
    Update-HoldSignals $h $send
    & $age 4000
    Update-HoldSignals $h $send
    Check 'в слоти — теж рядок' ((& $rows) -contains 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО SLOTS: слоти зайняті, позначок 1')

    # Рядки проходять шаблон публікатора: Add-Line вище вже відкинув би невідповідні шаблону claude_run.
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pubw" -OutboxDir "$tmp/pubo"
    $all = @(& $rows)
    $okPub = @($all | Where-Object { (Test-OutboxLine $_) -eq '' }).Count
    Check "в усі $($all.Count) рядки приймає й публікатор ($okPub)" ($all.Count -gt 0 -and $okPub -eq $all.Count)
    Check 'в чужий текст у причині шаблон відкидає' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: процес x; rm -rf, позначок 1') -ne '')
}

# --- (в2) планувальник: позначку з GPU тримає зайнята відеокарта, а не воркер --------------------------------------------
Scenario 'в планувальник' {
    $work = Join-Path $tmp 'cp'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/cpbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$tmp/lanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"
    $script:Limits = @{ slots = @{ claude = 2 }; source = 'код'; claude_laptop = @() }
    $m = [pscustomobject]@{ Valid = $true; Lane = 'claude'; Ref = 'gemini-queue/п/cc-claude-sonnet-5-5-medium/1/gpu'; Name = 'gemini-queue/п/cc-claude-sonnet-5-5-medium/1/gpu'
        Slug = 'п'; Model = 'cc-claude-sonnet-5-5-medium'; Sha = 'a' * 40; Time = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Gpu = $true; Prio = 5; Deadline = ''; N = '1'; Cond = 'gpu'; Seen = 0 }
    function Get-Markers { @($m) }
    function Get-OrderedMarkers($x) { @($x) }
    function Test-SlugBusy { $false }
    function Test-LockFree { $true }
    function Get-FreeSlot { 'claude-1' }
    $script:Started = 0
    function Start-Worker { $script:Started++; [pscustomobject]@{ Slot = 'claude-1'; Slug = 'п'; Gpu = $true; Marker = 'x'; Proc = [pscustomobject]@{ HasExited = $false } } }
    function Get-Command { [pscustomobject]@{ Source = 'nvidia-smi' } }
    function Get-GpuCounterRows { <# Запасне джерело — nvidia-smi; лічильник процесів міряє сценарії_gpu_процеси.ps1. #> $null }
    function Invoke-Native { param($Exe, $Arguments)
        if ($Arguments -contains '--query-gpu=memory.total,memory.free,utilization.gpu') { return [pscustomobject]@{ Code = 0; Out = $script:FakeTelemetry } }
        [pscustomobject]@{ Code = 0; Out = $script:FakeApps } }
    $script:FakeTelemetry = '16376, 2000, 74'; $script:FakeApps = '4120, C:\Users\x\chrome.exe'
    $w = New-Object System.Collections.ArrayList
    $r = Start-Markers $w
    Check 'в2 GPU зайнята процесом — воркер не запущено, позначка лишилась без узяття' ($script:Started -eq 0 -and $r[0] -eq 0 -and $script:Held['GPU'].Reason -ceq 'вільно 2000 з потрібних 8925 MiB; навантаження 74 %' -and $script:Held['GPU'].Markers.Count -eq 1)
    $script:FakeTelemetry = '16376, 16319, 0'; $script:FakeApps = ''
    $r = Start-Markers $w
    Check 'в2 GPU вільна — наряд узято' ($script:Started -eq 1 -and $r[0] -eq 1 -and -not $script:Held.ContainsKey('GPU'))
}

# --- (в3) gemini-run: ті самі утримання → рядок у out/alerts → публікатор кладе його у вихідні -------------------------
$g3out = Join-Path $tmp 'g3out'
Scenario 'в3 gemini-run' {
    $work = Join-Path $tmp 'g3'
    . (Join-Path $SourceDir 'gemini_run.ps1') -RepoDir $tmp -RepoUrl 'x' -RunsDir "$work/runs" -OutDir $g3out -LaneDir "$tmp/g3lanes" -AgyExe 'немає-cli' -ProfileDir $tmp
    foreach ($d in @("$work/runs", "$work/state", "$work/slots", $g3out, "$tmp/g3lanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"; $script:Limits = $null
    $script:HealthAlertDir = Join-Path $g3out 'alerts'
    $script:Lanes = @('agy', 'codex')
    $m = [pscustomobject]@{ Valid = $true; Lane = 'agy'; Ref = 'gemini-queue/п/gemini-3.8-flash-high/1/gpu'; Name = 'gemini-queue/п/gemini-3.8-flash-high/1/gpu'
        Slug = 'п'; Model = 'gemini-3.8-flash-high'; Sha = 'a' * 40; Time = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Gpu = $true; Prio = 5; Deadline = ''; N = '1'; Cond = 'gpu'; Seen = 0 }
    function Get-Markers { @($m) }
    function Get-NightlyMarker { @() }
    function Get-OrderedMarkers($x) { @($x) }
    function Test-SlugBusy { $false }
    function Test-LockFree { $true }
    function Get-Command { [pscustomobject]@{ Source = 'nvidia-smi' } }
    function Get-GpuCounterRows { <# Запасне джерело — nvidia-smi; лічильник процесів міряє сценарії_gpu_процеси.ps1. #> $null }
    function Invoke-Native { param($Exe, $Arguments)
        if ($Arguments -contains '--query-gpu=memory.total,memory.free,utilization.gpu') { return [pscustomobject]@{ Code = 0; Out = '16376, 2000, 74' } }
        [pscustomobject]@{ Code = 0; Out = '4120, C:\Users\x\chrome.exe' } }
    $w = New-Object System.Collections.ArrayList
    [void](Start-Markers $w)
    Check 'в3 GPU зайнята процесом — gemini-run не бере позначку й тримає GPU' ($script:Held['GPU'].Reason -ceq 'вільно 2000 з потрібних 8925 MiB; навантаження 74 %' -and $script:Held['GPU'].Markers.Count -eq 1)
    $send = { param($l) Add-HoldLine $l }
    Update-HoldSignals $script:Held $send
    $f = "$work/state/holds.json"
    $o = [IO.File]::ReadAllText($f, $utf) | ConvertFrom-Json
    foreach ($k in @($o.PSObject.Properties.Name)) { $o.$k.since = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 4000 }
    [IO.File]::WriteAllText($f, ($o | ConvertTo-Json -Compress), $utf)
    Update-HoldSignals $script:Held $send
    Update-HoldSignals $script:Held $send
    $rows = @(Get-ChildItem -LiteralPath "$g3out/alerts" -Filter '*.txt' -File -ErrorAction SilentlyContinue | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() })
    Check "в3 понад поріг — один рядок у out/alerts: $($rows -join ' | ')" ($rows.Count -eq 1 -and $rows[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: вільно 2000 з потрібних 8925 MiB; навантаження 74 %, позначок 1')
}
Scenario 'в3 публікатор' {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/g3pub" -OutDir $g3out -OutboxDir "$tmp/g3box"
    foreach ($d in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
    $script:HealthAlertDir = $OutboxDir   # як у Main публікатора
    Receive-HealthAlerts
    $rows = @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() })
    Check "в3 публікатор перекладає рядок рушія у вихідні для диспетчера: $($rows -join ' | ')" ($rows.Count -eq 1 -and $rows[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: вільно 2000 з потрібних 8925 MiB; навантаження 74 %, позначок 1' -and (Test-OutboxLine $rows[0]) -eq '')
    Receive-HealthAlerts
    Check 'в3 повторний імпорт — нових рядків нуль' (@(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' -File).Count -eq 1)
}

# --- (г) банер "понад 5 хв тому" ---------------------------------------------------------------------------------------
Scenario 'г банер' {
    $work = Join-Path $tmp 'cg'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/cgbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$tmp/gout")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"; $script:Limits = $null
    function Get-TaskRows { @() }
    function Get-HealthLines { @() }
    $body = Get-StatusBody
    Check 'г свіже тіло (оновлено щойно) не стверджує "Оновлено понад 5 хв тому"' ($body -cmatch '\*\*Ноутбук [^*]*\*\* · оновлено \d{4}-' -and $body -cnotmatch 'Оновлено понад 5 хв тому')
}

Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
if ($bad) { "ПОМИЛКА: провалів $bad"; exit 1 }
