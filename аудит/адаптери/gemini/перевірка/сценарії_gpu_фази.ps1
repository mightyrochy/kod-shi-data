#Requires -Version 5.1
<# Стенд замка GPU лише на фази прогону з моделлю: агент позначає кінець фаз з моделлю (`аудит/проби/кінець_моделі.py`),
процес наряду на такті очікування (Wait-PowerPause → Exit-GpuModelPhase) відпускає оренду, файл слота — gpu=false; база й
підсумок ідуть без замка, інший GPU-наряд проходить ворота, сторож простою такого прогону не лічить, а наряд без позначки
тримає карту до кінця. Кінець процесу агента з деревом відпускає оренду до завершальних кроків наряду (д), а процес codex,
що після події кінця ходу не виходить, зупиняється з деревом на такті очікування (е). Справжні функції обгортки
(claude_run.ps1 і gemini_run.ps1 з queue_lanes.ps1, StrictMode), справжні замки-файли, процеси й прилади python; підмінено
перелік LM Studio (екземпляри в пам'яті, вивантаження за ID), пам'ять карти, батарею, журнал і рушій (codex_хід.py). #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('gpufazy-' + [guid]::NewGuid().ToString('N'))
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
$root = (Resolve-Path (Join-Path $SourceDir '../../..')).Path
$python = (Get-Command python).Source
function Invoke-Py([string[]]$ArgList) {
    <# Прилад python із середовищем цього процесу (змінна KINETS_MODELI, яку дала обгортка): код і весь вивід. #>
    $psi = New-Object Diagnostics.ProcessStartInfo $python
    $psi.Arguments = (@($ArgList | ForEach-Object { '"' + $_ + '"' })) -join ' '
    $psi.UseShellExecute = $false; $psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $utf; $psi.StandardErrorEncoding = $utf
    $psi.EnvironmentVariables['PYTHONUTF8'] = '1'; $psi.EnvironmentVariables['PYTHONIOENCODING'] = 'utf-8'
    $p = [Diagnostics.Process]::Start($psi)
    $out = $p.StandardOutput.ReadToEndAsync(); $err = $p.StandardError.ReadToEnd(); $p.WaitForExit()
    [pscustomobject]@{ Code = $p.ExitCode; Out = ($out.Result + $err).Trim() }
}
$mark = Join-Path $root 'аудит/проби/кінець_моделі.py'
$scene = Join-Path $root 'аудит/проби/записати_сцену.py'

# claude_run.ps1 без Main: свої теки стану, слотів, запусків і смуг; викликається з крапкою (`. $newEnv 'а'`), щоб функції лишились у сценарії.
$newEnv = {
    param([string]$Name)
    $work = Join-Path $tmp $Name
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$work-box" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$work/lanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$work/runs", "$work/lanes", "$work-box")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"; $script:RunRoot = "$work/runs"
    $script:Limits = @{ slots = @{ claude = 2 }; source = 'код'; claude_laptop = @(); gpu_stall_minutes = 90; gpu_stall_percent = 15 }
    $script:Lms = New-Object System.Collections.ArrayList
    [void]$script:Lms.Add([pscustomobject]@{ id = 'owner-id'; model = 'owner-model' })
    $script:Unloaded = New-Object System.Collections.ArrayList
    $script:Logged = New-Object System.Collections.ArrayList
    $script:GpuLease = $null; $script:ModelPhaseJob = $null
    Remove-Item Env:KINETS_MODELI -ErrorAction SilentlyContinue
    function Get-LmsInstances { @($script:Lms) }
    function Invoke-RestMethod { param([string]$Uri, [string]$Method, [string]$ContentType, $Body, [int]$TimeoutSec, $ErrorAction)
        $id = ($Body | ConvertFrom-Json).instance_id
        [void]$script:Unloaded.Add($id)
        foreach ($x in @($script:Lms | Where-Object { $_.id -ceq $id })) { $script:Lms.Remove($x) }
        [pscustomobject]@{ status = 'unloaded' } }
    function Test-ExternalGpuFree { param([switch]$LogAcquisition) $true }
    function Get-GpuLoad { [pscustomobject]@{ Reason = '' } }
    function Test-OnBattery { $false }
    function Write-Log([string]$Text, [switch]$Required) { [void]$script:Logged.Add($Text) }
}
# Допуск GPU-наряду, як його робить Invoke-Worker обох смуг: оренда, файл слота (gpu=true) і замок слота живого процесу.
# Без теки запуску — наряд, якому адреси позначки не дано (ручний чи давній шлях): замок до кінця прогону.
$admit = {
    param([string]$Id, [string]$Slug, [string]$Slot, [bool]$WithDir = $true)
    $dir = $(if ($WithDir) { Join-Path $script:RunRoot $Id } else { '' })
    if ($dir) { [void][IO.Directory]::CreateDirectory($dir) }
    $job = [pscustomobject]@{ id = $Id; dir = $dir; slot = $Slot; slug = $Slug; gpu = $true; name = "gemini-queue/$Slug/cc-claude-sonnet-5-5-medium/1/p2-gpu" }
    $why = Enter-GpuLease $job
    $lock = $null
    if (-not $why) {
        $lock = Open-Lock (Join-Path $script:SlotDir "$Slot.lock")
        Write-FileAtomic (Join-Path $script:SlotDir "$Slot.json") (([ordered]@{ slot = $Slot; lane = 'claude'; marker = $job.name; slug = $Slug
                    model = 'claude-sonnet-5-5 medium'; since = '2026-11-18T05:17:00Z'; gpu = $true; prio = 2; pid = $PID; copy = '' }) | ConvertTo-Json -Compress)
    }
    [pscustomobject]@{ Job = $job; Why = $why; Lease = $script:GpuLease; SlotLock = $lock }
}
$leases = { @((Read-GpuSession).Leases | Where-Object { -not $_.done } | ForEach-Object { $_.run }) -join ',' }
$slotGpu = { param([string]$Slot) [bool](@(Read-SlotInfo 'claude' | Where-Object { [string]$_.slot -ceq $Slot }) | ForEach-Object { $_.gpu }) }
$holders = { @(foreach ($s in @(Read-SlotInfo 'claude')) { if ($s.gpu) { [pscustomobject]@{ Marker = [string]$s.marker; Since = [string]$s.since } } }) }

