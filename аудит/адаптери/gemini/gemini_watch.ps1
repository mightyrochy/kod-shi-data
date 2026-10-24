#Requires -Version 5.1
<#
.SYNOPSIS
Спостерігач (наряд М.9, частина Б): опитує `gh` і кладе в теку вихідних рядки диспетчерові; без моделі.

.DESCRIPTION
Задача планувальника під власником, раз на хвилину; один прохід за запуск. Що робить:
  1. Коментарі #963 і PR нарядів Codex (`codex/*`, автор mightyrochy): лише від `mightyrochy` і
     `chatgpt-codex-connector[bot]`; новий id -> «новий», той самий id з іншим `updated_at` -> «змінено».
  2. Стан CI голів відкритих PR від `mightyrochy`: рядок лише на зміну, `pending` у теку не йде (лише в стан).
  3. Перенос diff: відповідь бота з блоком ```diff -> чистий worktree від голови `codex/<наряд>` -> `git apply --check`
     -> коміт -> пуш лише в `refs/heads/codex/<наряд>` (fast-forward) -> рядок «ПЕРЕНЕСЕНО»; не лягло — рядок із кодом.
Перший прохід лише запам'ятовує наявне (без рядків). У тека вихідних іде тільки рядок, що повністю збігся з шаблоном:
номери, SHA, id, коди й імена гілок, перевірені за SlugPattern; тексту коментаря чи PR там нема.
Інтерфейс з обгорткою доставки — лише тека вихідних: один файл — один рядок, UTF-8 без BOM, `<yyyyMMdd-HHmmss>-<12 hex>.txt`,
пишеться через тимчасовий файл і перейменування. Налаштування — `СПОСТЕРІГАЧ.md` поруч.
#>
[CmdletBinding()]
param(
    [string]$WorkDir = (Join-Path $env:USERPROFILE 'gemini-watch'),
    [string]$OutDir = (Join-Path $env:USERPROFILE 'gemini-outbox'),
    [string]$Repo = 'mightyrochy/kod-shi-data',
    [string]$RepoUrl = 'https://github.com/mightyrochy/kod-shi-data.git',
    [int]$CommentIssue = 963,
    [string]$GhExe = 'gh',
    [string]$GitExe = 'git',
    [string]$GeminiUser = 'gemini',
    [int]$MaxRows = 20,
    [int]$MaxDiffKB = 128,
    [int]$MaxPushTries = 3,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}$'
$script:Owner = 'mightyrochy'
$script:Bot = 'chatgpt-codex-connector[bot]'
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -ne 'Core') -or [bool](Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)
$script:Rows = 0

# Шаблони рядків (узгоджені з обгорткою доставки): рядок, що не збігся з жодним, у теку не потрапляє.
$sl = '[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}'
$script:LineTemplates = @(
    '^СПОСТЕРІГАЧ КОМЕНТАР #[0-9]+ [0-9]+ (mightyrochy|chatgpt-codex-connector\[bot\]) (новий|змінено)\z',
    '^СПОСТЕРІГАЧ CI #[0-9]+ [0-9a-f]{40} (success|failure|cancelled|timed_out|action_required|neutral|skipped|pending)\z',
    "^СПОСТЕРІГАЧ ПЕРЕНЕСЕНО $sl codex/$sl [0-9a-f]{40} #[0-9]+\z",
    "^СПОСТЕРІГАЧ НЕ ПЕРЕНЕСЕНО $sl [A-Z0-9_]{2,40}\z"
)

function Write-WatchLog([string]$Text) {
    $path = Join-Path $WorkDir 'watch.log'
    if ((Test-Path -LiteralPath $path) -and (Get-Item -LiteralPath $path).Length -gt 1MB) {
        Move-Item -LiteralPath $path -Destination ($path + '.old') -Force
    }
    $line = '{0:yyyy-MM-dd HH:mm:ss} {1}' -f (Get-Date), $Text
    [System.IO.File]::AppendAllText($path, $line + "`n", $script:Utf8)
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

