#Requires -Version 5.1
<# Стенд наряду «обгортка-вивантаження-моделі» (31.10, редакція без вивантаження): GPU-позначки стояли через робочий стіл
Windows (уся відеопам'ять карти понад GpuIdleMiB), а модель LM Studio — інструмент прогонів, не сторонній процес (власник
31.10 ~21:33 UTC); «Позначки без старту» в #1856 — порожні клітинки; позначка не за форматом стояла мовчки. Справжні функції
обгортки; підмінено лише лічильник відеопам'яті процесів, nvidia-smi, Get-Process, перелік позначок і замки. Кожен виклик
Invoke-Native записано: обгортка не викликає `lms` (моделей не вивантажує). #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('gpuproc-' + [guid]::NewGuid().ToString('N'))
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

# Карта: процеси робочого столу (31.10 — ShellHost, CrossDeviceResume, оверлей NVIDIA) кожен під порогом, разом понад 512 MiB,
# і оверлей понад поріг сам; LM Studio — вікно (pid 7000) і рушій моделі з теки `~\.lmstudio` (pid 7100, 9000 MiB).
# Лічильник Windows дає байти на процес і адаптер.
$script:Names = @{ 7000 = 'LM Studio'; 7100 = 'node'; 5100 = 'ShellHost'; 5200 = 'CrossDeviceResume'; 5300 = 'NVIDIA Overlay'; 5400 = 'dwm'; 4120 = 'chrome'; 3300 = 'AvastUI' }
$script:Paths = @{ 7000 = 'C:\Users\x\AppData\Local\Programs\LM Studio\LM Studio.exe'; 7100 = 'C:\Users\x\.lmstudio\extensions\backends\llama.cpp-win-x86_64-nvidia-cuda12\llm_engine.node'
    4120 = 'C:\Program Files\Google\Chrome\Application\chrome.exe' }
$script:DesktopProcs = @(@{ Pid = 5100; MiB = 310 }, @{ Pid = 5200; MiB = 260 }, @{ Pid = 5300; MiB = 640 }, @{ Pid = 5400; MiB = 180 })
$script:ModelProcs = @(@{ Pid = 7000; MiB = 120 }, @{ Pid = 7100; MiB = 9000 })
$script:IdleProcs = @(@{ Pid = 3300; MiB = 57 })
$script:NoCounter = $false  # claude_run.ps1 вмикає Set-StrictMode: неініціалізована змінна — виняток
$fakes = {
    function Get-GpuCounterRows {
        if ($script:NoCounter) { return $null }
        , @(foreach ($p in @($script:Procs)) {
                [pscustomobject]@{ Name = "pid_$($p.Pid)_luid_0x00000000_0x0000D1B2_phys_0"; DedicatedUsage = [uint64]($p.MiB * 1MB) }
            })
    }
    function Get-Process { [CmdletBinding()] param([int]$Id) $n = $script:Names[$Id]; if (-not $n) { throw "процесу $Id нема" }; [pscustomobject]@{ ProcessName = $n; Path = [string]$script:Paths[$Id] } }
    function Get-Command { [pscustomobject]@{ Source = 'nvidia-smi' } }
    $script:NativeCalls = New-Object System.Collections.ArrayList
    function Invoke-Native { param([string]$Exe, [string[]]$Arguments, [string]$Dir = '', [double]$TimeoutMinutes = 10)
        [void]$script:NativeCalls.Add("$Exe $($Arguments -join ' ')")
        if ($Exe -ne 'nvidia-smi') { return [pscustomobject]@{ Code = 1; Out = ''; Err = 'стенд: лише nvidia-smi' } }
        if ($Arguments -contains '--query-gpu=memory.used') { $s = 0; foreach ($p in @($script:Procs)) { $s += $p.MiB }; return [pscustomobject]@{ Code = 0; Out = "$s" } }
        [pscustomobject]@{ Code = 0; Out = $script:Apps } }
    if ($null -eq $script:Bound) { $script:Bound = @{} }
    $script:Logged = New-Object System.Collections.ArrayList
    function Write-Log([string]$Text) { [void]$script:Logged.Add($Text) }
}
function Get-LmsCalls { @($script:NativeCalls | Where-Object { $_ -notlike 'nvidia-smi *' }) }

