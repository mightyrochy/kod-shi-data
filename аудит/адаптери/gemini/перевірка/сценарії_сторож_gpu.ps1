#Requires -Version 5.1
<# Стенд наряду «обгортка-сторож-gpu-замка» (15.11): GPU-наряд тримає замок 640 хв, карта на 0 %, PID сервера щоп'ять хвилин
новий, а запобіжник завислості мовчить; наглядова сесія не підтверджує листів, а стан ноутбука цього не показує.
Справжні функції обгортки (Update-GpuWatch, Get-GpuStateLines, Get-SupervisorLine, публікатор); підмінено лише вимір карти й
час. Git для рядка наглядової — справжній, на тимчасовому origin. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('storozh-' + [guid]::NewGuid().ToString('N'))
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
$marker = 'gemini-queue/Е1-нічний-живий-20261115/gpt-6.1-sol-high/1/gpu-p8'
$other = 'gemini-queue/Річ-колір-межі-свідок-вставки/gpt-6.1-sol-high/2/gpu-p8'
$day = [datetime]::SpecifyKind([datetime]'2026-11-15T00:00:00', [DateTimeKind]::Utc)
function At([int]$H, [int]$M) { $day.AddHours($H).AddMinutes($M) }

# claude_run.ps1 без Main: свої теки стану, слотів і вихідних; викликається з крапкою (`. $newEnv 'a'`), щоб функції лишились у сценарії.
$newEnv = {
    param([string]$Name)
    $work = Join-Path $tmp $Name; $box = Join-Path $tmp "$Name-box"
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir $box -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", $box, "$tmp/lanes", "$tmp/gout")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"
    $script:Limits = @{ slots = @{ claude = 2 }; source = 'код'; claude_laptop = @(); gpu_stall_minutes = 90; gpu_stall_percent = 15 }
    $script:TestBox = $box
}
# Події сну, як їх веде публікатор (`sleep-events.json`): сон 11:30–15:29 UTC (Power-Troubleshooter/1) і не-сон «вимкнено й запущено» 06:00–06:30.
[void][IO.Directory]::CreateDirectory("$tmp/pub")
[IO.File]::WriteAllText("$tmp/pub/sleep-events.json", (@{ read_utc = '2099-01-01T00:00:00.0000000+00:00'; events = @(
    @{ key = 'a'; from = '2026-11-15T11:30:00.0000000+00:00'; to = '2026-11-15T15:29:00.0000000+00:00'; source = 'Power-Troubleshooter/1'; announced = $true },
    @{ key = 'b'; from = '2026-11-15T06:00:00.0000000+00:00'; to = '2026-11-15T06:30:00.0000000+00:00'; source = 'heartbeat/boot'; announced = $true }) } | ConvertTo-Json -Depth 5 -Compress), $utf)
function Read-Box { @(Get-ChildItem -LiteralPath $script:TestBox -Filter '*.txt' -File -ErrorAction SilentlyContinue | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() }) }

