#Requires -Version 5.1
<#
.SYNOPSIS
Обгортка Gemini (наряди М.2, М.9-Е), сторона `gemini`: планувальник смуг Codex і `agy` — позначки черги -> прогони
водночас (до N у смузі) -> бандл гілки `gemini/<наряд>` на кожен.

.DESCRIPTION
Задача планувальника під користувачем Windows `gemini` (ізоляція ОС; входу в GitHub і Claude нема, ключів нема), раз на
5 хв, без межі часу задачі. Запуск — планувальник: живе, доки йде хоч один його наряд, і опитує чергу раз на
`poll_minutes`; без нарядів — виходить (наступний запуск — за 5 хв). Наряд — окремий процес того самого скрипта
(`-WorkerFile`) зі своїм слотом, текою запуску й робочою копією (git worktree клону). Спільне з `claude_run.ps1` —
`queue_lanes.ps1` (позначки, порядок, смуги, слоти, межі з `смуги.json` на `origin/main`, чекання квоти, замок GPU).
  1. перевірка ізоляції за `GEMINI.md` (whoami, `net session`, чужі профілі й диски, змінні з ключами);
  2. `git fetch` без входу: `main`, `gemini/*` і позначки черги `gemini-queue/<наряд>/<модель>/<спроба>[/<умови>]`, які
     ставить лише диспетчер; позначка має вказувати на коміт із `main`, текст наряду — лише `аудит/наряди/<наряд>.md` з нього;
  2а. смуга за назвою моделі: `gpt-<модель>[-<зусилля>]` — Codex (`codex exec`; зусилля — none|minimal|low|medium|high|
      xhigh|max|ultra, відмову `codex exec` обгортка віддає кодом EFFORT_INVALID, без підміни), інша — `agy`; квота `agy`
      як дані (`agy -p "/usage"`, 0 ходів, не частіше за `usage_minutes`): група моделі з 0 % — позначка чекає скидання
      (рядок QUOTA0 диспетчерові раз), після скидання її бере та сама смуга; відмова за квотою посеред прогону (429) —
      так само, до MaxRetakes разів; коли задано `-CodexFallbackModel`, `agy` на 0 % замінює Codex з цією моделлю;
  3. гілка `gemini/<наряд>` від свіжого `main` (чи від уже опублікованої `gemini/<наряд>` — доробка; чи від голови
     прогону, зупиненого квотою);
  4. прогін `agy` з межею часу; хід без звіту чи звіт, що не збігся з гілкою, — догонка тієї самої розмови;
     Codex межі часу прогону не має: його зупиняє лише завислість (нема нових подій `--json` довше за поріг);
  5. бандл гілки й стан (лише коди й числа) у теці обміну; публікує їх окрема задача власника `gemini_publish.ps1`;
     heartbeat.json — смуги, слоти, квота груп моделей із часом скидання в UTC (для стану ноутбука в `claude_run.ps1`).
Нічого не пушить; ізоляцію не створює й не змінює. Налаштування — `НАЛАШТУВАННЯ.md` поруч.
#>
[CmdletBinding()]
param(
    [string]$RepoDir = (Join-Path $env:USERPROFILE 'kod-shi-data'),
    [string]$RunsDir = (Join-Path $env:USERPROFILE 'gemini-runs'),
    [string]$OutDir = 'C:\Users\Public\gemini\out',
    [string]$LaneDir = 'C:\Users\Public\gemini\lanes',
    [string]$RepoUrl = 'https://github.com/mightyrochy/kod-shi-data',
    [string]$ExpectedUser = 'gemini',
    [string]$GitExe = 'git',
    [string]$AgyExe = 'agy',
    [string]$CodexExe = 'codex',
    [string]$CodexFallbackModel = '',
    [switch]$EnableCodex,
    [ValidateSet('stream', 'print')]
    [string]$Mode = 'stream',
    [double]$TurnMinutes = 120,
    [double]$TotalMinutes = 180,
    [double]$CodexStallMinutes = 60,
    [double]$PollMinutes = 2,
    [double]$UsageMinutes = 15,
    [double]$QuotaWaitMinutes = 60,
    [int]$MaxNudges = 4,
    [double]$QuotaMinutes = 2,
    [int]$MarkerMaxAgeDays = 7,
    [switch]$NoPrintTimeoutFlag,
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

# Смуги цього планувальника; Claude — `claude_run.ps1` під власником.
$script:Lanes = @('codex', 'agy')
# Імена моделей для рядка ПУЛИ (9740): лише родини gemini/claude/gpt; той самий шаблон у gemini_publish.ps1.
$script:PoolModelPattern = '^(gemini|claude|gpt)-[a-z0-9.-]{1,36}$'
# `agy -p "/usage"` без ходу моделі й без витрати квоти — з v1.1.11 (changelog agy, 7.08.2026): перелік у НАЛАШТУВАННЯ.md.
$script:UsageMinVersion = [version]'1.1.11'
# Каскад моделей «проєктування» (pro): наступна за пулом після самої моделі позначки; далі лише Codex (-CodexFallbackModel).
$script:ClaudeCascadeModel = 'claude-opus-5-5-high'
# Суфікс-зусилля позначки gpt-*: що `codex exec` не приймає, то відмова (EFFORT_INVALID), а не тиха підміна.
$script:CodexEfforts = 'none|minimal|low|medium|high|xhigh|max|ultra'
# Родини моделей: група /usage без власних слів («Gemini Models», «Claude and GPT models») — спільна для родини.
$script:Families = @('gemini', 'claude', 'gpt')
$script:AgyVersionDone = $false; $script:AgyVersion = $null; $script:AgyModels = $null
$script:Limits = $null

# --- дрібні помічники ---------------------------------------------------------------------------------------------

function Write-Log([string]$Text) {
    <# Рядок у wrapper.log. Пишуть водночас планувальник і процеси нарядів: зайнятий файл — кілька спроб, потім рядок
    губиться, а не валить наряд. #>
    $tag = $(if ($WorkerFile) { "[$PID] " } else { '' })
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}{2}' -f (Get-Date), $tag, $Text
    for ($i = 0; $i -lt 20; $i++) {
        try { [System.IO.File]::AppendAllText((Join-Path $RunsDir 'wrapper.log'), $line + "`n", $script:Utf8); return } catch { Start-Sleep -Milliseconds 50 }
    }
}

# JSON-рядок лише з ASCII: stdin процесу в .NET Framework кодується кодовою сторінкою консолі.
function ConvertTo-JsonString([string]$Text) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append('"')
    foreach ($c in $Text.ToCharArray()) {
        $i = [int]$c
        if ($c -eq '"') { [void]$sb.Append('\"') }
        elseif ($c -eq '\') { [void]$sb.Append('\\') }
        elseif ($i -lt 0x20 -or $i -gt 0x7e) { [void]$sb.Append(('\u{0:x4}' -f $i)) }
        else { [void]$sb.Append($c) }
    }
    [void]$sb.Append('"')
    $sb.ToString()
}

# Запуск без межі часу (Codex): процес зупиняє лише завислість — жодного нового рядка stdout (події `--json`) довше за
# $StallMinutes. Кожен рядок одразу йде в $LogFile, а мітка часу й тип події — в $EventsFile (щоб поріг вивіряти за прогонами).
function Invoke-NativeUntilStall([string]$Exe, [string[]]$Arguments, [string]$WorkDir, [double]$StallMinutes, [string]$LogFile, [string]$EventsFile) {
    $psi = New-StartInfo $Exe $Arguments $WorkDir
    $p = [System.Diagnostics.Process]::Start($psi)
    $err = $p.StandardError.ReadToEndAsync()
    $out = New-Object System.Text.StringBuilder
    $last = Get-Date
    $stalled = $false
    $pending = $null
    while ($true) {
        if ($null -eq $pending) { $pending = $p.StandardOutput.ReadLineAsync() }
        $left = ($last.AddMinutes($StallMinutes) - (Get-Date)).TotalMilliseconds
        if ($left -le 0) { $stalled = $true; break }
        if (-not $pending.Wait([int][Math]::Min($left, 60000))) {
            # stdout міг лишитись відкритим у нащадка завершеного процесу: це не завислість.
            if ($p.HasExited) { break }
            continue
        }
        $line = $pending.Result
        $pending = $null
        if ($null -eq $line) { break }
        $last = Get-Date
        [void]$out.Append($line).Append("`n")
        [System.IO.File]::AppendAllText($LogFile, $line + "`n", $script:Utf8)
        $type = ''
        if ($line -match '"type"\s*:\s*"([^"]{1,60})"') { $type = $Matches[1] }
        [System.IO.File]::AppendAllText($EventsFile, $last.ToString('s') + "`t" + $type + "`n", $script:Utf8)
    }
    if (-not $stalled -and -not $p.WaitForExit([int][Math]::Min([double][int]::MaxValue, $StallMinutes * 60000))) { $stalled = $true }
    if ($stalled) { Stop-Tree $p } else { $p.WaitForExit() }
    $errText = ''
    if ($err.Wait(15000)) { $errText = $err.Result }
    [pscustomobject]@{ Code = $(if ($stalled) { -1 } else { $p.ExitCode }); Stalled = $stalled; Out = $out.ToString(); Err = $errText }
}

# --- ізоляція (GEMINI.md) -----------------------------------------------------------------------------------------

