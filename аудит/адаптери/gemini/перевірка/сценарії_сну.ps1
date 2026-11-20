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
        $script:PowerEvents = @()
        function Get-WinEvent {
            <# XML подій підміняється, його розбирає справжній Get-WakeRows; Kernel-Power віддає найновіші першими й, як журнал, кидає виняток без подій. #>
            param([hashtable]$FilterHashtable, [int]$MaxEvents = 0, $ErrorAction)
            $f = $FilterHashtable
            $out = @()
            if ($f.ProviderName -ceq 'Microsoft-Windows-Kernel-Power') {
                $out = @($script:PowerEvents | Where-Object { $f.Id -contains $_.id -and (-not $f.ContainsKey('StartTime') -or $_.t -ge $f.StartTime.ToUniversalTime()) -and (-not $f.ContainsKey('EndTime') -or $_.t -le $f.EndTime.ToUniversalTime()) } | Sort-Object t, rec -Descending)
                if ($MaxEvents -gt 0) { $out = @($out | Select-Object -First $MaxEvents) }
                $out = @($out | ForEach-Object {
                    $items = ($_.data.GetEnumerator() | ForEach-Object { "<Data Name='$($_.Key)'>$($_.Value)</Data>" }) -join ''
                    $value = [pscustomobject]@{ Id=$_.id; TimeCreated=$_.t; RecordId=$_.rec; XmlText="<Event><EventData>$items</EventData></Event>" }
                    Add-Member -InputObject $value -MemberType ScriptMethod -Name ToXml -Value {$this.XmlText}
                    $value })
            } else {
                $out = @($script:WakeRows | ForEach-Object {
                    $value = [pscustomobject]@{ XmlText="<Event><EventData><Data Name='SleepTime'>$($_.from)</Data><Data Name='WakeTime'>$($_.to)</Data></EventData></Event>" }
                    Add-Member -InputObject $value -MemberType ScriptMethod -Name ToXml -Value {$this.XmlText}
                    $value })
            }
            if ($out.Count -eq 0) { throw 'No events were found that match the specified selection criteria.' }
            $out
        }
        function Add-PowerEvent([int]$Id, [string]$At, [hashtable]$Data) {
            <# Подія Kernel-Power стенда: час UTC, поля EventData; номер запису зростає за порядком додавання. #>
            $script:PowerEvents += [pscustomobject]@{ id=$Id; t=([datetime]::Parse($At, [cultureinfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal)); rec=@($script:PowerEvents).Count; data=$Data }
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
            $bootLines = @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' | ForEach-Object { [IO.File]::ReadAllText($_.FullName,$script:Utf8).Trim() } | Where-Object { $_ -cmatch 'ВИМКНЕНО-СТАРТ' })
            [pscustomobject]@{Name='нове завантаження — рядок ВИМКНЕНО-СТАРТ, а не СОН';Ok=($bootLines.Count -eq 1 -and $bootLines[0] -cmatch '\AGEMINI ОБГОРТКА: ВИМКНЕНО-СТАРТ 2026-11-02T05:00:00Z → 2026-11-02T05:01:00Z, нарядів [0-9]+\z' -and -not (Test-OutboxLine $bootLines[0]))}
            [pscustomobject]@{Name='сон за Power-Troubleshooter лишається рядком СОН, лише одним';Ok=(@(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' | ForEach-Object { [IO.File]::ReadAllText($_.FullName,$script:Utf8) } | Where-Object { $_ -cmatch 'ОБГОРТКА: СОН ' }).Count -eq 2)}
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
            $off = 'GEMINI ОБГОРТКА: СВІТЛА НЕМА 2026-11-16T15:44:52Z'
            $on = 'GEMINI ОБГОРТКА: СВІТЛО Є 2026-11-17T07:26:10Z ПАУЗА З 2026-11-16T15:44:52Z'
            [pscustomobject]@{Name='рядки про світло — за шаблоном вихідних (не в карантин)';Ok=((Test-OutboxLine $off) -ceq '' -and (Test-OutboxLine $on) -ceq '')}
            [pscustomobject]@{Name='рядок про світло зі зайвим текстом чи без часу зникнення — карантин NO_TEMPLATE';Ok=((Test-OutboxLine ($off + ' ще')) -ceq 'NO_TEMPLATE' -and (Test-OutboxLine 'GEMINI ОБГОРТКА: СВІТЛО Є 2026-11-17T07:26:10Z') -ceq 'NO_TEMPLATE')}
            [pscustomobject]@{Name='обидва рядки про світло будять диспетчера (не зведення)';Ok=((Test-DispatcherAction $off) -and (Test-DispatcherAction $on))}
            # Modern Standby (запис ноутбука 16–17.11): Power-Troubleshooter 1 не пишеться, межі сну — Kernel-Power 506/507, світло — 105.
            $in = { param([string]$id) @{ ScenarioInstanceId=$id; ScenarioInstanceIdV2=$id; BootId='146' } }
            $out = { param([string]$id, [string]$asleep, [string]$goesOn, [string]$entry) @{ ScenarioInstanceId=$id; ScenarioInstanceIdV2=$entry; SleepEntered=$asleep; IsCsSessionInProgressOnExit=$goesOn; BootId='146' } }
            Add-PowerEvent 105 '2026-11-16T15:43:27.283Z' @{AcOnline='false'}
            Add-PowerEvent 506 '2026-11-16T15:51:01.142Z' (& $in '17')
            Add-PowerEvent 507 '2026-11-16T15:51:02.960Z' (& $out '19' 'false' 'false' '17')
            Add-PowerEvent 506 '2026-11-16T15:51:05.678Z' (& $in '20')
            Add-PowerEvent 507 '2026-11-16T15:51:31.950Z' (& $out '22' 'true' 'true' '20')
            Add-PowerEvent 506 '2026-11-16T15:51:31.953Z' (& $in '22')
            Add-PowerEvent 105 '2026-11-17T07:23:00.726Z' @{AcOnline='true'}
            Add-PowerEvent 507 '2026-11-17T07:23:01.788Z' (& $out '24' 'true' 'false' '22')
            Add-PowerEvent 105 '2026-11-17T11:31:58.781Z' @{AcOnline='false'}
            Add-PowerEvent 506 '2026-11-17T11:32:01.641Z' (& $in '25')
            Add-PowerEvent 507 '2026-11-17T13:32:01.930Z' (& $out '27' 'true' 'true' '25')
            Add-PowerEvent 506 '2026-11-17T13:32:01.932Z' (& $in '27')
            Add-PowerEvent 105 '2026-11-17T15:52:31.688Z' @{AcOnline='true'}
            Add-PowerEvent 507 '2026-11-17T15:52:32.909Z' (& $out '29' 'true' 'false' '27')
            Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' | Remove-Item
            $script:WakeRows = @(); $script:Boot = $null
            Write-FileAtomic (Join-Path $WorkDir 'sleep-events.json') '{"read_utc":"2026-11-16T15:00:00Z","events":[]}'
            $script:Clock = [datetime]'2026-11-17T16:00:00Z'
            Update-SleepEvents; Update-SleepEvents
            $sent = { @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' | Sort-Object Name | ForEach-Object { [IO.File]::ReadAllText($_.FullName,$script:Utf8).Trim() }) }
            $standby = @(& $sent)
            $night = 'GEMINI ОБГОРТКА: СОН 2026-11-16T15:51:05Z → 2026-11-17T07:23:01Z, нарядів 0 СВІТЛА НЕ БУЛО З 2026-11-16T15:43:27Z ДОСТУПНИЙ З 2026-11-17T07:23:01Z'
            $day = 'GEMINI ОБГОРТКА: СОН 2026-11-17T11:32:01Z → 2026-11-17T15:52:32Z, нарядів 0 СВІТЛА НЕ БУЛО З 2026-11-17T11:31:58Z ДОСТУПНИЙ З 2026-11-17T15:52:32Z'
            [pscustomobject]@{Name='Modern Standby 16–17.11: один рядок на сон, межі й світло з Kernel-Power (506→507→506 — один сон; 507 без сну — не сон)';Ok=($standby.Count -eq 2 -and $standby[0] -ceq $night -and $standby[1] -ceq $day)}
            [pscustomobject]@{Name='рядки Modern Standby проходять доставку й будять диспетчера';Ok=((Test-OutboxLine $night) -ceq '' -and (Test-OutboxLine $day) -ceq '' -and (Test-DispatcherAction $night) -and (Test-DispatcherAction $day))}
            [pscustomobject]@{Name='хвіст про світло лише в СОН: ВИМКНЕНО-СТАРТ чи зайвий текст — карантин';Ok=((Test-OutboxLine ($night -replace 'СОН','ВИМКНЕНО-СТАРТ')) -ceq 'NO_TEMPLATE' -and (Test-OutboxLine ($day + ' ще')) -ceq 'NO_TEMPLATE')}
            # Сон на мережі — рядок без світла, зведенням; сон, що закінчився на батареї, — без «доступний з»; сон, що ще триває, дочитується з початку.
            Add-PowerEvent 506 '2026-11-18T01:00:00.100Z' (& $in '30')
            Add-PowerEvent 507 '2026-11-18T01:30:00.200Z' (& $out '31' 'true' 'false' '30')
            $script:Clock = [datetime]'2026-11-18T02:00:00Z'; Update-SleepEvents
            $plain = [string](@(& $sent) | Select-Object -Last 1)
            [pscustomobject]@{Name='сон на мережі — СОН без світла, лише зведенням';Ok=($plain -ceq 'GEMINI ОБГОРТКА: СОН 2026-11-18T01:00:00Z → 2026-11-18T01:30:00Z, нарядів 0' -and -not (Test-DispatcherAction $plain))}
            Add-PowerEvent 105 '2026-11-18T03:00:00.000Z' @{AcOnline='false'}
            Add-PowerEvent 506 '2026-11-18T03:01:00.100Z' (& $in '32')
            Add-PowerEvent 507 '2026-11-18T03:30:00.200Z' (& $out '33' 'true' 'false' '32')
            $script:Clock = [datetime]'2026-11-18T04:00:00Z'; Update-SleepEvents
            $battery = [string](@(& $sent) | Select-Object -Last 1)
            [pscustomobject]@{Name='сон на батареї без повернення світла: час зникнення без «доступний з»';Ok=($battery -ceq 'GEMINI ОБГОРТКА: СОН 2026-11-18T03:01:00Z → 2026-11-18T03:30:00Z, нарядів 0 СВІТЛА НЕ БУЛО З 2026-11-18T03:00:00Z' -and (Test-DispatcherAction $battery))}
            Add-PowerEvent 105 '2026-11-18T04:30:00.000Z' @{AcOnline='true'}
            Add-PowerEvent 506 '2026-11-18T05:00:00.100Z' (& $in '34')
            $count = @(& $sent).Count
            $script:Clock = [datetime]'2026-11-18T05:10:00Z'; Update-SleepEvents
            $resume = Get-SleepTime ([string]((Get-Content -LiteralPath (Join-Path $WorkDir 'sleep-events.json') -Raw -Encoding UTF8 | ConvertFrom-Json).read_utc))
            [pscustomobject]@{Name='вхід без виходу — рядка нема, читання дочитає сон з його початку';Ok=(@(& $sent).Count -eq $count -and $resume -lt ([datetime]'2026-11-18T05:00:00.100Z').ToUniversalTime() -and $resume -gt ([datetime]'2026-11-18T04:00:00Z').ToUniversalTime())}
            Add-PowerEvent 507 '2026-11-18T05:20:00.300Z' (& $out '35' 'true' 'false' '34')
            $script:Clock = [datetime]'2026-11-18T06:00:00Z'; Update-SleepEvents; Update-SleepEvents
            [pscustomobject]@{Name='сон, що тривав між читаннями, — один рядок із початком із журналу';Ok=(@(& $sent).Count -eq $count + 1 -and [string](@(& $sent) | Select-Object -Last 1) -ceq 'GEMINI ОБГОРТКА: СОН 2026-11-18T05:00:00Z → 2026-11-18T05:20:00Z, нарядів 0')}
            # Той самий сон у Power-Troubleshooter 1 і Kernel-Power — один рядок, за Power-Troubleshooter.
            $script:WakeRows = @([pscustomobject]@{ from='2026-11-18T07:00:00.0000000Z';to='2026-11-18T07:30:00.0000000Z' })
            Add-PowerEvent 506 '2026-11-18T07:00:00.500Z' (& $in '36')
            Add-PowerEvent 507 '2026-11-18T07:30:00.600Z' (& $out '37' 'true' 'false' '36')
            $script:Clock = [datetime]'2026-11-18T08:00:00Z'; Update-SleepEvents
            $both = @(& $sent | Where-Object { $_ -cmatch '2026-11-18T07:00:00Z' })
            [pscustomobject]@{Name='сон у двох журналах — один рядок';Ok=($both.Count -eq 1 -and $both[0] -ceq 'GEMINI ОБГОРТКА: СОН 2026-11-18T07:00:00Z → 2026-11-18T07:30:00Z, нарядів 0' -and @($script:SleepEvents | Select-Object -Last 1 | ForEach-Object { $_.source }) -ceq 'Power-Troubleshooter/1')}
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
            # Стенд однієї особи не може створити канал іншого owner: далі підмінено
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
    $targets = New-Module -ArgumentList $SourceDir,$tmp -ScriptBlock {
        param($src,$tmp)
        . (Join-Path $src 'gemini_run.ps1') -RunsDir "$tmp/runs-t" -OutDir "$tmp/out-t" -LaneDir "$tmp/lanes-t" -UpdateRoot "$tmp/trusted-t"
        function Get-Process {
            <# Перелік процесів машини: інтерфейс, lms, окремий llmster, процес із теки .lmstudio, ComfyUI і сторонні. #>
            foreach ($row in @(@('LM Studio',21,''),@('lms',22,''),@('llmster',23,''),@('node',24,'C:\Users\u\.lmstudio\bin\server.exe'),@('ComfyUI',25,''),@('chrome',26,'C:\Chrome\chrome.exe'),@('notepad',27,''))) {
                [pscustomobject]@{ ProcessName = $row[0]; Id = $row[1]; Path = $row[2] }
            }
        }
        function Get-CimInstance { }
        function Run {
            <# Планувальник ставить на паузу всі процеси LM Studio за визначенням Test-GpuModelProcess, сторонніх не чіпає. #>
            $script:PauseMachine = $true
            $ids = @(Get-PauseTargets)
            [pscustomobject]@{Name='пауза машини: LM Studio, lms, окремий llmster і процес із .lmstudio, ComfyUI — але не chrome і notepad';Ok=(($ids -join ',') -ceq '21,22,23,24,25')}
            $script:PauseMachine = $false
            [pscustomobject]@{Name='без планувальника процесів машини в цілях паузи нема';Ok=(@(Get-PauseTargets).Count -eq 0)}
        }
        Export-ModuleMember -Function Run
    }
    foreach ($check in @(& $targets {Run})) {Check $check.Name $check.Ok}
    $free = New-Module -ArgumentList $SourceDir,$tmp -ScriptBlock {
        param($src,$tmp)
        . (Join-Path $src 'gemini_run.ps1') -RunsDir "$tmp/runs-f" -OutDir "$tmp/out-f" -LaneDir "$tmp/lanes-f" -UpdateRoot "$tmp/trusted-f"
        [void][IO.Directory]::CreateDirectory($LaneDir)
        $script:Calls = New-Object Collections.ArrayList
        function Test-OnBattery { $b = $script:Battery[0]; $script:Battery = @($script:Battery | Select-Object -Skip 1); $b }
        function Start-Sleep { }
        function Invoke-HealthBeat { }
        function Write-Log([string]$Text) { }
        function Get-PauseTargets { @(11) }
        function Set-ProcessPause([int]$Id, [bool]$On) { [void]$script:Calls.Add("пауза $Id $On"); $true }
        function Get-LmsInstances { [pscustomobject]@{ id = 'owner'; model = 'm1' }; [pscustomobject]@{ id = 'job'; model = 'm2' } }
        function Invoke-RestMethod {
            <# Підробні LM Studio і ComfyUI: :8188 вимкнено, решта відповідає. #>
            [CmdletBinding()] param([Parameter(Position=0)][string]$Uri, $Method, $ContentType, $Body, $TimeoutSec)
            [void]$script:Calls.Add("$Uri $Body")
            if ($Uri -like '*:8188/*') { throw 'зʼєднання відхилено' }
            [pscustomobject]@{ status = 'unloaded' }
        }
        function Invoke-Outage([string]$Session) {
            <# Одна пауза зі світлом, що повертається; $Session — вміст gpu-models.json ('' — запису нема). #>
            $p = Join-Path $LaneDir 'gpu-models.json'
            if ($Session) { [IO.File]::WriteAllText($p, $Session) } else { Remove-Item -LiteralPath $p -Force -ErrorAction SilentlyContinue }
            $script:Calls.Clear(); $script:Battery = @($true, $true, $false)
            Wait-PowerPause
            $script:Calls -join ' | '
        }
        function Run {
            <# Звільнення карти: до заморожування; модель живої оренди лишається; збій сервера паузи не зриває. #>
            $script:PauseMachine = $true
            $session = '{"v":2,"before":[{"id":"owner","model":"m1"}],"leases":[{"run":"r1","marker":"наряд-1","join":["owner"],"done":false}],"dirty":false}'
            $unloadOwner = 'http://127.0.0.1:1234/api/v1/models/unload {"instance_id":"owner"}'
            $unloadJob = 'http://127.0.0.1:1234/api/v1/models/unload {"instance_id":"job"}'
            $comfy = 'http://127.0.0.1:8000/free {"unload_models":true,"free_memory":true} | http://127.0.0.1:8188/free {"unload_models":true,"free_memory":true}'
            $lease = Open-Lock (Get-GpuLeaseLockPath 'r1')
            $got = Invoke-Outage $session
            [pscustomobject]@{Name='живий GPU-наряд: вивантажено лише чуже, його модель лишилась; ComfyUI звільнено; усе до заморожування';Ok=($got -ceq "$unloadOwner | $comfy | пауза 11 True | пауза 11 False")}
            $lease.Dispose()
            $got = Invoke-Outage ''
            [pscustomobject]@{Name='без GPU-нарядів: вивантажено всі екземпляри LM Studio';Ok=($got -ceq "$unloadOwner | $unloadJob | $comfy | пауза 11 True | пауза 11 False")}
            $got = Invoke-Outage '{"v":2}'
            [pscustomobject]@{Name='неповний запис GPU: LM Studio не чіпається, ComfyUI звільнено, пауза йде';Ok=($got -ceq "$comfy | пауза 11 True | пауза 11 False")}
            $gate = Open-Lock (Get-GpuLockPath)
            $got = Invoke-Outage ''
            $gate.Dispose()
            [pscustomobject]@{Name='ворота GPU зайняті: LM Studio не чіпається, пауза йде';Ok=($got -ceq "$comfy | пауза 11 True | пауза 11 False")}
            $script:PauseMachine = $false
            $got = Invoke-Outage ''
            [pscustomobject]@{Name='без планувальника claude-run карту не звільняє';Ok=($got -ceq 'пауза 11 True | пауза 11 False')}
        }
        Export-ModuleMember -Function Run
    }
    foreach ($check in @(& $free {Run})) {Check $check.Name $check.Ok}
    $light = New-Module -ArgumentList $SourceDir,$tmp -ScriptBlock {
        param($src,$tmp)
        . (Join-Path $src 'claude_run.ps1') -WorkDir "$tmp/cl-w" -RepoDir "$tmp/cl-r" -OutboxDir "$tmp/cl-box" -PublishDir "$tmp/cl-pub" -LaneDir "$tmp/cl-lanes" -OffWaitMinutes 0.05 -NoStatus
        foreach ($d in @($WorkDir,$OutboxDir,"$PublishDir/state")) { [void][IO.Directory]::CreateDirectory($d) }
        $script:Events = New-Object Collections.ArrayList
        $script:Log = New-Object Collections.ArrayList
        $script:Deliver = ''; $script:Battery = @($false); $script:Refuse = $false; $script:Ver = @('')
        $script:WaitDisplay = $null
        function Write-Log([string]$Text) { [void]$script:Log.Add($Text) }
        function Invoke-HealthBeat { }
        function Clear-GpuForPause { }
        function Get-PauseTargets { @(11, 12) }
        function Set-ProcessPause([int]$Id, [bool]$On) { $true }
        function Set-KeepAwake([bool]$On, [bool]$Display = $false) { [void]$script:Events.Add("тримання $On" + $(if ($On -and $Display) { ' з дисплеєм' } else { '' })); -not ($On -and $script:Refuse) }
        function Test-OnBattery { $b = $script:Battery[0]; if ($script:Battery.Count -gt 1) { $script:Battery = $script:Battery[1..($script:Battery.Count - 1)] }; $b }
        function Get-VersionSwitch { $v = $script:Ver[0]; if ($script:Ver.Count -gt 1) { $script:Ver = $script:Ver[1..($script:Ver.Count - 1)] }; $v }
        function Get-Outbox { @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' -File | Sort-Object Name | ForEach-Object { [IO.File]::ReadAllText($_.FullName).Trim() }) }
        function Start-Sleep {
            <# Такт тримача (-Seconds 1), чекання доставки (-Seconds 10: публікатор закриває стан o-<id>.json з
            $script:Deliver) і чекання світла паузою (-Milliseconds). #>
            param([int]$Seconds, [int]$Milliseconds)
            if ($Milliseconds) { [void]$script:Events.Add('світло-чекання'); return }
            if ($Seconds -eq 1) { [void]$script:Events.Add('такт'); return }
            [void]$script:Events.Add('доставка-чекання ' + (@(Get-Outbox).Count))
            $script:WaitDisplay = $script:LightDisplay
            Microsoft.PowerShell.Utility\Start-Sleep -Milliseconds 50
            if ($script:Deliver) {
                foreach ($f in @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' -File)) {
                    [IO.File]::WriteAllText((Join-Path "$PublishDir/state" ('o-' + $f.BaseName + '.json')), $script:Deliver)
                }
            }
        }
        function Tick([bool]$Battery, [string]$Delivered = '') {
            <# Один такт тримача з чистими подіями й журналом; повертає події через « | ». #>
            $script:Events.Clear(); $script:Log.Clear(); $script:Deliver = $Delivered; $script:Battery = @($Battery)
            Step-Light
            $script:Events -join ' | '
        }
        function Clear-Box {
            <# Порожні тека вихідних і стани публікатора. #>
            Get-ChildItem -LiteralPath $OutboxDir -File -ErrorAction SilentlyContinue | Remove-Item -Force
            Get-ChildItem -LiteralPath "$PublishDir/state" -File -ErrorAction SilentlyContinue | Remove-Item -Force
        }
        function Run {
            <# Тримач світла: запит на мережі заздалегідь; світла нема — рядок, доставка, лише тоді запит відпущено;
            світло є — рядок і запит знову. Пише лише тримач: пауза рушія рядків не пише й ноутбука не тримає. #>
            $ok = '{"line":"x","sent":true,"attempts":1}'
            $script:LightHeld = $false; $script:LightDisplay = $false; $script:LightRefused = $false
            $ev = Tick $false
            [pscustomobject]@{Name="на мережі запит тримається заздалегідь, рядків нема: $ev";Ok=($ev -ceq 'тримання True' -and $script:LightHeld -and @(Get-Outbox).Count -eq 0)}
            [pscustomobject]@{Name="на мережі лише «система потрібна» — без дисплея, дисплей гасне за схемою Windows: $ev";Ok=($ev -cnotmatch 'дисплеєм' -and -not $script:LightDisplay -and $script:Log[-1] -cmatch 'мережа, GPU вільна — запит «система потрібна» \(дисплей — за схемою Windows\) тримається$')}
            $ev = Tick $false
            [pscustomobject]@{Name="другий такт на мережі запиту не чіпає: '$ev'";Ok=($ev -ceq '' -and $script:LightHeld)}
            $script:WaitDisplay = $null
            $ev = Tick $true $ok
            [pscustomobject]@{Name="перехід мережа → батарея: запит міняє прапорці — система лишається, дисплей додано до кінця чекання доставки: $ev; дисплей під час чекання: $($script:WaitDisplay)";Ok=($ev -ceq 'тримання True з дисплеєм | доставка-чекання 1 | тримання False' -and $script:WaitDisplay -eq $true -and -not $script:LightHeld -and -not $script:LightDisplay)}
            $lines = @(Get-Outbox); $st = Read-LightState; $off = $(if ($st) { $st.Off } else { '' })
            [pscustomobject]@{Name="світла нема: один рядок за шаблоном, без числа процесів: $($lines -join '')";Ok=($lines.Count -eq 1 -and $off -and $lines[0] -cmatch $script:PowerOffLineTemplate -and $lines[0].EndsWith(" НЕМА $off") -and $st.Id -ceq '')}
            [pscustomobject]@{Name="світла нема → рядок → доставка → запит відпущено: $ev; $($script:Log[-1])";Ok=($ev -ceq 'тримання True з дисплеєм | доставка-чекання 1 | тримання False' -and -not $script:LightHeld -and $script:Log[-1] -cmatch 'запит відпущено — доставлено$')}
            $ev = Tick $true $ok
            [pscustomobject]@{Name="на батареї після сказаного — ні рядка, ні запиту: '$ev'";Ok=($ev -ceq '' -and @(Get-Outbox).Count -eq 1)}
            $ev = Tick $false
            $lines = @(Get-Outbox); $on = @($lines | Where-Object { $_ -cmatch $script:PowerOnLineTemplate })
            [pscustomobject]@{Name="світло є: рядок із часом зникнення, запит знову тримається: $ev; $($on -join '')";Ok=($lines.Count -eq 2 -and $on.Count -eq 1 -and $on[0].EndsWith(" ПАУЗА З $off") -and $ev -ceq 'тримання True' -and $script:LightHeld -and -not $script:LightDisplay -and -not (Read-LightState))}
            Clear-Box
            $ev = Tick $true ''
            [pscustomobject]@{Name="доставки нема до -OffWaitMinutes — запит відпущено, причина в журналі: $($script:Log[-1])";Ok=($ev -cmatch '^тримання True з дисплеєм \| доставка-чекання 1( \| доставка-чекання 1)* \| тримання False$' -and -not $script:LightHeld -and $script:Log[-1] -cmatch 'запит відпущено — не доставлено до межі чекання' -and @(Get-Outbox).Count -eq 1)}
            [void](Tick $false); Clear-Box
            $ev = Tick $true '{"line":"x","sent":false,"attempts":3}'
            [pscustomobject]@{Name="перший прохід публікатора без доставки — запит відпущено, довше не чекає: $ev";Ok=($ev -ceq 'тримання True з дисплеєм | доставка-чекання 1 | тримання False' -and $script:Log[-1] -cmatch 'перший прохід публікатора')}
            [void](Tick $false); Clear-Box; Set-LightHold $false
            $ev = Tick $true $ok
            [pscustomobject]@{Name="тримач стартував уже на батареї — запит лише на час доставки: $ev";Ok=($ev -ceq 'тримання True з дисплеєм | доставка-чекання 1 | тримання False' -and @(Get-Outbox).Count -eq 1)}
            $ev = Tick $true $ok
            [pscustomobject]@{Name="перезапуск на батареї після сказаного — тиша (light.txt): '$ev'";Ok=($ev -ceq '' -and @(Get-Outbox).Count -eq 1)}
            # Тримач перезапущено посеред чекання: light.txt має id рядка — новий процес бере запит і чекає саме його, без дубля.
            [void](Tick $false); Clear-Box; Set-LightHold $false
            $off = '2026-11-17T11:31:58Z'
            $id = Add-Line "GEMINI ОБГОРТКА: СВІТЛА НЕМА $off"
            Write-FileAtomic (Join-Path $WorkDir 'light.txt') "$off $id"
            $ev = Tick $true $ok
            $st = Read-LightState
            [pscustomobject]@{Name="перезапуск посеред чекання доставки — запит знову, той самий рядок, без дубля: $ev; $($script:Log -join ' / ')";Ok=($ev -ceq 'тримання True з дисплеєм | доставка-чекання 1 | тримання False' -and @(Get-Outbox).Count -eq 1 -and $st.Off -ceq $off -and $st.Id -ceq '' -and $script:Log[-1] -cmatch 'запит відпущено — доставлено$')}
            [void](Tick $false); Clear-Box; Set-LightHold $false
            # Запит із дисплеєм (батарея), а світло вже є: наступний такт мережі знімає дисплей, систему не відпускає.
            Set-LightHold $true $true
            $ev = Tick $false
            [pscustomobject]@{Name="повернення світла з запитом із дисплеєм — знову лише система, без паузи запиту: $ev";Ok=($ev -ceq 'тримання True' -and $script:LightHeld -and -not $script:LightDisplay)}
            Set-LightHold $false
            # Екран за замком GPU: живу оренду GPU-наряду читає тримач тим самим кодом, що смуги (запис сесії й замок оренди).
            $sessPath = Join-Path $LaneDir 'gpu-models.json'
            $sess = '{"v":2,"before":[{"id":"owner","model":"m1"}],"leases":[{"run":"r1","marker":"наряд-1","join":["owner"],"done":false}],"dirty":false}'
            [void][IO.Directory]::CreateDirectory($LaneDir)
            [IO.File]::WriteAllText($sessPath, $sess)
            $leaseLock = Open-Lock (Get-GpuLeaseLockPath 'r1')
            $ev = Tick $false; $n1 = $script:Log.Count
            [pscustomobject]@{Name="мережа, оренда GPU жива — запит із дисплеєм, один рядок: $ev; $($script:Log -join ' / ')";Ok=($ev -ceq 'тримання True з дисплеєм' -and $script:LightHeld -and $script:LightDisplay -and $n1 -eq 1 -and $script:Log[-1] -cmatch 'мережа, GPU зайнята \(наряд-1\) — запит «система й дисплей потрібні» тримається$')}
            $ev = Tick $false
            [pscustomobject]@{Name="друга секунда зайнятої GPU — запиту й рядка нема: '$ev'; рядків $($script:Log.Count)";Ok=($ev -ceq '' -and $script:LightDisplay -and $script:Log.Count -eq 0)}
            $leaseLock.Dispose()
            $ev = Tick $false
            [pscustomobject]@{Name="мережа, оренда мертва (замок відпущено) — знову лише система, один рядок: $ev; $($script:Log -join ' / ')";Ok=($ev -ceq 'тримання True' -and $script:LightHeld -and -not $script:LightDisplay -and $script:Log.Count -eq 1 -and $script:Log[-1] -cmatch 'мережа, GPU вільна — запит «система потрібна»')}
            $ev = Tick $false
            [pscustomobject]@{Name="друга секунда вільної GPU — запиту й рядка нема: '$ev'";Ok=($ev -ceq '' -and -not $script:LightDisplay -and $script:Log.Count -eq 0)}
            $leaseLock = Open-Lock (Get-GpuLeaseLockPath 'r1')
            $ev = Tick $false
            [pscustomobject]@{Name="вільна → зайнята знову — дисплей додано, один рядок: $ev";Ok=($ev -ceq 'тримання True з дисплеєм' -and $script:LightDisplay -and $script:Log.Count -eq 1)}
            $script:Battery = @($true); $script:Events.Clear(); $script:Log.Clear(); $script:Deliver = $ok
            Step-Light
            $ev = $script:Events -join ' | '
            [pscustomobject]@{Name="перехід на батарею за зайнятої GPU — дисплей уже є, запит не міняється до кінця доставки: $ev";Ok=($ev -ceq 'доставка-чекання 1 | тримання False' -and -not $script:LightHeld)}
            Clear-Box
            $ev = Tick $false
            [pscustomobject]@{Name="світло повернулось за зайнятої GPU — запит із дисплеєм: $ev";Ok=($ev -ceq 'тримання True з дисплеєм' -and $script:LightDisplay)}
            $leaseLock.Dispose(); Remove-Item -LiteralPath $sessPath -Force
            $ev = Tick $false
            [pscustomobject]@{Name="сесію закрито — знову лише система: $ev";Ok=($ev -ceq 'тримання True' -and -not $script:LightDisplay)}
            [IO.File]::WriteAllText($sessPath, '{"v":2}')
            $ev = Tick $false
            [pscustomobject]@{Name="запис сесії нечитаний — GPU не вільна, дисплей і причина в журналі: $ev; $($script:Log -join ' / ')";Ok=($ev -ceq 'тримання True з дисплеєм' -and $script:Log.Count -eq 1 -and $script:Log[-1] -cmatch 'GPU зайнята \(запис GPU-сесії нечитаний: ')}
            Remove-Item -LiteralPath $sessPath -Force
            Set-LightHold $false
            $script:Refuse = $true; $script:LightRefused = $false
            $ev = Tick $false
            $refused = @($script:Log | Where-Object { $_ -cmatch 'НЕ ПРИЙНЯТО' }).Count
            $ev += ' / ' + (Tick $false)
            $refused += @($script:Log | Where-Object { $_ -cmatch 'НЕ ПРИЙНЯТО' }).Count
            [pscustomobject]@{Name="запит не прийнято — тримач пробує щотакту, журнал каже раз: $ev; $refused";Ok=($ev -ceq 'тримання True / тримання True' -and -not $script:LightHeld -and $refused -eq 1)}
            $script:Refuse = $false
            # Пауза рушія (навіть планувальника) лише заморожує: ні рядків, ні запиту.
            $script:Events.Clear(); $script:Battery = @($true, $true, $false); $script:PauseMachine = $true
            Wait-PowerPause
            $ev = $script:Events -join ' | '
            [pscustomobject]@{Name="пауза планувальника рядків не пише й ноутбука не тримає: $ev";Ok=($ev -ceq 'світло-чекання' -and @(Get-Outbox).Count -eq 0)}
            # Постійний процес: нова версія — вихід із відпущеним запитом; другий тримач при живому першому — одразу вихід.
            Set-LightHold $false; $script:Events.Clear(); $script:Battery = @($false); $script:Ver = @('', 'aaaaaaaa → bbbbbbbb')
            $code = Invoke-Light
            $ev = $script:Events -join ' | '
            [pscustomobject]@{Name="нова версія — тримач виходить кодом 0 і відпускає запит: $code; $ev";Ok=($code -eq 0 -and $ev -ceq 'тримання True | такт | тримання False' -and -not $script:LightHeld)}
            $lock = Open-Lock (Join-Path $WorkDir 'light.lock')
            $script:Events.Clear(); $script:Ver = @('')
            $code = Invoke-Light
            $lock.Dispose()
            [pscustomobject]@{Name="другий тримач при живому першому (light.lock) виходить, нічого не чіпаючи: $code";Ok=($code -eq 0 -and $script:Events.Count -eq 0)}
        }
        Export-ModuleMember -Function Run
    }
    foreach ($check in @(& $light {Run})) {Check $check.Name $check.Ok}
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
# Артефакти лишаються в TEMP стенда; він не торкається робочих обгорток і станів ноутбука.
"провалів: $bad"
exit ([int]($bad -gt 0))
