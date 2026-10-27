# Стенд claude_run.ps1: підвантажує крапкою, підміняє ноутбук (користувач, час увімкнення, задачі, shutdown) і запускає Main.
param([string]$Script, [string]$ArgsJson)
$p = @{}
(ConvertFrom-Json $ArgsJson).PSObject.Properties | ForEach-Object { $p[$_.Name] = $_.Value }
# Стенд не чіпає справжньої спільної теки ноутбука (C:\Users\Public\gemini\lanes): без LaneDir — тимчасова тека.
if ((Get-Command $Script).Parameters.ContainsKey('LaneDir') -and -not $p.ContainsKey('LaneDir')) {
    $p['LaneDir'] = Join-Path ([System.IO.Path]::GetTempPath()) ('lanes-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
}
. $Script @p
# Процес наряду — знов цей стенд (а не сам скрипт), тож бере ті самі підміни, що батьківський (10164).
$script:SideFile = $PSCommandPath; $script:SideScript = $Script; $script:SideArgs = $p
function Get-WorkerCommand([string]$File) {
    $q = @{}
    foreach ($k in $script:SideArgs.Keys) { $q[$k] = $script:SideArgs[$k] }
    $q['WorkerFile'] = $File
    @{ Exe = (Get-Process -Id $PID).Path; Args = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $script:SideFile,
            '-Script', $script:SideScript, '-ArgsJson', ($q | ConvertTo-Json -Compress)) }
}
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
