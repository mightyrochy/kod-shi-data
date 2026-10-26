#Requires -Version 5.1
<#
.SYNOPSIS
Третій рушій ноутбука: наряд за позначкою `gemini-queue/<наряд>/cc-<модель>[-<зусилля>]/<спроба>` веде Claude Code без
вікна (`claude -p`) під власником; кінець — один рядок теки вихідних; стан ноутбука — тіло issue, переписане на місці.

.DESCRIPTION
Задача планувальника `claude-run` під власником, раз на 5 хв; водночас один прохід (замок) і один наряд.
  1. Позначки — лише `cc-…` з `origin` (fetch у клон власника `RepoDir`); `gemini-run` їх не бере. Узята позначка —
     файл стану на ноутбуці, вдруге не береться. Коміт позначки — у `main`, наряд — файл `аудит/наряди/<наряд>.md`
     на цьому коміті; позначка вибирає лише наряд, модель і спробу. Позначок обгортка не пушить.
  2. `cc-<модель>-<зусилля>`: модель і зусилля йдуть у `claude --model/--effort` дослівно; неприйняте —
     ЗАБЛОКОВАНО з кодом (MODEL_INVALID, EFFORT_INVALID), без підміни. Дозволи — `--permission-mode auto`
     (класифікатор, як у ноутбучних сесій), без обходу.
  3. Промпт — перший і останній рядки запускача (`аудит/ЗАПУСКАЧ.md`) без його id і з вимкненням «лише обгортка за
     позначкою»; нова спроба при наявній гілці наряду — ще «продовжуй з гілки». Гілку й PR-чернетку сесія пушить сама.
  4. Межі часу всього нема: зупиняє лише завислість — жодної події stream-json довше за -HangMinutes (HANG). Часи
     подій — `runs\<id>\events.tsv`, щоб поріг вивіряти за прогонами.
  5. Кінець — рядок теки вихідних (доставляє `gemini-publish`): ГОТОВО <гілка> <SHA40>, лише коли `origin` має
     саме цей SHA на гілці зі звіту, або ЗАБЛОКОВАНО claude/<наряд> <КОД>. Лише обчислене: тексту сесії в рядку нема.
  6. Позначка `gemini-queue/ВИМКНИ-НОУТБУК/cc-off/<спроба>`: коли рушії не працюють — рядок ВИМКНЕНО, чекання
     доставки й `shutdown`. Позначка, що вже була до першого проходу після ввімкнення, — ЗАБЛОКОВАНО … BOOT.
  7. Стан — тіло issue -StatusIssue (`gh api -X PATCH`), щопроходу й раз на -StatusMinutes під час наряду: задачі
     планувальника, `isolation`, узяті позначки, рушії, моделі, хвилини — лише обчислене.
#>
[CmdletBinding()]
param(
    [string]$WorkDir = (Join-Path $env:USERPROFILE 'claude-run'),
    [string]$RepoDir = (Join-Path $env:USERPROFILE 'kod-shi-data'),
    [string]$OutboxDir = (Join-Path $env:USERPROFILE 'gemini-outbox'),
    [string]$PublishDir = (Join-Path $env:USERPROFILE 'gemini-publish'),
    [string]$GeminiOutDir = 'C:\Users\Public\gemini\out',
    [string]$RepoUrl = 'https://github.com/mightyrochy/kod-shi-data',
    [string]$Repo = 'mightyrochy/kod-shi-data',
    [int]$StatusIssue = 1856,
    [string]$GitExe = 'git',
    [string]$ClaudeExe = 'claude',
    [string]$GhExe = 'gh',
    [double]$HangMinutes = 120,
    [double]$StatusMinutes = 5,
    [int]$MarkerMaxAgeDays = 7,
    [double]$OffWaitMinutes = 10,
    [string[]]$TaskNames = @('claude-run', 'gemini-run', 'gemini-publish', 'gemini-watch'),
    [string]$GeminiUser = 'gemini',
    [switch]$NoStatus
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:QueuePrefix = 'refs/remotes/origin/gemini-queue/'
$script:TaskDir = 'аудит/наряди/'
$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}\z'
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
$script:EffortPattern = '^(.+)-(none|minimal|low|medium|high|xhigh|max|ultra)$'
$script:OffSlug = 'ВИМКНИ-НОУТБУК'
$script:OffModel = 'cc-off'
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -ne 'Core') -or [bool](Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)
$script:Phase = 'старт'
$script:Current = $null
$script:LastStatus = [datetime]::MinValue
$script:FreshBoot = $false

