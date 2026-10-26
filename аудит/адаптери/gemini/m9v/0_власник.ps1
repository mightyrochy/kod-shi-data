#Requires -Version 5.1
<#
.SYNOPSIS
М.9-В, підготовка, частина власника: без адміністратора, під своїм обліковим записом (не під gemini).

.DESCRIPTION
Крок 1 НАЛАШТУВАННЯ.md (claude --version), крок 2 (файли й SHA-256 проти хеші.psd1 = таблиці «Хеші файлів»),
тека %USERPROFILE%\gemini-outbox, спостерігач за СПОСТЕРІГАЧ.md «Налаштування» (спершу -DryRun, потім реєстрація),
рушій Claude — задача claude-run (НАЛАШТУВАННЯ.md «Рушій Claude»).
Ідемпотентний: повторний запуск перекачує файли, перевіряє хеші, перереєструє задачу. Паролів і токенів не читає.
Команди — дослівно з НАЛАШТУВАННЯ.md і СПОСТЕРІГАЧ.md.
#>
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
function Stop-Here([string]$m) { Write-Host "СТОП: $m" -ForegroundColor Red; Write-Host 'Напиши диспетчерові: ЗАБЛОКОВАНО + цей текст.'; exit 1 }
function Step([string]$m) { Write-Host "`n== $m" -ForegroundColor Cyan }

if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Stop-Here 'це вікно запущене від адміністратора. Цей скрипт — у звичайному PowerShell під твоїм обліковим записом.' }
if ($env:USERNAME -eq 'gemini') { Stop-Here 'ти під користувачем gemini; цей скрипт — під своїм обліковим записом.' }

# --- крок 1: Claude CLI (лише перевірка) ---
Step 'Крок 1: claude --version'
$ErrorActionPreference = 'Continue'   # stderr рідних команд у 5.1 при Stop — виняток
try { $v = & claude --version 2>&1; if ($LASTEXITCODE -ne 0) { throw "код $LASTEXITCODE" }; Write-Host $v }
catch { Stop-Here "claude --version не відповів ($($_.Exception.Message)). Встанови: irm https://claude.ai/install.ps1 | iex ; відкрий нове вікно ; claude auth login — і запусти скрипт знову." }

$ErrorActionPreference = 'Stop'

# --- крок 2: файли й хеші ---
Step 'Крок 2: файли обгортки і SHA-256'
$expected = Import-PowerShellDataFile (Join-Path $here 'хеші.psd1')
$base = 'https://raw.githubusercontent.com/mightyrochy/kod-shi-data/main/аудит/адаптери/gemini'
$pub = "$env:USERPROFILE\gemini-publish"; New-Item -ItemType Directory -Force $pub | Out-Null
Invoke-WebRequest "$base/gemini_publish.ps1" -OutFile "$pub\gemini_publish.ps1" -UseBasicParsing
Invoke-WebRequest "$base/gemini_run.ps1" -OutFile "$env:TEMP\gemini_run.ps1" -UseBasicParsing
$w = "$env:USERPROFILE\gemini-watch"; New-Item -ItemType Directory -Force $w | Out-Null
Invoke-WebRequest "$base/gemini_watch.ps1" -OutFile "$w\gemini_watch.ps1" -UseBasicParsing
$cr = "$env:USERPROFILE\claude-run"; New-Item -ItemType Directory -Force $cr | Out-Null
Invoke-WebRequest "$base/claude_run.ps1" -OutFile "$cr\claude_run.ps1" -UseBasicParsing
Get-FileHash "$pub\gemini_publish.ps1", "$env:TEMP\gemini_run.ps1" | Format-List Hash, Path
$bad = @()
foreach ($p in @(@('gemini_publish.ps1', "$pub\gemini_publish.ps1"), @('gemini_run.ps1', "$env:TEMP\gemini_run.ps1"), @('gemini_watch.ps1', "$w\gemini_watch.ps1"), @('claude_run.ps1', "$cr\claude_run.ps1"))) {
    $got = (Get-FileHash $p[1] -Algorithm SHA256).Hash
    if ($got -ne $expected[$p[0]]) { $bad += "$($p[0]): маємо $got, очікували $($expected[$p[0]])" }
}
if ($bad) { Stop-Here ("хеші не збіглися (нічого не зареєстровано):`n  " + ($bad -join "`n  ")) }
Write-Host 'Хеші збіглися з таблицею.' -ForegroundColor Green