# --- (а) кінець фаз з моделлю: база без замка, модель сцен вивантажено, сцени після позначки не пишуться --------------------
Scenario 'а база без замка' {
    . $newEnv 'а'
    $a = & $admit 'f-a' ('автоживий-' + 'a' * 40) 'claude-1'
    [void]$script:Lms.Add([pscustomobject]@{ id = 'gemma-a'; model = 'gemma' })
    $markPath = Join-Path $a.Job.dir 'kinets-modeli'
    Check "а допуск дав агентові адресу позначки в теці запуску: «$($a.Why)», KINETS_MODELI=$env:KINETS_MODELI" ($a.Why -eq '' -and $env:KINETS_MODELI -ceq $markPath -and -not (Test-Path -LiteralPath $markPath))
    Wait-PowerPause; Wait-PowerPause
    $why = Get-GpuBusyReason
    Check "а сцени: без позначки такти очікування оренди не чіпають — «$why», оренди $(& $leases)" ($null -ne $script:GpuLease -and $why -match 'тримає живий GPU-наряд' -and (& $leases) -ceq 'f-a' -and (& $slotGpu 'claude-1'))
    $r = Invoke-Py @($mark)
    Check "а прилад позначив кінець фаз з моделлю (код $($r.Code)): $($r.Out)" ($r.Code -eq 0 -and (Test-Path -LiteralPath $markPath) -and $r.Out.Contains('кінець фаз з моделлю позначено'))
    $script:Logged.Clear()
    Wait-PowerPause
    $why = Get-GpuBusyReason
    Check "а ПІСЛЯ: на такті очікування оренду відпущено, ворота вільні («$why»), запису сесії нема" ($null -eq $script:GpuLease -and $why -eq '' -and -not (Test-Path -LiteralPath (Join-Path $LaneDir 'gpu-models.json')) -and -not (Test-Path -LiteralPath (Get-GpuLeaseLockPath 'f-a')))
    Check "а модель сцен вивантажено, модель власника лишилась: [$($script:Unloaded -join ',')]" (($script:Unloaded -join ',') -ceq 'gemma-a' -and (@($script:Lms | ForEach-Object { $_.id }) -join ',') -ceq 'owner-id')
    Check "а файл слота — gpu=false, прогін іде далі в слоті; журнал: $($script:Logged -join ' | ')" (-not (& $slotGpu 'claude-1') -and @(Read-SlotInfo 'claude').Count -eq 1 -and @($script:Logged | Where-Object { $_ -like "GPU відпущено до кінця прогону $($a.Job.name): агент позначив кінець фаз з моделлю*" }).Count -eq 1)
    $out = Join-Path $tmp 'а-сцена'
    $r = Invoke-Py @($scene, 'збірка', 'кеш', $out, '--сцена', 'ж1')
    Check "а сцена після позначки — відмова до старту, теки нема (код $($r.Code)): $($r.Out)" ($r.Code -ne 0 -and $r.Out.Contains('ВІДМОВА: кінець фаз з моделлю вже позначено') -and -not (Test-Path -LiteralPath $out))
    $script:Unloaded.Clear()
    Exit-GpuLease $a.Job
    Check 'а кінець прогону після відпущеної оренди нічого не вивантажує й сесії не відкриває' ($script:Unloaded.Count -eq 0 -and -not (Test-Path -LiteralPath (Join-Path $LaneDir 'gpu-models.json')))
    $a.SlotLock.Dispose()
}