# Шаблони рядків — ті самі, що в `gemini_publish.ps1` (OutboxTemplates): рядок, що не збігся, у теку не йде.
$script:SlugCore = $script:SlugPattern -replace '^\^|\\z$', ''
$script:LineTemplates = @(
    "\AGEMINI ОБГОРТКА: ГОТОВО claude/$script:SlugCore [0-9a-f]{40} МОДЕЛЬ [a-z0-9][a-z0-9.-]{1,63}\z",
    "\AGEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$script:SlugCore [A-Z0-9_]{2,40}\z",
    '\AGEMINI ОБГОРТКА: ВИМКНЕНО [0-9a-f]{40}\z'
)

# --- допоміжне ----------------------------------------------------------------------------------------------------

function Write-RunLog([string]$Text) {
    $path = Join-Path $WorkDir 'claude-run.log'
    if ((Test-Path -LiteralPath $path) -and (Get-Item -LiteralPath $path).Length -gt 1MB) {
        Move-Item -LiteralPath $path -Destination ($path + '.old') -Force
    }
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Text
    [System.IO.File]::AppendAllText($path, $line + "`n", $script:Utf8)
}

function Get-Sha256Hex([string]$Text) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { -join ($sha.ComputeHash($script:Utf8.GetBytes($Text)) | ForEach-Object { $_.ToString('x2') }) }
    finally { $sha.Dispose() }
}

function Write-FileAtomic([string]$Path, [string]$Text) {
    $tmp = $Path + '.part'
    [System.IO.File]::WriteAllText($tmp, $Text, $script:Utf8)
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    Move-Item -LiteralPath $tmp -Destination $Path
}

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

function New-StartInfo([string]$Exe, [string[]]$Arguments, [string]$Dir) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = ConvertTo-ArgString $Arguments
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8
    $psi.StandardErrorEncoding = $script:Utf8
    if ($Dir) { $psi.WorkingDirectory = $Dir }
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
    } catch { Write-RunLog "зупинка процесу: $($_.Exception.Message)" }
}

function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$Dir = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) {
    $psi = New-StartInfo $Exe $Arguments $Dir
    $psi.RedirectStandardInput = ($null -ne $StdIn)
    $p = [System.Diagnostics.Process]::Start($psi)
    $out = $p.StandardOutput.ReadToEndAsync()
    $err = $p.StandardError.ReadToEndAsync()
    if ($null -ne $StdIn) {
        $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $script:Utf8)
        $w.Write($StdIn)
        $w.Close()
    }
    $timedOut = -not $p.WaitForExit([int][Math]::Min([double][int]::MaxValue, $TimeoutMinutes * 60000))
    if ($timedOut) { Stop-Tree $p } else { $p.WaitForExit() }
    [pscustomobject]@{ Code = $(if ($timedOut) { -1 } else { $p.ExitCode }); Out = $out.Result; Err = $err.Result }
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

# Обгортка не пушить і входу не потребує: credential.helper вимкнено (репозиторій відкритий), гачки — порожня тека.
function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail, [double]$TimeoutMinutes = 10) {
    $all = @('-C', $RepoDir, '-c', "core.hooksPath=$script:NoHooks", '-c', 'credential.helper=', '-c', 'core.quotepath=false') + $GitArgs
    $r = Invoke-Native $GitExe $all '' $TimeoutMinutes
    if ($r.Code -ne 0 -and -not $AllowFail) { throw "git $($GitArgs -join ' ') -> $($r.Code): $($r.Err.Trim())" }
    $r
}

