#Requires -Version 5.1
<# Стенд дошки 15004: від 05.11 жоден звіт живого прогону не мав рядка `ПЕРЕВІРЕНО ЗБІРКУ`, бо в кожному плані були
питання, яких прогін не виконає (режим, що прилад відхиляє, сцена «у хмарі», обрив стенда), а межа — «все або нічого»
й лише з рядка агента. План Е1 ріс 29 → 48 → 64 сцени, жодна прогнана сцена його не звужувала.
ДО — звіт без записів приладів, як його бачив план до правки: усі питання лишаються. ПІСЛЯ — `Get-AutoRanPairs` бере
завершені записи сцен із голови звіту: прогнані питання виходять із плану, непрогнані лишаються. Справжні функції
обгортки; підмінено лише список PR (Get-AutoPublicItems). #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('mezha-scen-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Write-Log([string]$Text) {
    <# queue_lanes.ps1 вимагає від хазяїна функцію журналу. #>
    Write-Host "  журнал обгортки: $Text"
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $repo = Join-Path $tmp 'plan'
    [void][IO.Directory]::CreateDirectory("$repo/аудит/проби")
    & git -C $repo init -q -b main
    & git -C $repo config user.name 'Стенд'; & git -C $repo config user.email 'stand@local'
    $script:RepoDir = $repo; $script:Repo = $repo; $script:NoHooks = Join-Path $tmp 'no-hooks'
    [IO.File]::WriteAllText("$repo/аудит/проби/живі_сцени.txt", [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf), $utf)
    function Commit([string]$Date, [string]$Name) {
        $author = $env:GIT_AUTHOR_DATE; $committer = $env:GIT_COMMITTER_DATE
        try {
            $env:GIT_AUTHOR_DATE = $Date; $env:GIT_COMMITTER_DATE = $Date
            & git -C $repo add -A
            & git -C $repo commit -q --allow-empty -m $Name
            if ($LASTEXITCODE) { throw 'Не створено коміт' }
            (& git -C $repo rev-parse HEAD).Trim()
        } finally { $env:GIT_AUTHOR_DATE = $author; $env:GIT_COMMITTER_DATE = $committer }
    }
    function Put([string]$Path, [string]$Text) {
        $full = Join-Path $repo $Path
        [void][IO.Directory]::CreateDirectory((Split-Path -Parent $full))
        [IO.File]::WriteAllText($full, $Text, $utf)
    }
    # Сцени: A, B, C, D — режим «повне», E — «функція» (у хмарі).
    $A = 'ж1_робота'; $B = 'ж2_побачення_вечір'; $C = 'ж3_співбесіда'; $D = 'ж3_свято_др'; $E = 'ж7_прогулянка_субота'
    $old = Commit '2026-01-01T00:00:00Z' 'Збірка останньої повної межі'
    $scene = @{11 = $A; 12 = $B; 13 = $C; 14 = $C; 15 = $D; 16 = $E; 17 = $A}
    $merge = @{}
    foreach ($n in 11..16) { $merge[$n] = Commit ('2026-01-02T0' + ($n - 10) + ':00:00Z') "Злиття #$n" }
    $build1 = Commit '2026-01-02T08:00:00Z' 'збірка 1'
    # Голова звіту Е1 — поза main: план, журнал приладу й записи сцен, як їх лишає `записати_план.py` і `нова_база.js`.
    & git -C $repo checkout -q -b report $build1
    $slug = 'Е1-нічний-живий-20260102'; $dir = "аудит/проби/$slug"
    $planJson = '{"since_sha":"' + $old + '","scenes":{"' + $A + '":[{"pr":11,"question":"q11"}],"' + $B + '":[{"pr":12,"question":"q12"}],"' +
        $C + '":[{"pr":13,"question":"q13"},{"pr":14,"question":"q14"}],"' + $D + '":[{"pr":15,"question":"q15"}]},"cloud":{"' + $E + '":[{"pr":16,"question":"q16"}]},"bad":[]}'
    Put "$dir/ПЛАН.json" $planJson
    Put "$dir/done.txt" ('{"сцена": "' + $C + '", "pr": 13, "відмова_питання": "довільна інструкція"}' + "`n" +
        '{"команда": ["python", "записати_сцену.py", "--сцена", "' + $A + '"], "rc": 1}' + "`n")
    function Put-Record([string]$Path, [int]$Rc) {
        Put "$Path/результат.json" ('{"rc": ' + $Rc + ', "sha": "' + $build1 + '"}')
        foreach ($f in @('повтор.json', 'знімки/доказ.json', 'VIDPOVIDI/обмін/00001.json')) { Put "$Path/$f" '{}' }
        Put "$Path/лог.txt" 'лог'
    }
    Put-Record "$dir/$A" 1
    Put-Record "$dir/$B" 2
    Put-Record "$dir/$C" 0
    # D зелена — `нова_база.js` перенесла її в нічні; походження називає теку запису наряду (шлях Windows).
    Put-Record "аудит/проби/нічні/20260102/$D" 0
    Put "аудит/проби/нічні/20260102/$D/походження.json" ('{"шлях_запису": "' + ("$dir/$D" -replace '/', '\\') + '"}')
    $reportHead = Commit '2026-01-02T12:00:00Z' 'Звіт Е1 без рядка межі'
    & git -C $repo checkout -q main
    $merge[17] = Commit '2026-01-03T01:00:00Z' 'Злиття #17 після звіту'
    $build2 = Commit '2026-01-03T02:00:00Z' 'збірка 2'
    function Pull($Number, [string]$Ref, $Merged, $Merge, [string]$Body, [string]$Created, [string]$Head = '') {
        [pscustomobject]@{number = $Number; user = @{login = 'mightyrochy'}; head = @{ref = $Ref; sha = $Head; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merged_at = $Merged; merge_commit_sha = $Merge; body = $Body; created_at = $Created}
    }
    $script:PlanPulls = @()
    foreach ($n in 11..17) { $script:PlanPulls += Pull $n 'claude/код' '2026-01-02T00:00:00Z' $merge[$n] "ЖИВИЙ ПІСЛЯ: $($scene[$n]) — q$n" '2026-01-02T00:00:00Z' }
    $script:PlanPulls += Pull 90 'gemini/Е1-нічний-живий-20260101' $null $null "ПЕРЕВІРЕНО ЗБІРКУ: $old" '2026-01-01T06:00:00Z'
    $report = Pull 91 "gemini/$slug" $null $null 'Звіт: план виконано не весь, рядка межі нема' '2026-01-02T12:00:00Z' $reportHead
    $script:PlanPulls += $report
    function Get-AutoPublicItems { $script:PlanPulls }
    function Pairs($Plan, [string]$Field) {
        @(@($Plan.$Field.PSObject.Properties) | ForEach-Object { $id = $_.Name; @($_.Value) | ForEach-Object { "$($_.pr)|$id" } } | Sort-Object)
    }

    Scenario '1 ДО: звіт без записів приладів не звужує план' {
        $report.head.sha = ''
        $plan = ConvertFrom-Json (Get-AutoLivePlan $build2)
        $report.head.sha = $reportHead
        "ДО: сцени $((Pairs $plan 'scenes') -join ', ')"
        Check '1 межа — та сама повна збірка' ($plan.since_sha -ceq $old)
        Check '1 усі шість питань сцен у плані, хоч три з них звіт прогнав' ((Pairs $plan 'scenes').Count -eq 6)
    }
    Scenario '2 ПІСЛЯ: прогнане виходить, непрогнане лишається' {
        $plan = ConvertFrom-Json (Get-AutoLivePlan $build2)
        $left = Pairs $plan 'scenes'
        "ПІСЛЯ: сцени $($left -join ', '); у хмарі $((Pairs $plan 'cloud') -join ', '); прогнано $($plan.ran.'91')"
        Check '2 межа без рядка агента не зсунулась — нічого не стало «прогнаним» цілком' ($plan.since_sha -ceq $old)
        Check '2 завершений запис з rc 1 прибрав питання #11' ("11|$A" -notin $left)
        Check '2 зелений запис, перенесений у нічні, прибрав питання #15' ("15|$D" -notin $left)
        Check '2 сцена з rc 0 прибрала питання #14, якого прилад не відхилив' ("14|$C" -notin $left)
        Check '2 обрив стенда (rc 2) лишив питання #12' ("12|$B" -in $left)
        Check '2 питання #13, яке прилад відхилив, лишилось, хоч сцену записано' ("13|$C" -in $left)
        Check '2 злиття після коду запису (#17) лишилось' ("17|$A" -in $left)
        Check '2 сцена «у хмарі» лишилась у cloud' ((Pairs $plan 'cloud') -join ',' -ceq "16|$E")
        Check '2 план звітує, скільки питань звіт прогнав' ($left.Count -eq 3 -and $plan.ran.'91' -eq 3)
    }
    Scenario '3 нерозбірний журнал приладу — звіт нічого не прибирає' {
        & git -C $repo checkout -q report
        Put "$dir/done.txt" 'не JSON'
        $broken = Commit '2026-01-02T13:00:00Z' 'Зіпсований журнал'
        & git -C $repo checkout -q main
        $report.head.sha = $broken
        $plan = ConvertFrom-Json (Get-AutoLivePlan $build2)
        $report.head.sha = $reportHead
        Check '3 відмова питання могла загубитись — усі шість питань лишаються' ((Pairs $plan 'scenes').Count -eq 6)
    }
    Scenario '4 запис без обміну моделі — не завершений' {
        & git -C $repo checkout -q report
        Remove-Item -LiteralPath (Join-Path $repo "$dir/$A/VIDPOVIDI") -Recurse -Force
        $partial = Commit '2026-01-02T14:00:00Z' 'Запис без VIDPOVIDI'
        & git -C $repo checkout -q main
        $report.head.sha = $partial
        $plan = ConvertFrom-Json (Get-AutoLivePlan $build2)
        $report.head.sha = $reportHead
        Check '4 питання #11 лишається' ("11|$A" -in (Pairs $plan 'scenes'))
    }
    Scenario '5 автоживий із прогнаним планом — порожній, без моделі' {
        $script:PlanPulls = @($script:PlanPulls | Where-Object { $_.number -notin @(12, 13, 16, 17) })
        $text = "наряд`nПЛАН ЖИВОГО — ДАНІ (JSON):`n" + (Get-AutoLivePlan $build1) + "`n"
        Check '5 усе прогнане — EMPTY_PLAN до моделі' (Test-AutoPlanEmpty ('автоживий-' + $build1) $text)
    }
} finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^mezha-scen-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
if ($bad) { exit 1 }
