#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('zhyvyi-ryadok-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    <# Незалежні правила виконуються до кінця й при відсутній функції базової версії. #>
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir,"$WorkDir/state","$WorkDir/seen",$OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $config = [pscustomobject]@{codex='gpt-review';agy='gemini-review';claude='cc-claude-review'}
    $sha = 'a' * 40
    $registryText = [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf)
    $registry = Get-LiveSceneRegistry $registryText
    Scenario '1 реєстр' {
        Check '1 реєстр читається, режим сцени ж7_прогулянка_субота — функція' ($registry.Count -gt 50 -and $registry['ж7_прогулянка_субота'] -cmatch '^функція')
        Check '1 перше поле — голий id, коментарі не id' (-not ($registry.Keys -ccontains '#') -and ($registry.Keys -ccontains 'ж1_оціни_образ_6б'))
    }
    Scenario '2 розбір рядка' {
        function Parse([string]$Text) { @(Get-LiveAfterLines $Text $registry) }
        $ok = Parse 'ЖИВИЙ ПІСЛЯ: ж2_побачення_вечір — чи зник хибний ліміт → повне → main → ремонтів менше'
        Check '2 повний рядок розібрано: id і питання' ($ok.Count -eq 1 -and -not $ok[0].error -and $ok[0].id -ceq 'ж2_побачення_вечір' -and $ok[0].question.StartsWith('чи зник'))
        $series = Parse 'ЖИВИЙ ПІСЛЯ: серія 2 `б1_доречність` — у картці, бібліотеці'
        Check '2 «серія 2 `id`» — вада: id не голий' ($series.Count -eq 1 -and $series[0].error -match 'не голий')
        $paren = Parse 'ЖИВИЙ ПІСЛЯ: ж1_оціни_образ_6б (стенд: сцени 6 і 6б) → повне +фото → main → краще'
        Check '2 id із дужками без « — » — вада' ($paren.Count -eq 1 -and $paren[0].error -match 'нема « — »')
        $quoted = Parse 'ЖИВИЙ ПІСЛЯ: `ж3_співбесіда` — питання'
        Check '2 id із зворотними лапками — вада' ($quoted.Count -eq 1 -and $quoted[0].error -match 'не голий')
        $unknown = Parse 'ЖИВИЙ ПІСЛЯ: ж9_нема_такої — питання'
        Check '2 id поза реєстром — вада' ($unknown.Count -eq 1 -and $unknown[0].error -match 'нема першим полем')
        $case = Parse 'ЖИВИЙ ПІСЛЯ: Ж3_співбесіда — питання'
        Check '2 id порівнюється з урахуванням регістру' ($case.Count -eq 1 -and [bool]$case[0].error)
        $empty = Parse 'ЖИВИЙ ПІСЛЯ: ж3_співбесіда — '
        Check '2 порожнє питання — вада' ($empty.Count -eq 1 -and [bool]$empty[0].error)
        $heading = Parse "## ЖИВИЙ ПІСЛЯ`nпроза під заголовком"
        Check '2 заголовок «ЖИВИЙ ПІСЛЯ» без рядка — вада' ($heading.Count -eq 1 -and [bool]$heading[0].error)
        $list = Parse '- ЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання'
        Check '2 рядок у списку — вада, не мовчки пропущений' ($list.Count -eq 1 -and $list[0].error -match 'маркера списку')
        $indent = Parse "   ЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання`r"
        Check '2 пробіли й CR обрізано, рядок розібрано' ($indent.Count -eq 1 -and -not $indent[0].error)
        $deep = Parse "Опис`n`nТекст про ЖИВИЙ ПІСЛЯ у середині рядка`nЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання"
        Check '2 згадка в середині рядка не рядок; рядок будь-де в тілі знайдено' ($deep.Count -eq 1 -and -not $deep[0].error)
        Check '2 тіло без рядка — нічого' ((Parse 'Звичайний опис PR').Count -eq 0 -and (Parse '').Count -eq 0)
        $inject = Parse 'ЖИВИЙ ПІСЛЯ: ж3_співбесіда — $(Remove-Item -Recurse /); `rm -rf /` "x"'
        Check '2 чужий текст — лише дані: питання збережено дослівно' ($inject.Count -eq 1 -and -not $inject[0].error -and $inject[0].question.Contains('$(Remove-Item'))
    }
    Scenario '3 мірило: тіла #2551, #2557, #2559 до і після правки диспетчера' {
        $before = @{
            2551 = "Що змінено`n`nЖИВИЙ ПІСЛЯ: серія 2 ``б1_доречність`` — у картці, бібліотеці, підписі локального фото та стані"
            2557 = "ЖИВИЙ ПІСЛЯ: ж1_оціни_образ_6б (стенд: сцени 6 і 6б) → кнопка «Оновити «…»» і підпис крамниці"
            2559 = "## ЖИВИЙ ПІСЛЯ`n`nСерія 2 ``б1_доречність``, зокрема шість проблемних запитів, і свіжа сцена"
        }
        foreach ($n in 2551,2557,2559) {
            $items = @(Get-LiveAfterLines $before[$n] $registry)
            Check "3 ДО: тіло #$n — рядок вадний з причиною" ($items.Count -ge 1 -and @($items | Where-Object { $_.error }).Count -eq $items.Count)
        }
        $after = @{
            2551 = "ЖИВИЙ ПІСЛЯ: ж1_оціни_образ_6б — підпис крамниці → повне +фото → main → підпис без дубля`nЖИВИЙ ПІСЛЯ: ж2_побачення_вечір — стан картки → повне → main → без хибного ліміту"
            2557 = "ЖИВИЙ ПІСЛЯ: ж3_співбесіда — тон запрошення → повне → main → без «стиліст»`nЖИВИЙ ПІСЛЯ: ж3_свято_др — кольорові образи → повне → main → кольорових більше"
            2559 = "ЖИВИЙ ПІСЛЯ: ж7_прогулянка_субота — функція без моделі → функція → main → працює у Chromium"
        }
        foreach ($n in 2551,2557,2559) {
            $items = @(Get-LiveAfterLines $after[$n] $registry)
            Check "3 ПІСЛЯ: тіло #$n — усі рядки розібрано" ($items.Count -ge 1 -and @($items | Where-Object { $_.error }).Count -eq 0)
        }
        $planRepo = Join-Path $tmp 'plan'
        [void][IO.Directory]::CreateDirectory("$planRepo/аудит/проби")
        & git -C $planRepo init -q -b main
        & git -C $planRepo config user.name 'Стенд'; & git -C $planRepo config user.email 'stand@local'
        $script:RepoDir = $planRepo; $script:Repo = $planRepo
        [IO.File]::WriteAllText("$planRepo/аудит/проби/живі_сцени.txt", $registryText, $utf)
        function Plan-Commit([string]$Date, [string]$Name) {
            $author = $env:GIT_AUTHOR_DATE; $committer = $env:GIT_COMMITTER_DATE
            try {
                $env:GIT_AUTHOR_DATE = $Date; $env:GIT_COMMITTER_DATE = $Date
                & git -C $planRepo add -A
                & git -C $planRepo commit -q --allow-empty -m $Name
                if ($LASTEXITCODE) { throw 'Не створено коміт плану' }
                (& git -C $planRepo rev-parse HEAD).Trim()
            } finally { $env:GIT_AUTHOR_DATE = $author; $env:GIT_COMMITTER_DATE = $committer }
        }
        $base = Plan-Commit '2026-01-01T00:00:00Z' 'Реєстр'
        $merged = Plan-Commit '2026-01-02T00:00:00Z' 'Злиті PR'
        $head = Plan-Commit '2026-01-03T00:00:00Z' 'Збірка'
        $script:Bodies = $before
        function Get-AutoPublicItems {
            @(2551,2557,2559 | ForEach-Object {
                [pscustomobject]@{number=$_;user=@{login='mightyrochy'};head=@{ref='claude/код';repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}};merge_commit_sha=$merged;merged_at='2026-01-02T00:00:00Z';created_at='2026-01-02T00:00:00Z';body=$script:Bodies[$_]}
            })
        }
        $plan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '3 ДО: у плані сцен 0, вадних 3 з номером PR і причиною' (@($plan.scenes.PSObject.Properties).Count -eq 0 -and @($plan.bad).Count -ge 3 -and (@($plan.bad.pr | Sort-Object -Unique) -join ',') -eq '2551,2557,2559' -and -not @($plan.bad | Where-Object { -not $_.reason }))
        Check '3 ДО: вадний план не порожній — прогін не закрито EMPTY_PLAN' (-not (Test-AutoPlanEmpty ('автоживий-' + $head) ("наряд`nПЛАН ЖИВОГО — ДАНІ (JSON):`n" + (Get-AutoLivePlan $head) + "`n")))
        $script:Bodies = $after
        $plan = ConvertFrom-Json (Get-AutoLivePlan $head)
        $laptop = @($plan.scenes.PSObject.Properties.Name | Sort-Object) -join ','
        $expected = (@('ж1_оціни_образ_6б','ж2_побачення_вечір','ж3_співбесіда','ж3_свято_др') | Sort-Object) -join ','
        Check '3 ПІСЛЯ: на ноутбук ж1_оціни_образ_6б, ж2_побачення_вечір, ж3_співбесіда, ж3_свято_др' ($laptop -ceq $expected)
        Check '3 ПІСЛЯ: ж7_прогулянка_субота — «у хмарі» з PR і питанням' (@($plan.cloud.PSObject.Properties.Name) -ceq 'ж7_прогулянка_субота' -and $plan.cloud.ж7_прогулянка_субота[0].pr -eq 2559 -and [bool]$plan.cloud.ж7_прогулянка_субота[0].question)
        Check '3 ПІСЛЯ: вадних 0, функція не потрапила в сцени ноутбука' (@($plan.bad).Count -eq 0 -and -not ($plan.scenes.PSObject.Properties.Name -ccontains 'ж7_прогулянка_субота'))
        $script:Bodies = @{2551='Звичайний опис';2557='';2559='ЖИВИЙ ПІСЛЯ: ж7_прогулянка_субота — лише функція → функція → main → працює'}
        $planText = "наряд`nПЛАН ЖИВОГО — ДАНІ (JSON):`n" + (Get-AutoLivePlan $head) + "`n"
        Check '3 лише хмарна сцена: план не порожній, звіт має її назвати' (-not (Test-AutoPlanEmpty ('автоживий-' + $head) $planText))
        $script:Bodies = @{2551='Звичайний опис';2557='';2559=''}
        $emptyText = "наряд`nПЛАН ЖИВОГО — ДАНІ (JSON):`n" + (Get-AutoLivePlan $head) + "`n"
        Check '3 без рядків план порожній, як і раніше' (Test-AutoPlanEmpty ('автоживий-' + $head) $emptyText)
    }
    Scenario '4 шаблон і CI' {
        $template = [IO.File]::ReadAllText((Join-Path $SourceDir '../../наряди/автоживий.md'), $utf)
        Check '4 шаблон велить ЗАБЛОКОВАНО диспетчерові за вадним рядком і називає сцени «у хмарі»' ($template.Contains('"bad"') -and $template.Contains('ЗАБЛОКОВАНО') -and $template.Contains('"cloud"') -and $template.Contains('у хмарі'))
        $workflow = [IO.File]::ReadAllText((Join-Path $SourceDir '../../../.github/workflows/zhyvyi-ryadok.yml'), $utf)
        Check '4 CI читає тіло PR з події через змінну середовища, не підстановкою в команду' ($workflow.Contains('PR_BODY: ${{ github.event.pull_request.body }}') -and -not ($workflow -match 'run:[^\n]*\$\{\{ *github\.event\.pull_request\.body'))
        Check '4 CI на opened, synchronize, edited, ready_for_review до main' ($workflow -match 'types: \[opened, synchronize, edited, ready_for_review\]' -and $workflow.Contains('branches: [main]'))
    }
} finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^zhyvyi-ryadok-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($bad) { exit 1 }
