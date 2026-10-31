#Requires -Version 5.1
<# Стенд наряду «обгортка-вивантаження-моделі» (31.10): GPU-позначки стояли через робочий стіл Windows (уся відеопам'ять
карти понад GpuIdleMiB) і модель LM Studio, яку ніхто не вивантажив; «Позначки без старту» в #1856 — порожні клітинки;
позначка не за форматом стояла мовчки. Справжні функції обгортки; підмінено лише лічильник відеопам'яті процесів, nvidia-smi,
назви процесів, перелік позначок, замки й CLI LM Studio — `fake_lms.py` іде справжнім процесом через Invoke-Native. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('vyvant-' + [guid]::NewGuid().ToString('N'))
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

# --- підробний lms: справжній процес у теці з ASCII-шляхом (cmd.exe читає .cmd в OEM-кодуванні) -------------------------
$onWin = ($env:OS -eq 'Windows_NT')
$pyName = $(if ($onWin) { 'python' } else { 'python3' })
$pyExe = @(Get-Command $pyName -CommandType Application -ErrorAction Stop)[0].Source
$lmsDir = Join-Path $tmp 'lms'
[void][IO.Directory]::CreateDirectory($lmsDir)
Copy-Item -LiteralPath (Join-Path (Join-Path $SourceDir 'перевірка') 'fake_lms.py') -Destination (Join-Path $lmsDir 'fake_lms.py')
if ($onWin) {
    $script:Lms = Join-Path $lmsDir 'lms.cmd'
    [IO.File]::WriteAllText($script:Lms, "@`"$pyExe`" `"$(Join-Path $lmsDir 'fake_lms.py')`" %*`r`n", [Text.Encoding]::ASCII)
} else {
    $script:Lms = Join-Path $lmsDir 'lms'
    [IO.File]::WriteAllText($script:Lms, "#!/bin/sh`nexec `"$pyExe`" `"$(Join-Path $lmsDir 'fake_lms.py')`" `"`$@`"`n", $utf)
    & chmod +x $script:Lms
}
$env:FAKE_LMS_STATE = Join-Path $tmp 'lms-state.json'
$env:FAKE_LMS_LOG = Join-Path $tmp 'lms-calls.txt'
Remove-Item Env:FAKE_LMS_NOJSON -ErrorAction SilentlyContinue

function Set-Models([string[]]$Names) {
    <# Моделі, «завантажені» в підробному LM Studio; журнал викликів lms — з нуля. #>
    $json = '[' + ((@($Names) | ForEach-Object { '"' + $_ + '"' }) -join ',') + ']'
    [IO.File]::WriteAllText($env:FAKE_LMS_STATE, $json, $utf)
    Remove-Item -LiteralPath $env:FAKE_LMS_LOG -Force -ErrorAction SilentlyContinue
}
function Test-ModelLoaded { (Test-Path -LiteralPath $env:FAKE_LMS_STATE) -and ([IO.File]::ReadAllText($env:FAKE_LMS_STATE, $utf).Trim() -ne '[]') }
function Get-LmsCalls { if (Test-Path -LiteralPath $env:FAKE_LMS_LOG) { @([IO.File]::ReadAllLines($env:FAKE_LMS_LOG, $utf)) } else { @() } }

# Карта: процеси робочого столу (31.10 — ShellHost, CrossDeviceResume, оверлей NVIDIA) кожен під порогом, разом понад 512 MiB;
# модель LM Studio (pid 7000) — 9000 MiB, поки підробний lms її тримає. Лічильник Windows дає байти на процес і адаптер.
$script:Names = @{ 7000 = 'LM Studio'; 5100 = 'ShellHost'; 5200 = 'CrossDeviceResume'; 5300 = 'NVIDIA Overlay'; 5400 = 'dwm'; 4120 = 'chrome'; 3300 = 'AvastUI' }
$script:DesktopProcs = @(@{ Pid = 5100; MiB = 310 }, @{ Pid = 5200; MiB = 260 }, @{ Pid = 5300; MiB = 240 }, @{ Pid = 5400; MiB = 180 })
$script:IdleProcs = @(@{ Pid = 3300; MiB = 57 })
function Get-CardProcs {
    $p = @($script:Procs)
    if (Test-ModelLoaded) { $p += @{ Pid = 7000; MiB = 9000 } }
    $p
}
$fakes = {
    function Get-GpuCounterRows {
        if ($script:NoCounter) { return $null }
        , @(foreach ($p in @(Get-CardProcs)) {
                [pscustomobject]@{ Name = "pid_$($p.Pid)_luid_0x00000000_0x0000D1B2_phys_0"; DedicatedUsage = [uint64]($p.MiB * 1MB) }
            })
    }
    function Get-Process { [CmdletBinding()] param([int]$Id) $n = $script:Names[$Id]; if (-not $n) { throw "процесу $Id нема" }; [pscustomobject]@{ ProcessName = $n } }
    function Find-LmsExe { $script:Lms }
    function Get-Command { [pscustomobject]@{ Source = 'nvidia-smi' } }
    $script:RealNative = ${function:Invoke-Native}
    function Invoke-Native { param([string]$Exe, [string[]]$Arguments, [string]$Dir = '', [double]$TimeoutMinutes = 10)
        if ($Exe -ne 'nvidia-smi') { return (& $script:RealNative $Exe $Arguments $Dir $TimeoutMinutes) }
        if ($Arguments -contains '--query-gpu=memory.used') { $s = 0; foreach ($p in @(Get-CardProcs)) { $s += $p.MiB }; return [pscustomobject]@{ Code = 0; Out = "$s" } }
        [pscustomobject]@{ Code = 0; Out = $script:Apps } }
    function Start-Sleep { }
    if ($null -eq $script:Bound) { $script:Bound = @{} }
    $script:Logged = New-Object System.Collections.ArrayList
    function Write-Log([string]$Text) { [void]$script:Logged.Add($Text) }
}

# --- (а) карту тримає лише робочий стіл ----------------------------------------------------------------------------------
Scenario 'а робочий стіл' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    function Test-LockFree { $true }
    $LaneDir = $tmp; $script:StateDir = Join-Path $tmp 'a-state'; [void][IO.Directory]::CreateDirectory($script:StateDir)
    $script:Procs = $script:DesktopProcs + $script:IdleProcs; $script:Apps = '5100, C:\Windows\ShellHost.exe' + "`n" + '5200, C:\x\CrossDeviceResume.exe' + "`n" + '5300, C:\x\NVIDIA Overlay.exe'
    Set-Models @()
    $why = Get-GpuBusyReason @()
    Check "а робочий стіл (4 процеси, разом 990 MiB, кожен під 512) без навантаження — карту віддано: «$why»" ($why -eq '' -and (Test-ExternalGpuFree))
    Check 'а карту з робочим столом віддано без звернення до LM Studio' ((Get-LmsCalls).Count -eq 0)
}

# --- (б) модель попереднього прогону: планувальник вивантажує й бере позначку тим самим проходом -------------------------
Scenario 'б залишена модель' {
    $work = Join-Path $tmp 'cb'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/cbbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/cblanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$tmp/cblanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"
    $script:Limits = @{ slots = @{ claude = 2 }; source = 'код'; claude_laptop = @() }
    $m = [pscustomobject]@{ Valid = $true; Lane = 'claude'; Ref = 'gemini-queue/п/cc-claude-sonnet-5-5-medium/1/p2-gpu'; Name = 'gemini-queue/п/cc-claude-sonnet-5-5-medium/1/p2-gpu'
        Slug = 'п'; Model = 'cc-claude-sonnet-5-5-medium'; Sha = 'a' * 40; Time = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Gpu = $true; Prio = 2; Deadline = ''; N = '1'; Cond = 'p2-gpu'; Seen = 0 }
    function Get-Markers { @($m) }
    function Get-OrderedMarkers($x) { @($x) }
    function Test-SlugBusy { $false }
    function Test-LockFree { $true }
    function Get-FreeSlot { 'claude-1' }
    $script:Started = 0
    function Start-Worker { $script:Started++; [pscustomobject]@{ Slot = 'claude-1'; Slug = $m.Slug; Gpu = $true; Marker = $m.Name; Proc = [pscustomobject]@{ HasExited = $false } } }
    . $fakes
    $script:Procs = $script:DesktopProcs + $script:IdleProcs; $script:Apps = ''
    Set-Models @('qwen/qwen3.5-9b')
    $w = New-Object System.Collections.ArrayList
    $r = Start-Markers $w
    $calls = @(Get-LmsCalls)
    Check "б модель 9000 MiB у LM Studio без власного GPU-наряду — lms unload викликано: $($calls -join ' | ')" ($calls -contains '["unload", "--all"]' -and -not (Test-ModelLoaded))
    Check "б рядок журналу з назвою моделі: $(@($script:Logged | Where-Object { $_ -like '*LM Studio*' }) -join ' | ')" (@($script:Logged | Where-Object { $_ -like '*вивантажено*qwen/qwen3.5-9b*' }).Count -eq 1)
    Check 'б GPU-позначку взято тим самим проходом, утримання GPU нема' ($script:Started -eq 1 -and $r[0] -eq 1 -and -not $script:Held.ContainsKey('GPU'))
}

# --- (в) живий власний GPU-наряд: модель не чіпаємо --------------------------------------------------------------------
Scenario 'в власний наряд' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    $LaneDir = $tmp; $script:StateDir = Join-Path $tmp 'v-state'; [void][IO.Directory]::CreateDirectory($script:StateDir)
    $script:Procs = $script:IdleProcs; $script:Apps = ''
    Set-Models @('mamaylm-gemma-3-12b-it-v2.0')
    function Test-LockFree { $true }
    $own = @([pscustomobject]@{ Slot = 'claude-1'; Slug = 'п'; Gpu = $true; Marker = 'x'; Proc = [pscustomobject]@{ HasExited = $false } })
    $why = Get-GpuBusyReason $own
    Check "в живий власний GPU-наряд — модель не вивантажено: «$why»" ($why -ne '' -and (Test-ModelLoaded) -and (Get-LmsCalls).Count -eq 0)
    function Test-LockFree { $false }
    $why = Get-GpuBusyReason @()
    Check "в замок GPU тримає наряд іншого облікового запису — модель не вивантажено: «$why»" ($why -ne '' -and (Test-ModelLoaded) -and (Get-LmsCalls).Count -eq 0)
}

