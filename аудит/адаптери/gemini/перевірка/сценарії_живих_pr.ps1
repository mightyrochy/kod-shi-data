#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot), [Alias('Phase')][ValidateSet('ДО','ПІСЛЯ')][string]$MeasurePhase = 'ПІСЛЯ')
$ErrorActionPreference = 'Stop'
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('live-pr-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Друкує факт; кожна відмова змінює код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:failures++ }
}
try {
    foreach ($lane in @('codex','agy','claude')) {
        $case = Join-Path $tmp $lane; [void][IO.Directory]::CreateDirectory($case)
        $seed = Join-Path $case 'seed'; $remote = Join-Path $case 'origin.git'
        & git init -q --bare $remote; & git init -q -b main $seed
        & git -C $seed config core.autocrlf false
        & git -C $seed config user.name 'стенд'; & git -C $seed config user.email 'stend@example.invalid'
        & git -C $seed remote add origin $remote
        foreach ($d in @('аудит/наряди','аудит/адаптери/gemini')) { [void][IO.Directory]::CreateDirectory((Join-Path $seed $d)) }
        Copy-Item -LiteralPath (Join-Path $SourceDir 'ланцюг.json') -Destination "$seed/аудит/адаптери/gemini/ланцюг.json"
        foreach ($task in @('автоперевірка','автоживий')) { [IO.File]::WriteAllText("$seed/аудит/наряди/$task.md", 'Наряд стенда', $utf) }
        & git -C $seed add -A; & git -C $seed commit -q -m 'стенд'; & git -C $seed push -q origin main
        $head = (& git -C $seed rev-parse HEAD).Trim(); $other = 'a' * 40
        $bare = Join-Path $case 'repo.git'; & git clone -q --bare $remote $bare
        . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$case/pub" -OutboxDir "$case/lines" -OutDir "$case/out"
        $script:Repo = $bare; $script:NoHooks = Join-Path $case 'no-hooks'
        foreach ($d in @($WorkDir,"$WorkDir/seen",$OutboxDir,$OutDir)) { [void][IO.Directory]::CreateDirectory($d) }
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        $script:CaseModel = switch ($lane) { codex { 'gpt-6.1-sol-high' } agy { 'gemini-3.8-flash-high' } claude { 'cc-claude-opus-5-5-high' } }
        function Pull([int]$Number, [string]$Branch, [string]$Sha, [string]$State='open') {
            <# Закритий, змінений, давній, звіт і живий PR у формі GitHub REST. #>
            [pscustomobject]@{number=$Number;title='Код';state=$State;created_at=[datetimeoffset]::UtcNow.AddDays(-10).ToString('o');updated_at=[datetimeoffset]::UtcNow.ToString('o');user=@{login='mightyrochy'};head=@{ref=$Branch;sha=$Sha;repo=@{full_name='mightyrochy/kod-shi-data'}};base=@{ref='main';repo=@{full_name='mightyrochy/kod-shi-data'}}}
        }
        $script:Cases = @{
            '1'=(Pull 1 'claude/закритий' $head 'closed'); '2'=(Pull 2 'claude/змінений' $other)
            '3'=(Pull 3 'claude/давній' $other); '4'=(Pull 4 'gemini/автоперевірка-звіт' $head)
            '5'=(Pull 5 'claude/живий' $head)
        }
        # Три вже наявні позначки: їх не видаляємо, навіть якщо ланцюг більше не вибирає ці PR.
        foreach ($n in @(1,2,4)) { Add-ChainMarker "автоперевірка-$n-$head" $script:CaseModel $head }
        function Get-ChainPulls { @($script:Cases['3'],$script:Cases['4'],$script:Cases['5']) }
        function Complete-EngineDrafts { }
        function Get-ReviewModels($Pull,$Config) { $script:CaseModel }
        function Invoke-ChainApi([string]$Path) {
            if ($Path -match '/files\?') { return [pscustomobject]@{filename='джерела/a.py'} }
            $sha = ($Path -split '/')[-1]
            $date = if ($sha -eq ('a' * 40)) { [datetimeoffset]::UtcNow.AddDays(-10) } else { [datetimeoffset]::UtcNow.AddMinutes(-1) }
            [pscustomobject]@{sha=$sha;commit=@{committer=@{date=$date.ToString('o')}}}
        }
        Invoke-WrapperChain
        $refs = @(& git -C $remote for-each-ref '--format=%(refname)' refs/heads/gemini-queue/)
        Check "$MeasurePhase $lane : давній PR із сьогоднішнім коментарем" ((@($refs | Where-Object { $_ -match 'автоперевірка-3-' }).Count -eq 0) -eq ($MeasurePhase -eq 'ПІСЛЯ'))
        $pubWork = $WorkDir
        if ($lane -eq 'claude') {
            . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$case/claude" -RepoDir $seed -OutboxDir "$case/lines" -LaneDir "$case/lanes" -NoStatus
        } else {
            . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$case/runs" -RepoDir $seed -OutDir "$case/out" -LaneDir "$case/lanes" -EnableCodex
            $script:Lanes = @($lane)
        }
        $script:StateDir = Join-Path $case 'state'; $script:SlotDir = Join-Path $case 'slots'
        $script:NoHooks = Join-Path $case 'no-hooks'; $script:Limits = @{slots=@{codex=4;agy=4;claude=4}}
        foreach ($d in @($script:StateDir,$script:SlotDir,$RunsDir,$OutDir,$LaneDir)) { if ($d) { [void][IO.Directory]::CreateDirectory($d) } }
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main','+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
        $script:Jobs = New-Object Collections.ArrayList
        $script:ApiFail = $false
        function Invoke-RestMethod {
            param($Uri,$Method,$TimeoutSec,$MaximumRedirection,$Headers)
            if ($script:ApiFail) { throw 'HTTP 503' }
            $script:Cases[($Uri -split '/')[-1]]
        }
        function Write-Log([string]$Text) { }
        function Select-Engine($M,[long]$After) {
            [pscustomobject]@{Engine=@{Name=$lane;Model='модель-стенда';Effort='high'};Model=$M.Model;Quota=@{Blocked=$false;Known=$false;Group='';Left=0}}
        }
        function Get-FreeSlot { 'стенд-1' }
        function Test-SlugBusy { $false }
        function Start-Worker($Job,[string]$Dir) {
            [void]$script:Jobs.Add($Job)
            [pscustomobject]@{Slug=$Job.slug;Proc=@{HasExited=$true};Gpu=$false}
        }
        $workers = New-Object Collections.ArrayList
        $null = Start-Markers $workers
        function Get-AutoReviewInput { '[]' }
        $script:Models = 0
        function Find-EngineExe { 'стенд' }
        function Find-CodexExe { 'стенд' }
        function Find-Exe { 'стенд' }
        function Get-Quota { [pscustomobject]@{Known=$false} }
        function Invoke-Agent {
            $script:Models++
            [pscustomobject]@{Tail='';Code='NO_REPORT';Report='NONE';Turns=1}
        }
        function Invoke-Claude {
            $script:Models++
            [pscustomobject]@{Kind='NO_REPORT'}
        }
        foreach ($job in $script:Jobs) {
            $m = @(Get-Markers | Where-Object { $_.Slug -ceq $job.slug })[0]
            if ($lane -eq 'claude') { $m = Add-ClaudeFields $m }
            $null = Invoke-Task $m $job
        }
        "$MeasurePhase $lane : запусків моделі $script:Models/5"
        $expected = if ($MeasurePhase -eq 'ДО') { 5 } else { 1 }
        Check "$MeasurePhase $lane : точне мірило" ($script:Models -eq $expected)
        if ($MeasurePhase -eq 'ПІСЛЯ') {
            if ($lane -eq 'claude') {
                $staleLines = @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' | ForEach-Object { [IO.File]::ReadAllText($_.FullName) } | Where-Object { $_ -match ' STALE\s*$' })
                Check "$lane : три службові рядки STALE" ($staleLines.Count -eq 3)
            } else {
                $WorkDir = $pubWork
                $sent = 0; $duplicates = 0
                foreach ($file in @(Get-ChildItem -LiteralPath $OutDir -Filter '*.json')) {
                    $result = ConvertFrom-Json ([IO.File]::ReadAllText($file.FullName))
                    if ($result.code -ne 'STALE') { continue }
                    $line = Get-Line $file.BaseName
                    if ($null -ne $line -and $line.Outbox -match ' STALE$') { $sent++ }
                    if ($null -ne (Get-Line $file.BaseName)) { $duplicates++ }
                }
                Check "$lane : публікатор прийняв три STALE, без повторних рядків" ($sent -eq 3 -and $duplicates -eq 0)
            }
            $states = @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.txt' | ForEach-Object { [IO.File]::ReadAllText($_.FullName) })
            Check "$lane : три старі позначки закрито STALE" (@($states | Where-Object { $_ -match ' STALE$' }).Count -eq 3)
            $script:Jobs.Clear(); $null = Start-Markers $workers
            Check "$lane : повтор не запускає й не закриває вдруге" ($script:Jobs.Count -eq 0)
            # API-відмова до старту не перетворює невідоме на LIVE чи на STALE.
            $slug = "автоперевірка-6-$head"
            [void](Invoke-Git @('push','-q','origin',"${head}:refs/heads/gemini-queue/$slug/$script:CaseModel/1"))
            [void](Invoke-Git @('fetch','-q','origin','+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
            $script:Cases['6'] = Pull 6 'claude/після-збою' $head
            $script:ApiFail = $true; $null = Start-Markers $workers
            $m = @(Get-Markers | Where-Object { $_.Slug -eq $slug })[0]
            if ($lane -eq 'claude') { $m = Add-ClaudeFields $m }
            $job = $script:Jobs[0]; $priorModels = $script:Models
            $null = Invoke-Task $m $job
            Check "$lane : збій API повертає позначку в WAIT, без моделі" ((Get-MarkerState $m).Kind -eq 'WAIT' -and $script:Models -eq $priorModels -and (Get-Retakes (Get-StatePath (Get-MarkerKey $m))) -eq 0)
            $script:ApiFail = $false
            # Пересуваємо лише годинник API; черга й бюджет зберігаються, реального чекання нема.
            function Get-ReviewTime { [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + 121 }
            $null = Invoke-Task $m $job
            Check "$lane : після відновлення API та сама позначка запускає модель" ($script:Models -eq ($priorModels + 1))
            Remove-Item Function:Get-ReviewTime
            . (Join-Path $SourceDir 'queue_lanes.ps1')
        }
    }
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^live-pr-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($failures) { exit 1 }