# --- (б) інший GPU-наряд бере карту під час бази першого; кінець першого оренди другого не чіпає -----------------------------
Scenario 'б інший наряд під час бази' {
    . $newEnv 'б'
    $a = & $admit 'f-a' ('автоживий-' + 'a' * 40) 'claude-1'
    [void]$script:Lms.Add([pscustomobject]@{ id = 'gemma-a'; model = 'gemma' })
    $b0 = & $admit 'f-b' 'Б.1-серія-2' 'claude-2'
    Check "б ДО позначки: другий GPU-наряд чекає — «$($b0.Why)», оренди $(& $leases)" ($b0.Why -match 'тримає живий GPU-наряд \(gemini-queue/автоживий-' -and (& $leases) -ceq 'f-a')
    $script:GpuLease = $a.Lease
    $null = Invoke-Py @($mark)
    Wait-PowerPause
    $b = & $admit 'f-b' 'Б.1-серія-2' 'claude-2'
    $onCard = @($script:Lms | ForEach-Object { $_.id }) -join ','
    Check "б ПІСЛЯ позначки: другий допущено («$($b.Why)»), оренди $(& $leases), на карті при допуску лише модель власника ($onCard)" ($b.Why -eq '' -and (& $leases) -ceq 'f-b' -and $onCard -ceq 'owner-id')
    [void]$script:Lms.Add([pscustomobject]@{ id = 'gemma-b'; model = 'gemma' })
    # Кінець прогону першого — у своєму процесі, де оренди вже нема (Invoke-Worker, finally → Exit-GpuLease).
    $script:Unloaded.Clear(); $script:GpuLease = $null
    Exit-GpuLease $a.Job
    $script:GpuLease = $b.Lease
    Check "б кінець першого не вивантажує модель другого й не закриває його оренди: [$($script:Unloaded -join ',')], оренди $(& $leases)" ($script:Unloaded.Count -eq 0 -and (& $leases) -ceq 'f-b' -and (Test-LeaseLive (Get-GpuLeaseLockPath 'f-b')))
    $why = Get-GpuBusyReason
    Check "б третій GPU-наряд чекає другого, як і раніше: «$why»" ($why -match 'тримає живий GPU-наряд \(gemini-queue/Б.1-серія-2/')
    Exit-GpuLease $b.Job
    Check "б кінець другого вивантажує його модель: [$($script:Unloaded -join ',')]" (($script:Unloaded -join ',') -ceq 'gemma-b' -and -not (Test-Path -LiteralPath (Join-Path $LaneDir 'gpu-models.json')))
    $a.SlotLock.Dispose(); $b.SlotLock.Dispose()
}