function Get-RefSha([string]$Ref) {
    $r = Invoke-Git @('rev-parse', '-q', '--verify', "$Ref^{commit}") -AllowFail
    if ($r.Code -ne 0) { return '' }
    $r.Out.Trim()
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

function Get-UtcStamp([datetime]$When) { $When.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }

# --- тека вихідних ------------------------------------------------------------------------------------------------

# Ім'я файлу (без .txt) або '' — рядок не за шаблоном.
function Add-Line([string]$Line) {
    $ok = $false
    foreach ($t in $script:LineTemplates) { if ($Line -cmatch $t) { $ok = $true; break } }
    if (-not $ok -or $Line.Contains('..')) { Write-RunLog "рядок не за шаблоном — не записано: $Line"; return '' }
    $id = New-Id
    Write-FileAtomic (Join-Path $OutboxDir "$id.txt") $Line
    Write-RunLog "рядок $id : $Line"
    $id
}

# --- позначки -----------------------------------------------------------------------------------------------------

function Get-StatePath([string]$Key) { Join-Path (Join-Path $WorkDir 'state') ((Get-Sha256Hex $Key) + '.txt') }

# Лише позначки рушія Claude (модель `cc-…`), за часом коміту.
function Get-Markers {
    $fmt = '%(refname)%09%(objectname)%09%(committerdate:unix)'
    $r = Invoke-Git @('for-each-ref', "--format=$fmt", $script:QueuePrefix)
    $list = foreach ($line in ($r.Out -split "`n")) {
        if (-not $line.Trim()) { continue }
        $f = $line.Trim() -split "`t"
        $parts = $f[0].Substring($script:QueuePrefix.Length) -split '/'
        if ($parts.Count -ne 3 -or -not $parts[1].StartsWith('cc-')) { continue }
        if ($parts[0] -notmatch $script:SlugPattern -or $parts[0].Contains('..') -or $parts[0].EndsWith('.lock') -or
            $parts[1] -notmatch $script:ModelPattern -or $parts[2] -notmatch '^[1-9][0-9]{0,2}$') { continue }
        $cc = $parts[1].Substring(3); $model = $cc; $effort = ''
        if ($cc -cmatch $script:EffortPattern) { $model = $Matches[1]; $effort = $Matches[2] }
        [pscustomobject]@{ Ref = $f[0]; Name = 'gemini-queue/' + ($parts -join '/'); Sha = $f[1]; Time = [long]$f[2]
            Slug = $parts[0]; Model = $parts[1]; Claude = $model; Effort = $effort; N = $parts[2]
            Off = ($parts[0] -ceq $script:OffSlug -and $parts[1] -ceq $script:OffModel) }
    }
    @($list | Sort-Object Time, Name)
}

function Get-NextMarker {
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    foreach ($m in Get-Markers) {
        $state = Get-StatePath "$($m.Ref) $($m.Sha)"
        if (Test-Path -LiteralPath $state) {
            # Виконана позначка вимкнення (стан OFF) на першому проході після нового ввімкнення — теж один BOOT і без
            # другого вимкнення: диспетчер бачить, що ноутбук знову працює, а позначка витрачена.
            if (-not ($m.Off -and $script:FreshBoot -and [System.IO.File]::ReadAllText($state, $script:Utf8).StartsWith('OFF '))) { continue }
        }
        elseif (($now - $m.Time) -gt $MarkerMaxAgeDays * 86400) {
            Write-RunLog "позначка $($m.Name): коміт старший за $MarkerMaxAgeDays діб — пропущено"
            Write-FileAtomic $state 'STALE'
            continue
        }
        # Позначка вимкнення, що вже стояла до першого проходу після ввімкнення, — поставлена, коли ноутбук був вимкнений.
        if ($m.Off -and $script:FreshBoot) {
            Write-RunLog "позначка $($m.Name): була до ввімкнення — не вимикаю"
            [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($m.Slug) BOOT")
            Write-FileAtomic $state 'DONE BOOT'
            continue
        }
        return $m
    }
    $null
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
        } catch { }
        [pscustomobject]$row
    }
}

# heartbeat.json обгортки Gemini: лише поля за форматом, решта — «?».
function Read-GeminiBeat {
    $b = [ordered]@{ Time = '?'; Isolation = '?'; Marker = ''; Engine = ''; Model = ''; Minutes = '' }
    $path = Join-Path $GeminiOutDir 'heartbeat.json'
    try { $j = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json } catch { return [pscustomobject]$b }
    $get = { param($n) $p = $j.PSObject.Properties[$n]; if ($null -eq $p) { '' } elseif ($p.Value -is [datetime]) { $p.Value.ToString('s') } else { [string]$p.Value } }
    $t = & $get 'time'
    if ($t -match '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$') { $b.Time = Get-UtcStamp ([datetime]::ParseExact($t, 's', [cultureinfo]::InvariantCulture)) }
    $iso = & $get 'isolation'
    if ($iso -cmatch '^[A-Z0-9_]{2,40}$') { $b.Isolation = $iso }
    $mk = & $get 'marker'
    if ($mk -cmatch '^gemini-queue/[\p{L}\p{Nd}._-]{1,80}/[a-z0-9][a-z0-9.-]{1,63}/[1-9][0-9]{0,2}$' -and -not $mk.Contains('..')) {
        $b.Marker = $mk
        $e = & $get 'engine'; if ($e -cmatch '^[a-z]{2,10}$') { $b.Engine = $e }
        $md = & $get 'model'; if ($md -cmatch $script:ModelPattern) { $b.Model = $md }
        $s = & $get 'since'
        if ($s -match '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d$') {
            $b.Minutes = [string][int][Math]::Floor(((Get-Date) - [datetime]::ParseExact($s, 's', [cultureinfo]::InvariantCulture)).TotalMinutes)
        }
    }
    [pscustomobject]$b
}

