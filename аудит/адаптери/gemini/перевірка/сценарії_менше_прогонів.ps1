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
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir,"$WorkDir/state","$WorkDir/seen",$OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $config = [pscustomobject]@{codex='gpt-review';agy='gemini-review';claude='cc-claude-review'}
    $sha = 'a' * 40
    Scenario '1а фактична модель' {
        foreach ($model in @('gpt-6.1-sol-high','gemini-3.8-flash-high','cc-claude-opus-5-5-high','невідома')) {
            $pull = [pscustomobject]@{head=@{ref='gemini/виконавець';sha=$sha}}
            # Файл моделі попередньої ітерації (та сама гілка й SHA) не має підміняти невідому модель.
            Remove-Item -LiteralPath "$WorkDir/engine-models" -Recurse -Force -ErrorAction SilentlyContinue
            Save-DraftRequest $pull.head.ref $sha $model
            $models = @(Get-ReviewModels $pull $config)
            $expected = if ($model -like 'gpt-*' -or $model -like 'cc-*') { $config.agy } else { $config.codex }
            Check "1а $model — рівно один інший постачальник" ($models.Count -eq 1 -and $models[0] -ceq $expected)
        }
    }
    Scenario '1а модель із прийнятого рядка' {
        Write-FileAtomic "$WorkDir/state/model.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/стан $sha МОДЕЛЬ gpt-6.1-sol-high"}) | ConvertTo-Json)
        $models = @(Get-ReviewModels ([pscustomobject]@{head=@{ref='gemini/стан';sha=$sha}}) $config)
        Check '1а фактичний GPT із ГОТОВО вибирає agy без файла моделі' ($models.Count -eq 1 -and $models[0] -ceq $config.agy)
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
        function script:Get-ChainPullRisk { -1 }
        function script:Test-LiveModels { $true }
        function script:Add-ChainMarker($Slug,$Model,$Main,[switch]$Gpu) { $script:TestMarkers += $Slug }
        # Клон стенда без origin; зняття мертвих позначок на справжньому origin міряє сценарії_ланцюга.ps1.
        function script:Remove-DeadReviewMarkers { }
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
        $planRepo = Join-Path $tmp 'plan'
        [void][IO.Directory]::CreateDirectory($planRepo)
        & git -C $planRepo init -q -b main
        & git -C $planRepo config user.name 'Стенд'
        & git -C $planRepo config user.email 'stand@local'
        $script:RepoDir = $planRepo; $script:Repo = $planRepo
        function Plan-Commit([string]$Date, [string]$Name) {
            <# Детермінована історія відрізняє склад збірки від часу публікації звіту. #>
            $author = $env:GIT_AUTHOR_DATE; $committer = $env:GIT_COMMITTER_DATE
            try {
                $env:GIT_AUTHOR_DATE = $Date; $env:GIT_COMMITTER_DATE = $Date
                & git -C $planRepo add -A
                & git -C $planRepo commit -q --allow-empty -m $Name
                if ($LASTEXITCODE) { throw 'Не створено коміт плану' }
                (& git -C $planRepo rev-parse HEAD).Trim()
            } finally { $env:GIT_AUTHOR_DATE = $author; $env:GIT_COMMITTER_DATE = $committer }
        }
        # Планувальник читає реєстр сцен із дерева збірки: без нього план не складається.
        [void][IO.Directory]::CreateDirectory("$planRepo/аудит/проби")
        [IO.File]::WriteAllText("$planRepo/аудит/проби/живі_сцени.txt", [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf), $utf)
        $old = Plan-Commit '2026-01-01T00:00:00Z' 'Попередній код'
        [IO.File]::WriteAllText("$planRepo/build.txt", $old, $utf)
        $checked = Plan-Commit '2026-01-02T00:00:00Z' 'Збірка попереднього прогону'
        # PR зливається після старту, але до створення звіту о 04:00.
        $during = Plan-Commit '2026-01-02T03:00:00Z' 'PR під час прогону'
        $later = Plan-Commit '2026-01-03T00:00:00Z' 'Наступний PR'
        [IO.File]::WriteAllText("$planRepo/build.txt", $later, $utf)
        $head = Plan-Commit '2026-01-04T00:00:00Z' 'Наступна збірка'
        $future = Plan-Commit '2026-01-05T00:00:00Z' 'Майбутній PR'
        $script:PlanPulls = @()
        function Get-AutoPublicItems { $script:PlanPulls }
        foreach ($n in @(1,2,3,4,6,7)) {
            $commit = switch ($n) { 1 {$old} 2 {$during} 6 {$future} default {$later} }
            $date = switch ($n) { 1 {'2026-01-01T00:00:00Z'} 2 {'2026-01-02T03:00:00Z'} 6 {'2026-01-05T00:00:00Z'} default {'2026-01-03T00:00:00Z'} }
            $script:PlanPulls += [pscustomobject]@{number=$n;user=@{login=$(if ($n -eq 4) {'чужий'} else {'mightyrochy'})};head=@{ref='claude/код';repo=@{full_name=$(if ($n -eq 7) {'чужий/форк'} else {'mightyrochy/kod-shi-data'})}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}};merge_commit_sha=$commit;merged_at=$date;created_at=$date;body="ЖИВИЙ ПІСЛЯ: ж1_робота — питання $n"}
        }
        # Без попереднього звіту всі три довірені питання утворюють одну сцену.
        $plan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 одна сцена на три питання довірених PR' (@($plan.scenes.PSObject.Properties.Name).Count -eq 1 -and @($plan.scenes.ж1_робота).Count -eq 3)
        $report = [pscustomobject]@{number=5;user=@{login='mightyrochy'};head=@{ref="gemini/автоживий-$old";repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}};merged_at=$null;created_at='2026-01-02T04:00:00Z';body="ПЕРЕВІРЕНО ЗБІРКУ: $checked"}
        $script:PlanPulls += $report
        $plan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 злитий під час прогону PR входить у наступний план' (2 -in @($plan.scenes.ж1_робота.pr))
        Check '2 попередній опублікований звіт, склад збірки й довіра обмежують план' (@($plan.scenes.ж1_робота).Count -eq 2 -and ($plan.scenes.ж1_робота.pr -join ',') -eq '2,3')
        $context = Add-AutoTaskContext 'Е1-нічний-живий-20261028' 'ніч' $head
        Check '2 Е1 використовує той самий план' ($context.Contains('ПЛАН ЖИВОГО — ДАНІ') -and $context.Contains((Get-AutoLivePlan $head)))
        $report.head.ref = 'gemini/Е1-нічний-живий-20260102'
        $nightPlan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 нічний звіт теж задає перевірену збірку' (($nightPlan.scenes.ж1_робота.pr -join ',') -eq '2,3')
        $report.body = 'Старий звіт без SHA'; $report.head.ref = "gemini/автоживий-$old"
        $stampPlan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 штамп у назві автоживого зберігає межу старого звіту' (($stampPlan.scenes.ж1_робота.pr -join ',') -eq '2,3')
        $report.head.ref = 'gemini/Е1-нічний-живий-20260102'
        $unknownPlan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 нічний звіт без перевіреного SHA не губить питання' (@($unknownPlan.scenes.ж1_робота).Count -eq 3)
        $report.body = "ПЕРЕВІРЕНО ЗБІРКУ: $future"
        $futurePlan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 звіт майбутньої збірки не звужує поточний план' (@($futurePlan.scenes.ж1_робота).Count -eq 3)
        $report.body = "ПЕРЕВІРЕНО ЗБІРКУ: $head"
        $samePlan = ConvertFrom-Json (Get-AutoLivePlan $head)
        Check '2 уже перевірена збірка має порожній план' (@($samePlan.scenes.PSObject.Properties).Count -eq 0)
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
        function Get-GpuCounterRows { $null }
        function Invoke-Native { [pscustomobject]@{Code=0;Out='37780'} }
        Check '5 чужий GPU-процес означає чекання' (-not (Test-ExternalGpuFree))
        # Випадок 29.10: після перезапуску 14:26 UTC nvidia-smi називає в --query-compute-apps порожній AvastUI (57 MiB), і кожен
        # GPU-наряд (автоживий, Е3-наживо) стояв у черзі 6+ год. ДО — старий предикат; ПІСЛЯ — вільна пам'ять і навантаження.
        function Invoke-Native {
            param($Exe, $Arguments)
            if ($Arguments -contains '--query-compute-apps=pid,used_memory') { return [pscustomobject]@{Code=0;Out='23660, [N/A]'} }
            if ($Arguments -contains '--query-gpu=memory.total,memory.free,utilization.gpu') { return [pscustomobject]@{Code=0;Out='16376, 16319, 0'} }
            [pscustomobject]@{Code=1;Out='';Err='невідомий виклик'}
        }
        $old = (Invoke-Native 'nvidia-smi' @('--query-compute-apps=pid,used_memory')).Out.Trim()
        Check '5 ДО: перелік compute-процесів із порожнім AvastUI не порожній (старий предикат давав «зайнята»)' ($old -ne '')
        Check '5 ПІСЛЯ: 57 MiB від AvastUI — GPU вільна' (Test-ExternalGpuFree)
        $script:Logged = @(); $LaneDir = $tmp
        function Write-Log([string]$Text) { $script:Logged += $Text }
        Check '5 ПІСЛЯ: причина зайнятості порожня' ((Get-GpuBusyReason @()) -eq '')
        function Invoke-Native { param($Exe, $Arguments) [pscustomobject]@{Code=0;Out='16376, 7376, 0'} }
        Check '5 чужа модель (9000 MiB) — причина називає залишок і потребу' ((Get-GpuBusyReason @()) -match 'вільно 7376 з потрібних 8925 MiB')
        $m = [pscustomobject]@{Name='gemini-queue/Е3-наживо/gpt-6.1-sol-high/1/p1-gpu'}
        $skip = Join-Path $tmp 'skipped.json'
        Add-Skip $m 'GPU: тест'; Save-Skips $skip
        $since = ([IO.File]::ReadAllText($skip,$utf) | ConvertFrom-Json).since
        Start-Sleep -Seconds 1
        Add-Skip $m 'GPU: тест'; Save-Skips $skip
        Check '5 мовчазний пропуск лишає рядок журналу один раз, since не зсувається' (@($script:Logged | Where-Object { $_ -like '*не стартує*' }).Count -eq 1 -and ([IO.File]::ReadAllText($skip,$utf) | ConvertFrom-Json).since -eq $since)
        Save-Skips $skip
        Check '5 позначка, що стартувала, зникає з файла пропусків' (([IO.File]::ReadAllText($skip,$utf)).Trim() -eq '[]')
        Add-Note (Join-Path $tmp 'blocked-reasons.json') 'gemini/крок' ('ЗАБЛОКОВАНО: суперечливі вимоги' + [char]13 + [char]10 + 'другий рядок')
        Check '5 причина BLOCKED без гілки — один рядок у файлі для #1856' ((@([IO.File]::ReadAllText((Join-Path $tmp 'blocked-reasons.json'),$utf) | ConvertFrom-Json)[0].text) -eq 'ЗАБЛОКОВАНО: суперечливі вимоги другий рядок')
        # Test-TaskFile: вирок «нема» лише від git; збій — виняток (позначка вертається в чергу), не NO_TASK_FILE.
        function Start-Sleep { }
        $script:Git = @()
        function Invoke-Git { param($GitArgs, [switch]$AllowFail) $script:Calls++; $script:Git[0] }
        $script:Calls = 0; $script:Git = @([pscustomobject]@{Code=128;TimedOut=$false;Err='fatal: unable to read tree (abc)'})
        $threw = $false; try { [void](Test-TaskFile ('a'*40) 'аудит/наряди/х.md') } catch { $threw = $true }
        Check '5 збій git cat-file після 3 спроб — виняток, не NO_TASK_FILE' ($threw -and $script:Calls -eq 3)
        $script:Git = @([pscustomobject]@{Code=128;TimedOut=$false;Err="fatal: path 'x' does not exist in 'abc'"})
        Check '5 git каже «нема» — вирок без повторів' ((-not (Test-TaskFile ('a'*40) 'x')) -and $script:Calls -eq 4)
        $script:Git = @([pscustomobject]@{Code=0;TimedOut=$false;Err=''})
        Check '5 файл є — істина' (Test-TaskFile ('a'*40) 'x')
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
