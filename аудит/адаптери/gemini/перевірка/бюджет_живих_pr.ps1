#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir, [Alias('Phase')][ValidateSet('ДО','ПІСЛЯ')][string]$MeasurePhase = 'ПІСЛЯ')
$ErrorActionPreference = 'Stop'
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('review-budget-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Друкує вимір і повертає ненульовий код за невиконання мірила. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:failures++ }
}
try {
    $script:ApiCalls = 0; $script:Burned = 0; $script:Models = 0; $script:LockHeldInRequest = $false
    $script:Clock = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $shared = Join-Path $tmp 'lanes'; [void][IO.Directory]::CreateDirectory($shared)
    $head = 'b' * 40
    foreach ($lane in @('codex','agy','claude')) {
        $case = Join-Path $tmp $lane
        $OutboxDir = Join-Path $case 'lines'; $OutDir = Join-Path $case 'out'; $WorkDir = $case
        if ($lane -eq 'claude') {
            . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $case -RepoDir $case -OutboxDir "$case/lines" -LaneDir $shared -NoStatus
        # Тут вимірюється бюджет звірки голови; дані рецензії перевіряє окремий стенд.
        function Get-AutoReviewInput { '[]' }
        function Get-NightlyMarker { }
        } else {
            . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir $case -RepoDir $case -OutDir "$case/out" -LaneDir $shared -EnableCodex
        # Тут вимірюється бюджет звірки голови; дані рецензії перевіряє окремий стенд.
        function Get-AutoReviewInput { '[]' }
        function Get-NightlyMarker { }
            $script:Lanes = @($lane)
        }
        $script:StateDir = Join-Path $case 'state'; $script:SlotDir = Join-Path $case 'slots'
        foreach ($d in @($case,$script:StateDir,$script:SlotDir,$OutDir,$OutboxDir,"$case/runs")) {
            if ($d) { [void][IO.Directory]::CreateDirectory($d) }
        }
        $script:Limits = @{slots=@{codex=4;agy=4;claude=4}; poll_minutes=$script:Defaults['poll_minutes']}
        $script:ReadySlot = $false; $script:ApiError = ''; $script:Jobs = New-Object Collections.ArrayList
        $script:Markers = @()
        $model = switch ($lane) {codex {'gpt-6.1-sol-high'} agy {'gemini-3.8-flash-high'} claude {'cc-claude-opus-5-5-high'}}
        for ($n = 1; $n -le 10; $n++) {
            $number = 100 + $script:Markers.Count + $(switch ($lane) {codex {0} agy {10} claude {20}})
            $script:Markers += ConvertTo-Marker ("refs/remotes/origin/gemini-queue/автоперевірка-$number-$head/$model/1`t$head`t$script:Clock")
        }
        # Перевірки Claude на ноутбуці вже не ставляться; бюджет API смуги міряємо на нарядах із переліку ноутбука.
        $script:Limits.claude_laptop = @($script:Markers | ForEach-Object { $_.Slug })
        function Get-Markers { $script:Markers }
        function Get-ReviewTime { $script:Clock }
        function Write-Log([string]$Text) { }
        function Invoke-RestMethod {
            param($Uri,$Method,$TimeoutSec,$MaximumRedirection,$Headers)
            $script:ApiCalls++
            if ((Test-Path -LiteralPath $LaneDir) -and -not (Test-LockFree (Join-Path $LaneDir 'review-api.lock'))) { $script:LockHeldInRequest = $true }
            if ($script:ApiError) { throw $script:ApiError }
            $number = ($Uri -split '/')[-1]
            [pscustomobject]@{number=[int]$number;state='open';user=@{login='mightyrochy'};head=@{sha=$head;ref='claude/живий';repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}}}
        }
        function Select-Engine($M,[long]$After) { [pscustomobject]@{Engine=@{Name=$lane;Model='стенд';Effort='high'};Model=$M.Model;Quota=@{Blocked=$false;Known=$false;Group='';Left=0}} }
        function Get-FreeSlot { if ($script:ReadySlot) { 'стенд-1' } }
        function Test-SlugBusy { $false }
        function Start-Worker($Job,[string]$Dir) { [void]$script:Jobs.Add($Job); [pscustomobject]@{Slug=$Job.slug;Proc=@{HasExited=$true};Gpu=$false} }
        function Get-RefSha { $head }
        function Invoke-Git { [pscustomobject]@{Code=0;Out='Наряд стенда';Err=''} }
        function Reset-WorkTree { }
        function Get-Prompt { 'Наряд стенда' }
        function Find-EngineExe { 'стенд' }
        function Find-CodexExe { 'стенд' }
        function Find-Exe { 'стенд' }
        function Get-ContinueBranch { '' }
        function Get-Quota { [pscustomobject]@{Known=$false} }
        function Invoke-Agent { $script:Models++; [pscustomobject]@{Tail='';Code='NO_REPORT';Report='NONE';Turns=1} }
        function Invoke-Claude { $script:Models++; [pscustomobject]@{Kind='NO_REPORT'} }
        function Complete-Status($Status,$StatePath) {
            Write-FileAtomic $StatePath "DONE $($Status.id) $($Status.code)"
            Remove-Claim $StatePath
        }
        # 60 хвилинних проходів на 30 позначках у трьох смугах; перші 30 без слота, наступні зі слотом.
        $before = $script:ApiCalls
        $workers = New-Object Collections.ArrayList
        for ($poll = 0; $poll -lt 60; $poll++) {
            $script:ReadySlot = $poll -ge 30
            $script:Clock = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + $poll * 60
            $null = Start-Markers $workers
            foreach ($job in @($script:Jobs)) {
                $m = @($script:Markers | Where-Object { $_.Slug -eq $job.slug })[0]
                if ($lane -eq 'claude') { $m = Add-ClaudeFields $m }
                $null = Invoke-Task $m $job
            }
            $script:Jobs.Clear()
        }
        "$MeasurePhase $lane : API за 60 проходів = $($script:ApiCalls - $before)"
        Check "$lane : усі десять живих позначок дійшли до моделі" ($script:Models -eq $(switch ($lane) {codex {10} agy {20} claude {30}}))
    }
    "$MeasurePhase разом: 30 позначок, 60 проходів, API=$script:ApiCalls, моделей=$script:Models"
    Check 'бюджет запитів до API' ($script:ApiCalls -eq $(if ($MeasurePhase -eq 'ДО') {690} else {30}))
    if ($MeasurePhase -eq 'ПІСЛЯ') {
        # Новий процес читає той самий бюджет; додаткові PR і зміна смуги не обходять межу.
        Check '31-й запит відкладено' ((Get-AutoReviewState "автоперевірка-999-$head") -eq 'REVIEW_API' -and $script:ApiCalls -eq 30)
        $savedNow = $script:Clock
        $clockFile = Join-Path $shared 'clock.txt'; [IO.File]::WriteAllText($clockFile,[string]$savedNow)
        $child = Join-Path $tmp 'child.ps1'
        $source = (Join-Path $SourceDir 'queue_lanes.ps1').Replace("'","''")
        $childText = @"
`$LaneDir = '$($shared.Replace("'","''"))'
. '$source'
function Get-ReviewTime { [long][IO.File]::ReadAllText('$($clockFile.Replace("'","''"))') }
function Invoke-RestMethod { throw 'НЕОЧІКУВАНИЙ ЗАПИТ' }
if ((Get-AutoReviewState 'автоперевірка-999-$head') -ne 'REVIEW_API') { exit 1 }
if (([IO.File]::ReadAllText((Join-Path `$LaneDir 'review-api.json')) | ConvertFrom-Json).calls.Count -ne 30) { exit 2 }
"@
        [IO.File]::WriteAllText($child,$childText,(New-Object Text.UTF8Encoding($true)))
        & (Get-Process -Id $PID).Path -NoProfile -ExecutionPolicy Bypass -File $child
        Check 'спільний бюджет зберігається в новому процесі' ($LASTEXITCODE -eq 0)
        $script:Clock += 3601
        Check 'після рухомої години свіжий PR перевіряється' ((Get-AutoReviewState "автоперевірка-999-$head") -eq 'LIVE' -and $script:ApiCalls -eq 31)
        Check 'запит REST іде поза замком бюджету (замок на час запиту не мав верхньої межі: DNS поза -TimeoutSec)' (-not $script:LockHeldInRequest)
        # Корінь «REVIEW_API» без причини: замок бюджету тримає процес, що робить запит; друга позначка того ж проходу чекає
        # (ДО — одразу REVIEW_API, ПІСЛЯ — обидві доходять) і, якщо замок не звільнився, називає причину «замок».
        $savedLane = $LaneDir; $LaneDir = Join-Path $tmp 'hold'; [void][IO.Directory]::CreateDirectory($LaneDir)
        $ready = Join-Path $LaneDir 'ready.txt'; $holder = Join-Path $tmp 'holder.ps1'
        $holdText = "`$l = [IO.File]::Open('$((Join-Path $LaneDir 'review-api.lock').Replace("'","''"))','OpenOrCreate','ReadWrite','None')`n[IO.File]::WriteAllText('$($ready.Replace("'","''"))','1')`nStart-Sleep -Seconds 3`n`$l.Dispose()"
        [IO.File]::WriteAllText($holder,$holdText,(New-Object Text.UTF8Encoding($true)))
        $holdProc = Start-Process -FilePath (Get-Process -Id $PID).Path -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$holder) -PassThru -WindowStyle Hidden
        $until = [DateTime]::UtcNow.AddSeconds(30)
        while (-not (Test-Path -LiteralPath $ready) -and [DateTime]::UtcNow -lt $until) { Start-Sleep -Milliseconds 100 }
        $script:Clock = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); $callsBefore = $script:ApiCalls
        $waited = [Diagnostics.Stopwatch]::StartNew()
        Check 'замок бюджету зайнятий іншим процесом: звірка чекає й проходить' ((Get-AutoReviewState "автоперевірка-998-$head") -eq 'LIVE' -and $script:ApiCalls -eq $callsBefore + 1 -and $waited.Elapsed.TotalSeconds -ge 1)
        [void]$holdProc.WaitForExit(15000)
        $held = [IO.File]::Open((Join-Path $LaneDir 'review-api.lock'),'OpenOrCreate','ReadWrite','None')
        $oldBound = Get-Variable -Name Bound -Scope Script -ValueOnly -ErrorAction SilentlyContinue; $script:Bound = @{ PollMinutes = 0.02 }
        $r = Get-AutoReviewState "автоперевірка-998-$head"
        if ($null -eq $oldBound) { Remove-Variable -Name Bound -Scope Script -ErrorAction SilentlyContinue } else { $script:Bound = $oldBound }; $held.Dispose()
        Check "замок не звільнився за межу: REVIEW_API з ознакою «замок» (є «$script:ReviewApiCause»)" ($r -eq 'REVIEW_API' -and $script:ReviewApiCause -ceq 'замок' -and $script:ApiCalls -eq $callsBefore + 1)
        $LaneDir = $savedLane
        # Ознаки інших гілок відмови.
        $dir = Join-Path $tmp 'cause'; [void][IO.Directory]::CreateDirectory($dir); $LaneDir = $dir; $now = $script:Clock
        $bf = Join-Path $dir 'review-api.json'
        [IO.File]::WriteAllText($bf,'{"x":1}',(New-Object Text.UTF8Encoding($false)))
        $r1 = Get-AutoReviewState "автоперевірка-997-$head"; $c1 = $script:ReviewApiCause
        [IO.File]::WriteAllText($bf,('{"calls":[],"until":' + ($now + 100) + '}'),(New-Object Text.UTF8Encoding($false)))
        $r2 = Get-AutoReviewState "автоперевірка-997-$head"; $c2 = $script:ReviewApiCause
        [IO.File]::WriteAllText($bf,('{"calls":[' + ((1..30 | ForEach-Object { $now }) -join ',') + '],"until":0}'),(New-Object Text.UTF8Encoding($false)))
        $r3 = Get-AutoReviewState "автоперевірка-997-$head"; $c3 = $script:ReviewApiCause
        Check "ознаки: пошкоджений бюджет «$c1», чекання «$c2», вичерпано «$c3»" ($r1 -eq 'REVIEW_API' -and $r2 -eq 'REVIEW_API' -and $r3 -eq 'REVIEW_API' -and $c1 -ceq 'бюджет пошкоджено' -and $c2 -ceq 'чекання' -and $c3 -ceq 'бюджет вичерпано')
        $ioErr = New-Object System.IO.IOException 'секретний текст відповіді'
        $toErr = New-Object System.TimeoutException 'секретний текст відповіді'
        $respErr = New-Object System.Exception 'REVIEW_RESPONSE'; $httpErr = New-Object System.Exception 'The remote server returned an error: (503) Server Unavailable.'
        $causes = @((Get-ReviewApiCause $ioErr),(Get-ReviewApiCause $toErr),(Get-ReviewApiCause $respErr),(Get-ReviewApiCause $httpErr))
        Check "ознаки винятків без тексту відповіді: $($causes -join ' | ')" ($causes[0] -ceq 'мережа' -and $causes[1] -ceq 'межа часу' -and $causes[2] -ceq 'відповідь' -and $causes[3] -ceq 'HTTP 503' -and -not (($causes -join '') -match 'секретний'))
        $LaneDir = $savedLane
        # Межа застряглої передачі git: мережева команда несе lowSpeed від poll_minutes, локальна — ні.
        $net = @(Get-GitStallOptions @('fetch','-q','origin')); $loc = @(Get-GitStallOptions @('rev-parse','HEAD'))
        $expect = [string][int]((Get-Limit $script:Limits 'PollMinutes' 'poll_minutes') * 60)
        Check "fetch: http.lowSpeedLimit=1 і http.lowSpeedTime=$expect (poll_minutes × 60); rev-parse без меж" ($net -ccontains 'http.lowSpeedLimit=1' -and $net -ccontains "http.lowSpeedTime=$expect" -and $loc.Count -eq 0)
    }
    # Відмова вже взятої позначки: реальний Invoke-Task у кожній смузі, не лише чиста функція API.
    foreach ($lane in @('codex','agy','claude')) {
        # Функції Invoke-Task завантажуються знову, IO та виклики моделей лишаються підмінами стенда.
        $name = if ($lane -eq 'claude') {'claude_run.ps1'} else {'gemini_run.ps1'}
        # AST бере саме поточне тіло функції з перевірюваного джерела, зберігаючи ізоляцію стенда.
        $tokens=$null; $errors=$null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir $name),[ref]$tokens,[ref]$errors)
        $fn = $ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-Task'},$false)
        . ([scriptblock]::Create($fn.Extent.Text))
        foreach ($errorText in @('HTTP 403','HTTP 429','мережевий збій')) {
            $LaneDir = Join-Path $tmp ("error-$lane-" + [guid]::NewGuid().ToString('N'))
            [void][IO.Directory]::CreateDirectory($LaneDir)
            $script:Clock = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
            $script:ApiError = $errorText
            $m = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/автоперевірка-777-$head/$model/1`t$head`t$script:Clock")
            if ($lane -eq 'claude') { $m = Add-ClaudeFields $m }
            $sp = Get-StatePath (Get-MarkerKey $m)
            Write-FileAtomic $sp ('WAIT {"until":0,"retakes":5}')
            $id = '20261028-060000-abcdefabcdef'; $dir = Join-Path $WorkDir "runs/$id"
            [void][IO.Directory]::CreateDirectory($dir)
            [void](New-Claim $m $id)
            $job = @{id=$id;dir=$dir;slot='стенд-1';head=('c'*40);sel=@{engine=$lane;model=$model;emodel='стенд';effort='high';qknown=$false;qleft=0;qgroup=''}}
            $priorModels = $script:Models
            $null = Invoke-Task $m $job
            $st = Get-MarkerState $m
            $ok = $st.Kind -eq 'WAIT' -and (Get-Retakes $sp) -eq 5 -and $script:Models -eq $priorModels
            if ($MeasurePhase -eq 'ПІСЛЯ') { Check "$lane $errorText : WAIT, retakes=5, без моделі" $ok }
            if ($MeasurePhase -eq 'ПІСЛЯ') { $wantCause = $(if ($errorText -ceq 'мережевий збій') { 'запит RuntimeException' } else { $errorText }); Check "$lane $errorText : причина в стані позначки «$($st.Wait.reason)»" ($st.Kind -eq 'WAIT' -and $st.Wait.reason -ceq $wantCause) }
            else { if (-not $ok) { $script:Burned++ } }
            if ($MeasurePhase -eq 'ПІСЛЯ') {
                if ($lane -ne 'claude' -and $st.Kind -eq 'WAIT') { Check "$lane : збережено голову продовження" ($st.Wait.head -eq ('c'*40)) }
                $script:ApiError = ''; $script:Clock += 121
                $null = Invoke-Task $m $job
                Check "$lane $errorText : та сама спроба запускається після відновлення" ($script:Models -eq ($priorModels+1))
            }
        }
    }
    "$MeasurePhase спалених спроб через відмови API=$script:Burned"
    if ($MeasurePhase -eq 'ПІСЛЯ') { Check 'відмови API не спалюють спроби' ($script:Burned -eq 0) }
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^review-budget-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($failures) { exit 1 }