# --- (а) карту тримає лише робочий стіл ----------------------------------------------------------------------------------
Scenario 'а робочий стіл' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    function Test-LockFree { $true }
    $LaneDir = $tmp
    $script:Procs = $script:DesktopProcs + $script:IdleProcs; $script:Apps = '5100, C:\Windows\ShellHost.exe' + "`n" + '5200, C:\x\CrossDeviceResume.exe' + "`n" + '5300, C:\x\NVIDIA Overlay.exe'
    $why = Get-GpuBusyReason @()
    Check "а робочий стіл (4 процеси, разом 1390 MiB, оверлей 640) без навантаження — карту віддано: «$why»" ($why -eq '' -and (Test-ExternalGpuFree))
}

# --- (б) модель LM Studio і робочий стіл: позначку взято тим самим проходом, lms не викликано ------------------------------
Scenario 'б модель LM Studio' {
    $work = Join-Path $tmp 'cb'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/cbbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/cblanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$tmp/cblanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"
    $script:Limits = @{ slots = @{ claude = 2 }; source = 'код'; claude_laptop = @() }
    $mk = { param($slug, $cond) $n = "gemini-queue/$slug/cc-claude-sonnet-5-5-medium/1/$cond"
        [pscustomobject]@{ Valid = $true; Lane = 'claude'; Ref = $n; Name = $n; Slug = $slug; Model = 'cc-claude-sonnet-5-5-medium'; Sha = 'a' * 40
            Time = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Gpu = $true; Prio = 2; Deadline = ''; N = '1'; Cond = $cond; Seen = 0 } }
    $script:Marker = & $mk 'п' 'p2-gpu'
    function Get-Markers { @($script:Marker) }
    function Get-OrderedMarkers($x) { @($x) }
    function Test-SlugBusy { $false }
    function Test-LockFree { $true }
    function Get-FreeSlot { 'claude-1' }
    $script:Started = 0
    function Start-Worker { $script:Started++; [pscustomobject]@{ Slot = 'claude-1'; Slug = $script:Marker.Slug; Gpu = $true; Marker = $script:Marker.Name; Proc = [pscustomobject]@{ HasExited = $false } } }
    . $fakes
    $script:Procs = $script:DesktopProcs + $script:ModelProcs + $script:IdleProcs; $script:Apps = ''
    $r = Start-Markers (New-Object System.Collections.ArrayList)
    Check "б робочий стіл і модель LM Studio 9000 MiB — GPU-позначку взято тим самим проходом, утримання GPU нема: $($script:Logged -join ' | ')" ($script:Started -eq 1 -and $r[0] -eq 1 -and -not $script:Held.ContainsKey('GPU'))
    Check "б обгортка не викликала lms (моделей не вивантажує): $((Get-LmsCalls) -join ' | ')" (@(Get-LmsCalls).Count -eq 0 -and -not (Test-Path function:Invoke-GpuModelUnload))
    $script:Marker = & $mk 'Е2-вікно-переповнення' 'p3-gpu'
    $script:Started = 0
    $r = Start-Markers (New-Object System.Collections.ArrayList)
    Check 'б друга GPU-позначка (Е2-вікно-переповнення) за тієї самої карти — теж взято' ($script:Started -eq 1 -and $r[0] -eq 1)
}

# --- (в) живий власний GPU-наряд чи замок: карта зайнята -----------------------------------------------------------------
Scenario 'в власний наряд' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    $LaneDir = $tmp
    $script:Procs = $script:ModelProcs + $script:IdleProcs; $script:Apps = ''
    function Test-LockFree { $true }
    $own = @([pscustomobject]@{ Slot = 'claude-1'; Slug = 'п'; Gpu = $true; Marker = 'x'; Proc = [pscustomobject]@{ HasExited = $false } })
    $why = Get-GpuBusyReason $own
    Check "в живий власний GPU-наряд — другий не стартує: «$why»" ($why -ne '' -and @(Get-LmsCalls).Count -eq 0)
    function Test-LockFree { $false }
    $why = Get-GpuBusyReason @()
    Check "в замок GPU тримає наряд іншого облікового запису — не стартує: «$why»" ($why -ne '' -and @(Get-LmsCalls).Count -eq 0)
}