# --- (в) наряд без позначки (ручний, давній шаблон) і наряд, що позначки не поставив, тримають карту до кінця ----------------
Scenario 'в без позначки — як раніше' {
    . $newEnv 'в'
    $c = & $admit 'f-c' 'ручний-gpu-наряд' 'claude-1' $false
    $r = Invoke-Py @($mark)
    Check "в наряд без адреси позначки: змінної нема, прилад нічого не пише (код $($r.Code)): $($r.Out)" ($c.Why -eq '' -and -not $env:KINETS_MODELI -and $r.Code -eq 0 -and $r.Out.StartsWith('KINETS_MODELI нема') -and @(Get-ChildItem -LiteralPath $script:RunRoot -Recurse -File).Count -eq 0)
    foreach ($i in 1..3) { Wait-PowerPause }
    $d = & $admit 'f-d' 'Б.1-серія-2' 'claude-2'
    Check "в замок тримається весь прогін: оренда є, слот gpu=true, другий чекає — «$($d.Why)»" ($null -ne $script:GpuLease -and (& $slotGpu 'claude-1') -and $d.Why -match 'тримає живий GPU-наряд \(gemini-queue/ручний-gpu-наряд/' -and (& $leases) -ceq 'f-c')
    Exit-GpuLease $c.Job
    $c.SlotLock.Dispose(); Remove-Item -LiteralPath (Join-Path $script:SlotDir 'claude-1.json') -Force
    $e = & $admit 'f-e' ('автоживий-' + 'e' * 40) 'claude-1'
    foreach ($i in 1..3) { Wait-PowerPause }
    $d = & $admit 'f-d' 'Б.1-серія-2' 'claude-2'
    Check "в автоживий з адресою, що позначки не поставив: замок до кінця, другий чекає — «$($d.Why)»" ($e.Why -eq '' -and $null -ne $script:GpuLease -and (& $slotGpu 'claude-1') -and $d.Why -match 'тримає живий GPU-наряд' -and -not (Test-Path -LiteralPath (Join-Path $e.Job.dir 'kinets-modeli')))
    Exit-GpuLease $e.Job
    $d = & $admit 'f-d' 'Б.1-серія-2' 'claude-2'
    Check "в кінець прогону відпускає карту, як і раніше: «$($d.Why)»" ($d.Why -eq '' -and (& $leases) -ceq 'f-d')
    Exit-GpuLease $d.Job
    $e.SlotLock.Dispose(); $d.SlotLock.Dispose()
}

