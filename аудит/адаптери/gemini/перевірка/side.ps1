# Стенд: підвантажує обгортку крапкою, підміняє перевірки Windows (ізоляція, користувач) і запускає Main.
param([string]$Script, [string]$ArgsJson)
# UTF-8 із BOM у стандартному stdin .NET Framework, як у раннера Windows.
if ($env:OS -eq 'Windows_NT') { [Console]::InputEncoding = [Text.Encoding]::UTF8 }
$p = @{}
(ConvertFrom-Json $ArgsJson).PSObject.Properties | ForEach-Object { $p[$_.Name] = $_.Value }
# Стенд не чіпає справжньої спільної теки ноутбука (C:\Users\Public\gemini\lanes): без LaneDir — тимчасова тека.
if ((Get-Command $Script).Parameters.ContainsKey('LaneDir') -and -not $p.ContainsKey('LaneDir')) {
    $p['LaneDir'] = Join-Path ([System.IO.Path]::GetTempPath()) ('lanes-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
}
# Наявний selfupdate.ready робочої обгортки не є входом синтетичного стенда.
if ((Get-Command $Script).Parameters.ContainsKey('UpdateRoot') -and -not $p.ContainsKey('UpdateRoot')) {
    $p['UpdateRoot'] = Join-Path ([System.IO.Path]::GetTempPath()) ('update-' + [guid]::NewGuid().ToString('N'))
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
function Test-Isolation { [string]$env:FAKE_ISOLATION }
function Test-OwnerUser { $true }
exit (Main)
