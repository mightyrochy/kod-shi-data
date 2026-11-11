param([string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path $env:TEMP 'eof3448'
[void][IO.Directory]::CreateDirectory($tmp)
. (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/trusted"
function Write-Log([string]$Text) {}
$script:PowerChecks = 0
$script:PauseCalls = 0
$script:Watch = [Diagnostics.Stopwatch]::StartNew()
function Test-OnBattery {
    $script:PowerChecks++
    $script:Watch.Elapsed.TotalSeconds -ge 0.75
}
function Set-ProcessPause([int]$Id, [bool]$On) {
    $script:PauseCalls++
    throw 'Стенд не має призупиняти реальних процесів'
}
$script:Utf8 = New-Object Text.UTF8Encoding($false)
$child = Join-Path $tmp 'child.py'
[IO.File]::WriteAllText($child, @'
import os, time
time.sleep(0.25)
os.close(1)
time.sleep(2)
'@, $script:Utf8)
$script:Watch.Restart()
$result = Invoke-NativeUntilStall (Get-Command python.exe).Source @($child) $tmp 1 "$tmp/stdout.log" "$tmp/events.tsv"
'код={0}; завислість={1}; секунд={2:N2}; перевірок-живлення={3}; викликів-паузи={4}; батарея-після-0,75-с=True' -f $result.Code,$result.Stalled,$script:Watch.Elapsed.TotalSeconds,$script:PowerChecks,$script:PauseCalls
if ($result.Code -ne 0 -or $script:PauseCalls -ne 0 -or $script:Watch.Elapsed.TotalSeconds -lt 2) { throw 'Неочікуваний результат проби' }