# --- (г) сторож простою: з замком прогін без chat-запитів дістав би вирок STALL; база без замка — не лічиться ----------------
Scenario 'г сторож під час бази' {
    . $newEnv 'г'
    $a = & $admit 'f-a' ('автоживий-' + 'a' * 40) 'claude-1'
    $send = { param($l) $true }
    $watch = Join-Path $script:StateDir 'gpu-watch.json'
    $verdict = Join-Path $LaneDir 'gpu-stall.json'
    $at = [datetime]::SpecifyKind([datetime]'2026-11-18T08:17:00', [DateTimeKind]::Utc)
    $h = @(& $holders)
    $w = Update-GpuWatch $h ([pscustomobject]@{ Percent = 0; OwnerPid = 0; CallAgeMin = 180 }) $send $watch $at
    Check "г ДО: замок на всю базу (180 хв без chat-запитів, поріг 90) — вирок STALL ($($w.NoCallMinutes) хв)" ($h.Count -eq 1 -and $w.Stop -and (Test-Path -LiteralPath $verdict) -and (Get-GpuStallVerdict).Marker -ceq $a.Job.name)
    $null = Invoke-Py @($mark)
    Wait-PowerPause
    $h = @(& $holders)
    $w = Update-GpuWatch $h ([pscustomobject]@{ Percent = 0; OwnerPid = 0; CallAgeMin = 180 }) $send $watch $at.AddMinutes(5)
    Check "г ПІСЛЯ позначки: тримачів замка нема ($($h.Count)), ряд і вирок знято — STALL посеред бази нема" ($h.Count -eq 0 -and $null -eq $w -and -not (Test-Path -LiteralPath $verdict) -and $null -eq (Get-GpuStallVerdict) -and -not (Test-Path -LiteralPath $watch))
    Exit-GpuLease $a.Job
    $a.SlotLock.Dispose()
}

# --- (д) процес агента закінчився: оренду відпущено до завершальних кроків наряду, не на кінці процесу наряду ---------------
Scenario 'д кінець агента' {
    . $newEnv 'д'
    $a = & $admit 'f-a' 'Річ-кадр-варіант-кадри' 'claude-1' $false
    [void]$script:Lms.Add([pscustomobject]@{ id = 'gemma-a'; model = 'gemma' })
    $script:Seen = New-Object System.Collections.ArrayList
    function Get-Prompt { 'наряд' }
    function Invoke-Claude { [void]$script:Seen.Add("агент: оренда=$($null -ne $script:GpuLease) слот-gpu=$(& $slotGpu 'claude-1')"); [pscustomobject]@{ Kind = 'STALL' } }
    function Complete-Task { [void]$script:Seen.Add("кінець: оренда=$($null -ne $script:GpuLease) слот-gpu=$(& $slotGpu 'claude-1') ворота=«$(Get-GpuBusyReason)»") }
    $runDir = Join-Path $script:RunRoot 'f-a'; [void][IO.Directory]::CreateDirectory($runDir)
    $M = [pscustomobject]@{ Name = $a.Job.name; Slug = 'Річ-кадр-варіант-кадри'; Claude = 'claude-sonnet-5-5'; Effort = '' }
    Invoke-ClaudeTask $M $a.Job 'claude' 'текст' '' $runDir 'стан' 'копія'
    $seen = $script:Seen -join ' | '
    Check "д під час агента оренда тримається, після нього — відпущена до кінця наряду, ворота вільні: $seen" ($script:Seen.Count -eq 2 -and $script:Seen[0] -ceq 'агент: оренда=True слот-gpu=True' -and $script:Seen[1] -ceq 'кінець: оренда=False слот-gpu=False ворота=«»')
    Check "д модель наряду вивантажено, журнал каже чому: [$($script:Unloaded -join ',')] $($script:Logged -join ' | ')" (($script:Unloaded -join ',') -ceq 'gemma-a' -and @($script:Logged | Where-Object { $_ -ceq "GPU відпущено до кінця прогону $($a.Job.name): процес агента з деревом закінчився, далі завершальні кроки без моделі" }).Count -eq 1)
    $script:Unloaded.Clear(); $script:Logged.Clear()
    Exit-GpuLease $a.Job; Exit-GpuAfterAgent $a.Job
    Check "д кінець процесу наряду й повторний виклик нічого не чіпають: [$($script:Unloaded -join ',')] $($script:Logged -join ' | ')" ($script:Unloaded.Count -eq 0 -and $script:Logged.Count -eq 0 -and -not (Test-Path -LiteralPath (Join-Path $LaneDir 'gpu-models.json')))
    $a.SlotLock.Dispose()
}

