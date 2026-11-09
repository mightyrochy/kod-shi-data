#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot), [switch]$Before)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('sleep-stand-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Провал твердження червонить код виходу стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    Check 'Windows PowerShell 5.1' ($PSVersionTable.PSVersion.Major -eq 5 -and $PSVersionTable.PSVersion.Minor -eq 1)
    if ($Before) {
        . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/trusted"
        foreach ($dir in @($WorkDir,"$WorkDir/seen",$OutDir,$OutboxDir,$UpdateRoot)) { [void][IO.Directory]::CreateDirectory($dir) }
        function Get-RefSha { 'a'*40 }
        $id='20261102-003000-000000000001'
        $s=@{v=1;id=$id;slug='сон';model='gpt-test-high';n=1;marker=('a'*40);head='';cond='';code='STALL';turns=1;minutes=120;ahead=0;bundle='';started_utc='2026-11-02T00:30:00Z';ended_utc='2026-11-02T02:30:00Z'}
        Write-FileAtomic (Join-Path $OutDir ($id+'.json')) ($s|ConvertTo-Json -Compress)
        $result=Get-Line $id
        Check 'ДО: перерваний STALL одразу дає ЗАБЛОКОВАНО' ($result.Outbox -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/сон STALL')
        Check 'ДО: рядків СОН 0, запитів автоматичного повтору 0' (@(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt').Count -eq 0 -and @(Get-ChildItem -LiteralPath $UpdateRoot -Filter 'sleep-retry-*.json').Count -eq 0)
        exit ([int]($bad -gt 0))
    }
    $pub = New-Module -ArgumentList $SourceDir,$tmp -ScriptBlock {
        param($src,$tmp)
        . (Join-Path $src 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/trusted"
        foreach ($dir in @($WorkDir,"$WorkDir/seen",$OutDir,$OutboxDir,$UpdateRoot)) { [void][IO.Directory]::CreateDirectory($dir) }
        $script:MainHead = 'a'*40; $script:PublishedHead = 'b'*40; $script:OutputHead = 'c'*40
        $script:Marker = 'a'*40; $script:Queue = 'gemini-queue/сон/gpt-test-high/1'
        $script:PublishCode = 'OK'; $script:PublishCalls = 0
        $script:WakeRows = @([pscustomobject]@{ from='2026-11-02T01:00:00.0000000Z';to='2026-11-02T02:00:00.0000000Z';source='Power-Troubleshooter/1' })
        $script:Clock = [datetime]'2026-11-02T02:30:00Z'
        $script:Boot = $null
        function Test-UpdateRoot { $true }
        function Get-PowerTime { $script:Clock }
        function Get-PowerBoot { $script:Boot }
        function Get-WinEvent {
            <# XML подій підміняється, його розбирає справжній Get-WakeRows. #>
            foreach ($row in $script:WakeRows) {
                $value = [pscustomobject]@{ XmlText="<Event><EventData><Data Name='SleepTime'>$($row.from)</Data><Data Name='WakeTime'>$($row.to)</Data></EventData></Event>" }
                Add-Member -InputObject $value -MemberType ScriptMethod -Name ToXml -Value {$this.XmlText}
                $value
            }
        }
        function Get-RefSha([string]$Ref) {
            <# Підміна лише віддалених ref, які вже отримав fetch. #>
            if ($Ref -ceq "refs/remotes/origin/$script:Queue") { return $script:Marker }
            if ($Ref -ceq 'refs/remotes/origin/main') { return $script:MainHead }
            if ($Ref -ceq 'refs/remotes/origin/gemini/сон') { return $script:PublishedHead }
            ''
        }
        function Publish-Bundle($Status,[string]$Id) {
            <# Стенд перевіряє межу успішної публікації та відмови; мережевих викликів нема. #>
            $script:PublishCalls++
            if ($script:PublishCode -eq 'OK') { $script:PublishedHead = [string]$Status.head }
            @($script:PublishCode,1)
        }
        function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
            <# Тіло опублікованого коміту фікстури: після Publish-Bundle читач PR звіряє саме його. #>
            if ($GitArgs -contains '--format=%B') { return [pscustomobject]@{Code=0;Out='Звіт стенда сну';Err=''} }
            throw ('Неочікуваний git у стенді сну: ' + ($GitArgs -join ' '))
        }
        function Status([string]$Id,[string]$Code,[string]$Parent='',[bool]$Bundle=$true) {
            <# Явні UTC охоплюють підмінений сон. #>
            [pscustomobject][ordered]@{ v=1;id=$Id;slug='сон';model='gpt-test-high';n=1;marker=$script:Marker;head=$script:OutputHead;cond='';code=$Code;
                turns=1;minutes=120;ahead=1;bundle=$(if($Bundle){$Id+'.bundle'}else{''});started_utc='2026-11-02T00:30:00Z';ended_utc='2026-11-02T02:30:00Z';sleep_parent=$Parent }
        }
        function Save-Status($Status) { Write-FileAtomic (Join-Path $OutDir ($Status.id+'.json')) ($Status | ConvertTo-Json -Compress) }
        function Run {
            <# Один цикл: подія → рядок СОН → опублікований результат → дозвіл повтору. #>
            $badId='20261102-000000-000000000098'
            Write-FileAtomic (Join-Path $OutDir ($badId+'.json')) '{'
            $raw=Get-Line $badId -StatusOnly
            $bad=Get-Line $badId
            [pscustomobject]@{Name='читання невалідного JSON для лічби не споживає повідомлення STATE_INVALID';Ok=($null -eq $raw -and $bad.Outbox -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/невідомо STATE_INVALID')}
            Remove-Item -LiteralPath (Join-Path $OutDir ($badId+'.json'))
            $first = '20261102-003000-000000000001'
            $s = Status $first 'STALL'; Save-Status $s
            Write-FileAtomic (Join-Path $WorkDir 'sleep-events.json') ('{"read_utc":"2026-11-02T00:00:00Z","events":[]}')
            Update-SleepEvents; Update-SleepEvents
            $lines = @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt')
            $line = [IO.File]::ReadAllText($lines[0].FullName,$script:Utf8).Trim()
            [pscustomobject]@{Name='одна подія — один рядок СОН, нарядів 1';Ok=($lines.Count -eq 1 -and $line -ceq 'GEMINI ОБГОРТКА: СОН 2026-11-02T01:00:00Z → 2026-11-02T02:00:00Z, нарядів 1')}
            [pscustomobject]@{Name='рядок СОН проходить доставку';Ok=(-not (Test-OutboxLine $line))}
            [pscustomobject]@{Name='довільний текст у рядок СОН не проходить';Ok=([bool](Test-OutboxLine ($line+' зайве')))}
            $result = Get-Line $first
            $request = [IO.File]::ReadAllText((Join-Path $UpdateRoot ('sleep-retry-'+$first+'.json')),$script:Utf8) | ConvertFrom-Json
            [pscustomobject]@{Name='STALL_PUBLISHED — один повтор після публікації голови';Ok=($null -eq $result -and $script:PublishCalls -eq 1 -and $request.head -ceq $script:PublishedHead -and $request.head -ceq $script:OutputHead)}
            $requests = @(Get-ChildItem -LiteralPath $UpdateRoot -Filter 'sleep-retry-*.json').Count
            [void](Get-Line $first)
            [pscustomobject]@{Name='повтор обробки першого результату не дублює запит';Ok=(@(Get-ChildItem -LiteralPath $UpdateRoot -Filter 'sleep-retry-*.json').Count -eq $requests -and $script:PublishCalls -eq 1)}
            $requestPath = Join-Path $UpdateRoot ('sleep-retry-'+$first+'.json')
            $originalRequest = [IO.File]::ReadAllText($requestPath,$script:Utf8)
            Remove-Item -LiteralPath $requestPath
            [void](Get-Line $first)
            [pscustomobject]@{Name='збій після публікації не губить запит повтору';Ok=((Test-Path -LiteralPath $requestPath) -and $script:PublishCalls -eq 1)}
            $forgedFirst = Status '20261102-003000-000000000099' 'STALL'; Save-Status $forgedFirst
            [void](Get-Line $forgedFirst.id)
            [pscustomobject]@{Name='інший ID не повторює вже опубліковану позначку';Ok=(-not (Test-Path -LiteralPath (Join-Path $UpdateRoot ('sleep-retry-'+$forgedFirst.id+'.json'))))}
            $script:WakeRows = @([pscustomobject]@{from='2026-11-02T03:00:00Z';to='2026-11-02T04:00:00Z';source='Power-Troubleshooter/1'})
            $script:Clock = [datetime]'2026-11-02T04:30:00Z'
            Update-SleepEvents
            $second = Status '20261102-023000-000000000002' 'STALL' $first
            $second.started_utc='2026-11-02T02:30:00Z';$second.ended_utc='2026-11-02T04:30:00Z';$second.head='d'*40
            Save-Status $second
            $result = Get-Line $second.id
            [pscustomobject]@{Name='другий сон — ЗАБЛОКОВАНО, публікація повтору не губиться';Ok=($result.Outbox -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/сон STALL_PUBLISHED' -and $script:PublishedHead -ceq $second.head -and $script:PublishCalls -eq 2)}
            [pscustomobject]@{Name='другий сон не створює третього прогону';Ok=(@(Get-ChildItem -LiteralPath $UpdateRoot -Filter 'sleep-retry-*.json').Count -eq 1)}
            $forged = Status '20261102-043000-000000000003' 'DONE' '20261102-000000-ffffffffffff'
            Save-Status $forged; [void](Get-Line $forged.id)
            [pscustomobject]@{Name='поле sleep_parent без власного дозволу не відкриває публікацію';Ok=($script:PublishCalls -eq 2)}
            $script:SleepEvents = @([pscustomobject]@{key='e'*64;from='2026-11-02T01:00:00Z';to='2026-11-02T02:00:00Z'})
            foreach ($code in @('STALL','STALL_PUBLISHED','AGY_ERROR','BLOCKED','BLOCKED_PUBLISHED','INTERRUPTED')) {
                $s = Status $first $code '' $false
                [pscustomobject]@{Name="$code належить класу перерваних сном";Ok=(Request-SleepRetry $s $script:Queue $script:Marker '')}
            }
            Write-FileAtomic $requestPath $originalRequest
            $s = Status $first 'AGY_ERROR' '' $false; $s.started_utc='2026-11-02T01:30:00Z'
            [pscustomobject]@{Name='початок посеред сну не дає повтору';Ok=(-not (Request-SleepRetry $s $script:Queue $script:Marker ''))}
            $s.started_utc='2026-11-02T00:30:00Z';$s.ended_utc='2026-11-02T01:30:00Z'
            [pscustomobject]@{Name='кінець до пробудження не дає повтору';Ok=(-not (Request-SleepRetry $s $script:Queue $script:Marker ''))}
            $s.ended_utc='2026-11-02T02:30:00Z';$s.code='AUTH'
            [pscustomobject]@{Name='відмова входу не є дозволом на повтор';Ok=(-not (Request-SleepRetry $s $script:Queue $script:Marker ''))}
            $s.code='BLOCKED';$s.bundle=$first+'.bundle';$s.id='20261102-003000-000000000004'
            # Нова позначка — окремий незалежний наряд.
            $script:Marker='f'*40;$s.marker=$script:Marker;Save-Status $s
            $script:PublishCode='WRAPPER_FILES';$result=Get-Line $s.id
            [pscustomobject]@{Name='відмова запобіжника публікації не дає повтору';Ok=($result.Outbox -match ' WRAPPER_FILES$' -and -not (Test-Path -LiteralPath (Join-Path $UpdateRoot ('sleep-retry-'+$s.id+'.json'))))}
            # Новий процес читає збережений стан події й не створює другого рядка.
            $script:SleepEvents=@();$script:WakeRows=@();Update-SleepEvents
            [pscustomobject]@{Name='перезапуск публікатора зберігає дедуплікацію';Ok=(@(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt').Count -eq 2)}
            Write-FileAtomic (Join-Path $WorkDir 'sleep-events.json') ('{"read_utc":"2026-11-02T00:30:00Z","events":[]}')
            Update-SleepEvents
            [pscustomobject]@{Name='сама тривала пауза публікатора без сну чи boot не дає події';Ok=($script:SleepEvents.Count -eq 0)}
            $script:Clock = [datetime]'2026-11-02T05:02:00Z'
            $script:Boot = ([datetime]'2026-11-02T05:01:00Z').ToUniversalTime()
            Write-FileAtomic (Join-Path $WorkDir 'sleep-events.json') ('{"read_utc":"2026-11-02T05:00:00Z","events":[]}')
            Update-SleepEvents
            [pscustomobject]@{Name='коротке вимкнення дає рядок навіть за паузи менше 5 хвилин';Ok=($script:SleepEvents.Count -eq 1 -and $script:SleepEvents[0].to -ceq '2026-11-02T05:01:00.0000000Z')}
            $duringGap=Status '20261102-050030-000000000008' 'STALL'
            $duringGap.started_utc='2026-11-02T05:00:30Z';$duringGap.ended_utc='2026-11-02T05:01:30Z'
            [pscustomobject]@{Name='наряд між heartbeat і вимкненням також належить попередньому завантаженню';Ok=($null -ne (Get-RunSleep $duringGap))}
            $script:SleepEvents=@([pscustomobject]@{key='e'*64;from='2026-11-02T01:00:00Z';to='2026-11-02T02:00:00Z'})
            $script:Marker='e'*40;$script:PublishCode='OK'
            $noBundle = Status '20261102-003000-000000000006' 'AGY_ERROR' '' $false
            Save-Status $noBundle;$publishBefore=$script:PublishCalls;$result=Get-Line $noBundle.id
            $request=[IO.File]::ReadAllText((Join-Path $UpdateRoot ('sleep-retry-'+$noBundle.id+'.json')),$script:Utf8)|ConvertFrom-Json
            [pscustomobject]@{Name='AGY_ERROR без нових комітів повторюється від наявної опублікованої голови';Ok=($null -eq $result -and $request.head -ceq $script:PublishedHead -and $script:PublishCalls -eq $publishBefore)}
            $noBundleRetry=Status '20261102-023000-000000000007' 'AGY_ERROR' $noBundle.id $false
            Save-Status $noBundleRetry;$result=Get-Line $noBundleRetry.id
            [pscustomobject]@{Name='повтор без нових комітів завершується ЗАБЛОКОВАНО';Ok=($result.Outbox -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/сон AGY_ERROR')}
        }
        Export-ModuleMember -Function Run
    }
    foreach ($check in @(& $pub { Run })) { Check $check.Name $check.Ok }
    $worker = New-Module -ArgumentList $SourceDir,$tmp -ScriptBlock {
        param($src,$tmp)
        . (Join-Path $src 'gemini_run.ps1') -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/trusted"
        $script:StateDir=Join-Path $RunsDir 'state';$script:SlotDir=Join-Path $RunsDir 'slots'
        foreach($dir in @($RunsDir,$script:StateDir,$script:SlotDir,$LaneDir)) {[void][IO.Directory]::CreateDirectory($dir)}
        $script:Head='c'*40;$script:Marker='a'*40
        $script:M=[pscustomobject]@{Valid=$true;Name='gemini-queue/сон/gpt-test-high/1';Ref='refs/remotes/origin/gemini-queue/сон/gpt-test-high/1';Sha=$script:Marker;Slug='сон';Model='gpt-test-high';N='1';Cond='';Lane='codex';Time=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds();Seen=0;Gpu=$false;Prio=2;Deadline=''}
        $script:Limits=@{slots=@{codex=1;agy=0}}
        $script:Jobs=New-Object Collections.ArrayList
        function Get-Markers {$script:M}
        function Get-NightlyMarker { }
        function Test-SlugBusy {$false}
        function Get-RefSha { $script:Head }
        function Invoke-Git {[pscustomobject]@{Code=0;Out='';Err=''}}
        function Select-Engine { [pscustomobject]@{Engine=@{Name='codex';Model='gpt-test';Effort='high'};Model='gpt-test-high';Quota=@{Blocked=$false;Known=$false;Left=0;Group=''}} }
        function Get-FreeSlot { 'codex-1' }
        function Start-Worker($Job,[string]$Dir) {
            <# Межа запуску процесу: фіксуємо справжній job планувальника, моделі не запускаються. #>
            [void]$script:Jobs.Add($Job)
            Write-FileAtomic (Get-StatePath (Get-MarkerKey $script:M)) ('STARTED '+(@{id=$Job.id}|ConvertTo-Json -Compress))
            [pscustomobject]@{Slug=$Job.slug;Proc=@{HasExited=$false};Gpu=$false}
        }
        function Run {
            <# Запит не запускає модель до появи голови у fetched origin. #>
            $state=Get-StatePath (Get-MarkerKey $script:M);$parent='20261102-003000-000000000001'
            Write-FileAtomic $state "DONE $parent STALL"
            # Негативна проба перевірки: успішний DONE, жодної події чи дозволу публікатора.
            $permitPath=Join-Path $UpdateRoot ('sleep-retry-'+$parent+'.json')
            $permit=[IO.File]::ReadAllText($permitPath,$script:Utf8)
            Remove-Item -LiteralPath $permitPath
            Write-FileAtomic $state "DONE $parent DONE"
            $forged=@{parent=$parent;queue=$script:M.Name;marker=$script:M.Sha;head=$script:Head;sleep=('f'*64)}
            $forgedPath=Join-Path $OutDir ('sleep-retry-'+$parent+'.json')
            Write-FileAtomic $forgedPath ($forged|ConvertTo-Json -Compress)
            Import-SleepRetries
            $workers=New-Object Collections.ArrayList
            $started=Start-Markers $workers
            [pscustomobject]@{Name='підроблений OutDir без сну й дозволу: DONE лишається DONE, запусків 0';Ok=((Get-MarkerState $script:M).Kind -eq 'DONE' -and $started -eq 0 -and $script:Jobs.Count -eq 0 -and -not (Test-Path ($state+'.sleep.json')))}
            Write-FileAtomic $state "DONE $parent STALL"
            Import-SleepRetries
            [pscustomobject]@{Name='підроблений OutDir з кодом STALL теж не відкриває повтор';Ok=((Get-MarkerState $script:M).Kind -eq 'DONE' -and -not (Test-Path ($state+'.sleep.json')))}
            Write-FileAtomic $state "DONE $parent DONE"
            [pscustomobject]@{Name='справжня перевірка ACL відхиляє файл і корінь, доступні агенту для запису';Ok=(-not (Test-SleepRetryPath $forgedPath))}
            # Стенд однієї особи не може створити канал іншого власника: далі підмінено
            # тільки ACL-межу. Вибір теки, розбір, кінцеві коди й планувальник справжні.
            function script:Test-SleepRetryPath { $true }
            Write-FileAtomic $permitPath $permit
            Import-SleepRetries
            [pscustomobject]@{Name='навіть дозвіл каналу не відкриває успішний код DONE';Ok=((Get-MarkerState $script:M).Kind -eq 'DONE')}
            Write-FileAtomic $state "DONE $parent STALL"
            $script:Head='b'*40
            function script:Invoke-Git {[pscustomobject]@{Code=1;Out='';Err=''}}
            Import-SleepRetries
            [pscustomobject]@{Name='повтор чекає, доки fetch отримає опубліковану голову';Ok=([IO.File]::ReadAllText($state).StartsWith('DONE '))}
            $script:Head='c'*40
            function script:Invoke-Git {[pscustomobject]@{Code=0;Out='';Err=''}}
            Import-SleepRetries
            $wait=Get-MarkerState $script:M
            [pscustomobject]@{Name='без нової позначки диспетчера DONE → WAIT від опублікованої голови';Ok=($wait.Kind -eq 'WAIT' -and $wait.Wait.head -ceq $script:Head -and $wait.Wait.group -ceq 'SLEEP' -and (Test-MarkerReady $wait))}
            [pscustomobject]@{Name='дозвіл повтору записано до наступного STARTED';Ok=((Get-SleepParent $state) -ceq $parent)}
            $workers=New-Object Collections.ArrayList
            $started=Start-Markers $workers;Import-SleepRetries;$again=Start-Markers $workers
            [pscustomobject]@{Name='планувальник запускає рівно один повтор із головою опублікованої гілки';Ok=($started -eq 1 -and $again -eq 0 -and $script:Jobs.Count -eq 1 -and $script:Jobs[0].head -ceq $script:Head)}
            [pscustomobject]@{Name='зайнятий повтор не ставиться повторно';Ok=([IO.File]::ReadAllText($state).StartsWith('STARTED '))}
            Write-FileAtomic $state 'DONE 20261102-023000-000000000002 STALL';Import-SleepRetries
            [pscustomobject]@{Name='завершений повтор не воскресає після перезапуску планувальника';Ok=([IO.File]::ReadAllText($state) -ceq 'DONE 20261102-023000-000000000002 STALL')}
            # Спільний фінал, який викликають і Invoke-Task, і Resume-Interrupted.
            $s=[ordered]@{id='20261102-050000-000000000005';slug='сон';start='';ahead=0;code='AGY_ERROR';turns=1;started_utc='2026-11-02T00:30:00Z';sleep_parent=$parent}
            Complete-Status $s $state '' ([datetime]::MinValue)
            $saved=[IO.File]::ReadAllText((Join-Path $OutDir ($s.id+'.json')),$script:Utf8)|ConvertFrom-Json
            [pscustomobject]@{Name='спільний фінал зберігає UTC обох меж і походження повтору';Ok=($saved.started_utc -ceq $s.started_utc -and [bool]$saved.ended_utc -and $saved.sleep_parent -ceq $parent)}
            [pscustomobject]@{Name='квота не скидає дозвіл сну';Ok=((Get-SleepParent $state) -ceq $parent)}
        }
        Export-ModuleMember -Function Run
    }
    foreach ($check in @(& $worker {Run})) {Check $check.Name $check.Ok}
    $limits = New-Module -ArgumentList $SourceDir,$tmp -ScriptBlock {
        param($src,$tmp)
        . (Join-Path $src 'gemini_run.ps1') -RunsDir "$tmp/runs-l" -OutDir "$tmp/out-l" -LaneDir "$tmp/lanes-l" -UpdateRoot "$tmp/trusted-l"
        $script:TotalMinutes = 10; $script:TurnMinutes = 5; $script:MaxNudges = 2
        $script:Head = 'c'*40
        # Годинник на стіні й годинник неспання підмінено: сон — це стрибок першого без руху другого.
        $script:Wall = [datetime]'2026-11-08T09:21:00'; $script:Awake = [timespan]::FromHours(100)
        function Get-Date { $script:Wall }
        function Get-AwakeTime { $script:Awake }
        function Write-Log([string]$Text) { }
        function Close-StreamRun($Run) { }
        function Get-Facts { [pscustomobject]@{Head=$script:Head;OnBranch=$true;Dirty=0;Ahead=1} }
        function Get-HeadLivePublication { [pscustomobject]@{Bad=@()} }
        function Get-Nudge { 'догонка' }
        function Invoke-Turn($M, $Run, [string]$Text, $Deadline) {
            $script:Turns++
            if ($script:Turns -eq 1) {
                # agy губить з'єднання за сон; розмова лишається, тож можлива догонка.
                $Run.Conversation = 'розмова-1'
                $script:Wall = $script:Wall + $script:WallStep; $script:Awake = $script:Awake + $script:AwakeStep
                return [pscustomobject]@{Kind='eof';Result=$null}
            }
            [pscustomobject]@{Kind='result';Result=[pscustomobject]@{status='OK';response="НОУТБУК ГОТОВО gemini/сон $script:Head"}}
        }
        function Run {
            <# Межа agy (`agy_total_minutes`): 7 год сну — не TIMEOUT, 11 хв неспання — TIMEOUT. #>
            $m = [pscustomobject]@{Slug='сон'}
            $sel = [pscustomobject]@{Engine=[pscustomobject]@{Name='agy';Effort='high'};Exe='не запускати'}
            $script:Turns = 0; $script:WallStep = [timespan]::FromMinutes(433); $script:AwakeStep = [timespan]::FromMinutes(1)
            $res = Invoke-Agent $m $script:Head 'наряд' $tmp $sel
            [pscustomobject]@{Name='сон 7 год посеред ходу agy: догонка й DONE, не TIMEOUT';Ok=($res.Code -ceq 'DONE' -and $res.Turns -eq 2)}
            $script:Turns = 0; $script:WallStep = [timespan]::FromMinutes(11); $script:AwakeStep = [timespan]::FromMinutes(11)
            $res = Invoke-Agent $m $script:Head 'наряд' $tmp $sel
            [pscustomobject]@{Name='11 хв неспання за межі 10 хв: TIMEOUT, як і було';Ok=($res.Code -ceq 'TIMEOUT' -and $res.Turns -eq 1)}
        }
        Export-ModuleMember -Function Run
    }
    foreach ($check in @(& $limits {Run})) {Check $check.Name $check.Ok}
    $pause = New-Module -ArgumentList $SourceDir,$tmp -ScriptBlock {
        param($src,$tmp)
        . (Join-Path $src 'gemini_run.ps1') -RunsDir "$tmp/runs-p" -OutDir "$tmp/out-p" -LaneDir "$tmp/lanes-p" -UpdateRoot "$tmp/trusted-p"
        # Батарея на вході й на двох обертах циклу, далі мережа; кожен Start-Sleep — 2 год неспання.
        $script:Battery = @($true, $true, $true, $false); $script:Clock = [timespan]::FromHours(100)
        $script:Calls = New-Object Collections.ArrayList
        function Test-OnBattery { $b = $script:Battery[0]; if ($script:Battery.Count -gt 1) { $script:Battery = $script:Battery[1..($script:Battery.Count - 1)] }; $b }
        function Get-UnbiasedTime { $script:Clock }
        function Start-Sleep { $script:Clock += [timespan]::FromHours(2) }
        function Get-PauseTargets { @(11, 12) }
        function Set-ProcessPause([int]$Id, [bool]$On) { [void]$script:Calls.Add("$Id $On"); $true }
        function Write-Log([string]$Text) { }
        # Серцебиття всередині паузи доходить до Invoke-Native — друга пауза не має нічого робити.
        function Invoke-HealthBeat { Wait-PowerPause }
        function Run {
            <# Без світла процеси нарядів стоять, після — відновлені; 4 год паузи не йдуть ні в межі, ні в завислість. #>
            $before = Get-AwakeTime
            Wait-PowerPause
            [pscustomobject]@{Name='пауза: кожен процес призупинено й відновлено рівно раз, у такому порядку';Ok=(($script:Calls -join ',') -ceq '11 True,12 True,11 False,12 False')}
            [pscustomobject]@{Name='4 год паузи не додали робочого часу (Get-AwakeTime)';Ok=((Get-AwakeTime) -eq $before -and $script:PausedTotal -eq [timespan]::FromHours(4))}
            $script:Calls.Clear(); $script:Battery = @($false)
            Wait-PowerPause
            [pscustomobject]@{Name='від мережі пауза нічого не чіпає';Ok=($script:Calls.Count -eq 0)}
        }
        Export-ModuleMember -Function Run
    }
    foreach ($check in @(& $pause {Run})) {Check $check.Name $check.Ok}
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
# Артефакти лишаються в TEMP стенда; він не торкається робочих обгорток і станів ноутбука.
"провалів: $bad"
exit ([int]($bad -gt 0))
