#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir, [Parameter(Mandatory=$true)][string]$Template)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
# Доповнює синтетичний стенд PR; Get-ChainBranchWork, Invoke-WrapperChain і
# Write-Heartbeat беруться з перевірюваного дерева без змін їхньої реалізації.
$extra = @'
    $tokens = $null; $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'gemini_run.ps1'), [ref]$tokens, [ref]$errors)
    $heartbeat = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Write-Heartbeat' }, $true)
    Invoke-Expression $heartbeat.Extent.Text
    function Get-UtcStamp($Date) { $Date.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
    foreach ($lane in @('codex', 'agy')) {
        $activeHead = $(if ($lane -ceq 'codex') { '1'*40 } else { '3'*40 })
        $completedHead = $(if ($lane -ceq 'codex') { '2'*40 } else { '4'*40 })
        $slots = Join-Path $tmp 'gemini-runs/slots'
        [void][IO.Directory]::CreateDirectory($slots)
        $slotPath = Join-Path $slots "$lane-1.lock"
        $activeMarker = "gemini-queue/ізоляція-$lane/gpt-test/1/p1"
        Write-FileAtomic (Join-Path $slots "$lane-1.json") ((@{slot="$lane-1";lane=$lane;slug="ізоляція-$lane";marker=$activeMarker}) | ConvertTo-Json)
        $activeLock = [IO.File]::Open($slotPath, 'OpenOrCreate', 'ReadWrite', 'None')
        try {
            # Main на помилці ізоляції викликає цю справжню функцію,
            # не зупиняючи вже запущеного worker із зайнятим замком.
            Write-Heartbeat 'TEST_ISOLATION'
            $hb = ConvertFrom-Json ([IO.File]::ReadAllText("$OutDir/heartbeat.json"))
            Check "${lane}: heartbeat ізоляції не має lanes" ($null -eq $hb.PSObject.Properties['lanes'])
            $busy = $false
            try { $probe = [IO.File]::Open($slotPath, 'Open', 'ReadWrite', 'None'); $probe.Dispose() } catch [IO.IOException] { $busy = $true }
            Check "${lane}: справжній замок слота досі зайнятий" $busy
            $beforeCount = CountReviews 2386
            Tick $activeHead "gemini/ізоляція-$lane"
            $added = (CountReviews 2386) - $beforeCount
            Check "${lane}: перевірок активної голови $added, інваріант вимагає 0" ($added -eq 0)
        } finally { $activeLock.Dispose() }

        $completedMarker = "gemini-queue/завершений-$lane/gpt-test/1/p1"
        Write-FileAtomic (Join-Path $slots "$lane-1.json") ((@{slot="$lane-1";lane=$lane;slug="завершений-$lane";marker=$completedMarker}) | ConvertTo-Json)
        $activeLock = [IO.File]::Open($slotPath, 'Open', 'ReadWrite', 'None')
        Write-FileAtomic "$OutDir/heartbeat.json" ((@{lanes=@(@{lane=$lane;busy=@(@{slot="$lane-1";marker=$completedMarker})})}) | ConvertTo-Json -Depth 6)
        $activeLock.Dispose()
        Write-FileAtomic "$WorkDir/state/completed-$lane.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/завершений-$lane $completedHead МОДЕЛЬ gpt-test"}) | ConvertTo-Json)
        $probe = [IO.File]::Open($slotPath, 'Open', 'ReadWrite', 'None'); $probe.Dispose()
        $beforeCount = CountReviews 2386
        Tick $completedHead "gemini/завершений-$lane"
        $added = (CountReviews 2386) - $beforeCount
        Check "${lane}: після ГОТОВО і звільнення слота перевірок $added, інваріант вимагає 1" ($added -eq 1)
    }
'@
$original = [IO.File]::ReadAllText($Template)
$anchor = '} finally {'
if (($original.Split(@($anchor), [StringSplitOptions]::None)).Count -ne 2) { throw 'Змінена структура стенда: очікується один finally' }
$probePath = Join-Path ([IO.Path]::GetTempPath()) ('review2423-heartbeat-' + [guid]::NewGuid().ToString('N') + '.ps1')
try {
    [IO.File]::WriteAllText($probePath, $original.Replace($anchor, $extra + "`n" + $anchor), (New-Object Text.UTF8Encoding($true)))
    & powershell -NoProfile -ExecutionPolicy Bypass -File $probePath -SourceDir $SourceDir
    $result = $LASTEXITCODE
} finally { Remove-Item -LiteralPath $probePath -Force }
exit $result