# --- (а) сьогоднішній випадок: замок тримається, карта 0 %, PID міняється; перед тим — сон ноутбука -------------------------------
Scenario 'а випадок 15.11' {
    . $newEnv 'a'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T09:00:00Z' })
    $tick = { param([int]$Min, [int]$Pct, [int]$OwnerPid, [int]$Call = 120) Update-GpuWatch $holder ([pscustomobject]@{ Percent = $Pct; OwnerPid = $OwnerPid; CallAgeMin = $Call }) $send "$tmp/a/state/gpu-watch.json" $day.AddMinutes($Min) { param($f, $t) Get-SleepOverlap $f $t } }
    # ДО: запобіжник утримань (Update-HoldSignals) бачить лише позначки, що не стартують, — наряд, що йде, рядка не дає.
    Update-HoldSignals @{} $send
    Check 'а ДО: наявний запобіжник за цього випадку мовчить — рядків 0' (@(Read-Box).Count -eq 0)
    # Робота до сну (11:00, 11:05), сон ноутбука без вимірів до 15:35, далі карта працює до 19:35.
    [void](& $tick (11 * 60) 60 30000); [void](& $tick (11 * 60 + 5) 60 30000)
    for ($m = 15 * 60 + 35; $m -le 19 * 60 + 35; $m += 5) { [void](& $tick $m 60 30000) }
    # Виміри з #1856: 19:39 0 %, 19:45 0 %, 19:50 12 %, 19:55 0 %; PID 30368, 28888, 30348, 36888; далі карта на 0 % і той самий PID.
    foreach ($s in @(@(39, 0, 30368), @(45, 0, 28888), @(50, 12, 30348), @(55, 0, 36888))) { $w = & $tick (19 * 60 + $s[0]) $s[1] $s[2] }
    for ($m = 20 * 60; $m -le 21 * 60 + 5; $m += 5) { $w = & $tick $m 0 36888 }
    Check "а до порога (86 хв без роботи) — рядка нема; в #1856: замок $($w.LockMinutes) хв, сон $($w.SleepMinutes), без роботи $($w.IdleMinutes) хв, PID ×$($w.PidChanges)" (@(Read-Box).Count -eq 0 -and $w.IdleMinutes -eq 86 -and $w.PidChanges -eq 4 -and $w.SleepMinutes -eq 239 -and $w.LockMinutes -eq 486)
    $w = & $tick (21 * 60 + 9) 0 36888
    $r = @(Read-Box)
    Check "а понад поріг — рівно один рядок диспетчерові (замок без сну, сон окремо): $($r -join ' | ')" ($r.Count -eq 1 -and $r[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU_IDLE codex/Е1-нічний-живий-20261115 ЗАМОК 490 СОН 239 БЕЗ_РОБОТИ 90 PID_ЗМІН 4')
    for ($m = 21 * 60 + 14; $m -le 22 * 60 + 9; $m += 5) { [void](& $tick $m 0 $(if ($m -eq 22 * 60 + 9) { 1 } else { 36888 })) }
    Check 'а повторні проходи тієї самої причини (навіть із новим PID) — нових рядків нуль' (@(Read-Box).Count -eq 1)
    # Карта попрацювала й знову стала на 90 хв — нова причина, новий рядок.
    [void](& $tick (22 * 60 + 14) 70 1)
    for ($m = 22 * 60 + 19; $m -le 23 * 60 + 49; $m += 5) { [void](& $tick $m 0 1) }
    Check 'а нова бездіяльність після роботи карти — другий рядок' (@(Read-Box).Count -eq 2)
    # Рядки проходять шаблон публікатора, чужий текст — ні.
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pubw" -OutboxDir "$tmp/pubo"
    $all = @(Read-Box)
    Check 'а обидва рядки приймає й публікатор' (@($all | Where-Object { (Test-OutboxLine $_) -eq '' }).Count -eq $all.Count)
    Check 'а рядок будить диспетчера (Test-DispatcherAction)' (Test-DispatcherAction $all[0])
    Check 'а підроблений рядок (чужий текст у позначці) публікатор відкидає' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU_IDLE codex/x; rm ЗАМОК 1 СОН 0 БЕЗ_РОБОТИ 1 PID_ЗМІН 0') -ne '')
    Check 'а рядок старого формату (без СОН) публікатор відкидає' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU_IDLE codex/x ЗАМОК 1 БЕЗ_РОБОТИ 1 PID_ЗМІН 0') -ne '')
}

# --- (а2) справний прогін: чергування двох моделей (перезавантаження з новим PID), підготовка без викликів, сон ------------------
# 15.11 у справному прогоні було 107 перезавантажень на 377 викликів (20–120 с без обчислень кожне), 69 хв підготовки Codex без
# викликів моделі і сон ноутбука 11:30–15:29 UTC: сторож не має давати тривоги.
Scenario 'а2 справний прогін' {
    . $newEnv 'a2'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T09:00:00Z' })
    $maxIdle = 0; $w = $null; $n = 0
    for ($m = 9 * 60; $m -le 20 * 60 + 30; $m += 5) {
        if ($m -gt 11 * 60 + 25 -and $m -lt 15 * 60 + 35) { continue }   # сон: вимірів нема
        if ($m -lt 9 * 60 + 70) { $s = [pscustomobject]@{ Percent = 0; OwnerPid = 100; CallAgeMin = 200 } }   # підготовка Codex, 69 хв без викликів
        else { $n++; $s = [pscustomobject]@{ Percent = $(if ($n % 4 -eq 0) { 0 } else { 75 }); OwnerPid = 200 + [int][Math]::Floor($n / 4); CallAgeMin = 3 } }   # кожен четвертий вимір — перезавантаження моделі
        $w = Update-GpuWatch $holder $s $send "$tmp/a2/state/gpu-watch.json" $day.AddMinutes($m) { param($f, $t) Get-SleepOverlap $f $t }
        $maxIdle = [Math]::Max($maxIdle, $w.IdleMinutes)
    }
    Check "а2 справний прогін зі сном і чергуванням моделей — рядка нема (найдовше без роботи $maxIdle хв, PID ×$($w.PidChanges), сон $($w.SleepMinutes) хв)" (@(Read-Box).Count -eq 0 -and $maxIdle -lt 90 -and $w.PidChanges -gt 15 -and $w.SleepMinutes -eq 239)
    Check "а2 хвилини замка в #1856 — без сну: $($w.LockMinutes)" ($w.LockMinutes -eq 451)
}

# --- (а3) знімки 0 %, а виклики моделі йдуть (за журналом LM Studio) — рядка нема; журнала нема — не виміряно, без тривоги ------------
Scenario 'а3 виклики моделі' {
    . $newEnv 'a3'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T09:00:00Z' })
    $w = $null
    for ($m = 19 * 60; $m -le 21 * 60; $m += 5) { $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 300 + $m; CallAgeMin = 2 }) $send "$tmp/a3/state/gpu-watch.json" $day.AddMinutes($m) }
    Check "а3 карта на 0 % 120 хв із новим PID, але останній виклик моделі 2 хв тому — рядка нема (без роботи $($w.IdleMinutes) хв)" (@(Read-Box).Count -eq 0 -and $w.IdleMinutes -eq 120)
    $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 1; CallAgeMin = -1 }) $send "$tmp/a3/state/gpu-watch.json" $day.AddMinutes(21 * 60 + 5)
    Check 'а3 журнал LM Studio не читається — без тривоги, в результаті «не виміряно» (-1)' (@(Read-Box).Count -eq 0 -and $w.CallAgeMinutes -eq -1)
    $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 1; CallAgeMin = 95 }) $send "$tmp/a3/state/gpu-watch.json" $day.AddMinutes(21 * 60 + 10)
    Check 'а3 викликів моделі нема 95 хв і карта стояла — рядок раз' (@(Read-Box).Count -eq 1)
}

