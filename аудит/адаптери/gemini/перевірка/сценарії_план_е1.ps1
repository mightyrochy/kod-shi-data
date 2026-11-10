#Requires -Version 5.1
<# Стенд наряду «обгортка-е1-план-gpu» (07.11, #1856): позначка `Е1-нічний-живий-*` p1 щопроходу йшла в REVIEW_API і WAIT 120 с,
прогін не стартував, а решта GPU-позначок проходу стояла «її щойно взяв наряд цього проходу», хоч GPU була вільна.
Корінь: `Get-AutoLivePlan` читав усі 33 сторінки `pulls` (по 100) без бюджету й без входу, збій ставав мовчазним REVIEW_API без межі,
а прохід тримав GPU за процесом, який за секунди пішов у чекання. Справжні функції обгортки; підмінено лише мережу
(Invoke-RestMethod), годинник і запуск процесів наряду. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('plan-e1-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
function Plan-Date([string]$Iso) { [datetimeoffset]::Parse($Iso, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal) }
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $LaneDir = Join-Path $tmp 'lanes'; [void][IO.Directory]::CreateDirectory($LaneDir)
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $registryText = [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf)
    $planRepo = Join-Path $tmp 'plan'
    [void][IO.Directory]::CreateDirectory("$planRepo/аудит/проби")
    & git -C $planRepo init -q -b main
    & git -C $planRepo config user.name 'Стенд'; & git -C $planRepo config user.email 'stand@local'
    $script:RepoDir = $planRepo; $script:Repo = $planRepo; $script:NoHooks = Join-Path $tmp 'no-hooks'
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
    # Історія main: реєстр і 40 злиттів із кроком у 3 год від 01.11.
    $null = Plan-Commit '2026-10-01T00:00:00Z' 'Реєстр'
    $commits = @{}
    $dates = @{}
    for ($k = 1; $k -le 40; $k++) {
        $when = (Plan-Date '2026-11-01T00:00:00Z').AddHours(3 * $k)
        $commits[$k] = Plan-Commit $when.ToString('yyyy-MM-ddTHH:mm:ssZ') "Злиття $k"
        $dates[$k] = $when
    }
    $buildMain = $commits[40]
    $ids = @('ж1_оціни_образ_6б', 'ж2_побачення_вечір', 'ж3_співбесіда', 'ж3_свято_др')
    function Fake-Pull([int]$Number, [string]$Ref, [string]$Updated, [string]$Merged, [string]$Merge, [string]$Body) {
        [pscustomobject]@{number = $Number; updated_at = $Updated; merged_at = $(if ($Merged) { $Merged } else { $null }); merge_commit_sha = $Merge; body = $Body
            user = @{login = 'mightyrochy'}; head = @{ref = $Ref; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}}
    }
    # Дані як на ноутбуці 07.11: 3273 PR; звіт Е1 у верхівці, довкола — злиті PR після нього й непотрібні оновлення (шум).
    # Старі PR (2982) оновлені до 30.10 — старіші за збірку звіту.
    function New-PullSet([int]$ReportBuild, [bool]$WithReport, [int]$Noise) {
        $all = New-Object Collections.ArrayList
        $number = 5000
        for ($k = 1; $k -le 40; $k++) {
            $body = "ЖИВИЙ ПІСЛЯ: $($ids[$k % 4]) — питання $k → повне → main → ок"
            [void]$all.Add((Fake-Pull ($number + $k) "claude/код-$k" $dates[$k].AddHours($k % 5).ToString('yyyy-MM-ddTHH:mm:ssZ') $dates[$k].ToString('yyyy-MM-ddTHH:mm:ssZ') $commits[$k] $body))
        }
        if ($WithReport) {
            $when = $dates[$ReportBuild].AddHours(2).ToString('yyyy-MM-ddTHH:mm:ssZ')
            [void]$all.Add((Fake-Pull 6000 ('claude/автоживий-' + $commits[$ReportBuild]) $when '' '' 'Звіт'))
        }
        $noiseStart = (Plan-Date '2026-11-03T12:00:00Z')
        for ($i = 0; $i -lt $Noise; $i++) {
            [void]$all.Add((Fake-Pull (7000 + $i) "claude/шум-$i" $noiseStart.AddMinutes(20 + $i * 5).ToString('yyyy-MM-ddTHH:mm:ssZ') '' '' ''))
        }
        $old = (Plan-Date '2026-10-30T00:00:00Z')
        $total = 3273
        for ($i = 0; $all.Count -lt $total; $i++) {
            $covered = $commits[($i % 19) + 1]
            [void]$all.Add((Fake-Pull (1 + $i) "claude/давнє-$i" $old.AddMinutes(-$i).ToString('yyyy-MM-ddTHH:mm:ssZ') $old.AddMinutes(-$i).ToString('yyyy-MM-ddTHH:mm:ssZ') $covered ''))
        }
        # GitHub сортує за оновленням від найновішого; стабільний порядок за номером.
        @($all | Sort-Object @{Expression = { $_.updated_at }; Descending = $true }, @{Expression = { $_.number }})
    }
    $script:Served = @()
    $script:RestCalls = 0
    $script:RestFail = ''
    function Invoke-RestMethod {
        param($Uri, $Method, $TimeoutSec, $MaximumRedirection, $Headers)
        $script:RestCalls++
        if ($script:RestFail -and $script:RestCalls -ge $script:RestFailAt) { throw $script:RestFail }
        if ($Uri -cnotmatch 'per_page=([0-9]+)&page=([0-9]+)$') { throw "Невідомий запит $Uri" }
        $per = [int]$Matches[1]; $page = [int]$Matches[2]
        if ($per -gt 100) { throw 'per_page понад 100' }
        $skip = ($page - 1) * $per
        if ($skip -ge $script:Served.Count) { return @() }
        , @($script:Served | Select-Object -Skip $skip -First $per)
    }
    function Reset-Budget { Remove-Item -LiteralPath (Join-Path $LaneDir 'review-api.json') -Force -ErrorAction SilentlyContinue }
    function Reset-Counters { $script:RestCalls = 0; $script:AutoApiCalls = 0; $script:RestFail = '' }

    Scenario '1 план: ДО (усі сторінки по 100) і ПІСЛЯ (до межі)' {
        $script:Served = New-PullSet 20 $true 250
        Check '1 набір як на ноутбуці: 3273 PR' ($script:Served.Count -eq 3273)
        # ДО: усе читання, як було (per_page=100, без ранньої зупинки, без бюджету-межі).
        $keep = @($script:AutoPlanPerPage, $script:AutoPlanMaxPages, $script:AutoPlanMarginHours, $script:ReviewApiLimit)
        try {
            $script:AutoPlanPerPage = 100; $script:AutoPlanMaxPages = 100; $script:AutoPlanMarginHours = 1000000; $script:ReviewApiLimit = 100000
            Reset-Budget; Reset-Counters
            $before = Get-AutoLivePlan $buildMain
            $callsBefore = $script:RestCalls
        } finally { $script:AutoPlanPerPage, $script:AutoPlanMaxPages, $script:AutoPlanMarginHours, $script:ReviewApiLimit = $keep }
        Check "1 ДО: $callsBefore запити на спробу, а без входу GitHub дає 60 на годину" ($callsBefore -eq 33)
        # ПІСЛЯ: налаштування за замовчуванням.
        Reset-Budget; Reset-Counters
        $after = Get-AutoLivePlan $buildMain
        $callsAfter = $script:RestCalls
        "ПІСЛЯ: запитів на спробу = $callsAfter (ДО = $callsBefore)"
        Check '1 ПІСЛЯ: запитів не більше восьми' ($callsAfter -ge 1 -and $callsAfter -le 8)
        Check '1 ПІСЛЯ: лічильник запитів плану збігається з мережею' ($script:AutoApiCalls -eq $callsAfter)
        Check '1 ПІСЛЯ: склад плану той самий, що й після повного читання' ($after -ceq $before)
        $plan = ConvertFrom-Json $after
        $expectedScenes = @{}
        for ($k = 21; $k -le 40; $k++) { $expectedScenes[$ids[$k % 4]] = $true }
        Check '1 у плані злиття 21..40, нічого з покритого звітом' ((@($plan.scenes.PSObject.Properties.Name) | Sort-Object) -join ',' -ceq (($expectedScenes.Keys | Sort-Object) -join ',') -and $plan.since_sha -ceq $commits[20])
        $questions = @($plan.scenes.PSObject.Properties | ForEach-Object { @($_.Value) | ForEach-Object { $_.question } })
        Check '1 питань рівно двадцять — жодне не загублене' ($questions.Count -eq 20 -and @($questions | Where-Object { $_ -clike 'питання 21 *' }).Count -eq 1 -and @($questions | Where-Object { $_ -clike 'питання 40 *' }).Count -eq 1 -and @($questions | Where-Object { $_ -clike 'питання 20 *' }).Count -eq 0)
        $used = ConvertFrom-Json ([IO.File]::ReadAllText((Join-Path $LaneDir 'review-api.json'), $utf))
        Check '1 запити плану взято зі спільного бюджету' (@($used.calls).Count -eq $callsAfter -and @($used.calls).Count -le $script:ReviewApiLimit)
    }
    Scenario '2 склад плану не залежить від місця звіту й від кількох звітів' {
        foreach ($build in @(5, 20, 33, 39)) {
            $script:Served = New-PullSet $build $true 120
            $keep = @($script:AutoPlanPerPage, $script:AutoPlanMaxPages, $script:AutoPlanMarginHours, $script:ReviewApiLimit)
            try {
                $script:AutoPlanPerPage = 100; $script:AutoPlanMaxPages = 100; $script:AutoPlanMarginHours = 1000000; $script:ReviewApiLimit = 100000
                Reset-Budget; Reset-Counters
                $full = Get-AutoLivePlan $buildMain
            } finally { $script:AutoPlanPerPage, $script:AutoPlanMaxPages, $script:AutoPlanMarginHours, $script:ReviewApiLimit = $keep }
            Reset-Budget; Reset-Counters
            $short = Get-AutoLivePlan $buildMain
            Check "2 звіт збірки $build : плани однакові, запитів $($script:RestCalls) замість 33" ($short -ceq $full -and $script:RestCalls -lt 33 -and ((ConvertFrom-Json $short).since_sha -ceq $commits[$build]))
        }
        # Два звіти: чинний — новіша збірка, давніший звіт плану не звужує.
        $set = New-PullSet 15 $true 120
        $newer = Fake-Pull 6001 ('claude/автоживий-' + $commits[30]) ($dates[30].AddHours(2).ToString('yyyy-MM-ddTHH:mm:ssZ')) '' '' 'Звіт'
        $script:Served = @(@($set) + @($newer) | Sort-Object @{Expression = { $_.updated_at }; Descending = $true }, @{Expression = { $_.number }})
        Reset-Budget; Reset-Counters
        $two = ConvertFrom-Json (Get-AutoLivePlan $buildMain)
        Check '2 два звіти: межа — збірка новішого' ($two.since_sha -ceq $commits[30] -and @($two.scenes.PSObject.Properties | ForEach-Object { @($_.Value) }).Count -eq 10)
    }
    Scenario '3 нема звіту: AUTO_PAGES, а не вічне повторення' {
        $script:Served = New-PullSet 20 $false 250
        Reset-Budget; Reset-Counters
        $message = ''
        try { $null = Get-AutoLivePlan $buildMain } catch { $message = $_.Exception.Message }
        Check "3 без звіту читання стає на межі сторінок і каже AUTO_PAGES (запитів $($script:RestCalls))" ($message -ceq 'AUTO_PAGES' -and $script:RestCalls -eq $script:AutoPlanMaxPages)
        Check '3 одна марна спроба лишає в бюджеті запас для інших читачів' ($script:AutoPlanMaxPages -lt $script:ReviewApiLimit)
    }
    Scenario '4 бюджет без входу' {
        $script:Served = New-PullSet 20 $true 250
        # 29 запитів уже витрачено за годину: далі пускаємо один, план без другої сторінки не збудується.
        Reset-Counters
        $now = Get-ReviewTime
        $calls = @(1..29 | ForEach-Object { $now - 60 })
        Write-FileAtomic (Join-Path $LaneDir 'review-api.json') ([ordered]@{calls = $calls; until = 0} | ConvertTo-Json -Compress)
        $message = ''
        try { $null = Get-AutoLivePlan $buildMain } catch { $message = $_.Exception.Message }
        $saved = ConvertFrom-Json ([IO.File]::ReadAllText((Join-Path $LaneDir 'review-api.json'), $utf))
        Check '4 бюджет вичерпано: AUTO_BUDGET, у мережу пішов лише дозволений запит' ($message -ceq 'AUTO_BUDGET' -and $script:RestCalls -eq 1 -and @($saved.calls).Count -eq 30)
        Check '4 перевірка PR бачить те саме вичерпання' ((Get-AutoReviewState ('автоперевірка-9-' + ('a' * 40))) -ceq 'REVIEW_API')
        # Збій мережі: спільна пауза, наступна спроба не йде в мережу.
        Reset-Budget; Reset-Counters
        $script:RestFail = 'HTTP 403'; $script:RestFailAt = 2
        $message = ''
        try { $null = Get-AutoLivePlan $buildMain } catch { $message = $_.Exception.Message }
        Check '4 збій 403 на другій сторінці: помилка мережі збережена, не AUTO_BUDGET' ($message -ceq 'HTTP 403' -and $script:RestCalls -eq 2)
        $before = $script:RestCalls
        $script:RestFail = ''
        $message = ''
        try { $null = Get-AutoLivePlan $buildMain } catch { $message = $_.Exception.Message }
        Check '4 після збою діє спільна пауза: у мережу не йдемо' ($message -ceq 'AUTO_BUDGET' -and $script:RestCalls -eq $before)
        Reset-Budget
    }
    Scenario '5 збій плану має свій код і будить диспетчера' {
        $m = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/Е1-нічний-живий-20261107/cc-claude-sonnet-5-5-medium/1/gpu-p1`t$buildMain`t1")
        $script:StateDir = Join-Path $tmp 'state-plan'; [void][IO.Directory]::CreateDirectory($script:StateDir)
        $sp = Get-StatePath (Get-MarkerKey $m)
        $script:Clock = 1000000
        function Get-ReviewTime { $script:Clock }
        function Write-Log([string]$Text) { }
        $results = @()
        for ($i = 1; $i -le 7; $i++) { $results += [bool](Enter-PlanWait $m 'AUTO_PAGES' ('c' * 40)) }
        Check '5 чекань, далі межа: PLAN_FAILED' (($results[0..4] -join ',') -ceq 'True,True,True,True,True' -and -not $results[5] -and -not $results[6])
        $state = Get-MarkerState $m
        Check '5 останнє чекання записане з лічильником, часом +300 с і причиною' ($state.Kind -ceq 'WAIT' -and [int]$state.Wait.retakes -eq 5 -and [long]$state.Wait.until -eq 1000300 -and $state.Wait.reason -ceq 'AUTO_PAGES' -and $state.Wait.group -ceq 'PLAN_WAIT')
        Check '5 причина збою: код обгортки, статус HTTP або PLAN_ERROR — без тексту сервера' ((Get-PlanFailReason 'AUTO_PAGES') -ceq 'AUTO_PAGES' -and (Get-PlanFailReason 'The remote server returned an error: (403) rate limit exceeded.') -ceq 'HTTP_403' -and (Get-PlanFailReason 'Response status code does not indicate success: 429 (Too Many Requests).') -ceq 'HTTP_429' -and (Get-PlanFailReason 'щось інше') -ceq 'PLAN_ERROR')
        # AUTO_BUDGET — чекання вікна, а не вада: лічильник не росте, межі нема.
        $n = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/Е1-нічний-живий-20261108/cc-claude-sonnet-5-5-medium/1/gpu-p1`t$buildMain`t1")
        $budgetOk = $true
        for ($i = 1; $i -le 12; $i++) { $budgetOk = $budgetOk -and [bool](Enter-PlanWait $n 'AUTO_BUDGET') }
        Check '5 AUTO_BUDGET: двічі по шість разів чекання без PLAN_FAILED, retakes не росте' ($budgetOk -and (Get-Retakes (Get-StatePath (Get-MarkerKey $n))) -eq 0 -and $(Get-MarkerState $n).Wait.group -ceq 'REVIEW_API')
        # Автоперевірка PR лишається при REVIEW_API без межі, як і була.
        $r = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/автоперевірка-41-$('a' * 40)/gpt-6.1-sol-high/1`t$buildMain`t1")
        $reviewOk = $true
        for ($i = 1; $i -le 8; $i++) { $reviewOk = $reviewOk -and [bool](Enter-PlanWait $r 'HTTP 403') }
        Check '5 автоперевірка PR: збій API — REVIEW_API без межі' ($reviewOk -and (Get-Retakes (Get-StatePath (Get-MarkerKey $r))) -eq 0)
        Check '5 код PLAN_FAILED є в таблиці кодів публікатора' ($script:RunCodes.ContainsKey('PLAN_FAILED') -and ([string]$script:RunCodes['PLAN_FAILED']).Length -gt 10)
        Check '5 PLAN_FAILED не тихий: правило ЧЕРГА.md «будить усе, крім STALE, REVIEW_API, EMPTY_PLAN»' ('PLAN_FAILED' -cnotmatch $script:QuietBlockedCodes -and 'REVIEW_API' -cmatch $script:QuietBlockedCodes)
        $queueDoc = [IO.File]::ReadAllText((Join-Path $SourceDir 'ЧЕРГА.md'), $utf)
        Check '5 ЧЕРГА.md називає PLAN_FAILED' ($queueDoc.Contains('PLAN_FAILED'))
    }
    Scenario '6 GPU: наряд, що пішов у чекання, не тримає GPU решти позначок' {
        $script:StateDir = Join-Path $tmp 'state-gpu'; [void][IO.Directory]::CreateDirectory($script:StateDir)
        function Invoke-HealthBeat { }
        $stateFile = Join-Path $tmp 'worker-state.txt'
        $script:GpuStartWaitSeconds = 2
        $script:GpuStartPollMs = 20
        $exited = [pscustomobject]@{Proc = [pscustomobject]@{HasExited = $true}; Gpu = $true}
        Check '6 процес наряду скінчився до моделі — EXITED' ((Wait-GpuWorkerOutcome $exited $stateFile) -ceq 'EXITED')
        $alive = [pscustomobject]@{Proc = [pscustomobject]@{HasExited = $false}; Gpu = $true}
        [IO.File]::WriteAllText($stateFile, 'STARTED {"id":"x","start":"","slot":"1"}', $utf)
        $script:GpuStartWaitSeconds = 1
        Check '6 готується (STARTED без початку прогону) — TIMEOUT, GPU лишається за ним' ((Wait-GpuWorkerOutcome $alive $stateFile) -ceq 'TIMEOUT')
        [IO.File]::WriteAllText($stateFile, 'STARTED {"id":"x","start":"' + ('b' * 40) + '","slot":"1"}', $utf)
        Check '6 модель стартувала (gemini: start — SHA) — RUNNING' ((Wait-GpuWorkerOutcome $alive $stateFile) -ceq 'RUNNING')
        [IO.File]::WriteAllText($stateFile, 'STARTED 20261107-160000-abcdefabcdef {"pid":5,"start":"2026-11-07T16:00:00Z"}', $utf)
        Check '6 модель стартувала (claude: start — час процесу) — RUNNING' ((Wait-GpuWorkerOutcome $alive $stateFile) -ceq 'RUNNING')
        [IO.File]::WriteAllText($stateFile, 'WAIT {"until":1}', $utf)
        $script:GpuStartWaitSeconds = 1
        Check '6 WAIT — це не старт' (-not (Test-RunStarted $stateFile))
        Check '6 нема файла стану — це не старт' (-not (Test-RunStarted (Join-Path $tmp 'нема.txt')))
        $mk = {
            param([string]$Slug, [string]$Cond, [int]$Seen)
            $m = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/$Slug/cc-claude-sonnet-5-5-medium/1/$Cond`t$buildMain`t1")
            $m
        }
        $p1 = & $mk 'Е1-нічний-живий-20261107' 'gpu-p1'
        $p2 = & $mk 'Річ-колір-вимір' 'gpu-p2'
        $cpu = & $mk 'Дошка-0' 'p0'
        $ordered = @($p1, $p2, $cpu)
        Check '6 після p1 стоїть готова GPU-позначка p2' (Test-LaterGpuMarker $ordered $p1)
        Check '6 після p2 далі GPU-позначок нема' (-not (Test-LaterGpuMarker $ordered $p2))
        Write-FileAtomic (Get-StatePath (Get-MarkerKey $p2)) 'WAIT {"until":99999999999}'
        Check '6 p2 ще чекає квоту — не готова, p1 не чекає даремно' (-not (Test-LaterGpuMarker $ordered $p1))
    }
} finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^plan-e1-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
if ($bad) { exit 1 }
