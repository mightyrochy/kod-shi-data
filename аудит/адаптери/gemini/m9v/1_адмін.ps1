#Requires -Version 5.1
<#
.SYNOPSIS
М.9-В, підготовка, частина адміністратора: кроки 3 і 5 НАЛАШТУВАННЯ.md. Запуск — «PowerShell від імені адміністратора».

.DESCRIPTION
Крок 3: тека C:\ProgramData\gemini-wrapper (gemini лише читає) з gemini_run.ps1 і queue_lanes.ps1. Крок 5: право
«вхід як пакетне завдання» для gemini і задачі gemini-run (під gemini, раз на 5 хв, без межі часу) та gemini-publish
(під власником). Ідемпотентний.
Пароль gemini — лише через Get-Credential (системне вікно); скрипт його не читає в змінну для виводу й не пише.
Попередні умови: 0_власник.ps1 пройдено; gemini має пароль (той, що вже стоїть у задачі gemini-run; без пароля — Ctrl+Alt+Del у сеансі gemini).
Команди кроків — дослівно з НАЛАШТУВАННЯ.md.
З -EnableCodex задача gemini-run дістає ключ `-EnableCodex` в аргументах (рушій Codex ввімкнено; рішення власника 25.10, 9738);
без ключа — аргументи, як були, Codex не кличеться. Повторний запуск з іншим значенням перереєстровує задачу (-Force).
#>
param([switch]$EnableCodex)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
function Stop-Here([string]$m) { Write-Host "СТОП: $m" -ForegroundColor Red; Write-Host 'Напиши диспетчерові: ЗАБЛОКОВАНО + цей текст.'; exit 1 }
function Step([string]$m) { Write-Host "`n== $m" -ForegroundColor Cyan }

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Stop-Here 'потрібен PowerShell від імені адміністратора (Пуск → PowerShell → правий клік → «Запуск від імені адміністратора» → Так).' }
if ($env:USERNAME -eq 'gemini') { Stop-Here 'це вікно відкрито під gemini; відкрий від свого облікового запису.' }
if (-not (Get-LocalUser -Name gemini -ErrorAction SilentlyContinue)) { Stop-Here 'користувача gemini нема на цьому ноутбуці (ізоляція 19.10).' }

# файли з 0_власник.ps1 і їхні хеші (ProgramData отримує саме перевірену копію)
$expected = Import-PowerShellDataFile (Join-Path $here 'хеші.psd1')
$pubFile = "$env:USERPROFILE\gemini-publish\gemini_publish.ps1"
foreach ($f in @(@('gemini_run.ps1', "$env:TEMP\gemini_run.ps1"), @('queue_lanes.ps1', "$env:TEMP\queue_lanes.ps1"), @('gemini_publish.ps1', $pubFile))) {
    if (-not (Test-Path $f[1])) { Stop-Here "нема $($f[1]): спершу 0_власник.ps1 (у цьому ж обліковому записі, не іншим адміністратором)." }
}

Step 'Крок 3: тека обгортки gemini лише для читання'
$run = 'C:\ProgramData\gemini-wrapper'
New-Item -ItemType Directory -Force $run | Out-Null
icacls $run /inheritance:r /grant:r "*S-1-5-18:(OI)(CI)F" "*S-1-5-32-544:(OI)(CI)F" "${env:USERNAME}:(OI)(CI)F" "gemini:(OI)(CI)RX"
if ($LASTEXITCODE -ne 0) { Stop-Here "icacls повернув код $LASTEXITCODE." }
# Звірка без вікна підміни (9742): $env:TEMP пише звичайний користувач, тож «звірити файл, потім скопіювати» лишало вікно.
# gemini_run.ps1 копіюємо в ProgramData (звичайний користувач туди не пише), хеш рахуємо вже з копії; розбіжність — копію
# видаляємо й падаємо. gemini_publish.ps1 лишається у профілі власника (задача gemini-publish запускає його звідти): байти
# читаємо раз, хеш — з пам'яті.
# queue_lanes.ps1 — спільний модуль смуг (М.9-Е): gemini_run.ps1 підвантажує його з тієї самої теки.
Copy-Item "$env:TEMP\gemini_run.ps1" "$run\gemini_run.ps1" -Force
Copy-Item "$env:TEMP\queue_lanes.ps1" "$run\queue_lanes.ps1" -Force
foreach ($name in @('gemini_run.ps1', 'queue_lanes.ps1')) {
    $dst = Join-Path $run $name
    $got = (Get-FileHash $dst -Algorithm SHA256).Hash
    if ($got -ne $expected[$name]) {
        Remove-Item $dst -Force -ErrorAction SilentlyContinue
        Stop-Here "хеш $name у ProgramData не збігся з хеші.psd1: маємо $got; файл видалено. Запусти 0_власник.ps1 знову; не допомогло — диспетчерові."
    }
}
$sha = [System.Security.Cryptography.SHA256]::Create()
$got = ([BitConverter]::ToString($sha.ComputeHash([System.IO.File]::ReadAllBytes($pubFile))) -replace '-', '')
if ($got -ne $expected['gemini_publish.ps1']) { Stop-Here "хеш gemini_publish.ps1 не збігся з хеші.psd1: маємо $got. Запусти 0_власник.ps1 знову; не допомогло — диспетчерові." }

