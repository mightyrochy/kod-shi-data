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
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmpRoot/pub" -OutDir "$tmpRoot/gem-out" -OutboxDir "$tmpRoot/out" -UpdateRoot "$tmpRoot/update"
    $GeminiRunsDir = "$tmpRoot/gemini-runs"
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
    function SetAgy([bool]$Blocked) {
        $left = if ($Blocked) { 0 } else { 40 }
        [IO.File]::WriteAllText("$OutDir/pools.json", ((@{v=1;groups=@(@{g='GEMINIFLASH';left=$left;reset=90}, @{g='GEMINIPRO';left=$left;reset=90})}) | ConvertTo-Json -Compress -Depth 4), $utf)
    }
    function OutLines { @(Get-ChildItem -LiteralPath $OutboxDir -File -ErrorAction SilentlyContinue | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() }) }
    function CloudLines([string]$N) { @(OutLines | Where-Object { $_ -cmatch ('^GEMINI ОБГОРТКА: ПОТРІБНА ПЕРЕВІРКА CLAUDE #' + $N + ' [0-9a-f]{40}$') }) }
    $script:Pulls = @(); $script:Ready = $true
    SetCodex $false; SetClaude $false; SetAgy $false
    $head = Merge 'квота-1.txt' '1'
    $script:Pulls = @((Pull 31 'claude/квота-a' $head)); Invoke-WrapperChain
    Check 'автор Claude: перевіряє agy, не claude -p' (@(SlugMarkers "автоперевірка-31-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-31-$head")[0] -match '/gemini-3\.8-flash-high/1/p2$')
    $script:Pulls = @((Pull 39 'codex/квота-i' $head)); Invoke-WrapperChain
    Check 'автор GPT: перевіряє agy' (@(SlugMarkers "автоперевірка-39-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-39-$head")[0] -match '/gemini-3\.8-flash-high/1/p2$')
    $script:Pulls = @((Pull 40 'gemini/квота-j' $head)); Invoke-WrapperChain
    Check 'автор Gemini: перевіряє Codex' (@(SlugMarkers "автоперевірка-40-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-40-$head")[0] -match '/gpt-6\.1-sol-high/1/p2$')
    SetAgy $true
    $head = Merge 'квота-2.txt' '2'
    $script:Pulls = @((Pull 32 'claude/квота-b' $head)); Invoke-WrapperChain
    Check 'автор Claude, agy на квоті: Codex' (@(SlugMarkers "автоперевірка-32-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-32-$head")[0] -match '/gpt-6\.1-sol-high/1/p2$')
    $script:Pulls = @((Pull 33 'codex/квота-c' $head)); Invoke-WrapperChain
    Check 'автор GPT, agy на квоті: рядок хмарному Claude, позначки нема' (@(SlugMarkers "автоперевірка-33-$head").Count -eq 0 -and @(CloudLines 33).Count -eq 1 -and @(CloudLines 33)[0].EndsWith($head))
    Invoke-WrapperChain
    Check 'повтор не дублює рядок хмарному Claude' (@(CloudLines 33).Count -eq 1)
    SetCodex $true
    $script:Pulls = @((Pull 34 'gemini/квота-d' $head)); Invoke-WrapperChain
    Check 'автор Gemini, Codex на квоті: хмарний Claude' (@(SlugMarkers "автоперевірка-34-$head").Count -eq 0 -and @(CloudLines 34).Count -eq 1)
    Check 'жодної позначки cc- для перевірки' (@(Markers | Where-Object { $_ -match 'автоперевірка-.*/cc-' }).Count -eq 0)
    $head = Merge 'квота-3.txt' '3'
    $script:Pulls = @((Pull 35 'claude/квота-e' $head)); Invoke-WrapperChain
    Check 'обидва на квоті: позначка чекає першого постачальника за порядком' (@(SlugMarkers "автоперевірка-35-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-35-$head")[0] -match '/gemini-3\.8-flash-high/1/p2$')
    # Позначка, що чекає вичерпаної квоти, переходить до доступного рушія без дубля.
    SetCodex $false; SetAgy $false
    $head = Merge 'квота-4.txt' '4'
    $script:Pulls = @((Pull 36 'claude/квота-f' $head)); Invoke-WrapperChain
    Check 'до квоти: позначка agy' (@(SlugMarkers "автоперевірка-36-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-36-$head")[0] -match '/gemini-3\.8-flash-high/1/p2$')
    SetAgy $true; Invoke-WrapperChain
    $moved = @(SlugMarkers "автоперевірка-36-$head")
    Check 'agy вичерпано: позначка перейшла до Codex, одна' ($moved.Count -eq 1 -and $moved[0] -match '/gpt-6\.1-sol-high/1/p2$')
    Invoke-WrapperChain; SetAgy $false; Invoke-WrapperChain
    Check 'повтор і відновлення agy не дублюють перевірку' (@(SlugMarkers "автоперевірка-36-$head").Count -eq 1)
    # Позначка Codex роботи Gemini, Codex вичерпано: позначку знято, перевірку бере хмарний Claude.
    SetCodex $false
    $head = Merge 'квота-4б.txt' '4б'
    $script:Pulls = @((Pull 38 'gemini/квота-h' $head)); Invoke-WrapperChain
    Check 'до квоти: позначка Codex роботи Gemini' (@(SlugMarkers "автоперевірка-38-$head").Count -eq 1 -and @(CloudLines 38).Count -eq 0)
    SetCodex $true; Invoke-WrapperChain; Invoke-WrapperChain
    Check 'Codex вичерпано: позначку знято, один рядок хмарному Claude' (@(SlugMarkers "автоперевірка-38-$head").Count -eq 0 -and @(CloudLines 38).Count -eq 1)
    SetCodex $false; Invoke-WrapperChain
    Check 'відновлення Codex не ставить другої перевірки' (@(SlugMarkers "автоперевірка-38-$head").Count -eq 0)
    # Мірило наряду обгортка-рецензент-за-групою-квоти: квота agy — за групою саме обраної моделі (gemini-3.8-flash-high →
    # «Gemini Models»), а не за будь-якою групою pools.json. ДО — той самий pools.json без слів назви: так його пише main, і
    # Test-ModelQuota судить його правилом main (усі групи на 0 %). «Зараз» — 2026-10-29T19:00Z.
    function SetPools($Gem, $Cg, [switch]$Old) {
        $gs = @([ordered]@{g='GEMINIMODELS';left=$Gem;reset=90;n='gemini models'}, [ordered]@{g='CLAUDEANDGPTMODE';left=$Cg;reset=90;n='claude and gpt models'})
        if ($Old) { foreach ($g in $gs) { $g.Remove('n') } }
        [IO.File]::WriteAllText("$OutDir/pools.json", ((@{v=1;groups=$gs}) | ConvertTo-Json -Compress -Depth 4), $utf)
    }
    function SetRefused([string]$At) {
        $hb = $(if ($At) { @{codex=@{refused=$At}} } else { @{} })
        [IO.File]::WriteAllText("$OutDir/heartbeat.json", ($hb | ConvertTo-Json -Compress -Depth 3), $utf)
    }
    $chainCfg = ConvertFrom-Json ([IO.File]::ReadAllText((Join-Path $SourceDir 'ланцюг.json'), $utf))
    $at19 = [datetimeoffset]::new(2026, 10, 29, 19, 0, 0, [timespan]::Zero)
    $tablePull = Pull 50 'claude/таблиця-квоти' $head
    $cases = @(
        @{N=1; Gem=0; Cg=1; Refused='2026-10-29T15:18:00Z'; Want='gpt-6.1-sol-high'},
        @{N=2; Gem=0; Cg=1; Refused='2026-10-29T18:30:00Z'; Want='gemini-3.8-flash-high'},
        @{N=3; Gem=100; Cg=0; Refused='2026-10-29T15:18:00Z'; Want='gemini-3.8-flash-high'},
        @{N=4; Gem=0; Cg=0; Refused=''; Want='gpt-6.1-sol-high'},
        @{N=5; Gem=$null; Cg=$null; Refused=''; Want='gemini-3.8-flash-high'})
    foreach ($c in $cases) {
        SetRefused $c.Refused
        if ($null -eq $c.Gem) { Remove-Item -LiteralPath "$OutDir/pools.json" -ErrorAction SilentlyContinue } else { SetPools $c.Gem $c.Cg -Old }
        $was = @(Get-ReviewModels $tablePull $chainCfg $at19)
        if ($null -ne $c.Gem) { SetPools $c.Gem $c.Cg }
        $got = @(Get-ReviewModels $tablePull $chainCfg $at19)
        Check "випадок $($c.N) таблиці: рецензент $($c.Want)" ($got.Count -eq 1 -and $got[0] -ceq $c.Want)
        "  мірило: випадок $($c.N) — ДО $($was -join ',') → ПІСЛЯ $($got -join ',')"
    }
    # Випадок 1 для поставленої позначки: …/gemini-3.8-flash-high/… знімається, ставиться …/gpt-6.1-sol-high/…, один раз.
    SetCodex $false; SetPools 40 1
    $head = Merge 'квота-група.txt' '1'
    $script:Pulls = @((Pull 51 'claude/квота-група' $head)); Invoke-WrapperChain
    Check 'група: до квоти позначка agy' (@(SlugMarkers "автоперевірка-51-$head").Count -eq 1 -and @(SlugMarkers "автоперевірка-51-$head")[0] -match '/gemini-3\.8-flash-high/1/p2$')
    SetRefused (Stamp -3.7); SetPools 0 1 -Old; Invoke-WrapperChain
    $was = @(SlugMarkers "автоперевірка-51-$head")
    SetPools 0 1; Invoke-WrapperChain; Invoke-WrapperChain
    $got = @(SlugMarkers "автоперевірка-51-$head")
    Check 'група GEMINIMODELS 0 %, CLAUDEANDGPTMODE 1 %: позначка перейшла до Codex, одна' ($got.Count -eq 1 -and $got[0] -match '/gpt-6\.1-sol-high/1/p2$')
    "  мірило: заміна позначки у випадку 1 — ДО $(@($was | ForEach-Object { ($_ -split '/')[-3] }) -join ',') → ПІСЛЯ $(@($got | ForEach-Object { ($_ -split '/')[-3] }) -join ',')"
    SetCodex $false
    # Звіт, що вже опубліковано, інший рушій не повторює.
    SetAgy $false
    [void][IO.Directory]::CreateDirectory("$WorkDir/state")
    $head = Merge 'квота-5.txt' '5'
    $script:Pulls = @((Pull 37 'claude/квота-g' $head)); Invoke-WrapperChain
    [IO.File]::WriteAllText("$WorkDir/state/done37.json", ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/автоперевірка-37-$head $head"}) | ConvertTo-Json), $utf)
    SetAgy $true; Invoke-WrapperChain
    Check 'готовий звіт: нової позначки нема' (@(SlugMarkers "автоперевірка-37-$head").Count -eq 1)
    SetAgy $false
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
    $reportBranch = 'gemini/перевірка-3110-2'
    [void](Invoke-Git @('push','-q','origin',"${newer}:refs/heads/$reportBranch"))
    Save-DraftRequest $reportBranch $newer
    Complete-EngineDrafts
    Check 'звіт перевірки без рядків дошки лишається гілкою без PR-чернетки' ($script:DraftPosts -eq 1 -and @(Get-ChildItem "$WorkDir/drafts/*.json" -ErrorAction SilentlyContinue).Count -eq 0)
    # Мірило наряду обгортка-ресурс-слотів: 3 відкриті PR, у одного голова змінилась, один злито. ДО (за кодом до зміни)
    # лишалось 5 позначок: по одній на кожну побачену голову й ніякого зняття; ПІСЛЯ — одна на живу голову.
    $h1 = Merge 'три-pr.txt' '1'
    $script:Pulls = @((Pull 41 'claude/живий' $h1), (Pull 42 'codex/змінений' $h1), (Pull 43 'claude/злитий' $h1)); Invoke-WrapperChain
    Check 'три PR — три позначки' (@(Markers | Where-Object { $_ -match "автоперевірка-4[123]-$h1/" }).Count -eq 3)
    & git -C $seed push -q origin "${h1}:refs/heads/gemini-queue/автоперевірка-41-$h1/gpt-6.1-sol-high/1/p2"
    $h2 = Merge 'три-pr.txt' '2'
    $script:Pulls = @((Pull 41 'claude/живий' $h1), (Pull 42 'codex/змінений' $h2)); Invoke-WrapperChain
    $after = @(Markers | Where-Object { $_ -match 'автоперевірка-4[123]-' })
    $log = [IO.File]::ReadAllText((Join-Path $WorkDir 'publish.log'), $utf)
    Check 'ПІСЛЯ: по одній позначці на живу голову відкритого PR' ($after.Count -eq 2 -and @($after | Where-Object { $_ -match "автоперевірка-41-$h1/" }).Count -eq 1 -and @($after | Where-Object { $_ -match "автоперевірка-42-$h2/" }).Count -eq 1)
    Check 'мертві позначки знято до узяття: стара голова, злитий PR, дубль' (@($after | Where-Object { $_ -match "автоперевірка-4[23]-$h1/" }).Count -eq 0 -and $log.Contains('знято — голова PR змінилась') -and $log.Contains('знято — PR не відкритий') -and $log.Contains('знято — друга позначка тієї самої голови'))
    "  мірило: позначок ДО 5 (за кодом main) → ПІСЛЯ $($after.Count)"
    # Мірило наряду обгортка-claude-у-хмару: позначка автоперевірки Claude на ноутбуці від старого вибору (ключ у стані
    # ланцюга) знімається, голова отримує рецензента іншого постачальника, а кількість знятих — рядок у зведенні.
    $script:Pulls = @((Pull 44 'codex/старий-вибір' $h2)); Invoke-WrapperChain
    $agyRef = @(SlugMarkers "автоперевірка-44-$h2")
    & git -C $seed push -q origin ":$($agyRef[0])"
    & git -C $seed push -q origin "${h2}:refs/heads/gemini-queue/автоперевірка-44-$h2/cc-claude-sonnet-5-5-medium/1/p2"
    $st = ConvertFrom-Json ([IO.File]::ReadAllText($file, $utf))
    $st.reviews = @(@($st.reviews | Where-Object { $_ -notmatch "^44 $h2 " }) + "44 $h2 cc-claude-sonnet-5-5-medium")
    [IO.File]::WriteAllText($file, ($st | ConvertTo-Json -Compress -Depth 7), $utf)
    Get-ChildItem -LiteralPath $OutboxDir -File | Remove-Item
    $before = @(SlugMarkers "автоперевірка-44-$h2")
    Invoke-WrapperChain
    $now44 = @(SlugMarkers "автоперевірка-44-$h2")
    Check 'старий вибір: позначку cc- знято, рецензент — agy' ($before.Count -eq 1 -and $before[0] -match '/cc-' -and $now44.Count -eq 1 -and $now44[0] -match '/gemini-3\.8-flash-high/1/p2$' -and ([IO.File]::ReadAllText((Join-Path $WorkDir 'publish.log'), $utf)).Contains('знято — Claude на ноутбуці не перевіряє'))
    Check 'зняття позначок — рядок у зведенні' (@(OutLines | Where-Object { $_ -ceq 'GEMINI ОБГОРТКА: ЗНЯТО ПОЗНАЧОК ПЕРЕВІРКИ 1' }).Count -eq 1)
    Check 'рядок зняття не будить диспетчера, рядок хмарного Claude будить' (-not (Test-DispatcherAction 'GEMINI ОБГОРТКА: ЗНЯТО ПОЗНАЧОК ПЕРЕВІРКИ 1') -and (Test-DispatcherAction "GEMINI ОБГОРТКА: ПОТРІБНА ПЕРЕВІРКА CLAUDE #44 $h2") -and (Test-OutboxLine "GEMINI ОБГОРТКА: ПОТРІБНА ПЕРЕВІРКА CLAUDE #44 $h2") -eq '' -and -not (Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/автоперевірка-44-$h2 CLAUDE_NOT_LAPTOP") -and (Test-DispatcherAction 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/наряд CLAUDE_NOT_LAPTOP'))
    "  мірило: позначок cc- автоперевірки ДО 1 → ПІСЛЯ $(@(Markers | Where-Object { $_ -match 'автоперевірка-.*/cc-' }).Count)"
    # Правила 31.10 (ПК-9): перевірка лише на голову з оголошеним кінцем і ризиком Р1–Р3; та сама зміна (patch-id) — без нової.
    $script:FilePaths = @('джерела/a.py')
    function Invoke-ChainApi([string]$Path) {
        if ($Path -match '/files\?') { return @($script:FilePaths | ForEach-Object { [pscustomobject]@{filename=$_} }) }
        [pscustomobject]@{sha=($Path -split '/')[-1];commit=@{committer=@{date=[datetimeoffset]::UtcNow.AddMinutes(-1).ToString('o')}}}
    }
    function DraftPull([int]$Number, [string]$Branch, [string]$Sha) { $p = Pull $Number $Branch $Sha; $p | Add-Member -NotePropertyName draft -NotePropertyValue $true; $p }
    SetCodex $false; SetAgy $false; SetClaude $false
    $head = Merge 'кінець-1.txt' '1'
    $script:Pulls = @((DraftPull 80 'claude/кінець-a' $head)); Invoke-WrapperChain
    Check 'чернетка без ГОТОВО смуги: перевірки нема' (@(SlugMarkers "автоперевірка-80-$head").Count -eq 0)
    [IO.File]::WriteAllText("$WorkDir/state/done80.json", ((@{line="GEMINI ОБГОРТКА: ГОТОВО claude/кінець-a $head МОДЕЛЬ cc-claude-sonnet-5-5-medium"}) | ConvertTo-Json), $utf)
    Invoke-WrapperChain
    Check 'чернетка з ГОТОВО смуги на цій голові: одна перевірка' (@(SlugMarkers "автоперевірка-80-$head").Count -eq 1)
    $head = Merge 'кінець-2.txt' '2'
    $script:Pulls = @((Pull 81 'claude/кінець-b' $head)); Invoke-WrapperChain
    Check 'PR не чернетка: одна перевірка' (@(SlugMarkers "автоперевірка-81-$head").Count -eq 1)
    [void](Merge 'аудит/наряди/р0-проба.md' "р0-проба | вид: код | ризик Р0`nтіло`n")
    $head = Merge 'ризик-1.txt' '1'
    $script:FilePaths = @('джерела/a.py', 'аудит/наряди/р0-проба.md')
    $script:Pulls = @((Pull 82 'claude/ризик-0' $head)); Invoke-WrapperChain
    Check 'ризик Р0 у шапці наряду: перевірки нема' (@(SlugMarkers "автоперевірка-82-$head").Count -eq 0)
    [void](Merge 'аудит/наряди/р2-проба.md' "р2-проба | вид: код | ризик Р2`n")
    $head = Merge 'ризик-2.txt' '2'
    $script:FilePaths = @('джерела/a.py', 'аудит/наряди/р2-проба.md')
    $script:Pulls = @((Pull 83 'claude/ризик-2' $head)); Invoke-WrapperChain
    Check 'ризик Р2: одна перевірка' (@(SlugMarkers "автоперевірка-83-$head").Count -eq 1)
    $script:FilePaths = @('джерела/a.py')
    $base = Get-RefSha 'refs/remotes/origin/main'
    & git -C $seed checkout -q -b pid-a
    [IO.File]::WriteAllText("$seed/джерела/пч.txt", 'x', $utf); & git -C $seed add -A; & git -C $seed commit -q -m 'a'
    $pidA = (& git -C $seed rev-parse HEAD).Trim()
    & git -C $seed checkout -q -b pid-b $base
    [IO.File]::WriteAllText("$seed/джерела/пч.txt", 'x', $utf); & git -C $seed add -A; & git -C $seed commit -q -m 'b: інший текст коміту'
    $pidB = (& git -C $seed rev-parse HEAD).Trim()
    & git -C $seed push -q origin pid-a pid-b
    & git -C $seed checkout -q main
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/pid-a:refs/remotes/origin/pid-a','+refs/heads/pid-b:refs/remotes/origin/pid-b'))
    $mainNow = Get-RefSha 'refs/remotes/origin/main'
    $idA = Get-ReviewPatchId $pidA $mainNow
    Check 'patch-id: та сама зміна в різних комітах має один id' ($idA -and $pidA -cne $pidB -and $idA -ceq (Get-ReviewPatchId $pidB $mainNow))
    [IO.File]::WriteAllText("$WorkDir/state/done84.json", ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/автоперевірка-84-$pidA $pidA"}) | ConvertTo-Json), $utf)
    $rv = @{ '84' = @{head=$pidA;diff='';pid=$idA} }
    Check 'нова голова з тим самим patch-id після звіту: нової перевірки нема' (Test-ReviewedMerge (Pull 84 'claude/пч' $pidB) $rv $mainNow)
    $rv['84'].pid = 'інший'
    Check 'інший patch-id: перевірка потрібна' (-not (Test-ReviewedMerge (Pull 84 'claude/пч' $pidB) $rv $mainNow))
    Check 'звіти перевірки кирилицею, латинкою й новою формою виключені' ((Test-ReviewBranch 'claude/avtoperevirka-3110') -and (Test-ReviewBranch 'codex/perevirka-3110-1') -and (Test-ReviewBranch 'claude/перевірка-3110-1') -and -not (Test-ReviewBranch 'claude/наряд'))
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
    $emptyText = "наряд`nПЛАН ЖИВОГО — ДАНІ (JSON):`n" + '{"since_sha":"","scenes":{}}' + "`n"
    $fullText = "наряд`nПЛАН ЖИВОГО — ДАНІ (JSON):`n" + '{"since_sha":"","scenes":{"ж1_сцена":[{"pr":1,"question":"q"}]}}' + "`n"
    Check 'автоживий на порожньому плані: ні прогону, ні PR' (Test-AutoPlanEmpty "автоживий-$newer" $emptyText)
    Check 'автоживий із рядками ЖИВИЙ ПІСЛЯ іде на прогін' (-not (Test-AutoPlanEmpty "автоживий-$newer" $fullText))
    Check 'нічний Е1 на порожньому плані виконує мінімальну сцену' (-not (Test-AutoPlanEmpty 'Е1-нічний-живий-20261031' $emptyText))
    # Вікна за віком коміту нема (review_hours знято, рішення менеджера 01.11): добір — за новим PR чи зміною SHA.
    $clock = [datetimeoffset]::UtcNow; $installed = $clock.AddDays(-2); $heads = @{}
    $oldPull = Pull 70 'claude/давній' $first
    $oldPull.created_at = $clock.AddDays(-10).ToString('o')
    Check 'давня голова давнього PR не добирається' (-not (Test-RecentReviewHead $oldPull $heads $installed $clock))
    Check 'та сама давня голова не оживає при повторі' (-not (Test-RecentReviewHead $oldPull $heads $installed $clock))
    $oldPull.head.sha = $newer
    Check 'спостережена зміна SHA оживляє PR' (Test-RecentReviewHead $oldPull $heads $installed $clock)
    $savedHeads = ConvertFrom-Json ($heads | ConvertTo-Json -Depth 5)
    $headsAgain = @{}; foreach ($entry in $savedHeads.PSObject.Properties) { $headsAgain[$entry.Name] = $entry.Value }
    Check 'право нової голови зберігається після перезапуску' (Test-RecentReviewHead $oldPull $headsAgain $installed ($clock.AddDays(3)))
    $oldPull.created_at = $clock.AddHours(-1).ToString('o')
    Check 'PR, створений після встановлення, добирається' (Test-RecentReviewHead $oldPull @{} $installed $clock)
    $cc = ConvertFrom-Json ([IO.File]::ReadAllText((Join-Path $SourceDir 'ланцюг.json')))
    Check 'ланцюг.json без review_hours' ($null -eq $cc.PSObject.Properties['review_hours'])
    $script:DryRun = $true; $script:Pulls = @((Pull 99 'claude/наряд' $newer)); Invoke-WrapperChain
    Check 'DryRun нічого не ставить' (@(Markers | Where-Object { $_ -match 'автоперевірка-99-' }).Count -eq 0)
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmpRoot) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmpRoot) -cmatch '^e0-chain-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmpRoot -Recurse -Force }
}
if ($failures) { exit 1 }