function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDirectory = '', [double]$TimeoutMinutes = 5, [string]$StdIn = $null) {
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = ConvertTo-ArgString $Arguments
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.StandardOutputEncoding = $script:Utf8
    $psi.StandardErrorEncoding = $script:Utf8
    if ($WorkDirectory) { $psi.WorkingDirectory = $WorkDirectory }
    $psi.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $psi.EnvironmentVariables['GCM_INTERACTIVE'] = 'never'
    $psi.RedirectStandardInput = ($null -ne $StdIn)
    $p = [System.Diagnostics.Process]::Start($psi)
    $out = $p.StandardOutput.ReadToEndAsync()
    $err = $p.StandardError.ReadToEndAsync()
    if ($null -ne $StdIn) {
        $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $script:Utf8)
        $w.Write($StdIn)
        $w.Close()
    }
    if (-not $p.WaitForExit([int]($TimeoutMinutes * 60000))) {
        if ($script:OnWindows) { & taskkill.exe /PID $p.Id /T /F *> $null } else { $p.Kill($true) }
        [void]$p.WaitForExit(15000)
        return [pscustomobject]@{ Code = -1; Out = ''; Err = 'межа часу' }
    }
    $p.WaitForExit()
    [pscustomobject]@{ Code = $p.ExitCode; Out = $out.Result; Err = $err.Result }
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

function Test-OwnerUser {
    if (-not $script:OnWindows) { return $true }
    $name = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    ($name -split '\\')[-1] -ne $GeminiUser
}

function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
    $all = @('--git-dir', $script:GitDir, '-c', "core.hooksPath=$script:NoHooks", '-c', 'core.quotepath=false') + $GitArgs
    $r = Invoke-Native $GitExe $all $WorkDir
    if ($r.Code -ne 0 -and -not $AllowFail) { throw "git $($GitArgs -join ' ') -> $($r.Code): $($r.Err.Trim())" }
    $r
}

function Get-RefSha([string]$Ref) {
    $r = Invoke-Git @('rev-parse', '-q', '--verify', "$Ref^{commit}") -AllowFail
    if ($r.Code -ne 0) { return '' }
    $r.Out.Trim()
}

function Get-Prop($Obj, [string]$Name) {
    if ($null -eq $Obj) { return $null }
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p) { return $null }
    $p.Value
}

