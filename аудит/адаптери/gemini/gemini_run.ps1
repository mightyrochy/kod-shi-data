#Requires -Version 5.1
<#
.SYNOPSIS
Обгортка Gemini (наряд М.2), сторона `gemini`: наряд із публічної черги -> прогін `agy` -> бандл гілки `gemini/<наряд>`.

.DESCRIPTION
Задача планувальника під користувачем Windows `gemini` (ізоляція ОС; входу в GitHub і Claude нема, ключів нема).
Один запуск — щонайбільше один наряд:
  1. перевірка ізоляції за `GEMINI.md` (whoami, `net session`, чужі профілі й диски, змінні з ключами);
  2. `git fetch` без входу: `main`, `gemini/*` і позначки черги `gemini-queue/<наряд>/<модель>/<спроба>`, які ставить
     лише диспетчер; позначка має вказувати на коміт із `main`, текст наряду — лише `аудит/наряди/<наряд>.md` з нього;
  2а. рушій за назвою моделі в позначці (М.9-В): `gpt-<модель>[-<зусилля>]` — локальний Codex (`codex exec`; зусилля —
      none|minimal|low|medium|high|xhigh|max|ultra, відмову `codex exec` обгортка віддає кодом EFFORT_INVALID, без підміни),
      інша — `agy`; квота `agy` як дані (`agy -p "/usage" --output-format json`, 0 ходів): група моделі з 0 % — наряд не
      береться (код `QUOTA_ZERO`), а коли задано `-CodexFallbackModel`, `agy` на 0 % замінює Codex з цією моделлю
      (квоту Codex без ходу не прочитати: його 429 ловить обгортка, код `QUOTA`);
  3. гілка `gemini/<наряд>` від свіжого `main` (чи від уже опублікованої `gemini/<наряд>` — доробка);
  4. один прогін `agy` з межею часу; хід без звіту чи звіт, що не збігся з гілкою, — догонка тієї самої розмови;
     Codex межі часу прогону не має: його зупиняє лише завислість (нема нових подій `--json` довше за -CodexStallMinutes);
  5. бандл гілки й стан (лише коди й числа) у теці обміну; публікує їх окрема задача власника `gemini_publish.ps1`.
Нічого не пушить; ізоляцію не створює й не змінює. Налаштування — `НАЛАШТУВАННЯ.md` поруч.
#>
[CmdletBinding()]
param(
    [string]$RepoDir = (Join-Path $env:USERPROFILE 'kod-shi-data'),
    [string]$RunsDir = (Join-Path $env:USERPROFILE 'gemini-runs'),
    [string]$OutDir = 'C:\Users\Public\gemini\out',
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
    [int]$MaxNudges = 4,
    [double]$QuotaMinutes = 2,
    [int]$MarkerMaxAgeDays = 7,
    [switch]$NoPrintTimeoutFlag
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:QueuePrefix = 'refs/remotes/origin/gemini-queue/'
$script:TaskDir = 'аудит/наряди/'
$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}\z'
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
# Імена моделей для рядка ПУЛИ (9740): лише родини gemini/claude/gpt; той самий шаблон у gemini_publish.ps1.
$script:PoolModelPattern = '^(gemini|claude|gpt)-[a-z0-9.-]{1,36}$'
# `agy -p "/usage"` без ходу моделі й без витрати квоти — з v1.1.11 (changelog agy, 7.08.2026): перелік у НАЛАШТУВАННЯ.md.
$script:UsageMinVersion = [version]'1.1.11'
# Каскад моделей «проєктування» (pro): наступна за пулом після самої моделі позначки; далі лише Codex (-CodexFallbackModel).
$script:ClaudeCascadeModel = 'claude-opus-5-5-high'
# Суфікс-зусилля позначки gpt-*: що `codex exec` не приймає, то відмова (EFFORT_INVALID), а не тиха підміна.
$script:CodexEfforts = 'none|minimal|low|medium|high|xhigh|max|ultra'
$script:AgyVersionDone = $false; $script:AgyVersion = $null; $script:Usage = $null; $script:AgyModels = $null
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -ne 'Core') -or [bool](Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)

