#Requires -Version 5.1
<#
.SYNOPSIS
Смуга Claude Code ноутбука: наряди за позначками `gemini-queue/<наряд>/cc-<модель>[-<зусилля>]/<спроба>[/<умови>]` веде
`claude -p` під власником — до N водночас (слоти з `смуги.json`), за пріоритетом і строком; кінець — рядок теки
вихідних; стан ноутбука (усі смуги, слоти, квота) — тіло issue, переписане на місці.

.DESCRIPTION
Задача планувальника `claude-run` під власником, раз на 5 хв, без межі часу задачі. Запуск — планувальник: живе, доки йде
хоч один його наряд, і опитує чергу раз на `poll_minutes`; без нарядів — виходить. Наряд — окремий процес того самого
скрипта (`-WorkerFile`) зі своїм слотом і текою запуску; копія задачі — `w\<прогін>` (git worktree клону `RepoDir` без
тек-архівів, `TEMP` — там же) — є лише після звірки голови й прибирається після звіту (`queue_lanes.ps1`, New-TaskCopy).
Спільне з `gemini_run.ps1` — `queue_lanes.ps1` (позначки, порядок, слоти, межі, чекання квоти, замок GPU).
  1. Позначки — лише `cc-…` з `origin` (fetch у клон власника `RepoDir`); `gemini-run` їх не бере. Узяття — атомарне
     (`.claim`), виконана позначка — файл стану, вдруге не береться. Коміт позначки — у `main`, наряд — файл
     `аудит/наряди/<наряд>.md` на цьому коміті; позначка вибирає лише наряд, модель, спробу й умови. Без умови `gpu` і
     поза переліком `claude_laptop` у `смуги.json` — ЗАБЛОКОВАНО … CLAUDE_NOT_LAPTOP, без копії й слота: решта — хмарі.
  2. `cc-<модель>-<зусилля>`: модель і зусилля йдуть у `claude --model/--effort` дослівно; неприйняте —
     ЗАБЛОКОВАНО з кодом (MODEL_INVALID, EFFORT_INVALID), без підміни. Дозволи — `--permission-mode auto`.
  3. Промпт — перший і останній рядки запускача (`аудит/ЗАПУСКАЧ.md`) без його id і з вимкненням «лише обгортка за
     позначкою»; нова спроба при наявній гілці наряду — ще «продовжуй з гілки». Гілку й PR-чернетку сесія пушить сама.
  4. Межі часу всього нема: зупиняє лише завислість — жодної події stream-json довше за поріг (HANG).
  5. Кінець — рядок теки вихідних (доставляє `gemini-publish`): ГОТОВО <гілка> <SHA40>, лише коли `origin` має
     саме цей SHA на гілці зі звіту, або ЗАБЛОКОВАНО claude/<наряд> <КОД>; копія з незапушеними комітами лишається — ще рядок COPY_KEPT. Відмова за квотою — не кінець: позначка
     чекає скидання (час — з події `rate_limit_event` stream-json) і рядок QUOTA0_CLAUDE_M<хв>; потім її бере ця ж смуга.
  6. Позначка `gemini-queue/ВИМКНИ-НОУТБУК/cc-off/<спроба>`: коли рушії не працюють — рядок ВИМКНЕНО, чекання
     доставки й `shutdown`. Позначка, що вже була до першого проходу після ввімкнення, — ЗАБЛОКОВАНО … BOOT.
  7. Стан — тіло issue -StatusIssue (`gh api -X PATCH`), щопроходу не частіше за -StatusMinutes: задачі планувальника,
     смуги й слоти (свої й gemini-run з heartbeat), квота груп моделей і Claude з часом скидання в UTC, позначки в
     чеканні квоти, GPU, межі без джерела, здоров'я машини (місце, теки, позначки за рушієм, видом і віком), аварії однієї
     причини — лише обчислене.
#>
[CmdletBinding()]
param(
    [string]$WorkDir = (Join-Path $env:USERPROFILE 'claude-run'),
    [string]$RepoDir = (Join-Path $env:USERPROFILE 'kod-shi-data'),
    [string]$OutboxDir = (Join-Path $env:USERPROFILE 'gemini-outbox'),
    [string]$PublishDir = (Join-Path $env:USERPROFILE 'gemini-publish'),
    [string]$GeminiOutDir = 'C:\Users\Public\gemini\out',
    [string]$GeminiStateDir = (Join-Path $env:USERPROFILE 'gemini-runs\state'),
    [string]$LaneDir = 'C:\Users\Public\gemini\lanes',
    [string]$RepoUrl = 'https://github.com/mightyrochy/kod-shi-data',
    [string]$Repo = 'mightyrochy/kod-shi-data',
    [int]$StatusIssue = 1856,
    [string]$GitExe = 'git',
    [string]$ClaudeExe = 'claude',
    [string]$GhExe = 'gh',
    [double]$HangMinutes = 120,
    [double]$StatusMinutes = 5,
    [double]$PollMinutes = 2,
    [double]$QuotaWaitMinutes = 60,
    [int]$MarkerMaxAgeDays = 7,
    [double]$OffWaitMinutes = 10,
    [string[]]$TaskNames = @('claude-run', 'gemini-run', 'gemini-publish', 'gemini-watch'),
    [string]$GeminiUser = 'gemini',
    [string]$HealthDrive = 'C:\',
    [string]$TmpDir = 'C:\tmp',
    [switch]$NoStatus,
    [string]$WorkerFile = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Явно задані параметри (задача планувальника, стенд) — процесу наряду ті самі; вони сильніші за файл даних.
$script:Bound = @{}
foreach ($k in $PSBoundParameters.Keys) {
    if ($k -eq 'WorkerFile') { continue }
    $v = $PSBoundParameters[$k]
    $script:Bound[$k] = $(if ($v -is [System.Management.Automation.SwitchParameter]) { $v.IsPresent } else { $v })
}
$script:SelfPath = $PSCommandPath
. (Join-Path $PSScriptRoot 'queue_lanes.ps1')

$script:Lanes = @('claude')
$script:EffortPattern = '^(.+)-(none|minimal|low|medium|high|xhigh|max|ultra)$'
$script:OffSlug = 'ВИМКНИ-НОУТБУК'
$script:OffModel = 'cc-off'
$script:Phase = 'старт'
$script:LastStatus = [datetime]::MinValue
$script:FreshBoot = $false
$script:Limits = $null
$script:Workers = $null
$script:MarkerRx = '^gemini-queue/[\p{L}\p{Nd}._-]{1,80}/[a-z0-9][a-z0-9.-]{1,63}/[1-9][0-9]{0,2}(?:/(?:p[0-9]|d20[0-9]{10}|gpu)(?:-(?:p[0-9]|d20[0-9]{10}|gpu)){0,2})?$'
$script:UtcRx = '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$'

# Шаблони рядків — ті самі, що в `gemini_publish.ps1` (OutboxTemplates): рядок, що не збігся, у теку не йде.
$script:LineTemplates = @(
    "\AGEMINI ОБГОРТКА: ГОТОВО claude/$script:SlugCore [0-9a-f]{40} МОДЕЛЬ [a-z0-9][a-z0-9.-]{1,63}\z",
    "\AGEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$script:SlugCore [A-Z0-9_]{2,40}\z",
    '\AGEMINI ОБГОРТКА: ВИМКНЕНО [0-9a-f]{40}\z',
    '\AGEMINI ОБГОРТКА: ПРОСТІЙ 20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z [0-9]{1,6}\z',
    $script:HoldLineTemplate
)

# --- допоміжне ----------------------------------------------------------------------------------------------------

function Write-Log([string]$Text) {
    <# Рядок у claude-run.log. Пишуть водночас планувальник і процеси нарядів: зайнятий файл — кілька спроб. #>
    $path = Join-Path $WorkDir 'claude-run.log'
    $tag = $(if ($WorkerFile) { "[$PID] " } else { '' })
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}{2}' -f (Get-Date), $tag, $Text
    for ($i = 0; $i -lt 20; $i++) {
        try {
            if (-not $WorkerFile -and (Test-Path -LiteralPath $path) -and (Get-Item -LiteralPath $path).Length -gt 1MB) {
                Move-Item -LiteralPath $path -Destination ($path + '.old') -Force
            }
            [System.IO.File]::AppendAllText($path, $line + "`n", $script:Utf8); return
        } catch { Start-Sleep -Milliseconds 50 }
    }
}

# Шлях до виконуваного або ''. .NET із UseShellExecute=false дописує лише .exe, а CLI з npm — це .cmd.
function Find-Exe([string]$Name) {
    if (Test-Path -LiteralPath $Name -PathType Leaf) { return $Name }
    $cmds = @(Get-Command $Name -All -CommandType Application -ErrorAction SilentlyContinue)
    foreach ($ext in @('\.exe$', '\.cmd$', '')) {
        $hit = @($cmds | Where-Object { $_.Source -match $ext })
        if ($hit.Count -gt 0) { return $hit[0].Source }
    }
    ''
}

function Test-OwnerUser {
    if (-not $script:OnWindows) { return $true }
    $name = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    ($name -split '\\')[-1] -ne $GeminiUser
}

# SHA гілки на origin зараз або ''.
function Get-RemoteSha([string]$Branch) {
    $r = Invoke-Git @('ls-remote', 'origin', "refs/heads/$Branch") -AllowFail -TimeoutMinutes 3
    if ($r.Code -ne 0) { return '' }
    foreach ($line in ($r.Out -split "`n")) {
        $f = $line.Trim() -split "`t"
        if ($f.Count -eq 2 -and $f[1] -ceq "refs/heads/$Branch" -and $f[0] -match '^[0-9a-f]{40}$') { return $f[0] }
    }
    ''
}

function Test-ClaudeBranch([string]$Branch) {
    $Branch -cmatch "^claude/$script:SlugCore\z" -and -not $Branch.Contains('..') -and -not $Branch.EndsWith('.lock')
}

function New-Id { '{0:yyyyMMdd-HHmmss}-{1}' -f (Get-Date), ([guid]::NewGuid().ToString('N').Substring(0, 12)) }

# --- тека вихідних ------------------------------------------------------------------------------------------------

# Ім'я файлу (без .txt) або '' — рядок не за шаблоном.
function Add-Line([string]$Line) {
    $ok = $false
    foreach ($t in $script:LineTemplates) { if ($Line -cmatch $t) { $ok = $true; break } }
    if (-not $ok -or $Line.Contains('..')) { Write-Log "рядок не за шаблоном — не записано: $Line"; return '' }
    $id = New-Id
    Write-FileAtomic (Join-Path $OutboxDir "$id.txt") ($Line + "`n")
    Write-Log "рядок $id : $Line"
    $id
}

# --- позначки -----------------------------------------------------------------------------------------------------

# Модель і зусилля Claude з назви `cc-<модель>[-<зусилля>]`; Off — позначка вимкнення.
function Add-ClaudeFields($M) {
    $cc = $M.Model.Substring(3); $model = $cc; $effort = ''
    if ($cc -cmatch $script:EffortPattern) { $model = $Matches[1]; $effort = $Matches[2] }
    $M | Add-Member -NotePropertyName Claude -NotePropertyValue $model -Force
    $M | Add-Member -NotePropertyName Effort -NotePropertyValue $effort -Force
    $M | Add-Member -NotePropertyName Off -NotePropertyValue ($M.Slug -ceq $script:OffSlug -and $M.Model -ceq $script:OffModel) -Force
    $M
}

