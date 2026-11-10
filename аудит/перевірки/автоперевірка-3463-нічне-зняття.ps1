#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('review3463-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
# Імпорт не запускає Main; усі залежності, які можуть звернутися до зовнішнього стану, підмінено.
. (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir $tmp -OutDir "$tmp/out" -LaneDir "$tmp/lanes"
$script:NightReader = ${function:Get-NightlyMarker}
$script:ReviewNow = [datetime]'2026-11-11T03:00:00Z'
$script:ReviewSha = 'a' * 40
$script:ReviewCancelled = $false
$script:ReviewClosed = 0
function Get-RefSha([string]$Ref) { if ($Ref -eq 'refs/remotes/origin/main') { 'a' * 40 } else { $script:ReviewSha } }
function Invoke-Git($ArgList, [switch]$AllowFail) {
    $code = 0; $out = ''
    if ($ArgList[0] -eq 'merge-base' -and $script:ReviewCancelled) { $code = 1 }
    [pscustomobject]@{Code=$code; Out=$out; Err=''}
}
function Repair-GpuModels { }
function Save-Skips($Path) { }
function Get-NightlyMarker { & $script:NightReader $script:ReviewNow }
function Get-Markers {
    ConvertTo-Marker ($script:QueuePrefix + 'Е1-нічний-живий-20261111/gpt-6.1-sol-high/1/gpu-p8' + "`t" + $script:ReviewSha + "`t1794366000`tЗНЯТО: проба перевірки")
}
function Close-CancelledMarker($M, $Workers) { $script:ReviewClosed++ }
$before = @(Get-NightlyMarker)
if ($before.Count -ne 1) { throw 'Початкову нічну позначку не прочитано' }
$script:ReviewCancelled = $true
$script:ReviewSha = 'b' * 40
$cancelled = @(Get-Markers)
$nightly = @(Get-NightlyMarker)
$started = Start-Markers @([pscustomobject]@{Marker=$cancelled[0].Name; Slug=$cancelled[0].Slug; Proc=[pscustomobject]@{HasExited=$false}})
"ДО ЗНЯТО: нічних позначок $($before.Count)"
"ПІСЛЯ ЗНЯТО: спільний читач $($cancelled.Count), Cancel=$($cancelled[0].Cancel); нічний читач $($nightly.Count)"
"Планувальник: нових прогонів $started; викликів Close-CancelledMarker $script:ReviewClosed"
if ($cancelled.Count -eq 1 -and $cancelled[0].Cancel -and $nightly.Count -eq 0 -and $script:ReviewClosed -eq 0) {
    'ВІДТВОРЕНО: нічне ЗНЯТО не доходить до обробника скасування'
    exit 0
}
throw 'Заявлений механізм не відтворився'