# --- (г) GPU-наряд за завантаженої моделі: воркер стартує, після кінця lms не викликано -----------------------------------
Scenario 'г воркер' {
    $work = Join-Path $tmp 'cg'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/cgbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/cglanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$tmp/cglanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"
    . $fakes
    $script:Procs = $script:DesktopProcs + $script:ModelProcs + $script:IdleProcs; $script:Apps = ''
    function Remove-Claim { }
    function Close-FailedStart { }
    function Get-TaskCopyDir { '' }
    function Set-BrowserGpuPolicy { }
    $script:Ran = 0
    function Invoke-Task { $script:Ran++ }
    $limits = [pscustomobject]@{ slots = [pscustomobject]@{ claude = 2 }; source = 'код' }
    $script:Job = [pscustomobject]@{ id = 'g-1'; slot = 'claude-1'; ref = 'gemini-queue/г/cc-claude-sonnet-5-5-medium/1/gpu'; name = 'gemini-queue/г/cc-claude-sonnet-5-5-medium/1/gpu'
        sha = 'b' * 40; time = 0; slug = 'г'; model = 'cc-claude-sonnet-5-5-medium'; n = '1'; cond = 'gpu'; claude = 'claude-sonnet-5-5'; effort = 'medium'
        gpu = $true; prio = 5; limits = $limits }
    $code = Invoke-Worker
    Check "г GPU-наряд за моделі LM Studio на карті — воркер пройшов перевірку GPU (код $code) і наряд виконано; lms не викликано: $((Get-LmsCalls) -join ' | '); журнал: $($script:Logged -join ' | ')" ($script:Ran -eq 1 -and $code -ne $script:WorkerGpuBusy -and @(Get-LmsCalls).Count -eq 0)
}

# --- (д) сторонній процес: позначка стоїть, причина з назвою й MiB -----------------------------------------------------
Scenario 'д сторонній процес' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    function Test-LockFree { $true }
    $LaneDir = $tmp; $script:StateDir = Join-Path $tmp 'd-state'; [void][IO.Directory]::CreateDirectory($script:StateDir)
    $script:Procs = @(@{ Pid = 4120; MiB = 2300 }) + $script:DesktopProcs + $script:ModelProcs + $script:IdleProcs; $script:Apps = '4120, C:\Users\x\chrome.exe'
    $why = Get-GpuBusyReason @()
    Check "д сторонній процес 2300 MiB поряд з робочим столом і моделлю — карту не віддано, причина лише з ним: «$why» / «$($script:GpuHoldReason)»" ($why -match 'зайнято 2300 MiB' -and $why -match 'chrome\.exe 2300 MiB' -and $script:GpuHoldReason -ceq 'процес chrome.exe 2300 MiB' -and -not (Test-ExternalGpuFree))
    $line = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: $($script:GpuHoldReason), позначок 1"
    Check "д рядок диспетчерові проходить шаблон: $line" (Test-HoldLine $line)
    Check "д lms не викликано: $((Get-LmsCalls) -join ' | ')" (@(Get-LmsCalls).Count -eq 0)
    # Сигнал запобіжника: MiB гуляють між проходами — повтору нема; змінилась назва — новий рядок.
    # Update-HoldSignals має свою змінну $sent: рядки — у змінній скрипта, щоб блок не підхопив її динамічно.
    $script:Limits = $null; $script:SentLines = New-Object System.Collections.ArrayList
    $send = { param($l) [void]$script:SentLines.Add($l); $true }
    $held = { param($why) $h = @{}; Add-Hold $h 'GPU' $why 'gemini-queue/н/cc-m/1/gpu'; $h }
    Update-HoldSignals (& $held 'процес chrome.exe 2300 MiB') $send
    $f = Join-Path $script:StateDir 'holds.json'
    $o = [IO.File]::ReadAllText($f, $utf) | ConvertFrom-Json
    $o.GPU.since = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 4000
    [IO.File]::WriteAllText($f, ($o | ConvertTo-Json -Compress), $utf)
    Update-HoldSignals (& $held 'процес chrome.exe 2300 MiB') $send
    Update-HoldSignals (& $held 'процес chrome.exe 2316 MiB') $send
    Update-HoldSignals (& $held 'процес game.exe 6100 MiB') $send
    $sent = @($script:SentLines)
    Check "д сигнал: один рядок на назву, зміна MiB не повторює: $($sent -join ' | ')" ($sent.Count -eq 2 -and $sent[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: процес chrome.exe 2300 MiB, позначок 1' -and $sent[1] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: процес game.exe 6100 MiB, позначок 1')
}