Step 'Крок 5: дві задачі планувальника'
$set = @{ MultipleInstances = 'IgnoreNew'; AllowStartIfOnBatteries = $true; DontStopIfGoingOnBatteries = $true; StartWhenAvailable = $true }

# право «Вхід як пакетне завдання» для gemini: без нього задача не стартує (0x80070569); на Windows Home нема secpol.msc
$sid = ([System.Security.Principal.NTAccount]"$env:COMPUTERNAME\gemini").Translate([System.Security.Principal.SecurityIdentifier]).Value
$d = "$env:TEMP\batchright"; New-Item -ItemType Directory -Force $d | Out-Null
secedit /export /cfg "$d\cur.inf" /areas USER_RIGHTS | Out-Null
$line = Get-Content "$d\cur.inf" | Where-Object { $_ -match '^SeBatchLogonRight' }
$old = if ($line) { ($line -split '=', 2)[1].Trim() } else { '' }
$new = if (-not $old) { "*$sid" } elseif ($old -match [regex]::Escape($sid)) { $old } else { "$old,*$sid" }
'[Unicode]','Unicode=yes','[Version]','signature="$CHICAGO$"','Revision=1','[Privilege Rights]',"SeBatchLogonRight = $new" | Set-Content -Encoding Unicode "$d\new.inf"
secedit /configure /db "$d\new.sdb" /cfg "$d\new.inf" /areas USER_RIGHTS
if ($LASTEXITCODE -ne 0) { Stop-Here "secedit повернув код $LASTEXITCODE." }

# під gemini: раз на 5 хв, без межі часу задачі (М.9-Е): запуск — планувальник смуг, живе, доки йдуть його наряди
# (Codex без межі, agy — до agy_total_minutes), і сам опитує чергу; IgnoreNew не пускає другого.
$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\ProgramData\gemini-wrapper\gemini_run.ps1'
if ($EnableCodex) { $a.Arguments += ' -EnableCodex' }   # рішення власника 25.10 (9738): ключ рушія Codex у gemini_run.ps1
$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 5)
$s = New-ScheduledTaskSettingsSet @set -ExecutionTimeLimit ([TimeSpan]::Zero)
$c = Get-Credential -UserName "$env:COMPUTERNAME\gemini" -Message 'Пароль користувача gemini'
if (-not $c) { Stop-Here 'пароль gemini не введено.' }
Register-ScheduledTask -TaskName 'gemini-run' -Action $a -Trigger $t -Settings $s -User $c.UserName -Password $c.GetNetworkCredential().Password -RunLevel Limited -Force | Out-Null
$c = $null

# під тобою: раз на 1 хв (кінець прогону доходить за ≤ 2 хв), до 30 хв, поки ти увійшов у Windows (блокування екрана не заважає): задача з паролем
# акаунта Microsoft не приймає (0x8007052E); conhost --headless ховає вікно
$a2 = New-ScheduledTaskAction -Execute 'conhost.exe' -Argument "--headless powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$env:USERPROFILE\gemini-publish\gemini_publish.ps1`""
$t2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 1)
$s2 = New-ScheduledTaskSettingsSet @set -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
$p2 = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'gemini-publish' -Action $a2 -Trigger $t2 -Settings $s2 -Principal $p2 -Force | Out-Null

Get-ScheduledTask gemini-run, gemini-publish | ForEach-Object { $_.TaskName, $_.Principal.LogonType, $_.Triggers[0].Repetition.Interval, $_.Triggers[0].Repetition.Duration }

# очікувано: Password і Interactive, PT5M/PT1M, тривалість порожня; не порожня — виправ у «Планувальнику завдань» (НАЛАШТУВАННЯ.md, крок 5)
$bad = @()
foreach ($task in (Get-ScheduledTask gemini-run, gemini-publish)) {
    if ($task.Triggers[0].Repetition.Duration) { $bad += $task.TaskName }
}
if ($bad) { Write-Host "УВАГА: у $($bad -join ', ') тривалість повторення не порожня — Планувальник завдань → задача → Тригери → Змінити → «протягом: Безстроково»." -ForegroundColor Yellow }
Write-Host "Codex у gemini-run: $(if ($EnableCodex) { 'ВВІМКНЕНО (-EnableCodex)' } else { 'вимкнено' })"
Write-Host "`nГОТОВО: кроки 3 і 5. Далі — ЩО_НАТИСНУТИ.md: повернися в сеанс gemini і запусти 2_під_gemini.ps1 ще раз." -ForegroundColor Green