# --- дрібні помічники ---------------------------------------------------------------------------------------------

function Write-WrapperLog([string]$Text) {
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Text
    [System.IO.File]::AppendAllText((Join-Path $RunsDir 'wrapper.log'), $line + "`n", $script:Utf8)
}

function Get-Sha256Hex([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $bytes = $sha.ComputeHash($script:Utf8.GetBytes($Text)) } finally { $sha.Dispose() }
    -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

function Write-FileAtomic([string]$Path, [string]$Text) {
    $tmp = $Path + '.part'
    [System.IO.File]::WriteAllText($tmp, $Text, $script:Utf8)
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    Move-Item -LiteralPath $tmp -Destination $Path
}

# Рядок аргументів за правилами CommandLineToArgvW: .NET Framework не має ArgumentList, а вбудований виклик
# PowerShell 5.1 губить лапки всередині аргументів.
function ConvertTo-ArgString([string[]]$Items) {
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

function New-StartInfo([string]$Exe, [string[]]$Arguments, [string]$WorkDir) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = ConvertTo-ArgString $Arguments
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8
    $psi.StandardErrorEncoding = $script:Utf8
    if ($WorkDir) { $psi.WorkingDirectory = $WorkDir }
    $psi.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $psi.EnvironmentVariables['GCM_INTERACTIVE'] = 'never'
    $psi
}

function Stop-Tree($Proc) {
    if ($null -eq $Proc) { return }
    try {
        if (-not $Proc.HasExited) {
            if ($script:OnWindows) { & taskkill.exe /PID $Proc.Id /T /F *> $null }
            else { $Proc.Kill($true) }
        }
        [void]$Proc.WaitForExit(15000)
    } catch { Write-WrapperLog "зупинка процесу: $($_.Exception.Message)" }
}

# Запуск із межею часу; по межі — зупинка всього дерева процесів.
function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDir = '', [double]$TimeoutMinutes = 10) {
    $psi = New-StartInfo $Exe $Arguments $WorkDir
    $p = [System.Diagnostics.Process]::Start($psi)
    $out = $p.StandardOutput.ReadToEndAsync()
    $err = $p.StandardError.ReadToEndAsync()
    $timedOut = -not $p.WaitForExit([int][Math]::Min([double][int]::MaxValue, $TimeoutMinutes * 60000))
    if ($timedOut) { Stop-Tree $p } else { $p.WaitForExit() }
    [pscustomobject]@{ Code = $(if ($timedOut) { -1 } else { $p.ExitCode }); TimedOut = $timedOut; Out = $out.Result; Err = $err.Result }
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

function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
    $all = @('-C', $RepoDir, '-c', "core.hooksPath=$script:NoHooks", '-c', 'credential.helper=', '-c', 'core.quotepath=false') + $GitArgs
    $r = Invoke-Native $GitExe $all
    if ($r.Code -ne 0 -and -not $AllowFail) { throw "git $($GitArgs -join ' ') -> $($r.Code): $($r.Err.Trim())" }
    $r
}