# --- стан ---------------------------------------------------------------------------------------------------------

function Get-StatusBody {
    $host_ = $(if ($env:COMPUTERNAME -match '^[A-Za-z0-9-]{1,15}$') { $env:COMPUTERNAME } else { '?' })
    $g = Read-GeminiBeat
    $rows = @(Get-TaskRows)
    $c = $script:Current
    $lines = @(
        '<!-- Тіло переписує задача claude-run на ноутбуці (аудит/адаптери/gemini/claude_run.ps1); лише обчислене. -->',
        "**Ноутбук $host_** · оновлено $(Get-UtcStamp (Get-Date)) · claude-run: $script:Phase",
        '',
        'Оновлено понад 15 хв тому — задача `claude-run` не працює: ноутбук вимкнено, сплячий чи задачу зупинено.',
        '',
        '| задача | востаннє запущено (UTC) | результат | стан |',
        '|---|---|---|---|'
    )
    foreach ($r in $rows) { $lines += "| $($r.Name) | $($r.Last) | $($r.Result) | $($r.State) |" }
    $lines += @('', '| рушій | позначка | модель | хвилин |', '|---|---|---|---|')
    if ($null -ne $c) {
        $mins = [int][Math]::Floor(((Get-Date) - $c.Since).TotalMinutes)
        $lines += "| claude | $($c.Marker) | $($c.Claude)$(if ($c.Effort) { ' ' + $c.Effort }) | $mins |"
    } else { $lines += '| claude | — | — | — |' }
    if ($g.Marker) { $lines += "| gemini-run · $(if ($g.Engine) { $g.Engine } else { '?' }) | $($g.Marker) | $(if ($g.Model) { $g.Model } else { '?' }) | $(if ($g.Minutes) { $g.Minutes } else { '?' }) |" }
    else { $lines += '| gemini-run | — | — | — |' }
    $lines += @('', "heartbeat gemini-run: $($g.Time) · isolation: $($g.Isolation)")
    ($lines -join "`n") + "`n"
}

# Стан — у файл і в issue; збій GitHub не зупиняє наряду. -Force — поза ритмом -StatusMinutes.
function Update-Status([switch]$Force) {
    if (-not $Force -and ((Get-Date) - $script:LastStatus).TotalMinutes -lt $StatusMinutes) { return }
    $script:LastStatus = Get-Date
    try {
        $body = Get-StatusBody
        Write-FileAtomic (Join-Path $WorkDir 'status.md') $body
        $hb = [ordered]@{ time = (Get-Date).ToString('s'); phase = $script:Phase }
        if ($null -ne $script:Current) { $hb.marker = $script:Current.Marker; $hb.model = $script:Current.Model; $hb.since = $script:Current.Since.ToString('s') }
        Write-FileAtomic (Join-Path $WorkDir 'heartbeat.json') ($hb | ConvertTo-Json -Compress)
        if ($NoStatus) { return }
        $gh = Find-Exe $GhExe
        if (-not $gh) { Write-RunLog 'стан: gh не знайдено'; return }
        $in = Join-Path $WorkDir 'status.json'
        Write-FileAtomic $in (([ordered]@{ body = $body }) | ConvertTo-Json -Compress)
        $r = Invoke-Native $gh @('api', '-X', 'PATCH', '-H', 'Accept: application/vnd.github+json',
            "repos/$Repo/issues/$StatusIssue", '--input', $in) $WorkDir 3
        if ($r.Code -ne 0) { Write-RunLog "стан: gh api -> $($r.Code): $($r.Err.Trim())" }
    } catch { Write-RunLog "стан: $($_.Exception.Message)" }
}

