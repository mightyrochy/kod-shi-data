#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('menshe-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    <# Незалежні правила виконуються до кінця й при відсутній функції базової версії. #>
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutboxDir "$tmp/out"
    foreach ($dir in @($WorkDir,"$WorkDir/state","$WorkDir/seen",$OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $config = [pscustomobject]@{codex='gpt-review';claude='cc-claude-review'}
    $sha = 'a' * 40
    Scenario '1а фактична модель' {
        foreach ($model in @('gpt-6.1-sol-high','gemini-3.8-flash-high','cc-claude-opus-5-5-high','невідома')) {
            $pull = [pscustomobject]@{head=@{ref='gemini/виконавець';sha=$sha}}
            Save-DraftRequest $pull.head.ref $sha $model
            $models = @(Get-ReviewModels $pull $config)
            $expected = if ($model -like 'gpt-*') { $config.claude } else { $config.codex }
            Check "1а $model — рівно один інший постачальник" ($models.Count -eq 1 -and $models[0] -ceq $expected)
        }
    }
    Scenario '1а модель із прийнятого рядка' {
        Write-FileAtomic "$WorkDir/state/model.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/стан $sha МОДЕЛЬ gpt-6.1-sol-high"}) | ConvertTo-Json)
        $models = @(Get-ReviewModels ([pscustomobject]@{head=@{ref='gemini/стан';sha=$sha}}) $config)
        Check '1а фактичний GPT із ГОТОВО вибирає Claude без файла моделі' ($models.Count -eq 1 -and $models[0] -ceq $config.claude)
        $models = @(Get-ReviewModels ([pscustomobject]@{head=@{ref='gemini/невідома';sha=$sha}}) $config)
        Check '1а немає даних про модель — один Codex' ($models.Count -eq 1 -and $models[0] -ceq $config.codex)
    }
    Scenario '1в вердикти' {
        foreach ($branch in @('gemini/перевірка-12','claude/pachka-5','codex/перевірка-коду','gemini/автоперевірка-12')) {
            Check "1в $branch без рекурсії" (@(Get-ReviewModels ([pscustomobject]@{head=@{ref=$branch;sha=$sha}}) $config).Count -eq 0)
        }
    }
    Scenario '1б справжнє злиття main' {
        $script:seed = Join-Path $tmp 'seed'; & git init -q -b main $seed
        & git -C $seed config user.name 'стенд'; & git -C $seed config user.email 'stend@example.invalid'
        & git -C $seed config core.autocrlf false
        [IO.File]::WriteAllText("$seed/a.txt","початок`n",$utf)
        & git -C $seed add -A; & git -C $seed commit -q -m 'база'
        & git -C $seed checkout -q -b claude/task
        [IO.File]::WriteAllText("$seed/a.txt","зміна`n",$utf)
        & git -C $seed commit -qam 'код'; $old = (& git -C $seed rev-parse HEAD).Trim()
        & git -C $seed checkout -q main
        [IO.File]::WriteAllText("$seed/b.txt","main`n",$utf)
        & git -C $seed add -A; & git -C $seed commit -q -m 'інший файл main'
        $main = (& git -C $seed rev-parse HEAD).Trim()
        & git -C $seed checkout -q claude/task; & git -C $seed merge -q --no-edit main
        $merged = (& git -C $seed rev-parse HEAD).Trim()
        $script:RepoDir = $seed; $script:Repo = $seed; $script:NoHooks = Join-Path $tmp 'no-hooks'
        & git -C $seed checkout -q main
        foreach ($dir in @('аудит/наряди','аудит/адаптери/gemini')) { [void][IO.Directory]::CreateDirectory((Join-Path $seed $dir)) }
        Copy-Item -LiteralPath (Join-Path $SourceDir 'ланцюг.json') -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
        foreach ($task in @('автоживий','автоперевірка')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md",$task,$utf) }
        # Шаблони належать main, а код PR — окремій гілці.
        & git -C $seed add -A; & git -C $seed commit -q -m 'шаблони'
        $main = (& git -C $seed rev-parse HEAD).Trim()
        & git -C $seed checkout -q claude/task
        & git -C $seed merge -q --no-edit main
        $merged = (& git -C $seed rev-parse HEAD).Trim()
        & git -C $seed update-ref refs/remotes/origin/main $main
        $script:TestPulls = @(); $script:TestMarkers = @()
        function script:Get-ChainPulls { $script:TestPulls }
        function script:Complete-EngineDrafts { }
        function script:Test-ChainCodePull { $true }
        function script:Test-LiveModels { $true }
        function script:Add-ChainMarker($Slug,$Model,$Main,[switch]$Gpu) { $script:TestMarkers += $Slug }
        function script:Invoke-ChainApi([string]$Path) { [pscustomobject]@{sha=($Path -split '/')[-1];commit=@{committer=@{date=[datetimeoffset]::UtcNow.AddSeconds(-1).ToString('o')}}} }
        $pull = [pscustomobject]@{number=9;created_at=[datetimeoffset]::UtcNow.ToString('o');title='код';user=@{login='mightyrochy'};head=@{ref='claude/task';sha=$old;repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}}}
        $script:TestPulls = @($pull)
        Invoke-WrapperChain
        Write-FileAtomic "$WorkDir/state/review.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/автоперевірка-9-$old $sha"}) | ConvertTo-Json)
        $pull.head.sha = $merged
        Invoke-WrapperChain


        Check '1б чисте злиття main — одна позначка замість двох' (@($script:TestMarkers | Where-Object { $_ -like 'автоперевірка-*' }).Count -eq 1)
        [IO.File]::WriteAllText("$seed/a.txt","інший код`n",$utf)
        & git -C $seed commit -qam 'реальна зміна'; $pull.head.sha = (& git -C $seed rev-parse HEAD).Trim()
        Invoke-WrapperChain
        Check '1б зміна коду — друга перевірка' (@($script:TestMarkers | Where-Object { $_ -like 'автоперевірка-*' }).Count -eq 2)
    }
    Scenario '2 останній штамп' {
        $script:TestPulls = @()
        foreach ($n in @(1,2,3)) {
            $stamp = (& git -C $seed rev-parse HEAD).Trim()
            [IO.File]::WriteAllText("$seed/build.txt",$stamp,$utf)
            & git -C $seed add -A; & git -C $seed commit -q -m "збірка $n"
            $head = (& git -C $seed rev-parse HEAD).Trim()
            & git -C $seed update-ref refs/remotes/origin/main $head
            Invoke-WrapperChain
            if ($n -eq 1) { $firstStamp = $stamp }
        }
        Check '2 під час активного три штампи — одна позначка' (@($script:TestMarkers | Where-Object { $_ -like 'автоживий-*' }).Count -eq 1)
        Check '2 пропущений проміжний штамп має журнал' ([IO.File]::ReadAllText("$WorkDir/publish.log").Contains('пропущено проміжний штамп'))
        Write-FileAtomic "$WorkDir/state/live.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/автоживий-$firstStamp $sha"}) | ConvertTo-Json)
        Invoke-WrapperChain
        $live = @($script:TestMarkers | Where-Object { $_ -like 'автоживий-*' })
        Check '2 після звіту рівно наступна позначка останнього штампу' ($live.Count -eq 2 -and $live[-1] -ceq "автоживий-$stamp")
        Write-FileAtomic "$WorkDir/state/live-next.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/автоживий-$stamp $sha"}) | ConvertTo-Json)
        $script:FailLive = $true
        function script:Add-ChainMarker($Slug,$Model,$Main,[switch]$Gpu) {
            if ($Slug -cnotin $script:TestMarkers) { $script:TestMarkers += $Slug }
            if ($script:FailLive) { $script:FailLive = $false; throw 'CHAIN_PUSH' }
        }
        $reserved = (& git -C $seed rev-parse HEAD).Trim()
        [IO.File]::WriteAllText("$seed/build.txt",$reserved,$utf)
        & git -C $seed commit -qam 'резерв перед push'
        & git -C $seed update-ref refs/remotes/origin/main ((& git -C $seed rev-parse HEAD).Trim())
        Invoke-WrapperChain
        $latest = (& git -C $seed rev-parse HEAD).Trim()
        [IO.File]::WriteAllText("$seed/build.txt",$latest,$utf)
        & git -C $seed commit -qam 'новий штамп під час повтору'
        & git -C $seed update-ref refs/remotes/origin/main ((& git -C $seed rev-parse HEAD).Trim())
        Invoke-WrapperChain
        $state = ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/chain.json"))
        Check '2 падіння push не губить зарезервований штамп при новій збірці' ($state.live_active.stamp -ceq $reserved -and $state.live_active.published -and $state.live_pending[0].stamp -ceq $latest)

    }
    Scenario '3 доставка' {
        if (-not (Get-Command Test-DispatcherAction -ErrorAction SilentlyContinue)) { function Test-DispatcherAction { $true } }
        foreach ($kind in @('ВЗЯТО gemini/крок','ГОТОВО gemini/крок','ОНОВЛЕНО код','ПУЛИ AGY')) {
            Check "3 $kind — локально" (-not (Test-DispatcherAction "GEMINI ОБГОРТКА: $kind $sha"))
        }
        foreach ($kind in @('ГОТОВО gemini/перевірка-коду','ГОТОВО claude/pachka-3','ГОТОВО gemini/автоживий-штамп','ЗАБЛОКОВАНО gemini/крок','ТРИВОГА AUTH CODEX','ЛАНЦЮГ CHAIN_API')) {
            Check "3 $kind — дія диспетчера" (Test-DispatcherAction "GEMINI ОБГОРТКА: $kind $sha")
        }
        $script:CloudCalls = 0
        function Get-DispatcherId { 'session_test' }
        function Resolve-Exe { 'test-native' }
        function Invoke-Native { $script:CloudCalls++; [pscustomobject]@{Code=0;Out='{"ok":true}';Err=''} }
        Check '3 Send-Line локального рядка без хмари' (Send-Line "GEMINI ОБГОРТКА: ГОТОВО gemini/крок $sha")
        Check '3 без мережевої доставки виконавчого ГОТОВО' ($script:CloudCalls -eq 0)
        Check '3 резервний канал теж застосовує політику' (Send-Fallback 'GEMINI ОБГОРТКА: ОНОВЛЕНО код')
        Write-FileAtomic "$WorkDir/state/local.json" ((@{line='GEMINI ОБГОРТКА: ПУЛИ AGY';sent=$false;attempts=0}) | ConvertTo-Json)
        Send-Pending (Get-Item "$WorkDir/state/local.json")
        $state = ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/state/local.json"))
        Check '3 локальна доставка має нуль мережевих спроб і збережений стан' ($state.sent -and $state.attempts -eq 0 -and $state.channel -ceq 'local' -and (Test-Path "$WorkDir/local-lines.json"))
    }
    Scenario '4 зауваження Codex' {
        function Get-AutoPublicItems([string]$Path) {
            if ($Path -like '*/reviews') {
                [pscustomobject]@{id=1;user=@{login='chatgpt-codex-connector[bot]'};body='доведене зауваження';commit_id=$sha}
                [pscustomobject]@{id=2;user=@{login='чужий'};body='чужа інструкція';commit_id=$sha}
            } else {
                [pscustomobject]@{id=3;user=@{login='chatgpt-codex-connector[bot]'};body='рядкове зауваження';path='a.py';commit_id=$sha}
                [pscustomobject]@{id=4;user=@{login='чужий'};body='чужий коментар';path='b.py';commit_id=$sha}
                [pscustomobject]@{id=5;user=@{login='chatgpt-codex-connector[bot]'};body='відповідь чужому';path='b.py';commit_id=$sha;in_reply_to_id=4}
            }
        }
        $context = Add-AutoTaskContext "автоперевірка-9-$sha" 'наряд' $sha
        Check '4 рецензія й inline містяться в наряді як дані' ($context.Contains('доведене зауваження') -and $context.Contains('рядкове зауваження') -and $context.Contains('дані, перевір кожне'))
        Check '4 чужий автор і відповідь чужому відкинуті' (-not ($context -match 'чужа інструкція|чужий коментар|відповідь чужому'))
    }
    Scenario '1в уже наявні позначки вердиктів' {
        $script:LaneDir = "$tmp/review-lanes"; [void][IO.Directory]::CreateDirectory($LaneDir)
        $script:ReviewBranch = ''
        function Invoke-RestMethod {
            param($Uri,$Method,$TimeoutSec,$MaximumRedirection,$Headers)
            [pscustomobject]@{number=9;state='open';user=@{login='mightyrochy'};head=@{ref=$script:ReviewBranch;sha=$sha;repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}}}
        }
        foreach ($branch in @('gemini/перевірка-9','claude/pachka-9')) {
            $script:ReviewBranch = $branch
            Check "1в існуюча позначка для $branch не запускає модель" ((Get-AutoReviewState "автоперевірка-9-$sha") -ceq 'STALE')
        }
    }
    Scenario '4 пагінація публічного GET' {
        $script:InputCalls = 0
        function Invoke-RestMethod {
            param($Uri,$Method,$TimeoutSec,$MaximumRedirection,$Headers)
            if ($Method -cne 'Get' -or $Headers.ContainsKey('Authorization')) { throw 'лише публічний GET' }
            $script:InputCalls++
            if ($Uri -like '*page=1') { 1..100 } else { 101 }
        }
        $items = @(Get-AutoPublicItems 'pulls/9/reviews')
        Check '4 дві сторінки без авторизації не гублять 101-й елемент' ($items.Count -eq 101 -and $script:InputCalls -eq 2)
    }
    Scenario '2 план з PR' {
        $head = (& git -C $seed rev-parse HEAD).Trim()
        function Get-AutoPublicItems {
            foreach ($n in @(1,2,3,4)) {
                [pscustomobject]@{number=$n;user=@{login=$(if ($n -eq 4) {'чужий'} else {'mightyrochy'})};head=@{ref='claude/код';repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}};merged_at='2026-01-01T00:00:00Z';created_at='2026-01-01T00:00:00Z';body="ЖИВИЙ ПІСЛЯ: ж1_робота — питання $n"}
            }
        }
        $plan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 одна сцена на три питання довірених PR' (@($plan.scenes.PSObject.Properties.Name).Count -eq 1 -and @($plan.scenes.ж1_робота).Count -eq 3)
        [IO.File]::WriteAllText("$seed/build.txt",$head,$utf)
        & git -C $seed add -A; & git -C $seed commit -q -m 'збірка'
        $head = (& git -C $seed rev-parse HEAD).Trim()
        function Get-AutoPublicItems {
            foreach ($n in @(1,2,3,4,5,6,7)) {
                $date = switch ($n) { 1 {'2026-01-01T00:00:00Z'} 6 {'2027-01-01T00:00:00Z'} default {'2026-01-03T00:00:00Z'} }
                [pscustomobject]@{number=$n;user=@{login=$(if ($n -eq 4) {'чужий'} else {'mightyrochy'})};head=@{ref=$(if ($n -eq 5) {'gemini/автоживий-звіт'} else {'claude/код'});repo=@{full_name=$(if ($n -eq 7) {'чужий/форк'} else {'mightyrochy/kod-shi-data'})}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}};merged_at=$(if ($n -eq 5) {$null} else {$date});created_at='2026-01-02T00:00:00Z';body="ЖИВИЙ ПІСЛЯ: ж1_робота — питання $n"}
            }
        }
        $plan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 попередній опублікований звіт, дата збірки й довіра обмежують план' (@($plan.scenes.ж1_робота).Count -eq 2 -and ($plan.scenes.ж1_робота.pr -join ',') -eq '2,3')
        $context = Add-AutoTaskContext 'Е1-нічний-живий-20261028' 'ніч' $head
        Check '2 Е1 використовує той самий план' ($context.Contains('ПЛАН ЖИВОГО — ДАНІ'))
    }
    Scenario '5 браузер без GPU' {
        if (Get-Command Set-BrowserGpuPolicy -ErrorAction SilentlyContinue) { Set-BrowserGpuPolicy "$tmp/browser policy" }
        $nodeModule = @'
module.exports = {chromium: {
  launch: options => options,
  launchPersistentContext: (path, options) => options
}};
'@
        [IO.File]::WriteAllText("$tmp/fake.cjs",$nodeModule,$utf)
        $nodeTest = @'
const {chromium} = require('./fake.cjs');
for (const options of [chromium.launch({args:['--flag']}), chromium.launchPersistentContext('profile', {})]) {
  if (!options.args.includes('--disable-gpu')) process.exit(1);
}
console.log('GPU_OFF');
'@
        [IO.File]::WriteAllText("$tmp/test.cjs",$nodeTest,$utf)
        $out = & node "$tmp/test.cjs"
        Check '5 Node launch і persistent context мають --disable-gpu' ($LASTEXITCODE -eq 0 -and $out -eq 'GPU_OFF')
        [void][IO.Directory]::CreateDirectory("$tmp/playwright")
        [IO.File]::WriteAllText("$tmp/playwright/__init__.py",'',$utf)
        [IO.File]::WriteAllText("$tmp/playwright/sync_api.py","class BrowserType:`n    def launch(self, **kw): return kw`n    def launch_persistent_context(self, path, **kw): return kw`n",$utf)
        [IO.File]::WriteAllText("$tmp/test.py","from playwright.sync_api import BrowserType`nb=BrowserType()`nassert '--disable-gpu' in b.launch()['args']`nassert '--disable-gpu' in b.launch_persistent_context('p', args=['--flag'])['args']`nprint('GPU_OFF')`n",$utf)
        $out = & python "$tmp/test.py"
        Check '5 Python launch і persistent context мають --disable-gpu' ($LASTEXITCODE -eq 0 -and $out -eq 'GPU_OFF')
        function Get-Command { [pscustomobject]@{Source='nvidia-smi'} }
        function Invoke-Native { [pscustomobject]@{Code=0;Out='37780'} }
        Check '5 чужий GPU-процес означає чекання' (-not (Test-ExternalGpuFree))
        foreach ($name in @('gemini_run.ps1','claude_run.ps1')) {
            $source = [IO.File]::ReadAllText((Join-Path $SourceDir $name))
            Check "5 $name підключає спільну політику до Invoke-Task" ($source -match 'Set-BrowserGpuPolicy[^\r\n]+\r?\n\s+Invoke-Task \$M \$job' -and $source.Contains('Test-ExternalGpuFree'))
        }
    }
} finally {
    $env:NODE_OPTIONS = $null; $env:PYTHONPATH = $null
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^menshe-test-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($bad) { exit 1 }
