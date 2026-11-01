# Стенд: підвантажує обгортку крапкою, підміняє перевірки Windows (ізоляція, користувач) і запускає Main.
param([string]$Script, [string]$ArgsJson)
# UTF-8 із BOM у стандартному stdin .NET Framework, як у раннера Windows.
if ($env:OS -eq 'Windows_NT') { [Console]::InputEncoding = [Text.Encoding]::UTF8 }
$p = @{}
(ConvertFrom-Json $ArgsJson).PSObject.Properties | ForEach-Object { $p[$_.Name] = $_.Value }
# Розмір профілю у синтетичному прогоні не потребує обходу справжнього профілю ноутбука.
if ((Get-Command $Script).Parameters.ContainsKey('ProfileDir') -and -not $p.ContainsKey('ProfileDir')) {
    $p['ProfileDir'] = Join-Path ([System.IO.Path]::GetTempPath()) ('profile-' + [guid]::NewGuid().ToString('N'))
}
# Стенд не чіпає справжньої спільної теки ноутбука (C:\Users\Public\gemini\lanes): без LaneDir — тимчасова тека.
if ((Get-Command $Script).Parameters.ContainsKey('LaneDir') -and -not $p.ContainsKey('LaneDir')) {
    $p['LaneDir'] = Join-Path ([System.IO.Path]::GetTempPath()) ('lanes-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
}
# Наявний selfupdate.ready робочої обгортки не є входом синтетичного стенда.
if ((Get-Command $Script).Parameters.ContainsKey('UpdateRoot') -and -not $p.ContainsKey('UpdateRoot')) {
    $p['UpdateRoot'] = Join-Path ([System.IO.Path]::GetTempPath()) ('update-' + [guid]::NewGuid().ToString('N'))
}
if ((Get-Command $Script).Parameters.ContainsKey('GeminiRunsDir') -and -not $p.ContainsKey('GeminiRunsDir')) {
    $p['GeminiRunsDir'] = Join-Path ([System.IO.Path]::GetTempPath()) ('gemini-runs-' + [guid]::NewGuid().ToString('N'))
}
# Файл, що не завантажився, — провал стенда з причиною: без Main PowerShell знайшов би main.cpl (PATHEXT має .CPL)
# і відкрив "Миша – властивості" поверх вікон власника (29.10, 20 разів за 2 хв).
try { . $Script @p } catch { [Console]::Error.WriteLine("СТЕНД: $Script не завантажився: $($_.Exception.Message)"); exit 2 }
if (-not (Get-Command Main -CommandType Function -ErrorAction SilentlyContinue)) { [Console]::Error.WriteLine("СТЕНД: $Script не визначив Main"); exit 2 }
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
# Політику пробудження окремо перевіряє сценарії_менше_прогонів.ps1.
if ((Split-Path -Leaf $Script) -eq 'gemini_publish.ps1') {
    function Test-DispatcherAction([string]$Line) { $true }
}
function Test-ExternalGpuFree { $true }
# Планувальник читає той самий вхід напряму через Get-GpuBusyReason.
function Get-GpuTelemetry { <# Ізольована карта синтетичного планувальника. #> [pscustomobject]@{ Error = ''; TotalMiB = 16376; FreeMiB = 16376; Percent = 0 } }
# Лічильник відеопам'яті процесів — справжній на ноутбуці: стенд не бачить карти (його міряє сценарії_gpu_процеси.ps1).
function Get-GpuCounterRows { $null }
exit (Main)
