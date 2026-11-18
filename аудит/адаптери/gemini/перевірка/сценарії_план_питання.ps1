#Requires -Version 5.1
<# Стенд наряду «План-автоживого-питання-має-відповідь» (18.11): справжній `Get-AutoLivePlan` обгортки на шести злитих
PR, хмарній теці запису й оцінках у дереві збірки; мережа GitHub (`Get-AutoPublicItems`) — підміною. Мірила: питання, на
яке сцена механічно не може відповісти (replay, PORTRET без входу, збирання в режимі «розмова»), — у `bad` з причиною й
сценою, сцена заради нього не записується (ДО — сцена в плані); запис, який оцінка дала «не виміряно», не прогнаний:
той самий текст — у `bad` з причиною оцінки, виправлений рядок і «не виміряно (обрив)» — у плані (ДО — пару лічено
прогнаною); межа перевіреної збірки (`ПЕРЕВІРЕНО ЗБІРКУ`) не покриває пари, яку оцінка теки того звіту дала «не
виміряно» (ДО — губилась); повтор відсіяного планом-джерелом не новий (`unfit_new`), і план лише з ним порожній (`Test-AutoPlanEmpty`). #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('plan-pytannia-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
$script:Logged = New-Object System.Collections.ArrayList
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Write-Log([string]$Text) {
    <# queue_lanes.ps1 вимагає від хазяїна функцію журналу; рядки журналу стенд звіряє. #>
    [void]$script:Logged.Add($Text)
    Write-Host "  журнал обгортки: $Text"
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $LaneDir = Join-Path $tmp 'lanes'; [void][IO.Directory]::CreateDirectory($LaneDir)
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $repo = Join-Path $tmp 'repo'
    & git init -q -b main $repo
    & git -C $repo config user.name 'Стенд'; & git -C $repo config user.email 'stand@local'; & git -C $repo config core.autocrlf false
    $script:RepoDir = $repo; $script:Repo = $repo; $script:NoHooks = Join-Path $tmp 'no-hooks'
    [void][IO.Directory]::CreateDirectory("$repo/аудит/проби")
    [void][IO.Directory]::CreateDirectory("$repo/аудит/перевірки")
    [IO.File]::WriteAllText("$repo/аудит/проби/живі_сцени.txt", [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf), $utf)
    function Repo-Commit([string]$Date, [string]$Name) {
        $author = $env:GIT_AUTHOR_DATE; $committer = $env:GIT_COMMITTER_DATE
        try {
            $env:GIT_AUTHOR_DATE = $Date; $env:GIT_COMMITTER_DATE = $Date
            & git -C $repo add -A
            & git -C $repo commit -q --allow-empty -m $Name
            if ($LASTEXITCODE) { throw 'Не створено коміт' }
            (& git -C $repo rev-parse HEAD).Trim()
        } finally { $env:GIT_AUTHOR_DATE = $author; $env:GIT_COMMITTER_DATE = $committer }
    }
    $null = Repo-Commit '2026-11-01T00:00:00Z' 'Реєстр'
    # Реєстр: ж1_робота й ж2_побачення_вечір — «повне», ж2_похорон — «розмова», ж3_свято_др — «повне»; входу (PORTRET=…) нема ні в кого.
    $questions = @{
        101 = @('ж1_робота', 'питання 101')
        102 = @('ж2_побачення_вечір', 'питання 102')
        103 = @('ж2_похорон', 'чи збирання дає три образи')
        104 = @('ж3_свято_др', 'питання 104')
        105 = @('ж3_свято_др', 'replay запису дає той самий кадр')
        106 = @('ж1_робота', 'чи PORTRET змінює колір образу')
    }
    $merges = @{}
    $script:Merged = @()
    function Pull([int]$Number, [string]$Body, [string]$Date, [string]$Merge, [string]$Ref) {
        [pscustomobject]@{number = $Number; user = @{login = 'mightyrochy'}; head = @{ref = $Ref; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merge_commit_sha = $Merge; merged_at = $Date; created_at = $Date; updated_at = $Date
            body = $Body}
    }
    foreach ($n in 101..106) {
        $date = '2026-11-01T0' + ($n - 100) + ':00:00Z'
        $merges[$n] = Repo-Commit $date "Злиття $n"
        $script:Merged += @(Pull $n "ЖИВИЙ ПІСЛЯ: $($questions[$n][0]) — $($questions[$n][1])" $date $merges[$n] "claude/код-$n")
    }
    $build = $merges[106]
    # Хмарний прогін записав ж1_робота (PR 101) і ж2_побачення_вечір (PR 102) на коді збірки.
    $cloudName = 'Тестовий-прогін-хмара-стенд'
    $cloudDir = "$repo/аудит/проби/$cloudName"
    $planScenes = @{}
    foreach ($n in @(101, 102)) {
        $record = "$cloudDir/$($questions[$n][0])"
        foreach ($sub in @('знімки', 'VIDPOVIDI/обмін')) { [void][IO.Directory]::CreateDirectory("$record/$sub") }
        [IO.File]::WriteAllText("$record/результат.json", ('{"rc": 0, "sha": "' + $build + '"}'), $utf)
        foreach ($file in @('повтор.json', 'лог.txt', 'знімки/доказ.json', 'VIDPOVIDI/обмін/1.json')) { [IO.File]::WriteAllText("$record/$file", '{}', $utf) }
        $planScenes[$questions[$n][0]] = @(@{pr = $n; question = $questions[$n][1]})
    }
    [IO.File]::WriteAllText("$cloudDir/ПЛАН.json", (ConvertTo-Json -Compress -Depth 5 @{build = $build; scenes = $planScenes}), $utf)
    [IO.File]::WriteAllText("$cloudDir/done.txt", (@($planScenes.Keys | ForEach-Object { '{"сцена": "' + $_ + '", "rc": 0, "секунд": 300}' }) -join "`n") + "`n", $utf)
    $treeNoEval = Repo-Commit '2026-11-02T00:00:00Z' 'Хмарний прогін'
    # Оцінка того прогону: PR 101 — «не виміряно» (відповіді нема), PR 102 — «не виміряно (обрив)».
    $evalPath = 'аудит/перевірки/Оцінка-стенд.md'
    [IO.File]::WriteAllText("$repo/$evalPath", ("# Оцінка прогону ``аудит/проби/$cloudName```n`n| сцена | PR | відповідь | чому |`n|---|---|---|---|`n" +
        "| ж1_робота | #101 | не виміряно | сцена не дійшла до вибору |`n| ж2_побачення_вечір | #102 | не виміряно (обрив) | стенд обірвався |`n"), $utf)
    $tree = Repo-Commit '2026-11-03T00:00:00Z' 'Оцінка'
    function Get-Plan([string]$Main) { ConvertFrom-Json (Get-AutoLivePlan $Main) }
    function Scene-Names($Plan) { @($Plan.scenes.PSObject.Properties | ForEach-Object { $_.Name }) }
    function Bad-Of($Plan, [int]$Number) { @($Plan.bad | Where-Object { $null -ne $_ -and [int]$_.pr -eq $Number }) }
    $script:PlanPulls = @($script:Merged)
    function Get-AutoPublicItems { $script:PlanPulls }

    Scenario '1 питання без відповіді — до прогону' {
        $script:Logged.Clear()
        $plan = Get-Plan $tree
        $names = @(Scene-Names $plan)
        "ДАНІ сцени: $($names -join ', '); bad: " + (@($plan.bad | ForEach-Object { "#$($_.pr) $($_.scene) — $($_.reason)" }) -join ' | ')
        foreach ($n in @(103, 105, 106)) {
            $entry = @(Bad-Of $plan $n)
            Check "1 #$n ($($questions[$n][1])) — у bad зі сценою й причиною «не для живого прогону»" ($entry.Count -eq 1 -and [string]$entry[0].scene -ceq $questions[$n][0] -and
                [string]$entry[0].reason -cmatch '^не для живого прогону: ' -and [string]$entry[0].line -ceq "ЖИВИЙ ПІСЛЯ: $($questions[$n][0]) — $($questions[$n][1])")
        }
        Check '1 причина replay, PORTRET і збирання — своя' ([string](Bad-Of $plan 105)[0].reason -cmatch 'replay' -and [string](Bad-Of $plan 106)[0].reason -cmatch 'PORTRET' -and
            [string](Bad-Of $plan 103)[0].reason -cmatch 'збирання')
        Check '1 сцени лише відсіяних питань (ж2_похорон) у плані нема (ДО — була)' ('ж2_похорон' -cnotin $names)
        Check '1 сцена з іншим придатним питанням лишається з ним одним (ж3_свято_др: #104)' ('ж3_свято_др' -cin $names -and
            @($plan.scenes.'ж3_свято_др').Count -eq 1 -and [int]@($plan.scenes.'ж3_свято_др')[0].pr -eq 104)
        $line = @($script:Logged | Where-Object { $_ -cmatch '^план живого: ' })
        Check '1 журнал обгортки — один рядок із відсіяним і причинами' ($line.Count -eq 1 -and $line[0] -cmatch 'відсіяно до прогону 4 \(нових 4\)' -and
            $line[0] -cmatch '#105 ж3_свято_др — не для живого прогону: ')
        Check '1 unfit_new — усе відсіяне нове (4)' ([int]$plan.unfit_new -eq 4)
    }
    Scenario '2 «не виміряно» не прогнано' {
        $before = Get-Plan $treeNoEval
        $beforeNames = @(Scene-Names $before)
        Check '2 без оцінки записи 101 і 102 лічено прогнаними (ДО)' ('ж2_побачення_вечір' -cnotin $beforeNames -and @(Bad-Of $before 101).Count -eq 0 -and
            'ж1_робота' -cnotin $beforeNames)
        $plan = Get-Plan $tree
        $names = @(Scene-Names $plan)
        $entry = @(Bad-Of $plan 101)
        Check '2 той самий текст після «не виміряно» — у bad з місцем і причиною оцінки, сцени в плані нема' ($entry.Count -eq 1 -and [string]$entry[0].scene -ceq 'ж1_робота' -and
            [string]$entry[0].reason -ceq "не виміряно в оцінці ${evalPath}:5: сцена не дійшла до вибору" -and 'ж1_робота' -cnotin $names)
        Check '2 «не виміряно (обрив)» — питання знову в плані' ('ж2_побачення_вечір' -cin $names -and @(Bad-Of $plan 102).Count -eq 0 -and
            [string]@($plan.scenes.'ж2_побачення_вечір')[0].question -ceq 'питання 102')
        $fixed = @($script:Merged | ForEach-Object { if ($_.number -eq 101) { Pull 101 'ЖИВИЙ ПІСЛЯ: ж1_робота — питання 101 з виправленим рядком' $_.merged_at $_.merge_commit_sha $_.head.ref } else { $_ } })
        $script:PlanPulls = $fixed
        try { $changed = Get-Plan $tree } finally { $script:PlanPulls = @($script:Merged) }
        Check '2 виправлений рядок (інший текст) — у плані, не в bad' ('ж1_робота' -cin @(Scene-Names $changed) -and @(Bad-Of $changed 101).Count -eq 0 -and
            [string]@($changed.scenes.'ж1_робота')[0].question -ceq 'питання 101 з виправленим рядком')
    }
    Scenario '3 відповідь в іншій оцінці' {
        [IO.File]::WriteAllText("$repo/аудит/перевірки/Оцінка-стенд-друга.md", ("Переоцінка запису ``$cloudName``.`n`n| сцена | PR | вердикт |`n|---|---|---|`n| ж1_робота | 101 | так |`n"), $utf)
        $answered = Repo-Commit '2026-11-04T00:00:00Z' 'Друга оцінка'
        $plan = Get-Plan $answered
        Check '3 пара з відповіддю в іншій оцінці тієї теки — прогнана: ні в плані, ні в bad' ('ж1_робота' -cnotin @(Scene-Names $plan) -and @(Bad-Of $plan 101).Count -eq 0 -and
            [int]$plan.ran.$cloudName -eq 1)
        & git -C $repo rm -q -- 'аудит/перевірки/Оцінка-стенд-друга.md'
        $null = Repo-Commit '2026-11-04T01:00:00Z' 'Без другої оцінки'
    }
    Scenario '4 повтор відсіяного не новий' {
        $first = Get-AutoLivePlan $tree
        $dir = "аудит/проби/автоживий-$tree"
        [void][IO.Directory]::CreateDirectory("$repo/$dir")
        [IO.File]::WriteAllText("$repo/$dir/ПЛАН.json", $first, $utf)
        $reportHead = Repo-Commit '2026-11-05T00:00:00Z' 'Звіт автоживого'
        $report = [pscustomobject]@{number = 110; user = @{login = 'mightyrochy'}; head = @{ref = "claude/автоживий-$tree"; sha = $reportHead; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merge_commit_sha = $null; merged_at = $null
            created_at = '2026-11-05T00:00:00Z'; updated_at = '2026-11-05T00:00:00Z'; body = ''}
        $carry = Read-AutoCarryPlan $report @{$tree = 0} @{}
        Check '4 план-джерело пам''ятає відсіяне «PR|сцена|рядок»' ($null -ne $carry -and $carry.unfit.Count -eq 4 -and
            $carry.unfit.Contains('105|ж3_свято_др|ЖИВИЙ ПІСЛЯ: ж3_свято_др — replay запису дає той самий кадр'))
        $script:PlanPulls = @($report) + @($script:Merged)
        try { $plan = Get-Plan $reportHead } finally { $script:PlanPulls = @($script:Merged) }
        "ДАНІ повтор: bad $(@($plan.bad).Count), unfit_new $($plan.unfit_new)"
        Check '4 те саме відсіяне з планом-джерелом — у bad, але не нове (unfit_new 0)' (@($plan.bad | Where-Object { $null -ne $_.PSObject.Properties['scene'] }).Count -eq 4 -and [int]$plan.unfit_new -eq 0)
    }
    Scenario '6 межа перевіреної збірки й «не виміряно»' {
        # Звіт автоживого перевірив збірку $build (`ПЕРЕВІРЕНО ЗБІРКУ`) і записав ж1_робота (PR 101) та ж3_свято_др (PR 104).
        $dirName = "автоживий-$build"
        $scenesRun = @{}
        foreach ($n in @(101, 104)) {
            $record = "$repo/аудит/проби/$dirName/$($questions[$n][0])"
            foreach ($sub in @('знімки', 'VIDPOVIDI/обмін')) { [void][IO.Directory]::CreateDirectory("$record/$sub") }
            [IO.File]::WriteAllText("$record/результат.json", ('{"rc": 0, "sha": "' + $build + '"}'), $utf)
            foreach ($file in @('повтор.json', 'лог.txt', 'знімки/доказ.json', 'VIDPOVIDI/обмін/1.json')) { [IO.File]::WriteAllText("$record/$file", '{}', $utf) }
            $scenesRun[$questions[$n][0]] = @(@{pr = $n; question = $questions[$n][1]})
        }
        [IO.File]::WriteAllText("$repo/аудит/проби/$dirName/ПЛАН.json", (ConvertTo-Json -Compress -Depth 5 @{build = $build; scenes = $scenesRun}), $utf)
        [IO.File]::WriteAllText("$repo/аудит/проби/$dirName/done.txt", (@($scenesRun.Keys | ForEach-Object { '{"сцена": "' + $_ + '", "rc": 0, "секунд": 300}' }) -join "`n") + "`n", $utf)
        $reportHead = Repo-Commit '2026-11-06T00:00:00Z' 'Звіт межі'
        $report = [pscustomobject]@{number = 120; user = @{login = 'mightyrochy'}; head = @{ref = "claude/$dirName"; sha = $reportHead; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merge_commit_sha = $null; merged_at = $null
            created_at = '2026-11-06T00:00:00Z'; updated_at = '2026-11-06T00:00:00Z'; body = "Звіт`n`nПЕРЕВІРЕНО ЗБІРКУ: $build`n"}
        $script:PlanPulls = @($report) + @($script:Merged)
        try {
            $before = Get-Plan $reportHead
            Check '6 без оцінки теки звіту межа покриває всі PR до збірки: ні сцен, ні bad' (@(Scene-Names $before).Count -eq 0 -and @($before.bad | Where-Object { $null -ne $_ }).Count -eq 0)
            $boundEval = 'аудит/перевірки/Оцінка-межа.md'
            [IO.File]::WriteAllText("$repo/$boundEval", ("# Оцінка прогону ``аудит/проби/$dirName```n`n| сцена | PR | відповідь | чому |`n|---|---|---|---|`n" +
                "| ж1_робота | #101 | не виміряно | модель не дійшла до вибору |`n| ж3_свято_др | #104 | так | видно |`n"), $utf)
            $evalHead = Repo-Commit '2026-11-07T00:00:00Z' 'Оцінка звіту межі'
            $plan = Get-Plan $evalHead
            $entry = @(Bad-Of $plan 101)
            "ДАНІ межа: сцени $(@(Scene-Names $plan) -join ', '); bad: " + (@($plan.bad | Where-Object { $null -ne $_ } | ForEach-Object { "#$($_.pr) $($_.scene) — $($_.reason)" }) -join ' | ')
            Check '6 пара під межею, яку оцінка теки звіту дала «не виміряно», — у bad з причиною оцінки (ДО — губилась)' ($entry.Count -eq 1 -and
                [string]$entry[0].scene -ceq 'ж1_робота' -and [string]$entry[0].reason -cmatch '^не виміряно в оцінці ')
            Check '6 інші пари під межею лишаються покритими: ні сцен, ні іншого bad' (@(Scene-Names $plan).Count -eq 0 -and
                @($plan.bad | Where-Object { $null -ne $_ }).Count -eq 1)
        } finally { $script:PlanPulls = @($script:Merged) }
    }
    Scenario '5 порожній план' {
        $slug = 'автоживий-' + ('a' * 40)
        $line = 'ЖИВИЙ ПІСЛЯ: ж3_свято_др — replay запису дає той самий кадр'
        function Plan-Text([int]$New, [bool]$WithScene) {
            $entry = [ordered]@{pr = 105; line = $line; reason = 'не для живого прогону: replay'}
            if ($WithScene) { $entry.scene = 'ж3_свято_др' }
            "Наряд`nПЛАН ЖИВОГО — ДАНІ (JSON):`n" + (ConvertTo-Json -Compress -Depth 6 ([ordered]@{scenes = @{}; cloud = @{}; bad = @($entry); unfit_new = $New})) + "`n"
        }
        Check '5 лише повтор відсіяного (unfit_new 0) — план порожній' (Test-AutoPlanEmpty $slug (Plan-Text 0 $true))
        Check '5 нове відсіяне (unfit_new 1) — план не порожній: звіт назве його' (-not (Test-AutoPlanEmpty $slug (Plan-Text 1 $true)))
        Check '5 нерозібраний рядок (bad без сцени) — план не порожній' (-not (Test-AutoPlanEmpty $slug (Plan-Text 0 $false)))
    }
} finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^plan-pytannia-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($bad) { exit 1 }
