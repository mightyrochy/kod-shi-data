#Requires -Version 5.1
<# Стенд `codex_pause_until` у ланцюг.json (дошка 16804): тижневий залишок Codex малий, тож до скидання автоживий не йде на Codex
і на Claude ноутбука, а бере agy; нічний Е1 і позначки диспетчера лишаються як були. Справжні функції ланцюга й публікатора на
тимчасовому origin; підмінено лише API GitHub, готовність моделей і вікно нічного. #>
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ('e0-chain-pause-' + [guid]::NewGuid().ToString('N'))
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
    $cfgPath = 'аудит/адаптери/gemini/ланцюг.json'
    $baseCfg = [IO.File]::ReadAllText((Join-Path $SourceDir 'ланцюг.json'), $utf)
    [IO.File]::WriteAllText("$seed/$cfgPath", $baseCfg, $utf)
    foreach ($task in @('автоперевірка','автоживий')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md", $task, $utf) }
    [IO.File]::WriteAllText("$seed/джерела/a.py", '1', $utf)
    & git -C $seed add -A; & git -C $seed commit -q -m 'початкова'; & git -C $seed push -q origin main
    $bare = Join-Path $tmpRoot 'repo.git'; & git clone -q --bare $remote $bare
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmpRoot/pub" -OutDir "$tmpRoot/gem-out" -OutboxDir "$tmpRoot/out" -UpdateRoot "$tmpRoot/update"
    [void][IO.Directory]::CreateDirectory("$OutDir/marker-state")
    Write-FileAtomic "$OutDir/marker-state/ready" '1'
    $GeminiRunsDir = "$tmpRoot/gemini-runs"
    $claudeDir = Join-Path $tmpRoot 'claude-run'; [void][IO.Directory]::CreateDirectory($claudeDir)
    foreach ($d in @($WorkDir, (Join-Path $WorkDir 'seen'), (Join-Path $WorkDir 'state'), $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
    $script:Repo = $bare; $script:NoHooks = Join-Path $tmpRoot 'no-hooks'
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    $script:Pulls = @(); $script:Ready = $true
    function Get-ChainPulls { $script:Pulls }
    function Invoke-ChainApi([string]$Path) {
        if ($Path -match '/files\?') { return [pscustomobject]@{filename='джерела/a.py'} }
        $sha = ($Path -split '/')[-1]
        [pscustomobject]@{sha=$sha;commit=@{committer=@{date=[datetimeoffset]::UtcNow.AddMinutes(-1).ToString('o')}}}
    }
    function Test-LiveModels($Config) { $script:Ready }
    function Test-NightlyOpen([datetime]$Utc) { $true }
    function Stamp([double]$Hours) { [datetimeoffset]::UtcNow.AddHours($Hours).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
    function SetCodex([bool]$Blocked) {
        $v = if ($Blocked) { @{refused=(Stamp -1);reset=(Stamp 140)} } else { @{refused=(Stamp -200);reset=(Stamp -50)} }
        [IO.File]::WriteAllText("$OutDir/heartbeat.json", ((@{codex=$v}) | ConvertTo-Json -Compress), $utf)
    }
    function SetClaude([bool]$Blocked) {
        $v = if ($Blocked) { @{read=(Stamp 0);status='rejected';windows=@();refused=(Stamp -1);reset=(Stamp 3)} } else { @{read=(Stamp 0);status='allowed';windows=@(@{w='5H';left=40;reset=(Stamp 2)});refused='';reset=''} }
        [IO.File]::WriteAllText("$claudeDir/quota-claude.json", ($v | ConvertTo-Json -Compress -Depth 4), $utf)
    }
    function SetAgy([bool]$Blocked) {
        $left = if ($Blocked) { 0 } else { 40 }
        [IO.File]::WriteAllText("$OutDir/pools.json", ((@{v=1;groups=@(@{g='GEMINIMODELS';n='gemini models';left=0;reset=90}, @{g='GEMINI4ARGON';n='gemini 4 argon';left=$left;reset=90})}) | ConvertTo-Json -Compress -Depth 4), $utf)
    }
    function Markers([string]$Slug) { @(& git -C $remote for-each-ref '--format=%(refname:short)' "refs/heads/gemini-queue/$Slug/") }
    function Merge([string]$Path, [string]$Text) {
        <# Злитий стан main і наступний справжній fetch публікатора. #>
        [IO.File]::WriteAllText((Join-Path $seed $Path), $Text, $utf)
        & git -C $seed add -A; & git -C $seed commit -q -m 'злиття'; & git -C $seed push -q origin main
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        Get-RefSha 'refs/remotes/origin/main'
    }
    function Tick {
        <# Прохід публікатора: fetch черги, потім ланцюг. #>
        [void](Invoke-Git @('fetch','-q','--prune','--no-tags','origin','+refs/heads/main:refs/remotes/origin/main','+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
        Invoke-WrapperChain
    }
    function SetPause([string]$Json) {
        <# Поле codex_pause_until дописується в ланцюг.json одразу після `"v": 1,`; порожній рядок — поле відсутнє. #>
        $text = $(if ($Json) { $baseCfg.Replace('"v": 1,', '"v": 1,' + "`n  `"codex_pause_until`": $Json,") } else { $baseCfg })
        [void](Merge $cfgPath $text)
    }
    function PauseLogLines { @(Select-String -LiteralPath "$WorkDir/publish.log" -Encoding utf8 -Pattern 'пауза Codex до' -SimpleMatch -ErrorAction SilentlyContinue).Count }
    function ConfigFailLines { @(Select-String -LiteralPath "$WorkDir/publish.log" -Encoding utf8 -Pattern 'ланцюг: CHAIN_CONFIG' -SimpleMatch -ErrorAction SilentlyContinue).Count }
    function NewStamp([string]$Text) { $s = Merge 'джерела/a.py' $Text; [void](Merge 'build.txt' $s); $s }
    $future = '"' + (Stamp 72) + '"'; $past = '"' + (Stamp -1) + '"'
    $codexModel = 'gpt-6.1-sol-high'; $claudeModel = 'cc-claude-sonnet-5-5-medium'; $agyModel = 'gemini-4-argon-high'
    SetCodex $false; SetClaude $false; SetAgy $false
    Invoke-WrapperChain

    # Нічний Е1 під час паузи: дозвіл стоїть на codex, ланцюг його не переносить на agy (той самий Move-NightlyMarker, що й без паузи).
    $night = 'Е1-нічний-живий-' + [datetimeoffset]::UtcNow.UtcDateTime.ToString('yyyyMMdd')
    $permit = Get-RefSha 'refs/remotes/origin/main'
    & git -C $seed push -q origin "${permit}:refs/heads/gemini-queue/$night/$codexModel/1/gpu-p8"
    SetPause $future; Tick
    $nm = @(Markers $night)
    Check 'пауза, нічний, codex з квотою: дозвіл лишається на codex' ($nm.Count -eq 1 -and $nm[0] -match "/$codexModel/1/gpu-p8$")
    SetCodex $true; SetClaude $false; Tick
    $nm = @(Markers $night)
    Check 'пауза, нічний, codex 0 %: дозвіл іде за своїм порядком codex→claude, не на agy' ($nm.Count -eq 1 -and $nm[0] -match "/$claudeModel/1/gpu-p8$")
    & git -C $seed push -q origin ":$($nm[0])"
    SetCodex $false

    # Автоживий під час паузи: agy, навіть коли codex і claude вільні.
    $s1 = NewStamp '2'; Tick
    $m1 = @(Markers "автоживий-$s1")
    "ДАНІ пауза в майбутньому, codex і claude вільні: позначка автоживого — $($m1 -join ' ')"
    Check 'пауза в майбутньому: автоживий на agy, умова p2-gpu, одна позначка' ($m1.Count -eq 1 -and $m1[0] -match "/$agyModel/1/p2-gpu$")
    Check 'пауза: лише один рядок журналу на значення паузи, не на прохід' ((PauseLogLines) -eq 1)
    Tick; Tick
    Check 'повторні проходи паузи не множать ні позначок, ні рядків журналу' (@(Markers "автоживий-$s1").Count -eq 1 -and (PauseLogLines) -eq 1)
    # Кінець активного штампу — зняття всіх його позначок на origin (Get-LiveCompletion); так стенд звільняє чергу між випадками.
    # Позначка, що чекає на agy, не стрибає на codex чи claude, коли agy на квоті.
    SetAgy $true; SetCodex $false; SetClaude $false; Tick
    Check 'пауза, agy на квоті: позначка лишається на agy й чекає, на codex і claude не йде' (@(Markers "автоживий-$s1").Count -eq 1 -and @(Markers "автоживий-$s1")[0] -match "/$agyModel/1/p2-gpu$")
    foreach ($m in @(Markers "автоживий-$s1")) { & git -C $seed push -q origin ":refs/heads/$m" }
    # Нова збірка під паузою, agy на квоті: позначка ставиться на agy й чекає скидання (Select-ReviewModel віддає єдиного кандидата).
    SetAgy $true
    $s2 = NewStamp '3'; Tick
    Check 'пауза, нова збірка при agy на квоті: позначка на agy, не на codex і claude' (@(Markers "автоживий-$s2").Count -eq 1 -and @(Markers "автоживий-$s2")[0] -match "/$agyModel/1/p2-gpu$")
    SetAgy $false
    foreach ($m in @(Markers "автоживий-$s2")) { & git -C $seed push -q origin ":refs/heads/$m" }

    # Пауза минула: як було — codex.
    SetPause $past
    $s3 = NewStamp '4'; Tick
    Check 'пауза минула: автоживий на codex, як без поля' (@(Markers "автоживий-$s3").Count -eq 1 -and @(Markers "автоживий-$s3")[0] -match "/$codexModel/1/p2-gpu$")
    foreach ($m in @(Markers "автоживий-$s3")) { & git -C $seed push -q origin ":refs/heads/$m" }

    # Поле відсутнє й null: як було.
    foreach ($case in @(@{Name='поле відсутнє'; Json=''}, @{Name='codex_pause_until: null'; Json='null'})) {
        SetPause $case.Json
        $s = NewStamp ("5-" + $case.Name); Tick
        Check "$($case.Name): автоживий на codex, як було" (@(Markers "автоживий-$s").Count -eq 1 -and @(Markers "автоживий-$s")[0] -match "/$codexModel/1/p2-gpu$")
        foreach ($m in @(Markers "автоживий-$s")) { & git -C $seed push -q origin ":refs/heads/$m" }
    }
    # Закінчення паузи на тій самій позначці: codex на квоті під час паузи не потрібен — після паузи порядок codex→claude.
    SetCodex $true; SetClaude $false
    $s4 = NewStamp '6'; Tick
    Check 'без паузи, codex 0 %: Claude, як було (пауза нічого не змінила для порядку)' (@(Markers "автоживий-$s4").Count -eq 1 -and @(Markers "автоживий-$s4")[0] -match "/$claudeModel/1/p2-gpu$")
    foreach ($m in @(Markers "автоживий-$s4")) { & git -C $seed push -q origin ":refs/heads/$m" }
    SetCodex $false

    # Невалідне значення — CHAIN_CONFIG, позначок нема; після виправлення прохід підхоплює штамп.
    $bad = @('"завтра"', '"2026-11-23 10:16:00"', '"2026-11-23T10:16:00+02:00"', '"2026-13-40T10:16:00Z"', '12345', '""', 'true')
    $stBad = NewStamp '7'
    foreach ($json in $bad) {
        SetPause $json
        $before = ConfigFailLines; Tick
        Check "невалідне ${json}: CHAIN_CONFIG, автоживий не поставлено" ((ConfigFailLines) -eq $before + 1 -and @(Markers "автоживий-$stBad").Count -eq 0)
    }
    SetPause ''
    Tick
    Check 'після виправлення поля прохід ставить штамп, що чекав' (@(Markers "автоживий-$stBad").Count -eq 1 -and @(Markers "автоживий-$stBad")[0] -match "/$codexModel/1/p2-gpu$")
} catch {
    Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false
} finally {
    if ((Split-Path -Leaf $tmpRoot) -cmatch '^e0-chain-pause-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
"провалів: $failures"
if ($failures) { exit 1 }