function Get-RefSha([string]$Ref) {
    $r = Invoke-Git @('rev-parse', '-q', '--verify', "$Ref^{commit}") -AllowFail
    if ($r.Code -ne 0) { return '' }
    $r.Out.Trim()
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

# --- черга --------------------------------------------------------------------------------------------------------

function Get-StatePath([string]$Key) { Join-Path (Join-Path $RunsDir 'state') ((Get-Sha256Hex $Key) + '.txt') }

function Get-Markers {
    $fmt = '%(refname)%09%(objectname)%09%(committerdate:unix)'
    $r = Invoke-Git @('for-each-ref', "--format=$fmt", $script:QueuePrefix)
    $list = foreach ($line in ($r.Out -split "`n")) {
        if (-not $line.Trim()) { continue }
        $f = $line.Trim() -split "`t"
        $rest = $f[0].Substring($script:QueuePrefix.Length)
        $parts = $rest -split '/'
        $m = [pscustomobject]@{ Ref = $f[0]; Name = 'gemini-queue/' + $rest; Sha = $f[1]; Time = [long]$f[2]
            Slug = ''; Model = ''; N = ''; Valid = $false }
        if ($parts.Count -eq 3 -and $parts[0] -match $script:SlugPattern -and -not $parts[0].Contains('..') -and
            -not $parts[0].EndsWith('.lock') -and $parts[1] -match $script:ModelPattern -and $parts[2] -match '^[1-9][0-9]{0,2}$') {
            $m.Slug = $parts[0]; $m.Model = $parts[1]; $m.N = $parts[2]; $m.Valid = $true
        }
        $m
    }
    @($list | Sort-Object Time, Name)
}

function Get-NextMarker {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    foreach ($m in Get-Markers) {
        $state = Get-StatePath "$($m.Ref) $($m.Sha)"
        if (Test-Path -LiteralPath $state) { continue }
        # Позначки `cc-` — рушій Claude під власником (claude_run.ps1): gemini-run їх не бере й узятими не позначає.
        if ($m.Valid -and $m.Model.StartsWith('cc-')) { continue }
        if (-not $m.Valid) {
            Write-WrapperLog "позначка $($m.Name): назва не за форматом gemini-queue/<наряд>/<модель>/<спроба> — пропущено"
            Write-FileAtomic $state 'INVALID_NAME'
            continue
        }
        if (($now - $m.Time) -gt $MarkerMaxAgeDays * 86400) {
            Write-WrapperLog "позначка $($m.Name): коміт старший за $MarkerMaxAgeDays діб — пропущено"
            Write-FileAtomic $state 'STALE'
            continue
        }
        return $m
    }
    $null
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
    if (-not $EnableCodex) { Write-WrapperLog 'рушій: Codex вимкнено (без -EnableCodex, 9738) — не кличу'; return $null }
    Find-EngineExe $CodexExe
}

# Шлях до виконуваного рушія; нема в PATH — $null (рушій недоступний), не збій обгортки.
function Find-EngineExe([string]$Name) {
    try { Resolve-Exe $Name } catch { Write-WrapperLog "рушій: $($_.Exception.Message)"; $null }
}

# --- квота --------------------------------------------------------------------------------------------------------

# `agy -p "/usage"` — рядки з табами, дані без ходу моделі (agy ≥ 1.1.11). Колонок документація не наводить: розбір
# за рядком-заголовком і терпимий до назв полів; нерозпізнане — «невідомо»: наряд іде далі (429 ловить Get-ErrorCode).
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

# Хвилини до скидання; -1 — невідомо.
function Get-ResetMinutes($Node) {
    $now = [DateTimeOffset]::UtcNow
    $sec = ConvertTo-Number (Get-FirstValue $Node @('reset_in_seconds', 'resetInSeconds', 'seconds_until_reset', 'secondsUntilReset'))
    if ($null -ne $sec) { return [int][Math]::Ceiling([Math]::Max(0, $sec) / 60) }
    $at = Get-FirstValue $Node @('reset_time', 'resetTime', 'resets_at', 'resetsAt', 'reset_at', 'resetAt', 'reset')
    $when = $null
    if ($at -is [datetime]) { $when = [DateTimeOffset]$at.ToUniversalTime() }
    elseif ($at -is [string]) {
        $dt = [DateTimeOffset]::MinValue
        if ([DateTimeOffset]::TryParse($at, [System.Globalization.CultureInfo]::InvariantCulture, [System.Globalization.DateTimeStyles]::AssumeUniversal, [ref]$dt)) { $when = $dt }
    } else {
        $n = ConvertTo-Number $at
        if ($null -ne $n -and $n -gt 1e9) { $when = [DateTimeOffset]::FromUnixTimeSeconds([long]$(if ($n -gt 1e11) { $n / 1000 } else { $n })) }
    }
    if ($null -eq $when) { return -1 }
    [int][Math]::Ceiling([Math]::Max(0, ($when - $now).TotalMinutes))
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
            [void]$Acc.Add([pscustomobject]@{ Name = $name.Trim(); Left = [int][Math]::Max(0, [Math]::Min(100, [Math]::Round($left))); ResetMin = (Get-ResetMinutes $Node) })
        }
    }
    foreach ($p in $Node.PSObject.Properties) { Get-UsageGroups $p.Value $Acc ($Depth + 1) }
}

