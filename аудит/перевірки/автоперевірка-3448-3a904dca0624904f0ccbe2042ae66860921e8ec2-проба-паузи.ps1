param([string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
. (Join-Path $SourceDir 'queue_lanes.ps1')
function Write-Log([string]$Text) { Write-Output $Text }
function Invoke-HealthBeat { }
function Get-Limit { 0.0333333333333333 }
$script:Battery = @($true, $true, $false)
function Test-OnBattery {
    $value = $script:Battery[0]
    if ($script:Battery.Count -gt 1) { $script:Battery = $script:Battery[1..($script:Battery.Count - 1)] }
    $value
}
$probeDir = Join-Path $env:TEMP 'native-pause3448'
[void][IO.Directory]::CreateDirectory($probeDir)
$outFile = Join-Path $probeDir 'ticks.txt'
$childFile = Join-Path $probeDir 'child.ps1'
$childText = @'
param([string]$OutFile)
while ($true) {
    [IO.File]::AppendAllText($OutFile, "tick`n")
    Start-Sleep -Milliseconds 100
}
'@
[IO.File]::WriteAllText($childFile, $childText, $script:Utf8)
if (Test-Path -LiteralPath $outFile) { Remove-Item -LiteralPath $outFile }
$proc = Start-Tree (New-StartInfo "$PSHOME/powershell.exe" @('-NoProfile','-ExecutionPolicy','Bypass','-File',$childFile,'-OutFile',$outFile))
$check = $null
try {
    $ready = [Diagnostics.Stopwatch]::StartNew()
    while (-not (Test-Path -LiteralPath $outFile)) {
        if ($ready.Elapsed.TotalSeconds -gt 10) { throw 'тестовий процес не стартував' }
        Start-Sleep -Milliseconds 20
    }
    Add-PowerType
    $beforeRows = [IO.File]::ReadAllLines($outFile).Count
    $before = Get-AwakeTime
    $wall = [Diagnostics.Stopwatch]::StartNew()
    Wait-PowerPause
    $awake = ((Get-AwakeTime) - $before).TotalSeconds
    $afterRows = [IO.File]::ReadAllLines($outFile).Count
    Start-Sleep -Milliseconds 450
    $resumedRows = [IO.File]::ReadAllLines($outFile).Count
    $check = [ordered]@{ rows_before=$beforeRows; rows_after=$afterRows; rows_resumed=$resumedRows; wall_seconds=[math]::Round($wall.Elapsed.TotalSeconds,3); awake_seconds=[math]::Round($awake,3); paused_seconds=[math]::Round($script:PausedTotal.TotalSeconds,3); ok=($beforeRows -eq $afterRows -and $resumedRows -gt $afterRows -and $awake -lt 0.2) }
} finally { Stop-Tree $proc }
$check | ConvertTo-Json -Compress
if (-not $check.ok) { exit 1 }
