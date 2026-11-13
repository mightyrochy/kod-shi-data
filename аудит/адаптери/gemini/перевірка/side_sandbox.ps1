# Спільне для стендів side.ps1, side_claude.ps1, side_watch.ps1: ізоляція від живого стану ноутбука.
# Вада 13.11 (05:25Z): стенд без -OutDir/-RunsDir/-RepoDir лишав їх справжніми й записав живим нарядам INTERRUPTED,
# узяв справжню позначку черги. Тепер непереданий шлях веде в Temp, а шлях у живий стан — відмова стенда.

# Параметри, що без підстановки вказують на живий стан, — для кожного скрипта лише ті, що в нього є.
# OutboxDir gemini_publish.ps1 тут нема: порожній, він виводиться з WorkDir у Main, і сценарії спираються на це.
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
}

function ConvertTo-SidePath([string]$Path) {
    if (-not $Path) { return '' }
    $s = $Path -replace '/', '\'
    if ($env:OS -eq 'Windows_NT') { try { $s = [System.IO.Path]::GetFullPath($s) } catch { $null = $_ <# лишаємо як є #> } }
    $s.TrimEnd('\').ToLowerInvariant()
}

# Після підвантаження скрипта (змінні параметрів уже в області стенда), до Main: відмова, якщо хоч один шлях веде в живий
# стан — теки черги, запусків, вихідних і публікатора, спільну теку, теку самооновлення чи справжній клон — або RepoUrl
# справжній (fetch узяв би справжні refs/remotes/origin/gemini-queue/*, публікатор запушив би).
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
    $url = [string](Get-Variable -Name 'RepoUrl' -ValueOnly -ErrorAction SilentlyContinue)
    if ($url -match '(?i)github\.com[/:]mightyrochy/kod-shi-data(\.git)?/?$') { [void]$bad.Add("-RepoUrl $url (справжній репозиторій)") }
    if ($bad.Count) { throw ('відмова: стенд не працює над живим станом ноутбука — ' + ($bad -join '; ') + '. Передай тимчасові теки й RepoUrl локального origin.') }
}