# Порожній рядок — ізоляція на місці; інакше код перевірки, що не пройшла.
function Test-Isolation {
    $name = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    if (($name -split '\\')[-1] -ne $ExpectedUser) { return 'WHOAMI' }
    $net = Invoke-Native 'net.exe' @('session') '' 1
    if ($net.Code -eq 0) { return 'NET_SESSION' }
    $own = [System.IO.Path]::GetFullPath($env:USERPROFILE).TrimEnd('\')
    $profiles = Get-ChildItem 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList' |
        Where-Object { $_.PSChildName -like 'S-1-5-21-*' } |
        ForEach-Object { [string](Get-ItemProperty -LiteralPath $_.PSPath).ProfileImagePath }
    foreach ($dir in $profiles) {
        if (-not $dir -or ($dir.TrimEnd('\') -eq $own)) { continue }
        try { [void][System.IO.Directory]::GetFileSystemEntries($dir); return 'PROFILES' } catch { $null = $_ <# недоступний — так і треба #> }
    }
    $sysDrive = [System.IO.Path]::GetPathRoot($env:SystemRoot)
    foreach ($d in [System.IO.DriveInfo]::GetDrives()) {
        if ($d.Name -eq $sysDrive) { continue }
        if ($d.DriveType -ne 'Fixed' -and $d.DriveType -ne 'Network') { continue }
        try { [void][System.IO.Directory]::GetFileSystemEntries($d.RootDirectory.FullName); return 'DRIVES' } catch { $null = $_ <# недоступний — так і треба #> }
    }
    $secret = Get-ChildItem env: | Where-Object { $_.Name -match 'KEY|TOKEN|SECRET|PASSWORD' }
    if ($secret) { return 'ENV' }
    ''
}

# --- рушії (М.9-В) ------------------------------------------------------------------------------------------------

# Рушій за назвою моделі з позначки: gpt-* -> Codex (зусилля — суфікс назви), інакше agy.
function Get-Engine([string]$Model) {
    if ($Model -cmatch '^gpt-(.+)$') {
        $name = $Model; $effort = ''
        if ($Model -cmatch ('^(.+)-(' + $script:CodexEfforts + ')$')) { $name = $Matches[1]; $effort = $Matches[2] }
        return [pscustomobject]@{ Name = 'codex'; Model = $name; Effort = $effort }
    }
    [pscustomobject]@{ Name = 'agy'; Model = $Model; Effort = '' }
}

# Codex за замовчуванням вимкнений (9738: акаунт ChatGPT для користувача gemini ще не вибрано): рушій вмикає лише явний
# -EnableCodex у задачі gemini-run; без нього Codex не кличеться ні за позначкою gpt-*, ні каскадом.
function Find-CodexExe {
    if (-not $EnableCodex) { Write-Log 'рушій: Codex вимкнено (без -EnableCodex, 9738) — не кличу'; return $null }
    Find-EngineExe $CodexExe
}

# Шлях до виконуваного рушія; нема в PATH — $null (рушій недоступний), не збій обгортки.
function Find-EngineExe([string]$Name) {
    try { Resolve-Exe $Name } catch { Add-HealthAlert 'ENGINE' $(if ($Name -match 'codex') { 'CODEX' } else { 'AGY' }); Write-Log "рушій: $($_.Exception.Message)"; $null }
}

# --- квота --------------------------------------------------------------------------------------------------------

# `agy -p "/usage"` — рядки з табами, дані без ходу моделі (agy ≥ 1.1.11). Живий вивід 1.4.7 (26.10) — без заголовка:
# «група ⇥ вікно ⇥ NN% ⇥ скидання ISO UTC», по рядку на вікно (тиждень, 5 год); давніший розбір — за рядком-заголовком
# і JSON, терпимий до назв полів. Нерозпізнане — «невідомо»: наряд іде далі (429 ловить Get-ErrorCode).
function Get-FirstValue($Obj, [string[]]$Names) {
    foreach ($n in $Names) {
        foreach ($p in $Obj.PSObject.Properties) { if ($p.Name -ieq $n -and $null -ne $p.Value) { return $p.Value } }
    }
    $null
}

function ConvertTo-Number($Value) {
    if ($Value -is [string]) {
        $d = 0.0
        if ([double]::TryParse($Value.Trim().TrimEnd('%'), [System.Globalization.NumberStyles]::Float, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$d)) { return $d }
        return $null
    }
    if ($Value -is [ValueType] -and $Value -isnot [bool] -and $Value -isnot [datetime]) { return [double]$Value }
    $null
}

# Час скидання вікна (DateTimeOffset UTC) або $null — невідомо. Відносні секунди — від часу зчитування /usage.
function Get-ResetTime($Node) {
    $sec = ConvertTo-Number (Get-FirstValue $Node @('reset_in_seconds', 'resetInSeconds', 'seconds_until_reset', 'secondsUntilReset'))
    if ($null -ne $sec) { return $script:UsageReadTime.AddSeconds([Math]::Max(0, $sec)) }
    $at = Get-FirstValue $Node @('reset_time', 'resetTime', 'resets_at', 'resetsAt', 'reset_at', 'resetAt', 'reset')
    if ($at -is [datetime]) { return [DateTimeOffset]$at.ToUniversalTime() }
    if ($at -is [string]) {
        $dt = [DateTimeOffset]::MinValue
        if ([DateTimeOffset]::TryParse($at, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AssumeUniversal, [ref]$dt)) { return $dt.ToUniversalTime() }
        return $null
    }
    $n = ConvertTo-Number $at
    if ($null -ne $n -and $n -gt 1e9) { return [DateTimeOffset]::FromUnixTimeSeconds([long]$(if ($n -gt 1e11) { $n / 1000 } else { $n })) }
    $null
}

function Get-UsageGroups($Node, $Acc, [int]$Depth = 0) {
    if ($null -eq $Node -or $Node -is [string] -or $Node -is [ValueType] -or $Depth -gt 8) { return }
    if ($Node -is [System.Collections.IEnumerable]) { foreach ($i in $Node) { Get-UsageGroups $i $Acc ($Depth + 1) }; return }
    $name = Get-FirstValue $Node @('name', 'group', 'group_name', 'groupName', 'model_group', 'modelGroup', 'model', 'model_name', 'modelName', 'display_name', 'displayName', 'title', 'label', 'id')
    if ($name -is [string] -and $name.Trim()) {
        $left = ConvertTo-Number (Get-FirstValue $Node @('remaining_percent', 'remainingPercent', 'percent_remaining', 'percentRemaining', 'remaining_pct', 'remainingPct', 'percent_left', 'percentLeft'))
        if ($null -eq $left) {
            $frac = ConvertTo-Number (Get-FirstValue $Node @('remaining_fraction', 'remainingFraction'))
            if ($null -ne $frac) { $left = $frac * 100 }
        }
        if ($null -eq $left) {
            $used = ConvertTo-Number (Get-FirstValue $Node @('used_percent', 'usedPercent', 'percent_used', 'percentUsed', 'used_pct', 'usedPct'))
            if ($null -ne $used) { $left = 100 - $used }
        }
        if ($null -eq $left) {
            $rem = ConvertTo-Number (Get-FirstValue $Node @('remaining', 'remaining_requests', 'remainingRequests', 'remaining_tokens', 'remainingTokens'))
            $lim = ConvertTo-Number (Get-FirstValue $Node @('limit', 'total', 'quota', 'max'))
            if ($null -ne $rem -and $null -ne $lim -and $lim -gt 0) { $left = $rem / $lim * 100 }
            elseif ($null -ne $rem -and $rem -le 0) { $left = 0 }
        }
        if ($null -ne $left) {
            $win = [string](Get-FirstValue $Node @('window', 'period', 'limit_name', 'limitName'))
            [void]$Acc.Add([pscustomobject]@{ Name = $name.Trim(); Window = (ConvertTo-WindowCode $win)
                Left = [int][Math]::Max(0, [Math]::Min(100, [Math]::Round($left))); Reset = (Get-ResetTime $Node) })
        }
    }
    foreach ($p in $Node.PSObject.Properties) { Get-UsageGroups $p.Value $Acc ($Depth + 1) }
}

# Вікно квоти — закритий перелік (текст /usage від agy в стан не йде): тиждень, 5 год, доба, інше.
function ConvertTo-WindowCode([string]$Text) {
    if ($Text -match '(?i)week') { return 'WEEK' }
    if ($Text -match '(?i)five.?hour|5.?h') { return '5H' }
    if ($Text -match '(?i)\bday|daily') { return 'DAY' }
    $(if ($Text) { 'OTHER' } else { '' })
}

# Слова назви без чисел і службових слів: група «Gemini 3.5 Flash» ↔ модель gemini-3.8-flash-high — спільне «flash».
function Get-NameTokens([string]$Name) {
    $stop = @('gemini', 'high', 'medium', 'low', 'preview', 'latest', 'thinking', 'exp', 'and', 'the', 'models', 'model')
    @(($Name.ToLowerInvariant() -split '[^a-z0-9]+') | Where-Object { $_ -and $_ -notmatch '^[0-9]+$' -and $stop -notcontains $_ })
}

# Власні слова назви — без назв родин (gemini, claude, gpt): «Gemini 4 Argon» -> argon, «Claude and GPT models» -> нічого.
function Get-SpecificTokens([string]$Name) { @(Get-NameTokens $Name | Where-Object { $script:Families -notcontains $_ }) }

# Версія agy з `agy --version`; $null — не розпізнано. Одне читання на процес.
function Get-AgyVersion {
    if ($script:AgyVersionDone) { return $script:AgyVersion }
    $script:AgyVersionDone = $true
    try {
        if ($script:Agy) {
            $r = Invoke-Native $script:Agy @('--version') $RepoDir 1
            # Версія — з рядка з назвою agy («agy 1.1.11», «agy version v1.1.11 (збірка …)») або весь вивід — одна версія
            # x.y.z (живий agy 1.4.7 друкує лише «1.4.7»). Дата (рік із чотирьох цифр) чи число з іншого місця версією не
            # стає: нерозпізнане — версія невідома і /usage не кличеться (9743).
            if ($r.Code -eq 0 -and $r.Out -match '\bagy\b[^0-9\r\n]*v?([0-9]+(?:\.[0-9]+){1,3})(?![0-9.])') { $script:AgyVersion = [version]$Matches[1] }
            elseif ($r.Code -eq 0 -and $r.Out.Trim() -match '^v?([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,4})$') { $script:AgyVersion = [version]$Matches[1] }
            else { Write-Log "agy --version не розпізнано (код $($r.Code))" }
        }
    } catch { Write-Log "agy --version: $($_.Exception.Message)" }
    $script:AgyVersion
}

# Таблиця з табами: з рядком-заголовком (без цифр) або без нього у форматі agy 1.4.7 (група, [вікно,] NN%, ISO-час). Інакше $null.
function ConvertFrom-UsageTable([string]$Text) {
    $lines = @($Text -split "`r?`n" | Where-Object { $_.Contains("`t") })
    if ($lines.Count -lt 1) { return $null }
    if ($lines[0] -match '[0-9]') {
        # Без заголовка — лише коли КОЖЕН рядок: перша колонка — назва, передостання — відсоток, остання — ISO-час.
        $rows = New-Object System.Collections.ArrayList
        foreach ($l in $lines) {
            $c = @($l -split "`t" | ForEach-Object { $_.Trim() })
            $dt = [DateTimeOffset]::MinValue
            if ($c.Count -lt 3 -or $c[0] -notmatch '[A-Za-z]' -or $c[-2] -notmatch '^[0-9]{1,3}%$' -or
                $c[-1] -notmatch '^\d{4}-\d\d-\d\dT' -or -not [DateTimeOffset]::TryParse($c[-1], [cultureinfo]::InvariantCulture, 'AssumeUniversal', [ref]$dt)) { return $null }
            $o = [ordered]@{ name = $c[0]; remaining_percent = $c[-2]; reset_time = $c[-1] }
            if ($c.Count -ge 4) { $o.window = $c[1] }
            [void]$rows.Add([pscustomobject]$o)
        }
        return ,@($rows)
    }
    if ($lines.Count -lt 2) { return $null }
    $head = @($lines[0] -split "`t" | ForEach-Object { ($_.Trim().ToLowerInvariant() -replace '[^a-z0-9]+', '_').Trim('_') })
    $rows = New-Object System.Collections.ArrayList
    foreach ($l in $lines[1..($lines.Count - 1)]) {
        $c = @($l -split "`t")
        $o = [ordered]@{}
        for ($i = 0; $i -lt [Math]::Min($c.Count, $head.Count); $i++) {
            $k = $head[$i]; $v = $c[$i].Trim()
            if (-not $k -or -not $v) { continue }
            if ($k -match '^(?:remaining|left)' -and $v.EndsWith('%')) { $k = 'remaining_percent' }
            elseif ($k -match '^(?:used|usage)' -and $v.EndsWith('%')) { $k = 'used_percent' }
            elseif ($k -match '^resets?(?:_|$)') {
                $k = 'reset_time'
                if ($v -match '^(?:([0-9]+)\s*d)?\s*(?:([0-9]+)\s*h)?\s*(?:([0-9]+)\s*m)?$') {
                    $k = 'reset_in_seconds'
                    $v = [string](86400 * [int]('0' + $Matches[1]) + 3600 * [int]('0' + $Matches[2]) + 60 * [int]('0' + $Matches[3]))
                }
            }
            $o[$k] = $v
        }
        [void]$rows.Add([pscustomobject]$o)
    }
    ,@($rows)
}

# JSON /usage (command.data.groups[].buckets[]) -> вікна квоти (Name, Window, Left, Reset); Known=$false — не розпізнано.
function ConvertFrom-UsageText([string]$Text, [long]$ReadUnix) {
    $script:UsageReadTime = [DateTimeOffset]::FromUnixTimeSeconds($ReadUnix)
    $u = [pscustomobject]@{ Known = $false; Windows = @(); Text = ''; Read = $script:UsageReadTime }
    $text = $Text.Trim()
    if (-not $text) { return $u }
    $doc = $null
    try { $json = $text | ConvertFrom-Json } catch { $json = $null }
    $command = Get-JsonProp $json 'command'
    if ((Get-JsonProp $command 'name') -eq 'usage') {
        $acc = New-Object System.Collections.ArrayList
        foreach ($g in @(Get-JsonProp (Get-JsonProp $command 'data') 'groups')) {
            foreach ($b in @(Get-JsonProp $g 'buckets')) {
                $fraction = ConvertTo-Number (Get-JsonProp $b 'remaining_fraction')
                if ($null -eq $fraction -or $fraction -lt 0 -or $fraction -gt 1) { continue }
                Get-UsageGroups ([pscustomobject]@{ name = (Get-JsonProp $g 'name'); window = (Get-JsonProp $b 'window')
                    remaining_fraction = $fraction; reset_time = (Get-JsonProp $b 'reset_time') }) $acc
            }
        }
        $u.Known = ($acc.Count -gt 0); $u.Windows = @($acc)
        return $u
    }
    $doc = ConvertFrom-UsageTable $text
    if ($null -eq $doc -and $text.Contains("`t")) {
        # Табличний вивід без розпізнаного заголовка: колонок не знаємо — квота невідома, не вгадуємо.
        Write-Log 'квота: /usage — таблиця без розпізнаного заголовка; квота НЕВІДОМА, каскад за пулом не вмикаю'
    }
    if ($null -eq $doc) {
        try { $doc = $text | ConvertFrom-Json } catch {
            $a = $text.IndexOf('{'); $b = $text.LastIndexOf('}')
            if ($a -ge 0 -and $b -gt $a) { try { $doc = $text.Substring($a, $b - $a + 1) | ConvertFrom-Json } catch { $null = $_ } }
        }
        if ($null -ne $doc -and $doc.PSObject.Properties['response'] -and $doc.response -is [string]) {
            try { $doc = $doc.response | ConvertFrom-Json } catch { $null = $_ }
        }
    }
    $acc = New-Object System.Collections.ArrayList
    if ($null -ne $doc) { Get-UsageGroups $doc $acc }
    $u.Known = ($acc.Count -gt 0); $u.Windows = @($acc); $u.Text = $text.Substring(0, [Math]::Min(400, $text.Length))
    if (-not $u.Known) { Write-Log ('квота: груп не розпізнано; вивід /usage: ' + $u.Text) }
    $u
}

# Групи з вікон: залишок — найменший серед вікон групи; скидання — того вікна, що на нулі (кількох — найпізніше), інакше
# найменшого. Ім'я групи — як у /usage.
function Merge-UsageWindows($Windows) {
    $now = [DateTimeOffset]::UtcNow
    foreach ($grp in @($Windows | Group-Object Name)) {
        $w = @($grp.Group)
        $min = ($w | Measure-Object Left -Minimum).Minimum
        $at = @($w | Where-Object { $_.Left -eq $min })
        $reset = $null
        foreach ($x in $at) { if ($null -ne $x.Reset -and ($null -eq $reset -or $x.Reset -gt $reset)) { $reset = $x.Reset } }
        $mins = $(if ($null -eq $reset) { -1 } else { [int][Math]::Ceiling([Math]::Max(0, ($reset - $now).TotalMinutes)) })
        [pscustomobject]@{ Name = $grp.Name; Left = [int]$min; ResetMin = $mins; Reset = $reset }
    }
}

# Кеш /usage і `agy models` (usage.json): agy питаємо не частіше за usage_minutes (не щопроходу) — і щоразу, коли
# позначка чекає скидання, що вже минуло. Заодно — pools.json для рядка ПУЛИ (gemini_publish.ps1).
function Update-UsageCache {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $c = [ordered]@{ time = $now; text = ''; models = @() }
    try {
        $v = Get-AgyVersion
        if ($null -eq $v -or $v -lt $script:UsageMinVersion) {
            Write-Log "квота: agy $(if ($v) { $v } else { '?' }) < $($script:UsageMinVersion) — /usage не кличу"
        } else {
            $r = Invoke-Native $script:Agy @('-p', '/usage', '--output-format', 'json') $RepoDir $QuotaMinutes
            if ($r.TimedOut -or $r.Code -ne 0) { [void](Get-ErrorCode ($r.Out + $r.Err)); Write-Log "квота: agy /usage -> $($r.Code)" } else { $c.text = $r.Out }
        }
        $c.models = @(Get-AgyModels)
    } catch { Write-Log "квота: $($_.Exception.Message)" }
    try { Write-FileAtomic (Join-Path $RunsDir 'usage.json') ($c | ConvertTo-Json -Compress -Depth 3) } catch { Write-Log "кеш квоти: $($_.Exception.Message)" }
    $u = ConvertFrom-UsageText $c.text $now
    try { Write-Pools $v $u $c.models } catch { Write-Log "пули: $($_.Exception.Message)" }
    [pscustomobject]$c
}

# Вікна квоти з кешу; -Fresh чи кеш старший за usage_minutes чи за -After (unix) — agy питаємо знову.
function Read-Usage([switch]$Fresh, [long]$After = 0) {
    $c = $null
    try { $c = [System.IO.File]::ReadAllText((Join-Path $RunsDir 'usage.json'), $script:Utf8) | ConvertFrom-Json } catch { $null = $_ }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $age = (Get-Limit $script:Limits 'UsageMinutes' 'usage_minutes') * 60
    if ($Fresh -or $null -eq $c -or [long]$c.time -lt $After -or ($now - [long]$c.time) -ge $age) {
        if (-not $script:Agy) { return [pscustomobject]@{ Known = $false; Windows = @(); Text = ''; Read = [DateTimeOffset]::UtcNow } }
        $c = Update-UsageCache
    }
    $script:AgyModels = $(if (@($c.models).Count -gt 0) { @($c.models) } else { $null })
    ConvertFrom-UsageText ([string]$c.text) ([long]$c.time)
}

# ASCII-код групи для рядка: назва → A-Z0-9, до 16 знаків.
function ConvertTo-GroupCode([string]$Name) {
    $g = ($Name.ToUpperInvariant() -replace '[^A-Z0-9]', '')
    if (-not $g) { $g = 'MODEL' }
    $g.Substring(0, [Math]::Min(16, $g.Length))
}

# Групи моделі: за власними словами («argon», «flash»); нема — група родини без власних слів («Gemini Models»).
function Get-ModelGroups([string]$Model, $Groups) {
    $mt = @(Get-SpecificTokens $Model)
    $hit = @($Groups | Where-Object { $g = $_; @(Get-SpecificTokens $g.Name | Where-Object { $mt -contains $_ }).Count -gt 0 })
    if ($hit.Count -gt 0) { return $hit }
    $fam = ($Model.ToLowerInvariant() -split '-')[0]
    if ($script:Families -notcontains $fam) { return @() }
    @($Groups | Where-Object { @(Get-SpecificTokens $_.Name).Count -eq 0 -and @($_.Name.ToLowerInvariant() -split '[^a-z0-9]+') -contains $fam })
}

# Known=$false — квоту не прочитано (наряд іде далі). Blocked — усі групи моделі на 0 %; Group — ASCII-ім'я для коду рядка.
function Get-Quota([string]$Model, [switch]$Fresh, [long]$After = 0) {
    $none = [pscustomobject]@{ Known = $false; Blocked = $false; Group = ''; ResetMin = -1; ResetAt = 0L; Left = -1 }
    $u = Read-Usage -Fresh:$Fresh -After $After
    if (-not $u.Known) { return $none }
    $hit = @(Get-ModelGroups $Model @(Merge-UsageWindows $u.Windows))
    if ($hit.Count -eq 0) {
        Write-Log ('квота: групу моделі {0} не розпізнано; вивід /usage: {1}' -f $Model, $u.Text)
        return $none
    }
    $zeros = @($hit | Where-Object { $_.Left -eq 0 })
    $ref = $(if ($zeros.Count -eq $hit.Count) { $zeros[0] } else { @($hit | Sort-Object Left -Descending)[0] })
    [pscustomobject]@{ Known = $true; Blocked = ($ref.Left -eq 0); Group = (ConvertTo-GroupCode $ref.Name); ResetMin = $ref.ResetMin
        ResetAt = $(if ($null -ne $ref.Reset) { $ref.Reset.ToUnixTimeSeconds() } else { 0L }); Left = $ref.Left }
}

# Клас моделі за назвою: код — flash, проєктування — pro; інше — без каскаду.
function Get-ModelClass([string]$Model) {
    $t = @(Get-NameTokens $Model)
    if ($t -contains 'flash') { return 'code' }
    if ($t -contains 'pro') { return 'design' }
    ''
}

# Кандидати за порядком: модель позначки → [claude-opus-5-5-high для проєктування] → Codex (лише з -CodexFallbackModel).
function Get-Cascade([string]$Model) {
    $c = @($Model)
    if ((Get-ModelClass $Model) -eq 'design') { $c += $script:ClaudeCascadeModel }
    if ($EnableCodex -and $CodexFallbackModel -and (Get-Engine $CodexFallbackModel).Name -eq 'codex') { $c += $CodexFallbackModel }
    $c
}

# Рушій наряду за позначкою й квотою пулів. Model — фактична модель (каскад); Quota — пулу першого кандидата, якщо всі
# на 0 % (Blocked); Exe $null — рушія нема на ноутбуці. -After — позначка чекала скидання до цього часу (unix): квоту
# читаємо, зчитану не раніше.
function Select-Engine($M, [long]$After = 0) {
    $e = Get-Engine $M.Model
    $unknown = [pscustomobject]@{ Known = $false; Blocked = $false; Group = ''; ResetMin = -1; ResetAt = 0L; Left = -1 }
    if ($e.Name -ne 'agy') {
        # `codex exec` не має документованого способу прочитати залишок без ходу: квота невідома, 429 ловить Get-ErrorCode.
        return [pscustomobject]@{ Engine = $e; Exe = (Find-CodexExe); Quota = $unknown; Model = $M.Model }
    }
    $first = $null
    foreach ($cand in (Get-Cascade $M.Model)) {
        $ce = Get-Engine $cand
        if ($ce.Name -eq 'codex') {
            $cx = Find-CodexExe
            if ($cx) {
                Write-Log "рушій: пули agy на 0 % — Codex, модель $cand"
                return [pscustomobject]@{ Engine = $ce; Exe = $cx; Quota = $unknown; Model = $cand }
            }
            continue
        }
        $q = Get-Quota $cand -After $After
        if ($cand -ne $M.Model -and $null -ne $script:AgyModels -and @($script:AgyModels) -notcontains $cand) {
            Write-Log "каскад: $cand нема в agy models — пропущено"
            continue
        }
        if ($null -eq $first) { $first = $q }
        if ($q.Blocked) { Write-Log "каскад: $cand на 0 % (група $($q.Group))"; continue }
        if ($cand -ne $M.Model) { Write-Log "рушій: каскад $($M.Model) -> $cand" }
        return [pscustomobject]@{ Engine = $ce; Exe = $script:Agy; Quota = $q; Model = $cand }
    }
    [pscustomobject]@{ Engine = $e; Exe = $script:Agy; Quota = $(if ($first) { $first } else { $unknown }); Model = $M.Model }
}

# Скидання квоти Codex з тексту відмови (unix) або 0 — CLI його не дав. Розпізнає «try again in 2 days 3 hours 5 minutes»,
# «resets_in_seconds: N» і «resets_at: <unix>»; «try again at 3:42 PM» (місцевий час без дати) — ні, бо неоднозначно.
function Get-CodexReset([string]$Text) {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $t = Expand-JsonEscapes $Text
    if ($t -match '(?i)resets?_in_seconds"?\s*[:=]\s*([0-9]{1,9})') { return $now + [long]$Matches[1] }
    if ($t -match '(?i)resets?_at"?\s*[:=]\s*([0-9]{10})\b') { return [long]$Matches[1] }
    if ($t -match '(?i)try again in ((?:[0-9]+\s*(?:days?|hours?|hrs?|minutes?|mins?|seconds?|secs?)[\s,and]*)+)') {
        $sec = 0L
        foreach ($p in [regex]::Matches($Matches[1], '(?i)([0-9]+)\s*(d|h|m|s)')) {
            $sec += [long]$p.Groups[1].Value * @{ d = 86400; h = 3600; m = 60; s = 1 }[$p.Groups[2].Value.ToLowerInvariant()]
        }
        if ($sec -gt 0) { return $now + $sec }
    }
    0
}

# --- прогін agy ---------------------------------------------------------------------------------------------------

# Роль агента Codex — з рядка «Роль — …» наряду (перший, з першої колонки): ПЕРЕВІРКА за `аудит/ПЕРЕВІРКА.md`;
# нема чи інша — виконавець. Рядки всередині огороджених блоків (```/~~~, зокрема незакритого) — приклад, а не мета наряду;
# слово ролі не має продовжуватись літерою чи цифрою, кінець тексту без переносу рядка допустимий.
function Get-TaskRole([string]$TaskText) {
    $body = [regex]::Replace($TaskText, '(?ms)^[ \t]*(`{3,}|~{3,}).*?(?:^[ \t]*\1[ \t\r]*$|\z)', '')
    if ($body -cmatch '(?m)^Роль — (ВИКОНАВЕЦЬ|ПЕРЕВІРКА)(?![\p{L}\p{N}_-])') { return $Matches[1] }
    'ВИКОНАВЕЦЬ'
}

function Get-Prompt($M, [string]$TaskText, [string]$EngineName = 'agy') {
    $branch = "gemini/$($M.Slug)"
    $adapter = $(if ($EngineName -eq 'codex') { 'адаптер — лише цей текст' } else { 'адаптер середовища — `GEMINI.md`' })
    $role = $(if ($EngineName -eq 'codex') { Get-TaskRole $TaskText } else { 'ВИКОНАВЕЦЬ' })
    $roleText = $(if ($role -eq 'ПЕРЕВІРКА') { 'перевірка' } else { 'виконавець' })
    $roleFile = $(if ($role -eq 'ПЕРЕВІРКА') { 'ПЕРЕВІРКА' } else { 'ВИКОНАВЕЦЬ' })
    $commitRule = $(if ($role -eq 'ПЕРЕВІРКА') {
        "звіт перевірки (вердикт, докази, вади) — файл, який називає наряд, у цій гілці;`n  тілом останнього коміту — його підсумок: диспетчер відкриє PR саме з нього."
    } else {
        "звіт ролі (що зроблено, ДО -> ПІСЛЯ, вади поза мірилом) — тілом`n  останнього коміту: диспетчер відкриє PR саме з нього."
    })
@"
Ти — $roleText за ``AGENTS.md`` і ``аудит/$roleFile.md``; $adapter. Ізоляцію ОС уже
перевірила обгортка. Тебе запустила обгортка М.2 без людини: питань не став, відповіді не буде.

- Наряд — ``$($script:TaskDir)$($M.Slug).md`` з ``main`` на коміті $($M.Sha); повний текст — нижче між рисками.
- Гілку ``$branch`` уже вибрано: працюй і коміть лише в ній. Не пуш і не створюй бандла — це робить обгортка.
  Файлів ``.github/`` і ``аудит/адаптери/gemini/`` не змінюй: таку гілку не опублікують.
- Кожну команду виконуй на передньому плані й чекай її завершення: фонове завдання зупиняється разом із ходом, а
  звіт без результату — кинутий прогін.
- Коміть після кожного завершеного кроку; $commitRule
- Останній рядок відповіді — рівно один із двох:
  НОУТБУК ГОТОВО $branch <повний SHA голови гілки>
  ЗАБЛОКОВАНО: <що саме й чого чекаєш> — і зроблене до того закомічене.

----- НАРЯД -----
$TaskText
----- КІНЕЦЬ НАРЯДУ -----
"@
}

function Get-Facts($M, [string]$Start) {
    $branchRef = "refs/heads/gemini/$($M.Slug)"
    $head = Get-RefSha $branchRef
    $cur = (Invoke-Git @('symbolic-ref', '-q', 'HEAD') -AllowFail).Out.Trim()
    $st = (Invoke-Git @('status', '--porcelain', '-z', '--untracked-files=normal')).Out
    $dirty = @($st -split "`0" | Where-Object { $_ }).Count
    $ahead = 0
    if ($head) { $ahead = [int](Invoke-Git @('rev-list', '--count', "$Start..$head")).Out.Trim() }
    [pscustomobject]@{ Head = $head; OnBranch = ($cur -eq $branchRef); Dirty = $dirty; Ahead = $ahead }
}

# Звіт агента -> DONE, BLOCKED або NONE; приймається лише те, що збіглося з гілкою.
function Test-Report($M, [string]$Start, [string]$Response) {
    $lines = @($Response -split "`r?`n" | Where-Object { $_.Trim() })
    $last = ''
    if ($lines.Count -gt 0) { $last = $lines[-1].Trim().Trim('`', '*', ' ') }
    $f = Get-Facts $M $Start
    $kind = 'NONE'
    $claimed = ''
    $done = '^НОУТБУК ГОТОВО gemini/' + [regex]::Escape($M.Slug) + ' ([0-9a-f]{40})$'
    if ($last -match $done) { $kind = 'DONE'; $claimed = $Matches[1] }
    elseif ($last -match '^ЗАБЛОКОВАНО:') { $kind = 'BLOCKED' }
    # ЗАБЛОКОВАНО без комітів приймається: зробленого може не бути; ГОТОВО — лише з комітом і точним SHA.
    $ok = $f.OnBranch -and $f.Dirty -eq 0
    if ($kind -eq 'DONE') { $ok = $ok -and $f.Ahead -gt 0 -and ($claimed -eq $f.Head) }
    [pscustomobject]@{ Kind = $kind; Accepted = ($kind -ne 'NONE' -and $ok); Facts = $f; Claimed = $claimed }
}

function Get-Nudge($M, $Check, [string]$Why) {
    $branch = "gemini/$($M.Slug)"
    $f = $Check.Facts
    $facts = "Факти обгортки: поточна гілка — $(if ($f.OnBranch) { $branch } else { 'інша' }); голова $branch — " +
        "$(if ($f.Head) { $f.Head } else { 'нема' }); нових комітів — $($f.Ahead); незакомічених файлів — $($f.Dirty)."
    $head = switch ($Why) {
        'mismatch' { 'Звіт не збігся з гілкою.' }
        'timeout' { 'Хід перевищив межу часу й зупинений обгорткою.' }
        'eof' { 'Процес agy перервався; це та сама розмова.' }
        default { 'Хід закінчився без звіту.' }
    }
@"
$head $facts
Якщо запускав фонове завдання — воно могло зупинитись: перевір, що зроблено, доведи роботу на передньому плані,
закоміть у $branch. Останній рядок — як у наряді: ``НОУТБУК ГОТОВО $branch <повний SHA>`` або ``ЗАБЛОКОВАНО: …``.
"@
}

# Рядки подій `--json` приходять з екрануванням JSON (`\u0027` замість апострофа, `\"`); клас відмови шукаємо в розкодованому
# тексті, а не в сирому: інакше межа слова біля `\u0027max\u0027` ламається. Розкодування не залежить від того, чи рядок
# події цілий (хвіст виводу обрізаний по символах) — тому це підстановка, а не ConvertFrom-Json.
function Expand-JsonEscapes([string]$Text) {
    $t = [regex]::Replace($Text, '\\u([0-9a-fA-F]{4})', { param($m) [string][char][Convert]::ToInt32($m.Groups[1].Value, 16) })
    $t = [regex]::Replace($t, '\\[nrt]', ' ')
    [regex]::Replace($t, '\\(["\\/])', '$1')
}

function Get-ErrorCode([string]$Text, [string]$EngineName = 'agy', [string]$Effort = '') {
    $Text = Expand-JsonEscapes $Text
    if ($Text -match 'invalid model selection|not recognized as a known model') { return 'MODEL_INVALID' }
    # Codex не приймає зусилля з позначки: помилка конфігурації `model_reasoning_effort`, відповідь API про `reasoning.effort`
    # або відповідь «Invalid/Unsupported value … Supported values are: …», де названо надіслане зусилля чи перелік зусиль
    # (сервер параметра в тексті не називає). Чужа «Unsupported value: temperature» зусиллям не вважається.
    if ($EngineName -eq 'codex') {
        $badValue = $Text -match '(?:Invalid|Unsupported) value|unknown variant'
        $namesEffort = $Effort -and ($Text -cmatch ('(?<![\p{L}\p{N}_-])' + [regex]::Escape($Effort) + '(?![\p{L}\p{N}_-])'))
        $listsEfforts = $Text -cmatch ('Supported values are:.*(?<![\p{L}\p{N}_-])(?:xhigh|minimal)(?![\p{L}\p{N}_-])')
        if ($Text -match 'reasoning[._ -]?effort' -or ($badValue -and ($namesEffort -or $listsEfforts))) { return 'EFFORT_INVALID' }
    }
    if ($Text -match '429|RESOURCE_EXHAUSTED|[Qq]uota|[Uu]sage limit|[Rr]ate limit') { return 'QUOTA' }
    if ($Text -match 'authentication required|[Nn]ot logged in|[Pp]lease (?:log ?in|sign in)|authentication_error|\b401\b') {
        Add-HealthAlert 'AUTH' $EngineName.ToUpperInvariant(); return 'AUTH'
    }
    'AGY_ERROR'
}

function Get-AgyArgs($M, [string]$Conversation, [string[]]$Head) {
    $a = $Head + @('--output-format', $(if ($Mode -eq 'stream') { 'stream-json' } else { 'json' }),
        '--model', $M.Model, '--dangerously-skip-permissions')
    if ($Mode -eq 'stream') { $a = @('--input-format', 'stream-json') + $a }
    if (-not $NoPrintTimeoutFlag) { $a += @('--print-timeout', ('{0}m' -f [int][Math]::Ceiling($TurnMinutes))) }
    if ($Conversation) { $a += @('--conversation', $Conversation) }
    $a
}

# Один хід у режимі stream: подія result, eof (процес закінчився) або timeout.
function Wait-StreamResult($Run, [datetime]$Deadline) {
    while ($true) {
        if ($null -eq $Run.Pending) { $Run.Pending = $Run.Proc.StandardOutput.ReadLineAsync() }
        $left = ($Deadline - (Get-Date)).TotalMilliseconds
        if ($left -le 0) { return [pscustomobject]@{ Kind = 'timeout'; Result = $null } }
        if (-not $Run.Pending.Wait([int][Math]::Min($left, 60000))) { continue }
        $line = $Run.Pending.Result
        $Run.Pending = $null
        if ($null -eq $line) { return [pscustomobject]@{ Kind = 'eof'; Result = $null } }
        [System.IO.File]::AppendAllText($Run.Log, $line + "`n", $script:Utf8)
        try { $ev = $line | ConvertFrom-Json } catch { continue }
        if (-not $ev.PSObject.Properties['event']) { continue }
        if ($ev.event -eq 'init' -and $ev.PSObject.Properties['conversation_id']) { $Run.Conversation = [string]$ev.conversation_id }
        if ($ev.event -eq 'result') {
            if ($ev.result.PSObject.Properties['conversation_id'] -and $ev.result.conversation_id) {
                $Run.Conversation = [string]$ev.result.conversation_id
            }
            return [pscustomobject]@{ Kind = 'result'; Result = $ev.result }
        }
    }
}

function Start-StreamRun($M, $Run) {
    $psi = New-StartInfo $script:Agy (Get-AgyArgs $M $Run.Conversation @()) $RepoDir
    $psi.RedirectStandardInput = $true
    # .NET Framework створює StandardInput з AutoFlush: BOM пишеться вже під час Start.
    $stdinEncoding = [Console]::InputEncoding
    try {
        [Console]::InputEncoding = $script:Utf8
        $Run.Proc = [System.Diagnostics.Process]::Start($psi)
    } finally { [Console]::InputEncoding = $stdinEncoding }
    $Run.Stdin = New-Object System.IO.StreamWriter($Run.Proc.StandardInput.BaseStream, $script:Utf8)
    $Run.Stderr = $Run.Proc.StandardError.ReadToEndAsync()
    $Run.Pending = $null
}

function Close-StreamRun($Run) {
    if ($null -eq $Run.Proc) { return }
    # Дерево — разом із фоновими завданнями агента: інакше вони тримають файли клону до наступного прогону.
    Stop-Tree $Run.Proc
    try { [System.IO.File]::AppendAllText($Run.ErrLog, $Run.Stderr.Result, $script:Utf8) } catch { Write-Log "stderr agy: $($_.Exception.Message)" }
    $Run.Proc = $null
}

# Рушій без розмови (Codex): кожен хід — окремий процес; текст ходу — у файлі, аргумент без лапок і
# метасимволів cmd. Догонка несе повний наряд, бо нової розмови рушій не пам'ятає, а стан роботи — у гілці.
# Межі часу ходу нема: зупиняє лише завислість (Invoke-NativeUntilStall, -CodexStallMinutes) — вид ходу 'stall'.
# Прапори Codex `exec` -C/-m/-c/--json/-o/--dangerously-bypass-approvals-and-sandbox
# (https://learn.chatgpt.com/docs/developer-commands?surface=cli): обхід пісочниці Codex — лише тому, що ізоляція ОС
# (користувач gemini без прав і входів) уже стоїть, як вимагає документація («only inside an isolated runner»).
function Invoke-OneShotTurn($M, $Run, [string]$Text) {
    $Run.Turn++
    $file = Join-Path $Run.Dir ('turn{0}.md' -f $Run.Turn)
    $body = $(if ($Run.Turn -gt 1) { $Run.BasePrompt + "`n`n----- ПРОДОВЖЕННЯ -----`n" + $Text } else { $Text })
    [System.IO.File]::WriteAllText($file, $body, $script:Utf8)
    $short = "Прочитай файл $file і виконай його повністю"
    $outFile = Join-Path $Run.Dir ('turn{0}.out.md' -f $Run.Turn)
    $a = @('exec', '-C', $RepoDir, '-m', $Run.Engine.Model)
    if ($Run.Engine.Effort) { $a += @('-c', "model_reasoning_effort=$($Run.Engine.Effort)") }
    $a += @('--json', '-o', $outFile, '--dangerously-bypass-approvals-and-sandbox', $short)
    $r = Invoke-NativeUntilStall $Run.Exe $a $RepoDir $CodexStallMinutes $Run.Log (Join-Path $Run.Dir 'codex.events.tsv')
    [System.IO.File]::AppendAllText($Run.ErrLog, $r.Err, $script:Utf8)
    if ($r.Stalled) {
        Write-Log "codex: нових подій нема понад $CodexStallMinutes хв — завислість, зупинено"
        return [pscustomobject]@{ Kind = 'stall'; Result = $null }
    }
    $resp = ''; $err = ''
    if (Test-Path -LiteralPath $outFile) { $resp = [System.IO.File]::ReadAllText($outFile, $script:Utf8) }
    if ($r.Code -ne 0) { $err = ($r.Err + "`n" + $r.Out.Substring([Math]::Max(0, $r.Out.Length - 2000))).Trim() }
    if ($r.Code -ne 0 -and -not $err) { $err = "код виходу $($r.Code)" }
    $res = [pscustomobject]@{ status = $(if ($err) { 'ERROR' } else { 'SUCCESS' }); response = $resp; error = $err }
    [pscustomobject]@{ Kind = 'result'; Result = $res }
}

function Invoke-Turn($M, $Run, [string]$Text, [datetime]$Deadline) {
    if ($Run.Engine.Name -ne 'agy') { return Invoke-OneShotTurn $M $Run $Text }
    if ($Mode -eq 'stream') {
        if ($null -eq $Run.Proc) { Start-StreamRun $M $Run }
        try {
            $Run.Stdin.Write('{"event":"user","message":{"content":' + (ConvertTo-JsonString $Text) + '}}' + "`n")
            $Run.Stdin.Flush()
        } catch { return [pscustomobject]@{ Kind = 'eof'; Result = $null } }
        $r = Wait-StreamResult $Run $Deadline
        if ($r.Kind -ne 'result') { Close-StreamRun $Run }
        return $r
    }
    # Режим print: кожен хід — окремий процес; текст ходу — у файлі, аргумент без лапок і метасимволів cmd.
    $Run.Turn++
    $file = Join-Path $Run.Dir ('turn{0}.md' -f $Run.Turn)
    [System.IO.File]::WriteAllText($file, $Text, $script:Utf8)
    $short = "Прочитай файл $file і виконай його повністю"
    $minutes = ($Deadline - (Get-Date)).TotalMinutes
    if ($minutes -le 0) { return [pscustomobject]@{ Kind = 'timeout'; Result = $null } }
    # Запас 2 хв: agy має встигнути сам віддати конверт із conversation_id по своїй --print-timeout.
    $r = Invoke-Native $script:Agy (Get-AgyArgs $M $Run.Conversation @('-p', $short)) $RepoDir ($minutes + 2)
    [System.IO.File]::AppendAllText($Run.Log, $r.Out + "`n", $script:Utf8)
    [System.IO.File]::AppendAllText($Run.ErrLog, $r.Err, $script:Utf8)
    if ($r.TimedOut) { return [pscustomobject]@{ Kind = 'timeout'; Result = $null } }
    $json = @($r.Out -split "`n" | Where-Object { $_.Trim().StartsWith('{') })
    if ($json.Count -eq 0) { return [pscustomobject]@{ Kind = 'eof'; Result = $null } }
    try { $res = $json[-1] | ConvertFrom-Json } catch { return [pscustomobject]@{ Kind = 'eof'; Result = $null } }
    if ($res.PSObject.Properties['conversation_id'] -and $res.conversation_id) { $Run.Conversation = [string]$res.conversation_id }
    [pscustomobject]@{ Kind = 'result'; Result = $res }
}

# Прогін до прийнятого звіту, межі часу чи межі догонок. Повертає код, вид звіту й число ходів.
function Invoke-Agent($M, [string]$Start, [string]$Prompt, [string]$Dir, $Sel) {
    $run = [pscustomobject]@{ Proc = $null; Stdin = $null; Stderr = $null; Pending = $null; Conversation = $(if ($Sel.Engine.Name -ne 'agy') { 'oneshot' } else { '' })
        Engine = $Sel.Engine; Exe = $Sel.Exe; BasePrompt = $Prompt
        Dir = $Dir; Log = (Join-Path $Dir 'agy.jsonl'); ErrLog = (Join-Path $Dir 'agy.stderr.txt'); Turn = 0
        Responses = New-Object System.Collections.Generic.List[string] }
    # Codex без межі часу всього й ходу (власник 26.10): його зупиняє лише завислість; `agy` — як було.
    $unlimited = ($Sel.Engine.Name -eq 'codex')
    $deadline = $(if ($unlimited) { [datetime]::MaxValue } else { (Get-Date).AddMinutes($TotalMinutes) })
    $text = $Prompt
    $turns = 0
    $nudges = 0
    $code = ''
    $report = 'NONE'
    try {
        while ($true) {
            $turnDeadline = $deadline
            if (-not $unlimited) {
                $turnDeadline = (Get-Date).AddMinutes($TurnMinutes)
                if ($turnDeadline -gt $deadline) { $turnDeadline = $deadline }
            }
            $turns++
            $r = Invoke-Turn $M $run $text $turnDeadline
            if ($r.Kind -eq 'stall') { $code = 'STALL'; break }
            $why = $r.Kind
            if ($r.Kind -eq 'result') {
                $status = [string]$r.Result.status
                $resp = ''
                if ($r.Result.PSObject.Properties['response']) { $resp = [string]$r.Result.response }
                $run.Responses.Add($resp)
                if ($status -in @('ERROR', 'INVALID', 'CANCELED')) {
                    $err = ''
                    if ($r.Result.PSObject.Properties['error']) { $err = [string]$r.Result.error }
                    $code = Get-ErrorCode $err $run.Engine.Name $run.Engine.Effort
                    Write-Log "agy: статус $status ($code)"
                    break
                }
                $check = Test-Report $M $Start $resp
                if ($check.Accepted) { $code = $check.Kind; $report = $check.Kind; break }
                $why = $(if ($check.Kind -ne 'NONE') { 'mismatch' } else { 'none' })
            }
            # Без id розмови догонка пішла б у нову розмову без наряду.
            if ($r.Kind -ne 'result' -and -not $run.Conversation) {
                $code = $(if ($r.Kind -eq 'timeout') { 'TIMEOUT' } else { 'AGY_ERROR' })
                Write-Log "agy: $($r.Kind) без id розмови — догонки нема"
                break
            }
            if ((Get-Date) -ge $deadline) { $code = 'TIMEOUT'; break }
            if ($nudges -ge $MaxNudges) { $code = 'NO_REPORT'; break }
            $nudges++
            $text = Get-Nudge $M (Test-Report $M $Start '') $why
            Write-Log "догонка $nudges ($why)"
        }
    } finally {
        Close-StreamRun $run
    }
    $tail = (($run.Responses -join "`n") -split "`r?`n" | Select-Object -Last 60) -join "`n"
    [pscustomobject]@{ Code = $code; Report = $report; Turns = $turns; Tail = $tail }
}

# Назви моделей з `agy models` (лише назви за шаблоном): диспетчер обере робочу без руки власника.
function Get-AgyModels {
    $r = Invoke-Native $script:Agy @('models') $RepoDir 2
    $names = foreach ($line in ($r.Out -split "`n")) {
        $w = ($line.Trim() -split '\s+')[0]
        if ($w -cmatch $script:ModelPattern) { $w }
    }
    @($names | Select-Object -Unique -First 20)
}

# Пули для диспетчера (pools.json у теці вихідних): версія agy, групи (ASCII-код, % залишку, хв до скидання), назви
# `agy models` за ModelPattern. Лише числа й назви за шаблоном; рядок із них складає gemini_publish.ps1.
function Write-Pools($Version, $Usage, $Models) {
    $seen = @{}; $groups = @()
    foreach ($g in @(Merge-UsageWindows $Usage.Windows)) {
        $c = ConvertTo-GroupCode $g.Name
        if ($seen.ContainsKey($c)) { continue }
        $seen[$c] = 1
        $groups += [ordered]@{ g = $c; left = [int]$g.Left; reset = [int]$g.ResetMin }
    }
    $pm = @($Models | Where-Object { $_ -cmatch $script:PoolModelPattern } | Select-Object -First 6)
    $doc = [ordered]@{ v = 1; time = (Get-Date).ToString('s'); agy = $(if ($Version) { [string]$Version } else { '' }); groups = @($groups | Select-Object -First 6); models = $pm; unknown = (-not $Usage.Known) }
    Write-FileAtomic (Join-Path $OutDir 'pools.json') ($doc | ConvertTo-Json -Compress -Depth 4)
}

# --- один наряд ---------------------------------------------------------------------------------------------------

# Кінець прогону: факти гілки, бандл (коли є нові коміти), стан у теці обміну. Спільне для звичайного кінця й
# для прогону, перерваного вимкненням чи сном ноутбука (тоді стан — `STARTED` із JSON).
function Complete-Status($Status, [string]$StatePath, [string]$Tail, [datetime]$T0) {
    try {
        if ($Status.start) {
            $slugObj = [pscustomobject]@{ Slug = $Status.slug }
            $f = Get-Facts $slugObj $Status.start
            $Status.head = $f.Head
            $Status.ahead = $f.Ahead
            if ($f.Ahead -gt 0) {
                $bundle = Join-Path $OutDir ($Status.id + '.bundle')
                $exclude = @('^refs/remotes/origin/main', "^$($Status.start)")
                [void](Invoke-Git (@('bundle', 'create', '-q', ($bundle + '.part'), "refs/heads/gemini/$($Status.slug)") + $exclude))
                Move-Item -LiteralPath ($bundle + '.part') -Destination $bundle -Force
                $Status.bundle = $Status.id + '.bundle'
            }
        }
    } catch {
        Write-Log "бандл: $($_.Exception.Message)"
        if ($Status.code -in @('DONE', 'BLOCKED', '')) { $Status.code = 'CRASH' }
    }
    if ($T0 -ne [datetime]::MinValue) { $Status.minutes = [int][Math]::Round(((Get-Date) - $T0).TotalMinutes) }
    if ($Tail) { [System.IO.File]::WriteAllText((Join-Path $OutDir ($Status.id + '.tail.txt')), $Tail, $script:Utf8) }
    Write-FileAtomic (Join-Path $OutDir ($Status.id + '.json')) ($Status | ConvertTo-Json -Compress)
    Write-FileAtomic $StatePath "DONE $($Status.id) $($Status.code)"
    Remove-Claim $StatePath
    Write-Log "наряд $($Status.slug) [$($Status.id)]: $($Status.code), ходів $($Status.turns), комітів $($Status.ahead)"
}

# Рядок диспетчерові «чекає скидання квоти» (QUOTA0_<група>_M<хв>, gemini_publish.ps1): стан без бандла, позначка — у
# чеканні (Set-MarkerWait), не виконана.
function Write-QuotaStatus($M, [string]$Id, [string]$Group, [long]$Until, [hashtable]$Extra) {
    $mins = [int][Math]::Ceiling([Math]::Max(0, $Until - [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) / 60)
    $s = [ordered]@{ v = 1; id = $Id; slug = $M.Slug; model = $M.Model; n = [int]$M.N; marker = $M.Sha; cond = $M.Cond
        start = ''; head = ''; code = 'QUOTA_ZERO'; report = 'NONE'; ahead = 0; turns = 0; minutes = 0; bundle = ''; quota = 0; qgroup = $Group; qreset = $mins }
    foreach ($k in $Extra.Keys) { $s[$k] = $Extra[$k] }
    Write-FileAtomic (Join-Path $OutDir ($Id + '.json')) ($s | ConvertTo-Json -Compress)
    Write-Log "квота: $($M.Name) — група $Group на 0 %, чекає до $(Get-UtcStamp ([DateTimeOffset]::FromUnixTimeSeconds($Until).UtcDateTime))"
}

# Відмова до STARTED: лічильник повернень і межа ті самі, що в квоти; на межі — кінцевий стан CRASH і рядок диспетчерові.
function Close-FailedStart($M, [string]$Id, [string]$StatePath) {
    if ((Step-FailedStart $M $StatePath) -ne 'LIMIT') { return }
    $status = [ordered]@{ v = 1; id = $Id; slug = $M.Slug; model = $M.Model; n = [int]$M.N; marker = $M.Sha; cond = $M.Cond; slot = ''
        start = ''; head = ''; code = 'CRASH'; report = 'NONE'; ahead = 0; turns = 0; minutes = 0; bundle = ''; engine = 'agy' }
    Write-Log "позначка $($M.Name): відмов до запуску понад $script:MaxRetakes — кінець CRASH"
    Complete-Status $status $StatePath '' ([datetime]::MinValue)
}

function New-RunId([string]$Key) { '{0:yyyyMMdd-HHmmss}-{1}' -f (Get-Date), (Get-Sha256Hex ($Key + [guid]::NewGuid())).Substring(0, 12) }

# Прогони, що не йдуть: стан STARTED без живого процесу наряду (замок його слота вільний) — закрити й забандлити.
function Resume-Interrupted {
    foreach ($sf in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.txt' -File)) {
        $text = [System.IO.File]::ReadAllText($sf.FullName, $script:Utf8)
        if (-not $text.StartsWith('STARTED {')) { continue }
        $j = $text.Substring(8) | ConvertFrom-Json
        $slot = [string](Get-JsonProp $j 'slot')
        if ((Test-SlotName $slot $script:Lanes) -and -not (Test-LockFree (Join-Path $script:SlotDir "$slot.lock"))) { continue }
        $status = [ordered]@{}
        foreach ($p in $j.PSObject.Properties) { $status[$p.Name] = $p.Value }
        $status.code = 'INTERRUPTED'
        Write-Log "прогін $($status.id) перервано — закриваю"
        Complete-Status $status $sf.FullName '' ([datetime]::MinValue)
    }
}

# Наряд у процесі наряду: робоча копія слота вже вибрана ($RepoDir), рушій вибрав планувальник ($Job.sel).
function Invoke-Task($M, $Job) {
    $key = Get-MarkerKey $M
    $id = [string]$Job.id
    $statePath = Get-StatePath $key
    $status = [ordered]@{ v = 1; id = $id; slug = $M.Slug; model = $M.Model; n = [int]$M.N; marker = $M.Sha; cond = $M.Cond; slot = [string]$Job.slot
        start = ''; head = ''; code = ''; report = 'NONE'; ahead = 0; turns = 0; minutes = 0; bundle = ''; engine = 'agy'
        retakes = (Get-Retakes $statePath) }
    Write-FileAtomic $statePath ('STARTED ' + ($status | ConvertTo-Json -Compress))
    $dir = [string]$Job.dir
    $t0 = Get-Date
    $tail = ''
    $waiting = $false
    Write-Log "наряд $($M.Name) $($M.Sha) -> $id (слот $($Job.slot))"
    try {
        $main = Get-RefSha 'refs/remotes/origin/main'
        $anc = Invoke-Git @('merge-base', '--is-ancestor', $M.Sha, $main) -AllowFail
        $taskPath = Get-AutoTaskPath $M.Slug
        if ($anc.Code -ne 0) { $status.code = 'NOT_ON_MAIN'; return }
        if ((Invoke-Git @('cat-file', '-e', "$($M.Sha):$taskPath") -AllowFail).Code -ne 0) { $status.code = 'NO_TASK_FILE'; return }
        $taskText = Add-AutoTaskContext $M.Slug ((Invoke-Git @('cat-file', 'blob', "$($M.Sha):$taskPath")).Out)
        $js = $Job.sel
        $eng = [pscustomobject]@{ Name = [string]$js.engine; Model = [string]$js.emodel; Effort = [string]$js.effort }
        $exe = $(if ($eng.Name -eq 'codex') { Find-CodexExe } else { Find-EngineExe $AgyExe })
        $q = [pscustomobject]@{ Known = [bool]$js.qknown; Blocked = $false; Group = [string]$js.qgroup; ResetMin = -1; Left = [int]$js.qleft }
        $sel = [pscustomobject]@{ Engine = $eng; Exe = $exe; Quota = $q; Model = [string]$js.model }
        $script:Agy = Find-EngineExe $AgyExe
        $status.engine = $sel.Engine.Name
        $status.actual = $sel.Model
        # Межа розміру наряду — для agy (як було); Codex читає наряд з файлу `turnN.md`, розмір не обмежено (власник 26.10).
        if ($sel.Engine.Name -ne 'codex' -and $taskText.Length -gt 30000) { $status.code = 'TASK_TOO_LONG'; return }
        $MA = $M | Select-Object *
        $MA.Model = $sel.Model
        if (-not $sel.Exe) { $status.code = 'ENGINE_MISSING'; return }
        $start = Get-RefSha "refs/remotes/origin/gemini/$($M.Slug)"
        # Повтор після відмови за квотою: від голови того прогону, якщо опублікована гілка — її предок (інакше NOT_FF).
        $wh = [string]$Job.head
        if ($wh -match '^[0-9a-f]{40}$' -and (Get-RefSha $wh) -and (-not $start -or (Invoke-Git @('merge-base', '--is-ancestor', $start, $wh) -AllowFail).Code -eq 0)) { $start = $wh }
        if (-not $start) { $start = $main }
        Reset-WorkTree $RepoDir
        [void](Invoke-Git @('checkout', '-q', '-f', '--ignore-other-worktrees', '-B', "gemini/$($M.Slug)", $start))
        $status.start = $start
        # Стан із початком гілки: перерваний прогін наступний запуск закриє й забандлить (Resume-Interrupted).
        Write-FileAtomic $statePath ('STARTED ' + ($status | ConvertTo-Json -Compress))
        $prompt = Get-Prompt $MA $taskText $sel.Engine.Name
        [System.IO.File]::WriteAllText((Join-Path $dir 'prompt.md'), $prompt, $script:Utf8)
        $res = Invoke-Agent $MA $start $prompt $dir $sel
        $tail = $res.Tail
        $status.code = $res.Code
        $status.report = $res.Report
        $status.turns = $res.Turns
        if ($res.Code -eq 'MODEL_INVALID') { $status.models = @(Get-AgyModels) }
        if ($res.Code -eq 'QUOTA') { $waiting = Enter-RunQuotaWait $M $sel $status $res $dir }
        # Залишок квоти після прогону — для рядка кінця наряду.
        $qa = $(if ($sel.Engine.Name -eq 'agy' -and -not $waiting) { Get-Quota $sel.Model -Fresh } else { $q })
        if ($qa.Known) { $status.quota = $qa.Left; $status.qgroup = $qa.Group }
    } catch {
        $status.code = 'CRASH'
        Write-Log "збій: $($_.Exception.Message)"
    } finally {
        if (-not $waiting) { Complete-Status $status $statePath $tail $t0 }
        [void](Invoke-Git @('checkout', '-q', '--detach') -AllowFail)
    }
}

# Відмова за квотою посеред прогону (429): позначка повертається в чергу до скидання (agy — з /usage, Codex — з тексту
# відмови, нема — quota_wait_minutes), зроблене лишається в гілці, повтор почне з її голови. Понад MaxRetakes — кінець
# із кодом QUOTA, як до смуг. $true — позначка чекає.
function Enter-RunQuotaWait($M, $Sel, $Status, $Res, [string]$Dir) {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $until = 0L; $group = 'CODEX'
    if ($Sel.Engine.Name -eq 'agy') {
        $q = Get-Quota $Sel.Model -Fresh
        $group = $(if ($q.Group) { $q.Group } else { 'AGY' })
        if ($q.Known -and $q.ResetAt -gt $now) { $until = [long]$q.ResetAt }
    } else {
        $err = ''
        try { $err = [System.IO.File]::ReadAllText((Join-Path $Dir 'agy.stderr.txt'), $script:Utf8) } catch { $null = $_ }
        $until = Get-CodexReset ($Res.Tail + "`n" + $err)
        $cq = [ordered]@{ refused = (Get-UtcStamp (Get-Date)); reset = $(if ($until -gt 0) { Get-UtcStamp ([DateTimeOffset]::FromUnixTimeSeconds($until).UtcDateTime) } else { '' }) }
        try { Write-FileAtomic (Join-Path $RunsDir 'quota-codex.json') ($cq | ConvertTo-Json -Compress) } catch { $null = $_ }
    }
    $known = $until -gt 0
    if (-not $known) { $until = $now + [long](60 * (Get-Limit $script:Limits 'QuotaWaitMinutes' 'quota_wait_minutes')) }
    $f = Get-Facts $M $Status.start
    $n = Set-MarkerWait $M $until @{ retake = $true; group = $group; head = $(if ($f.Ahead -gt 0) { $f.Head } else { '' }) }
    if ($null -eq $n) { Write-Log "квота: $($M.Name) — повернень у чергу понад $script:MaxRetakes, кінець QUOTA"; return $false }
    Write-QuotaStatus $M (New-RunId (Get-MarkerKey $M)) $group $until @{ engine = $Sel.Engine.Name; turns = $Status.turns; retake = $n }
    $true
}

function Write-IsolationStatus([string]$Check) {
    Add-HealthAlert 'ISOLATION' $Check
    $key = 'isolation ' + $Check + ' ' + (Get-Date -Format 'yyyyMMdd')
    $state = Get-StatePath $key
    if (Test-Path -LiteralPath $state) { return }
    $id = '{0:yyyyMMdd-HHmmss}-{1}' -f (Get-Date), (Get-Sha256Hex $key).Substring(0, 12)
    $status = [ordered]@{ v = 1; id = $id; code = 'ISOLATION'; check = $Check }
    Write-FileAtomic (Join-Path $OutDir ($id + '.json')) ($status | ConvertTo-Json -Compress)
    Write-FileAtomic $state "DONE $id ISOLATION"
}

# Шлях до виконуваного: .NET із UseShellExecute=false дописує лише .exe, а CLI з npm — це .cmd.
function Resolve-Exe([string]$Name) {
    if (Test-Path -LiteralPath $Name -PathType Leaf) { return $Name }
    $cmds = @(Get-Command $Name -All -CommandType Application -ErrorAction SilentlyContinue)
    foreach ($ext in @('\.exe$', '\.cmd$', '')) {
        $hit = @($cmds | Where-Object { $_.Source -match $ext })
        if ($hit.Count -gt 0) { return $hit[0].Source }
    }
    throw "$Name не знайдено в PATH"
}

# --- планувальник --------------------------------------------------------------------------------------------------

# GPU вільна для нового наряду: свого живого GPU-наряду нема й замок відеокарти (спільний з claude-run) не тримає ніхто.
function Test-GpuFree($Workers) {
    if (@($Workers | Where-Object { $_.Gpu -and -not $_.Proc.HasExited }).Count -gt 0) { return $false }
    Test-LockFree (Get-GpuLockPath)
}

# Позначка agy на нульовій квоті до старту: чекає скидання (спроба не спалена); рядок диспетчерові — раз, коли позначка
# входить у чекання вперше.
function Enter-StartQuotaWait($M, $Q, $State) {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    # Скидання — час із /usage; минув, а група ще на нулі, чи невідомий — quota_wait_minutes.
    $until = $(if ($Q.ResetAt -gt $now) { [long]$Q.ResetAt } else { $now + [long](60 * (Get-Limit $script:Limits 'QuotaWaitMinutes' 'quota_wait_minutes')) })
    $head = $(if ($State.Kind -eq 'WAIT') { [string](Get-JsonProp $State.Wait 'head') } else { '' })
    [void](Set-MarkerWait $M $until @{ group = $Q.Group; head = $head })
    if ($State.Kind -eq 'NEW') { Write-QuotaStatus $M (New-RunId (Get-MarkerKey $M)) $Q.Group $until @{} }
}

# Один прохід: позначки смуг codex і agy за порядком черги — у вільні слоти, кожна окремим процесом. Повертає число
# запущених.
function Start-Markers($Workers) {
    $started = 0
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $all = @(Get-Markers)
    foreach ($m in @($all | Where-Object { -not $_.Valid })) {
        $state = Get-StatePath (Get-MarkerKey $m)
        if (Test-Path -LiteralPath $state) { continue }
        Write-Log "позначка $($m.Name): назва не за форматом gemini-queue/<наряд>/<модель>/<спроба>[/<умови>] — пропущено"
        Write-FileAtomic $state 'INVALID_NAME'
    }
    $mine = @($all | Where-Object { $_.Valid -and $script:Lanes -contains $_.Lane })
    if ($mine.Count -eq 0) { return 0 }
    foreach ($m in (Get-OrderedMarkers $mine)) {
        $st = Get-MarkerState $m
        if (-not (Test-MarkerReady $st)) { continue }
        if (($now - $m.Time) -gt $MarkerMaxAgeDays * 86400) {
            Write-Log "позначка $($m.Name): коміт старший за $MarkerMaxAgeDays діб — пропущено"
            Write-FileAtomic (Get-StatePath (Get-MarkerKey $m)) 'STALE'
            continue
        }
        if ((@($Workers | Where-Object { $_.Slug -ceq $m.Slug -and -not $_.Proc.HasExited }).Count -gt 0) -or (Test-SlugBusy $m.Slug $script:Lanes)) { continue }
        if ($m.Gpu -and -not (Test-GpuFree $Workers)) { continue }
        $after = $(if ($st.Kind -eq 'WAIT') { [long]$st.Wait.until } else { 0L })
        $sel = Select-Engine $m $after
        if ($sel.Quota.Blocked) { Enter-StartQuotaWait $m $sel.Quota $st; continue }
        # Слот і смуга — за фактичним рушієм після вибору (каскад agy -> Codex займає слот Codex і не перевищує його N).
        $lane = $(if ($sel.Engine.Name -eq 'codex') { 'codex' } else { 'agy' })
        $slot = Get-FreeSlot $lane ([int]$script:Limits.slots[$lane]) $Workers
        if (-not $slot) { continue }
        $id = New-RunId (Get-MarkerKey $m)
        if (-not (New-Claim $m $id)) { continue }
        # Усе між claim і STARTED — під одним обліком відмов (retakes, MaxRetakes, CRASH на межі), 10162/10182.
        try {
            $dir = Join-Path $RunsDir $id
            [void](New-Item -ItemType Directory -Force -Path $dir)
            $job = @{ id = $id; dir = $dir; slot = $slot; lane = $lane; ref = $m.Ref; sha = $m.Sha; time = $m.Time; name = $m.Name
                slug = $m.Slug; model = $m.Model; n = $m.N; cond = $m.Cond; prio = $m.Prio; deadline = $m.Deadline; gpu = $m.Gpu
                head = $(if ($st.Kind -eq 'WAIT') { [string](Get-JsonProp $st.Wait 'head') } else { '' })
                sel = @{ engine = $sel.Engine.Name; emodel = $sel.Engine.Model; effort = $sel.Engine.Effort; model = $sel.Model
                    qknown = $sel.Quota.Known; qleft = $sel.Quota.Left; qgroup = $sel.Quota.Group }
                limits = $script:Limits }
            [void]$Workers.Add((Start-Worker $job $dir))
        } catch {
            Write-Log "позначка $($m.Name): процес наряду не запущено — $($_.Exception.Message)"
            Close-FailedStart $m $id (Get-StatePath (Get-MarkerKey $m))
            continue
        }
        Write-Log "позначка $($m.Name): слот $slot, пріоритет $($m.Prio)$(if ($m.Deadline) { ", строк $($m.Deadline)" })$(if ($m.Gpu) { ', GPU' }) -> $id"
        $started++
    }
    $started
}

# heartbeat.json для стану ноутбука (claude_run.ps1 читає, перевіряючи кожне поле): смуги й слоти, квота груп моделей
# (вікна, % залишку, скидання UTC, коли зчитано), остання відмова Codex, позначки в чеканні квоти. Лише назви й числа.
function Write-Heartbeat([string]$Iso) {
    $hb = [ordered]@{ read_utc = (Get-UtcStamp (Get-Date)); time = (Get-Date).ToString('s'); isolation = $(if ($Iso) { $Iso } else { 'OK' }) }
    if (-not $Iso -and $null -ne $script:Limits) {
        $lanes = @(); $first = $null
        foreach ($ln in $script:Lanes) {
            $busy = @(foreach ($s in @(Read-SlotInfo $ln)) {
                [ordered]@{ slot = [string]$s.slot; marker = [string]$s.marker; model = [string]$s.model; since = [string]$s.since; gpu = [bool]$s.gpu }
            })
            if ($null -eq $first -and $busy.Count -gt 0) { $first = $busy[0] }
            $lanes += [ordered]@{ lane = $ln; n = [int]$script:Limits.slots[$ln]; busy = $busy }
        }
        $hb.lanes = $lanes
        $hb.limits = $script:Limits.source
        # Старі копії claude_run.ps1 читають одну узяту позначку: перша зайнята.
        if ($null -ne $first) {
            $hb.marker = $first.marker; $hb.engine = $(if ($first.slot -like 'codex-*') { 'codex' } else { 'agy' }); $hb.model = $first.model
            try { $hb.since = ([datetime]::ParseExact($first.since, "yyyy-MM-dd'T'HH:mm:ss'Z'", [cultureinfo]::InvariantCulture, 'AssumeUniversal,AdjustToUniversal')).ToLocalTime().ToString('s') } catch { $null = $_ }
        }
        try {
            $c = [System.IO.File]::ReadAllText((Join-Path $RunsDir 'usage.json'), $script:Utf8) | ConvertFrom-Json
            $u = ConvertFrom-UsageText ([string]$c.text) ([long]$c.time)
            $hb.quota = [ordered]@{ read = (Get-UtcStamp $u.Read.UtcDateTime); known = $u.Known
                windows = @(foreach ($w in @($u.Windows | Select-Object -First 12)) {
                    [ordered]@{ g = (ConvertTo-GroupCode $w.Name); w = $w.Window; left = $w.Left; reset = $(if ($null -ne $w.Reset) { Get-UtcStamp $w.Reset.UtcDateTime } else { '' }) }
                }) }
        } catch { $null = $_ }
        try { $hb.codex = [System.IO.File]::ReadAllText((Join-Path $RunsDir 'quota-codex.json'), $script:Utf8) | ConvertFrom-Json } catch { $null = $_ }
        $hb.wait = @(foreach ($w in @(Get-WaitingMarkers | Select-Object -First 12)) { [ordered]@{ marker = $w.Marker; until = $w.Until; g = $w.Group } })
    }
    try { Write-FileAtomic (Join-Path $OutDir 'heartbeat.json') ($hb | ConvertTo-Json -Compress -Depth 6) } catch { Write-Log "heartbeat: $($_.Exception.Message)" }
}

# Процес наряду: слот (замок на весь прогін), GPU (замок, спільний з claude-run), робоча копія слота, прогін.
function Invoke-Worker {
    $job = $script:Job
    $lim = @{ slots = @{} }
    foreach ($p in $job.limits.PSObject.Properties) { $lim[$p.Name] = $p.Value }
    $script:Limits = $lim
    if (-not $script:Bound.ContainsKey('TurnMinutes')) { $script:TurnMinutes = [double]$lim['agy_turn_minutes'] }
    if (-not $script:Bound.ContainsKey('TotalMinutes')) { $script:TotalMinutes = [double]$lim['agy_total_minutes'] }
    if (-not $script:Bound.ContainsKey('CodexStallMinutes')) { $script:CodexStallMinutes = [double]$lim['codex_stall_minutes'] }
    $statePath = Get-StatePath "$($job.ref) $($job.sha)"
    $slotLock = Open-Lock (Join-Path $script:SlotDir "$($job.slot).lock")
    if ($null -eq $slotLock) { Remove-Claim $statePath; Write-Log "слот $($job.slot) зайнятий — позначку не взято"; return $script:WorkerSlotBusy }
    $gpu = $null
    $info = Join-Path $script:SlotDir "$($job.slot).json"
    try {
        if ($job.gpu) {
            $gpu = Open-Lock (Get-GpuLockPath)
            if ($null -eq $gpu) { Remove-Claim $statePath; Write-Log "GPU зайнята — $($job.name) лишається в черзі"; return $script:WorkerGpuBusy }
        }
        Write-FileAtomic $info (([ordered]@{ slot = $job.slot; lane = $job.lane; marker = $job.name; slug = $job.slug; model = $job.model
                    since = (Get-UtcStamp (Get-Date)); gpu = [bool]$job.gpu; prio = $job.prio; pid = $PID }) | ConvertTo-Json -Compress)
        $M = [pscustomobject]@{ Ref = $job.ref; Name = $job.name; Sha = $job.sha; Time = [long]$job.time; Slug = $job.slug; Model = $job.model
            N = [string]$job.n; Cond = [string]$job.cond; Prio = $job.prio; Deadline = $job.deadline; Gpu = [bool]$job.gpu; Lane = $job.lane }
        $wt = Enter-WorkTree (Join-Path (Join-Path $RunsDir 'w') $job.slot) 'refs/remotes/origin/main'
        Set-Variable -Scope Script -Name RepoDir -Value $wt
        Invoke-Task $M $job
        0
    } catch {
        Add-HealthException $_.Exception; Write-Log "процес наряду $($job.name): $($_.Exception.Message)"
        1
    } finally {
        Remove-Item -LiteralPath $info -Force -ErrorAction SilentlyContinue
        # Помилка до STARTED (робоча копія тощо) не лишає claim: позначка повертається в чергу (10162).
        Close-FailedStart ([pscustomobject]@{ Ref = $job.ref; Name = $job.name; Sha = $job.sha; Slug = $job.slug; Model = $job.model
                N = [string]$job.n; Cond = [string]$job.cond }) ([string]$job.id) $statePath
        if ($null -ne $gpu) { $gpu.Dispose() }
        $slotLock.Dispose()
    }
}

function Main {
    if ($WorkerFile) { $script:Job = Read-WorkerJob $WorkerFile }
    $script:StateDir = Join-Path $RunsDir 'state'
    $script:SlotDir = Join-Path $RunsDir 'slots'
    foreach ($d in @($RunsDir, $script:StateDir, $script:SlotDir, $OutDir, $LaneDir)) { [void](New-Item -ItemType Directory -Force -Path $d) }
    $script:NoHooks = Join-Path ([System.IO.Path]::GetTempPath()) ('no-hooks-' + [guid]::NewGuid().ToString('N'))
    $script:HealthAlertDir = Join-Path $OutDir 'alerts'
    if ($WorkerFile) { return (Invoke-Worker) }
    $script:CurrentIsolation = ''
    $script:HeartbeatAction = { Write-Heartbeat $script:CurrentIsolation }
    $lockFile = Open-Lock (Join-Path $RunsDir 'lock')
    if ($null -eq $lockFile) { return 0 }
    try {
        $workers = New-Object System.Collections.ArrayList
        $first = $true
        while ($true) {
            $iso = Test-Isolation
            $script:CurrentIsolation = $iso
            if ($iso) {
                Write-Log "ізоляція: $iso — нових прогонів нема"; Write-IsolationStatus $iso; Write-Heartbeat $iso
                if (@($workers | Where-Object { -not $_.Proc.HasExited }).Count -eq 0) { return 0 }
                Wait-Workers $workers 1; continue
            }
            if ($first) {
                $origin = (Invoke-Git @('remote', 'get-url', 'origin')).Out.Trim()
                if (($origin.TrimEnd('/') -replace '\.git$', '') -ne ($RepoUrl.TrimEnd('/') -replace '\.git$', '')) {
                    Write-Log "origin клону ($origin) не $RepoUrl — прогонів нема"
                    return 1
                }
            }
            $started = 0
            try {
                [void](Invoke-Git @('fetch', '-q', '--prune', '--no-tags', 'origin',
                        '+refs/heads/main:refs/remotes/origin/main',
                        '+refs/heads/gemini/*:refs/remotes/origin/gemini/*',
                        '+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
                $script:Limits = Get-Limits
                if ($first) { Resume-Interrupted }
                Clear-OrphanClaims $RunsDir
                $script:Agy = Find-EngineExe $AgyExe
                if ($script:Agy) { [void](Read-Usage) }
                $started = Start-Markers $workers
            } catch { Add-HealthException $_.Exception; Write-Log "прохід: $($_.Exception.Message)" }
            $first = $false
            foreach ($w in @($workers | Where-Object { $_.Proc.HasExited })) { $workers.Remove($w) }
            Write-Heartbeat ''
            if ($workers.Count -eq 0 -and $started -eq 0) { break }
            Wait-Workers $workers (Get-Limit $script:Limits 'PollMinutes' 'poll_minutes')
        }
        0
    } catch {
        Add-HealthException $_.Exception; Write-Log "збій обгортки: $($_.Exception.Message)"
        1
    } finally {
        $lockFile.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Main) }