# --- (е) карта без лічильника процесів: memory.used і назви compute-apps -------------------------------------------------
Scenario 'е без лічильника' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    function Test-LockFree { $true }
    $LaneDir = $tmp; $script:NoCounter = $true
    $script:Procs = $script:DesktopProcs + $script:ModelProcs; $script:Apps = '7000, C:\Users\x\AppData\Local\Programs\LM Studio\LM Studio.exe' + "`n" + '5100, C:\Windows\ShellHost.exe'
    $why = Get-GpuBusyReason @()
    Check "е без лічильника: compute-apps називає лише LM Studio й робочий стіл — карту віддано: «$why»" ($why -eq '')
    $script:Procs += @(@{ Pid = 4120; MiB = 2300 }); $script:Apps += "`n" + '4120, C:\Users\x\chrome.exe'
    $why = Get-GpuBusyReason @()
    Check "е без лічильника: сторонній chrome.exe — карту не віддано, причина з назвою: «$why» / «$($script:GpuHoldReason)»" ($why -ne '' -and $script:GpuHoldReason -ceq 'процес chrome.exe')
    $script:NoCounter = $false
}

# --- (є) «Позначки без старту» в #1856: позначка, час і причина ----------------------------------------------------------
Scenario 'є позначки без старту' {
    $work = Join-Path $tmp 'ce'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/cebox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/ceout" -LaneDir "$tmp/celanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$tmp/ceout")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"
    $script:Logged = New-Object System.Collections.ArrayList
    function Write-Log([string]$Text) { [void]$script:Logged.Add($Text) }
    $skip = Join-Path $work 'skipped.json'
    $a = [pscustomobject]@{ Name = 'gemini-queue/автоживий-173ba2da/cc-claude-sonnet-5-5-medium/1/p2-gpu' }
    $b = [pscustomobject]@{ Name = 'gemini-queue/Е2-вікно-переповнення/cc-claude-sonnet-5-5-medium/1/p3-gpu' }
    Add-Skip $a 'GPU: зайнято 9990 MiB стороннім процесом (поріг 512)'; Add-Skip $b 'GPU: зайнято 9990 MiB стороннім процесом (поріг 512)'; Save-Skips $skip
    $rows = @(Read-NoteRows $skip @('marker', 'since', 'why'))
    $full = @($rows | Where-Object { $_[0] -like 'gemini-queue/*' -and $_[1] -ne '' -and $_[2] -like 'GPU:*' })
    Check "є дві позначки — два рядки таблиці з позначкою, часом і причиною: $(@($rows | ForEach-Object { $_ -join ' ; ' }) -join ' | ')" ($rows.Count -eq 2 -and $full.Count -eq 2)
    $since = @($rows | ForEach-Object { $_[1] })
    Start-Sleep -Seconds 1
    Add-Skip $a 'GPU: зайнято 9990 MiB стороннім процесом (поріг 512)'; Add-Skip $b 'GPU: зайнято 9990 MiB стороннім процесом (поріг 512)'; Save-Skips $skip
    $again = @(@(Read-NoteRows $skip @('marker', 'since', 'why')) | ForEach-Object { $_[1] })
    Check 'є та сама причина наступного проходу — since не зсувається, рядок журналу не повторюється' (($again -join ',') -ceq ($since -join ',') -and @($script:Logged | Where-Object { $_ -like '*не стартує*' }).Count -eq 2)
    [IO.File]::WriteAllText((Join-Path "$tmp/ceout" 'skipped.json'), '[]', $utf)
    Check 'є порожній файл іншого планувальника — жодного рядка' (@(Read-NoteRows (Join-Path "$tmp/ceout" 'skipped.json') @('marker', 'since', 'why')).Count -eq 0)
    $notes = Join-Path $work 'blocked-reasons.json'
    Add-Note $notes 'gemini/а' 'ЗАБЛОКОВАНО: перша'; Add-Note $notes 'gemini/б' 'ЗАБЛОКОВАНО: друга'
    $nr = @(Read-NoteRows $notes @('utc', 'marker', 'text'))
    Check "є причини BLOCKED — два рядки з наряду й тексту: $(@($nr | ForEach-Object { $_ -join ' ; ' }) -join ' | ')" ($nr.Count -eq 2 -and $nr[0][1] -ceq 'gemini/а' -and $nr[1][2] -ceq 'ЗАБЛОКОВАНО: друга')
}

