#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$root = Join-Path ([IO.Path]::GetTempPath()) ('review2912-seen-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($root)
$bad = 0
try {
    $seed = Join-Path $root 'seed'; $remote = Join-Path $root 'origin.git'
    & git init -q --bare $remote
    & git init -q -b main $seed
    & git -C $seed config user.name 'Перевірка'
    & git -C $seed config user.email 'review@example.invalid'
    & git -C $seed remote add origin $remote
    foreach ($dir in @('аудит/наряди','аудит/адаптери/gemini')) { [void][IO.Directory]::CreateDirectory((Join-Path $seed $dir)) }
    Copy-Item -LiteralPath (Join-Path $SourceDir 'ланцюг.json') -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
    foreach ($task in @('автоперевірка','автоживий')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md", $task, $utf) }
    & git -C $seed add -A
    & git -C $seed commit -qm 'База відтворення'
    & git -C $seed push -q origin main
    $head = (& git -C $seed rev-parse HEAD).Trim()
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$root/pub" -OutDir "$root/out" -OutboxDir "$root/outbox" -UpdateRoot "$root/update"
    $script:Repo = "$seed/.git"; $script:NoHooks = "$root/no-hooks"
    $GeminiRunsDir = "$root/gemini-runs"
    foreach ($dir in @($WorkDir,$OutboxDir,"$WorkDir/seen")) { [void][IO.Directory]::CreateDirectory($dir) }
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    # Справжні Invoke-WrapperChain, очищення, перенесення, refs і chain.json.
    # Зовнішні API, допуск PR і завершення моделі замінено детермінованими даними.
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
    function Get-ReviewModels { @($script:Target) }
    function Test-ModelQuota([string]$Model, $Now) { $Model -ceq 'gpt-6.1-terra-high' }
    function Get-ChainPulls { $script:Pull }
    function Get-ChainMarkerState {
        if ($script:Unavailable) { throw [UnauthorizedAccessException]::new('відтворення тимчасової відмови') }
        [pscustomobject]@{ Kind='WAIT'; Wait=$null }
    }
    foreach ($target in @('gemini-4-argon-high','claude-cloud')) {
        $script:Target = $target
        $n = $(if ($target -ceq 'claude-cloud') { 902 } else { 901 })
        $slug = "автоперевірка-$n-$head"
        $old = "refs/heads/gemini-queue/$slug/gpt-6.1-terra-high/1/p2"
        & git -C $seed push -q origin "${head}:$old"
        $script:Pull = [pscustomobject]@{number=$n;title='Проба';user=@{login='mightyrochy'};
            head=@{ref='codex/проба';sha=$head;repo=@{full_name=$GitHubRepo}};
            base=@{ref='main';repo=@{full_name=$GitHubRepo}}}
        $statePath = Join-Path $WorkDir 'chain.json'
        $oldKey = "$n $head gpt-6.1-terra-high"
        Write-FileAtomic $statePath (@{main=$head;reviewed=@{};reviews=@($oldKey)} | ConvertTo-Json -Depth 5)
        $script:Unavailable = $true
        Invoke-WrapperChain
        $first = ConvertFrom-Json ([IO.File]::ReadAllText($statePath,$utf))
        $key = "$n $head $target"
        $premature = $key -cin @($first.reviews)
        $script:Unavailable = $false
        Invoke-WrapperChain
        $refs = @(& git -C $remote for-each-ref '--format=%(refname)' "refs/heads/gemini-queue/$slug/")
        $cloudSent = Test-Path -LiteralPath (Get-SeenPath "cloud-review $n $head")
        $delivered = $(if ($target -ceq 'claude-cloud') { $cloudSent } else { @($refs | Where-Object { $_.Contains("/$target/") }).Count -gt 0 })
        $stuck = $premature -and -not $delivered -and $old -cin $refs
        "ціль=$target; передчасний_seen=$premature; доставлено_після_відновлення=$delivered; стара_позначка=$($old -cin $refs); дефект_відтворено=$stuck"
        if (-not $stuck) { $bad++ }
        # Контроль: той самий справжній механізм після відновлення вміє передати.
        if ($target -ceq 'claude-cloud') { Request-CloudReview $n $head; $control = Test-Path -LiteralPath (Get-SeenPath "cloud-review $n $head") }
        else { $control = Move-BlockedMarkers $slug $target $head ([datetimeoffset]::UtcNow) }
        "ціль=$target; пряма_передача_після_відновлення=$control"
        if (-not $control) { $bad++ }
    }
} finally {
    $resolved = [IO.Path]::GetFullPath($root)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\','/')
    if ((Split-Path -Parent $resolved) -ceq $parent -and (Split-Path -Leaf $resolved) -cmatch '^review2912-seen-[0-9a-f]{32}$') {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
"невідтворених випадків: $bad"
if ($bad) { exit 1 }
