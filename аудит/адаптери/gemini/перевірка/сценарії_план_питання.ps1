#Requires -Version 5.1
<# Стенд наряду «План-автоживого-питання-має-відповідь» (18.11): справжній `Get-AutoLivePlan` обгортки на шести злитих
PR, хмарній теці запису й оцінках у дереві збірки; мережа GitHub (`Get-AutoPublicItems`) — підміною. Мірила: питання, на
яке сцена механічно не може відповісти (replay, PORTRET без входу, збирання в режимі «розмова»), — у `bad` з причиною й
сценою, сцена заради нього не записується (ДО — сцена в плані); запис, який оцінка дала «не виміряно», не прогнаний:
той самий текст — у `bad` з причиною оцінки, виправлений рядок і «не виміряно (обрив)» — у плані (ДО — пару лічено
прогнаною); межа перевіреної збірки (`ПЕРЕВІРЕНО ЗБІРКУ`) не покриває пари, яку оцінка теки того звіту дала «не
виміряно» (ДО — губилась); повтор відсіяного планом-джерелом не новий (`unfit_new`), і план лише з ним порожній (`Test-AutoPlanEmpty`);
план-джерело притримує (`held`) прогнане записом і покрите межею, що записував прогін звіту межі: оцінку «не виміряно»,
злиту після нього, наступний план застосовує й тоді, коли PR пари поза читанням (ДО — пару губило: її не було ні в `bad`,
ні в `scenes`); план без `held` читається, як і раніше. #>
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
    Scenario '7 план-джерело притримує прогнане й покрите межею' {
        function Held-Pairs($Plan) { @(@($Plan.held.PSObject.Properties) | ForEach-Object { $id = $_.Name; @($_.Value) | ForEach-Object { "$($_.pr)|$id" } }) }
        function Report([int]$Number, [string]$Dir, [string]$Head, [string]$Date, [string]$Body) {
            [pscustomobject]@{number = $Number; user = @{login = 'mightyrochy'}; head = @{ref = "claude/$Dir"; sha = $Head; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
                base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merge_commit_sha = $null; merged_at = $null
                created_at = $Date; updated_at = $Date; body = $Body}
        }
        function Save-Plans([string]$Dir, [string]$Plan, [string]$Date) {
            # Той самий план двічі: без `held` (як складав код до цього поля) і з ним — дві голови звіту.
            $old = ConvertFrom-Json $Plan; $old.PSObject.Properties.Remove('held')
            [void][IO.Directory]::CreateDirectory("$repo/аудит/проби/$Dir")
            [IO.File]::WriteAllText("$repo/аудит/проби/$Dir/ПЛАН.json", (ConvertTo-Json -InputObject $old -Depth 8 -Compress), $utf)
            $oldHead = Repo-Commit $Date 'Звіт: план без held'
            [IO.File]::WriteAllText("$repo/аудит/проби/$Dir/ПЛАН.json", $Plan, $utf)
            @($oldHead, (Repo-Commit $Date 'Звіт: план з held'))
        }
        function Where-Is($Plan, [int]$Number, [string]$Scene) {
            $in = @(@($Plan.scenes.PSObject.Properties) | Where-Object { $_.Name -ceq $Scene } | ForEach-Object { @($_.Value) } | Where-Object { [int]$_.pr -eq $Number })
            $out = @(Bad-Of $Plan $Number | Where-Object { [string]$_.scene -ceq $Scene })
            if ($in.Count) { 'scenes' } elseif ($out.Count) { 'bad: ' + [string]$out[0].reason } else { 'ніде' }
        }
        try {
            # (а) Прогнане записом. План P1 на збірці без оцінки лічить #101 і #102 прогнаними хмарною текою.
            & git -C $repo checkout -q -b plan-held-ran $treeNoEval
            if ($LASTEXITCODE) { throw 'Не створено гілку plan-held-ran' }
            $script:PlanPulls = @($script:Merged)
            $p1Text = Get-AutoLivePlan $treeNoEval
            $p1 = ConvertFrom-Json $p1Text
            Check '7а план P1 притримує прогнане (#101, #102) у held, у scenes і bad їх нема' ((@(Held-Pairs $p1 | Sort-Object) -join ',') -ceq '101|ж1_робота,102|ж2_побачення_вечір' -and
                (Where-Is $p1 101 'ж1_робота') -ceq 'ніде' -and (Where-Is $p1 102 'ж2_побачення_вечір') -ceq 'ніде')
            $dirA = "автоживий-$treeNoEval"
            $heads = Save-Plans $dirA $p1Text '2026-11-08T00:00:00Z'
            # Оцінку хмарної теки злито після плану: #101 — «не виміряно», #102 — «не виміряно (обрив)».
            [IO.File]::WriteAllText("$repo/$evalPath", ("# Оцінка прогону ``аудит/проби/$cloudName```n`n| сцена | PR | відповідь | чому |`n|---|---|---|---|`n" +
                "| ж1_робота | #101 | не виміряно | сцена не дійшла до вибору |`n| ж2_побачення_вечір | #102 | не виміряно (обрив) | стенд обірвався |`n"), $utf)
            $evalA = Repo-Commit '2026-11-09T00:00:00Z' 'Оцінка після плану'
            # Читання дійшло лише до звіту: PR #101–#106 поза межею сторінок, їхні рядки — з плану-джерела.
            $script:PlanPulls = @(Report 130 $dirA $heads[0] '2026-11-08T00:00:00Z' '')
            $before = Get-Plan $evalA
            $script:PlanPulls = @(Report 131 $dirA $heads[1] '2026-11-08T00:00:00Z' '')
            $after = Get-Plan $evalA
            "ДАНІ 7а ДО: #101 — $(Where-Is $before 101 'ж1_робота'); #102 — $(Where-Is $before 102 'ж2_побачення_вечір')"
            "ДАНІ 7а ПІСЛЯ: #101 — $(Where-Is $after 101 'ж1_робота'); #102 — $(Where-Is $after 102 'ж2_побачення_вечір')"
            Check '7а ДО (план без held): пар #101 і #102 нема ні в bad, ні в scenes, решта плану-джерела на місці' ((Where-Is $before 101 'ж1_робота') -ceq 'ніде' -and
                (Where-Is $before 102 'ж2_побачення_вечір') -ceq 'ніде' -and (Where-Is $before 104 'ж3_свято_др') -ceq 'scenes' -and @(Bad-Of $before 105).Count -eq 1)
            Check '7а ПІСЛЯ: «не виміряно» — #101 у bad з причиною оцінки, «обрив» — #102 знову в scenes' ((Where-Is $after 101 'ж1_робота') -ceq
                "bad: не виміряно в оцінці ${evalPath}:5: сцена не дійшла до вибору" -and (Where-Is $after 102 'ж2_побачення_вечір') -ceq 'scenes')

            # (б) Покрите межею. Звіт #140 перевірив збірку $build і записав #101 та #104; його план — ці дві пари.
            & git -C $repo checkout -q -b plan-held-bound $treeNoEval
            if ($LASTEXITCODE) { throw 'Не створено гілку plan-held-bound' }
            $dirB = "автоживий-$build"
            $runScenes = @{}
            foreach ($n in @(101, 104)) {
                $record = "$repo/аудит/проби/$dirB/$($questions[$n][0])"
                foreach ($sub in @('знімки', 'VIDPOVIDI/обмін')) { [void][IO.Directory]::CreateDirectory("$record/$sub") }
                [IO.File]::WriteAllText("$record/результат.json", ('{"rc": 0, "sha": "' + $build + '"}'), $utf)
                foreach ($file in @('повтор.json', 'лог.txt', 'знімки/доказ.json', 'VIDPOVIDI/обмін/1.json')) { [IO.File]::WriteAllText("$record/$file", '{}', $utf) }
                $runScenes[$questions[$n][0]] = @(@{pr = $n; question = $questions[$n][1]})
            }
            [IO.File]::WriteAllText("$repo/аудит/проби/$dirB/ПЛАН.json", (ConvertTo-Json -Compress -Depth 5 @{build = $build; scenes = $runScenes}), $utf)
            [IO.File]::WriteAllText("$repo/аудит/проби/$dirB/done.txt", (@($runScenes.Keys | ForEach-Object { '{"сцена": "' + $_ + '", "rc": 0, "секунд": 300}' }) -join "`n") + "`n", $utf)
            $head140 = Repo-Commit '2026-11-08T00:00:00Z' 'Звіт межі #140'
            $report140 = Report 140 $dirB $head140 '2026-11-08T00:00:00Z' "Звіт`n`nПЕРЕВІРЕНО ЗБІРКУ: $build`n"
            $script:PlanPulls = @($report140) + @($script:Merged)
            $paText = Get-AutoLivePlan $head140
            $pa = ConvertFrom-Json $paText
            Check '7б план під межею притримує лише пари прогону звіту межі (#101, #104), не #102' ((@(Held-Pairs $pa | Sort-Object) -join ',') -ceq '101|ж1_робота,104|ж3_свято_др' -and
                @(Scene-Names $pa).Count -eq 0)
            $dirC = "автоживий-$head140"
            $heads = Save-Plans $dirC $paText '2026-11-09T00:00:00Z'
            $boundEval = 'аудит/перевірки/Оцінка-межа-план.md'
            [IO.File]::WriteAllText("$repo/$boundEval", ("# Оцінка прогону ``аудит/проби/$dirB```n`n| сцена | PR | відповідь | чому |`n|---|---|---|---|`n" +
                "| ж3_свято_др | #104 | не виміряно | модель не дійшла до вибору |`n"), $utf)
            $evalB = Repo-Commit '2026-11-10T00:00:00Z' 'Оцінка звіту межі після плану'
            # Читання дійшло лише до звіту #150: звіт межі #140 — з reports плану-джерела, PR #101–#106 — поза читанням.
            $script:PlanPulls = @(Report 150 $dirC $heads[0] '2026-11-09T00:00:00Z' '')
            $before = Get-Plan $evalB
            $script:PlanPulls = @(Report 151 $dirC $heads[1] '2026-11-09T00:00:00Z' '')
            $after = Get-Plan $evalB
            "ДАНІ 7б ДО: #104 — $(Where-Is $before 104 'ж3_свято_др'); ПІСЛЯ: #104 — $(Where-Is $after 104 'ж3_свято_др')"
            Check '7б ДО (план без held): пари #104 під межею нема ні в bad, ні в scenes' ((Where-Is $before 104 'ж3_свято_др') -ceq 'ніде')
            Check '7б ПІСЛЯ: #104 у bad з причиною оцінки звіту межі, #101 лишається покритим і притриманим' ((Where-Is $after 104 'ж3_свято_др') -ceq
                "bad: не виміряно в оцінці ${boundEval}:5: модель не дійшла до вибору" -and (Where-Is $after 101 'ж1_робота') -ceq 'ніде' -and
                (@(Held-Pairs $after) -join ',') -ceq '101|ж1_робота')
        } finally { $script:PlanPulls = @($script:Merged) }
    }
} finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^plan-pytannia-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($bad) { exit 1 }
