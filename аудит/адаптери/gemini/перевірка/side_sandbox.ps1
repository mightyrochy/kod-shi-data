# Спільне для стендів side.ps1, side_claude.ps1, side_watch.ps1: ізоляція від живого стану ноутбука.
# Вада 13.11 (05:25Z): стенд без -OutDir/-RunsDir/-RepoDir лишав їх справжніми й записав живим нарядам INTERRUPTED,
# узяв справжню позначку черги. Тепер непереданий шлях веде в Temp, а шлях у живий стан — відмова стенда.
# Той самий розрив у виконуваних: без -GhExe/-ClaudeExe/-AgyExe/-CodexExe обгортка бере справжні gh, claude, agy, codex
# (коментар у #1690, хід Codex з акаунта власника). Непередане тепер веде до заглушки-відмови, а передане справжнє —
# до відмови стенда: кожен сценарій передає свою заглушку.

# Параметр виконуваного -> команда, яку обгортка знайшла б у PATH. Git тут нема: він іде на локальний origin, а справжній
# RepoUrl стенд і так відхиляє.
$script:SideExeParams = @{ GhExe = 'gh'; ClaudeExe = 'claude'; AgyExe = 'agy'; CodexExe = 'codex' }

# Заглушка-відмова: друкує «СТЕНД: справжній <exe> заборонено» і виходить з кодом 3. Обгортка бачить виконуваний, що
# збоїть, — той самий шлях, що за справжнього збою gh чи Codex, — а не відсутній.
function New-SideDenyExe([string]$Dir, [string]$Name) {
    [void][System.IO.Directory]::CreateDirectory($Dir)
    $bom = New-Object System.Text.UTF8Encoding($true)
    $plain = New-Object System.Text.UTF8Encoding($false)
    if ($env:OS -eq 'Windows_NT') {
        # Кирилицю друкує .ps1 з BOM: .cmd читається в OEM-кодуванні й не зберіг би її.
        $deny = @'
try { [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false) } catch { $null = $_ }
[Console]::Error.WriteLine("СТЕНД: справжній $($args[0]) заборонено — передай заглушку сценарію")
exit 3
'@
        [System.IO.File]::WriteAllText((Join-Path $Dir 'deny.ps1'), ($deny -replace "`r?`n", "`r`n"), $bom)
        $ps = (Get-Process -Id $PID).Path
        $cmd = "@echo off`n`"$ps`" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"%~dp0deny.ps1`" $Name`nexit /b %ERRORLEVEL%`n"
        $path = Join-Path $Dir ($Name + '.cmd')
        [System.IO.File]::WriteAllText($path, ($cmd -replace "`n", "`r`n"), $plain)
        return $path
    }
    $path = Join-Path $Dir $Name
    $sh = @'
#!/bin/sh
printf '%s\n' 'СТЕНД: справжній @NAME@ заборонено — передай заглушку сценарію' >&2
exit 3
'@
    [System.IO.File]::WriteAllText($path, (($sh -replace '@NAME@', $Name) + "`n"), $plain)
    & chmod +x $path
    $path
}

