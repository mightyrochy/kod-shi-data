#Requires -Version 5.1
<#
.SYNOPSIS
CI на тілі PR: кожен рядок `ЖИВИЙ ПІСЛЯ` або розбирається повністю, або це вада (код виходу 1, перелік рядків із причиною).

.DESCRIPTION
Розбір — ті самі `Get-LiveSceneRegistry` і `Get-LiveAfterLines`, що в планувальнику (`queue_lanes.ps1`), і реєстр
`аудит/проби/живі_сцени.txt` свіжого дерева. Тіло PR — дані зі змінної середовища PR_BODY: у команду оболонки
воно не підставляється й не виконується; з `queue_lanes.ps1` береться лише текст двох функцій (без побічних дій
файла, що підвантажується крапкою). Тіла нема чи нема рядка `ЖИВИЙ ПІСЛЯ` — зелений.
#>
param([Parameter(Mandatory=$true)][string]$Root)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$source = Join-Path $Root 'аудит/адаптери/gemini/queue_lanes.ps1'
$errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($source, [ref]$null, [ref]$errors)
if ($errors -and $errors.Count) { Write-Host "✗ queue_lanes.ps1 не розбирається: $($errors[0].Message)"; exit 1 }
$names = @('Get-LiveSceneRegistry', 'Get-LiveAfterLines')
$found = @($ast.FindAll({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $names -ccontains $n.Name }, $true))
if ($found.Count -ne $names.Count) { Write-Host '✗ у queue_lanes.ps1 нема функцій розбору рядка ЖИВИЙ ПІСЛЯ'; exit 1 }
foreach ($function in $found) { . ([scriptblock]::Create($function.Extent.Text)) }
$registry = Get-LiveSceneRegistry ([IO.File]::ReadAllText((Join-Path $Root 'аудит/проби/живі_сцени.txt'), $utf))
if (-not $registry.Count) { Write-Host '✗ реєстр живі_сцени.txt порожній'; exit 1 }
$body = [string]$env:PR_BODY
$items = @(Get-LiveAfterLines $body $registry)
$bad = @($items | Where-Object { $_.error })
Write-Host "Рядків ЖИВИЙ ПІСЛЯ у тілі PR: $($items.Count); вадних: $($bad.Count)"
foreach ($item in $items) {
    if ($item.error) { Write-Host "  ✗ вада: $($item.error)`n    рядок: $($item.line)" }
    else { Write-Host "  ✓ $($item.id) ($($item.mode))" }
}
if ($bad.Count) {
    Write-Host 'Виправ рядок за форматом: ЖИВИЙ ПІСЛЯ: <id> — <питання правки> → <режим> → <ДО звідки> → <що вважати кращим>; id — голий, перше поле аудит/проби/живі_сцени.txt; одна сцена — один рядок.'
    exit 1
}
exit 0
