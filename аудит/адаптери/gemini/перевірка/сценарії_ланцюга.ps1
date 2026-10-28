#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$utf = New-Object Text.UTF8Encoding($false)
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ('e0-chain-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmpRoot)
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Один результат стенда, без прихованих відмов. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:failures++ }
}
try {
    $seed = Join-Path $tmpRoot 'seed'; $remote = Join-Path $tmpRoot 'origin.git'
    & git init -q --bare $remote; & git init -q -b main $seed
    & git -C $seed config user.name 'стенд'; & git -C $seed config user.email 'stend@example.invalid'
    & git -C $seed remote add origin $remote
    foreach ($dir in @('аудит/наряди','аудит/адаптери/gemini','джерела')) { [void][IO.Directory]::CreateDirectory((Join-Path $seed $dir)) }
    Copy-Item -LiteralPath (Join-Path $SourceDir 'ланцюг.json') -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
    foreach ($task in @('автоперевірка','автоживий')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md", $task, $utf) }
    [IO.File]::WriteAllText("$seed/джерела/a.py", '1', $utf)
    & git -C $seed add -A; & git -C $seed commit -q -m 'початкова'; & git -C $seed push -q origin main
    $bare = Join-Path $tmpRoot 'repo.git'; & git clone -q --bare $remote $bare
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmpRoot/pub" -OutboxDir "$tmpRoot/out" -UpdateRoot "$tmpRoot/update"
    foreach ($d in @($WorkDir, (Join-Path $WorkDir 'seen'), $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
    $script:Repo = $bare; $script:NoHooks = Join-Path $tmpRoot 'no-hooks'
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    $first = Get-RefSha 'refs/remotes/origin/main'
    $script:RealModelsCheck = (Get-Command Test-LiveModels).ScriptBlock
    $script:OriginalGetPulls = (Get-Command Get-ChainPulls).ScriptBlock
    $script:Pulls = @(); $script:Ready = $false
    function Get-ChainPulls { $script:Pulls }
    function Test-LiveModels($Config) { $script:Ready }
    function Pull([int]$Number, [string]$Branch, [string]$Sha, [string]$Owner = 'mightyrochy', [string]$Repository = 'mightyrochy/kod-shi-data') {
        <# Дані API; довільного тексту в позначки не передаємо. #>
        [pscustomobject]@{ number=$Number; user=@{login=$Owner}; head=@{ref=$Branch;sha=$Sha;repo=@{full_name=$Repository}}; base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}} }
    }
    $script:Pulls = @((Pull 12 'claude/наряд' $first), (Pull 13 'codex/наряд' $first), (Pull 14 'gemini/наряд' $first), (Pull 15 'claude/чужий' $first 'чужий'), (Pull 16 'claude/форк' $first 'mightyrochy' 'чужий/форк'), (Pull 17 "gemini/автоперевірка-12-$first" $first))
    Invoke-WrapperChain
    function Markers { @(& git -C $remote for-each-ref '--format=%(refname)' refs/heads/gemini-queue/) }
    Check 'готові PR автоматично отримали незалежні рушії, каскад Gemini — обидва' ((Markers).Count -eq 4)
    Check 'чужий автор, форк та автозвіт не породили нарядів' (@(Markers | Where-Object { $_ -match 'автоперевірка-(15|16|17)-' }).Count -eq 0)
    Invoke-WrapperChain
    Check 'повтор після перезапуску не дублює позначки' ((Markers).Count -eq 4)
    $file = Join-Path $WorkDir 'chain.json'; Remove-Item -LiteralPath $file
    Invoke-WrapperChain
    Check 'втрата локального списку не перезаписує наявні позначки' ((Markers).Count -eq 4)
    function Merge([string]$Path, [string]$Text) {
        <# Злитий стан main і наступний справжній fetch публікатора. #>
        [IO.File]::WriteAllText((Join-Path $seed $Path), $Text, $utf)
        & git -C $seed add -A; & git -C $seed commit -q -m 'злиття'; & git -C $seed push -q origin main
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        Get-RefSha 'refs/remotes/origin/main'
    }
    $docs = Merge 'опис.md' 'документ'; Invoke-WrapperChain
    Check 'документація не займає GPU' (@(Markers | Where-Object { $_ -match 'автоживий-' }).Count -eq 0)
    $product = Merge 'джерела/a.py' '2'; Invoke-WrapperChain
    $state = ConvertFrom-Json ([IO.File]::ReadAllText($file))
    Check 'злиття продукту збережене в очікуванні моделей' ($state.pending -ceq $product)
    $newer = Merge 'джерела/a.py' '3'; Invoke-WrapperChain
    $script:Ready = $true; Invoke-WrapperChain
    Check 'кілька злиттів зібрані в одну GPU-позначку після доступу моделей' (@(Markers | Where-Object { $_ -match "автоживий-$newer/.*/1/p2-gpu$" }).Count -eq 1)
    Invoke-WrapperChain
    Check 'живий прогін не дублюється' (@(Markers | Where-Object { $_ -match 'автоживий-' }).Count -eq 1)
    $script:Pulls = @((Pull 12 'claude/наряд' $newer)); Invoke-WrapperChain
    Check 'нова голова PR отримала нову перевірку' (@(Markers | Where-Object { $_ -match "автоперевірка-12-$newer/" }).Count -eq 1)
    # Справжня постановка PR-завдання та POST із підміною лише gh.
    $draftBranch = 'gemini/готовий'
    [void](Invoke-Git @('push','-q','origin',"${newer}:refs/heads/$draftBranch"))
    $script:NativeOriginal = (Get-Command Invoke-Native).ScriptBlock
    $script:DraftPosts = 0; $script:GhExe = 'fake-gh'
    function Resolve-Exe([string]$Name) { $Name }
    function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDirectory = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) {
        if ($Exe -eq 'fake-gh') {
            $body = ConvertFrom-Json $StdIn
            if ($body.draft -ne $true -or $body.base -ne 'main' -or $body.head -ne 'gemini/готовий') { throw 'невірне тіло PR' }
            $script:DraftPosts++
            return [pscustomobject]@{Code=0;Out='{"number":101}';Err=''}
        }
        & $script:NativeOriginal $Exe $Arguments $WorkDirectory $TimeoutMinutes $StdIn
    }
    Save-DraftRequest $draftBranch $newer
    Complete-EngineDrafts
    Complete-EngineDrafts
    Check 'DONE створює PR-чернетку сам, повтор POST відсутній' ($script:DraftPosts -eq 1 -and @(Get-ChildItem "$WorkDir/drafts/*.json").Count -eq 0)
    # Сторінки API розгортаються без втрати після першої сотні.
    $script:ApiPages = 0
    function Invoke-ChainApi([string]$Path) { $script:ApiPages++; if ($script:ApiPages -eq 1) { 1..100 } else { 101 } }
    Check 'відкриті PR читаються з усіх сторінок API' (@(& $script:OriginalGetPulls).Count -eq 101 -and $script:ApiPages -eq 2)
    $script:ModelCatalog = @([pscustomobject]@{key='qwen/qwen3.5-9b';loaded_instances=@()}, [pscustomobject]@{key='mamaylm-gemma-3-12b-it-v2.0';loaded_instances=@()})
    function Invoke-RestMethod { [pscustomobject]@{models=$script:ModelCatalog} }
    $cfg = ConvertFrom-Json ([IO.File]::ReadAllText((Join-Path $SourceDir 'ланцюг.json')))
    Check 'каталог незавантажених моделей допускає постановку без двох моделей у VRAM' ([bool](& $script:RealModelsCheck $cfg))
    $script:ModelCatalog = @($script:ModelCatalog[0])
    Check 'однієї доступної моделі недостатньо' (-not [bool](& $script:RealModelsCheck $cfg))
    function Invoke-RestMethod { throw 'сервер недоступний' }
    Check 'недоступний сервер лишає очікування' (-not [bool](& $script:RealModelsCheck $cfg))
    # Шаблони планувальників: повний SHA, ніякого вільного тексту з API.
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    Check 'обидва планувальники можуть узяти шаблон автонаряду' ((Get-AutoTaskPath "автоперевірка-12-$newer") -ceq 'аудит/наряди/автоперевірка.md' -and (Add-AutoTaskContext "автоживий-$newer" 'текст') -match $newer)
    $script:DryRun = $true; $script:Pulls = @((Pull 99 'claude/наряд' $newer)); Invoke-WrapperChain
    Check 'DryRun нічого не ставить' (@(Markers | Where-Object { $_ -match 'автоперевірка-99-' }).Count -eq 0)
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmpRoot) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmpRoot) -cmatch '^e0-chain-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmpRoot -Recurse -Force }
}
if ($failures) { exit 1 }
