#Requires -Version 5.1
<# Справжні рішення модуля й транспорт причини; підмінено лише драйвер, WMI та замок.
Числа сценаріїв — фікстури, а 8925 MiB і 0 % виробничого бюджету звірено з паспортом виміру. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
. (Join-Path $SourceDir 'queue_lanes.ps1')
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Друкує мірило й накопичує всі провали до завершення стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
$LaneDir = [IO.Path]::GetTempPath()
$script:LockFree = $true
function Test-LockFree { $script:LockFree }
$script:Free = 14455; $script:Percent = 0; $script:SmiCode = 0; $script:SmiOut = $null
$script:NoSmi = $false; $script:NoCounter = $false; $script:Rows = @(); $script:Calls = @()
function Get-Command {
    if (-not $script:NoSmi) { [pscustomobject]@{ Source = 'nvidia-smi' } }
}
function Invoke-Native { param($Exe, $Arguments)
    $script:Calls += "$Exe $($Arguments -join ' ')"
    $out = "16376, $script:Free, $script:Percent"
    if ($null -ne $script:SmiOut) { $out = $script:SmiOut }
    # Старі запити також відповідають тій самій фікстурі: ДО/ПІСЛЯ змінює лише виробничий модуль.
    if ($Arguments -contains '--query-gpu=memory.used') { $out = [string](16376 - $script:Free) }
    if ($Arguments -contains '--query-compute-apps=pid,process_name') { $out = '4120, C:\chrome.exe' }
    [pscustomobject]@{ Code = $script:SmiCode; Out = $out }
}
function Get-GpuCounterRows {
    if ($script:NoCounter) { return $null }
    , @($script:Rows)
}
function Get-GpuProcessInfo([int]$ProcessId) {
    $name = $(if ($ProcessId -eq 7000) { 'LM Studio' } elseif ($ProcessId -eq 5100) { 'dwm' } else { 'chrome' })
    [pscustomobject]@{ Name = $name; Path = ''; Label = "$name.exe" }
}
function Row([int]$Id, [long]$MiB) {
    <# Лічильник повертає байти, а не MiB. #>
    [pscustomobject]@{ Name = "pid_${Id}_luid_0x0_0x1_phys_0"; DedicatedUsage = $MiB * 1MB }
}
function State([string]$Name, [bool]$Expected, [string]$Reason = '') {
    <# Планувальник і воркер мають однакове рішення, причина доходить до публікатора. #>
    $why = Get-GpuBusyReason @()
    $free = Test-ExternalGpuFree
    Check "$Name — вільна=$free; причина=«$why»" (($why -eq '') -eq $Expected -and $free -eq $Expected)
    if ($Reason) {
        Check "$Name — причина називає ресурс" ($why -match $Reason)
        $line = "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: $script:GpuHoldReason, позначок 3"
        Check "$Name — причина проходить транспорт" (Test-HoldLine $line)
    }
}

$script:Rows = @((Row 5100 1221), (Row 4120 700))
State 'стіл 1221 MiB + браузер 700 MiB, 0 %' $true
$script:NoCounter = $true
State 'той самий браузер без WMI' $true
$script:NoCounter = $false
$script:Percent = 74; $script:Free = 9000; $script:Rows = @((Row 4120 7376))
State 'гра з гігабайтами та обчисленнями' $false 'навантаження 74 %'
$script:Rows = @((Row 5100 7376))
State 'обчислення не приховає назва робочого столу' $false 'навантаження 74 %'
$script:Percent = 0; $script:Free = 2000; $script:Rows = @((Row 4120 14376))
State 'чужа неактивна модель не лишила памʼяті' $false 'вільно 2000 з потрібних 8925 MiB'
$script:Free = 8925; $script:Rows = @()
State 'рівність вільної памʼяті бюджету' $true
$script:Free = 8924
State 'на 1 MiB менше бюджету' $false 'вільно 8924 з потрібних 8925 MiB'
$script:Free = 14455; $script:Percent = 1
State 'немає довільного дозволеного ненульового навантаження' $false 'навантаження 1 %'
$script:Percent = 0; $script:Free = 5000; $script:Rows = @((Row 7000 9000))
State 'неактивна модель інструмента вже на карті' $true
$script:Rows = @((Row 7000 4000))
State 'модель зменшує лише залишкову потребу' $true
$script:Free = 4924
State 'бракує памʼяті навіть із моделлю інструмента' $false 'вільно 4924 з потрібних 4925 MiB'
$script:Rows = @((Row 7000 4000), (Row 7000 4000))
State 'дубль лічильника не подвоює зарахування' $false 'вільно 4924 з потрібних 4925 MiB'
$script:Free = 5000; $script:Rows = @((Row 7000 9000)); $script:Percent = 69
State 'активна LM Studio також лишає наряд у черзі' $false 'навантаження 69 %'
$script:Percent = 0; $script:NoCounter = $true
State 'без WMI памʼять моделі не вважається вільною' $false 'вільно 5000 з потрібних 8925 MiB'
$script:NoCounter = $false; $script:Rows = @(); $script:Free = 14455
foreach ($out in @('16376, N/A, 0', '16376, 17000, 0', '16376, 14000, 101', '0, 0, 0', '', '99999999999999999999, 1, 0')) {
    $script:SmiOut = $out
    State "невалідна телеметрія [$out]" $false 'nvidia-smi'
}
$script:SmiOut = "16376, 9000, 0`n16376, 9000, 0"
State 'памʼять двох карт не складається' $false 'кілька GPU'
$script:SmiOut = $null; $script:SmiCode = 1
State 'драйвер не відповів' $false 'nvidia-smi'
$script:SmiCode = 0; $script:NoSmi = $true
State 'драйвера немає' $false 'nvidia-smi'
$script:NoSmi = $false; $script:LockFree = $false
Check 'між обліковими записами лишається замок GPU' ((Get-GpuBusyReason @()) -match 'замок')
$script:LockFree = $true
$worker = @([pscustomobject]@{ Gpu = $true; Proc = [pscustomobject]@{ HasExited = $false } })
Check 'власний GPU-наряд утримує карту' ((Get-GpuBusyReason $worker) -match 'власний наряд')
foreach ($reason in @('навантаження 101 %', 'навантаження -1 %', "вільно 1 з потрібних 2 MiB`nкоманда", 'вільно N/A з потрібних 8925 MiB')) {
    Check "транспорт відкидає довільний текст [$reason]" (-not (Test-HoldLine "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU: $reason, позначок 1"))
}
Check 'обгортка не викликала lms' (@($script:Calls | Where-Object { $_ -notlike 'nvidia-smi *' }).Count -eq 0)
if ($bad) { exit 1 }
exit 0
