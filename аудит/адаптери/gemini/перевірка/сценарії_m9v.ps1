#Requires -Version 5.1
# Читачі самооновлення в кроках m9v (запускає сценарії_m9v.sh): скрипти кроків 1 і 2 торкаються ProgramData, задач і
# профілю власника, тож тут перевіряються спільні функції читач.ps1 на тимчасових теках і розташування їхніх викликів
# у кроках (AST); справжні кроки на стенді не виконуються.
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$m9v = Join-Path $SourceDir 'm9v'
. (Join-Path $m9v 'читач.ps1')
$utf = New-Object Text.UTF8Encoding($false)
$sha = 'a' * 40
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('m9v-reader-' + [guid]::NewGuid().ToString('N'))
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Один результат стенда; провал робить запуск червоним. #>
    if ($Ok) { "ok  $Name" } else { "ПОМИЛКА $Name"; $script:failures++ }
}
function New-Root([string]$Name, [bool]$Ready, [string]$Pointer, [string[]]$Files) {
    <# Корінь оновлення: selfupdate.ready, active.txt і версія з файлами входів, що друкують свої ключі й виходять з 7. #>
    $root = Join-Path $tmp $Name
    $dir = Join-Path (Join-Path $root 'versions') $sha
    [void][IO.Directory]::CreateDirectory($dir)
    if ($Ready) { [IO.File]::WriteAllText((Join-Path $root 'selfupdate.ready'), '1', $utf) }
    if ($Pointer) { [IO.File]::WriteAllText((Join-Path $root 'active.txt'), $Pointer, $utf) }
    foreach ($f in $Files) { [IO.File]::WriteAllText((Join-Path $dir $f), "param([switch]`$DryRun, [switch]`$Light)`nWrite-Output (`"DRYRUN=`$DryRun LIGHT=`$Light`")`nexit 7`n", $utf) }
    $root
}
$all = @('gemini_run.ps1', 'gemini_publish.ps1', 'gemini_watch.ps1', 'claude_run.ps1')
function Parse-Errors([string]$Text) {
    <# Кількість помилок розбору тексту. #>
    $e = $null; $t = $null
    [void][Management.Automation.Language.Parser]::ParseInput($Text, [ref]$t, [ref]$e)
    $e.Count
}
try {
    # без selfupdate.ready (перша установка): мовчки $false, кроки лишаються при повних файлах
    $r = New-Root 'перша' $false $sha $all
    $out = @(Test-SelfUpdate $r 6>&1)
    Check 'без selfupdate.ready: $false без попередження' ($out.Count -eq 1 -and $out[0] -eq $false)

    # з selfupdate.ready, указівником і файлами всіх входів
    $r = New-Root 'встановлено' $true $sha $all
    $out = @(Test-SelfUpdate $r 6>&1)
    Check 'selfupdate.ready + active.txt + усі входи у версії: $true' ($out.Count -eq 1 -and $out[0] -eq $true)

    # битий стан: читач упав би — функція каже $false з попередженням, повні файли лишаються
    foreach ($case in @(
        @('кривий указівник', (New-Root 'крив' $true 'кривий' $all)),
        @('указівник із ..', (New-Root 'обхід' $true '..\..\..' $all)),
        @('версія без claude_run.ps1', (New-Root 'без_входу' $true $sha @('gemini_run.ps1', 'gemini_publish.ps1', 'gemini_watch.ps1'))))) {
        $out = @(Test-SelfUpdate $case[1] 6>&1)
        Check "битий стан ($($case[0])): `$false і попередження" ($out[-1] -eq $false -and $out.Count -eq 2 -and "$($out[0])" -match 'УВАГА')
    }
    $r = New-Root 'без_указівника' $true '' $all
    Check 'selfupdate.ready без active.txt: $false' (@(Test-SelfUpdate $r 6>&1)[-1] -eq $false)

    # читач: перша заміна зберігає повний файл, повтор нічого не міняє, потім читач запускає файл версії з аргументами
    $r = New-Root 'читач' $true $sha $all
    $entry = Join-Path $tmp 'профіль\claude-run'
    [void][IO.Directory]::CreateDirectory($entry)
    $file = Join-Path $entry 'claude_run.ps1'
    [IO.File]::WriteAllText($file, "# повний файл 1`n", $utf)
    Install-EntryReader $entry 'claude_run.ps1' $r
    Check 'читач стоїть на місці входу' ([IO.File]::ReadAllText($file) -ceq (Get-ReaderText $r 'claude_run.ps1'))
    Check 'попередній файл збережено як .before-update' ([IO.File]::ReadAllText($file + '.before-update') -ceq "# повний файл 1`n")
    [IO.File]::WriteAllText($file, "# повний файл 2`n", $utf)
    Install-EntryReader $entry 'claude_run.ps1' $r
    Check 'повторна заміна не затирає перший .before-update' ([IO.File]::ReadAllText($file + '.before-update') -ceq "# повний файл 1`n")
    $before = [IO.File]::GetLastWriteTimeUtc($file)
    Start-Sleep -Milliseconds 50
    Install-EntryReader $entry 'claude_run.ps1' $r
    Check 'читач, що вже стоїть, не переписується' ([IO.File]::GetLastWriteTimeUtc($file) -eq $before)
    $ps = (Get-Process -Id $PID).Path
    $res = & $ps -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $file -Light
    Check 'читач передає аргументи й код виходу версії' ($LASTEXITCODE -eq 7 -and "$res" -ceq 'DRYRUN=False LIGHT=True')
    Check 'текст читача з апострофом у корені розбирається' ((Parse-Errors (Get-ReaderText "C:\o'neil" 'claude_run.ps1')) -eq 0)

    # кроки: входи читачами ставляться лише в гілці $su, до реєстрації задач; повні копії — лише в гілці else
    $e = $null; $t = $null
    $own = [Management.Automation.Language.Parser]::ParseFile((Join-Path $m9v '0_власник.ps1'), [ref]$t, [ref]$e)
    $adm = [Management.Automation.Language.Parser]::ParseFile((Join-Path $m9v '1_адмін.ps1'), [ref]$t, [ref]$e)
    $isSu = { param($a) $a -is [Management.Automation.Language.IfStatementAst] -and $a.Clauses[0].Item1.Extent.Text -ceq '$su' }
    $cmd = { param($ast, $name) @($ast.FindAll({ param($a) $a -is [Management.Automation.Language.CommandAst] -and $a.GetCommandName() -ceq $name }, $true)) }
    $ownSu = @($own.FindAll($isSu, $true))
    $ownInstall = @(& $cmd $own 'Install-EntryReader')
    $ownReg = @(& $cmd $own 'Register-ScheduledTask')
    $inSu = @($ownInstall | Where-Object { $_.Extent.StartOffset -ge $ownSu[-1].Extent.StartOffset -and $_.Extent.EndOffset -le $ownSu[-1].Extent.EndOffset })
    Check 'крок 1: три читачі (publish, watch, claude-run) у гілці $su' ($ownSu.Count -eq 2 -and $inSu.Count -eq 3 -and $ownInstall.Count -eq 3 -and ($ownInstall.Extent.Text -join ' ') -match 'gemini_publish.*gemini_watch.*claude_run')
    Check 'крок 1: читачі стоять до реєстрації задач, задач три (watch, claude-run, claude-light)' ($ownReg.Count -eq 3 -and $ownInstall[-1].Extent.StartOffset -lt $ownReg[0].Extent.StartOffset)
    $firstDownload = @(& $cmd $own 'Invoke-WebRequest')[0]
    Check 'крок 1: теку перекачування підмінено до першого Invoke-WebRequest' ($ownSu[0].Extent.EndOffset -lt $firstDownload.Extent.StartOffset -and $ownSu[0].Extent.Text -match '\$stage')
    $admSu = @($adm.FindAll($isSu, $true))
    $admInstall = @(& $cmd $adm 'Install-EntryReader')
    $admCopy = @(& $cmd $adm 'Copy-Item' | Where-Object { $_.Extent.Text -match 'gemini_run\.ps1' })
    Check 'крок 2: читач gemini_run.ps1 — у гілці $su' ($admSu.Count -eq 1 -and $admInstall.Count -eq 1 -and $admInstall[0].Extent.Text -match 'gemini_run' -and $admInstall[0].Extent.StartOffset -ge $admSu[0].Extent.StartOffset -and $admInstall[0].Extent.EndOffset -le $admSu[0].Clauses[0].Item2.Extent.EndOffset)
    Check 'крок 2: повна копія gemini_run.ps1 — лише в else' ($admCopy.Count -eq 1 -and $null -ne $admSu[0].ElseClause -and $admCopy[0].Extent.StartOffset -ge $admSu[0].ElseClause.Extent.StartOffset -and $admCopy[0].Extent.EndOffset -le $admSu[0].ElseClause.Extent.EndOffset)
    Check 'крок 2: реєстрація задач поза гілкою $su' (@(& $cmd $adm 'Register-ScheduledTask' | Where-Object { $_.Extent.StartOffset -ge $admSu[0].Extent.StartOffset -and $_.Extent.EndOffset -le $admSu[0].Extent.EndOffset }).Count -eq 0)
} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
exit ([int]($failures -gt 0))