# --- (ж) позначка не за форматом — рядок FORMAT раз ------------------------------------------------------------------------
$gout = Join-Path $tmp 'gzout'
Scenario 'ж FORMAT' {
    $work = Join-Path $tmp 'gz'
    . (Join-Path $SourceDir 'gemini_run.ps1') -RepoDir $tmp -RepoUrl 'x' -RunsDir "$work/runs" -OutDir $gout -LaneDir "$tmp/gzlanes" -AgyExe 'немає-cli' -ProfileDir $tmp
    foreach ($d in @("$work/runs", "$work/state", "$work/slots", $gout, "$tmp/gzlanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"; $script:Limits = $null
    $script:HealthAlertDir = Join-Path $gout 'alerts'
    $script:Lanes = @('agy', 'codex')
    $bad1 = [pscustomobject]@{ Valid = $false; Ref = 'refs/remotes/origin/gemini-queue/ВИМКНИ-НОУТБУК/cc-off/31102'; Name = 'gemini-queue/ВИМКНИ-НОУТБУК/cc-off/31102'; Sha = 'c' * 40; Time = 0; Slug = ''; Lane = '' }
    $bad2 = [pscustomobject]@{ Valid = $false; Ref = 'refs/remotes/origin/gemini-queue/ВИМКНИ-НОУТБУК/cc-off/31101'; Name = 'gemini-queue/ВИМКНИ-НОУТБУК/cc-off/31101'; Sha = 'd' * 40; Time = 0; Slug = ''; Lane = '' }
    # 31101 позначено старим станом INVALID_NAME (до рядка FORMAT) — рядок отримує так само раз.
    Write-FileAtomic (Get-StatePath (Get-MarkerKey $bad2)) 'INVALID_NAME'
    function Get-Markers { @($bad1, $bad2) }
    function Get-NightlyMarker { @() }
    function Write-Log([string]$Text) { }
    [void](Start-Markers (New-Object System.Collections.ArrayList))
    [void](Start-Markers (New-Object System.Collections.ArrayList))
    $rows = @(Get-ChildItem -LiteralPath "$gout/alerts" -Filter '*.txt' -File -ErrorAction SilentlyContinue | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() } | Sort-Object)
    Check "ж дві позначки не за форматом, два проходи — по рядку FORMAT на позначку: $($rows -join ' | ')" ($rows.Count -eq 2 -and $rows[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini-queue/ВИМКНИ-НОУТБУК/cc-off/31101 FORMAT' -and $rows[1] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini-queue/ВИМКНИ-НОУТБУК/cc-off/31102 FORMAT')
}
Scenario 'ж публікатор' {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/gzpub" -OutDir $gout -OutboxDir "$tmp/gzbox"
    foreach ($d in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
    $script:HealthAlertDir = $OutboxDir
    Receive-HealthAlerts
    $rows = @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' -File -ErrorAction SilentlyContinue | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() })
    Check "ж публікатор кладе рядки FORMAT у вихідні диспетчерові й будить: $($rows -join ' | ')" ($rows.Count -eq 2 -and @($rows | Where-Object { (Test-OutboxLine $_) -eq '' -and (Test-DispatcherAction $_) }).Count -eq 2)
}

Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
if ($bad -gt 0) { exit 1 }
exit 0
