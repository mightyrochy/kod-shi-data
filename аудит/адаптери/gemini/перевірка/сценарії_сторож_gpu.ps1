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
    $script:Limits = @{ slots = @{ claude = 2 }; source = 'код'; claude_laptop = @(); gpu_idle_minutes = 30; gpu_idle_percent = 15 }
    $script:TestBox = $box
}
function Read-Box { @(Get-ChildItem -LiteralPath $script:TestBox -Filter '*.txt' -File -ErrorAction SilentlyContinue | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() }) }

# --- (а) сьогоднішній випадок: замок тримається, карта 0 %, PID міняється ---------------------------------------------------
Scenario 'а випадок 15.11' {
    . $newEnv 'a'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T09:00:00Z' })
    # ДО: запобіжник утримань (Update-HoldSignals) бачить лише позначки, що не стартують, — наряд, що йде, рядка не дає.
    Update-HoldSignals @{} $send
    Check 'а ДО: наявний запобіжник за цього випадку мовчить — рядків 0' (@(Read-Box).Count -eq 0)
    # Виміри з #1856: 19:39 0 %, 19:45 0 %, 19:50 12 %, 19:55 0 %; PID 30368, 28888, 30348, 36888.
    $series = @(@(19, 39, 0, 30368), @(19, 45, 0, 28888), @(19, 50, 12, 30348), @(19, 55, 0, 36888), @(20, 0, 0, 36888), @(20, 5, 0, 36888))
    foreach ($s in $series) { $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = $s[2]; OwnerPid = $s[3] }) $send "$tmp/a/state/gpu-watch.json" (At $s[0] $s[1]) }
    Check "а до порога (26 хв без роботи) — рядка нема, в #1856: замок $($w.LockMinutes) хв, без роботи $($w.IdleMinutes) хв, PID ×$($w.PidChanges)" (@(Read-Box).Count -eq 0 -and $w.IdleMinutes -eq 26 -and $w.PidChanges -eq 3 -and $w.LockMinutes -eq 665)
    $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 36888 }) $send "$tmp/a/state/gpu-watch.json" (At 20 9)
    $r = @(Read-Box)
    Check "а понад поріг — рівно один рядок диспетчерові: $($r -join ' | ')" ($r.Count -eq 1 -and $r[0] -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU_IDLE codex/Е1-нічний-живий-20261115 ЗАМОК 669 БЕЗ_РОБОТИ 30 PID_ЗМІН 3')
    foreach ($m in 14, 19, 24, 60) { [void](Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 36888 }) $send "$tmp/a/state/gpu-watch.json" (At 20 $m)) }
    [void](Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 1 }) $send "$tmp/a/state/gpu-watch.json" (At 21 5))
    Check 'а повторні проходи тієї самої причини (навіть із новим PID) — нових рядків нуль' (@(Read-Box).Count -eq 1)
    # Карта попрацювала й знову стала — нова причина, новий рядок.
    [void](Update-GpuWatch $holder ([pscustomobject]@{ Percent = 70; OwnerPid = 1 }) $send "$tmp/a/state/gpu-watch.json" (At 21 10))
    [void](Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 1 }) $send "$tmp/a/state/gpu-watch.json" (At 21 15))
    [void](Update-GpuWatch $holder ([pscustomobject]@{ Percent = 0; OwnerPid = 1 }) $send "$tmp/a/state/gpu-watch.json" (At 21 46))
    Check 'а нова бездіяльність після роботи карти — другий рядок' (@(Read-Box).Count -eq 2)
    # Рядки проходять шаблон публікатора, чужий текст — ні.
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pubw" -OutboxDir "$tmp/pubo"
    $all = @(Read-Box)
    Check 'а обидва рядки приймає й публікатор' (@($all | Where-Object { (Test-OutboxLine $_) -eq '' }).Count -eq $all.Count)
    Check 'а рядок будить диспетчера (Test-DispatcherAction)' (Test-DispatcherAction $all[0])
    Check 'а підроблений рядок (чужий текст у позначці) публікатор відкидає' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU_IDLE codex/x; rm ЗАМОК 1 БЕЗ_РОБОТИ 1 PID_ЗМІН 0') -ne '')
}

