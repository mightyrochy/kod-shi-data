#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('marker-end-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожна перевірка впливає на код виходу стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir,"$WorkDir/state","$WorkDir/seen",$OutDir,$OutboxDir,"$tmp/claude-run/runs")) { [void][IO.Directory]::CreateDirectory($dir) }
    $seed = "$tmp/seed"; $remote = "$tmp/origin.git"
    & git init -q --bare $remote
    & git init -q -b main $seed
    & git -C $seed config user.name 'Стенд'
    & git -C $seed config user.email 'stand@example.invalid'
    & git -C $seed config core.autocrlf false
    & git -C $seed remote add origin $remote
    foreach ($dir in @('аудит/наряди','аудит/адаптери/gemini')) { [void][IO.Directory]::CreateDirectory("$seed/$dir") }
    Copy-Item -LiteralPath "$SourceDir/ланцюг.json" -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
    foreach ($task in @('автоживий','автоперевірка')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md",$task,$utf) }
    & git -C $seed add -A
    & git -C $seed commit -qm 'База'
    & git -C $seed push -q origin main
    $script:Repo = "$seed/.git"; $script:NoHooks = "$tmp/no-hooks"
    function Build {
        <# Нова збірка має власний штамп і проходить справжній fetch. #>
        $stamp = (& git -C $seed rev-parse HEAD).Trim()
        [IO.File]::WriteAllText("$seed/build.txt",$stamp,$utf)
        & git -C $seed add -A
        & git -C $seed commit -qm 'Збірка'
        & git -C $seed push -q origin main
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        $stamp
    }
    function Get-ChainPulls { @() }
    function Complete-EngineDrafts { }
    function Test-LiveModels { $true }
    function Remove-DeadReviewMarkers { }
    function Move-BlockedMarkers { $false }
    function LiveMarkers { @(& git -C $remote for-each-ref '--format=%(refname)' refs/heads/gemini-queue/ | Where-Object { $_ -like '*/автоживий-*' }) }
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    Invoke-WrapperChain
    foreach ($engine in @('claude','codex','agy')) {
        $first = Build; Invoke-WrapperChain
        $middle = Build; Invoke-WrapperChain
        $latest = Build; Invoke-WrapperChain
        $count = @(LiveMarkers).Count
        $active = [pscustomobject]@{stamp=$first;published=$true}
        $branch = if ($engine -eq 'claude') { "claude/автоживий-$($first.Substring(0,8))" } elseif ($engine -eq 'codex') { "codex/автоживий-$first" } else { 'gemini/довільний-звіт' }
        $head = (& git -C $seed rev-parse HEAD).Trim()
        $report = "$WorkDir/state/$engine.json"
        # Гілка активного штампу при чужій позначці не закінчує роботу.
        Write-FileAtomic $report ((@{slug="автоживий-$latest";line="GEMINI ОБГОРТКА: ГОТОВО $branch $head"}) | ConvertTo-Json)
        Check "$engine чужий штамп у позначці — не кінець" (-not (Get-LiveCompletion $active))
        Invoke-WrapperChain
        Check "$engine чужий штамп не відкриває наступного прогону" (@(LiveMarkers).Count -eq $count)
        Remove-Item -LiteralPath $report
        if ($engine -eq 'claude') {
            $run = "$tmp/claude-run/runs/старий-формат"
            [void][IO.Directory]::CreateDirectory($run)
            Write-FileAtomic "$run/result.json" ((@{marker="gemini-queue/автоживий-$first/cc-claude-test/1/p2-gpu";code='DONE';branch=$branch;head=$head;end=[datetime]::UtcNow.ToString('s')}) | ConvertTo-Json)
        } else {
            Write-FileAtomic $report ((@{slug="автоживий-$first";line="GEMINI ОБГОРТКА: ГОТОВО $branch $head";sent=$true;attempts=0}) | ConvertTo-Json)
        }
        Check "$engine назва позначки визначає кінець" ([bool](Get-LiveCompletion $active))
        Invoke-WrapperChain
        $markers = @(LiveMarkers)
        Check "$engine наступна позначка — лише останній штамп" ($markers.Count -eq $count + 1 -and @($markers | Where-Object { $_ -like "*/автоживий-$latest/*" }).Count -eq 1 -and @($markers | Where-Object { $_ -like "*/автоживий-$middle/*" }).Count -eq 0)
        Invoke-WrapperChain
        Check "$engine повтор проходу не дублює позначку" (@(LiveMarkers).Count -eq $markers.Count)
        Write-FileAtomic "$WorkDir/state/blocked-$engine.json" ((@{slug="автоживий-$latest";line='GEMINI ОБГОРТКА: ЗАБЛОКОВАНО codex/короткий BLOCKED'}) | ConvertTo-Json)
        Check "$engine ЗАБЛОКОВАНО — кінець за позначкою" ([bool](Get-LiveCompletion ([pscustomobject]@{stamp=$latest;published=$true})))
        Invoke-WrapperChain
    }
    $removed = Build; Invoke-WrapperChain
    foreach ($ref in @(LiveMarkers | Where-Object { $_ -like "*/автоживий-$removed/*" })) { & git -C $seed push -q origin ":$ref" }
    $run = "$tmp/claude-run/runs/квота"
    [void][IO.Directory]::CreateDirectory($run)
    Write-FileAtomic "$run/result.json" ((@{marker="gemini-queue/автоживий-$removed/cc-claude-test/1/p2-gpu";code='QUOTA_WAIT'}) | ConvertTo-Json)
    # Віддалену позначку вже прибрано: окремо перевіряємо, що QUOTA_WAIT не є результатом.
    Check 'очікування квоти не є кінцем смуги' (-not (Get-ChainTaskCompletion "автоживий-$removed"))
    $netRun = "$tmp/claude-run/runs/мережа"
    [void][IO.Directory]::CreateDirectory($netRun)
    Write-FileAtomic "$netRun/result.json" ((@{marker="gemini-queue/автоживий-$removed/cc-claude-test/1/p2-gpu";code='NETWORK_WAIT'}) | ConvertTo-Json)
    Check 'обрив мережі не є кінцем смуги' (-not (Get-ChainTaskCompletion "автоживий-$removed"))
    Write-FileAtomic "$WorkDir/state/quota.json" ((@{line="GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/автоживий-$removed QUOTA0_CLAUDE_M60"}) | ConvertTo-Json)
    Check 'прийнятий ЗАБЛОКОВАНО за позначкою очікування квоти — кінець' ([bool](Get-ChainTaskCompletion "автоживий-$removed"))
    Remove-Item -LiteralPath "$WorkDir/state/quota.json"
    Check 'прибрана позначка — кінець' ([bool](Get-LiveCompletion ([pscustomobject]@{stamp=$removed;published=$true})))
    Check 'неопублікований резерв без позначки — ще не кінець' (-not (Get-LiveCompletion ([pscustomobject]@{stamp=('f'*40);published=$false})))
    $reviewHead = 'a'*40
    Write-FileAtomic "$WorkDir/state/review.json" ((@{slug="автоперевірка-9-$reviewHead";line="GEMINI ОБГОРТКА: ГОТОВО codex/коротка-перевірка $reviewHead"}) | ConvertTo-Json)
    Check 'автоперевірка впізнає скорочену гілку за позначкою' (Test-ChainReviewDone '9' $reviewHead)
    Check 'чужа голова позначки не закриває автоперевірку' (-not (Test-ChainReviewDone '9' ('b'*40)))
    Check 'публікатор будить диспетчера за позначкою короткого звіту' (Test-DispatcherAction "GEMINI ОБГОРТКА: ГОТОВО codex/коротка-перевірка $reviewHead")
    # Прийнятий рядок Codex/agy переносить slug із джерела й зберігає його в усіх каналах доставки.
    $id = '20261101-230000-0123456789ab'
    $slug = "автоживий-$reviewHead"
    $line = "GEMINI ОБГОРТКА: ГОТОВО codex/короткий-звіт $reviewHead"
    Write-FileAtomic "$WorkDir/state/$id.json" ((@{line='';slug=$slug;sent=$true;attempts=0;outbox="$id.txt"}) | ConvertTo-Json)
    Add-OutboxLine "$id.txt" $line
    Receive-Outbox
    $path = "$WorkDir/state/o-$id.json"
    $state = ConvertFrom-Json ([IO.File]::ReadAllText($path,$utf))
    Check 'Receive-Outbox переносить назву позначки' ($state.slug -ceq $slug)
    function Send-LineRetry { [pscustomobject]@{Ok=$true;Tries=1} }
    Send-Pending (Get-Item -LiteralPath $path)
    $state = ConvertFrom-Json ([IO.File]::ReadAllText($path,$utf))
    Check 'доставка хмарою не стирає назву позначки' ($state.slug -ceq $slug -and $state.sent -and $state.channel -ceq 'claude')
    $line = "GEMINI ОБГОРТКА: ГОТОВО gemini/звичайний $reviewHead"
    Write-FileAtomic "$WorkDir/state/local.json" ((@{line=$line;slug='звичайний';sent=$false;attempts=0}) | ConvertTo-Json)
    Send-Pending (Get-Item -LiteralPath "$WorkDir/state/local.json")
    $state = ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/state/local.json",$utf))
    Check 'локальна доставка не стирає назву позначки' ($state.slug -ceq 'звичайний' -and $state.channel -ceq 'local')
    # Старий опублікований стан без slug відновлюється через id, а не назву гілки звіту.
    $legacyId = '20261101-230001-0123456789ab'
    Write-FileAtomic "$OutDir/$legacyId.json" ((@{slug="автоперевірка-10-$reviewHead"}) | ConvertTo-Json)
    Write-FileAtomic "$WorkDir/state/o-$legacyId.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/автоперевірка-10-$reviewHead $reviewHead"}) | ConvertTo-Json)
    Check 'старий стан Codex/agy відновлює позначку за id' (Test-ChainReviewDone '10' $reviewHead)
    # Відкладений кінець: DONE з'являється у стані позначки між двома зверненнями до нього — зняття не губиться (стан читається раз).
    & {
        $q = 'gemini-queue/гонка/cc-test/1'; $m = 'c' * 40; $rid = '20261101-230002-0123456789ab'; $key = "refs/remotes/origin/$q $m"
        $script:StateReads = 0; $orig = ${function:Get-Sha256Hex}
        $sd = Join-Path $OutDir 'marker-state'; [void][IO.Directory]::CreateDirectory($sd)
        $sf = Join-Path $sd ((& $orig $key) + '.txt')
        $pending = Join-Path (Join-Path $WorkDir 'finish-pending') ((& $orig "$q $m $rid") + '.txt')
        function Get-RefSha { param($Ref) $m }
        function Get-Sha256Hex([string]$Text) {
            if ($Text -ceq $key) {
                $script:StateReads++
                if ($script:StateReads -eq 2) { Write-FileAtomic $sf "DONE $rid DONE" }
            }
            & $orig $Text
        }
        function Test-Finished { @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'finished') -Filter '*.txt' -File -ErrorAction SilentlyContinue | Where-Object { ([IO.File]::ReadAllText($_.FullName, $utf)).Trim() -ceq "$q $m" }).Count -gt 0 }
        Write-FileAtomic $sf 'STARTED {}'
        Add-PublishedMarker $q $m $rid 'DONE'
        Check 'JSON раніше за DONE: кінець відкладено, позначки до зняття ще нема' ((Test-Path -LiteralPath $pending) -and -not (Test-Finished))
        $script:StateReads = 0
        Confirm-PendingMarkers
        Check 'стан позначки читається раз за запис, а DONE між читаннями не відкидає відкладеного' ($script:StateReads -eq 1 -and (Test-Path -LiteralPath $pending) -and -not (Test-Finished))
        Write-FileAtomic $sf "DONE $rid DONE"
        Confirm-PendingMarkers
        Check 'після появи DONE відкладений кінець дає запис на зняття' ((Test-Finished) -and -not (Test-Path -LiteralPath $pending))
    }
    $script:RemoteFailure = $false
    function Invoke-Git { [pscustomobject]@{Code=1;Out='';Err='стенд мережі'} }
    try { [void](Get-LiveCompletion ([pscustomobject]@{stamp=('e'*40);published=$true})) } catch { $script:RemoteFailure = $_.Exception.Message -ceq 'CHAIN_REMOTE' }
    Check 'збій GitHub не видається за прибрану позначку' $script:RemoteFailure
    # Мережа після сну: ls-remote не питає в неї, доки ім'я вузла не розв'язується; збій при живій мережі лишає текст git у журналі.
    & {
        $script:NetChecks = 0; $script:LsCalls = 0; $script:NetUpAfter = 2; $script:LsErr = ''
        $keepDelay = $script:SendRetryDelaySeconds; $script:SendRetryDelaySeconds = 0
        function Test-ChainNetwork { $script:NetChecks++; $script:NetChecks -gt $script:NetUpAfter }
        function Invoke-Git {
            if ($args[0][0] -ceq 'remote') { return [pscustomobject]@{Code=0;Out='https://x-access-token:секрет@github.com/o/r.git';Err=''} }
            $script:LsCalls++
            if ($script:NetChecks -gt $script:NetUpAfter -and -not $script:LsErr) { return [pscustomobject]@{Code=0;Out='';Err=''} }
            [pscustomobject]@{Code=128;Out='';Err=$(if ($script:LsErr) { $script:LsErr } else { 'fatal: unable to access: Could not resolve host: github.com' })}
        }
        $active = [pscustomobject]@{stamp=('e'*40);published=$true}
        $threw = ''
        try { [void](Get-LiveCompletion $active) } catch { $threw = [string]$_.Exception.Message }
        "ДАНІ мережа-ще-нема: виняток='$threw' ls-remote=$($script:LsCalls) перевірок мережі=$($script:NetChecks)"
        Check 'мережа ще не встала: прохід чекає й ls-remote проходить без CHAIN_REMOTE' ($threw -ceq '' -and $script:LsCalls -eq 1 -and $script:NetChecks -eq 3)
        $script:NetChecks = 0; $script:LsCalls = 0; $script:NetUpAfter = -1; $script:LsErr = "remote: Repository not found.`nfatal: https://x-access-token:секрет@github.com/o/r.git"
        $log = "$WorkDir/publish.log"; $before = [IO.File]::ReadAllText($log, $utf).Length
        $threw = ''
        try { [void](Get-LiveCompletion $active) } catch { $threw = [string]$_.Exception.Message }
        $added = [IO.File]::ReadAllText($log, $utf).Substring($before)
        "ДАНІ мережа-жива: виняток='$threw' ls-remote=$($script:LsCalls) журнал=[$($added.Trim())]"
        Check 'мережа жива, ls-remote падає: CHAIN_REMOTE без повторів, текст git у журналі' ($threw -ceq 'CHAIN_REMOTE' -and $script:LsCalls -eq 1 -and $added.Contains('Repository not found') -and $added.Contains('код 128'))
        Check 'журнал не несе даних входу з адреси' (-not $added.Contains('секрет'))
        $script:SendRetryDelaySeconds = $keepDelay
    }
    & {
        . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$tmp/claude-run" -OutboxDir "$tmp/claude-out" -LaneDir "$tmp/claude-lanes"
        $script:ResultBeforeLine = $false
        function Add-Line {
            $script:ResultBeforeLine = Test-Path -LiteralPath "$tmp/claude-run/runs/ранній/result.json"
            $true
        }
        function Remove-Claim { }
        function Write-Log { }
        $m = [pscustomobject]@{Name="gemini-queue/автоживий-$reviewHead/cc-claude-test/1/p2-gpu";Slug="автоживий-$reviewHead";Sha=$reviewHead;Model='cc-claude-test'}
        Complete-Task $m "$tmp/claude-state.txt" 'ранній' 'BLOCKED'
        $result = ConvertFrom-Json ([IO.File]::ReadAllText("$tmp/claude-run/runs/ранній/result.json",$utf))
        Check 'рання відмова Claude зберігає позначку до рядка вихідних' ($script:ResultBeforeLine -and $result.marker -ceq $m.Name -and $result.code -ceq 'BLOCKED')
    }

} finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    if ((Split-Path -Parent $resolved) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $resolved) -cmatch '^marker-end-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
"Провалів: $bad"
if ($bad) { exit 1 }