# Слова назви без чисел і службових слів: група «Gemini 3.5 Flash» ↔ модель gemini-3.8-flash-high — спільне «flash».
function Get-NameTokens([string]$Name) {
    $stop = @('gemini', 'high', 'medium', 'low', 'preview', 'latest', 'thinking', 'exp', 'and', 'the', 'models', 'model')
    @(($Name.ToLowerInvariant() -split '[^a-z0-9]+') | Where-Object { $_ -and $_ -notmatch '^[0-9]+$' -and $stop -notcontains $_ })
}

# Версія agy з `agy --version`; $null — не розпізнано. Одне читання на прогін.
function Get-AgyVersion {
    if ($script:AgyVersionDone) { return $script:AgyVersion }
    $script:AgyVersionDone = $true
    try {
        if ($script:Agy) {
            $r = Invoke-Native $script:Agy @('--version') $RepoDir 1
            # Версія — лише з рядка з назвою agy («agy 1.1.11», «agy version v1.1.11 (збірка …)»); число з іншого місця
            # (дата, збірка) не береться, нерозпізнане — версія невідома і /usage не кличеться (9743).
            if ($r.Code -eq 0 -and $r.Out -match '\bagy\b[^0-9\r\n]*v?([0-9]+(?:\.[0-9]+){1,3})(?![0-9.])') { $script:AgyVersion = [version]$Matches[1] }
            else { Write-WrapperLog "agy --version не розпізнано (код $($r.Code))" }
        }
    } catch { Write-WrapperLog "agy --version: $($_.Exception.Message)" }
    $script:AgyVersion
}