# --- (е) codex закінчив хід, а процес не виходить: зупинка з деревом на такті очікування, а не на виході процесу ------------
Scenario 'е codex після кінця ходу' {
    $work = Join-Path $tmp 'е'
    . (Join-Path $SourceDir 'gemini_run.ps1') -RepoDir $tmp -RepoUrl 'x' -RunsDir "$work/runs" -OutDir "$work/out" -LaneDir "$work/lanes" -AgyExe 'немає-cli' -ProfileDir $tmp
    foreach ($d in @("$work/runs", "$work/out", "$work/lanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:Logged = New-Object System.Collections.ArrayList
    function Write-Log([string]$Text, [switch]$Required) { [void]$script:Logged.Add($Text) }
    function Test-OnBattery { $false }
    # Рушій: подія кінця ходу, файл відповіді (коли не «-»), тоді живе ще $rest с — як закриття рушія під збоєм мережі.
    $fake = Join-Path $work 'codex_хід.py'
    [IO.File]::WriteAllText($fake, "import json, sys, time`nkind, done, rest = sys.argv[1], sys.argv[2], float(sys.argv[3])`nprint(json.dumps({'type': 'turn.started'}), flush=True)`nprint(json.dumps({'type': kind}), flush=True)`nif done != '-':`n    open(done, 'w', encoding='utf-8').write('ГОТОВО')`ntime.sleep(rest)`n", $utf)
    $turn = {
        param([string]$Kind, [string]$Write, [string]$DoneFile, [int]$Rest)
        $script:Logged.Clear()
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $r = Invoke-NativeUntilStall $python @($fake, $Kind, $Write, [string]$Rest) $work 10 (Join-Path $work "$Kind.jsonl") (Join-Path $work "$Kind.tsv") $DoneFile
        $left = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { [string]$_.CommandLine -like "*codex_хід.py*$Kind*" }).Count
        [pscustomobject]@{ Code = $r.Code; Stalled = $r.Stalled; Seconds = [int]$sw.Elapsed.TotalSeconds; Left = $left; Log = ($script:Logged -join ' | ') }
    }
    $f = & $turn 'turn.failed' '-' (Join-Path $work 'f.out.md') 600
    Check "е turn.failed, процес живе далі: зупинено за такт ($($f.Seconds) с з 600), код $($f.Code), лишків $($f.Left); $($f.Log)" ($f.Seconds -lt 300 -and $f.Code -eq 1 -and -not $f.Stalled -and $f.Left -eq 0 -and $f.Log -ceq 'codex: хід закінчено (turn.failed), процес не вийшов за такт очікування — зупинено з деревом')
    $done = Join-Path $work 'c.out.md'
    $c = & $turn 'turn.completed' $done $done 600
    Check "е turn.completed, файл відповіді є, процес живе далі: зупинено за такт ($($c.Seconds) с з 600), код $($c.Code), лишків $($c.Left)" ($c.Seconds -lt 300 -and $c.Code -eq 0 -and -not $c.Stalled -and $c.Left -eq 0 -and $c.Log -like 'codex: хід закінчено (turn.completed)*' -and [IO.File]::ReadAllText($done) -ceq 'ГОТОВО')
    $w = & $turn 'turn.completed' '-' (Join-Path $work 'w.out.md') 70
    Check "е turn.completed без файлу відповіді: чекає виходу процесу, як раніше ($($w.Seconds) с з 70), код $($w.Code), журнал «$($w.Log)»" ($w.Seconds -ge 70 -and $w.Code -eq 0 -and -not $w.Stalled -and $w.Log -eq '')
}

Remove-Item Env:KINETS_MODELI -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
if ($bad) { "ПОМИЛКА: провалів $bad"; exit 1 }