# --- (б) карта працює — рядка нема ------------------------------------------------------------------------------------------
Scenario 'б карта працює' {
    . $newEnv 'b'
    $send = { param($l) [bool](Add-Line $l) }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = '2026-11-15T09:00:00Z' })
    $w = $null
    for ($i = 0; $i -lt 40; $i++) { $w = Update-GpuWatch $holder ([pscustomobject]@{ Percent = $(if ($i % 7 -eq 0) { 0 } else { 55 + $i }); OwnerPid = 30000 + $i }) $send "$tmp/b/state/gpu-watch.json" (At 17 0).AddMinutes(5 * $i) }
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
    [void](Update-GpuWatch $first ([pscustomobject]@{ Percent = 0; OwnerPid = 5 }) $send "$tmp/c/state/gpu-watch.json" (At 19 0))
    [void](Update-GpuWatch $first ([pscustomobject]@{ Percent = -1; OwnerPid = 0 }) $send "$tmp/c/state/gpu-watch.json" (At 19 20))
    $w = Update-GpuWatch $first ([pscustomobject]@{ Percent = 0; OwnerPid = 5 }) $send "$tmp/c/state/gpu-watch.json" (At 19 40)
    Check "в невідомий вимір ряд не рве: без роботи $($w.IdleMinutes) хв, рядок надіслано" ($w.IdleMinutes -eq 40 -and @(Read-Box).Count -eq 1)
    $w = Update-GpuWatch $next ([pscustomobject]@{ Percent = 0; OwnerPid = 9 }) $send "$tmp/c/state/gpu-watch.json" (At 20 15)
    Check "в новий власник замка — ряд і лічильник PID з нуля: замок $($w.LockMinutes), без роботи $($w.IdleMinutes), PID ×$($w.PidChanges)" ($w.Marker -ceq $other -and $w.LockMinutes -eq 5 -and $w.IdleMinutes -eq 0 -and $w.PidChanges -eq 0 -and @(Read-Box).Count -eq 1)
}

# --- (г) рядок у розділі GPU стану ноутбука (#1856) -----------------------------------------------------------------------------
Scenario 'г стан' {
    . $newEnv 'd'
    $now = [datetime]::UtcNow
    $st = [ordered]@{ marker = $marker; lock_since = (Get-UtcStamp $now.AddMinutes(-700)); idle_since = (Get-UtcStamp $now.AddMinutes(-45)); last_pid = 100; pid_changes = 3; sent = '' }
    [IO.File]::WriteAllText("$tmp/d/state/gpu-watch.json", ($st | ConvertTo-Json -Compress), $utf)
    function Get-GpuTelemetry { [pscustomobject]@{ Error = ''; TotalMiB = 24564; FreeMiB = 9000; Percent = 0 } }
    function Get-GpuCounterRows { @([pscustomobject]@{ Name = 'pid_200_luid_0x00000000_0x0001_phys_0'; DedicatedUsage = 8GB }) }
    function Get-GpuProcessInfo { param([int]$ProcessId) [pscustomobject]@{ Name = 'llama-server' } }
    $holder = @([pscustomobject]@{ Marker = $marker; Since = (Get-UtcStamp $now.AddMinutes(-700)) })
    $lines = @(Get-GpuStateLines @('codex-1') $holder)
    $row = @($lines | Where-Object { $_ -like '- замок тримає *' })
    Check "г рядок у GPU-розділі: $($row -join ' | ')" ($row.Count -eq 1 -and $row[0] -cmatch ('^- замок тримає ' + [regex]::Escape($marker) + ' 70[0-1] хв; карта без роботи 4[5-6] хв; PID сервера змінювався 4 разів$'))
    Check 'г і рядок диспетчерові надіслано раз' (@(Read-Box | Where-Object { $_ -cmatch 'GPU_IDLE codex/Е1-нічний-живий-20261115 ЗАМОК 70[0-1] БЕЗ_РОБОТИ 4[5-6] PID_ЗМІН 4$' }).Count -eq 1)
    $none = @(Get-GpuStateLines @() @() | Where-Object { $_ -like '- замок тримає *' })
    Check 'г замка нема — рядка «замок тримає» нема' ($none.Count -eq 0)
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