# --- (г) кінець GPU-наряду за будь-якого підсумку — модель вивантажено ---------------------------------------------------
Scenario 'г кінець наряду' {
    $work = Join-Path $tmp 'cg'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/cgbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/cglanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$tmp/cglanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"
    . $fakes
    $script:Procs = $script:IdleProcs; $script:Apps = ''
    function Remove-Claim { }
    function Close-FailedStart { }
    function Get-TaskCopyDir { '' }
    function Set-BrowserGpuPolicy { }
    $limits = [pscustomobject]@{ slots = [pscustomobject]@{ claude = 2 }; source = 'код' }
    foreach ($case in @('ГОТОВО', 'збій')) {
        Set-Models @()
        $script:Case = $case
        # Наряд сам вантажить модель (як живий прогін) і кінчається успіхом чи винятком.
        function Invoke-Task { [IO.File]::WriteAllText($env:FAKE_LMS_STATE, '["qwen/qwen3.5-9b"]', $utf); if ($script:Case -eq 'збій') { throw 'наряд упав' } }
        $script:Job = [pscustomobject]@{ id = "g-$case"; slot = 'claude-1'; ref = 'gemini-queue/г/cc-claude-sonnet-5-5-medium/1/gpu'; name = 'gemini-queue/г/cc-claude-sonnet-5-5-medium/1/gpu'
            sha = 'b' * 40; time = 0; slug = 'г'; model = 'cc-claude-sonnet-5-5-medium'; n = '1'; cond = 'gpu'; claude = 'claude-sonnet-5-5'; effort = 'medium'
            gpu = $true; prio = 5; limits = $limits }
        $code = Invoke-Worker
        $calls = @(Get-LmsCalls)
        Check "г GPU-наряд скінчився ($case, код $code) — модель вивантажено: $($calls -join ' | ')" ($calls -contains '["unload", "--all"]' -and -not (Test-ModelLoaded))
    }
}