# --- (а5) пропущені такти без події сну — не сон; Get-SleepOverlap; Get-LmsCallAge ----------------------------------------------------
Scenario 'а5 пропущені такти' {
    . $newEnv 'a5'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T05:59:00Z' })
    $sl = { param($f, $t) Get-SleepOverlap $f $t }
    $tk = { param([int]$Min) Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 7; CallAgeMin = 120 }) $send "$tmp/a5/state/gpu-watch.json" $day.AddMinutes($Min) $sl }
    [void](& $tk (5 * 60 + 59)); [void](& $tk (6 * 60 + 4))
    $w = & $tk (7 * 60 + 19)   # 14.11: такти 06:04–07:14 пропущено (IgnoreNew), ноутбук не спав
    Check "а5 73 хв без вимірів без події сну — не сон, ряд не скинуто, замок не зменшено: замок $($w.LockMinutes), сон $($w.SleepMinutes), без роботи $($w.IdleMinutes)" ($w.SleepMinutes -eq 0 -and $w.IdleMinutes -eq 80 -and $w.LockMinutes -eq 80 -and @(Read-Box).Count -eq 0)
    [void](& $tk (7 * 60 + 29))
    $r = @(Read-Box)
    Check "а5 рядок на 90-й хв ряду: $($r -join ' | ')" ($r.Count -eq 1 -and $r[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU_IDLE codex/Е1-нічний-живий-20261115 ЗАМОК 90 СОН 0 БЕЗ_РОБОТИ 90 PID_ЗМІН 0')
    Check 'а5 Get-SleepOverlap: сон 11:30–15:29 — повністю 239, частково 30, «вимкнено й запущено» (heartbeat/boot) не сон' ((Get-SleepOverlap $day.AddMinutes(11 * 60) $day.AddMinutes(16 * 60)) -eq 239 -and (Get-SleepOverlap $day.AddMinutes(11 * 60) $day.AddMinutes(12 * 60)) -eq 30 -and (Get-SleepOverlap $day.AddMinutes(5 * 60 + 59) $day.AddMinutes(7 * 60)) -eq 0)
    Check 'а5 sleep-events.json нема — сон 0, без збою' ((Get-SleepOverlap $day.AddMinutes(0) $day.AddMinutes(1)) -eq 0 -and (& { $PublishDir = "$tmp/нема"; (Get-SleepOverlap $day.AddMinutes(11 * 60) $day.AddMinutes(16 * 60)) -eq 0 }))
}

Scenario 'а6 журнал LM Studio' {
    . $newEnv 'a6'
    $root = Join-Path $tmp 'lms-logs'; $sub = Join-Path $root '2026-11'
    [void][IO.Directory]::CreateDirectory($sub)
    [IO.File]::WriteAllText("$sub/старий.log", 'a', $utf); [IO.File]::WriteAllText("$sub/свіжий.log", 'b', $utf)
    [IO.File]::SetLastWriteTimeUtc("$sub/старий.log", [datetime]::UtcNow.AddMinutes(-120)); [IO.File]::SetLastWriteTimeUtc("$sub/свіжий.log", [datetime]::UtcNow.AddMinutes(-4))
    $age = Get-LmsCallAge $root
    Check "а6 час найновішого файла журналу: $age хв (очікується 3–5)" ($age -ge 3 -and $age -le 5)
    $src = (Get-Command Get-LmsCallAge).ScriptBlock.ToString()
    Check 'а6 час береться з самого файла ([IO.File]::GetLastWriteTimeUtc), а не з запису каталогу (елемент переліку мав відставання 32 хв)' ($src -cmatch 'GetLastWriteTimeUtc\(\$f\.FullName\)' -and $src -cnotmatch '\$f\.LastWriteTimeUtc|Sort-Object LastWriteTimeUtc')
    Check 'а6 теки нема чи в ній жодного журналу — -1 (не виміряно)' ((Get-LmsCallAge (Join-Path $tmp 'нема')) -eq -1 -and (Get-LmsCallAge $sub.Replace('2026-11', 'порожня')) -eq -1)
}

# --- (б) карта працює — рядка нема ------------------------------------------------------------------------------------------
Scenario 'б карта працює' {
    . $newEnv 'b'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T09:00:00Z' })
    $w = $null
    for ($i = 0; $i -lt 40; $i++) { $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = $(if ($i % 7 -eq 0) { 0 } else { 55 + $i }); OwnerPid = 30000 + $i; CallAgeMin = 120 }) $send "$tmp/b/state/gpu-watch.json" (At 17 0).AddMinutes(5 * $i) }
    Check "б карта працює (3 год 15 хв, PID міняється, поодинокі 0 %) — рядка нема, без роботи $($w.IdleMinutes) хв" (@(Read-Box).Count -eq 0 -and $w.IdleMinutes -lt 30)
    $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = -1; OwnerPid = 0 }) $send "$tmp/b/state/gpu-watch.json" (At 20 30)
    Check 'б невідомий вимір (nvidia-smi мовчить) не береться за простій' (@(Read-Box).Count -eq 0 -and $w.IdleMinutes -eq 0)
    Check 'б замка нема — запис знято, повертається $null' ($null -eq (Update-GpuWatch @() ([pscustomobject]@{ Percent = 0; OwnerPid = 0 }) $send "$tmp/b/state/gpu-watch.json" (At 21 0)) -and -not (Test-Path "$tmp/b/state/gpu-watch.json"))
}