# Таблиця з табами: перший рядок — заголовок (без цифр), далі записи. Інакше $null.
function ConvertFrom-UsageTable([string]$Text) {
    $lines = @($Text -split "`r?`n" | Where-Object { $_.Contains("`t") })
    if ($lines.Count -lt 2 -or $lines[0] -match '[0-9]') { return $null }
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

# Групи пулів із `/usage`: Known=$false — не читали (стара версія agy, збій чи нерозпізнаний вивід). Кеш на прогін;
# -Fresh читає знову. Виклик лише на версії, яку джерело називає безпечною (UsageMinVersion).
function Read-Usage([switch]$Fresh) {
    if ($null -ne $script:Usage -and -not $Fresh) { return $script:Usage }
    $u = [pscustomobject]@{ Known = $false; Groups = @(); Text = '' }
    try {
        $v = Get-AgyVersion
        if ($null -eq $v -or $v -lt $script:UsageMinVersion) {
            Write-WrapperLog "квота: agy $(if ($v) { $v } else { '?' }) < $($script:UsageMinVersion) — /usage не кличу"
        } else {
            $r = Invoke-Native $script:Agy @('-p', '/usage') $RepoDir $QuotaMinutes
            if ($r.TimedOut -or $r.Code -ne 0) { Write-WrapperLog "квота: agy /usage -> $($r.Code)" }
            else {
                $text = $r.Out.Trim()
                $doc = ConvertFrom-UsageTable $text
                if ($null -eq $doc -and $text.Contains("`t")) {
                    # Табличний вивід без заголовка (чи заголовок із цифрами): колонок не знаємо — квота невідома, не вгадуємо.
                    Write-WrapperLog 'квота: /usage — таблиця без розпізнаного заголовка; квота НЕВІДОМА, каскад за пулом не вмикаю'
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
                $groups = New-Object System.Collections.ArrayList
                if ($null -ne $doc) { Get-UsageGroups $doc $groups }
                $u = [pscustomobject]@{ Known = ($groups.Count -gt 0); Groups = @($groups); Text = $text.Substring(0, [Math]::Min(400, $text.Length)) }
                if (-not $u.Known) { Write-WrapperLog ('квота: груп не розпізнано; вивід /usage: ' + $u.Text) }
            }
        }
    } catch { Write-WrapperLog "квота: $($_.Exception.Message)" }
    $script:Usage = $u
    $u
}

# ASCII-код групи для рядка: назва → A-Z0-9, до 16 знаків.
function ConvertTo-GroupCode([string]$Name) {
    $g = ($Name.ToUpperInvariant() -replace '[^A-Z0-9]', '')
    if (-not $g) { $g = 'MODEL' }
    $g.Substring(0, [Math]::Min(16, $g.Length))
}

# Known=$false — квоту не прочитано (наряд іде далі). Blocked — усі групи моделі на 0 %; Group — ASCII-ім'я для коду рядка.
function Get-Quota([string]$Model, [switch]$Fresh) {
    $none = [pscustomobject]@{ Known = $false; Blocked = $false; Group = ''; ResetMin = -1; Left = -1 }
    $u = Read-Usage -Fresh:$Fresh
    if (-not $u.Known) { return $none }
    $mt = @(Get-NameTokens $Model)
    $hit = @($u.Groups | Where-Object { $g = $_; @(Get-NameTokens $g.Name | Where-Object { $mt -contains $_ }).Count -gt 0 })
    if ($hit.Count -eq 0) {
        Write-WrapperLog ('квота: групу моделі {0} не розпізнано; вивід /usage: {1}' -f $Model, $u.Text)
        return $none
    }
    $zeros = @($hit | Where-Object { $_.Left -eq 0 })
    $ref = $(if ($zeros.Count -eq $hit.Count) { $zeros[0] } else { @($hit | Sort-Object Left -Descending)[0] })
    [pscustomobject]@{ Known = $true; Blocked = ($ref.Left -eq 0); Group = (ConvertTo-GroupCode $ref.Name); ResetMin = $ref.ResetMin; Left = $ref.Left }
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
# на 0 % (Blocked); Exe $null — рушія нема на ноутбуці.
function Select-Engine($M) {
    $e = Get-Engine $M.Model
    $unknown = [pscustomobject]@{ Known = $false; Blocked = $false; Group = ''; ResetMin = -1; Left = -1 }
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
                Write-WrapperLog "рушій: пули agy на 0 % — Codex, модель $cand"
                return [pscustomobject]@{ Engine = $ce; Exe = $cx; Quota = $unknown; Model = $cand }
            }
            continue
        }
        if ($cand -ne $M.Model -and $null -ne $script:AgyModels -and @($script:AgyModels) -notcontains $cand) {
            Write-WrapperLog "каскад: $cand нема в agy models — пропущено"
            continue
        }
        $q = Get-Quota $cand
        if ($null -eq $first) { $first = $q }
        if ($q.Blocked) { Write-WrapperLog "каскад: $cand на 0 % (група $($q.Group))"; continue }
        if ($cand -ne $M.Model) { Write-WrapperLog "рушій: каскад $($M.Model) -> $cand" }
        return [pscustomobject]@{ Engine = $ce; Exe = $script:Agy; Quota = $q; Model = $cand }
    }
    [pscustomobject]@{ Engine = $e; Exe = $script:Agy; Quota = $(if ($first) { $first } else { $unknown }); Model = $M.Model }
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
    if ($Text -match 'authentication required|[Nn]ot logged in|[Pp]lease (?:log ?in|sign in)') { return 'AUTH' }
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
    $Run.Proc = [System.Diagnostics.Process]::Start($psi)
    $Run.Stdin = New-Object System.IO.StreamWriter($Run.Proc.StandardInput.BaseStream, $script:Utf8)
    $Run.Stderr = $Run.Proc.StandardError.ReadToEndAsync()
    $Run.Pending = $null
}

