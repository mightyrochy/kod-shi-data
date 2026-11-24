#Requires -Version 5.1
param([Alias('WrapperRoot')][string]$SourceDir = (Split-Path -Parent $PSScriptRoot), [ValidateSet('ДО','ПІСЛЯ')][string]$Phase = 'ПІСЛЯ')
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
    $script:Pulls = @(); $script:Files = @{}; $script:Requests = @(); $script:FailPage = ''
    function Get-ChainPulls { $script:Pulls }
    function Complete-EngineDrafts { }
    function Test-LiveModels { $true }
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
    function Merge([string]$Path, [string]$Text, [string]$Subject = 'злиття') {
        <# Створює наступний main і отримує його справжнім fetch. #>
        [IO.File]::WriteAllText((Join-Path $seed $Path), $Text, $utf)
        & git -C $seed add -A; & git -C $seed commit -q -m $Subject; & git -C $seed push -q origin main
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        Get-RefSha 'refs/remotes/origin/main'
    }
    Invoke-WrapperChain
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
    $product = Merge 'джерела/a.py' '2'
    $merged = Pull 21
    $merged | Add-Member -NotePropertyName body -NotePropertyValue 'ЖИВИЙ ПІСЛЯ: с1_весілля — Чи проходить мірило?'
    $merged | Add-Member -NotePropertyName merged_at -NotePropertyValue ([datetimeoffset]::UtcNow.ToString('o'))
    $merged | Add-Member -NotePropertyName merge_commit_sha -NotePropertyValue $product
    $script:Pulls = @()
    Invoke-WrapperChain
    Check 'черга перед збіркою порожня' (@(Markers '.*').Count -eq 0)
    $built = Merge 'build.txt' $product "збірка: $product"
    # API відкритих PR не повертає вже злитий PR, навіть якщо він має рядок ЖИВИЙ ПІСЛЯ.
    function Invoke-ChainApi([string]$Path) {
        if ($Path -match 'pulls[?].*state=(all|closed)') { $merged }
    }
    Invoke-WrapperChain
    $expected = if ($Phase -eq 'ДО') { 1 } else { 0 }
    $liveCount = @(Markers '/автоживий-').Count
    Check "злито PR із ЖИВИЙ ПІСЛЯ, нова збірка: позначок автоживий-* — $liveCount" ($liveCount -eq $expected)
    if ($Phase -eq 'ПІСЛЯ') {
        $state = Join-Path $WorkDir 'chain.json'
        function Save-OldLiveState([bool]$Published) {
            <# Збережений стан публікатора до вимкнення самопостановки. #>
            Write-FileAtomic $state ((@{main=$built;reviewed=@{};reviews=@();
                live_stamps=@($product);live_active=@{stamp=$product;main=$built;published=$Published};live_pending=@()}) | ConvertTo-Json -Depth 5)
        }
        Save-OldLiveState $false
        Invoke-WrapperChain
        Check 'старий неопублікований резерв залишає чергу порожньою' (@(Markers '/автоживий-').Count -eq 0)
        # Позначку ставить окремий актор стенда лише в тимчасовий origin.
        $slug = "автоживий-$product"
        $model = 'gpt-6.1-sol-high'
        $queue = "gemini-queue/$slug/$model/1/p2-gpu"
        $ref = "refs/heads/$queue"
        & git -C $seed push -q origin "${built}:$ref"
        if ($LASTEXITCODE -ne 0) { throw 'стенд не записав вхідну позначку диспетчера' }
        # Старий ланцюг переносив опубліковану позначку, коли Codex на квоті, а Claude доступний.
        [void][IO.Directory]::CreateDirectory("$OutDir/marker-state")
        Write-FileAtomic "$OutDir/marker-state/ready" '1'
        $now = [datetimeoffset]::UtcNow
        $quota = @{codex=@{refused=$now.AddMinutes(-1).UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ss'Z'");
            reset=$now.AddHours(2).UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ss'Z'")}}
        Write-FileAtomic "$OutDir/heartbeat.json" ($quota | ConvertTo-Json -Depth 3)
        $available = 'cc-claude-sonnet-5-5-medium'
        Check 'перед проходом позначка нова, Codex на квоті й інший рушій доступний' (
            (Get-ChainMarkerState $queue $built $model).Kind -ceq 'NEW' -and (Test-ModelQuota $model $now) -and
            -not (Test-ModelQuota $available $now))
        Save-OldLiveState $true
        Invoke-WrapperChain
        $refs = @(Markers '/автоживий-')
        Check 'старий опублікований стан за умов перенесення зберігає єдину позначку й її SHA' (
            $refs.Count -eq 1 -and $refs[0] -ceq $ref -and (& git -C $remote rev-parse $ref).Trim() -ceq $built)
        # Перевіряємо й старий стан на момент появи наступної збірки.
        Save-OldLiveState $true
        $next = Merge 'джерела/a.py' '3'
        [void](Merge 'build.txt' $next "збірка: $next")
        Invoke-WrapperChain
        $refs = @(Markers '/автоживий-')
        Check 'нова збірка зберігає єдину позначку диспетчера на її SHA' (
            $refs.Count -eq 1 -and $refs[0] -ceq $ref -and (& git -C $remote rev-parse $ref).Trim() -ceq $built)
        # Консоль задачі планувальника розірвана (10.11 23:04: «No process is on the other end of the pipe»): сетер
        # Console.InputEncoding кидає, але запуск процесу й stdin без BOM не залежать від нього — прохід не рветься.
        $keyFile = Join-Path $tmp 'key.txt'; [IO.File]::WriteAllText($keyFile, 'ключ', $utf)
        $keyHash = (& git hash-object --no-filters $keyFile).Trim()
        # Консоль CI — кодова сторінка без BOM; локально (chcp 65001) її кодування саме додає BOM, тож приймаємо обидва вигляди.
        [IO.File]::WriteAllText($keyFile, 'ключ', (New-Object Text.UTF8Encoding($true)))
        $keyHashBom = (& git hash-object --no-filters $keyFile).Trim()
        function Set-ConsoleInputEncoding($Encoding) { throw 'No process is on the other end of the pipe.' }
        $viaPublish = Invoke-Native 'git' @('hash-object', '--stdin') $tmp 1 'ключ'
        Check 'Invoke-Native публікації: сетер кодування кидає — процес запущено, stdin доставлено' ($viaPublish.Code -eq 0 -and $viaPublish.Out.Trim() -cin @($keyHash, $keyHashBom))
        . (Join-Path $SourceDir 'gemini_run.ps1') -RepoDir $seed -RunsDir "$tmp/runs" -OutDir "$tmp/gem-out" -LaneDir "$tmp/lanes" -EnableCodex
        $script:StateDir = "$tmp/state"; $script:SlotDir = "$tmp/slots"
        $script:Limits = @{slots=@{codex=1;agy=1}}
        foreach ($dir in @($RunsDir,$OutDir,$LaneDir,$script:StateDir,$script:SlotDir)) { [void][IO.Directory]::CreateDirectory($dir) }
        function Set-ConsoleInputEncoding($Encoding) { throw 'No process is on the other end of the pipe.' }
        $viaLanes = Invoke-Native 'git' @('hash-object', '--stdin') $tmp 1 'ключ'
        Check 'Invoke-Native черги: сетер кодування кидає — процес запущено, stdin доставлено' ($viaLanes.Code -eq 0 -and $viaLanes.Out.Trim() -cin @($keyHash, $keyHashBom))
        function Get-AutoLivePlan { '{}' }
        [void](Invoke-Git @('fetch','-q','origin',"${ref}:refs/remotes/origin/$queue"))
        $marker = @(Get-Markers)
        Check 'смуга читає дійсну GPU-позначку диспетчера з точною збіркою' ($marker.Count -eq 1 -and $marker[0].Valid -and $marker[0].Gpu -and $marker[0].Sha -ceq $built)
        $context = Add-AutoTaskContext $marker[0].Slug 'Наряд' $marker[0].Sha
        Check 'наряд призначає дерево збірки й окремо називає штамп джерел' ((Get-TaskSource $marker[0]) -ceq 'аудит/наряди/автоживий.md' -and $context.Contains("коміт збірки $built") -and $context.Contains("штамп build.txt $product"))
        function Repair-GpuModels { }
        function Remove-OrphanWaits { }
        function Stop-GpuStalledRuns { }
        function Get-GpuBusyReason { '' }
        function Test-SlugBusy { $false }
        function Select-Engine {
            [pscustomobject]@{Engine=@{Name='codex';Model='стенд';Effort='high'};Model=$marker[0].Model;Quota=@{Blocked=$false;Known=$false;Left=0;Group=''}}
        }
        function Get-FreeSlot { 'codex-1' }
        $script:StartedJob = $null
        function Start-Worker($Job, [string]$Dir) {
            $script:StartedJob = $Job
            [pscustomobject]@{Slug=$Job.slug;Proc=@{HasExited=$true}}
        }
        $workers = New-Object Collections.ArrayList
        $started = Start-Markers $workers
        Check 'смуга взяла позначку диспетчера й передала її точний SHA процесу' ($started -eq 1 -and (Get-MarkerState $marker[0]).Kind -ceq 'TAKEN' -and $script:StartedJob.sha -ceq $built -and $script:StartedJob.slug -ceq $slug)

        & git -C $seed checkout -q --detach $built
        & git -C $seed commit -q --allow-empty -m 'ЗНЯТО: рішення диспетчера'
        & git -C $seed push -q origin "HEAD:$ref"
        if ($LASTEXITCODE -ne 0) { throw 'стенд не записав ЗНЯТО' }
        [void](Invoke-Git @('fetch','-q','origin',"${ref}:refs/remotes/origin/$queue"))
        $cancelled = @(Get-Markers)[0]
        Check 'голова ЗНЯТО розпізнається для позначки автоживого' ($cancelled.Slug -ceq $slug -and (Test-MarkerCancelled $cancelled) -and $cancelled.Reason -ceq 'рішення диспетчера')
    }
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^chain-build-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($failures) { exit 1 }