# --- (в) інший наряд бере замок — ряд починається заново; невідомий вимір ряд не рве ------------------------------------------
Scenario 'в зміна замка' {
    . $newEnv 'c'
    $send = { param($l) [bool](Add-Line $l) }
    $first = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T09:00:00Z' })
    $next = @([pscustomobject]@{ Marker = $other; Since = '2026-11-15T20:10:00Z' })
    $tick = { param($Holders, [int]$Min, [int]$Pct, [int]$OwnerPid) Update-GpuWatch $Holders ([pscustomobject]@{ Percent = $Pct; OwnerPid = $OwnerPid; CallAgeMin = 120 }) $send "$tmp/c/state/gpu-watch.json" (At 19 0).AddMinutes($Min) }
    [void](& $tick $first 0 0 5)
    [void](& $tick $first 20 -1 0)
    [void](& $tick $first 40 0 5)
    [void](& $tick $first 60 0 5); [void](& $tick $first 80 0 5)
    $w = & $tick $first 90 0 5
    Check "в невідомий вимір ряд не рве: без роботи $($w.IdleMinutes) хв, рядок надіслано" ($w.IdleMinutes -eq 90 -and @(Read-Box).Count -eq 1)
    $w = & $tick $next 95 0 9
    Check "в новий власник замка — ряд і лічильник PID з нуля: замок $($w.LockMinutes), без роботи $($w.IdleMinutes), PID ×$($w.PidChanges)" ($w.Marker -ceq $other -and $w.LockMinutes -eq 25 -and $w.IdleMinutes -eq 0 -and $w.PidChanges -eq 0 -and @(Read-Box).Count -eq 1)
}