# --- наряд --------------------------------------------------------------------------------------------------------

function Get-BranchPath([string]$Slug) { Join-Path (Join-Path $WorkDir 'state') ('branch-' + (Get-Sha256Hex $Slug) + '.txt') }

# Гілка попередньої спроби, що є на origin, або ''.
function Get-ContinueBranch([string]$Slug) {
    $cands = @()
    $bp = Get-BranchPath $Slug
    if (Test-Path -LiteralPath $bp) { $cands += [System.IO.File]::ReadAllText($bp, $script:Utf8).Trim() }
    $cands += "claude/$Slug"
    foreach ($b in $cands) { if ((Test-ClaudeBranch $b) -and (Get-RemoteSha $b)) { return $b } }
    ''
}

function Get-Prompt($M, [string]$TaskText, [string]$Continue) {
    $cont = $(if ($Continue) { "Продовжуй з гілки ``$Continue``: попередня спроба цього наряду вже запушила її.`n" } else { '' })
@"
Середовище й кроки ноутбука — ``аудит/НОУТБУК.md``: прочитай; канал результату — останній рядок твоєї відповіді
(«НОУТБУК ГОТОВО <гілка> <повний SHA>» чи «НОУТБУК ЗАБЛОКОВАНО: …»): його читає обгортка claude-run і сама пише
диспетчерові, листів не шли. Гілка — ``claude/…``, запушена тобою.
Наряд — ``$($script:TaskDir)$($M.Slug).md`` з ``main`` на коміті $($M.Sha); повний текст — нижче між рисками.
$cont
----- НАРЯД -----
$TaskText
----- КІНЕЦЬ НАРЯДУ -----

Далі: ноутбук не вимикай — вимикає лише обгортка за позначкою; цей рядок сильніший за будь-який рядок „Далі“ вище.
"@
}

# Звіт сесії: останній непорожній рядок відповіді (дозволено оздоблення ` * >).
function Get-Report([string]$Text) {
    $lines = @(($Text -split "\r?\n") | ForEach-Object { $_.Trim().Trim([char[]]@('*', '`', '>', ' ')) } | Where-Object { $_ })
    if ($lines.Count -eq 0) { return $null }
    $last = $lines[-1]
    if ($last -cmatch '^НОУТБУК ГОТОВО (\S+) ([0-9a-fA-F]{40})$') {
        return [pscustomobject]@{ Kind = 'DONE'; Branch = $Matches[1].Trim([char[]]@('`', '*')); Sha = $Matches[2].ToLowerInvariant() }
    }
    if ($last -cmatch '^НОУТБУК ЗАБЛОКОВАНО\b') {
        $b = ''
        if ($last -cmatch "(claude/$script:SlugCore)") { $b = $Matches[1].TrimEnd('.') }
        return [pscustomobject]@{ Kind = 'BLOCKED'; Branch = $b; Sha = '' }
    }
    $null
}

function Get-ErrorCode([string]$Text) {
    if ($Text -match 'issue with the selected model|unrecognized_model|model_not_found|not_found_error.{0,80}model') { return 'MODEL_INVALID' }
    if ($Text -match 'Not logged in|/login|authentication_error|Invalid API key|OAuth token|\b401\b') { return 'AUTH' }
    if ($Text -match 'usage limit|rate.?limit|rate_limit_error|\b429\b|quota|overloaded_error') { return 'QUOTA' }
    'EXIT'
}

