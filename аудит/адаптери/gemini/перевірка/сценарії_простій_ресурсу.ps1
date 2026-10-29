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

# --- (а) відеокарта зайнята лише справжнім навантаженням ----------------------------------------------------------------
Scenario 'а GPU' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    function Get-Command { [pscustomobject]@{ Source = 'nvidia-smi' } }
    function Invoke-Native { [pscustomobject]@{ Code = $script:SmiCode; Out = $script:SmiOut } }
    $script:SmiCode = 0
    $script:SmiOut = '6320, C:\Program Files\Avast Software\Avast\AvastUI.exe, N/A'
    Check 'а єдиний процес без пам''яті (AvastUI.exe, N/A) — GPU вільна, наряд береться' (Test-ExternalGpuFree)
    $script:SmiOut = '6320, C:\Program Files\Avast Software\Avast\AvastUI.exe, [N/A]' + "`n" + '7000, C:\x\app.exe, [Not Supported]'
    Check 'а [N/A] і [Not Supported] — вільна' (Test-ExternalGpuFree)
    $script:SmiOut = ''
    Check 'а порожній перелік — вільна' (Test-ExternalGpuFree)
    $script:SmiOut = '4120, C:\Users\x\small.exe, 57'
    Check 'а 57 МБ (спокій відеокарти, вимір 29.10) — вільна' (Test-ExternalGpuFree)
    $script:SmiOut = '6320, C:\Program Files\Avast Software\Avast\AvastUI.exe, N/A' + "`n" + '4120, C:\Users\x\chrome.exe, 2048'
    $free = Test-ExternalGpuFree
    Check "а процес із пам'яттю 2048 МБ — зайнята, назва в причині: «$script:GpuBusyBy»" (-not $free -and $script:GpuBusyBy -ceq 'процес chrome.exe')
    $script:SmiOut = '4120, C:\a b\dwm, evil;rm.exe, 900'
    $free = Test-ExternalGpuFree
    Check "а назва процесу з комою й зайвими знаками стає безпечною: «$script:GpuBusyBy»" (-not $free -and $script:GpuBusyBy -cmatch '^процес [A-Za-z0-9._+-]{1,92}$')
    $script:SmiCode = 9; $script:SmiOut = ''
    $free = Test-ExternalGpuFree
    Check 'а nvidia-smi не відповів — зайнята, причина названа' (-not $free -and $script:GpuBusyBy -ceq 'nvidia-smi не відповів')
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
    function Test-ExternalGpuFree { $script:GpuBusyBy = $script:FakeBy; -not $script:FakeBy }
    $script:FakeBy = 'процес chrome.exe'
    $w = New-Object System.Collections.ArrayList
    $r = Start-Markers $w
    Check 'в2 GPU зайнята процесом — воркер не запущено, позначка лишилась без узяття' ($script:Started -eq 0 -and $r[0] -eq 0 -and $script:Held['GPU'].Reason -ceq 'процес chrome.exe' -and $script:Held['GPU'].Markers.Count -eq 1)
    $script:FakeBy = ''
    $r = Start-Markers $w
    Check 'в2 GPU вільна — наряд узято' ($script:Started -eq 1 -and $r[0] -eq 1 -and -not $script:Held.ContainsKey('GPU'))
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