# --- (г) рядок у розділі GPU стану ноутбука (#1856) -----------------------------------------------------------------------------
Scenario 'г стан' {
    . $newEnv 'd'
    $now = [datetime]::UtcNow
    $st = [ordered]@{ marker = $marker; lock_since = (Get-UtcStamp $now.AddMinutes(-700)); idle_since = (Get-UtcStamp $now.AddMinutes(-100)); last_pid = 100; pid_changes = 3; sent = ''; last_at = (Get-UtcStamp $now.AddMinutes(-3)); sleep_min = 120 }
    [IO.File]::WriteAllText("$tmp/d/state/gpu-watch.json", ($st | ConvertTo-Json -Compress), $utf)
    function Get-LmsCallAge { 150 }
    function Get-GpuTelemetry { [pscustomobject]@{ Error = ''; TotalMiB = 24564; FreeMiB = 9000; Percent = 0 } }
    function Get-GpuCounterRows { @([pscustomobject]@{ Name = 'pid_200_luid_0x00000000_0x0001_phys_0'; DedicatedUsage = 8GB }) }
    function Get-GpuProcessInfo { param([int]$ProcessId) [pscustomobject]@{ Name = 'llama-server' } }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = (Get-UtcStamp $now.AddMinutes(-700)) })
    $lines = @(Get-GpuStateLines @('codex-1') $holder)
    $row = @($lines | Where-Object { $_ -like '- замок тримає *' })
    Check "г рядок у GPU-розділі: $($row -join ' | ')" ($row.Count -eq 1 -and $row[0] -cmatch ('^- замок тримає ' + [regex]::Escape($marker) + ' 5[7-8][0-9] хв \(без сну; сон 120 хв\); карта без роботи 10[0-1] хв; PID сервера змінювався 4 разів; виклики моделі: останній 150 хв тому$'))
    Check 'г і рядок диспетчерові надіслано раз' (@(Read-Box | Where-Object { $_ -cmatch 'GPU_IDLE codex/Е1-нічний-живий-20261115 ЗАМОК 5[7-8][0-9] СОН 120 БЕЗ_РОБОТИ 10[0-1] PID_ЗМІН 4$' }).Count -eq 1)
    # Журнал LM Studio не читається: без тривоги, в #1856 — «не виміряно».
    . $newEnv 'd2'
    [IO.File]::WriteAllText("$tmp/d2/state/gpu-watch.json", ($st | ConvertTo-Json -Compress), $utf)
    function Get-LmsCallAge { -1 }
    function Get-GpuTelemetry { [pscustomobject]@{ Error = ''; TotalMiB = 24564; FreeMiB = 9000; Percent = 0 } }
    function Get-GpuCounterRows { @() }
    function Get-GpuProcessInfo { param([int]$ProcessId) [pscustomobject]@{ Name = 'x' } }
    $row2 = @(Get-GpuStateLines @('codex-1') $holder | Where-Object { $_ -like '- замок тримає *' })
    Check "г журнала LM Studio нема — рядка диспетчерові нема, в #1856 «не виміряно»: $($row2 -join ' | ')" (@(Read-Box).Count -eq 0 -and $row2.Count -eq 1 -and $row2[0] -like '*виклики моделі: не виміряно*')
    $none = @(Get-GpuStateLines @() @() | Where-Object { $_ -like '- замок тримає *' })
    Check 'г замка нема — рядка «замок тримає» нема' ($none.Count -eq 0)
}

