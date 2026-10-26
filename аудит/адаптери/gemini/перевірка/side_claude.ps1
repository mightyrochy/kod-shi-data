# Стенд claude_run.ps1: підвантажує крапкою, підміняє ноутбук (користувач, час увімкнення, задачі, shutdown) і запускає Main.
param([string]$Script, [string]$ArgsJson)
$p = @{}
(ConvertFrom-Json $ArgsJson).PSObject.Properties | ForEach-Object { $p[$_.Name] = $_.Value }
. $Script @p
function Test-OwnerUser { $true }
function Get-BootStamp { [string]$env:FAKE_BOOT }
function Invoke-Shutdown { [System.IO.File]::WriteAllText((Join-Path $WorkDir 'shutdown.txt'), (Get-Date).ToString('s')) }
function Get-TaskRows {
    foreach ($n in $TaskNames) {
        $st = $(if ($n -eq 'gemini-run' -and $env:FAKE_GEMINI_STATE) { $env:FAKE_GEMINI_STATE } else { 'Ready' })
        [pscustomobject]@{ Name = $n; Last = '2026-10-26T10:00:00Z'; Result = '0x0'; State = $st }
    }
}
exit (Main)