# --- (д) сторонній процес без моделі: позначка стоїть, причина з назвою й MiB ---------------------------------------------
Scenario 'д сторонній процес' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    function Test-LockFree { $true }
    $LaneDir = $tmp; $script:StateDir = Join-Path $tmp 'd-state'; [void][IO.Directory]::CreateDirectory($script:StateDir)
    $script:Procs = @(@{ Pid = 4120; MiB = 2300 }) + $script:IdleProcs; $script:Apps = '4120, C:\Users\x\chrome.exe'
    Set-Models @()
    $why = Get-GpuBusyReason @()
    Check "д сторонній процес 2300 MiB — карту не віддано, причина з назвою й MiB: «$why» / «$($script:GpuHoldReason)»" ($why -match 'chrome\.exe 2300 MiB' -and $script:GpuHoldReason -ceq 'процес chrome.exe 2300 MiB' -and -not (Test-ExternalGpuFree))
    $line = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: $($script:GpuHoldReason), позначок 1"
    Check "д рядок диспетчерові проходить шаблон: $line" (Test-HoldLine $line)
    Check "д LM Studio спитано, моделей нема — нічого не вивантажено: $((Get-LmsCalls) -join ' | ')" (@(Get-LmsCalls | Where-Object { $_ -like '*unload*' }).Count -eq 0 -and @($script:Logged | Where-Object { $_ -like '*моделей нема*' }).Count -eq 1)
    $n = (Get-LmsCalls).Count
    [void](Get-GpuBusyReason @())
    Check 'д той самий сторонній процес наступного проходу — LM Studio вдруге не питаємо' ((Get-LmsCalls).Count -eq $n -and @($script:Logged | Where-Object { $_ -like '*моделей нема*' }).Count -eq 1)
    # Сигнал запобіжника: MiB гуляють між проходами — повтору нема; змінилась назва — новий рядок.
    $script:Limits = $null; $sent = New-Object System.Collections.ArrayList
    $send = { param($l) [void]$sent.Add($l); $true }
    $held = { param($why) $h = @{}; Add-Hold $h 'GPU' $why 'gemini-queue/н/cc-m/1/gpu'; $h }
    Update-HoldSignals (& $held 'процес chrome.exe 2300 MiB') $send
    $f = Join-Path $script:StateDir 'holds.json'
    $o = [IO.File]::ReadAllText($f, $utf) | ConvertFrom-Json
    $o.GPU.since = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 4000
    [IO.File]::WriteAllText($f, ($o | ConvertTo-Json -Compress), $utf)
    Update-HoldSignals (& $held 'процес chrome.exe 2300 MiB') $send
    Update-HoldSignals (& $held 'процес chrome.exe 2316 MiB') $send
    Update-HoldSignals (& $held 'процес game.exe 6100 MiB') $send
    Check "д сигнал: один рядок на назву, зміна MiB не повторює: $($sent -join ' | ')" ($sent.Count -eq 2 -and $sent[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: процес chrome.exe 2300 MiB, позначок 1' -and $sent[1] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: процес game.exe 6100 MiB, позначок 1')
}

# --- (е) старіший lms без --json і карта без лічильника процесів ----------------------------------------------------------
Scenario 'е запасні шляхи' {
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    . $fakes
    function Test-LockFree { $true }
    $LaneDir = $tmp; $script:StateDir = Join-Path $tmp 'e-state'; [void][IO.Directory]::CreateDirectory($script:StateDir)
    $script:Procs = $script:IdleProcs; $script:Apps = ''
    $env:FAKE_LMS_NOJSON = '1'
    Set-Models @('qwen/qwen3.5-9b')
    $why = Get-GpuBusyReason @()
    Remove-Item Env:FAKE_LMS_NOJSON
    Check "е lms без ps --json — модель з текстового переліку вивантажено, карту віддано: «$why»" ($why -eq '' -and -not (Test-ModelLoaded) -and @($script:Logged | Where-Object { $_ -like '*вивантажено qwen/qwen3.5-9b*' }).Count -eq 1)
    $script:NoCounter = $true
    Set-Models @('qwen/qwen3.5-9b')
    $why = Get-GpuBusyReason @()
    $script:NoCounter = $false
    Check "е без лічильника процесів (лише memory.used карти) — модель вивантажено, карту віддано: «$why»" ($why -eq '' -and -not (Test-ModelLoaded))
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