# --- (е) 15787: після пробудження стан оновлюється раніше, ніж публікатор запише подію сну ------------------------------------------
Scenario 'е сон ще не записано' {
    . $newEnv 'e'
    $PublishDir = "$tmp/pub-e"; [void][IO.Directory]::CreateDirectory($PublishDir)
    $pubE = { param([string]$Read, [bool]$WithEvent) [IO.File]::WriteAllText("$PublishDir/sleep-events.json", (@{ read_utc = $Read; events = $(if ($WithEvent) { @(@{ key = 'a'; from = '2026-11-15T11:30:00.0000000+00:00'; to = '2026-11-15T15:29:00.0000000+00:00'; source = 'Power-Troubleshooter/1'; announced = $true }) } else { @() }) } | ConvertTo-Json -Depth 5 -Compress), $utf) }
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T08:59:00Z' })
    $sl = { param($f, $t) Get-SleepOverlap $f $t }; $rd = { Get-SleepRead }
    $tk = { param([int]$Min, [int]$Call) Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 9; CallAgeMin = $Call }) $send "$tmp/e/state/gpu-watch.json" $day.AddMinutes($Min) $sl $rd }
    & $pubE '2026-11-15T11:30:00.0000000+00:00' $false
    for ($m = 9 * 60; $m -le 11 * 60 + 30; $m += 10) { [void](& $tk $m 2) }   # до сну карта на 0 %, але виклики моделі йшли
    # Ноутбук прокинувся о 15:29, такт 15:30 раніше за запис події: публікатор прочитав журнал лише до 11:30.
    $w = & $tk (15 * 60 + 30) 240
    Check "е ДО: такт до запису події сну — тривоги нема (було б СОН 0, БЕЗ_РОБОТИ 390); рядків $(@(Read-Box).Count)" (@(Read-Box).Count -eq 0)
    # Публікатор записав подію й прочитав журнал до 15:31; такт 15:32.
    & $pubE '2026-11-15T15:31:00.0000000+00:00' $true
    $w = & $tk (15 * 60 + 32) 240
    Check "е ПІСЛЯ: щойно подія з'явилась — сон пораховано ($($w.SleepMinutes) хв), ряд скинуто ($($w.IdleMinutes) хв), тривоги нема" ($w.SleepMinutes -eq 239 -and $w.IdleMinutes -lt 5 -and @(Read-Box).Count -eq 0)
    # Публікатор не просунувся за останній вимір: стан не міняється.
    & $pubE '2026-11-15T15:31:00.0000000+00:00' $true
    $w2 = & $tk (15 * 60 + 40) 240
    Check "е публікатор стоїть — стан не міняється, тривоги нема (сон $($w2.SleepMinutes), без роботи $($w2.IdleMinutes))" ($w2.SleepMinutes -eq 239 -and @(Read-Box).Count -eq 0)
}