# Параметри, що без підстановки вказують на живий стан, — для кожного скрипта лише ті, що в нього є.
# OutboxDir gemini_publish.ps1 тут нема: порожній, він виводиться з WorkDir у Main, і сценарії спираються на це.
# Виконувані, яких сценарій не передав, — заглушка-відмова в окремій ASCII-теці (.cmd кирилиці в шляху не читає).
function Set-SideSandbox([string]$Script, [hashtable]$P) {
    $names = @(switch ((Split-Path -Leaf $Script)) {
            'gemini_run.ps1' { 'RepoDir'; 'RunsDir'; 'OutDir' }
            'claude_run.ps1' { 'WorkDir'; 'RepoDir'; 'OutboxDir'; 'PublishDir'; 'GeminiOutDir' }
            'gemini_publish.ps1' { 'WorkDir'; 'OutDir' }
            'gemini_watch.ps1' { 'WorkDir'; 'OutDir' }
        })
    $root = Join-Path ([System.IO.Path]::GetTempPath()) ('stend-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    $params = (Get-Command $Script).Parameters
    foreach ($n in $names) {
        if ($params.ContainsKey($n) -and -not $P.ContainsKey($n)) { $P[$n] = Join-Path $root $n.ToLowerInvariant() }
    }
    $denyDir = Join-Path ([System.IO.Path]::GetTempPath()) ('stend-exe-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
    foreach ($n in $script:SideExeParams.Keys) {
        if ($params.ContainsKey($n) -and -not $P.ContainsKey($n)) { $P[$n] = New-SideDenyExe $denyDir $script:SideExeParams[$n] }
    }
}

# Нормалізований шлях без розширення виконуваного: npm-обгортки codex і claude лежать поруч у виглядах .cmd, .ps1 і без розширення.
function Get-SideExeKey([string]$Path) {
    (ConvertTo-SidePath $Path) -replace '\.(exe|cmd|bat|com|ps1)$', ''
}

# Справжній виконуваний: голе ім'я команди (обгортка знайде її в PATH) або шлях, що збігається з тим, що PATH дає для цієї команди.
function Test-SideRealExe([string]$Command, [string]$Value) {
    if (-not $Value) { return $false }
    $real = @(Get-Command $Command -All -CommandType Application -ErrorAction SilentlyContinue | ForEach-Object { Get-SideExeKey $_.Source })
    if ($Value -match '[\\/]' -or (Test-Path -LiteralPath $Value -PathType Leaf)) { return ($real -contains (Get-SideExeKey $Value)) }
    if ([System.IO.Path]::GetFileNameWithoutExtension($Value) -ieq $Command) { return $true }
    foreach ($h in @(Get-Command $Value -All -CommandType Application -ErrorAction SilentlyContinue)) { if ($real -contains (Get-SideExeKey $h.Source)) { return $true } }
    $false
}

function ConvertTo-SidePath([string]$Path) {
    if (-not $Path) { return '' }
    $s = $Path -replace '/', '\'
    if ($env:OS -eq 'Windows_NT') { try { $s = [System.IO.Path]::GetFullPath($s) } catch { $null = $_ <# лишаємо як є #> } }
    $s.TrimEnd('\').ToLowerInvariant()
}

# Після підвантаження скрипта (змінні параметрів уже в області стенда), до Main: відмова, якщо хоч один шлях веде в живий
# стан — теки черги, запусків, вихідних і публікатора, спільну теку, теку самооновлення чи справжній клон — або RepoUrl
# справжній (fetch узяв би справжні refs/remotes/origin/gemini-queue/*, публікатор запушив би) або GhExe/ClaudeExe/AgyExe/CodexExe
# веде до справжньої команди з PATH.
function Assert-SideIsolated {
    $live = @('C:\Users\Public\gemini', 'C:\ProgramData\gemini-wrapper', 'C:\Users\gemini')
    $clones = @('C:\Users\gemini\kod-shi-data')
    if ($env:USERPROFILE) {
        foreach ($d in @('gemini-runs', 'claude-run', 'gemini-outbox', 'gemini-publish', 'gemini-watch')) { $live += (Join-Path $env:USERPROFILE $d) }
        $clones += (Join-Path $env:USERPROFILE 'kod-shi-data')
    }
    $live = @($live | ForEach-Object { ConvertTo-SidePath $_ })
    $clones = @($clones | ForEach-Object { ConvertTo-SidePath $_ })
    $bad = New-Object System.Collections.ArrayList
    foreach ($n in @('RepoDir', 'RunsDir', 'OutDir', 'WorkDir', 'OutboxDir', 'PublishDir', 'GeminiOutDir', 'GeminiStateDir', 'GeminiRunsDir', 'LaneDir', 'UpdateRoot')) {
        $v = Get-Variable -Name $n -ValueOnly -ErrorAction SilentlyContinue
        $full = ConvertTo-SidePath ([string]$v)
        if (-not $full) { continue }
        foreach ($r in $live) { if ($full -eq $r -or $full.StartsWith($r + '\')) { [void]$bad.Add("-$n $v (живий стан $r)"); break } }
        if ($n -eq 'RepoDir' -and $clones -contains $full) { [void]$bad.Add("-$n $v (справжній клон)") }
    }
    foreach ($n in $script:SideExeParams.Keys) {
        $v = [string](Get-Variable -Name $n -ValueOnly -ErrorAction SilentlyContinue)
        if (Test-SideRealExe $script:SideExeParams[$n] $v) { [void]$bad.Add("-$n $v (справжній $($script:SideExeParams[$n]))") }
    }
    $url = [string](Get-Variable -Name 'RepoUrl' -ValueOnly -ErrorAction SilentlyContinue)
    if ($url -match '(?i)github\.com[/:]mightyrochy/kod-shi-data(\.git)?/?$') { [void]$bad.Add("-RepoUrl $url (справжній репозиторій)") }
    if ($bad.Count) { throw ('відмова: стенд не працює над живим станом ноутбука — ' + ($bad -join '; ') + '. Передай тимчасові теки, RepoUrl локального origin і заглушки виконуваних (-GhExe, -ClaudeExe, -AgyExe, -CodexExe).') }
}
