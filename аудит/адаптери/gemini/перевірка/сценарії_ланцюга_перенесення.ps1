#Requires -Version 5.1
<# Стенд наряду «Обгортка-автоживий-обрив-не-губить», ціль 2: поки прогін активного штампу не дав звіту чи відмови,
наступний штамп не публікується — зокрема коли позначку перенесено між рушіями чи смугами. 17.11 о 18:39Z диспетчер
зняв `автоживий-04911e68` зі смуги claude і поставив на `gpt-6.1-sol-high`; кінець старої позначки (CANCELLED) ланцюг
узяв за кінець прогону, і о 18:43Z поставив `автоживий-49b680c2`, хоч 04911e68 ішов. Справжні функції ланцюга й
публікатора на тимчасовому origin; підмінено лише API GitHub і готовність моделей. #>
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ('e0-chain-move-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmpRoot)
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Один результат стенда, без прихованих відмов. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:failures++ }
}
try {
    $seed = Join-Path $tmpRoot 'seed'; $remote = Join-Path $tmpRoot 'origin.git'
    & git init -q --bare $remote; & git init -q -b main $seed
    & git -C $seed config user.name 'стенд'; & git -C $seed config user.email 'stend@example.invalid'
    & git -C $seed remote add origin $remote
    foreach ($dir in @('аудит/наряди','аудит/адаптери/gemini','джерела')) { [void][IO.Directory]::CreateDirectory((Join-Path $seed $dir)) }
    Copy-Item -LiteralPath (Join-Path $SourceDir 'ланцюг.json') -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
    foreach ($task in @('автоперевірка','автоживий')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md", $task, $utf) }
    [IO.File]::WriteAllText("$seed/джерела/a.py", '1', $utf)
    & git -C $seed add -A; & git -C $seed commit -q -m 'початкова'; & git -C $seed push -q origin main
    $bare = Join-Path $tmpRoot 'repo.git'; & git clone -q --bare $remote $bare
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmpRoot/pub" -OutDir "$tmpRoot/gem-out" -OutboxDir "$tmpRoot/out" -UpdateRoot "$tmpRoot/update"
    [void][IO.Directory]::CreateDirectory("$OutDir/marker-state")
    Write-FileAtomic "$OutDir/marker-state/ready" '1'
    $GeminiRunsDir = "$tmpRoot/gemini-runs"
    foreach ($d in @($WorkDir, (Join-Path $WorkDir 'seen'), (Join-Path $WorkDir 'state'), $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
    $script:Repo = $bare; $script:NoHooks = Join-Path $tmpRoot 'no-hooks'
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    $script:Pulls = @(); $script:Ready = $false
    function Get-ChainPulls { $script:Pulls }
    function Invoke-ChainApi([string]$Path) {
        if ($Path -match '/files\?') { return [pscustomobject]@{filename='джерела/a.py'} }
        $sha = ($Path -split '/')[-1]
        [pscustomobject]@{sha=$sha;commit=@{committer=@{date=[datetimeoffset]::UtcNow.AddMinutes(-1).ToString('o')}}}
    }
    function Test-LiveModels($Config) { $script:Ready }
    function Markers([string]$Stamp) { @(& git -C $remote for-each-ref '--format=%(refname:short)' "refs/heads/gemini-queue/автоживий-$Stamp/") }
    function Merge([string]$Path, [string]$Text) {
        <# Злитий стан main і наступний справжній fetch публікатора. #>
        [IO.File]::WriteAllText((Join-Path $seed $Path), $Text, $utf)
        & git -C $seed add -A; & git -C $seed commit -q -m 'злиття'; & git -C $seed push -q origin main
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        Get-RefSha 'refs/remotes/origin/main'
    }
    function Tick {
        <# Прохід публікатора: fetch черги, потім ланцюг. #>
        [void](Invoke-Git @('fetch','-q','--prune','--no-tags','origin','+refs/heads/main:refs/remotes/origin/main','+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
        Invoke-WrapperChain
    }
    function Finish([string]$Ref, [string]$Line) {
        <# Смуга закрила позначку: прийнятий рядок обгортки зі `slug` у стані публікатора і зняття позначки з origin. #>
        $slug = ($Ref -split '/')[1]
        [IO.File]::WriteAllText("$WorkDir/state/$([guid]::NewGuid().ToString('N')).json", ((@{line=$Line; slug=$slug}) | ConvertTo-Json -Compress), $utf)
        & git -C $remote update-ref -d "refs/heads/$Ref"
    }
    Invoke-WrapperChain
    $stamp1 = Merge 'джерела/a.py' '2'; $build1 = Merge 'build.txt' $stamp1
    $script:Ready = $true; Tick
    $first = @(Markers $stamp1)
    Check '1 збірка 1 отримала одну позначку автоживого' ($first.Count -eq 1)
    # Перенесення диспетчером: позначка того самого штампу на іншому рушії, стара — «ЗНЯТО», смуга закрила її CANCELLED.
    $moved = "gemini-queue/автоживий-$stamp1/gpt-6.1-sol-medium/1/p2-gpu"
    & git -C $seed push -q origin "${build1}:refs/heads/$moved"
    Finish $first[0] "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/автоживий-$stamp1 CANCELLED"
    $stamp2 = Merge 'джерела/a.py' '3'; $build2 = Merge 'build.txt' $stamp2
    Tick
    $second = @(Markers $stamp2).Count
    "ДАНІ перенесення: нових позначок автоживий-* після перенесення активного — $second (ДО правки — 1)"
    Check '2 перенесена позначка активного штампу — нових позначок автоживий-* 0' ($second -eq 0)
    Tick
    Check '2 повторний прохід теж не публікує наступного штампу' (@(Markers $stamp2).Count -eq 0)
    # Знята «ЗНЯТО» позначка, якої смуга ще не закрила, роботи штампу не тримає.
    $stamp3 = Merge 'джерела/a.py' '4'; $build3 = Merge 'build.txt' $stamp3
    Finish $moved "GEMINI ОБГОРТКА: ГОТОВО gemini/автоживий-$stamp1 $build1 МОДЕЛЬ gpt-6.1-sol-medium"
    Tick
    $after = @(@(Markers $stamp2) + @(Markers $stamp3))
    Check '3 після кінця перенесеної — одна позначка останнього штампу' ($after.Count -eq 1 -and @(Markers $stamp3).Count -eq 1)
    # Нова позначка того самого штампу після кінця (повтор диспетчера) — теж робота штампу; «ЗНЯТО» на ній — ні.
    $active = @(Markers $stamp3)[0]
    Finish $active "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/автоживий-$stamp3 NO_REPORT"
    $retry = "gemini-queue/автоживий-$stamp3/gpt-6.1-sol-medium/2/p2-gpu"
    & git -C $seed push -q origin "${build3}:refs/heads/$retry"
    $stamp4 = Merge 'джерела/a.py' '5'; $build4 = Merge 'build.txt' $stamp4
    Tick
    Check '4 повтор того самого штампу в черзі — наступний штамп чекає' (@(Markers $stamp4).Count -eq 0)
    & git -C $seed checkout -q --detach $build3
    & git -C $seed commit -q --allow-empty -m 'ЗНЯТО: повтор не потрібен'
    & git -C $seed push -q -f origin "HEAD:refs/heads/$retry"
    & git -C $seed checkout -q main
    Tick
    Check '4 повтор знято «ЗНЯТО» — наступний штамп отримав одну позначку' (@(Markers $stamp4).Count -eq 1)
} catch {
    Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false
} finally {
    if ((Split-Path -Leaf $tmpRoot) -cmatch '^e0-chain-move-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
"провалів: $failures"
if ($failures) { exit 1 }