# --- (ж) 15788: невідомий вимір ряд не рве й не подовжує ---------------------------------------------------------------------------
Scenario 'ж невідомий вимір' {
    . $newEnv 'z'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T18:59:00Z' })
    $tk = { param([int]$Min, [int]$Pct) Update-GpuWatch $holder ([pscustomobject]@{ Percent = $Pct; OwnerPid = 5; CallAgeMin = 120 }) $send "$tmp/z/state/gpu-watch.json" $day.AddMinutes($Min) }
    [void](& $tk (19 * 60) 0)
    for ($m = 19 * 60 + 5; $m -le 20 * 60 + 30; $m += 5) { $w = & $tk $m -1 }
    Check "ж ДО: один вимір 0 % о 19:00 і 18 невідомих до 20:30 — тривоги нема (було б БЕЗ_РОБОТИ 90); без роботи $($w.IdleMinutes) хв, рядків $(@(Read-Box).Count)" ($w.IdleMinutes -eq 0 -and @(Read-Box).Count -eq 0)
    [void](& $tk (20 * 60 + 35) 0)
    $w = & $tk (20 * 60 + 40) 0
    Check "ж ПІСЛЯ: ряд не порвано, відновлений вимір рахується далі — без роботи $($w.IdleMinutes) хв (очікується 5), тривоги нема" ($w.IdleMinutes -eq 5 -and @(Read-Box).Count -eq 0)
    # Вимір працює 15 хв, ряд справді триває 90 хв — тривога йде.
    for ($m = 20 * 60 + 45; $m -le 22 * 60 + 15; $m += 5) { $w = & $tk $m 0 }
    Check "ж далі виміри без розривів — рядок раз після 90 хв відомої бездіяльності (без роботи $($w.IdleMinutes) хв)" (@(Read-Box).Count -eq 1)
}