function Close-StreamRun($Run) {
    if ($null -eq $Run.Proc) { return }
    # Дерево — разом із фоновими завданнями агента: інакше вони тримають файли клону до наступного прогону.
    Stop-Tree $Run.Proc
    try { [System.IO.File]::AppendAllText($Run.ErrLog, $Run.Stderr.Result, $script:Utf8) } catch { Write-WrapperLog "stderr agy: $($_.Exception.Message)" }
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
        Write-WrapperLog "codex: нових подій нема понад $CodexStallMinutes хв — завислість, зупинено"
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
                    Write-WrapperLog "agy: статус $status ($code)"
                    break
                }
                $check = Test-Report $M $Start $resp
                if ($check.Accepted) { $code = $check.Kind; $report = $check.Kind; break }
                $why = $(if ($check.Kind -ne 'NONE') { 'mismatch' } else { 'none' })
            }
            # Без id розмови догонка пішла б у нову розмову без наряду.
            if ($r.Kind -ne 'result' -and -not $run.Conversation) {
                $code = $(if ($r.Kind -eq 'timeout') { 'TIMEOUT' } else { 'AGY_ERROR' })
                Write-WrapperLog "agy: $($r.Kind) без id розмови — догонки нема"
                break
            }
            if ((Get-Date) -ge $deadline) { $code = 'TIMEOUT'; break }
            if ($nudges -ge $MaxNudges) { $code = 'NO_REPORT'; break }
            $nudges++
            $text = Get-Nudge $M (Test-Report $M $Start '') $why
            Write-WrapperLog "догонка $nudges ($why)"
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
function Write-Pools {
    $v = Get-AgyVersion
    $u = Read-Usage -Fresh
    $seen = @{}; $groups = @()
    foreach ($g in $u.Groups) {
        $c = ConvertTo-GroupCode $g.Name
        if ($seen.ContainsKey($c)) { continue }
        $seen[$c] = 1
        $groups += [ordered]@{ g = $c; left = [int]$g.Left; reset = [int]$g.ResetMin }
    }
    $models = @(Get-AgyModels)
    $script:AgyModels = $(if ($models.Count -gt 0) { $models } else { $null })
    $pm = @($models | Where-Object { $_ -cmatch $script:PoolModelPattern } | Select-Object -First 6)
    $doc = [ordered]@{ v = 1; time = (Get-Date).ToString('s'); agy = $(if ($v) { [string]$v } else { '' }); groups = @($groups | Select-Object -First 6); models = $pm; unknown = (-not $u.Known) }
    Write-FileAtomic (Join-Path $OutDir 'pools.json') ($doc | ConvertTo-Json -Compress -Depth 4)
}

# --- один наряд ---------------------------------------------------------------------------------------------------

