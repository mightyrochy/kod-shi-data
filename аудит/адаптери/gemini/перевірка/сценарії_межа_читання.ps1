#Requires -Version 5.1
<# Стенд дошки 15052: план живого читав `pulls` (за оновленням) до збірки останньої повної межі `ПЕРЕВІРЕНО ЗБІРКУ`. Межі
нема, доки в плані є питання, яких прогін не виконає, тож читання росло щодня до AUTO_PAGES.
ДО — звіт, чий `ПЛАН.json` не має `build`/`merge` (старий формат): читання йде до повної межі. ПІСЛЯ — план звіту стає
джерелом давніх PR: читання стає за збіркою того плану, непрогнані давні питання (відмова, без запису, «у хмарі», вадний
рядок) беруться з нього, прогнане за записами не повертається, PR, оновлений після звіту, читається з тіла, — і склад
плану той самий, що після повного читання. Справжні функції обгортки; підмінено лише мережу (Invoke-RestMethod). #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('mezha-chyt-' + [guid]::NewGuid().ToString('N'))
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
function T([string]$Iso) { [datetimeoffset]::Parse($Iso, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal) }
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $LaneDir = Join-Path $tmp 'lanes'; [void][IO.Directory]::CreateDirectory($LaneDir)
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
    # A, B, C, D — режим «повне», E — «функція» (у хмарі), Z — id, якого нема в реєстрі (вадний рядок).
    $A = 'ж1_робота'; $B = 'ж2_побачення_вечір'; $C = 'ж3_співбесіда'; $D = 'ж3_свято_др'; $E = 'ж7_прогулянка_субота'; $Z = 'ж0_нема_в_реєстрі'
    $merge = @{}
    $merge[10] = Commit '2026-01-01T12:00:00Z' 'Злиття #10 до повної межі'
    $checked = Commit '2026-01-02T00:00:00Z' 'Збірка повної межі'
    $scene = @{10 = $A; 11 = $A; 12 = $B; 13 = $C; 14 = $E; 15 = $Z; 16 = $C; 17 = $A; 18 = $D}
    foreach ($n in 11..16) { $merge[$n] = Commit ('2026-01-02T0' + ($n - 10) + ':00:00Z') "Злиття #$n" }
    $build1 = Commit '2026-01-04T00:00:00Z' 'Збірка звіту Е1'
    $merge[17] = Commit '2026-01-05T01:00:00Z' 'Злиття #17 після звіту'
    $merge[18] = Commit '2026-01-05T02:00:00Z' 'Злиття #18 після звіту'
    $build2 = Commit '2026-01-06T00:00:00Z' 'Нинішня збірка'
    function Pull($Number, [string]$Ref, [string]$Updated, $Merged, $Merge, [string]$Body, [string]$Head = '') {
        [pscustomobject]@{number = $Number; updated_at = $Updated; created_at = $Updated; merged_at = $Merged; merge_commit_sha = $Merge; body = $Body
            user = @{login = 'mightyrochy'}; head = @{ref = $Ref; sha = $Head; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}}
    }
    function Merged([int]$Number, [string]$When, [string]$Body) { Pull $Number 'claude/код' $When $When $merge[$Number] $Body }
    $base = (New-Object System.Collections.ArrayList)
    # Давні PR до повної межі й шум: 300 оновлень від 02.01 до 06.01 без рядків живого.
    for ($i = 0; $i -lt 60; $i++) { [void]$base.Add((Pull (1000 + $i) 'claude/давнє' (T '2025-12-20T00:00:00Z').AddHours($i).ToString('yyyy-MM-ddTHH:mm:ssZ') $null $null '')) }
    $noiseStart = T '2026-01-02T00:00:00Z'
    for ($i = 0; $i -lt 300; $i++) { [void]$base.Add((Pull (2000 + $i) 'claude/шум' $noiseStart.AddMinutes(19 * $i).ToString('yyyy-MM-ddTHH:mm:ssZ') $null $null '')) }
    [void]$base.Add((Merged 10 '2026-01-01T12:00:00Z' "ЖИВИЙ ПІСЛЯ: $A — q10"))
    foreach ($n in 11..16) { [void]$base.Add((Merged $n ('2026-01-02T0' + ($n - 10) + ':00:00Z') "ЖИВИЙ ПІСЛЯ: $($scene[$n]) — q$n")) }
    $boundary = Pull 900 'gemini/Е1-нічний-живий-20260101' '2026-01-02T06:00:00Z' $null $null "ПЕРЕВІРЕНО ЗБІРКУ: $checked"
    [void]$base.Add($boundary)
    function Serve($Items, [string]$Until) {
        $script:Served = @(@($Items) | Where-Object { $_.updated_at -le $Until } | Sort-Object @{Expression = { $_.updated_at }; Descending = $true }, @{Expression = { $_.number }})
    }
    $script:Asked = @()
    function Invoke-RestMethod {
        param($Uri, $Method, $TimeoutSec, $MaximumRedirection, $Headers)
        if ($Uri -cnotmatch 'per_page=([0-9]+)&page=([0-9]+)$') { throw "Невідомий запит $Uri" }
        $per = [int]$Matches[1]; $skip = ([int]$Matches[2] - 1) * $per
        $page = @($script:Served | Select-Object -Skip $skip -First $per)
        $script:Asked += @($page | ForEach-Object { $_.number })
        , $page
    }
    function Plan-Run([string]$Build, [switch]$Full) {
        <# Один план на свіжому бюджеті; Full — повне читання (запас годинників такий, що межа не стає). #>
        Remove-Item -LiteralPath (Join-Path $LaneDir 'review-api.json') -Force -ErrorAction SilentlyContinue
        $script:Asked = @(); $script:AutoApiCalls = 0
        $keep = $script:AutoPlanMarginHours
        try { if ($Full) { $script:AutoPlanMarginHours = 1000000 }; ConvertFrom-Json (Get-AutoLivePlan $Build) } finally { $script:AutoPlanMarginHours = $keep }
    }
    function Pairs($Plan) {
        $s = @(@('scenes', 'cloud') | ForEach-Object { $kind = $_; @($Plan.$kind.PSObject.Properties) | ForEach-Object { $id = $_.Name; @($_.Value) | ForEach-Object { "$kind|$($_.pr)|$id|$($_.question)" } } })
        @($s + @(@($Plan.bad) | Where-Object { $_ } | ForEach-Object { "bad|$($_.pr)|$($_.line)" }) | Sort-Object)
    }
    # План звіту Е1 на збірці 1 — як його склала обгортка й агент зберіг дослівно.
    Serve $base '2026-01-04T00:00:00Z'
    $plan1 = Get-AutoLivePlan $build1
    & git -C $repo checkout -q -b report $build1
    $slug = 'Е1-нічний-живий-20260104'; $dir = "аудит/проби/$slug"
    Put "$dir/ПЛАН.json" $plan1
    Put "$dir/done.txt" ('{"сцена": "' + $B + '", "pr": 12, "відмова_питання": "режим, який прилад відхиляє"}' + "`n")
    Put "$dir/$A/результат.json" ('{"rc": 0, "sha": "' + $build1 + '"}')
    foreach ($f in @('повтор.json', 'знімки/доказ.json', 'VIDPOVIDI/обмін/00001.json', 'лог.txt')) { Put "$dir/$A/$f" '{}' }
    $headNew = Commit '2026-01-04T12:00:00Z' 'Звіт Е1: план нового формату'
    $old = ConvertFrom-Json $plan1
    foreach ($field in @('build', 'merge', 'since_pr')) { $old.PSObject.Properties.Remove($field) }
    Put "$dir/ПЛАН.json" (ConvertTo-Json -InputObject $old -Depth 8 -Compress)
    $headOld = Commit '2026-01-04T12:05:00Z' 'Звіт Е1: план старого формату'
    $noMerge = ConvertFrom-Json $plan1
    $noMerge.merge.PSObject.Properties.Remove('13')
    Put "$dir/ПЛАН.json" (ConvertTo-Json -InputObject $noMerge -Depth 8 -Compress)
    $headNoMerge = Commit '2026-01-04T12:10:00Z' 'Звіт Е1: план без злиття #13'
    & git -C $repo checkout -q main
    $report = Pull 901 "gemini/$slug" '2026-01-04T12:00:00Z' $null $null 'Звіт: план виконано не весь, рядка межі нема' $headNew
    $now = (New-Object System.Collections.ArrayList); foreach ($one in $base) { [void]$now.Add($one) }
    [void]$now.Add($report)
    [void]$now.Add((Merged 17 '2026-01-05T01:00:00Z' "ЖИВИЙ ПІСЛЯ: $A — q17"))
    [void]$now.Add((Merged 18 '2026-01-05T02:00:00Z' "ЖИВИЙ ПІСЛЯ: $D — q18"))
    # #16 після звіту переписав питання: оновлення піднімає його в читання.
    $edited = @($now | Where-Object { $_.number -eq 16 })[0]
    $edited.body = "ЖИВИЙ ПІСЛЯ: $D — q16 нове"; $edited.updated_at = '2026-01-05T10:00:00Z'
    Serve $now '2026-01-06T00:00:00Z'

    Scenario '0 план звіту несе build, since_pr і merge' {
        $p = ConvertFrom-Json $plan1
        Check '0 build — збірка плану, межа — з номером звіту' ($p.build -ceq $build1 -and $p.since_sha -ceq $checked -and $p.since_pr -ceq '900')
        Check '0 merge — злиття кожного PR плану' ((@($p.merge.PSObject.Properties.Name) | Sort-Object) -join ',' -ceq '11,12,13,14,15,16' -and $p.merge.'13' -ceq $merge[13])
        $script:FullPairs = Pairs (Plan-Run $build2 -Full)
        "ПОВНЕ ЧИТАННЯ: $($script:AutoApiCalls) запитів; $($script:FullPairs -join '; ')"
        Check '0 повне читання дало план' ($script:FullPairs.Count -gt 0)
    }
    Scenario '1 ДО: план звіту старого формату — читання до повної межі' {
        $report.head.sha = $headOld
        try { $plan = Plan-Run $build2 } finally { $report.head.sha = $headNew }
        $script:Before = $script:AutoApiCalls
        "ДО: запитів $script:Before"
        Check '1 ДО: прочитано звіт повної межі (#900)' (900 -in $script:Asked)
        Check '1 ДО: склад плану той самий, що після повного читання' (((Pairs $plan) -join ';') -ceq ($script:FullPairs -join ';'))
    }
    Scenario '2 ПІСЛЯ: читання стає за збіркою плану звіту, склад той самий' {
        $plan = Plan-Run $build2
        $left = Pairs $plan
        "ПІСЛЯ: запитів $($script:AutoApiCalls) (ДО $script:Before); план: $($left -join '; ')"
        Check '2 ПІСЛЯ: запитів менше, ніж ДО' ($script:AutoApiCalls -lt $script:Before)
        Check '2 ПІСЛЯ: давні PR #11–#15 і звіт межі #900 не прочитано' (-not @(@(11, 12, 13, 14, 15, 900) | Where-Object { $_ -in $script:Asked }).Count)
        Check '2 ПІСЛЯ: склад плану той самий, що після повного читання' (($left -join ';') -ceq ($script:FullPairs -join ';'))
        Check '2 межа — та сама повна збірка з тим самим звітом' ($plan.since_sha -ceq $checked -and $plan.since_pr -ceq '900' -and $plan.build -ceq $build2)
        Check '2 прогнане за записами (#11) не повернулося' (-not @($left | Where-Object { $_ -clike "scenes|11|*" }).Count -and $plan.ran.'901' -eq 1)
        Check '2 відмова (#12) і запис без прогону (#13) лишились, хоч PR не прочитано' ("scenes|12|$B|q12" -in $left -and "scenes|13|$C|q13" -in $left)
        Check '2 «у хмарі» (#14) і вадний рядок (#15) лишились' ("cloud|14|$E|q14" -in $left -and @($left | Where-Object { $_ -clike 'bad|15|*' }).Count -eq 1)
        Check '2 #16, оновлений після звіту, — з тіла: нове питання, старого нема' ("scenes|16|$D|q16 нове" -in $left -and "scenes|16|$C|q16" -notin $left)
        Check '2 злиття після збірки звіту (#17, #18) у плані, покрите межею (#10) — ні' ("scenes|17|$A|q17" -in $left -and "scenes|18|$D|q18" -in $left -and -not @($left | Where-Object { $_ -clike '*|10|*' }).Count)
        Check '2 merge нового плану має давні PR з джерела' ($plan.merge.'13' -ceq $merge[13] -and $plan.merge.'15' -ceq $merge[15])
    }
    Scenario '3 план без злиття хоч одного PR — не джерело' {
        $report.head.sha = $headNoMerge
        try { $plan = Plan-Run $build2 } finally { $report.head.sha = $headNew }
        Check '3 читання до повної межі, склад той самий' ($script:AutoApiCalls -eq $script:Before -and ((Pairs $plan) -join ';') -ceq ($script:FullPairs -join ';'))
    }
    Scenario '4 звіт межі змінено після плану звіту — джерело не переносить старої межі' {
        $keep = @($boundary.body, $boundary.updated_at)
        $boundary.body = 'Межу знято'; $boundary.updated_at = '2026-01-05T12:00:00Z'
        Serve $now '2026-01-06T00:00:00Z'
        try { $plan = Plan-Run $build2; $fullNoBoundary = Pairs (Plan-Run $build2 -Full) }
        finally { $boundary.body, $boundary.updated_at = $keep; Serve $now '2026-01-06T00:00:00Z' }
        Check '4 без межі #10 повертається, склад як після повного читання' ("scenes|10|$A|q10" -in (Pairs $plan) -and ((Pairs $plan) -join ';') -ceq ($fullNoBoundary -join ';') -and -not $plan.since_sha)
    }
} finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^mezha-chyt-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
if ($bad) { exit 1 }