# --- (д) рядок наглядової: гілки claude/прочитано-ноутбук і claude/лист-ноутбуку-* ------------------------------------------------
Scenario 'д наглядова' {
    . $newEnv 'e'
    $origin = Join-Path $tmp 'origin.git'; $clone = Join-Path $tmp 'clone'
    & git init -q --bare $origin
    & git init -q -b main $clone
    & git -C $clone config user.email t@t; & git -C $clone config user.name t
    & git -C $clone remote add origin $origin
    [IO.File]::WriteAllText("$clone/f.txt", 'x', $utf); & git -C $clone add f.txt; & git -C $clone commit -q -m base
    $script:NoHooks = Join-Path $tmp 'no-hooks'
    $RepoDir = $clone   # Invoke-Git обгортки бере $RepoDir з області сценарію
    $tree = (& git -C $clone rev-parse 'HEAD^{tree}').Trim(); $base = (& git -C $clone rev-parse HEAD).Trim()
    # Кирилиця — лише через Invoke-Git обгортки (UTF-8 аргументи) і файл повідомлення: власні аргументи PowerShell 5.1 її псують.
    function New-Commit([string]$Msg, [string]$Date, [string]$Parent) {
        $f = Join-Path $tmp ('msg-' + [guid]::NewGuid().ToString('N') + '.txt'); [IO.File]::WriteAllText($f, $Msg, $utf)
        $env:GIT_AUTHOR_DATE = $Date; $env:GIT_COMMITTER_DATE = $Date
        try { $a = @('commit-tree', $tree, '-F', $f); if ($Parent) { $a += @('-p', $Parent) }; (Invoke-Git $a).Out.Trim() }
        finally { Remove-Item Env:GIT_AUTHOR_DATE, Env:GIT_COMMITTER_DATE -ErrorAction SilentlyContinue }
    }
    function Push-Ref([string]$Sha, [string]$Ref) { [void](Invoke-Git @('push', '-q', '-f', 'origin', "${Sha}:refs/heads/$Ref")) }
    function Remove-Ref([string]$Ref) { [void](Invoke-Git @('push', '-q', 'origin', '--delete', $Ref)) }
    Push-Ref $base 'main'
    $la = New-Commit 'ND: лист а' '2026-11-14T17:17:00+00:00' $base; Push-Ref $la 'claude/лист-ноутбуку-а'
    $lb = New-Commit 'ND: лист б' '2026-11-15T15:00:00+00:00' $base; Push-Ref $lb 'claude/лист-ноутбуку-б'
    # Усе прочитано: вершина — 22:02:47 за +02:00, тобто 20:02:47 UTC.
    $r1 = New-Commit "ПРОЧИТАНО claude/лист-ноутбуку-а $la" '2026-11-15T21:00:00+02:00' ''
    $r2 = New-Commit "ПРОЧИТАНО claude/лист-ноутбуку-б $lb (правила з origin/main 1e5ec4a4)" '2026-11-15T22:02:47+02:00' $r1
    Push-Ref $r2 'claude/прочитано-ноутбук'
    $line = Get-SupervisorLine -NoCache
    Check "д усе прочитано: $line" ($line -ceq 'наглядова: останнє ПРОЧИТАНО 2026-11-15T20:02:47Z (claude/лист-ноутбуку-б); листів без відповіді 0')
    # Є непрочитані: найстаріший — за часом коміту вершини гілки.
    $lc = New-Commit 'ND: лист в' '2026-11-15T20:30:00+00:00' $base; Push-Ref $lc 'claude/лист-ноутбуку-в'
    $ld = New-Commit 'ND: лист г' '2026-11-15T19:45:00+00:00' $base; Push-Ref $ld 'claude/лист-ноутбуку-г'
    $line = Get-SupervisorLine -NoCache
    Check "д є непрочитані: $line" ($line -ceq 'наглядова: останнє ПРОЧИТАНО 2026-11-15T20:02:47Z (claude/лист-ноутбуку-б); листів без відповіді 2, найстаріший claude/лист-ноутбуку-г 2026-11-15T19:45:00Z')
    # Кеш: у межах 10 хв той самий рядок без git.
    Push-Ref $la 'claude/лист-ноутбуку-д'
    $cached = Get-SupervisorLine
    Check 'д кеш до 10 хв: рядок не міняється' ($cached -ceq $line)
    # Гілки прочитано нема.
    Remove-Ref 'claude/прочитано-ноутбук'
    $line = Get-SupervisorLine -NoCache
    Check "д гілки прочитано нема: $line" ($line -ceq 'наглядова: гілки claude/прочитано-ноутбук нема (жодного ПРОЧИТАНО); листів без відповіді 5, найстаріший claude/лист-ноутбуку-а 2026-11-14T17:17:00Z' -or $line -ceq 'наглядова: гілки claude/прочитано-ноутбук нема (жодного ПРОЧИТАНО); листів без відповіді 5, найстаріший claude/лист-ноутбуку-д 2026-11-14T17:17:00Z')
    # Лист, зняту гілку якого вже прибрано, не лічиться.
    Remove-Ref 'claude/лист-ноутбуку-д'
    $line = Get-SupervisorLine -NoCache
    Check "д прибрана гілка листа не лічиться: $line" ($line -cmatch 'листів без відповіді 4, ')
    # Тіло стану несе рядок.
    function Get-TaskRows { @() }
    function Get-HealthLines { @() }
    $body = Get-StatusBody
    Check 'д тіло стану (#1856) містить рядок «наглядова: …»' ($body -cmatch '(?m)^наглядова: ')
}

Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
if ($bad) { "ПОМИЛКА: провалів $bad"; exit 1 }
