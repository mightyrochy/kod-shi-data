#Requires -Version 5.1
<# Стенд черги автоживого: у черзі (жде чи йде) не більше одного автоживого; наступний стає, коли попередній дав
відповідь чи названо причину обриву, і бере найсвіжішу збірку; той, що ще жде, свіжіша збірка заміняє комітом «ЗНЯТО»
(менеджер 20.11). Перенесення між рушіями чи смугами — не кінець: 17.11 о 18:39Z диспетчер зняв `автоживий-04911e68` зі
смуги claude і поставив на `gpt-6.1-sol-high`; кінець старої позначки (CANCELLED) ланцюг узяв за кінець прогону, і о 18:43Z
поставив `автоживий-49b680c2`, хоч 04911e68 ішов. 20.11: `автоживий-8e821357` ждав 09:40–13:31, поки злили дві свіжіші
збірки. Справжні функції ланцюга й публікатора на тимчасовому origin; підмінено лише API GitHub і готовність моделей. #>
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
    <# Базовий конфіг стенду — без codex_pause_until: справжнє значення в main не має міняти порядок моделей у сценаріях. #>
    [IO.File]::WriteAllText("$seed/аудит/адаптери/gemini/ланцюг.json", ([IO.File]::ReadAllText((Join-Path $SourceDir 'ланцюг.json'), $utf) -replace '(?m)^[ 	]*"codex_pause_until"[ 	]*:[^
]*
?
', ''), $utf)
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
    function Take([string]$Ref) {
        <# Смуга взяла позначку (файл `.claim` під ключем стану, як у Get-MarkerState): прогін іде. #>
        $sha = (& git -C $remote rev-parse "refs/heads/$Ref").Trim()
        [IO.File]::WriteAllText("$OutDir/marker-state/$(Get-Sha256Hex "refs/remotes/origin/$Ref $sha").claim", 'стенд', $utf)
    }
    function Subject([string]$Ref) { (& git -C $remote log -1 --format=%s "refs/heads/$Ref").Trim() }
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
    # (а) Прогін іде (позначку взято): свіжіша збірка другої позначки не дістає й першої не знімає.
    Take $first[0]
    $stamp2 = Merge 'джерела/a.py' '3'; $build2 = Merge 'build.txt' $stamp2
    Tick
    "ДАНІ (а): позначок автоживий-<збірка 2>, поки йде збірка 1 — $(@(Markers $stamp2).Count); голова збірки 1 — $(Subject $first[0])"
    Check '(а) другий автоживий не ставиться, поки перший іде, і той, що йде, не знято' (@(Markers $stamp2).Count -eq 0 -and (Subject $first[0]) -cnotmatch '^ЗНЯТО')
    # Перенесення диспетчером: позначка того самого штампу на іншому рушії (смуга її взяла), стара — CANCELLED.
    $moved = "gemini-queue/автоживий-$stamp1/gpt-6.1-sol-medium/1/p2-gpu"
    & git -C $seed push -q origin "${build1}:refs/heads/$moved"
    Take $moved
    Finish $first[0] "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/автоживий-$stamp1 CANCELLED"
    Tick
    $second = @(Markers $stamp2).Count
    "ДАНІ перенесення: нових позначок автоживий-* після перенесення активного — $second (ДО правки — 1)"
    Check '2 перенесена позначка активного штампу — нових позначок автоживий-* 0' ($second -eq 0)
    Tick
    Check '2 повторний прохід теж не публікує наступного штампу' (@(Markers $stamp2).Count -eq 0)
    # (б, в) Кінець із відповіддю — наступний стає на найсвіжішій збірці; проміжна збірка 2 позначки не дістає.
    $stamp3 = Merge 'джерела/a.py' '4'; $build3 = Merge 'build.txt' $stamp3
    Finish $moved "GEMINI ОБГОРТКА: ГОТОВО gemini/автоживий-$stamp1 $build1 МОДЕЛЬ gpt-6.1-sol-medium"
    Tick
    $after = @(@(Markers $stamp2) + @(Markers $stamp3))
    Check '(б, в) після кінця з відповіддю — одна позначка, на найсвіжішій збірці' ($after.Count -eq 1 -and @(Markers $stamp3).Count -eq 1 -and (& git -C $remote rev-parse "refs/heads/$(@(Markers $stamp3)[0])").Trim() -ceq $build3)
    # (г) Автоживий, що ще жде (не взятий), свіжіша збірка заміняє: «ЗНЯТО» поверх його позначки, нова — на свіжішій збірці.
    $waiting = @(Markers $stamp3)[0]
    $stamp4 = Merge 'джерела/a.py' '5'; $build4 = Merge 'build.txt' $stamp4
    Tick
    $cut = (& git -C $remote rev-parse "refs/heads/$waiting").Trim()
    "ДАНІ (г): голова позначки збірки 3 — «$(Subject $waiting)»; позначок збірки 4 — $(@(Markers $stamp4).Count)"
    Check '(г) автоживий, що жде, знято комітом ЗНЯТО поверх його позначки (гілку не видалено)' ((Subject $waiting) -cmatch '^ЗНЯТО' -and (& git -C $remote rev-parse "$cut^").Trim() -ceq $build3)
    Check '(г) замість нього — одна позначка на свіжішій збірці' (@(Markers $stamp4).Count -eq 1 -and (& git -C $remote rev-parse "refs/heads/$(@(Markers $stamp4)[0])").Trim() -ceq $build4)
    Tick
    Check '(г) повторний прохід не знімає вдруге й не дублює' ((& git -C $remote rev-parse "refs/heads/$waiting").Trim() -ceq $cut -and @(Markers $stamp4).Count -eq 1)
    Check '(г) зняття видно в журналі публікатора' (([IO.File]::ReadAllText((Join-Path $WorkDir 'publish.log'), $utf)).Contains("знято комітом ЗНЯТО — не стартував, чергу бере свіжіша збірка $stamp4"))
    Finish $waiting "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/автоживий-$stamp3 CANCELLED"
    # Без готових моделей автоживий, що жде, не знімається: черга не лишається порожньою.
    $active = @(Markers $stamp4)[0]
    $script:Ready = $false
    $stamp5 = Merge 'джерела/a.py' '6'; $build5 = Merge 'build.txt' $stamp5
    Tick
    Check '(г) моделі не готові — автоживий, що жде, лишається, нового нема' ((Subject $active) -cnotmatch '^ЗНЯТО' -and @(Markers $stamp5).Count -eq 0)
    $script:Ready = $true
    # Повтор того самого штампу, що йде, — теж робота штампу; «ЗНЯТО» на ньому — ні.
    Take $active
    Tick
    Check '4 узятий автоживий свіжіша збірка не знімає' ((Subject $active) -cnotmatch '^ЗНЯТО' -and @(Markers $stamp5).Count -eq 0)
    Finish $active "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/автоживий-$stamp4 NO_REPORT"
    $retry = "gemini-queue/автоживий-$stamp4/gpt-6.1-sol-medium/2/p2-gpu"
    & git -C $seed push -q origin "${build4}:refs/heads/$retry"
    Take $retry
    Tick
    Check '4 повтор того самого штампу йде — наступний штамп чекає' (@(Markers $stamp5).Count -eq 0)
    & git -C $seed checkout -q --detach $build4
    & git -C $seed commit -q --allow-empty -m 'ЗНЯТО: повтор не потрібен'
    & git -C $seed push -q -f origin "HEAD:refs/heads/$retry"
    & git -C $seed checkout -q main
    Tick
    Check '4 повтор знято «ЗНЯТО» — наступний штамп отримав одну позначку' (@(Markers $stamp5).Count -eq 1)
} catch {
    Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false
} finally {
    if ((Split-Path -Leaf $tmpRoot) -cmatch '^e0-chain-move-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
"провалів: $failures"
if ($failures) { exit 1 }