function Reset-Clone {
    foreach ($op in @('merge', 'rebase', 'cherry-pick', 'revert')) { [void](Invoke-Git @($op, '--abort') -AllowFail) }
    $lock = Join-Path $RepoDir '.git\index.lock'
    if (Test-Path -LiteralPath $lock) { Remove-Item -LiteralPath $lock -Force }
    [void](Invoke-Git @('reset', '-q', '--hard'))
    [void](Invoke-Git @('clean', '-q', '-ffd'))
}

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
        Write-WrapperLog "бандл: $($_.Exception.Message)"
        if ($Status.code -in @('DONE', 'BLOCKED', '')) { $Status.code = 'CRASH' }
    }
    if ($T0 -ne [datetime]::MinValue) { $Status.minutes = [int][Math]::Round(((Get-Date) - $T0).TotalMinutes) }
    if ($Tail) { [System.IO.File]::WriteAllText((Join-Path $OutDir ($Status.id + '.tail.txt')), $Tail, $script:Utf8) }
    Write-FileAtomic (Join-Path $OutDir ($Status.id + '.json')) ($Status | ConvertTo-Json -Compress)
    Write-FileAtomic $StatePath "DONE $($Status.id) $($Status.code)"
    Write-WrapperLog "наряд $($Status.slug) [$($Status.id)]: $($Status.code), ходів $($Status.turns), комітів $($Status.ahead)"
}

function Resume-Interrupted {
    foreach ($sf in @(Get-ChildItem -LiteralPath (Join-Path $RunsDir 'state') -Filter '*.txt' -File)) {
        $text = [System.IO.File]::ReadAllText($sf.FullName, $script:Utf8)
        if (-not $text.StartsWith('STARTED {')) { continue }
        $j = $text.Substring(8) | ConvertFrom-Json
        $status = [ordered]@{}
        foreach ($p in $j.PSObject.Properties) { $status[$p.Name] = $p.Value }
        $status.code = 'INTERRUPTED'
        Write-WrapperLog "прогін $($status.id) перервано — закриваю"
        Complete-Status $status $sf.FullName '' ([datetime]::MinValue)
    }
}

function Invoke-Task($M) {
    $key = "$($M.Ref) $($M.Sha)"
    $id = '{0:yyyyMMdd-HHmmss}-{1}' -f (Get-Date), (Get-Sha256Hex $key).Substring(0, 12)
    $statePath = Get-StatePath $key
    $status = [ordered]@{ v = 1; id = $id; slug = $M.Slug; model = $M.Model; n = [int]$M.N; marker = $M.Sha
        start = ''; head = ''; code = ''; report = 'NONE'; ahead = 0; turns = 0; minutes = 0; bundle = ''; engine = 'agy' }
    Write-FileAtomic $statePath ('STARTED ' + ($status | ConvertTo-Json -Compress))
    $dir = Join-Path $RunsDir $id
    [void](New-Item -ItemType Directory -Force -Path $dir)
    $t0 = Get-Date
    $tail = ''
    Write-WrapperLog "наряд $($M.Name) $($M.Sha) -> $id"
    try {
        $main = Get-RefSha 'refs/remotes/origin/main'
        $anc = Invoke-Git @('merge-base', '--is-ancestor', $M.Sha, $main) -AllowFail
        $taskPath = $script:TaskDir + $M.Slug + '.md'
        if ($anc.Code -ne 0) { $status.code = 'NOT_ON_MAIN'; return }
        if ((Invoke-Git @('cat-file', '-e', "$($M.Sha):$taskPath") -AllowFail).Code -ne 0) { $status.code = 'NO_TASK_FILE'; return }
        $taskText = (Invoke-Git @('cat-file', 'blob', "$($M.Sha):$taskPath")).Out
        # Квота до наряду: група моделі з 0 % — наряд не береться (марно палить спробу й дає 429 посеред прогону).
        $sel = Select-Engine $M
        $q = $sel.Quota
        $status.engine = $sel.Engine.Name
        $status.actual = $sel.Model
        # Межа розміру наряду — для agy (як було); Codex читає наряд з файлу `turnN.md`, розмір не обмежено (власник 26.10).
        if ($sel.Engine.Name -ne 'codex' -and $taskText.Length -gt 30000) { $status.code = 'TASK_TOO_LONG'; return }
        $MA = $M | Select-Object *
        $MA.Model = $sel.Model
        if (-not $sel.Exe) { $status.code = 'ENGINE_MISSING'; return }
        if ($q.Blocked) {
            $status.code = 'QUOTA_ZERO'; $status.quota = 0; $status.qgroup = $q.Group
            if ($q.ResetMin -ge 0) { $status.qreset = $q.ResetMin }
            Write-WrapperLog "квота: група $($q.Group) на 0 %, скидання через $($q.ResetMin) хв — наряд не береться"
            return
        }
        $start = Get-RefSha "refs/remotes/origin/gemini/$($M.Slug)"
        if (-not $start) { $start = $main }
        Reset-Clone
        [void](Invoke-Git @('checkout', '-q', '-f', '-B', "gemini/$($M.Slug)", $start))
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
        # Залишок квоти після прогону — для рядка кінця наряду.
        $qa = $(if ($sel.Engine.Name -eq 'agy') { Get-Quota $sel.Model -Fresh } else { $q })
        if ($qa.Known) { $status.quota = $qa.Left; $status.qgroup = $qa.Group }
    } catch {
        $status.code = 'CRASH'
        Write-WrapperLog "збій: $($_.Exception.Message)"
    } finally {
        Complete-Status $status $statePath $tail $t0
    }
}