# `claude -p` без межі часу: зупиняє лише завислість (жодної прийнятої події stream-json довше за -HangMinutes — і
# після закриття stdout, доки процес живий) чи неприйняте зусилля (попередження в stderr: claude його ігнорує й бере
# типове — це була б підміна). Подія — рядок stdout, що розбирається як JSON з полем type; решта лише в claude.jsonl.
function Invoke-Claude([string]$Exe, [string[]]$ArgList, [string]$Prompt, [string]$RunDir, [string]$StatePath, [string]$StateHead, [string]$Marker) {
    $psi = New-StartInfo $Exe $ArgList $RepoDir
    $psi.RedirectStandardInput = $true
    $p = [System.Diagnostics.Process]::Start($psi)
    $start = ''; try { $start = Get-UtcStamp $p.StartTime } catch { }
    Write-FileAtomic $StatePath ($StateHead + ' ' + (([ordered]@{ pid = $p.Id; start = $start; marker = $Marker }) | ConvertTo-Json -Compress))
    $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $script:Utf8)
    $w.Write($Prompt)
    $w.Close()
    $log = Join-Path $RunDir 'claude.jsonl'; $ev = Join-Path $RunDir 'events.tsv'; $errLog = Join-Path $RunDir 'claude.stderr.txt'
    $res = [pscustomobject]@{ Code = 0; Kind = ''; Result = $null; Err = '' }
    $err = New-Object System.Text.StringBuilder
    $last = Get-Date
    $outTask = $null; $errTask = $null; $outDone = $false; $errDone = $false
    while ($true) {
        if (-not $outDone -and $null -eq $outTask) { $outTask = $p.StandardOutput.ReadLineAsync() }
        if (-not $errDone -and $null -eq $errTask) { $errTask = $p.StandardError.ReadLineAsync() }
        $left = ($last.AddMinutes($HangMinutes) - (Get-Date)).TotalMilliseconds
        if ($left -le 0) { $res.Kind = 'HANG'; break }
        $ms = [int][Math]::Min($left, 60000)
        $wait = [System.Threading.Tasks.Task[]]@(@($outTask, $errTask) | Where-Object { $null -ne $_ })
        if ($wait.Count -eq 0) {
            # Обидва потоки закрито, процес ще живий: той самий поріг завислості й стан, без окремої межі.
            if ($p.WaitForExit($ms)) { break }
            Update-Status
            continue
        }
        $i = [System.Threading.Tasks.Task]::WaitAny($wait, $ms)
        Update-Status
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
        if ($line -match '^\s*\{\s*"type"\s*:\s*"([a-z_]{1,40})"') {
            $tp = $Matches[1]
            try { $obj = $line | ConvertFrom-Json -ErrorAction Stop; $type = $tp } catch { }
        }
        if (-not $type) { continue }
        $last = Get-Date
        [System.IO.File]::AppendAllText($ev, $last.ToString('s') + "`t" + $type + "`n", $script:Utf8)
        if ($type -eq 'result') { $res.Result = $obj }
    }
    if ($res.Kind) { Stop-Tree $p }
    $res.Code = $(if ($p.HasExited) { $p.ExitCode } else { -1 })
    $res.Err = $err.ToString()
    $res
}