# --- ноутбук (перекривається на стенді) ----------------------------------------------------------------------------

function Get-BootStamp {
    if (-not $script:OnWindows) { return '' }
    Get-UtcStamp (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
}

function Invoke-Shutdown { & shutdown.exe /s /t 60 }

function Get-TaskRows {
    foreach ($n in $TaskNames) {
        $row = [ordered]@{ Name = $n; Last = '?'; Result = '?'; State = '?' }
        try {
            $t = Get-ScheduledTask -TaskName $n -ErrorAction Stop
            $i = $t | Get-ScheduledTaskInfo -ErrorAction Stop
            if ([string]$t.State -match '^[A-Za-z]{1,20}$') { $row.State = [string]$t.State }
            if ($i.LastRunTime -is [datetime] -and $i.LastRunTime.Year -gt 2000) { $row.Last = Get-UtcStamp $i.LastRunTime }
            $row.Result = '0x{0:X}' -f $i.LastTaskResult
        } catch { $null = $_ <# задачу чужого користувача власник без адміна не бачить (10013) #> }
        [pscustomobject]$row
    }
}

# Файли skipped.json (позначки без старту) і blocked-reasons.json (причини BLOCKED без гілки) обох планувальників: пише
# gemini — недовірений файл, тож у #1856 лише одним рядком, обрізаним і без символів розмітки таблиці.
function Read-NoteRows([string]$Path, [string[]]$Names) {
    try { $rows = @([System.IO.File]::ReadAllText($Path, $script:Utf8) | ConvertFrom-Json) } catch { return @() }
    @($rows | Select-Object -Last 12 | ForEach-Object {
        $r = $_
        $cells = foreach ($n in $Names) {
            $p = $(if ($r -is [string] -or $r -is [ValueType]) { $null } else { $r.PSObject.Properties[$n] })
            $v = $(if ($null -eq $p -or $null -eq $p.Value) { '' } else { [string]$p.Value })
            $v = [regex]::Replace($v, '[\x00-\x1f\x7f|`<>]+', ' ').Trim()
            if ($v.Length -gt 200) { $v.Substring(0, 200) } else { $v }
        }
        ,@($cells)
    })
}

# heartbeat.json обгортки Gemini (пише gemini — недовірений файл): лише поля за форматом, решта — «?» чи пропущено.
function Read-GeminiBeat {
    $b = [ordered]@{ Time = '?'; Isolation = '?'; Marker = ''; Engine = ''; Model = ''; Minutes = ''; Lanes = @(); Quota = $null; Codex = $null; Wait = @(); Limits = ''
        Unsourced = @(); Profile = $null; Zero = '' }
    $path = Join-Path $GeminiOutDir 'heartbeat.json'
    try { $j = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json } catch { return [pscustomobject]$b }
    $get = { param($o, $n) $p = $(if ($null -eq $o -or $o -is [string] -or $o -is [ValueType]) { $null } else { $o.PSObject.Properties[$n] }); if ($null -eq $p -or $null -eq $p.Value) { '' } elseif ($p.Value -is [datetime]) { $p.Value.ToString('s') } else { [string]$p.Value } }
    $utc = { param($s) if ($s -match $script:UtcRx) { $s } else { '' } }
    $t = & $get $j 'time'
    if ($t -match '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$') { $b.Time = Get-UtcStamp ([datetime]::ParseExact($t, 's', [cultureinfo]::InvariantCulture)) }
    $readUtc = & $get $j 'read_utc'
    if ($readUtc -cmatch $script:UtcRx) { $b.Time = $readUtc }
    $iso = & $get $j 'isolation'
    if ($iso -cmatch '^[A-Z0-9_]{2,40}$') { $b.Isolation = $iso }
    $lim = & $get $j 'limits'
    if ($lim -in @('origin/main', 'код')) { $b.Limits = $lim }
    $fields = @(Get-LimitFields)
    $b.Unsourced = @(@(Get-JsonProp $j 'unsourced' | Select-Object -First 16) | ForEach-Object { [string]$_ } | Where-Object { $fields -ccontains $_ })
    $h = Get-JsonProp $j 'health'
    $pb = & $get $h 'profile'; $ps = & $get $h 'skipped'; $pu = & $utc (& $get $h 'read')
    if ($pb -match '^[0-9]{1,15}$' -and $ps -match '^[0-9]{1,9}$' -and $pu) { $b.Profile = [pscustomobject]@{ Bytes = [long]$pb; Skipped = [int]$ps; Read = $pu } }
    $z = & $get $h 'zero'
    if ($z -match '^[0-9]{1,5}$') { $b.Zero = $z }
    $mk = & $get $j 'marker'
    if ($mk -cmatch $script:MarkerRx -and -not $mk.Contains('..')) {
        $b.Marker = $mk
        $e = & $get $j 'engine'; if ($e -cmatch '^[a-z]{2,10}$') { $b.Engine = $e }
        $md = & $get $j 'model'; if ($md -cmatch $script:ModelPattern) { $b.Model = $md }
        $s = & $get $j 'since'
        if ($s -match '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$') {
            $b.Minutes = [string][int][Math]::Floor(((Get-Date) - [datetime]::ParseExact($s, 's', [cultureinfo]::InvariantCulture)).TotalMinutes)
        }
    }
    $lanes = @()
    foreach ($l in @(Get-JsonProp $j 'lanes' | Select-Object -First 2)) {
        $ln = & $get $l 'lane'; $n = & $get $l 'n'
        if ($ln -notin @('codex', 'agy') -or -not (Test-SlotCount $n)) { continue }
        $busy = @(foreach ($s in @(Get-JsonProp $l 'busy' | Select-Object -First $script:Ceil.slots[1])) {
            $sl = & $get $s 'slot'; $m = & $get $s 'marker'; $md = & $get $s 'model'; $since = & $utc (& $get $s 'since')
            if (-not (Test-SlotName $sl @($ln)) -or $m -cnotmatch $script:MarkerRx -or $m.Contains('..') -or $md -cnotmatch $script:ModelPattern) { continue }
            [pscustomobject]@{ Slot = $sl; Marker = $m; Model = $md; Since = $since; Gpu = ((& $get $s 'gpu') -eq 'True') }
        })
        $lanes += [pscustomobject]@{ Lane = $ln; N = [int]$n; Busy = $busy }
    }
    $b.Lanes = $lanes
    $q = Get-JsonProp $j 'quota'
    if ($null -ne $q) {
        $win = @(foreach ($w in @(Get-JsonProp $q 'windows' | Select-Object -First 12)) {
            $g = & $get $w 'g'; $wn = & $get $w 'w'; $left = & $get $w 'left'; $r = & $get $w 'reset'
            if ($g -cnotmatch '^[A-Z0-9]{1,16}$' -or $wn -cnotmatch '^(?:WEEK|5H|DAY|OTHER|)$' -or $left -notmatch '^(?:100|[1-9]?[0-9])$') { continue }
            [pscustomobject]@{ G = $g; W = $wn; Left = [int]$left; Reset = (& $utc $r) }
        })
        $b.Quota = [pscustomobject]@{ Read = (& $utc (& $get $q 'read')); Windows = $win }
    }
    $c = Get-JsonProp $j 'codex'
    if ($null -ne $c) { $b.Codex = [pscustomobject]@{ Refused = (& $utc (& $get $c 'refused')); Reset = (& $utc (& $get $c 'reset')) } }
    $b.Wait = @(foreach ($w in @(Get-JsonProp $j 'wait' | Select-Object -First 12)) {
        $m = & $get $w 'marker'; $g = & $get $w 'g'
        if ($m -cnotmatch $script:MarkerRx -or $m.Contains('..')) { continue }
        [pscustomobject]@{ Marker = $m; Until = (& $utc (& $get $w 'until')); Group = $(if ($g -cmatch '^[A-Z0-9]{1,16}$') { $g } else { '' }) }
    })
    [pscustomobject]$b
}

# --- стан ---------------------------------------------------------------------------------------------------------

function Get-Minutes([string]$Utc) {
    if ($Utc -notmatch $script:UtcRx) { return '?' }
    [string][int][Math]::Floor(((Get-Date).ToUniversalTime() - [datetime]::ParseExact($Utc, "yyyy-MM-dd'T'HH:mm:ss'Z'", [cultureinfo]::InvariantCulture)).TotalMinutes)
}

# Квота Claude з останньої події `rate_limit_event` (quota-claude.json, пише процес наряду) — лише обчислене.
function Read-ClaudeQuota {
    try { [System.IO.File]::ReadAllText((Join-Path $WorkDir 'quota-claude.json'), $script:Utf8) | ConvertFrom-Json } catch { $null }
}

# Здоров'я машини (10971): вільне місце диска й зміна за добу, розміри названих тек, позначки черги за рушієм, видом і
# віком голови, позначки на рушії з нульовою квотою. Лише показ — узяття не гейтить; вимір — не частіше за usage_minutes,
# без обходу всього диска; профіль gemini міряє gemini-run (heartbeat).
function Get-FreeBytes { (New-Object System.IO.DriveInfo $HealthDrive).AvailableFreeSpace }

function Format-Gb([double]$Bytes) { ($Bytes / 1GB).ToString('0.0', [cultureinfo]::InvariantCulture) + ' ГБ' }

function Update-Health {
    $path = Join-Path $WorkDir 'health.json'
    $h = $null
    if (Test-Path -LiteralPath $path) { try { $h = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json } catch { $null = $_ } }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    if ($null -ne $h -and $now - [long]$h.time -lt 60 * (Get-Limit $script:Limits 'UsageMinutes' 'usage_minutes')) { return $h }
    $samples = @(@(Get-JsonProp $h 'samples') | Where-Object { $null -ne $_ -and $now - [long]$_.t -le 2 * 86400 })
    try { $samples += [pscustomobject]@{ t = $now; free = [long](Get-FreeBytes) } } catch { Write-Log "здоров'я: місце не виміряно" }
    $dirs = @(foreach ($d in @(@('C:\tmp', $TmpDir), @('claude-run', $WorkDir))) {
        $r = Measure-DirBytes $d[1]
        [pscustomobject]@{ name = $d[0]; bytes = $(if ($null -ne $r) { $r.Bytes } else { -1 }); skipped = $(if ($null -ne $r) { $r.Skipped } else { 0 }) }
    })
    $h = [pscustomobject]@{ time = $now; samples = $samples; dirs = $dirs }
    Write-FileAtomic $path ($h | ConvertTo-Json -Compress -Depth 4)
    $h
}

function Get-HealthLines($G, $Cq) {
    $h = Update-Health
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $lines = @('', "### Здоров'я", '')
    $drive = $HealthDrive.TrimEnd('\')
    $s = @($h.samples)
    if ($s.Count -eq 0) { $lines += "- вільне місце на ${drive} не виміряно" }
    else {
        $last = $s[-1]
        $base = @($s | Where-Object { [long]$_.t -le $now - 86400 } | Select-Object -Last 1)
        if ($base.Count -eq 0) { $base = @($s[0]) }
        $hours = [int][Math]::Round(([long]$last.t - [long]$base[0].t) / 3600.0)
        $delta = [long]$last.free - [long]$base[0].free
        $span = $(if ($hours -ge 24) { 'за добу' } elseif ($s.Count -gt 1) { "за $hours год (доби вимірів ще нема)" } else { '' })
        $lines += "- вільне місце на ${drive} $(Format-Gb $last.free)$(if ($span) { " · зміна $span" + ': ' + $(if ($delta -ge 0) { '+' } else { '−' }) + (Format-Gb ([Math]::Abs($delta))) } else { ' · зміна за добу: ще один вимір' })"
    }
    $sizes = @(foreach ($d in @($h.dirs)) { "$($d.name) $(if ([long]$d.bytes -lt 0) { 'нема' } else { Format-Gb $d.bytes })$(if ([int]$d.skipped -gt 0) { " (недоступних тек $($d.skipped))" })" })
    $sizes += "профіль gemini $(if ($null -ne $G.Profile) { (Format-Gb $G.Profile.Bytes) + $(if ($G.Profile.Skipped -gt 0) { " (недоступних тек $($G.Profile.Skipped))" }) + " (зчитано $($G.Profile.Read))" } else { '? (gemini-run не дав)' })"
    $lines += "- розміри: $($sizes -join ' · ')"
    $ms = @(try { Get-Markers } catch { Write-Log "здоров'я: позначки не прочитано"; @() })
    $lines += @('', "Позначки черги: $($ms.Count) (вік — від коміту голови)", '', '| рушій | вид | < 1 год | < 1 доба | ≥ 1 доба |', '|---|---|---|---|---|')
    $keys = @{}; $cnt = @{}
    foreach ($m in $ms) {
        $key = "$(if ($m.Valid) { $m.Lane } else { '?' }) | $(Get-MarkerKind ([string]$m.Slug))"
        $age = $now - [long]$m.Time
        $b = "$key#$(if ($age -lt 3600) { 0 } elseif ($age -lt 86400) { 1 } else { 2 })"
        $keys[$key] = $true
        $cnt[$b] = 1 + $(if ($cnt.ContainsKey($b)) { [int]$cnt[$b] } else { 0 })
    }
    foreach ($k in @($keys.Keys | Sort-Object)) {
        $c = @(foreach ($i in 0..2) { $(if ($cnt.ContainsKey("$k#$i")) { $cnt["$k#$i"] } else { 0 }) })
        $lines += "| $k | $($c[0]) | $($c[1]) | $($c[2]) |"
    }
    if ($keys.Count -eq 0) { $lines += '| — | — | 0 | 0 | 0 |' }
    $zero = { param($Refused, $Reset)
        if ($Refused -notmatch $script:UtcRx) { return $false }
        if ($Reset -match $script:UtcRx) { return [int](Get-Minutes $Reset) -lt 0 }
        [int](Get-Minutes $Refused) -lt (Get-Limit $script:Limits 'QuotaWaitMinutes' 'quota_wait_minutes') }
    $cz = $(if ($null -ne $Cq -and (& $zero ([string](Get-JsonProp $Cq 'refused')) ([string](Get-JsonProp $Cq 'reset')))) { @($ms | Where-Object { $_.Lane -eq 'claude' }).Count } else { 0 })
    $xz = $(if ($null -ne $G.Codex -and (& $zero $G.Codex.Refused $G.Codex.Reset)) { @($ms | Where-Object { $_.Lane -eq 'codex' }).Count } else { 0 })
    $lines += @('', "Позначки на рушії з нульовою квотою: claude $cz · codex $xz · agy $(if ($G.Zero) { $G.Zero } else { '?' })")
    $lines
}

function Get-StatusBody {
    $host_ = $(if ($env:COMPUTERNAME -match '^[A-Za-z0-9-]{1,15}$') { $env:COMPUTERNAME } else { '?' })
    $g = Read-GeminiBeat
    $rows = @(Get-TaskRows)
    $lim = $script:Limits
    $lines = @(
        '<!-- Тіло переписує задача claude-run на ноутбуці (аудит/адаптери/gemini/claude_run.ps1); лише обчислене. -->',
        "**Ноутбук $host_** · оновлено $(Get-UtcStamp (Get-Date)) · claude-run: $script:Phase",
        '',
        # Тіло пише сама задача, тож не може знати, що воно застаріло: безумовний "Оновлено понад 5 хв тому" суперечив
        # власному "оновлено <час>" (#1856, 29.10). Умова — для читача, лічить він за часом вище.
        'Якщо «оновлено» старше за 5 хв — задача `claude-run` не працює: ноутбук вимкнено, сплячий чи задачу зупинено.',
        '',
        '| задача | востаннє запущено (UTC) | результат | стан |',
        '|---|---|---|---|'
    )
    foreach ($r in $rows) { $lines += "| $($r.Name) | $($r.Last) | $($r.Result) | $($r.State) |" }
    $lines += @('', '### Смуги', '', '| смуга | слотів | зайнято | позначка | модель | хв | GPU |', '|---|---|---|---|---|---|---|')
    $gpuBy = @()
    $own = @(Read-SlotInfo 'claude')
    # Щойно запущений наряд ще не записав файла слота: показати його з пам'яті планувальника.
    if ($null -ne $script:Workers) {
        foreach ($w in @($script:Workers | Where-Object { -not $_.Proc.HasExited })) {
            if (@($own | Where-Object { [string]$_.slot -eq $w.Slot }).Count -eq 0) {
                $own += [pscustomobject]@{ slot = $w.Slot; marker = $w.Marker; model = ($w.Marker -split '/')[2]; since = ''; gpu = $w.Gpu }
            }
        }
    }
    $n = $(if ($null -ne $lim) { [int]$lim.slots['claude'] } else { '?' })
    if ($own.Count -eq 0) { $lines += "| claude | $n | 0 | — | — | — | — |" }
    foreach ($s in $own) {
        if ($s.gpu) { $gpuBy += [string]$s.slot }
        $lines += "| claude | $n | $($own.Count) | $($s.marker) | $($s.model) | $(Get-Minutes ([string]$s.since)) | $(if ($s.gpu) { 'так' } else { '—' }) |"
    }
    foreach ($ln in @('codex', 'agy')) {
        $l = @($g.Lanes | Where-Object { $_.Lane -eq $ln })
        if ($l.Count -eq 0) {
            if (-not $g.Lanes -and $g.Marker -and ($g.Engine -eq $ln -or ($ln -eq 'agy' -and $g.Engine -ne 'codex'))) { $lines += "| $ln | ? | 1 | $($g.Marker) | $(if ($g.Model) { $g.Model } else { '?' }) | $(if ($g.Minutes) { $g.Minutes } else { '?' }) | ? |" }
            else { $lines += "| $ln | ? | ? | — | — | — | — |" }
            continue
        }
        if ($l[0].Busy.Count -eq 0) { $lines += "| $ln | $($l[0].N) | 0 | — | — | — | — |" }
        foreach ($s in $l[0].Busy) {
            if ($s.Gpu) { $gpuBy += $s.Slot }
            $lines += "| $ln | $($l[0].N) | $($l[0].Busy.Count) | $($s.Marker) | $($s.Model) | $(Get-Minutes $s.Since) | $(if ($s.Gpu) { 'так' } else { '—' }) |"
        }
    }
    $lines += @(Get-IdleLines)
    $lines += @('', "GPU: $(if ($gpuBy.Count) { 'зайнята — ' + ($gpuBy -join ', ') } else { 'вільна' }) · межі: claude-run — $(if ($null -ne $lim) { $lim.source } else { '?' }), gemini-run — $(if ($g.Limits) { $g.Limits } else { '?' })")
    $lines += @('', "heartbeat gemini-run (UTC): $($g.Time) · вік: $(Get-Minutes $g.Time) хв · isolation: $($g.Isolation) · понад 5 хв — джерело застаріле")
    # Межа без джерела (10970) діє з попереднього прийнятого значення; рядок — щоб її було видно, а не щоб зупинити.
    $unsrc = @(Get-Unsourced $lim)
    foreach ($f in @(@($unsrc) + @($g.Unsourced) | Select-Object -Unique)) {
        $who = @($(if ($unsrc -ccontains $f) { 'claude-run' }), $(if ($g.Unsourced -ccontains $f) { 'gemini-run' }) | Where-Object { $_ })
        $lines += "- межа без джерела: $f ($($who -join ', '))"
    }
    # Остання зміна версії головного процесу (Write-VersionSwitch старого процесу): нова версія справді взялась.
    $vt = ''; try { $vt = [System.IO.File]::ReadAllText((Join-Path $script:StateDir 'version.txt'), $script:Utf8).Trim() } catch { $null = $_ }
    if ($vt -cmatch '^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z) ([0-9a-f]{8}) → ([0-9a-f]{8})\z') { $lines += "- версія: $($Matches[2]) → $($Matches[3]) ($($Matches[1]))" }
    $cq = Read-ClaudeQuota
    try { $lines += @(Get-HealthLines $g $cq) } catch { Write-Log "здоров'я: $($_.Exception.Message)"; $lines += @('', "### Здоров'я", '', '- не виміряно (збій — claude-run.log)') }
    $lines += @('', '### Квота (UTC)', '', '| смуга · група | вікно | залишок | скидання | зчитано |', '|---|---|---|---|---|')
    if ($null -ne $g.Quota -and $g.Quota.Windows.Count -gt 0) {
        foreach ($w in $g.Quota.Windows) { $lines += "| agy · $($w.G) | $(if ($w.W) { $w.W } else { '—' }) | $($w.Left) % | $(if ($w.Reset) { $w.Reset } else { '?' }) | $(if ($g.Quota.Read) { $g.Quota.Read } else { '?' }) |" }
    } else { $lines += '| agy | — | невідомо | — | — |' }
    if ($null -ne $cq) {
        foreach ($w in @(Get-JsonProp $cq 'windows')) {
            $lines += "| claude | $([string]$w.w) | $([string]$w.left) % | $(if ($w.reset) { [string]$w.reset } else { '?' }) | $([string]$cq.read) |"
        }
        if ([string](Get-JsonProp $cq 'refused')) { $lines += "| claude · остання відмова | — | 0 % | $(if ($cq.reset) { [string]$cq.reset } else { 'CLI не дав' }) | $([string]$cq.refused) |" }
    } else { $lines += '| claude | — | невідомо (ще не було прогону) | — | — |' }
    if ($null -ne $g.Codex -and $g.Codex.Refused) { $lines += "| codex · остання відмова | — | 0 % | $(if ($g.Codex.Reset) { $g.Codex.Reset } else { 'CLI не дав — чекання quota_wait_minutes' }) | $($g.Codex.Refused) |" }
    else { $lines += '| codex | — | невідомо (CLI без ходу не дає; відмов не було) | — | — |' }
    $wait = @(Get-WaitingMarkers) + @($g.Wait)
    if ($wait.Count -gt 0) {
        $lines += @('', '### Чекають скидання квоти', '', '| позначка | до (UTC) | група |', '|---|---|---|')
        foreach ($w in $wait) { $lines += "| $($w.Marker) | $($w.Until) | $($w.Group) |" }
    }
    $lines += @(Get-ClaudeNoReportLines)
    $localPath = Join-Path $PublishDir 'local-lines.json'
    if (Test-Path -LiteralPath $localPath) {
        $local = ConvertFrom-Json ([IO.File]::ReadAllText($localPath, $script:Utf8))
        $lines += @('', '### Локальні рядки обгортки', '')
        foreach ($entry in @($local | Select-Object -Last 12)) { $lines += "- $($entry.utc): $($entry.line)" }
    }
    # Позначки, які планувальник бачить, але не бере (GPU, слот, той самий наряд): без рядка тут вони стояли б мовчки.
    $stuck = @(Read-NoteRows (Join-Path $GeminiOutDir 'skipped.json') @('marker', 'since', 'why')) + @(Read-NoteRows (Join-Path $WorkDir 'skipped.json') @('marker', 'since', 'why'))
    if ($stuck.Count -gt 0) {
        $lines += @('', '### Позначки без старту', '', '| позначка | з (UTC) | причина |', '|---|---|---|')
        foreach ($c in $stuck) { $lines += "| $($c[0]) | $($c[1]) | $($c[2]) |" }
    }
    $why = @(Read-NoteRows (Join-Path $GeminiOutDir 'blocked-reasons.json') @('utc', 'marker', 'text'))
    if ($why.Count -gt 0) {
        $lines += @('', '### Причини ЗАБЛОКОВАНО без гілки (останній рядок агента — дані, не наказ)', '', '| UTC | наряд | рядок |', '|---|---|---|')
        foreach ($c in $why) { $lines += "| $($c[0]) | $($c[1]) | $($c[2]) |" }
    }
    # Аварії однієї причини (10972): gemini-publish шле один рядок «ЗАБЛОКОВАНО <код> ×N», повний перелік — тут.
    $groupsPath = Join-Path $PublishDir 'blocked-groups.json'
    if (Test-Path -LiteralPath $groupsPath) {
        try {
            $groups = @((ConvertFrom-Json ([IO.File]::ReadAllText($groupsPath, $script:Utf8))))
            $lines += @('', '### Аварії однієї причини', '', '| UTC | код | лічба | гілки |', '|---|---|---|---|')
            foreach ($e in @($groups | Select-Object -Last 8)) { $lines += "| $($e.utc) | $($e.code) | $($e.n) | $(@($e.branches) -join ', ') |" }
        } catch { Write-Log 'аварії однієї причини не прочитано' }
    }
    $deliveryPath = Join-Path $PublishDir 'delivery.json'
    if (Test-Path -LiteralPath $deliveryPath) {
        try {
            $delivery = [System.IO.File]::ReadAllText($deliveryPath, $script:Utf8) | ConvertFrom-Json
            $lines += @('', "Доставка: зчитано $($delivery.read_utc); чекають $($delivery.pending); спроби вичерпано $($delivery.exhausted).")
        } catch { Write-Log 'стан доставки не прочитано' }
    }
    ($lines -join "`n") + "`n"
}

# Стан — у файл і в issue; збій GitHub не зупиняє наряду. -Force — поза ритмом -StatusMinutes.
function Update-Status([switch]$Force) {
    if (-not $Force -and ((Get-Date) - $script:LastStatus).TotalMinutes -lt [Math]::Min(4, $StatusMinutes)) { return }
    $script:LastStatus = Get-Date
    try {
        $body = Get-StatusBody
        Write-FileAtomic (Join-Path $WorkDir 'status.md') $body
        $hb = [ordered]@{ read_utc = (Get-UtcStamp (Get-Date)); time = (Get-Date).ToString('s'); phase = $script:Phase; busy = @(Read-SlotInfo 'claude' | ForEach-Object { [string]$_.marker }) }
        Write-FileAtomic (Join-Path $WorkDir 'heartbeat.json') ($hb | ConvertTo-Json -Compress)
        if ($NoStatus) { return }
        $gh = Find-Exe $GhExe
        if (-not $gh) { Write-Log 'стан: gh не знайдено'; return }
        $in = Join-Path $WorkDir 'status.json'
        Write-FileAtomic $in (([ordered]@{ body = $body }) | ConvertTo-Json -Compress)
        $r = Invoke-Native $gh @('api', '-X', 'PATCH', '-H', 'Accept: application/vnd.github+json',
            "repos/$Repo/issues/$StatusIssue", '--input', $in) $WorkDir 3
        if ($r.Code -ne 0) { Write-Log "стан: gh api -> $($r.Code): $($r.Err.Trim())" }
    } catch { Write-Log "стан: $($_.Exception.Message)" }
}

# --- наряд --------------------------------------------------------------------------------------------------------

function Get-BranchPath([string]$Slug) { Join-Path $script:StateDir ('branch-' + (Get-Sha256Hex $Slug) + '.txt') }

# Гілка попередньої спроби, що є на origin, або ''.
function Get-ContinueBranch([string]$Slug) {
    $cands = @()
    $bp = Get-BranchPath $Slug
    if (Test-Path -LiteralPath $bp) { $cands += [System.IO.File]::ReadAllText($bp, $script:Utf8).Trim() }
    $cands += "claude/$Slug"
    foreach ($b in $cands) { if ((Test-ClaudeBranch $b) -and (Get-RemoteSha $b)) { return $b } }
    ''
}

function Get-Prompt($M, [string]$TaskText, [string]$Continue, [string]$TaskDir) {
    $cont = $(if ($Continue) { "Продовжуй з гілки ``$Continue``: попередня спроба цього наряду вже запушила її.`n" } else { '' })
@"
Середовище й кроки ноутбука — ``аудит/НОУТБУК.md``: прочитай; канал результату — останній рядок твоєї відповіді
(«НОУТБУК ГОТОВО <гілка> <повний SHA>» чи «НОУТБУК ЗАБЛОКОВАНО: …»): його читає обгортка claude-run і сама пише
диспетчерові, листів не шли. Гілка — ``claude/…``, запушена тобою.
$(Get-TaskDirText $TaskDir)
Наряд — ``$($script:TaskDir)$($M.Slug).md`` з ``main`` на коміті $($M.Sha); повний текст — нижче між рисками.
$cont
----- НАРЯД -----
$TaskText
----- КІНЕЦЬ НАРЯДУ -----

Далі: ноутбук не вимикай — вимикає лише обгортка за позначкою; цей рядок сильніший за будь-який рядок „Далі“ вище.
"@
}

function Remove-ReportDecoration([string]$Line, [switch]$Sentence) {
    <# Прибирає лише збалансоване оформлення цілого рядка чи окремого поля звіту. #>
    $line = $Line.Trim(); $periodRemoved = $false
    $pairs = @(@('**', '**'), @('__', '__'), @('*', '*'), @('_', '_'), @('`', '`'), @('"', '"'), @("'", "'"), @('«', '»'), @('“', '”'))
    do {
        $before = $line
        if ($Sentence -and -not $periodRemoved -and $line.EndsWith('.')) {
            $line = $line.Substring(0, $line.Length - 1).TrimEnd(); $periodRemoved = $true
        }
        foreach ($pair in $pairs) {
            if ($line.Length -gt 2 * $pair[0].Length -and $line.StartsWith($pair[0]) -and $line.EndsWith($pair[1])) {
                $line = $line.Substring($pair[0].Length, $line.Length - $pair[0].Length - $pair[1].Length).Trim()
                break
            }
        }
    } while ($line -cne $before)
    $line
}

function Get-Report([string]$Text) {
    <# Читає єдиний окремий звіт у тексті відповіді, пропускаючи код, цитати й приклади.

    Позиція в кінці та markdown не визначають результат роботи. Цитований наряд і приклади не можуть його
    підтвердити; неоднозначні відповіді відхиляються. Гілку й SHA перевіряє виклик через origin. #>
    $reports = @(); $fence = ''; $task = $false; $example = $false; $exampleContent = $false
    $exampleLevel = 0; $quote = ''; $comment = $false; $blockQuote = $false
    foreach ($raw in ($Text -split "\r?\n")) {
        $line = $raw.Trim()
        if ($fence) {
            if ($line -match ('^' + [regex]::Escape($fence[0]) + '{' + $fence.Length + ',}\s*$')) { $fence = '' }
            continue
        }
        if ($blockQuote) { if (-not $line) { $blockQuote = $false }; continue }
        if ($line.StartsWith('>')) { $blockQuote = $true; continue }
        if ($quote) { if ($line.TrimEnd('.').EndsWith($quote)) { $quote = '' }; continue }
        if ($line.Contains('<!--')) { $comment = $true }
        if ($comment) { if ($line.Contains('-->')) { $comment = $false }; continue }
        if ($line -match '^(`{3,}|~{3,})') { $fence = $Matches[1]; $exampleContent = $example; continue }
        if ($line -cmatch '^----- НАРЯД -----$') { $task = $true; continue }
        if ($line -cmatch '^----- КІНЕЦЬ НАРЯДУ -----$') { $task = $false; continue }
        if ($task) { continue }
        if ($line -match '^(#{1,6})\s+(.+)$') {
            $level = $Matches[1].Length; $title = $Matches[2]
            if ($exampleLevel -and $level -le $exampleLevel) { $exampleLevel = 0 }
            if ($title -match '^(?:Приклад|Приклади|Зразок|Цитата|Цитати|Текст наряду)\b') { $exampleLevel = $level }
            continue
        }
        if ($exampleLevel) { continue }
        if (-not $line) { if ($exampleContent) { $example = $false; $exampleContent = $false }; continue }
        $label = Remove-ReportDecoration $line
        if ($label -match '^(?:Приклад|Зразок|Цитата|Текст наряду)\b.*:\s*$') { $example = $true; $exampleContent = $false; continue }
        if ($example) { $exampleContent = $true; continue }
        if ($raw -match '^(?: {4}|\t)') { continue }
        foreach ($pair in @(@('«', '»'), @('"', '"'), @('“', '”'))) {
            if ($line.StartsWith($pair[0]) -and -not $line.TrimEnd('.').EndsWith($pair[1])) { $quote = $pair[1]; break }
        }
        if ($quote) { continue }
        $line = $line -replace '^[-+*]\s+', ''
        $line = Remove-ReportDecoration $line -Sentence
        # Явна позначка прикладу лишається прикладом і після SHA.
        if ($line -match '\s+[—–]\s+(?:приклад|зразок|цитата)\b') { continue }
        # Пояснення після звіту не є частиною SHA.
        $withoutNote = $line -replace '\s+[—–]\s+.+$', ''
        if ($withoutNote -cne $line) { $line = Remove-ReportDecoration $withoutNote -Sentence }
        if ($line -cmatch '^НОУТБУК ГОТОВО (\S+) (\S+)$') {
            $branch = Remove-ReportDecoration $Matches[1]
            $sha = Remove-ReportDecoration $Matches[2]
            if ($sha -cnotmatch '^[0-9a-fA-F]{7,40}$') { return $null }
            $reports += [pscustomobject]@{ Kind = 'DONE'; Branch = $branch; Sha = $sha.ToLowerInvariant() }
        } elseif ($line -cmatch '^НОУТБУК ЗАБЛОКОВАНО\b') {
            $branch = ''
            if ($line -cmatch "(claude/$script:SlugCore)") { $branch = $Matches[1].TrimEnd('.') }
            $reports += [pscustomobject]@{ Kind = 'BLOCKED'; Branch = $branch; Sha = '' }
        }
    }
    if ($reports.Count -eq 1) { return $reports[0] }
    $null
}



function Get-ClaudeText($R) {
    <# Читає лише текст result; інші типи не перетворює на уявний звіт. #>
    $value = $null
    if ($null -ne $R.Result) {
        $property = $R.Result.PSObject.Properties['result']
        if ($null -ne $property) { $value = $property.Value }
    }
    if ($value -is [string]) { return $value }
    ''
}

function Get-ClaudeReport($R) {
    <# Відновлює звіт із останньої відповіді assistant, коли result порожній або її префікс. #>
    $text = Get-ClaudeText $R
    $report = Get-Report $text
    if ($null -ne $report) { return $report }
    $assistant = [string](Get-JsonProp $R 'AssistantText')
    # Інший непорожній result є остаточною відповіддю: приклади й цитати не стають звітом із попередньої події.
    if (-not $text.Trim() -or $assistant.StartsWith($text.TrimEnd(), [StringComparison]::Ordinal)) {
        return (Get-Report $assistant)
    }
    $null
}

function Read-ClaudeEvent($R, $Obj) {
    <# Запам'ятовує result і останню текстову відповідь assistant, без tool_result та thinking. #>
    $type = [string](Get-JsonProp $Obj 'type')
    if ($type -eq 'result') { $R.Result = $Obj }
    if ($type -eq 'assistant') {
        $message = Get-JsonProp $Obj 'message'
        $parts = @(foreach ($block in @(Get-JsonProp $message 'content')) {
            if ((Get-JsonProp $block 'type') -eq 'text') { [string](Get-JsonProp $block 'text') }
        })
        $R.AssistantText = $parts -join "`n"
    }
}

function Protect-ClaudeText([string]$Text) {
    <# Знеособлює вміст до будь-якого запису діагностики, включно з іменами секретних полів. #>
    $patterns = @(
        ('ey' + 'J[A-Za-z0-9_-]{10,}'), ('s' + 'k-[A-Za-z0-9_-]{16,}'),
        ('g' + 'h[pousr]_[A-Za-z0-9]{20,}'), ('github' + '_pat_[A-Za-z0-9_]{20,}'),
        ('(?is)BE' + 'GIN [A-Z ]*PRIVATE KEY.*?(?:END [A-Z ]*PRIVATE KEY|\z)'),
        # Значення секретного поля в будь-якій формі: JSON у лапках (закривальні лапки імені перед `:`), YAML, `ключ=значення`,
        # заголовок `Authorization: …`; ім'я — будь-яке, що містить слово секрету. Значення в лапках — до закривальних, інакше до кінця рядка.
        ('(?im)[A-Za-z0-9_.-]*(?:to' + 'ken|sec' + 'ret|pass' + 'w(?:or)?d|pwd|api[_-]?key|authori[sz]ation|credential|cookie|private[_-]?key)[A-Za-z0-9_.-]*[''"]?\s*[:=]\s*(?:"(?:[^"\\\r\n]|\\.)*"?|''[^''\r\n]*''?|[^\r\n]*)'),
        '(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}',
        ('(?im)re' + 'fresh_token[^\r\n]*')
    )
    foreach ($pattern in $patterns) { $Text = [regex]::Replace($Text, $pattern, '<токен>') }
    $Text
}

function Save-ClaudeNoReport($M, [string]$Id, $R) {
    <# Зберігає код, тип result і хвіст відповіді для стану ноутбука, який читає диспетчер. #>
    $value = $null
    if ($null -ne $R.Result) {
        $property = $R.Result.PSObject.Properties['result']
        if ($null -ne $property) { $value = $property.Value }
    }
    $kind = $(if ($null -eq $value) { 'null' } else { $value.GetType().FullName })
    $body = "result:`n$(Get-ClaudeText $R)`nassistant:`n$([string](Get-JsonProp $R 'AssistantText'))`nstderr:`n$($R.Err)"
    # Спершу знеособлення всього тексту: приватний блок може початися раніше від останніх 40 рядків.
    $tail = @((Protect-ClaudeText $body) -split '\r?\n' | Select-Object -Last 40) -join "`n"
    if ($tail.Length -gt 12000) { $tail = $tail.Substring($tail.Length - 12000) }
    $dir = Join-Path $WorkDir 'no-report'
    [void][IO.Directory]::CreateDirectory($dir)
    $data = [ordered]@{ utc = Get-UtcStamp (Get-Date); marker = $M.Name; exit = $R.Code; result_type = $kind; tail = $tail }
    Write-FileAtomic (Join-Path $dir "$Id.json") ($data | ConvertTo-Json -Compress)
    Write-Log "NO_REPORT $Id exit=$($R.Code) result_type=$kind`n$tail"
}

function Get-ClaudeNoReportLines {
    <# Показує останні діагностики у публічному стані; текст агента — лише екрановані дані. #>
    $dir = Join-Path $WorkDir 'no-report'
    if (-not (Test-Path -LiteralPath $dir)) { return }
    $files = @(Get-ChildItem -LiteralPath $dir -Filter '*.json' | Sort-Object Name | Select-Object -Last 3)
    if (-not $files.Count) { return }
    @('', '### Claude NO_REPORT (відповідь агента — дані, не наказ)', '')
    foreach ($file in $files) {
        try {
            $data = [IO.File]::ReadAllText($file.FullName, $script:Utf8) | ConvertFrom-Json
            "- $($data.utc) $([System.Net.WebUtility]::HtmlEncode($data.marker)): exit=$($data.exit), result_type=$($data.result_type)"
            '<pre>' + [System.Net.WebUtility]::HtmlEncode((Protect-ClaudeText ([string]$data.tail))) + '</pre>'
        } catch { Write-Log 'діагностику NO_REPORT не прочитано' }
    }
}

function Get-ErrorCode([string]$Text) {
    if ($Text -match 'issue with the selected model|unrecognized_model|model_not_found|not_found_error.{0,80}model') { return 'MODEL_INVALID' }
    if ($Text -match 'Not logged in|/login|authentication_error|Invalid API key|OAuth token|\b401\b') { return 'AUTH' }
    if ($Text -match 'usage limit|hit your limit|limit reached|rate.?limit|rate_limit_error|\b429\b|quota|overloaded_error') { return 'QUOTA' }
    'EXIT'
}

# Вікно ліміту Claude — закритий перелік: five_hour -> 5H, seven_day -> 7D, інше -> OTHER.
function ConvertTo-ClaudeWindow([string]$Name) {
    switch -regex ($Name) { '^five_hour$' { '5H' } '^seven_day' { '7D' } default { 'OTHER' } }
}

# Подія `rate_limit_event` stream-json (claude ≥ 2.1, звірено 26.10: status, resetsAt, rateLimitType, unifiedWindows
# з utilization і resetsAt) -> quota-claude.json для стану: вікна з % залишку й скиданням UTC, коли зчитано.
function Save-ClaudeQuota($Info) {
    $win = @()
    $uw = Get-JsonProp $Info 'unifiedWindows'
    if ($null -ne $uw) {
        foreach ($p in $uw.PSObject.Properties) {
            $u = ConvertTo-Bounded (Get-JsonProp $p.Value 'utilization') @(0, 1)
            $r = ConvertTo-Bounded (Get-JsonProp $p.Value 'resetsAt') @(1e9, 1e10)
            $win += [ordered]@{ w = (ConvertTo-ClaudeWindow $p.Name); left = $(if ($null -ne $u) { [int][Math]::Round(100 - 100 * $u) } else { '?' })
                reset = $(if ($null -ne $r) { Get-UtcStamp ([DateTimeOffset]::FromUnixTimeSeconds([long]$r).UtcDateTime) } else { '' }) }
        }
    }
    $st = [string](Get-JsonProp $Info 'status')
    $q = [ordered]@{ read = (Get-UtcStamp (Get-Date)); status = $(if ($st -cmatch '^[a-z_]{1,30}$') { $st } else { '?' }); windows = $win; refused = ''; reset = '' }
    $old = Read-ClaudeQuota
    if ($null -ne $old) { $q.refused = [string](Get-JsonProp $old 'refused'); $q.reset = [string](Get-JsonProp $old 'reset') }
    try { Write-FileAtomic (Join-Path $WorkDir 'quota-claude.json') ($q | ConvertTo-Json -Compress -Depth 4) } catch { $null = $_ }
}

# `claude -p` без межі часу: зупиняє лише завислість (жодної прийнятої події stream-json довше за поріг — і після
# закриття stdout, доки процес живий) чи неприйняте зусилля (попередження в stderr: claude його ігнорує й бере типове —
# це була б підміна). Подія — рядок stdout, що розбирається як JSON з полем type; решта лише в claude.jsonl.
function Invoke-Claude([string]$Exe, [string[]]$ArgList, [string]$Prompt, [string]$RunDir, [string]$StatePath, [string]$StateHead, [string]$Marker, [string]$Slot) {
    $hang = Get-Limit $script:Limits 'HangMinutes' 'claude_hang_minutes'
    $psi = New-StartInfo $Exe $ArgList $RepoDir
    $psi.RedirectStandardInput = $true
    # .NET Framework створює StandardInput з AutoFlush: BOM пишеться вже під час Start.
    $stdinEncoding = [Console]::InputEncoding
    try {
        [Console]::InputEncoding = $script:Utf8
        $p = [System.Diagnostics.Process]::Start($psi)
    } finally { [Console]::InputEncoding = $stdinEncoding }
    $start = ''; try { $start = Get-UtcStamp $p.StartTime } catch { $null = $_ }
    Write-FileAtomic $StatePath ($StateHead + ' ' + (([ordered]@{ pid = $p.Id; start = $start; marker = $Marker; slot = $Slot; retakes = (Get-Retakes $StatePath) }) | ConvertTo-Json -Compress))
    $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $script:Utf8)
    $w.Write($Prompt)
    $w.Close()
    $log = Join-Path $RunDir 'claude.jsonl'; $ev = Join-Path $RunDir 'events.tsv'; $errLog = Join-Path $RunDir 'claude.stderr.txt'
    $res = [pscustomobject]@{ Code = 0; Kind = ''; Result = $null; AssistantText = ''; Err = ''; Limit = $null }
    $err = New-Object System.Text.StringBuilder
    $last = Get-Date
    $outTask = $null; $errTask = $null; $outDone = $false; $errDone = $false
    while ($true) {
        if (-not $outDone -and $null -eq $outTask) { $outTask = $p.StandardOutput.ReadLineAsync() }
        if (-not $errDone -and $null -eq $errTask) { $errTask = $p.StandardError.ReadLineAsync() }
        $left = ($last.AddMinutes($hang) - (Get-Date)).TotalMilliseconds
        if ($left -le 0) { $res.Kind = 'HANG'; break }
        $ms = [int][Math]::Min($left, 60000)
        $wait = [System.Threading.Tasks.Task[]]@(@($outTask, $errTask) | Where-Object { $null -ne $_ })
        if ($wait.Count -eq 0) {
            # Обидва потоки закрито, процес ще живий: той самий поріг завислості, без окремої межі.
            if ($p.WaitForExit($ms)) { break }
            continue
        }
        $i = [System.Threading.Tasks.Task]::WaitAny($wait, $ms)
        if ($i -lt 0) {
            # stdout міг лишитись відкритим у нащадка (сервер, піднятий сесією) після кінця claude: це не завислість.
            if ($p.HasExited) { break }
            continue
        }
        # Порядок у $wait: stdout (поки не закритий), далі stderr (поки не закритий) — тож stderr завжди останній.
        if ($null -ne $errTask -and $i -eq $wait.Count - 1) {
            $line = $errTask.Result; $errTask = $null
            if ($null -eq $line) { $errDone = $true; continue }
            [System.IO.File]::AppendAllText($errLog, $line + "`n", $script:Utf8)
            if ($err.Length -lt 65536) { [void]$err.Append($line).Append("`n") }
            if ($line -match 'Unknown --effort value') { $res.Kind = 'EFFORT_INVALID'; break }
            continue
        }
        $line = $outTask.Result; $outTask = $null
        if ($null -eq $line) { $outDone = $true; continue }
        [System.IO.File]::AppendAllText($log, $line + "`n", $script:Utf8)
        if ($line -match 'Unknown --effort value') { $res.Kind = 'EFFORT_INVALID'; break }
        $type = ''; $obj = $null
        if ($line -match '^\s*\{') {
            try {
                $obj = $line | ConvertFrom-Json -ErrorAction Stop
                $tp = [string](Get-JsonProp $obj 'type')
                if ($tp -cmatch '^[a-z_]{1,40}$') { $type = $tp }
            } catch { $null = $_ }
        }
        if (-not $type) { continue }
        $last = Get-Date
        [System.IO.File]::AppendAllText($ev, $last.ToString('s') + "`t" + $type + "`n", $script:Utf8)
        Read-ClaudeEvent $res $obj
        if ($type -eq 'rate_limit_event') {
            $info = Get-JsonProp $obj 'rate_limit_info'
            if ($null -ne $info) { $res.Limit = $info; Save-ClaudeQuota $info }
        }
    }
    if ($res.Kind) { Stop-Tree $p }
    $res.Code = $(if ($p.HasExited) { $p.ExitCode } else { -1 })
    $res.Err = $err.ToString()
    $res
}

function Complete-Task($M, [string]$StatePath, [string]$Id, [string]$Code, [string]$Branch = '', [string]$Sha = '') {
    if ($Code -eq 'AUTH') { Add-HealthAlert 'AUTH' 'CLAUDE' }
    if ($Code -eq 'ENGINE_MISSING') { Add-HealthAlert 'ENGINE' 'CLAUDE' }
    $line = $(if ($Code -eq 'DONE') { "GEMINI ОБГОРТКА: ГОТОВО $Branch $Sha МОДЕЛЬ $($M.Model)" }
              else { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) $Code" })
    if (-not (Add-Line $line)) { $Code = 'LINE_REJECTED' }
    $runDir = Join-Path (Join-Path $WorkDir 'runs') $Id
    if (Test-Path -LiteralPath $runDir) {
        Write-FileAtomic (Join-Path $runDir 'result.json') (([ordered]@{ marker = $M.Name; sha = $M.Sha; code = $Code; branch = $Branch; head = $Sha; end = (Get-Date).ToString('s') }) | ConvertTo-Json -Compress)
    }
    Write-FileAtomic $StatePath "DONE $Id $Code"
    Remove-Claim $StatePath
    Write-Log "позначка $($M.Name): $Code"
}

# Відмова за квотою: позначка чекає скидання (resetsAt останньої `rate_limit_event` зі status rejected; інакше час
# із тексту `…|<unix>`; нема — quota_wait_minutes), рядок QUOTA0_CLAUDE_M<хв>; нова спроба продовжить гілку наряду.
# Понад MaxRetakes — $false (кінець QUOTA, як до смуг).
function Enter-ClaudeQuotaWait($M, [string]$StatePath, [string]$Id, $R, [string]$Text) {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $until = 0L
    if ($null -ne $R.Limit) {
        $ra = ConvertTo-Bounded (Get-JsonProp $R.Limit 'resetsAt') @(1e9, 1e10)
        if ($null -ne $ra -and [string](Get-JsonProp $R.Limit 'status') -ne 'allowed') { $until = [long]$ra }
    }
    if ($until -le $now -and $Text -match '\|([0-9]{10})\b') { $until = [long]$Matches[1] }
    $known = $until -gt $now
    if (-not $known) { $until = $now + [long](60 * (Get-Limit $script:Limits 'QuotaWaitMinutes' 'quota_wait_minutes')) }
    $n = Set-MarkerWait $M $until @{ retake = $true; group = 'CLAUDE' }
    if ($null -eq $n) { return $false }
    $q = Read-ClaudeQuota
    $o = [ordered]@{ read = (Get-UtcStamp (Get-Date)); status = 'rejected'; windows = @(); refused = (Get-UtcStamp (Get-Date)); reset = $(if ($known) { Get-UtcStamp ([DateTimeOffset]::FromUnixTimeSeconds($until).UtcDateTime) } else { '' }) }
    if ($null -ne $q) { $o.read = [string]$q.read; $o.status = [string]$q.status; $o.windows = @(Get-JsonProp $q 'windows') }
    try { Write-FileAtomic (Join-Path $WorkDir 'quota-claude.json') ($o | ConvertTo-Json -Compress -Depth 4) } catch { $null = $_ }
    $mins = [int][Math]::Ceiling(($until - $now) / 60)
    [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) QUOTA0_CLAUDE_M$mins")
    $runDir = Join-Path (Join-Path $WorkDir 'runs') $Id
    Write-FileAtomic (Join-Path $runDir 'result.json') (([ordered]@{ marker = $M.Name; sha = $M.Sha; code = 'QUOTA_WAIT'; until = $until; retake = $n; end = (Get-Date).ToString('s') }) | ConvertTo-Json -Compress)
    Write-Log "позначка $($M.Name): квота Claude, чекає до $(Get-UtcStamp ([DateTimeOffset]::FromUnixTimeSeconds($until).UtcDateTime)) (повернення $n)"
    $true
}

function Invoke-Task($M, $Job) {
    $statePath = Get-StatePath (Get-MarkerKey $M)
    $id = [string]$Job.id
    $main = Get-RefSha 'refs/remotes/origin/main'
    $taskPath = Get-AutoTaskPath $M.Slug
    if (-not $main -or (Invoke-Git @('merge-base', '--is-ancestor', $M.Sha, $main) -AllowFail).Code -ne 0) { return (Complete-Task $M $statePath $id 'NOT_ON_MAIN') }
    if (-not (Test-TaskFile $M.Sha $taskPath)) { return (Complete-Task $M $statePath $id 'NO_TASK_FILE') }
    if ($M.Claude -notmatch $script:ModelPattern) { return (Complete-Task $M $statePath $id 'MODEL_INVALID') }
    $review = Get-AutoReviewState $M.Slug
    if ($review -eq 'REVIEW_API') { Enter-ReviewWait $M; return }
    if ($review -ne 'LIVE') { return (Complete-Task $M $statePath $id $review) }
    $exe = Find-Exe $ClaudeExe
    if (-not $exe) { return (Complete-Task $M $statePath $id 'ENGINE_MISSING') }
    try { $taskText = Add-AutoTaskContext $M.Slug ((Invoke-Git @('cat-file', 'blob', "$($M.Sha):$taskPath")).Out) $M.Sha }
    catch { Enter-ReviewWait $M; Remove-Claim $statePath; return }
    if (Test-AutoPlanEmpty $M.Slug $taskText) { return (Complete-Task $M $statePath $id 'EMPTY_PLAN') }
    $cont = Get-ContinueBranch $M.Slug
    $runDir = Join-Path (Join-Path $WorkDir 'runs') $id
    [void](New-Item -ItemType Directory -Force -Path $runDir)
    # Копія задачі — лише після звірки голови: мертва позначка її не отримує; після звіту — геть.
    try {
        $taskDir = Get-TaskCopyDir $id
        [void](New-TaskCopy $taskDir 'refs/remotes/origin/main' $taskText)
        Invoke-ClaudeTask $M $Job $exe $taskText $cont $runDir $statePath $taskDir
    } finally {
        if (Close-TaskCopy @('--remotes')) { [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) COPY_KEPT") }
    }
}

# Тека задачі `<WorkDir>\w\<прогін>`: копія `repo` і `tmp` (queue_lanes.ps1, New-TaskCopy).
function Get-TaskCopyDir([string]$Id) { Join-Path (Join-Path $WorkDir 'w') $Id }

# Прогін claude у копії задачі ($RepoDir) і кінець за звітом.
function Invoke-ClaudeTask($M, $Job, [string]$Exe, [string]$TaskText, [string]$Cont, [string]$RunDir, [string]$StatePath, [string]$TaskDir) {
    $id = [string]$Job.id
    $prompt = Get-Prompt $M $TaskText $Cont $TaskDir
    [System.IO.File]::WriteAllText((Join-Path $runDir 'prompt.txt'), $prompt, $script:Utf8)
    $a = @('-p', '--model', $M.Claude)
    if ($M.Effort) { $a += @('--effort', $M.Effort) }
    $a += @('--permission-mode', 'auto', '--output-format', 'stream-json', '--verbose')
    Write-Log "позначка $($M.Name): старт $id у слоті $($Job.slot), claude $($a -join ' ')$(if ($cont) { ", продовжує $cont" })"
    try {
        $r = Invoke-Claude $Exe $a $prompt $runDir $statePath "STARTED $id" $M.Name ([string]$Job.slot)
    } catch {
        Write-Log "claude: $($_.Exception.Message)"
        return (Complete-Task $M $statePath $id 'CRASH')
    }
    if ($r.Kind) { return (Complete-Task $M $statePath $id $r.Kind) }
    $text = Get-ClaudeText $r; $isError = $false
    if ($null -ne $r.Result) {
        $pe = $r.Result.PSObject.Properties['is_error']; if ($null -ne $pe) { $isError = [bool]$pe.Value }
    }
    $rep = Get-ClaudeReport $r
    if ($null -ne $rep -and $rep.Branch -and (Test-ClaudeBranch $rep.Branch) -and (Get-RemoteSha $rep.Branch)) {
        [System.IO.File]::WriteAllText((Get-BranchPath $M.Slug), $rep.Branch, $script:Utf8)
    }
    if ($null -ne $rep -and $rep.Kind -eq 'DONE') {
        if (-not (Test-ClaudeBranch $rep.Branch)) { return (Complete-Task $M $statePath $id 'BAD_BRANCH') }
        $remote = Get-RemoteSha $rep.Branch
        if (-not $remote -or -not $remote.StartsWith($rep.Sha, [StringComparison]::Ordinal)) { return (Complete-Task $M $statePath $id 'NO_PUSH') }
        $rep.Sha = $remote
        return (Complete-Task $M $statePath $id 'DONE' $rep.Branch $rep.Sha)
    }
    if ($null -ne $rep) {
        # BLOCKED без гілки: причину знає лише останній рядок агента — він іде в #1856 (blocked-reasons.json), як у gemini_run.ps1.
        if ($rep.Kind -eq 'BLOCKED' -and -not (Test-ClaudeBranch $rep.Branch) -and $text) {
            $reason = @($text -split "`n" | Where-Object { $_.Trim() -cmatch '^(?:НОУТБУК )?ЗАБЛОКОВАНО' } | Select-Object -Last 1)
            if ($reason.Count -eq 0) { $reason = @($text -split "`n" | Where-Object { $_.Trim() } | Select-Object -Last 1) }
            try { Add-Note (Join-Path $GeminiOutDir 'blocked-reasons.json') "claude/$($M.Slug)" ([string]$reason[0]) } catch { Write-Log "причина BLOCKED не записана: $($_.Exception.Message)" }
        }
        return (Complete-Task $M $statePath $id 'BLOCKED')
    }
    if ($isError -or $r.Code -ne 0) {
        $code = Get-ErrorCode ($text + "`n" + $r.Err)
        if ($code -eq 'QUOTA' -and (Enter-ClaudeQuotaWait $M $statePath $id $r ($text + "`n" + $r.Err))) { return }
        return (Complete-Task $M $statePath $id $code)
    }
    Save-ClaudeNoReport $M $id $r
    Complete-Task $M $statePath $id 'NO_REPORT'
}

# Відмова до STARTED: лічильник повернень і межа ті самі, що в квоти; на межі — кінцевий стан CRASH і рядок диспетчерові.
function Close-FailedStart($M, [string]$Id, [string]$StatePath) {
    if ((Step-FailedStart $M $StatePath) -ne 'LIMIT') { return }
    Write-Log "позначка $($M.Name): відмов до запуску понад $script:MaxRetakes — кінець CRASH"
    Complete-Task $M $StatePath $Id 'CRASH'
}

# Прогін, перерваний вимкненням чи зупинкою задачі (замок його слота вільний): живий claude без нагляду зупиняється,
# диспетчерові — INTERRUPTED. Наряд, чий процес ще живий (слот зайнятий), не чіпаємо.
function Resume-Interrupted {
    foreach ($f in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.txt' -File -ErrorAction SilentlyContinue)) {
        $text = [System.IO.File]::ReadAllText($f.FullName, $script:Utf8)
        if ($text -notmatch '^STARTED ([0-9]{8}-[0-9]{6}-[0-9a-f]{12}) (\{.*\})\s*$') { continue }
        $id = $Matches[1]
        $j = $null; try { $j = $Matches[2] | ConvertFrom-Json } catch { $null = $_ }
        $slot = [string](Get-JsonProp $j 'slot')
        if ((Test-SlotName $slot @('claude')) -and -not (Test-LockFree (Join-Path $script:SlotDir "$slot.lock"))) { continue }
        $marker = [string](Get-JsonProp $j 'marker')
        try {
            $p = Get-Process -Id ([int]$j.pid) -ErrorAction Stop
            if ((Get-UtcStamp $p.StartTime) -eq [string]$j.start) { Stop-Tree $p; Write-Log "перерваний $id : claude $($j.pid) зупинено" }
        } catch { $null = $_ }
        $res = Join-Path (Join-Path (Join-Path $WorkDir 'runs') $id) 'result.json'
        $slug = $(if ($marker -match '^gemini-queue/([^/]+)/') { $Matches[1] } else { '' })
        if ($slug -cmatch $script:SlugPattern) { [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$slug INTERRUPTED") }
        else { Write-Log "перерваний $id : позначка невідома" }
        if (Test-Path -LiteralPath (Split-Path -Parent $res)) {
            if (-not (Test-Path -LiteralPath $res)) { Write-FileAtomic $res (([ordered]@{ marker = $marker; code = 'INTERRUPTED'; end = (Get-Date).ToString('s') }) | ConvertTo-Json -Compress) }
        }
        Write-FileAtomic $f.FullName "DONE $id INTERRUPTED"
        Remove-Claim $f.FullName
    }
}

# --- вимкнення ----------------------------------------------------------------------------------------------------

# Рушій Gemini зайнятий: задача gemini-run виконується (власникові без адміна її стан не видно, 10013) чи в heartbeat
# є узята позначка в будь-якій смузі.
function Test-GeminiBusy {
    $st = @(Get-TaskRows | Where-Object { $_.Name -eq 'gemini-run' } | ForEach-Object { $_.State })
    if ($st.Count -gt 0 -and $st[0] -ne '?') { return ($st[0] -eq 'Running') }
    $b = Read-GeminiBeat
    if ($b.Marker) { return $true }
    @($b.Lanes | Where-Object { $_.Busy.Count -gt 0 }).Count -gt 0
}

# Свої наряди йдуть: живий процес наряду чи зайнятий слот смуги Claude.
function Test-ClaudeBusy {
    if ($null -ne $script:Workers -and @($script:Workers | Where-Object { -not $_.Proc.HasExited }).Count -gt 0) { return $true }
    @(Get-BusySlots 'claude' @()).Count -gt 0
}

# Робота на ноутбуці: свій наряд чи наряд gemini-run йде, або в черзі є позначка, яку візьмуть. Не робота — позначка в стані
# DONE (знято, STALE, виконана), у чеканні квоти (WAIT, скидання ще не настало) і на рушії з нульовою квотою: Claude —
# вікно квоти з left 0 і скиданням у майбутньому чи свіжа відмова з майбутнім скиданням, Codex — відмова з майбутнім
# скиданням (heartbeat). Стан позначок смуг codex/agy — тека стану gemini-run (-GeminiStateDir).
function Test-FutureUtc([string]$Utc) {
    $Utc -cmatch $script:UtcRx -and [datetime]::ParseExact($Utc, "yyyy-MM-dd'T'HH:mm:ss'Z'", [cultureinfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal) -gt [datetime]::UtcNow
}

function Test-ClaudeQuotaZero {
    $cq = Read-ClaudeQuota
    if ($null -eq $cq) { return $false }
    foreach ($w in @(Get-JsonProp $cq 'windows')) { if ($null -ne $w -and [string]$w.left -eq '0' -and (Test-FutureUtc ([string]$w.reset))) { return $true } }
    ([string](Get-JsonProp $cq 'refused')) -ne '' -and (Test-FutureUtc ([string](Get-JsonProp $cq 'reset')))
}

function Get-MarkerStateIn($M, [string]$Dir) {
    $keep = $script:StateDir; $script:StateDir = $Dir
    try { Get-MarkerState $M } finally { $script:StateDir = $keep }
}

function Test-IdleBusy($G) {
    if (Test-ClaudeBusy) { return $true }
    if (Test-GeminiBusy) { return $true }
    $claudeZero = Test-ClaudeQuotaZero
    $codexZero = $null -ne $G.Codex -and (Test-FutureUtc ([string]$G.Codex.Reset))
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    foreach ($m in @(Get-Markers | Where-Object { $_.Valid })) {
        if (($now - $m.Time) -gt $MarkerMaxAgeDays * 86400) { continue }
        $st = $(if ($m.Lane -eq 'claude') { Get-MarkerState $m } else { Get-MarkerStateIn $m $GeminiStateDir })
        if (-not (Test-MarkerReady $st)) { continue }
        if (($m.Lane -eq 'claude' -and $claudeZero) -or ($m.Lane -eq 'codex' -and $codexZero)) { continue }
        return $true
    }
    $false
}

# Рядок простою в стані ноутбука (#1856): з якого часу, скільки, чи дійшов рядок; нема простою — остання робота.
function Get-IdleLines {
    $j = $null
    try { $j = [System.IO.File]::ReadAllText((Join-Path $script:StateDir 'idle.json'), $script:Utf8) | ConvertFrom-Json } catch { $null = $_ }
    if ($null -eq $j) { return @('', 'Простій: не виміряно (ще не було проходу)') }
    $since = Get-UtcProp $j 'since'
    if ($since -cmatch $script:UtcRx) {
        return @('', "Простій: з $since · $(Get-Minutes $since) хв · рядок ПРОСТІЙ $(if ((Get-JsonProp $j 'sent') -eq $true) { 'надіслано' } else { 'ще не надіслано' })")
    }
    $b = Get-UtcProp $j 'busy_utc'
    @('', "Простій: нема (остання робота $(if ($b -cmatch $script:UtcRx) { $b } else { '?' }))")
}

function Invoke-Off($M) {
    $statePath = Get-StatePath (Get-MarkerKey $M)
    $main = Get-RefSha 'refs/remotes/origin/main'
    if (-not $main -or (Invoke-Git @('merge-base', '--is-ancestor', $M.Sha, $main) -AllowFail).Code -ne 0) {
        [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) NOT_ON_MAIN")
        Write-FileAtomic $statePath 'DONE NOT_ON_MAIN'
        return
    }
    if ((Test-ClaudeBusy) -or (Test-GeminiBusy)) {
        # Стану не пишемо: наступний прохід спробує знову.
        $script:Phase = 'вимкнення чекає рушіїв'
        Write-Log "позначка $($M.Name): рушії зайняті — вимкнення чекає"
        return
    }
    $id = Add-Line "GEMINI ОБГОРТКА: ВИМКНЕНО $($M.Sha)"
    Write-FileAtomic $statePath "OFF $id"
    $script:Phase = 'вимикаю'
    Update-Status -Force
    # Рядок доставляє gemini-publish (раз на хвилину): вимикаємо після доставки або за -OffWaitMinutes.
    $sent = Join-Path (Join-Path $PublishDir 'state') "o-$id.json"
    $until = (Get-Date).AddMinutes($OffWaitMinutes)
    while ($id -and (Get-Date) -lt $until) {
        try { if (([System.IO.File]::ReadAllText($sent, $script:Utf8) | ConvertFrom-Json).sent) { break } } catch { $null = $_ }
        Start-Sleep -Seconds 10
    }
    Write-Log "позначка $($M.Name): вимикаю"
    Invoke-Shutdown
}

# --- планувальник ---------------------------------------------------------------------------------------------------

# Позначка вимкнення: стояла до першого проходу після ввімкнення — BOOT (без вимкнення); виконана (OFF) на першому
# проході після нового ввімкнення — теж один BOOT. Повертає $true, коли вимкнення треба спробувати.
function Test-OffMarker($M) {
    $state = Get-StatePath (Get-MarkerKey $M)
    if (Test-Path -LiteralPath $state) {
        if ($script:FreshBoot -and [System.IO.File]::ReadAllText($state, $script:Utf8).StartsWith('OFF ')) {
            [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) BOOT"); Write-FileAtomic $state 'DONE BOOT'
        }
        return $false
    }
    if (([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - $M.Time) -gt $MarkerMaxAgeDays * 86400) { Write-FileAtomic $state 'STALE'; return $false }
    if ($script:FreshBoot) {
        Write-Log "позначка $($M.Name): була до ввімкнення — не вимикаю"
        [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) BOOT")
        Write-FileAtomic $state 'DONE BOOT'
        return $false
    }
    $true
}

# Один прохід: позначки смуги Claude за порядком черги — у вільні слоти; позначка вимкнення нових нарядів не пускає.
# Повертає число запущених і позначку вимкнення, яку треба спробувати.
function Start-Markers($Workers) {
    $started = 0; $off = $null
    $script:Held = @{}
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $mine = @(Get-Markers | Where-Object { $_.Valid -and $_.Lane -eq 'claude' } | ForEach-Object { Add-ClaudeFields $_ })
    $skipFile = Join-Path $WorkDir 'skipped.json'
    if ($mine.Count -eq 0) { Save-Skips $skipFile; return @(0, $null) }
    $gpuWhy = $null
    $ordered = @(Get-OrderedMarkers $mine)
    foreach ($m in @($ordered | Where-Object { $_.Off })) { if ((Test-OffMarker $m) -and $null -eq $off) { $off = $m } }
    if ($null -ne $off) { return @(0, $off) }
    foreach ($m in @($ordered | Where-Object { -not $_.Off })) {
        $st = Get-MarkerState $m
        if (-not (Test-MarkerReady $st)) { continue }
        if (($now - $m.Time) -gt $MarkerMaxAgeDays * 86400) {
            Write-Log "позначка $($m.Name): коміт старший за $MarkerMaxAgeDays діб — пропущено"
            Write-FileAtomic (Get-StatePath (Get-MarkerKey $m)) 'STALE'
            continue
        }
        # Claude на ноутбуці — лише наряд, якому ноутбук потрібен: GPU чи перелік `claude_laptop` у смуги.json (власник
        # 26.10, 29.10). Решта — хмарним сесіям: рядок диспетчерові, копії й слота нема.
        if (-not $m.Gpu -and $m.Slug -cnotin @($script:Limits.claude_laptop)) {
            Complete-Task $m (Get-StatePath (Get-MarkerKey $m)) (New-Id) 'CLAUDE_NOT_LAPTOP'
            continue
        }
        $slot = Get-FreeSlot 'claude' ([int]$script:Limits.slots['claude']) $Workers
        if (-not $slot) { Add-Skip $m 'нема вільного слота смуги claude'; Add-Hold $script:Held 'SLOTS' 'слоти зайняті' $m.Name; continue }
        if ((@($Workers | Where-Object { $_.Slug -ceq $m.Slug -and -not $_.Proc.HasExited }).Count -gt 0) -or (Test-SlugBusy $m.Slug @('claude'))) { Add-Skip $m 'той самий наряд уже йде в слоті'; continue }
        if ($m.Gpu) {
            if ($null -eq $gpuWhy) { $gpuWhy = Get-GpuBusyReason $Workers }
            if ($gpuWhy) { Add-Skip $m $gpuWhy; Add-Hold $script:Held 'GPU' $script:GpuHoldReason $m.Name; continue }
        }
        $id = New-Id
        if (-not (New-Claim $m $id)) { continue }
        # Усе між claim і STARTED — під одним обліком відмов (retakes, MaxRetakes, CRASH на межі), 10162/10182.
        try {
            $dir = Join-Path (Join-Path $WorkDir 'runs') $id
            [void](New-Item -ItemType Directory -Force -Path $dir)
            $job = @{ id = $id; dir = $dir; slot = $slot; lane = 'claude'; ref = $m.Ref; sha = $m.Sha; time = $m.Time; name = $m.Name
                slug = $m.Slug; model = $m.Model; n = $m.N; cond = $m.Cond; prio = $m.Prio; deadline = $m.Deadline; gpu = $m.Gpu
                claude = $m.Claude; effort = $m.Effort; limits = $script:Limits }
            [void]$Workers.Add((Start-Worker $job $dir))
        } catch {
            Write-Log "позначка $($m.Name): процес наряду не запущено — $($_.Exception.Message)"
            Close-FailedStart $m $id (Get-StatePath (Get-MarkerKey $m))
            continue
        }
        Write-Log "позначка $($m.Name): слот $slot, пріоритет $($m.Prio)$(if ($m.Deadline) { ", строк $($m.Deadline)" })$(if ($m.Gpu) { ', GPU' }) -> $id"
        $started++
        if ($m.Gpu) { $gpuWhy = 'GPU: її щойно взяв наряд цього проходу' }
    }
    Save-Skips $skipFile
    @($started, $null)
}

# Процес наряду: слот (замок на весь прогін), GPU (замок, спільний з gemini-run), прогін (копію задачі дає Invoke-Task).
function Invoke-Worker {
    $job = $script:Job
    $lim = @{}
    foreach ($p in $job.limits.PSObject.Properties) { $lim[$p.Name] = $p.Value }
    $script:Limits = $lim
    $statePath = Get-StatePath "$($job.ref) $($job.sha)"
    $slotLock = Open-Lock (Join-Path $script:SlotDir "$($job.slot).lock")
    if ($null -eq $slotLock) { Remove-Claim $statePath; Write-Log "слот $($job.slot) зайнятий — позначку не взято"; return $script:WorkerSlotBusy }
    $gpu = $null
    $info = Join-Path $script:SlotDir "$($job.slot).json"
    try {
        if ($job.gpu) {
            $gpu = Open-Lock (Get-GpuLockPath)
            $why = $(if ($null -eq $gpu) { 'замок GPU' } elseif (Test-ExternalGpuFree) { '' } else { Get-GpuBusyReason @() })
            if ($why) { Remove-Claim $statePath; Write-Log "GPU зайнята ($why) — $($job.name) лишається в черзі"; return $script:WorkerGpuBusy }
        }
        Write-FileAtomic $info (([ordered]@{ slot = $job.slot; lane = 'claude'; marker = $job.name; slug = $job.slug
                    model = "$($job.claude)$(if ($job.effort) { ' ' + $job.effort })"; since = (Get-UtcStamp (Get-Date)); gpu = [bool]$job.gpu; prio = $job.prio; pid = $PID
                    copy = (Get-TaskCopyDir ([string]$job.id)) }) | ConvertTo-Json -Compress)
        $M = [pscustomobject]@{ Ref = $job.ref; Name = $job.name; Sha = $job.sha; Time = [long]$job.time; Slug = $job.slug; Model = $job.model
            N = [string]$job.n; Cond = [string]$job.cond; Claude = [string]$job.claude; Effort = [string]$job.effort; Gpu = [bool]$job.gpu }
        Set-BrowserGpuPolicy (Join-Path $script:SlotDir ($job.slot + '-browser'))
        Invoke-Task $M $job
        0
    } catch {
        Write-Log "процес наряду $($job.name): $($_.Exception.Message)"
        1
    } finally {
        Remove-Item -LiteralPath $info -Force -ErrorAction SilentlyContinue
        # Помилка до STARTED (робоча копія тощо) не лишає claim: позначка повертається в чергу (10162).
        Close-FailedStart ([pscustomobject]@{ Ref = $job.ref; Name = $job.name; Sha = $job.sha; Slug = $job.slug; Model = $job.model }) ([string]$job.id) $statePath
        if ($null -ne $gpu) { $gpu.Dispose() }
        $slotLock.Dispose()
    }
}

function Main {
    if ($WorkerFile) { $script:Job = Read-WorkerJob $WorkerFile }
    $script:StateDir = Join-Path $WorkDir 'state'
    $script:SlotDir = Join-Path $WorkDir 'slots'
    foreach ($d in @($WorkDir, $script:StateDir, $script:SlotDir, (Join-Path $WorkDir 'runs'), $OutboxDir, $LaneDir)) {
        [void](New-Item -ItemType Directory -Force -Path $d)
    }
    if (-not (Test-OwnerUser)) { Write-Log "запуск під $GeminiUser — відмова"; return 1 }
    $script:NoHooks = Join-Path ([System.IO.Path]::GetTempPath()) ('no-hooks-' + [guid]::NewGuid().ToString('N'))
    $script:HealthAlertDir = $OutboxDir
    if ($WorkerFile) { return (Invoke-Worker) }
    $script:HeartbeatAction = { Update-Status }
    $lockFile = Open-Lock (Join-Path $WorkDir 'lock')
    if ($null -eq $lockFile) { return 0 }
    try {
        $origin = (Invoke-Git @('remote', 'get-url', 'origin')).Out.Trim()
        if (($origin.TrimEnd('/') -replace '\.git$', '') -ne ($RepoUrl.TrimEnd('/') -replace '\.git$', '')) {
            $script:Phase = 'origin клону не той'
            Write-Log "origin клону ($origin) не $RepoUrl — нарядів нема"
            Update-Status -Force
            return 1
        }
        $bootFile = Join-Path $WorkDir 'boot.txt'
        $boot = Get-BootStamp
        $prev = $(if (Test-Path -LiteralPath $bootFile) { [System.IO.File]::ReadAllText($bootFile, $script:Utf8).Trim() } else { '' })
        $script:FreshBoot = ($boot -ne $prev)
        Resume-Interrupted
        $script:Workers = New-Object System.Collections.ArrayList
        $script:Held = @{}
        $first = $true; $clean = $true; $ver = ''
        while ($true) {
            $ver = Get-VersionSwitch
            if ($ver) { Write-VersionSwitch $ver; break }
            $started = 0; $off = $null
            try {
                [void](Invoke-Git @('fetch', '-q', '--prune', '--no-tags', 'origin',
                        '+refs/heads/main:refs/remotes/origin/main',
                        '+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*') -TimeoutMinutes 15)
                $script:Limits = Get-Limits
                # Накопичене — після першого успішного fetch (до нього origin/* застарілі): прохід, що впав на
                # fetch, прибирання не знімає.
                if ($clean) { Clear-TaskCopies (Join-Path $WorkDir 'w') @('--remotes'); $clean = $false }
                Clear-OrphanClaims (Join-Path $WorkDir 'runs')
                $r = Start-Markers $script:Workers
                $started = $r[0]; $off = $r[1]
                Update-HoldSignals $script:Held { param($l) Add-Line $l }
                $busy = ($started -gt 0) -or ($null -ne $off) -or ($script:Workers.Count -gt 0)
                if (-not $busy) { $busy = [bool](Test-IdleBusy (Read-GeminiBeat)) }
                Update-Idle $busy { param($l) [bool](Add-Line $l) } $script:FreshBoot
            } catch { Add-HealthException $_.Exception; Write-Log "прохід: $($_.Exception.Message)" }
            if ($first) { Write-FileAtomic $bootFile $boot; $script:FreshBoot = $false; $first = $false }
            foreach ($w in @($script:Workers | Where-Object { $_.Proc.HasExited })) { $script:Workers.Remove($w) }
            $script:Phase = $(if ($script:Workers.Count -gt 0) { "веде наряди: $($script:Workers.Count)" } else { 'чекає позначки' })
            if ($null -ne $off) { Invoke-Off $off }
            Update-Status -Force:($started -gt 0)
            if ($script:Workers.Count -eq 0 -and $started -eq 0) { break }
            Wait-Workers $script:Workers (Get-Limit $script:Limits 'PollMinutes' 'poll_minutes')
        }
        $script:Phase = $(if ($ver) { "оновлення версії: $ver" } else { 'чекає позначки' })
        Update-Status -Force
        0
    } catch {
        Add-HealthException $_.Exception; Write-Log "збій обгортки: $($_.Exception.Message)"
        $script:Phase = 'збій'
        Update-Status -Force
        1
    } finally {
        $lockFile.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Main) }
