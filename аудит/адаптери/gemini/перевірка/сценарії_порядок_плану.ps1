#Requires -Version 5.1
<# Стенд наряду «Обгортка-автоживий-обрив-не-губить» (18.11): справжній `Get-AutoLivePlan` обгортки на п'яти злитих PR
і мережа GitHub (`Get-AutoPublicItems`) — підміною. Мірила: сцена найновішого PR — перша (ДО — порядок злиття від
найдавнішого); хмарна тека `Тестовий-прогін-хмара-*` у дереві збірки лічить пару прогнаною (ДО — план повторював сцену). #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('poriadok-planu-' + [guid]::NewGuid().ToString('N'))
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
    $LaneDir = Join-Path $tmp 'lanes'; [void][IO.Directory]::CreateDirectory($LaneDir)
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $repo = Join-Path $tmp 'repo'
    & git init -q -b main $repo
    & git -C $repo config user.name 'Стенд'; & git -C $repo config user.email 'stand@local'; & git -C $repo config core.autocrlf false
    $script:RepoDir = $repo; $script:Repo = $repo; $script:NoHooks = Join-Path $tmp 'no-hooks'
    [void][IO.Directory]::CreateDirectory("$repo/аудит/проби")
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
    # П'ять злитих PR на чотири сцени; PR 105 — найновіший, другим питанням до сцени PR 102.
    $ids = @('ж1_робота', 'ж2_побачення_вечір', 'ж2_похорон', 'ж3_свято_др')
    $scenesOf = @{101 = $ids[0]; 102 = $ids[1]; 103 = $ids[2]; 104 = $ids[3]; 105 = $ids[1]}
    $merges = @{}
    $script:Merged = @()
    foreach ($n in 101..105) {
        $date = '2026-11-01T0' + ($n - 100) + ':00:00Z'
        $merges[$n] = Repo-Commit $date "Злиття $n"
        $script:Merged += [pscustomobject]@{number = $n; user = @{login = 'mightyrochy'}; head = @{ref = "claude/код-$n"; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merge_commit_sha = $merges[$n]; merged_at = $date; created_at = $date; updated_at = $date
            body = "ЖИВИЙ ПІСЛЯ: $($scenesOf[$n]) — питання $n"}
    }
    $build = $merges[105]
    $script:PlanPulls = @($script:Merged)
    function Get-AutoPublicItems { $script:PlanPulls }
    function Plan-Scenes([string]$Main) { @((ConvertFrom-Json (Get-AutoLivePlan $Main)).scenes.PSObject.Properties | ForEach-Object { $_.Name }) }
    $plan1 = Get-AutoLivePlan $build
    $order1 = @(Plan-Scenes $build)
    $M = $order1.Count

    Scenario '1 порядок' {
        Check '1 план: чотири сцени на п''ять питань' ($M -eq 4 -and @((ConvertFrom-Json $plan1).scenes.($ids[1])).Count -eq 2)
        "ДАНІ порядок: $($order1 -join ', ') (за злиттям — $($ids -join ', '))"
        Check '1 сцена найновішого PR (105) — перша, далі від новішого злиття до давнішого' (($order1 -join ',') -ceq (@($ids[1], $ids[3], $ids[2], $ids[0]) -join ','))
    }
    Scenario '2 хмарна тека' {
        $cloudDir = "$repo/аудит/проби/Тестовий-прогін-хмара-стенд"
        $record = "$cloudDir/$($ids[0])"
        foreach ($sub in @('знімки', 'VIDPOVIDI/обмін')) { [void][IO.Directory]::CreateDirectory("$record/$sub") }
        [IO.File]::WriteAllText("$cloudDir/ПЛАН.json", (ConvertTo-Json -Compress -Depth 5 @{build = $build; scenes = @{$ids[0] = @(@{pr = 101; question = 'питання 101'})}}), $utf)
        [IO.File]::WriteAllText("$cloudDir/done.txt", ('{"сцена": "' + $ids[0] + '", "rc": 0, "секунд": 300}' + "`n"), $utf)
        [IO.File]::WriteAllText("$record/результат.json", ('{"rc": 0, "sha": "' + $build + '"}'), $utf)
        foreach ($file in @('повтор.json', 'лог.txt', 'знімки/доказ.json', 'VIDPOVIDI/обмін/1.json')) { [IO.File]::WriteAllText("$record/$file", '{}', $utf) }
        $withCloud = Repo-Commit '2026-11-02T00:00:00Z' 'Хмарний прогін'
        $without = (Get-AutoRanPairs @() ([datetimeoffset]::MinValue)).Count
        $pairs = Get-AutoRanPairs @() ([datetimeoffset]::MinValue) $withCloud
        Check '2 без дерева збірки хмарних пар нема (ДО)' ($without -eq 0)
        Check '2 пара хмарного прогону — прогнана' ($pairs.ContainsKey("101|$($ids[0])") -and $pairs.Count -eq 1)
        $cloudPlan = @(Plan-Scenes $withCloud)
        "ДАНІ хмара: сцен у плані збірки з хмарною текою — $($cloudPlan.Count) (без неї — $M)"
        Check '2 план не повторює сцену, яку прогнала хмара' ($cloudPlan.Count -eq $M - 1 -and $ids[0] -cnotin $cloudPlan)
    }
} finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^poriadok-planu-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($bad) { exit 1 }