function Complete-Task($M, [string]$StatePath, [string]$Id, [string]$Code, [string]$Branch = '', [string]$Sha = '') {
    $line = $(if ($Code -eq 'DONE') { "GEMINI ОБГОРТКА: ГОТОВО $Branch $Sha МОДЕЛЬ $($M.Model)" }
              else { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) $Code" })
    if (-not (Add-Line $line)) { $Code = 'LINE_REJECTED' }
    $runDir = Join-Path (Join-Path $WorkDir 'runs') $Id
    if (Test-Path -LiteralPath $runDir) {
        Write-FileAtomic (Join-Path $runDir 'result.json') (([ordered]@{ marker = $M.Name; sha = $M.Sha; code = $Code; branch = $Branch; head = $Sha; end = (Get-Date).ToString('s') }) | ConvertTo-Json -Compress)
    }
    Write-FileAtomic $StatePath "DONE $Id $Code"
    Write-RunLog "позначка $($M.Name): $Code"
}

function Invoke-Task($M) {
    $statePath = Get-StatePath "$($M.Ref) $($M.Sha)"
    $id = New-Id
    $main = Get-RefSha 'refs/remotes/origin/main'
    $taskPath = "$($script:TaskDir)$($M.Slug).md"
    if (-not $main -or (Invoke-Git @('merge-base', '--is-ancestor', $M.Sha, $main) -AllowFail).Code -ne 0) { return (Complete-Task $M $statePath $id 'NOT_ON_MAIN') }
    if ((Invoke-Git @('cat-file', '-e', "$($M.Sha):$taskPath") -AllowFail).Code -ne 0) { return (Complete-Task $M $statePath $id 'NO_TASK_FILE') }
    if ($M.Claude -notmatch $script:ModelPattern) { return (Complete-Task $M $statePath $id 'MODEL_INVALID') }
    $exe = Find-Exe $ClaudeExe
    if (-not $exe) { return (Complete-Task $M $statePath $id 'ENGINE_MISSING') }
    $taskText = (Invoke-Git @('cat-file', 'blob', "$($M.Sha):$taskPath")).Out
    $cont = Get-ContinueBranch $M.Slug
    $runDir = Join-Path (Join-Path $WorkDir 'runs') $id
    [void](New-Item -ItemType Directory -Force -Path $runDir)
    $prompt = Get-Prompt $M $taskText $cont
    [System.IO.File]::WriteAllText((Join-Path $runDir 'prompt.txt'), $prompt, $script:Utf8)
    $a = @('-p', '--model', $M.Claude)
    if ($M.Effort) { $a += @('--effort', $M.Effort) }
    $a += @('--permission-mode', 'auto', '--output-format', 'stream-json', '--verbose')
    $script:Current = [pscustomobject]@{ Marker = $M.Name; Model = $M.Model; Claude = $M.Claude; Effort = $M.Effort; Since = (Get-Date) }
    $script:Phase = 'веде наряд'
    Write-RunLog "позначка $($M.Name): старт $id, claude $($a -join ' ')$(if ($cont) { ", продовжує $cont" })"
    Update-Status -Force
    try {
        $r = Invoke-Claude $exe $a $prompt $runDir $statePath "STARTED $id" $M.Name
    } catch {
        Write-RunLog "claude: $($_.Exception.Message)"
        return (Complete-Task $M $statePath $id 'CRASH')
    }
    if ($r.Kind) { return (Complete-Task $M $statePath $id $r.Kind) }
    $text = ''; $isError = $false
    if ($null -ne $r.Result) {
        $pr = $r.Result.PSObject.Properties['result']; if ($null -ne $pr -and $null -ne $pr.Value) { $text = [string]$pr.Value }
        $pe = $r.Result.PSObject.Properties['is_error']; if ($null -ne $pe) { $isError = [bool]$pe.Value }
    }
    $rep = $(if ($text) { Get-Report $text } else { $null })
    if ($null -ne $rep -and $rep.Branch -and (Test-ClaudeBranch $rep.Branch) -and (Get-RemoteSha $rep.Branch)) {
        [System.IO.File]::WriteAllText((Get-BranchPath $M.Slug), $rep.Branch, $script:Utf8)
    }
    if ($null -ne $rep -and $rep.Kind -eq 'DONE') {
        if (-not (Test-ClaudeBranch $rep.Branch)) { return (Complete-Task $M $statePath $id 'BAD_BRANCH') }
        if ((Get-RemoteSha $rep.Branch) -ne $rep.Sha) { return (Complete-Task $M $statePath $id 'NO_PUSH') }
        return (Complete-Task $M $statePath $id 'DONE' $rep.Branch $rep.Sha)
    }
    if ($null -ne $rep) { return (Complete-Task $M $statePath $id 'BLOCKED') }
    if ($isError -or $r.Code -ne 0) { return (Complete-Task $M $statePath $id (Get-ErrorCode ($text + "`n" + $r.Err))) }
    Complete-Task $M $statePath $id 'NO_REPORT'
}

# Прогін, перерваний вимкненням чи зупинкою задачі: живий claude без нагляду зупиняється, диспетчерові — INTERRUPTED.
function Resume-Interrupted {
    foreach ($f in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.txt' -File -ErrorAction SilentlyContinue)) {
        $text = [System.IO.File]::ReadAllText($f.FullName, $script:Utf8)
        if ($text -notmatch '^STARTED ([0-9]{8}-[0-9]{6}-[0-9a-f]{12}) (\{.*\})\s*$') { continue }
        $id = $Matches[1]
        $j = $null; try { $j = $Matches[2] | ConvertFrom-Json } catch { }
        $marker = ''
        if ($null -ne $j -and $null -ne $j.PSObject.Properties['marker']) { $marker = [string]$j.marker }
        try {
            $p = Get-Process -Id ([int]$j.pid) -ErrorAction Stop
            if ((Get-UtcStamp $p.StartTime) -eq [string]$j.start) { Stop-Tree $p; Write-RunLog "перерваний $id : claude $($j.pid) зупинено" }
        } catch { }
        $res = Join-Path (Join-Path (Join-Path $WorkDir 'runs') $id) 'result.json'
        $slug = $(if ($marker -match '^gemini-queue/([^/]+)/') { $Matches[1] } else { '' })
        if ($slug -cmatch $script:SlugPattern) { [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$slug INTERRUPTED") }
        else { Write-RunLog "перерваний $id : позначка невідома" }
        if (-not (Test-Path -LiteralPath $res)) { Write-FileAtomic $res (([ordered]@{ marker = $marker; code = 'INTERRUPTED'; end = (Get-Date).ToString('s') }) | ConvertTo-Json -Compress) }
        Write-FileAtomic $f.FullName "DONE $id INTERRUPTED"
    }
}

# --- вимкнення ----------------------------------------------------------------------------------------------------

# Рушій Gemini зайнятий: задача gemini-run виконується; стан задачі власникові не видно — за узятою позначкою в
# heartbeat (gemini_run.ps1 пише її на старті наряду й прибирає наприкінці).
function Test-GeminiBusy {
    $st = @(Get-TaskRows | Where-Object { $_.Name -eq 'gemini-run' } | ForEach-Object { $_.State })
    if ($st.Count -gt 0 -and $st[0] -ne '?') { return ($st[0] -eq 'Running') }
    [bool](Read-GeminiBeat).Marker
}

function Invoke-Off($M) {
    $statePath = Get-StatePath "$($M.Ref) $($M.Sha)"
    $main = Get-RefSha 'refs/remotes/origin/main'
    if (-not $main -or (Invoke-Git @('merge-base', '--is-ancestor', $M.Sha, $main) -AllowFail).Code -ne 0) {
        [void](Add-Line "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/$($M.Slug) NOT_ON_MAIN")
        Write-FileAtomic $statePath 'DONE NOT_ON_MAIN'
        return
    }
    if (Test-GeminiBusy) {
        # Стану не пишемо: наступний прохід спробує знову.
        $script:Phase = 'вимкнення чекає gemini-run'
        Write-RunLog "позначка $($M.Name): gemini-run зайнятий — вимкнення чекає"
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
        try { if (([System.IO.File]::ReadAllText($sent, $script:Utf8) | ConvertFrom-Json).sent) { break } } catch { }
        Start-Sleep -Seconds 10
    }
    Write-RunLog "позначка $($M.Name): вимикаю"
    Invoke-Shutdown
}

# --- вхід ---------------------------------------------------------------------------------------------------------

function Main {
    foreach ($d in @($WorkDir, (Join-Path $WorkDir 'state'), (Join-Path $WorkDir 'runs'), $OutboxDir)) {
        [void](New-Item -ItemType Directory -Force -Path $d)
    }
    if (-not (Test-OwnerUser)) { Write-RunLog "запуск під $GeminiUser — відмова"; return 1 }
    $script:NoHooks = Join-Path ([System.IO.Path]::GetTempPath()) ('no-hooks-' + [guid]::NewGuid().ToString('N'))
    $lockFile = $null
    try { $lockFile = [System.IO.File]::Open((Join-Path $WorkDir 'lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { return 0 }
    try {
        $origin = (Invoke-Git @('remote', 'get-url', 'origin')).Out.Trim()
        if (($origin.TrimEnd('/') -replace '\.git$', '') -ne ($RepoUrl.TrimEnd('/') -replace '\.git$', '')) {
            $script:Phase = 'origin клону не той'
            Write-RunLog "origin клону ($origin) не $RepoUrl — нарядів нема"
            Update-Status -Force
            return 1
        }
        $bootFile = Join-Path $WorkDir 'boot.txt'
        $boot = Get-BootStamp
        $prev = $(if (Test-Path -LiteralPath $bootFile) { [System.IO.File]::ReadAllText($bootFile, $script:Utf8).Trim() } else { '' })
        $script:FreshBoot = ($boot -ne $prev)
        Resume-Interrupted
        $script:Phase = 'чекає позначки'
        [void](Invoke-Git @('fetch', '-q', '--prune', '--no-tags', 'origin',
                '+refs/heads/main:refs/remotes/origin/main',
                '+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*') -TimeoutMinutes 15)
        $m = Get-NextMarker
        Write-FileAtomic $bootFile $boot
        Update-Status -Force
        if ($null -ne $m) {
            if ($m.Off) { Invoke-Off $m }
            else {
                try {
                    [void](New-Item -ItemType Directory -Force -Path (Join-Path $WorkDir 'runs'))
                    Invoke-Task $m
                } finally { $script:Current = $null; $script:Phase = 'чекає позначки' }
            }
            Update-Status -Force
        }
        0
    } catch {
        Write-RunLog "збій обгортки: $($_.Exception.Message)"
        $script:Phase = 'збій'
        Update-Status -Force
        1
    } finally {
        $lockFile.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Main) }
