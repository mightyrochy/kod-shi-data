#Requires -Version 5.1
<# Квота-повтор без нових комітів (gemini-run): коміт першої спроби C1 не губиться. Справжні Get-RunStart, Get-WaitResume,
Enter-RunQuotaWait, Enter-StartQuotaWait, Test-Report, Complete-Status, Resume-Interrupted і Get-RunDelivered на
локальних репозиторіях; підмінено лише Get-Quota (квота невідома — чекання quota_wait_minutes). Агента нема: спроба
комітить (чи ні) у клоні сама, як агент у копії задачі. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('kvota-povtor-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) { if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ } }
function Fixture-Git([string]$At, [string[]]$Items) {
    <# Команда git стенда; помилка — виняток. #>
    $out = & git -C $At -c user.name=stand -c user.email=stand@example.invalid -c core.autocrlf=false @Items 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($out -join "`n") }
    ($out -join "`n").Trim()
}
try {
    $origin = Join-Path $tmp 'origin.git'; $seed = Join-Path $tmp 'seed'; $clone = Join-Path $tmp 'clone'
    [void](Fixture-Git $tmp @('init', '-q', '--bare', $origin))
    [void][IO.Directory]::CreateDirectory($seed)
    [void](Fixture-Git $seed @('init', '-q', '-b', 'main'))
    [IO.File]::WriteAllText((Join-Path $seed 'base.txt'), "base`n")
    [void](Fixture-Git $seed @('add', '.')); [void](Fixture-Git $seed @('commit', '-q', '-m', 'База позначки'))
    [void](Fixture-Git $seed @('push', '-q', $origin, 'main'))
    [void](Fixture-Git $tmp @('clone', '-q', $origin, $clone))
    . (Join-Path $SourceDir 'gemini_run.ps1') -RepoDir $clone -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/update"
    $script:StateDir = "$RunsDir/state"; $script:SlotDir = "$RunsDir/slots"; $script:Limits = $null; $script:Lanes = @('agy')
    $script:NoHooks = Join-Path $tmp 'no-hooks'
    foreach ($dir in @($RunsDir, $script:StateDir, $script:SlotDir, $OutDir, $LaneDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    function Get-Quota { [pscustomobject]@{ Known = $false; Group = 'GEMINI'; Left = 0 } }
    $main = Get-RefSha 'refs/remotes/origin/main'
    $m = [pscustomobject]@{ Ref = 'refs/remotes/origin/gemini-queue/probe/gemini-3.8-flash-high/1'; Name = 'gemini-queue/probe/gemini-3.8-flash-high/1'
        Sha = $main; Slug = 'probe'; Model = 'gemini-3.8-flash-high'; N = '1'; Cond = '' }
    $sel = [pscustomobject]@{ Engine = [pscustomobject]@{ Name = 'agy' }; Model = $m.Model }
    function Attempt([string]$Id, [string]$Base) { [ordered]@{ v = 1; id = $Id; slug = 'probe'; model = $m.Model; n = 1; marker = $main; cond = ''
        slot = ''; start = $Base; head = ''; code = 'QUOTA'; report = 'NONE'; ahead = 0; turns = 1; minutes = 0; bundle = '' } }
    function Resume { Get-WaitResume (Get-MarkerState $m).Wait }

    # Спроба 1: нова, від main; агент комітить C1, далі 429.
    $r1 = Get-RunStart '' $main (Get-WaitResume $null)
    [void](Fixture-Git $clone @('checkout', '-q', '-B', 'gemini/probe', $r1.Start))
    [IO.File]::WriteAllText((Join-Path $clone 'work.txt'), "C1`n")
    [void](Fixture-Git $clone @('add', '.')); [void](Fixture-Git $clone @('commit', '-q', '-m', 'Робота спроби 1'))
    $c1 = Get-RefSha 'HEAD'
    [void](Enter-RunQuotaWait $m $sel (Attempt 'r1' $r1.Base) $null '')
    $w = Resume
    Check "спроба 1: чекання несе голову C1 і основу main" ($w.head -ceq $c1 -and $w.base -ceq $main)

    # Спроба 2: повтор від C1, нових комітів нема, знову 429.
    $r2 = Get-RunStart '' $main (Resume)
    Check "повтор: старт — голова C1, основа доставки — main" ($r2.Start -ceq $c1 -and $r2.Base -ceq $main -and $null -eq $r2.Attempt)
    $old = Attempt 'до' $r2.Start
    Complete-Status $old (Join-Path $tmp 'до.txt') '' ([datetime]::MinValue)
    "ДО (основа = голова повтору): комітів $($old.ahead), бандл '$($old.bundle)'"
    [void](Enter-RunQuotaWait $m $sel (Attempt 'r2' $r2.Base) $null '')
    $w = Resume
    Check "повтор без комітів: голова чекання не порожня (C1), основа main" ($w.head -ceq $c1 -and $w.base -ceq $main)
    Enter-StartQuotaWait $m ([pscustomobject]@{ Group = 'GEMINI'; ResetAt = 0 }) (Get-MarkerState $m)
    $w = Resume
    Check "квота до старту переносить голову й основу" ($w.head -ceq $c1 -and $w.base -ceq $main)

    # Спроба 3: повтор без комітів, звіт ГОТОВО на C1 — прийнято, бандл несе C1.
    $r3 = Get-RunStart '' $main (Resume)
    $rep = Test-Report $m $r3.Base "Готово.`nНОУТБУК ГОТОВО gemini/probe $c1"
    Check "звіт ГОТОВО без нових комітів прийнято (комітів від основи $($rep.Facts.Ahead))" ($rep.Kind -ceq 'DONE' -and $rep.Accepted)
    $s3 = Attempt 'r3' $r3.Base; $s3.code = 'DONE'; $s3.report = 'DONE'
    Complete-Status $s3 (Get-StatePath (Get-MarkerKey $m)) '' ([datetime]::MinValue)
    $heads = $(if ($s3.bundle) { Fixture-Git $clone @('bundle', 'list-heads', (Join-Path $OutDir $s3.bundle)) } else { '' })
    Check "ПІСЛЯ: кінець — комітів $($s3.ahead), бандл '$($s3.bundle)' з головою C1" ($s3.ahead -eq 1 -and $s3.head -ceq $c1 -and $heads.Contains($c1))
    Check "доставлене прогону містить C1 (копію можна прибрати)" (@(Get-RunDelivered 'r3') -ccontains $c1)

    # Перерваний повтор (STARTED без процесу): основа в стані — бандл теж несе C1.
    $s4 = Attempt 'r4' $r3.Base; $s4.code = ''
    [IO.File]::WriteAllText((Join-Path $script:StateDir 'перерваний.txt'), 'STARTED ' + ($s4 | ConvertTo-Json -Compress))
    Resume-Interrupted
    $j4 = [IO.File]::ReadAllText((Join-Path $OutDir 'r4.json')) | ConvertFrom-Json
    Check "INTERRUPTED повтору: комітів $($j4.ahead), бандл '$($j4.bundle)'" ($j4.code -ceq 'INTERRUPTED' -and $j4.ahead -eq 1 -and $j4.bundle -ceq 'r4.bundle')
} catch { Check "стенд зірвано: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit $(if ($bad) { 1 } else { 0 })
