#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot), [ValidateSet('ДО','ПІСЛЯ')][string]$Phase = 'ПІСЛЯ')
$ErrorActionPreference = 'Stop'
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('chain-build-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Друкує вимір і повертає помилку, якщо фаза не відповідає очікуванню. #>
    if ($Ok) { "✓ $Phase $Name" } else { "✗ $Phase $Name"; $script:failures++ }
}
try {
    $seed = Join-Path $tmp 'seed'; $remote = Join-Path $tmp 'origin.git'; $bare = Join-Path $tmp 'repo.git'
    & git init -q --bare $remote; & git init -q -b main $seed
    & git -C $seed config core.autocrlf false
    & git -C $seed config user.name 'стенд'; & git -C $seed config user.email 'stend@example.invalid'
    & git -C $seed remote add origin $remote
    foreach ($dir in @('аудит/наряди','аудит/адаптери/gemini','джерела')) { [void][IO.Directory]::CreateDirectory((Join-Path $seed $dir)) }
    Copy-Item -LiteralPath (Join-Path $SourceDir 'ланцюг.json') -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
    foreach ($task in @('автоперевірка','автоживий')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md", $task, $utf) }
    [IO.File]::WriteAllText("$seed/джерела/a.py", '1', $utf)
    & git -C $seed add -A; & git -C $seed commit -q -m 'початкова'; & git -C $seed push -q origin main
    & git clone -q --bare $remote $bare
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out" -UpdateRoot "$tmp/update"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $script:Repo = $bare; $script:NoHooks = Join-Path $tmp 'no-hooks'
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    $head = Get-RefSha 'refs/remotes/origin/main'
    $script:Pulls = @(); $script:Files = @{}; $script:Requests = @(); $script:FailPage = ''; $script:Ready = $true
    function Get-ChainPulls { $script:Pulls }
    function Complete-EngineDrafts { }
    function Test-LiveModels($Config) { $script:Ready }
    function Invoke-ChainApi([string]$Path) {
        <# Відповіді саме REST files: відмова другої сторінки не приховує неповний список. #>
        $script:Requests += $Path
        if ($Path -match '/pulls/([0-9]+)/files\?per_page=100&page=([0-9]+)$') {
            $key = "$($Matches[1])/$($Matches[2])"
            if ($script:FailPage -eq $key) { throw 'CHAIN_API' }
            return $script:Files[$key]
        }
        [pscustomobject]@{sha=($Path -split '/')[-1];commit=@{committer=@{date=[datetimeoffset]::UtcNow.ToString('o')}}}
    }
    function Pull([int]$Number, [string]$Title = 'Код') {
        <# Довірений PR зі свіжою головою; назва не потрапляє до наряду. #>
        [pscustomobject]@{number=$Number;title=$Title;created_at=[datetimeoffset]::UtcNow.ToString('o');user=@{login='mightyrochy'};head=@{ref="claude/зміна-$Number";sha=$head;repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}}}
    }
    function Markers([string]$Pattern) {
        <# Реальні Git refs відокремленого origin, а не лічильник викликів функції. #>
        @(& git -C $remote for-each-ref '--format=%(refname)' refs/heads/gemini-queue/ | Where-Object { $_ -match $Pattern })
    }
    function Merge([string]$Path, [string]$Text) {
        <# Створює наступний main і отримує його справжнім fetch. #>
        [IO.File]::WriteAllText((Join-Path $seed $Path), $Text, $utf)
        & git -C $seed add -A; & git -C $seed commit -q -m 'злиття'; & git -C $seed push -q origin main
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        Get-RefSha 'refs/remotes/origin/main'
    }
    Invoke-WrapperChain
    $after = $Phase -eq 'ПІСЛЯ'; $skip = if ($after) { 0 } else { 1 }
    # Позначки автоперевірок ставить диспетчер: за будь-якого складу файлів PR ланцюг їх не ставить і список файлів не читає.
    $paths = @('аудит/наряди/крок.md','джерела/a.py','.github/workflows/a.yml','аудит/адаптери/gemini/a.ps1','аудит/проби/a.py','каталог/a.json','a.py')
    $n = 1
    foreach ($path in $paths) { $script:Files["$n/1"] = @([pscustomobject]@{filename=$path}); $n++ }
    $script:Files['20/1'] = @(1..100 | ForEach-Object { [pscustomobject]@{filename="аудит/наряди/$_.md"} }); $script:Files['20/2'] = @([pscustomobject]@{filename='джерела/останній.py'})
    $script:FailPage = '20/2'
    $script:Pulls = @(@(1..$paths.Count | ForEach-Object { Pull $_ }) + (Pull 19 '[НЕ ЗЛИВАТИ] Код') + (Pull 20)); Invoke-WrapperChain
    Check "PR коду й документів, [НЕ ЗЛИВАТИ], дві сторінки файлів, збій сторінки: позначок автоперевірки=$(@(Markers 'автоперевірка-').Count)" (@(Markers 'автоперевірка-').Count -eq 0)
    Check 'список файлів PR ланцюг не читає' (@($script:Requests | Where-Object { $_ -match '/files\?' }).Count -eq 0)
    $script:FailPage = ''
    $script:Pulls = @()
    $product = Merge 'джерела/a.py' '2'; Invoke-WrapperChain
    Check "злиття без збірки: автоживих=$(@(Markers 'автоживий-').Count)" (@(Markers 'автоживий-').Count -eq $skip)
    $built = Merge 'build.txt' $product; Invoke-WrapperChain
    $expected = if ($after) { 1 } else { 2 }
    Check "злиття → збірка: автоживих=$(@(Markers 'автоживий-').Count)" (@(Markers 'автоживий-').Count -eq $expected)
    if ($after) {
        $ref = @(Markers "автоживий-$product/")[0]
        Check 'ключ — штамп джерел, ref — перший коміт готової збірки' ((& git -C $remote rev-parse $ref).Trim() -ceq $built)
    }
    # Новий процес: тільки збережений стан і refs, без пам'яті поточного процесу.
    $child = Join-Path $tmp 'restart.ps1'
    $childText = @"
`$ErrorActionPreference = 'Stop'
. '$((Join-Path $SourceDir 'gemini_publish.ps1').Replace("'","''"))' -WorkDir '$($WorkDir.Replace("'","''"))' -OutDir '$($OutDir.Replace("'","''"))' -OutboxDir '$($OutboxDir.Replace("'","''"))'
`$GeminiRunsDir = '$($GeminiRunsDir.Replace("'","''"))'
`$script:Repo = '$($bare.Replace("'","''"))'
`$script:NoHooks = '$($script:NoHooks.Replace("'","''"))'
function Get-ChainPulls { @() }
function Complete-EngineDrafts { }
function Test-LiveModels { `$true }
Invoke-WrapperChain
"@
    [IO.File]::WriteAllText($child, $childText, (New-Object Text.UTF8Encoding($true)))
    & (Get-Process -Id $PID).Path -NoProfile -ExecutionPolicy Bypass -File $child
    Check 'перезапуск процесу не дублює штамп' ($LASTEXITCODE -eq 0 -and @(Markers 'автоживий-').Count -eq $expected)
    if ($after) {
        $script:Ready = $false
        $second = Merge 'джерела/a.py' '3'; Invoke-WrapperChain
        $secondBuild = Merge 'build.txt' $second
        $third = Merge 'джерела/a.py' '4'
        $thirdBuild = Merge 'build.txt' $third
        $later = Merge 'опис.md' 'після збірки'; Invoke-WrapperChain
        $state = ConvertFrom-Json ([IO.File]::ReadAllText((Join-Path $WorkDir 'chain.json')))
        Check 'два штампи згорнуто до останнього, поки попередній активний' ($state.live_pending.Count -eq 1 -and $state.live_pending[0].stamp -ceq $third)
        $script:Ready = $true; Invoke-WrapperChain
        Check 'активний прогін не породжує наступної позначки' (@(Markers 'автоживий-').Count -eq 1)
        [void][IO.Directory]::CreateDirectory((Join-Path $WorkDir 'state'))
        Write-FileAtomic (Join-Path $WorkDir 'state/report.json') ((@{slug="автоживий-$product";line="GEMINI ОБГОРТКА: ГОТОВО gemini/автоживий-$product $built"}) | ConvertTo-Json)
        Invoke-WrapperChain
        Check 'після звіту лише останній штамп має позначку на коміті своєї збірки' (@(Markers 'автоживий-').Count -eq 2 -and @(Markers "автоживий-$second/").Count -eq 0 -and (& git -C $remote rev-parse @(Markers "автоживий-$third/")[0]).Trim() -ceq $thirdBuild)
        $back = Merge 'build.txt' $product; Invoke-WrapperChain
        Check 'повтор старого штампу не ставить нового прогону' (@(Markers 'автоживий-').Count -eq 2)
        $bad = Merge 'build.txt' 'пошкоджено'; Invoke-WrapperChain
        Check 'пошкоджений штамп не створює позначки' (@(Markers 'автоживий-').Count -eq 2)
        . (Join-Path $SourceDir 'queue_lanes.ps1')
        function Get-AutoLivePlan { '{}' }
        $context = Add-AutoTaskContext "автоживий-$product" 'Наряд' $built
        Check 'наряд призначає дерево збірки й окремо називає штамп джерел' ($context.Contains("коміт збірки $built") -and $context.Contains("штамп build.txt $product"))
    }
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^chain-build-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($failures) { exit 1 }