# JSON-дати PowerShell 7 перетворює на DateTime: до одного вигляду, щоб порівняння не залежало від версії.
function Get-Stamp($v) {
    if ($v -is [datetime]) { return $v.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
    [string]$v
}

function Invoke-Gh([string]$Path) {
    $r = Invoke-Native (Resolve-Exe $GhExe) @('api', '-H', 'Accept: application/vnd.github+json', $Path) $WorkDir 3
    if ($r.Code -ne 0) { throw "gh api $Path -> $($r.Code): $($r.Err.Trim())" }
    $r.Out | ConvertFrom-Json
}

# Сторінки по 100, поки не прийде неповна; лише масиви.
function Get-GhList([string]$Path, [string]$Query = '') {
    $all = @()
    for ($page = 1; $page -le 50; $page++) {
        $sep = $(if ($Path.Contains('?')) { '&' } else { '?' })
        $chunk = @(Invoke-Gh ("$Path${sep}per_page=100&page=$page$Query"))
        $all += $chunk
        if ($chunk.Count -lt 100) { break }
    }
    $all
}

# ---- тека вихідних ----

function Add-Line([string]$Line) {
    $ok = $false
    foreach ($t in $script:LineTemplates) { if ($Line -cmatch $t) { $ok = $true; break } }
    if ($ok -and $Line -cmatch '(?:codex/|НЕ ПЕРЕНЕСЕНО |ПЕРЕНЕСЕНО )' -and $Line.Contains('..')) { $ok = $false }
    if (-not $ok) { Write-WatchLog "рядок не за шаблоном — не записано: $Line"; return $false }
    if ($DryRun) { Write-WatchLog "DryRun: $Line"; $script:Rows++; return $true }
    $name = '{0:yyyyMMdd-HHmmss}-{1}.txt' -f (Get-Date), ([guid]::NewGuid().ToString('N').Substring(0, 12))
    Write-FileAtomic (Join-Path $OutDir $name) $Line
    Write-WatchLog "рядок $name : $Line"
    $script:Rows++
    $true
}

# ---- стан: пласка таблиця «ключ -> значення», у JSON ----

function Read-State {
    $st = @{}
    $path = Join-Path $WorkDir 'state.json'
    if (-not (Test-Path -LiteralPath $path)) { return $st }
    try {
        $o = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json
        foreach ($p in $o.PSObject.Properties) { $st[$p.Name] = Get-Stamp $p.Value }
    } catch { Write-WatchLog "state.json не читається, починаю з базової лінії: $($_.Exception.Message)"; return @{} }
    $st
}

function Save-State {
    $o = [ordered]@{}
    foreach ($k in ($script:State.Keys | Sort-Object)) { $o[$k] = $script:State[$k] }
    Write-FileAtomic (Join-Path $WorkDir 'state.json') ($o | ConvertTo-Json -Compress)
}

function Test-Cap { $script:Rows -ge $MaxRows }

# ---- коментарі ----

function Get-LastOwnerBot($Comment) {
    $login = [string](Get-Prop (Get-Prop $Comment 'user') 'login')
    if ($login -ceq $script:Owner) { return $script:Owner }
    if ($login -ceq $script:Bot) { return $script:Bot }
    ''
}

function Get-Diff([string]$Body) {
    $ms = [regex]::Matches($Body, '(?ms)^```diff[ \t]*\r?\n(.*?)^```[ \t]*\r?$')
    if ($ms.Count -eq 0) { return $null }
    $text = (@($ms | ForEach-Object { $_.Groups[1].Value }) -join '')
    $text = $text -replace "`r`n", "`n"
    if (-not $text.EndsWith("`n")) { $text += "`n" }
    $text
}

# Один diff -> гілка. Повертає код причини ('' — перенесено, рядок уже записано), 'RETRY' — спробувати наступного проходу.
function Invoke-Transfer($Pr, [string]$CommentId, [string]$Diff, [int]$Tries) {
    $n = [int]$Pr.Number; $slug = $Pr.Slug; $branch = "codex/$slug"
    $fail = {
        param($code)
        [void](Add-Line "СПОСТЕРІГАЧ НЕ ПЕРЕНЕСЕНО $slug $code")
        $code
    }
    if ($Diff.Contains([string][char]0xFFFD)) { return (& $fail 'FFFD') }
    if ($script:Utf8.GetByteCount($Diff) -gt $MaxDiffKB * 1KB) { return (& $fail 'TOO_BIG') }
    if ($Diff -notmatch '(?m)^diff --git ') { return (& $fail 'NO_DIFF') }
    if ($Diff -match '(?m)^(GIT binary patch|Binary files )') { return (& $fail 'BINARY') }
    if ($Diff -match '(?m)^(new file mode|old mode|new mode|deleted file mode|index [0-9a-f.]+\.\.[0-9a-f.]+) 1[26]0000') { return (& $fail 'SPECIAL_MODE') }
    [void](Invoke-Git @('fetch', '-q', '--no-tags', 'origin', "+refs/heads/${branch}:refs/remotes/origin/$branch"))
    $base = Get-RefSha "refs/remotes/origin/$branch"
    if (-not $base) { return (& $fail 'NO_BRANCH') }
    $wt = Join-Path (Join-Path $WorkDir 'wt') ([guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Force -Path (Split-Path $wt))
    $hasWt = $false
    try {
        [void](Invoke-Git @('worktree', 'add', '-q', '--detach', $wt, $base))
        $hasWt = $true
        $g = @('-c', "core.hooksPath=$script:NoHooks", '-c', 'core.autocrlf=false', '-c', 'core.safecrlf=false')
        $chk = Invoke-Native $GitExe ($g + @('apply', '--check', '--whitespace=nowarn', '-')) $wt 3 $Diff
        if ($chk.Code -ne 0) { Write-WatchLog "apply --check #$n коментар ${CommentId}: $($chk.Err.Trim())"; return (& $fail 'APPLY_FAILED') }
        $ap = Invoke-Native $GitExe ($g + @('apply', '--whitespace=nowarn', '-')) $wt 3 $Diff
        if ($ap.Code -ne 0) { Write-WatchLog "apply #$n коментар ${CommentId}: $($ap.Err.Trim())"; return (& $fail 'APPLY_FAILED') }
        $add = Invoke-Native $GitExe ($g + @('add', '-A')) $wt 3
        if ($add.Code -ne 0) { return (& $fail 'APPLY_FAILED') }
        $names = @((Invoke-Native $GitExe ($g + @('diff', '--cached', '--name-only', '--no-renames', '-z')) $wt 3).Out -split "`0" | Where-Object { $_ })
        if ($names.Count -eq 0) { return (& $fail 'EMPTY') }
        if (@($names | Where-Object { $_ -like '.github/*' -or $_ -like 'аудит/адаптери/*' }).Count -gt 0) { return (& $fail 'FORBIDDEN_PATH') }
        if (@($names | Where-Object { ($_ -split '/') -contains '.git' }).Count -gt 0) { return (& $fail 'FORBIDDEN_PATH') }
        $msg = "Перенос diff Codex з коментаря $CommentId до PR #$n (спостерігач без моделі)"
        $cm = Invoke-Native $GitExe ($g + @('-c', 'user.name=Спостерігач Люстерка', '-c', 'user.email=watcher@users.noreply.github.com',
                '-c', 'commit.gpgsign=false', 'commit', '-q', '--no-verify', '-m', $msg)) $wt 3
        if ($cm.Code -ne 0) { Write-WatchLog "commit #$n : $($cm.Err.Trim())"; return (& $fail 'COMMIT_FAILED') }
        $sha = (Invoke-Native $GitExe ($g + @('rev-parse', 'HEAD')) $wt 1).Out.Trim()
        if ($sha -notmatch '^[0-9a-f]{40}$') { return (& $fail 'COMMIT_FAILED') }
        $dst = "refs/heads/$branch"
        if (-not $dst.StartsWith('refs/heads/codex/')) { throw 'ціль пушу поза codex/*' }
        if ($DryRun) { Write-WatchLog "DryRun: пуш $sha -> $dst не робився"; return '' }
        $push = Invoke-Git @('push', '-q', '--no-verify', 'origin', "${sha}:$dst") -AllowFail
        if ($push.Code -ne 0) {
            Write-WatchLog "пуш $dst -> $($push.Code): $($push.Err.Trim())"
            [void](Invoke-Git @('fetch', '-q', '--no-tags', 'origin', "+refs/heads/${branch}:refs/remotes/origin/$branch") -AllowFail)
            if ((Get-RefSha "refs/remotes/origin/$branch") -ne $base) { return (& $fail 'NOT_FF') }
            if ($Tries + 1 -lt $MaxPushTries) { return 'RETRY' }
            return (& $fail 'PUSH_FAILED')
        }
        [void](Add-Line "СПОСТЕРІГАЧ ПЕРЕНЕСЕНО $slug $branch $sha #$n")
        return ''
    } finally {
        if ($hasWt) { [void](Invoke-Git @('worktree', 'remove', '--force', $wt) -AllowFail) }
        if (Test-Path -LiteralPath $wt) { Remove-Item -LiteralPath $wt -Recurse -Force -ErrorAction SilentlyContinue }
    }
}

# Один джерельний PR/issue: коментарі -> рядки, потім перенос. $Pr — $null для #963.
function Watch-Comments([int]$N, $Pr, [bool]$Baseline, [string]$Since) {
    $q = $(if ($Since) { "&since=$Since" } else { '' })
    $comments = @(Get-GhList "repos/$Repo/issues/$N/comments" $q)
    foreach ($c in $comments) {
        if (Test-Cap) { return $false }
        $who = Get-LastOwnerBot $c
        if (-not $who) { continue }
        $id = [string](Get-Prop $c 'id')
        if ($id -notmatch '^[0-9]{1,20}$') { continue }
        $upd = Get-Stamp (Get-Prop $c 'updated_at')
        $key = "c:${N}:$id"; $prev = $script:State[$key]
        $word = ''
        if ($Baseline) { $script:State[$key] = $upd }
        elseif ($null -eq $prev) { $word = 'новий' }
        elseif ($prev -ne $upd) { $word = 'змінено' }
        if ($word) {
            if (Add-Line "СПОСТЕРІГАЧ КОМЕНТАР #$N $id $who $word") { $script:State[$key] = $upd; Save-State }
        }
        if ($null -eq $Pr -or $who -cne $script:Bot) { continue }
        $xkey = "x:${N}:$id"; $xprev = $script:State[$xkey]
        if ($Baseline) { $script:State[$xkey] = "$upd baseline"; continue }
        $tries = 0
        if ($null -ne $xprev) {
            $parts = $xprev -split ' '
            if ($parts[0] -eq $upd -and $parts[1] -ne 'retry') { continue }
            if ($parts[0] -eq $upd -and $parts[1] -eq 'retry') { $tries = [int]$parts[2] }
        }
        $diff = Get-Diff ([string](Get-Prop $c 'body'))
        if ($null -eq $diff) { $script:State[$xkey] = "$upd nodiff"; continue }
        $res = Invoke-Transfer $Pr $id $diff $tries
        if ($res -eq 'RETRY') { $script:State[$xkey] = "$upd retry $($tries + 1)" } else { $script:State[$xkey] = "$upd done" }
        Save-State
    }
    $true
}

# ---- CI ----

function Get-CiState([string]$Sha) {
    $r = Invoke-Gh "repos/$Repo/commits/$Sha/check-runs?per_page=100"
    $runs = @(Get-Prop $r 'check_runs')
    if ($runs.Count -eq 0) { return 'pending' }
    $concl = @()
    foreach ($run in $runs) {
        if ([string](Get-Prop $run 'status') -ne 'completed') { return 'pending' }
        $concl += [string](Get-Prop $run 'conclusion')
    }
    foreach ($c in @('failure', 'timed_out', 'cancelled', 'action_required', 'success', 'neutral', 'skipped')) {
        if ($concl -contains $c) { return $c }
    }
    'neutral'
}

function Watch-Ci($Prs, [bool]$Baseline) {
    foreach ($pr in $Prs) {
        if (Test-Cap) { return }
        $state = Get-CiState $pr.Sha
        $key = "i:$($pr.Number)"; $prev = $script:State[$key]; $now = "$($pr.Sha) $state"
        if ($Baseline -or $prev -eq $now) { $script:State[$key] = $now; continue }
        if ($state -eq 'pending') { $script:State[$key] = $now; continue }
        if (Add-Line "СПОСТЕРІГАЧ CI #$($pr.Number) $($pr.Sha) $state") { $script:State[$key] = $now; Save-State }
    }
}

function Main {
    foreach ($d in @($WorkDir, $OutDir)) { [void](New-Item -ItemType Directory -Force -Path $d) }
    if (-not (Test-OwnerUser)) { Write-WatchLog "запуск під $GeminiUser — відмова"; return 1 }
    $script:GitDir = Join-Path $WorkDir 'repo.git'
    $script:NoHooks = Join-Path ([System.IO.Path]::GetTempPath()) ('no-hooks-' + [guid]::NewGuid().ToString('N'))
    $lockFile = $null
    try { $lockFile = [System.IO.File]::Open((Join-Path $WorkDir 'lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { return 0 }
    try {
        if (-not (Test-Path -LiteralPath (Join-Path $script:GitDir 'HEAD'))) {
            [void](Invoke-Native $GitExe @('init', '-q', '--bare', $script:GitDir) $WorkDir)
            [void](Invoke-Git @('config', 'remote.origin.url', $RepoUrl))
        }
        $script:State = Read-State
        $baseline = -not $script:State.ContainsKey('_since')
        $passStart = (Get-Date).ToUniversalTime()
        $since = $(if ($baseline) { '' } else { $script:State['_since'] })

        $raw = @(Get-GhList "repos/$Repo/pulls?state=open")
        $ours = @()
        foreach ($p in $raw) {
            if ([string](Get-Prop (Get-Prop $p 'user') 'login') -cne $script:Owner) { continue }
            $head = Get-Prop $p 'head'
            if ([string](Get-Prop (Get-Prop $head 'repo') 'full_name') -cne $Repo) { continue }
            $sha = [string](Get-Prop $head 'sha'); $ref = [string](Get-Prop $head 'ref'); $num = [string](Get-Prop $p 'number')
            if ($sha -notmatch '^[0-9a-f]{40}$' -or $num -notmatch '^[0-9]{1,9}$') { continue }
            $slug = ''
            if ($ref.StartsWith('codex/')) {
                $s = $ref.Substring(6)
                if ($s -cmatch $script:SlugPattern -and $s -notmatch '[\r\n]' -and -not $s.Contains('..')) { $slug = $s }
            }
            $ours += [pscustomobject]@{ Number = [int]$num; Sha = $sha; Slug = $slug }
        }
        # Закриті PR зникають зі стану CI.
        $open = @{}; foreach ($o in $ours) { $open["i:$($o.Number)"] = $true }
        foreach ($k in @($script:State.Keys | Where-Object { $_ -like 'i:*' })) { if (-not $open.ContainsKey($k)) { $script:State.Remove($k) } }

        $complete = Watch-Comments $CommentIssue $null $baseline $since
        foreach ($o in @($ours | Where-Object { $_.Slug })) {
            if (-not $complete) { break }
            $complete = Watch-Comments $o.Number $o $baseline $since
        }
        if ($complete) { Watch-Ci $ours $baseline }

        if ($complete -and -not (Test-Cap)) {
            $script:State['_since'] = $passStart.AddMinutes(-10).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
        }
        Save-State
        0
    } catch {
        Write-WatchLog "збій: $($_.Exception.Message)"
        1
    } finally {
        $lockFile.Dispose()
    }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Main) }