function Write-IsolationStatus([string]$Check) {
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

function Main {
    foreach ($d in @($RunsDir, (Join-Path $RunsDir 'state'), $OutDir)) { [void](New-Item -ItemType Directory -Force -Path $d) }
    $script:NoHooks = Join-Path ([System.IO.Path]::GetTempPath()) ('no-hooks-' + [guid]::NewGuid().ToString('N'))
    $lockFile = $null
    try { $lockFile = [System.IO.File]::Open((Join-Path $RunsDir 'lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { return 0 }
    try {
        $iso = Test-Isolation
        $hb = [ordered]@{ time = (Get-Date).ToString('s'); isolation = $(if ($iso) { $iso } else { 'OK' }) }
        Write-FileAtomic (Join-Path $OutDir 'heartbeat.json') ($hb | ConvertTo-Json -Compress)
        if ($iso) { Write-WrapperLog "ізоляція: $iso — прогонів нема"; Write-IsolationStatus $iso; return 0 }
        $origin = (Invoke-Git @('remote', 'get-url', 'origin')).Out.Trim()
        if (($origin.TrimEnd('/') -replace '\.git$', '') -ne ($RepoUrl.TrimEnd('/') -replace '\.git$', '')) {
            Write-WrapperLog "origin клону ($origin) не $RepoUrl — прогонів нема"
            return 1
        }
        [void](Invoke-Git @('fetch', '-q', '--prune', '--no-tags', 'origin',
                '+refs/heads/main:refs/remotes/origin/main',
                '+refs/heads/gemini/*:refs/remotes/origin/gemini/*',
                '+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
        $m = Get-NextMarker
        Resume-Interrupted
        $script:Agy = Find-EngineExe $AgyExe
        if ($script:Agy) { try { Write-Pools } catch { Write-WrapperLog "пули: $($_.Exception.Message)" } }
        if ($null -eq $m) { return 0 }
        # Узята позначка — в heartbeat, поки наряд іде: її бачать стан ноутбука й вимкнення (claude_run.ps1).
        $hb.marker = $m.Name; $hb.engine = (Get-Engine $m.Model).Name; $hb.model = $m.Model; $hb.since = (Get-Date).ToString('s')
        Write-FileAtomic (Join-Path $OutDir 'heartbeat.json') ($hb | ConvertTo-Json -Compress)
        try { Invoke-Task $m }
        finally {
            foreach ($k in @('marker', 'engine', 'model', 'since')) { $hb.Remove($k) }
            $hb.time = (Get-Date).ToString('s')
            Write-FileAtomic (Join-Path $OutDir 'heartbeat.json') ($hb | ConvertTo-Json -Compress)
        }
        0
    } catch {
        Write-WrapperLog "збій обгортки: $($_.Exception.Message)"
        1
    } finally {
        $lockFile.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Main) }
