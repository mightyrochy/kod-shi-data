#Requires -Version 5.1
param([string]$SourceDir = (Join-Path $PSScriptRoot '../../адаптери/gemini'))
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Utf8 = New-Object Text.UTF8Encoding($false)
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'queue_lanes.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Get-Sha256Hex', 'Get-MarkerKey', 'Get-StatePath', 'Get-ClaimPath', 'Get-MarkerState', 'Test-MarkerReady')) {
    $node = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    if (-not $node) { throw "Не знайдено функцію $name" }
    . ([scriptblock]::Create($node.Extent.Text))
}
$script:StateDir = Join-Path $env:TEMP ('no-code-probe-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($script:StateDir)
$marker = [pscustomobject]@{ Ref = 'refs/remotes/origin/gemini-queue/probe/gemini-3.8-flash-high/1/p1'; Sha = ('a' * 40) }
$path = Get-StatePath (Get-MarkerKey $marker)
$failed = 0
function Check([string]$Name, [bool]$Ok) {
    <# Невиконане твердження дає ненульовий код після всіх перевірок. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:failed++ }
}
try {
    Check 'Нова позначка готова до запуску' (Test-MarkerReady (Get-MarkerState $marker))
    [IO.File]::WriteAllText($path, 'DONE synthetic NO_REPORT', $script:Utf8)
    Check 'Після кінцевого NO_REPORT та сама позначка не запускається вже на main' (-not (Test-MarkerReady (Get-MarkerState $marker)))
    [IO.File]::WriteAllText($path, 'DONE synthetic НЕМАЄ_КОДУ', $script:Utf8)
    Check 'Навіть синтетичний кінцевий НЕМАЄ_КОДУ не запускає ту саму позначку' (-not (Test-MarkerReady (Get-MarkerState $marker)))
    [IO.File]::WriteAllText($path, 'WAIT {"until":0,"group":"GEMINIMODELS","retakes":1}', $script:Utf8)
    Check 'Після спливу WAIT квоти та сама позначка знову готова' (Test-MarkerReady (Get-MarkerState $marker))
    [IO.File]::WriteAllText($path, 'WAIT {"until":4102444800,"group":"GEMINIMODELS","retakes":1}', $script:Utf8)
    Check 'До скидання квоти позначка ще чекає' (-not (Test-MarkerReady (Get-MarkerState $marker)))
} finally {
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path }
    Remove-Item -LiteralPath $script:StateDir
}
exit [int]($failed -gt 0)
