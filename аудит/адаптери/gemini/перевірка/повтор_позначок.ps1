#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('review-retry-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Результат кожної сцени визначає код виходу. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/update"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir,$OutboxDir,"$WorkDir/seen","$OutDir/marker-state")) { [void][IO.Directory]::CreateDirectory($dir) }
    Write-FileAtomic "$OutDir/marker-state/ready" '1'
    $seed = "$tmp/seed"; $remote = "$tmp/origin.git"
    & git init -q --bare $remote
    & git init -q -b main $seed
    & git -C $seed config user.name 'Стенд'
    & git -C $seed config user.email 'stand@example.invalid'
    & git -C $seed remote add origin $remote
    [IO.File]::WriteAllText("$seed/проба.txt", 'база', $utf)
    foreach ($dir in @('аудит/наряди','аудит/адаптери/gemini')) { [void][IO.Directory]::CreateDirectory((Join-Path $seed $dir)) }
    Copy-Item -LiteralPath (Join-Path $SourceDir 'ланцюг.json') -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
    foreach ($task in @('автоперевірка','автоживий')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md", $task, $utf) }
    & git -C $seed add -A
    & git -C $seed commit -qm 'База'
    & git -C $seed push -q origin main
    $head = (& git -C $seed rev-parse HEAD).Trim()
    $script:Repo = "$seed/.git"; $script:NoHooks = "$tmp/no-hooks"
    $script:BlockedModels = @()
    function Test-ModelQuota([string]$Model, $Now) { $Model -cin $script:BlockedModels }
    function Test-ChainCodePull { $true }
    function Marker([int]$Pr, [int]$Attempt, [string]$State = '', [string]$Model = 'gpt-6.1-terra-high', [string]$Cond = 'p1') {
        <# Справжня віддалена позначка й стан за тим самим ключем, що читає смуга. #>
        $name = "gemini-queue/автоперевірка-$Pr-$head/$Model/$Attempt/$Cond"
        & git -C $seed push -q origin "${head}:refs/heads/$name"
        $key = "refs/remotes/origin/$name $head"
        $sp = Join-Path "$OutDir/marker-state" ((Get-Sha256Hex $key) + '.txt')
        if ($State) { Write-FileAtomic $sp $State }
        [pscustomobject]@{Name=$name;Path=$sp}
    }
    function Clean([int]$Pr) {
        <# Очищення працює зі справжнім bare origin, API замінено лише даними PR. #>
        $pull = [pscustomobject]@{number=$Pr;title='Код';user=@{login='mightyrochy'};
            head=@{ref='claude/проба';sha=$head;repo=@{full_name=$GitHubRepo}};
            base=@{ref='main';repo=@{full_name=$GitHubRepo}}}
        Remove-DeadReviewMarkers @($pull) @{} ([datetimeoffset]::UtcNow)
    }
    function Refs([int]$Pr) { @(& git -C $remote for-each-ref '--format=%(refname)' "refs/heads/gemini-queue/автоперевірка-$Pr-$head/") }
    function Take {
        <# Справжній Start-Markers і claim; запуск моделі замінено записом узятої позначки. #>
        . (Join-Path $SourceDir 'queue_lanes.ps1')
        $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'gemini_run.ps1'), [ref]$null, [ref]$errors)
        if ($errors.Count) { throw 'Синтаксис планувальника' }
        $f = $ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Start-Markers'}, $false)
        . ([scriptblock]::Create($f.Extent.Text))
        $LaneDir = "$tmp/lane"; [void][IO.Directory]::CreateDirectory($LaneDir)
        $script:StateDir = "$OutDir/marker-state"
        $script:Lanes = @('codex','agy'); $script:Limits = @{slots=@{codex=8;agy=8}}
        $script:StartedNames = @(); $RunsDir = $GeminiRunsDir; $RepoDir = $seed; $MarkerMaxAgeDays = 7
        function Save-Skips { }
        function Add-Skip { }
        function Test-SlugBusy { $false }
        function Select-Engine { [pscustomobject]@{Engine=@{Name='codex';Model='test';Effort='high'};Model='test';Quota=@{Blocked=$false;Known=$false;Left=100;Group='test'}} }
        function Get-FreeSlot { '1' }
        function New-RunId { [guid]::NewGuid().ToString('N') }
        function Start-Worker($Job, $Dir) { $script:StartedNames += $Job.name; [pscustomobject]@{Slug=$Job.slug;Proc=@{HasExited=$false}} }
        function Write-Log { }
        function Close-FailedStart { throw 'Не вдалося взяти позначку' }
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*','--prune'))
        $workers = New-Object Collections.ArrayList
        [void](Start-Markers $workers)
        @($script:StartedNames)
    }
    $old = Marker 101 1 'DONE BLOCKED'
    $new = Marker 101 2
    Clean 101
    $refs = @(Refs 101)
    Check 'кінцева /1 знята, нова /2 лишилась' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($new.Name)")
    $taken = @(Take)
    Check 'смуга взяла саме /2' ($taken.Count -eq 1 -and $taken[0] -ceq $new.Name -and (Test-Path ($new.Path -replace '\.txt$', '.claim')))
    $a = Marker 102 1
    $b = Marker 102 2
    Clean 102
    $refs = @(Refs 102)
    Check 'дві нові: лишилась одна /2' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($b.Name)")
    $a = Marker 103 2
    $b = Marker 103 10
    Clean 103
    $refs = @(Refs 103)
    Check 'числовий порядок: /10 перемагає /2' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($b.Name)")
    $a = Marker 104 1 'STALE'
    $b = Marker 104 2 ('WAIT ' + (@{until=[datetimeoffset]::UtcNow.AddHours(1).ToUnixTimeSeconds();retakes=0} | ConvertTo-Json -Compress))
    Clean 104
    $refs = @(Refs 104)
    Check 'STALE не заступає WAIT до скидання квоти' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($b.Name)")
    $script:BlockedModels = @('gpt-6.1-terra-high')
    $a = Marker 105 10 '' 'gpt-6.1-terra-high'
    $b = Marker 105 2 '' 'gemini-4-argon-high'
    Clean 105
    $refs = @(Refs 105)
    Check 'серед нових доступний постачальник важливіший за номер' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($b.Name)")
    $a = Marker 106 1 'DONE BLOCKED' 'gemini-4-argon-high'
    $b = Marker 106 2 '' 'gpt-6.1-terra-high'
    Clean 106
    $refs = @(Refs 106)
    Check 'кінцева доступна модель не заступає нову на квоті' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($b.Name)")
    $script:BlockedModels = @()
    $a = Marker 107 1 'STARTED {}'
    Write-FileAtomic ($a.Path -replace '\.txt$', '.claim') 'активна'
    $b = Marker 107 2
    Clean 107
    $refs = @(Refs 107)
    Check 'узята спроба зберігається без другого запуску' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($a.Name)")
    $a = Marker 108 2 '' 'gpt-6.1-terra-high' 'p1'
    $b = Marker 108 10 '' 'gpt-6.1-terra-high' 'p2'
    Clean 108
    $once = @(Refs 108); Clean 108; $twice = @(Refs 108)
    Check 'інший пріоритет не міняє числовий вибір; повтор сталий' ($once.Count -eq 1 -and $once[0] -ceq "refs/heads/$($b.Name)" -and ($once -join '') -ceq ($twice -join ''))
    $script:BlockedModels = @('gpt-6.1-terra-high')
    $a = Marker 109 1 'DONE BLOCKED' 'gemini-4-argon-high'
    $b = Marker 109 2 '' 'gpt-6.1-terra-high'
    Check 'перенесення в хмару ігнорує кінцеву доступну модель' (Test-CloudMove "автоперевірка-109-$head" ([datetimeoffset]::UtcNow))
    $a = Marker 110 1 'STARTED {}'
    Write-FileAtomic ($a.Path -replace '\.txt$', '.claim') 'активна'
    Check 'квота не переносить уже взяту перевірку в хмару' (-not (Test-CloudMove "автоперевірка-110-$head" ([datetimeoffset]::UtcNow)))
    $b = Marker 110 2 '' 'gemini-4-argon-high'
    Check 'перенесення між смугами не знімає вже взяту перевірку' (-not (Move-BlockedMarkers "автоперевірка-110-$head" 'gemini-4-argon-high' $head ([datetimeoffset]::UtcNow)))
    $a = Marker 111 1 'DONE BLOCKED' 'gemini-4-argon-high' 'p2'
    $b = Marker 111 2 '' 'gpt-6.1-terra-high'
    $moved = Move-BlockedMarkers "автоперевірка-111-$head" 'gemini-4-argon-high' $head ([datetimeoffset]::UtcNow)
    $refs = @(Refs 111)
    Check 'перенесення /2 враховує стан і створює нову спробу постачальника' ($moved -and "refs/heads/gemini-queue/автоперевірка-111-$head/gemini-4-argon-high/2/p2" -cin $refs -and "refs/heads/$($b.Name)" -cnotin $refs)
    $a = Marker 112 1 'DONE BLOCKED'
    Check 'кінцевий стан сам не запускає перенесення' (-not (Move-BlockedMarkers "автоперевірка-112-$head" 'gemini-4-argon-high' $head ([datetimeoffset]::UtcNow)))
    # Виняток саме у функції з текстового блоку: без ScriptName, як у читачах стану ланцюга.
    $script:BlockedModels = @()
    $a = Marker 113 1
    $b = Marker 113 2
    $c = Marker 114 1
    $d = Marker 114 2
    $script:ChainStateReaders = @($script:ChainStateReaders | Where-Object { $_.ToString() -cnotmatch '^function Get-MarkerState\(' }) + @([scriptblock]::Create(@'
function Get-MarkerState($M, [string]$StateDir) {
    if ($M.Ref -cmatch 'автоперевірка-113-[0-9a-f]{40}/[^/]+/1/') { throw [UnauthorizedAccessException]::new('/закритий/стан') }
    [pscustomobject]@{ Kind='NEW'; Wait=$null }
}
'@))
    $script:ErrorPulls = @(foreach ($n in @(113,114)) {
        [pscustomobject]@{number=$n;title='Код';user=@{login='mightyrochy'};
            head=@{ref='claude/проба';sha=$head;repo=@{full_name=$GitHubRepo}};
            base=@{ref='main';repo=@{full_name=$GitHubRepo}}}
    })
    function Get-ChainPulls { $script:ErrorPulls }
    function Complete-EngineDrafts { }
    function Test-RecentReviewHead { $script:ReachedAfterStateRead = $true; $false }
    $script:ReachedAfterStateRead = $false
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    Invoke-WrapperChain
    $refs = @(Refs 113)
    Check 'помилка одного стану зберегла обидві позначки його голови' ($refs.Count -eq 2 -and "refs/heads/$($a.Name)" -cin $refs -and "refs/heads/$($b.Name)" -cin $refs)
    $refs = @(Refs 114)
    Check 'інша голова очищена попри виняток читача' ($refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/$($d.Name)")
    Check 'прохід ланцюга дійшов до кроку після очищення' $script:ReachedAfterStateRead
    $lines = @(Get-ChildItem -LiteralPath $OutboxDir -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName,$utf).Trim() } | Where-Object { $_ -cmatch '^GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED' })
    Check 'рядок винятку читача має тип і функцію першого кадру' (@($lines | Where-Object { $_ -clike 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED UnauthorizedAccessException Get-MarkerState ШЛЯХ *' }).Count -eq 1)
    $log = [IO.File]::ReadAllText((Join-Path $WorkDir 'publish.log'),$utf)
    Check 'журнал містить позначку, причину й стек читача' ($log -cmatch 'стан gemini-queue/автоперевірка-113-' -and $log.Contains('/закритий/стан') -and $log.Contains('at Get-MarkerState, <No file>'))
    Check 'невідомий стан не передається іншому постачальнику' (-not (Move-BlockedMarkers "автоперевірка-113-$head" 'gemini-4-argon-high' $head ([datetimeoffset]::UtcNow)))
    Check 'невідомий стан не передається у хмару' (-not (Test-CloudMove "автоперевірка-113-$head" ([datetimeoffset]::UtcNow)))
    Request-CloudReview 113 $head
    Check 'пряма хмарна передача також зберегла всю голову' (@(Refs 113).Count -eq 2 -and -not (Test-Path -LiteralPath (Get-SeenPath "cloud-review 113 $head")))
    Check 'публікатор приймає функцію й стару форму файл:рядок' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED UnauthorizedAccessException Get-MarkerState') -ceq '' -and (Test-OutboxLine 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED RuntimeException wrapper_chain.ps1:123') -ceq '')
    Check 'публікатор відхиляє шлях, текст і довгу назву функції' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED UnauthorizedAccessException C:\private\state') -cne '' -and (Test-OutboxLine 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED UnauthorizedAccessException Get-State extra') -cne '' -and (Test-OutboxLine ('GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED UnauthorizedAccessException ' + ('A' * 81))) -cne '')
    . ([scriptblock]::Create("function Get-ChainPulls { throw [InvalidOperationException]::new('/закритий/прохід') }"))
    Invoke-WrapperChain
    $lines = @(Get-ChildItem -LiteralPath $OutboxDir -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName,$utf).Trim() })
    Check 'загальний catch теж передав тип і функцію текстового блоку' (@($lines | Where-Object { $_ -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED InvalidOperationException Get-ChainPulls' }).Count -eq 1)

    # Окремий простір даних: справжні проходи ланцюга, refs, chain.json і хмарний вихід.
    & {
        . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/transfer/pub" -OutDir "$tmp/transfer/out" -OutboxDir "$tmp/transfer/outbox" -UpdateRoot "$tmp/transfer/update"
        $script:Repo = "$seed/.git"; $script:NoHooks = "$tmp/no-hooks"
        foreach ($dir in @($WorkDir,$OutboxDir,"$WorkDir/seen")) { [void][IO.Directory]::CreateDirectory($dir) }
        function Complete-EngineDrafts { }
        function Get-ChainBuildStamp { '' }
        function Get-ChainBranchWork { '' }
        function Test-RecentReviewHead { $true }
        function Test-ReviewedMerge { $false }
        function Test-ChainCodePull { $true }
        function Test-ChainEndAnnounced { $true }
        function Get-ChainPullRisk { 2 }
        function Test-ChainReviewDone { $false }
        function Get-ReviewDiff { 'проба' }
        function Get-ReviewPatchId { 'проба' }
        function Get-ReviewModels { @($script:TransferTarget) }
        function Test-ModelQuota([string]$Model, $Now) { $Model -ceq 'gpt-6.1-terra-high' }
        function Get-ChainPulls { $script:TransferPull }
        function Get-ChainMarkerState($Ref, $Sha, $Model) {
            if ($Ref.Contains("/$script:TransferSlug/")) {
                $script:TransferReads++
                if ($script:Unavailable -and ($script:FailAt -eq 0 -or $script:TransferReads -eq $script:FailAt)) {
                    throw [UnauthorizedAccessException]::new('тимчасово недоступний стан')
                }
            }
            [pscustomobject]@{ Kind=$script:TransferKind; Wait=$null }
        }
        function CloudLines([int]$Number) {
            @(Get-ChildItem -LiteralPath $OutboxDir -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName,$utf).Trim() } |
                Where-Object { $_ -ceq "GEMINI ОБГОРТКА: ПОТРІБНА ПЕРЕВІРКА CLAUDE #$Number $head" })
        }
        foreach ($case in @(
            @{Number=201;Target='gemini-4-argon-high';FailAt=0;Name='запасна модель'},
            @{Number=202;Target='claude-cloud';FailAt=0;Name='хмара: попереднє читання'},
            @{Number=203;Target='claude-cloud';FailAt=3;Name='хмара: повторне читання перед передачею'}
        )) {
            $n = $case.Number; $label = $case.Name
            $script:TransferTarget = $case.Target; $script:FailAt = $case.FailAt
            $script:TransferSlug = "автоперевірка-$n-$head"
            $old = "refs/heads/gemini-queue/$script:TransferSlug/gpt-6.1-terra-high/1/p2"
            & git -C $seed push -q origin "${head}:$old"
            $script:TransferPull = [pscustomobject]@{number=$n;title='Проба';user=@{login='mightyrochy'};
                head=@{ref='codex/проба';sha=$head;repo=@{full_name=$GitHubRepo}};
                base=@{ref='main';repo=@{full_name=$GitHubRepo}}}
            $statePath = Join-Path $WorkDir 'chain.json'
            $oldKey = "$n $head gpt-6.1-terra-high"; $key = "$n $head $script:TransferTarget"
            Write-FileAtomic $statePath (@{main=$head;reviewed=@{};reviews=@($oldKey)} | ConvertTo-Json -Depth 5)
            $script:Unavailable = $true; $script:TransferReads = 0; $script:TransferKind = 'WAIT'
            Invoke-WrapperChain
            $first = ConvertFrom-Json ([IO.File]::ReadAllText($statePath,$utf))
            Check "$label — відкладення не записане в seen і reviewed" ($key -cnotin @($first.reviews) -and $null -eq $first.reviewed.PSObject.Properties[[string]$n])
            $refs = @(Refs $n)
            Check "$label — UNKNOWN зберіг стару позначку без хмарної доставки" ($refs.Count -eq 1 -and $refs[0] -ceq $old -and @(CloudLines $n).Count -eq 0)
            $script:Unavailable = $false
            Invoke-WrapperChain
            $second = ConvertFrom-Json ([IO.File]::ReadAllText($statePath,$utf))
            $refs = @(Refs $n)
            $delivered = if ($script:TransferTarget -ceq 'claude-cloud') {
                $refs.Count -eq 0 -and @(CloudLines $n).Count -eq 1 -and (Test-Path -LiteralPath (Get-SeenPath "cloud-review $n $head"))
            } else {
                $refs.Count -eq 1 -and $refs[0] -ceq "refs/heads/gemini-queue/$script:TransferSlug/$script:TransferTarget/1/p2"
            }
            Check "$label — наступний прохід після відновлення фактично передав роботу" $delivered
            Check "$label — seen записаний після передачі" ($key -cin @($second.reviews) -and $null -ne $second.reviewed.PSObject.Properties[[string]$n])
            $beforeRefs = $refs -join '|'; $beforeLines = @(CloudLines $n).Count
            Invoke-WrapperChain
            Check "$label — третій прохід не дублює доставку" (((@(Refs $n) -join '|') -ceq $beforeRefs) -and @(CloudLines $n).Count -eq $beforeLines)
        }
        # Узяту роботу передавати не треба; це завершене рішення, на відміну від UNKNOWN.
        foreach ($target in @('gemini-4-argon-high','claude-cloud')) {
            $script:TransferTarget = $target; $script:TransferKind = 'TAKEN'
            $script:TransferSlug = "автоперевірка-204-$head"
            & git -C $seed push -q origin "${head}:refs/heads/gemini-queue/$script:TransferSlug/gpt-6.1-terra-high/1/p2"
            $result = if ($target -ceq 'claude-cloud') { Test-CloudMove $script:TransferSlug ([datetimeoffset]::UtcNow) }
                      else { Move-BlockedMarkers $script:TransferSlug $target $head ([datetimeoffset]::UtcNow) }
            Check "$target — узята робота повертає рішення не потрібна" ($null -ne $result -and $result -ceq $false)
        }
    }
} catch { Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\','/')
    if ((Split-Path -Parent $resolved) -ceq $parent -and (Split-Path -Leaf $resolved) -cmatch '^review-retry-[0-9a-f]{32}$') {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
"провалів: $bad"
if ($bad) { exit 1 }
