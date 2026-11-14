#Requires -Version 5.1
<#
Перезавантаження Windows посеред наряду й виняток публікатора: робота не губиться мовчки.

Ланцюг справжніх функцій трьох процесів через спільні теки стенда: gemini_run (Complete-Status з finally обірваного
наряду) → gemini_publish (Main: подія boot, Get-Line, Publish-Bundle підмінено) → gemini_run (Import-SleepRetries).
Підмінено лише межі з мережею, git і ОС. -SourceDir на старі файли обгортки — стенд падає (ДО), на нові — проходить.
#>
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('reboot-stand-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Провал твердження червонить код виходу стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
$now = [datetime]::UtcNow
try {
    $run = New-Module -ArgumentList $SourceDir,$tmp,$now -ScriptBlock {
        param($src,$tmp,$now)
        . (Join-Path $src 'gemini_run.ps1') -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/trusted"
        $script:StateDir = Join-Path $RunsDir 'state'; $script:SlotDir = Join-Path $RunsDir 'slots'
        foreach ($d in @($RunsDir,$script:StateDir,$script:SlotDir,$OutDir,$LaneDir,$UpdateRoot)) { [void][IO.Directory]::CreateDirectory($d) }
        $script:Marker = 'a'*40; $script:Head = 'c'*40
        function Marker([string]$Slug) {
            [pscustomobject]@{Valid=$true;Name="gemini-queue/$Slug/gpt-test-high/1/p1";Ref="refs/remotes/origin/gemini-queue/$Slug/gpt-test-high/1/p1";Sha=$script:Marker;Slug=$Slug;Model='gpt-test-high';N='1';Cond='p1';Lane='codex';Time=0;Seen=0;Gpu=$false;Prio=1;Deadline=''}
        }
        function Get-Facts($M, [string]$Start) { [pscustomobject]@{Head=$script:Head;OnBranch=$true;Dirty=0;Ahead=$script:Ahead[$M.Slug]} }
        function Invoke-Git {
            <# Лише bundle create (файл .part) і is-ancestor; інший git стенду не потрібен. #>
            if ($args[0] -contains 'bundle') { [IO.File]::WriteAllText($args[0][3], 'бандл') }
            [pscustomobject]@{Code=0;Out='';Err=''}
        }
        function Get-RefSha { $script:Head }
        function Test-SleepRetryPath { $true }
        function Test-SlugBusy { $false }
        function Get-Markers { @(Marker 'обрив-коміти'; Marker 'обрив-порожній') }
        $script:Ahead = @{'обрив-коміти'=7; 'обрив-порожній'=0}
        function Finish([string]$Slug, [string]$Id) {
            <# Те, що робить finally Invoke-Task, коли вимкнення зупинило конвеєр: код ще порожній. #>
            $m = Marker $Slug; $state = Get-StatePath (Get-MarkerKey $m)
            $status = [ordered]@{ v=1; id=$Id; slug=$Slug; model=$m.Model; n=1; marker=$m.Sha; cond=$m.Cond; slot='codex-1'
                start=$script:Marker; head=''; code=''; report='NONE'; ahead=0; turns=0; minutes=0; bundle=''; engine='codex'
                retakes=0; started_utc=$now.AddHours(-3).ToString('o'); ended_utc=''; sleep_parent=''; actual='gpt-test-high' }
            Write-FileAtomic $state ('STARTED ' + ($status | ConvertTo-Json -Compress))
            Complete-Status $status $state '' $now.AddHours(-3)
            [IO.File]::ReadAllText($state, $script:Utf8)
        }
        function Requeue([string]$Slug) {
            <# Наступний прохід планувальника після нового завантаження: запит повтору від публікатора. #>
            Import-SleepRetries
            Get-MarkerState (Marker $Slug)
        }
        Export-ModuleMember -Function Finish,Requeue
    }
    $ids = @{ commits = '20261110-215213-000000000001'; empty = '20261111-001700-000000000002'; done = '20261110-215212-000000000003'; late = '20261110-215212-000000000004' }
    $stateA = & $run { param($i) Finish 'обрив-коміти' $i } $ids.commits
    $stateB = & $run { param($i) Finish 'обрив-порожній' $i } $ids.empty
    $saved = [IO.File]::ReadAllText((Join-Path "$tmp/out" ($ids.commits + '.json'))) | ConvertFrom-Json
    Check 'обірваний finally-ом наряд: код INTERRUPTED, а не порожній' ($saved.code -ceq 'INTERRUPTED' -and $stateA -ceq "DONE $($ids.commits) INTERRUPTED" -and $stateB -ceq "DONE $($ids.empty) INTERRUPTED")
    Check 'сім комітів обірваного наряду — у бандлі' ($saved.ahead -eq 7 -and $saved.bundle -ceq ($ids.commits + '.bundle'))

    $pub = New-Module -ArgumentList $SourceDir,$tmp,$now -ScriptBlock {
        param($src,$tmp,$now)
        . (Join-Path $src 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/trusted"
        foreach ($d in @($WorkDir,"$WorkDir/seen",$OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
        $script:Clock = $now.AddMinutes(3); $script:Boot = $now.AddMinutes(2)
        $script:Published = @{}; $script:PublishCalls = 0; $script:Fail = @{}
        function Test-OwnerUser { $true }
        function Invoke-Native { [pscustomobject]@{Code=0;Out='';Err=''} }
        function Invoke-Git { [pscustomobject]@{Code=0;Out='';Err=''} }
        function Invoke-WrapperChain { }
        function Add-PoolsLine { }
        function Receive-HealthAlerts { }
        function Receive-Outbox { }
        function Merge-BlockedLines { }
        function Send-Pending { }
        function Write-DeliveryStatus { }
        function Test-UpdateRoot { $true }
        function Get-PowerTime { $script:Clock }
        function Get-PowerBoot { $script:Boot }
        function Get-WinEvent { }
        function Get-EngineLivePublication { [pscustomobject]@{Bad=@()} }
        function Get-RefSha([string]$Ref) {
            if ($Ref -cmatch '^refs/remotes/origin/gemini-queue/') { return 'a'*40 }
            if ($Ref -cmatch '^refs/remotes/origin/gemini/(.+)$' -and $script:Published.ContainsKey($Matches[1])) { return $script:Published[$Matches[1]] }
            'b'*40
        }
        function Publish-Bundle($S, [string]$Id) {
            <# Пуш підмінено; виняток — той, що 10.11 кинув сетер Console.InputEncoding без консолі. #>
            if ($script:Fail[$Id] -ceq 'push') { $script:Fail.Remove($Id); throw 'Exception setting "InputEncoding": "No process is on the other end of the pipe."' }
            $script:PublishCalls++; $script:Published[[string]$S.slug] = [string]$S.head
            @('OK', 1)
        }
        function Save-DraftRequest([string]$Branch, [string]$Head, [string]$Model) {
            if ($script:Fail[$Branch] -ceq 'draft') { $script:Fail.Remove($Branch); throw 'збій після пушу' }
        }
        function Lines { @(Get-ChildItem -LiteralPath $OutboxDir -Filter '*.txt' | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $script:Utf8).Trim() }) }
        function Pass {
            <# Один запуск публікатора (задача раз на хвилину). #>
            [void](Main)
            [pscustomobject]@{ Lines = @(Lines); Calls = $script:PublishCalls; Retries = @(Get-ChildItem -LiteralPath $UpdateRoot -Filter 'sleep-retry-*.json' | ForEach-Object { $_.Name }) }
        }
        function Done([string]$Id) { Test-Path -LiteralPath (Join-Path (Join-Path $WorkDir 'state') ($Id + '.json')) }
        function Seed([string]$Id, [string]$Slug, [string]$Fail) {
            <# Звичайний кінець ГОТОВО з бандлом. #>
            $s = [ordered]@{ v=1; id=$Id; slug=$Slug; model='gpt-test-high'; n=1; marker='a'*40; cond='p1'; head='d'*40; code='DONE'; report='DONE'
                ahead=2; turns=1; minutes=5; bundle=($Id + '.bundle'); started_utc=$now.AddHours(-1).ToString('o'); ended_utc=$now.AddHours(-1).ToString('o'); sleep_parent='' }
            Write-FileAtomic (Join-Path $OutDir ($Id + '.json')) ($s | ConvertTo-Json -Compress)
            if ($Fail -ceq 'push') { $script:Fail[$Id] = 'push' } elseif ($Fail) { $script:Fail["gemini/$Slug"] = $Fail }
        }
        # Публікатор до вимкнення бачив світ 10 хв тому; boot — після кінця обірваних нарядів.
        Write-FileAtomic (Join-Path $WorkDir 'sleep-events.json') (([ordered]@{read_utc=$now.AddMinutes(-10).ToString('o'); events=@()}) | ConvertTo-Json -Compress)
        Export-ModuleMember -Function Pass,Done,Seed
    }
    $p = & $pub { Pass }
    Check 'вимкнення — подія ВИМКНЕНО-СТАРТ' (@($p.Lines | Where-Object { $_ -cmatch '^GEMINI ОБГОРТКА: ВИМКНЕНО-СТАРТ ' }).Count -eq 1)
    Check 'жодного «gemini/невідомо STATE_INVALID» за обірвані наряди' (@($p.Lines | Where-Object { $_ -cmatch 'невідомо' }).Count -eq 0)
    Check 'коміти обірваного наряду опубліковано, як у звичайного прогону' ($p.Calls -eq 1)
    Check 'обидва обірвані наряди — один автоматичний повтор після вимкнення' ($p.Retries -contains "sleep-retry-$($ids.commits).json" -and $p.Retries -contains "sleep-retry-$($ids.empty).json")
    $wa = & $run { Requeue 'обрив-коміти' }; $wb = & $run { Requeue 'обрив-порожній' }
    Check 'позначки обірваних нарядів — у черзі (WAIT від опублікованої голови), а не DONE' ($wa.Kind -ceq 'WAIT' -and $wb.Kind -ceq 'WAIT' -and $wa.Wait.group -ceq 'SLEEP')

    & $pub { param($i) Seed $i 'виняток-пуш' 'push' } $ids.done
    $p = & $pub { Pass }
    $kept = -not (& $pub { param($i) Done $i } $ids.done)
    Check 'виняток посеред обробки — стан не записано, лишається на повтор' $kept
    $p = & $pub { Pass }
    Check 'наступний прохід публікує той самий стан і дає ГОТОВО' ((& $pub { param($i) Done $i } $ids.done) -and @($p.Lines | Where-Object { $_ -ceq ('GEMINI ОБГОРТКА: ГОТОВО gemini/виняток-пуш ' + 'd'*40) }).Count -eq 1)
    & $pub { param($i) Seed $i 'виняток-після' 'draft' } $ids.late
    $before = (& $pub { Pass }).Calls
    $p = & $pub { Pass }
    Check 'виняток після пушу: другого пушу нема, рядок ГОТОВО є' ($p.Calls -eq $before -and @($p.Lines | Where-Object { $_ -ceq ('GEMINI ОБГОРТКА: ГОТОВО gemini/виняток-після ' + 'd'*40) }).Count -eq 1)
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    if ((Split-Path -Leaf $resolved) -cmatch '^reboot-stand-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction SilentlyContinue }
}
"провалів: $bad"
exit ([int]($bad -gt 0))
