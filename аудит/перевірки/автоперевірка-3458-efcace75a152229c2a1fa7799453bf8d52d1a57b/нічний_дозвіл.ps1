#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'

# Читає визначення з перевіреної голови; жоден запускач чи процес моделі не виконується.
foreach ($entry in @(
    @{File='queue_lanes.ps1'; Names=@('Get-Lane','ConvertTo-Marker','Get-Markers','Get-NightlyMarker')},
    @{File='claude_run.ps1'; Names=@('Start-Markers')}
)) {
    $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir $entry.File), [ref]$null, [ref]$errors)
    if ($errors.Count) { throw 'Помилка розбору джерела' }
    $names = $entry.Names
    $defs = @($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $names -ccontains $n.Name}, $true))
    if ($defs.Count -ne $names.Count) { throw 'Не всі визначення знайдено' }
    foreach ($def in $defs) { . ([scriptblock]::Create($def.Extent.Text)) }
}

$script:QueuePrefix = 'refs/remotes/origin/gemini-queue/'
$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}\z'
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
$script:CondPattern = '^(?:p[0-9]|d20[0-9]{10}|gpu)(?:-(?:p[0-9]|d20[0-9]{10}|gpu)){0,2}$'
$now = [datetimeoffset]::UtcNow
$date = $now.UtcDateTime.AddDays(-1).ToString('yyyyMMdd')
$ref = $script:QueuePrefix + "Е1-нічний-живий-$date/cc-claude-sonnet-5-5-medium/1/gpu-p8"
$script:Line = $ref + "`t" + ('a' * 40) + "`t" + $now.ToUnixTimeSeconds()

# Зовнішні межі: рядок Git, вільні GPU/слот, готовий стан. Узяття лише рахується і повертає false.
function Invoke-Git([string[]]$Items, [switch]$AllowFail) {
    if ($Items[0] -cne 'for-each-ref') { throw 'Неочікуваний виклик Git' }
    [pscustomobject]@{Code=0; Out=$script:Line}
}
function Get-RefSha([string]$Ref) { '' }
function Repair-GpuModels { }
function Add-ClaudeFields($M) { $M }
function Get-OrderedMarkers($Markers) { $Markers }
function Get-MarkerState($M) { 'NEW' }
function Test-MarkerReady($State) { $true }
function Get-FreeSlot($Lane,$Limit,$Workers) { 1 }
function Test-SlugBusy($Slug,$Lanes) { $false }
function Get-GpuBusyReason { '' }
function New-Id { 'проба' }
function Save-Skips($Path) { }
function Add-Skip($M,$Why) { throw "Неочікуваний пропуск: $Why" }
function New-Claim($M,$Id) { $script:Claims++; $false }
$script:Claims = 0
$script:Limits = @{slots=@{claude=1}; claude_laptop=@()}
$MarkerMaxAgeDays = 7
$WorkDir = [IO.Path]::GetTempPath()
$workers = New-Object System.Collections.ArrayList

$marker = @(Get-Markers)[0]
if (-not $marker.Valid -or $marker.Lane -cne 'claude' -or -not $marker.Gpu) { throw 'Позначка невалідна' }
$early = @(Get-NightlyMarker ([datetime]'2026-11-11T01:00:00Z')).Count
$expired = @(Get-NightlyMarker $now.UtcDateTime.AddDays(1).Date.AddHours(3)).Count
$result = @(Start-Markers $workers)
"UTC: $($now.ToString('o'))"
"Позначка попередньої доби: $($marker.Name)"
"Get-NightlyMarker до 02:00: $early"
"Get-NightlyMarker без дозволу наступної доби: $expired"
"Start-Markers Claude: спроб узяття простроченого дозволу $script:Claims"
"Процесів моделі запущено: $($workers.Count)"
if ($early -ne 0 -or $expired -ne 0 -or $script:Claims -ne 1 -or $workers.Count -ne 0) { throw 'Очікувану ваду не відтворено' }
'ВАДУ ВІДТВОРЕНО: смуга Claude намагається взяти дозвіл попередньої UTC-доби.'
