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
    function Invoke-ChainApi([string]$Path) {
        if ($Path -match '/files\?') { return [pscustomobject]@{filename='джерела/a.py'} }
        $sha = ($Path -split '/')[-1]
        [pscustomobject]@{sha=$sha;commit=@{committer=@{date=[datetimeoffset]::UtcNow.AddMinutes(-1).ToString('o')}}}
    }
    function Test-LiveModels($Config) { $script:Ready }
    function Pull([int]$Number, [string]$Branch, [string]$Sha, [string]$Owner = 'mightyrochy', [string]$Repository = 'mightyrochy/kod-shi-data') {
        <# Дані API; довільного тексту в позначки не передаємо. #>
        [pscustomobject]@{ created_at=[datetimeoffset]::UtcNow.ToString('o'); number=$Number;title='Код'; user=@{login=$Owner}; head=@{ref=$Branch;sha=$Sha;repo=@{full_name=$Repository}}; base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}} }
    }
    $script:Pulls = @((Pull 12 'claude/наряд' $first), (Pull 13 'codex/наряд' $first), (Pull 14 'gemini/наряд' $first), (Pull 15 'claude/чужий' $first 'чужий'), (Pull 16 'claude/форк' $first 'mightyrochy' 'чужий/форк'), (Pull 17 "gemini/автоперевірка-12-$first" $first))
    Invoke-WrapperChain
    function Markers { @(& git -C $remote for-each-ref '--format=%(refname)' refs/heads/gemini-queue/) }
    Check 'готові PR автоматично отримали незалежні рушії, Gemini — один' ((Markers).Count -eq 3)
    Check 'чужий автор, форк та автозвіт не породили нарядів' (@(Markers | Where-Object { $_ -match 'автоперевірка-(15|16|17)-' }).Count -eq 0)
    Invoke-WrapperChain
    Check 'повтор після перезапуску не дублює позначки' ((Markers).Count -eq 3)
    $file = Join-Path $WorkDir 'chain.json'; Remove-Item -LiteralPath $file
    Invoke-WrapperChain
    Check 'втрата локального списку не перезаписує наявні позначки' ((Markers).Count -eq 3)
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
    Check 'злиття продукту без штампу чекає збірки' (@(Markers | Where-Object { $_ -match 'автоживий-' }).Count -eq 0)
    $newer = Merge 'джерела/a.py' '3'; Invoke-WrapperChain
    $built = Merge 'build.txt' $newer; Invoke-WrapperChain
    $state = ConvertFrom-Json ([IO.File]::ReadAllText($file))
    Check 'збірка збережена в очікуванні моделей' ($state.live_pending.Count -eq 1 -and $state.live_pending[0].stamp -ceq $newer -and $state.live_pending[0].main -ceq $built)
    $script:Ready = $true; Invoke-WrapperChain
    Check 'кілька злиттів однієї збірки отримали одну GPU-позначку за штампом' (@(Markers | Where-Object { $_ -match "автоживий-$newer/.*/1/p2-gpu$" }).Count -eq 1)
    Invoke-WrapperChain
    Check 'живий прогін не дублюється' (@(Markers | Where-Object { $_ -match 'автоживий-' }).Count -eq 1)
    $script:Pulls = @((Pull 12 'claude/наряд' $newer)); Invoke-WrapperChain
    Check 'нова голова PR отримала нову перевірку' (@(Markers | Where-Object { $_ -match "автоперевірка-12-$newer/" }).Count -eq 1)
    # Квоти: вибір рушія за файлами, які смуги вже ведуть (heartbeat.json — Codex, quota-claude.json — Claude).
    $OutDir = Join-Path $tmpRoot 'gem-out'; [void][IO.Directory]::CreateDirectory($OutDir)
    $claudeDir = Join-Path $tmpRoot 'claude-run'; [void][IO.Directory]::CreateDirectory($claudeDir)
    function Stamp([double]$Hours) { [datetimeoffset]::UtcNow.AddHours($Hours).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
    function SetCodex([bool]$Blocked) {
        $v = if ($Blocked) { @{refused=(Stamp -1);reset=(Stamp 140)} } else { @{refused=(Stamp -200);reset=(Stamp -50)} }
        [IO.File]::WriteAllText("$OutDir/heartbeat.json", ((@{codex=$v}) | ConvertTo-Json -Compress), $utf)
    }
    function SetClaude([bool]$Blocked) {
        $v = if ($Blocked) { @{read=(Stamp 0);status='rejected';windows=@();refused=(Stamp -1);reset=(Stamp 3)} } else { @{read=(Stamp 0);status='allowed';windows=@(@{w='5H';left=40;reset=(Stamp 2)});refused='';reset=''} }
        [IO.File]::WriteAllText("$claudeDir/quota-claude.json", ($v | ConvertTo-Json -Compress -Depth 4), $utf)
    }
    function SlugMarkers([string]$Slug) { @(Markers | Where-Object { $_ -match [regex]::Escape("/$Slug/") }) }
    $script:Pulls = @(); $script:Ready = $true
    SetCodex $false; SetClaude $false
    $head = Merge 'квота-1.txt' '1'
    $script:Pulls = @((Pull 31 'claude/квота-a' $head)); Invoke-WrapperChain
    Check 'квота є: перевіряє Codex, як було' (@(SlugMarkers "автоперевірка-31-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-31-$head")[0] -match '/gpt-6\.1-sol-high/1/p2$')
    SetCodex $true
    $head = Merge 'квота-2.txt' '2'
    $script:Pulls = @((Pull 32 'claude/квота-b' $head)); Invoke-WrapperChain
    Check 'Codex на квоті: перевіряє Claude іншої моделі, ніж автор' (@(SlugMarkers "автоперевірка-32-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-32-$head")[0] -match '/cc-claude-opus-5-5-high/1/p2$')
    $script:Pulls = @((Pull 33 'codex/квота-c' $head)); Invoke-WrapperChain
    Check 'автор Codex, Codex на квоті: Claude (інший постачальник)' (@(SlugMarkers "автоперевірка-33-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-33-$head")[0] -match '/cc-claude-sonnet-5-5-medium/1/p2$')
    $script:Pulls = @((Pull 34 'gemini/квота-d' $head)); Invoke-WrapperChain
    Check 'автор Gemini, Codex на квоті: Claude' (@(SlugMarkers "автоперевірка-34-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-34-$head")[0] -match '/cc-claude-sonnet-5-5-medium/1/p2$')
    SetClaude $true
    $head = Merge 'квота-3.txt' '3'
    $script:Pulls = @((Pull 35 'claude/квота-e' $head)); Invoke-WrapperChain
    Check 'обидва на квоті: позначка чекає першого постачальника за порядком' (@(SlugMarkers "автоперевірка-35-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-35-$head")[0] -match '/gpt-6\.1-sol-high/1/p2$')
    # Позначка, що чекає вичерпаної квоти, переходить до доступного рушія без дубля.
    SetCodex $false; SetClaude $false
    $head = Merge 'квота-4.txt' '4'
    $script:Pulls = @((Pull 36 'claude/квота-f' $head)); Invoke-WrapperChain
    Check 'до квоти: позначка Codex' (@(SlugMarkers "автоперевірка-36-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-36-$head")[0] -match '/gpt-6\.1-sol-high/1/p2$')
    SetCodex $true; Invoke-WrapperChain
    $moved = @(SlugMarkers "автоперевірка-36-$head")
    Check 'Codex вичерпано: позначка перейшла до Claude, одна' ($moved.Count -eq 1 -and $moved[0] -match '/cc-claude-opus-5-5-high/1/p2$')
    Invoke-WrapperChain; SetCodex $false; Invoke-WrapperChain
    Check 'повтор і відновлення Codex не дублюють перевірку' (@(SlugMarkers "автоперевірка-36-$head").Count -eq 1)
    # Звіт, що вже опубліковано, інший рушій не повторює.
    SetCodex $false
    [void][IO.Directory]::CreateDirectory("$WorkDir/state")
    $head = Merge 'квота-5.txt' '5'
    $script:Pulls = @((Pull 37 'claude/квота-g' $head)); Invoke-WrapperChain
    [IO.File]::WriteAllText("$WorkDir/state/done37.json", ((@{line="GEMINI ОБГОРТКА: ГОТОВО claude/автоперевірка-37-$head $head"}) | ConvertTo-Json), $utf)
    SetCodex $true; Invoke-WrapperChain
    Check 'готовий звіт: нової позначки нема' (@(SlugMarkers "автоперевірка-37-$head").Count -eq 1)
    # Автоживий: позначка, що чекає Codex на квоті, переходить до Claude без дубля; відновлення Codex її не повертає.
    SetCodex $true; SetClaude $false; Invoke-WrapperChain
    Check 'автоживий при Codex на квоті — одна позначка Claude' (@(SlugMarkers "автоживий-$newer").Count -eq 1 -and @(SlugMarkers "автоживий-$newer")[0] -match '/cc-claude-sonnet-5-5-medium/1/p2-gpu$')
    SetCodex $false; Invoke-WrapperChain
    Check 'відновлення Codex не дублює автоживий' (@(SlugMarkers "автоживий-$newer").Count -eq 1)
    # Збій не з кодом CHAIN_*: у рядку тип і рядок скрипту, без шляхів і тексту.
    Get-ChildItem -LiteralPath $OutboxDir -File | Remove-Item
    [IO.File]::WriteAllText($file, 'не json /секрет/шлях', $utf)
    Invoke-WrapperChain
    $lines = @(Get-ChildItem -LiteralPath $OutboxDir -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() })
    Check 'збій проходу: тип і рядок скрипту в рядку ЛАНЦЮГ' ($lines.Count -eq 1 -and $lines[0] -cmatch '^GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED [A-Za-z0-9]+ wrapper_chain\.ps1:[0-9]+$')
    Check 'у рядку нема шляхів і тексту з даних' ($lines[0] -notmatch '[/\\]секрет')
    Check 'повний текст винятку — у журналі обгортки' ((Get-Content -Raw (Join-Path $WorkDir 'publish.log')) -match 'CHAIN_FAILED [A-Za-z.]+: ')
    Remove-Item -LiteralPath $file
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
    function Get-AutoLivePlan { '{}' }
    Check 'обидва планувальники можуть узяти шаблон автонаряду' ((Get-AutoTaskPath "автоперевірка-12-$newer") -ceq 'аудит/наряди/автоперевірка.md' -and (Add-AutoTaskContext "автоживий-$newer" 'текст' $built) -match $newer)
    # Вікно рахується за SHA й committer, а коментар не оживляє початковий архів.
    $clock = [datetimeoffset]::UtcNow; $installed = $clock.AddDays(-2); $heads = @{}
    $script:HeadDate = $clock.AddHours(-25)
    function Invoke-ChainApi([string]$Path) { [pscustomobject]@{sha=($Path -split '/')[-1];commit=@{committer=@{date=$script:HeadDate.ToString('o')}}} }
    $oldPull = Pull 70 'claude/давній' $first
    $oldPull.created_at = $clock.AddDays(-10).ToString('o')
    Check 'давня голова не потрапляє у початкове вікно 24 годин' (-not (Test-RecentReviewHead $oldPull $heads $installed $clock 24))
    $script:HeadDate = $clock.AddMinutes(-1)
    Check 'та сама давня голова не оживає від свіжих метаданих' (-not (Test-RecentReviewHead $oldPull $heads $installed $clock 24))
    $oldPull.head.sha = $newer
    Check 'спостережена зміна SHA оживляє PR незалежно від дати коміту' (Test-RecentReviewHead $oldPull $heads $installed $clock 24)
    $savedHeads = ConvertFrom-Json ($heads | ConvertTo-Json -Depth 5)
    $headsAgain = @{}; foreach ($entry in $savedHeads.PSObject.Properties) { $headsAgain[$entry.Name] = $entry.Value }
    Check 'право нової голови зберігається після перезапуску й за межами вікна' (Test-RecentReviewHead $oldPull $headsAgain $installed ($clock.AddDays(3)) 24)
    $oldPull.created_at = $clock.AddHours(-1).ToString('o'); $script:HeadDate = $clock.AddDays(-10)
    Check 'PR, створений після встановлення, допускає й старий коміт' (Test-RecentReviewHead $oldPull @{} $installed $clock 24)
    $oldPull.created_at = $clock.AddDays(-10).ToString('o'); $script:HeadDate = $clock.AddHours(-24)
    Check 'ліва межа вікна включена' (Test-RecentReviewHead $oldPull @{} $installed $clock 24)
    $script:HeadDate = $clock.AddHours(-24).AddSeconds(-1)
    Check 'секунда до лівої межі виключена' (-not (Test-RecentReviewHead $oldPull @{} $installed $clock 24))
    $script:HeadDate = $clock.AddMinutes(1)
    Check 'майбутня дата коміту не вважається рухом' (-not (Test-RecentReviewHead $oldPull @{} $installed $clock 24))
    $script:DryRun = $true; $script:Pulls = @((Pull 99 'claude/наряд' $newer)); Invoke-WrapperChain
    Check 'DryRun нічого не ставить' (@(Markers | Where-Object { $_ -match 'автоперевірка-99-' }).Count -eq 0)
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmpRoot) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmpRoot) -cmatch '^e0-chain-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmpRoot -Recurse -Force }
}
if ($failures) { exit 1 }