# --- тека вихідних ---
Step 'Тека вихідних'
New-Item -ItemType Directory -Force "$env:USERPROFILE\gemini-outbox" | Out-Null
Write-Host "$env:USERPROFILE\gemini-outbox — є."

# --- спостерігач ---
Step 'Спостерігач: gh і -DryRun'
$ErrorActionPreference = 'Continue'
try { & gh auth status 2>&1 | Out-Host; if ($LASTEXITCODE -ne 0) { throw 'нема входу gh' } }
catch { Stop-Here 'gh auth status не пройшов (вхід власника в gh). Увійди: gh auth login — і запусти скрипт знову.' }
$log = "$w\watch.log"; $before = if (Test-Path $log) { @(Get-Content $log).Count } else { 0 }
& powershell -NoProfile -ExecutionPolicy Bypass -File "$w\gemini_watch.ps1" -DryRun
$code = $LASTEXITCODE
$new = if (Test-Path $log) { @(Get-Content $log | Select-Object -Skip $before) } else { @() }
$new | Select-Object -Last 10 | ForEach-Object { Write-Host "  watch.log: $_" }
$fails = @($new | Where-Object { $_ -match 'збій|відмов|не записано' })
if ($code -ne 0 -or $fails) { Stop-Here "-DryRun: код $code, відмов у журналі: $($fails.Count). Покажи диспетчерові рядки з watch.log вище." }
$ErrorActionPreference = 'Stop'
Remove-Item "$w\state.json" -ErrorAction SilentlyContinue   # базову лінію реальний прохід бере сам
Write-Host "-DryRun: код 0, відмов 0." -ForegroundColor Green

Step 'Спостерігач: реєстрація задачі gemini-watch'
$set = @{ MultipleInstances = 'IgnoreNew'; AllowStartIfOnBatteries = $true; DontStopIfGoingOnBatteries = $true; StartWhenAvailable = $true }
$a = New-ScheduledTaskAction -Execute 'conhost.exe' -Argument "--headless powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$w\gemini_watch.ps1`""
$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
$s = New-ScheduledTaskSettingsSet @set -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
$p = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'gemini-watch' -Action $a -Trigger $t -Settings $s -Principal $p -Force | Out-Null
Get-ScheduledTask gemini-watch | ForEach-Object { "gemini-watch: $($_.State), інтервал $($_.Triggers[0].Repetition.Interval)" }

# --- рушій Claude ---
Step 'Рушій Claude: клон і реєстрація задачі claude-run'
$ErrorActionPreference = 'Continue'
$o = & git -C "$env:USERPROFILE\kod-shi-data" remote get-url origin 2>&1
$ErrorActionPreference = 'Stop'
if (($o -replace '\.git$', '') -ne 'https://github.com/mightyrochy/kod-shi-data') { Stop-Here "клон $env:USERPROFILE\kod-shi-data не знайдено чи origin не той ($o): claude-run бере наряди з нього." }
$a = New-ScheduledTaskAction -Execute 'conhost.exe' -Argument "--headless powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$cr\claude_run.ps1`""
$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$s = New-ScheduledTaskSettingsSet @set -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName 'claude-run' -Action $a -Trigger $t -Settings $s -Principal $p -Force | Out-Null
Get-ScheduledTask claude-run | ForEach-Object { "claude-run: $($_.State), інтервал $($_.Triggers[0].Repetition.Interval), межа часу $($_.Settings.ExecutionTimeLimit)" }

Write-Host "`nГОТОВО: частина власника пройдена. Далі — за ЩО_НАТИСНУТИ.md (крок 2: користувач gemini)." -ForegroundColor Green
