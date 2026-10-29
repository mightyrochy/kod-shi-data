#Requires -Version 5.1
param(
    [Parameter(Mandatory=$true)][string]$SourceDir,
    [Parameter(Mandatory=$true)][string]$BaseDir,
    [Parameter(Mandatory=$true)][string]$EvidenceDir
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
[void][IO.Directory]::CreateDirectory($EvidenceDir)
foreach ($item in @(@('base', $BaseDir), @('head', $SourceDir))) {
    $path = Join-Path $item[1] 'gemini_run.ps1'
    $tokens = $null; $errors = $null
    [void][Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
    "$($item[0]) parser_errors=$(@($errors).Count) bytes=$([BitConverter]::ToString([IO.File]::ReadAllBytes($path)[0..8]))"
}

# Підвантажуємо визначення функцій; Main, процеси агентів і GitHub не запускаються.
. (Join-Path $SourceDir 'queue_lanes.ps1')
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'claude_run.ps1'), [ref]$tokens, [ref]$errors)
if (@($errors).Count) { throw 'Не вдалося розібрати claude_run.ps1' }
foreach ($name in @('Start-Markers', 'Read-NoteRows')) {
    $node = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    if ($null -eq $node) { throw "Нема функції $name" }
    . ([scriptblock]::Create($node.Extent.Text))
}
$WorkDir = Join-Path $EvidenceDir 'skip-probe'
[void][IO.Directory]::CreateDirectory($WorkDir)
$script:Markers = @(1..3 | ForEach-Object {
    [pscustomobject]@{ Valid=$true; Lane='claude'; Off=$false
        Time=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Gpu=$true; Slug="task$_"
        Name="gemini-queue/task$_/cc-model/1/gpu" }
})
$script:Limits = @{ slots=@{claude=1}; claude_laptop=@() }
$MarkerMaxAgeDays = 7
function Get-Markers { $script:Markers }
function Add-ClaudeFields($m) { $m }
function Get-OrderedMarkers($m) { $m }
function Get-MarkerState($m) { [pscustomobject]@{Kind='NEW'} }
function Test-MarkerReady($state) { $true }
function Get-FreeSlot { $null }
function Write-Log([string]$Text) { }
[void](Start-Markers @())
$skipPath = Join-Path $WorkDir 'skipped.json'
$rows = @([IO.File]::ReadAllText($skipPath) | ConvertFrom-Json)
"ready_markers=$($script:Markers.Count) skipped_rows=$($rows.Count)"
foreach ($row in $rows) { "saved=$($row.marker) why=$($row.why)" }
$read = @(Read-NoteRows $skipPath @('marker','since','why'))
'Read-NoteRows_actual=' + (ConvertTo-Json -InputObject $read -Compress -Depth 5)
Add-Note (Join-Path $WorkDir 'blocked-reasons.json') 'gemini/task' 'ЗАБЛОКОВАНО: причина'
$blocked = @(Read-NoteRows (Join-Path $WorkDir 'blocked-reasons.json') @('utc','marker','text'))
'Read-NoteRows_blocked=' + (ConvertTo-Json -InputObject $blocked -Compress -Depth 5)
