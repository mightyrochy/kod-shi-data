#Requires -Version 5.1
<#
.SYNOPSIS
М.9-В, підготовка, частина gemini: крок 0 (клон, git config), Codex CLI, вхід, крок 4. Запуск — під gemini.

.DESCRIPTION
Запускається один раз, ПІСЛЯ 1_адмін.ps1 (обгортка в C:\ProgramData\gemini-wrapper уже стоїть); повторний запуск безпечний.
Паролів і токенів не читає й не виводить: про вхід судить лише наявність файлу чи код `codex login status`.
Джерела установки (Windows):
  Codex CLI  — `irm https://chatgpt.com/codex/install.ps1 | iex` (без Node.js): https://github.com/openai/codex ;
               вхід — `codex login` (браузер; `--device-auth` — без браузера): https://learn.chatgpt.com/docs/developer-commands?surface=cli
Gemini CLI не ставимо (рішення диспетчера 25.10: для Google One його замінено Antigravity CLI з 18.06.2026, README google-gemini/gemini-cli); другий рушій Gemini — наявний agy.
Команди кроків 0 і 4 — дослівно з НАЛАШТУВАННЯ.md.
#>
# Continue, не Stop: у Windows PowerShell 5.1 stderr рідних команд (git clone, npm) при Stop — виняток; коди виходу перевіряються вручну
$ErrorActionPreference = 'Continue'
function Stop-Here([string]$m) { Write-Host "СТОП: $m" -ForegroundColor Red; Write-Host 'Напиши диспетчерові: ЗАБЛОКОВАНО + цей текст.'; exit 1 }
function Step([string]$m) { Write-Host "`n== $m" -ForegroundColor Cyan }
function Update-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User') }
function Has([string]$n) { [bool](Get-Command $n -ErrorAction SilentlyContinue) }

if ($env:USERNAME -ne 'gemini') { Stop-Here "це має бути користувач gemini, а тут $env:USERNAME (Win+L → gemini)." }
if (([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Stop-Here 'gemini має бути без прав адміністратора (ізоляція 19.10).' }

# --- вимоги ---
Step 'Вимоги: git 2.30+ і обгортка'
Update-Path
if (-not (Has git)) { Stop-Here 'git не знайдено під gemini (НАЛАШТУВАННЯ.md, крок 0: git має бути).' }
if ((git --version) -notmatch '(\d+\.\d+\.\d+)') { Stop-Here 'git --version не розібрано.' }
$gv = [version]$Matches[1]
if ($gv -lt [version]'2.30') { Stop-Here "git $gv старіший за 2.30." }
Write-Host "git $gv — ок."
if (-not (Test-Path 'C:\ProgramData\gemini-wrapper\gemini_run.ps1')) {
    Stop-Here 'обгортки в C:\ProgramData\gemini-wrapper нема: спершу 1_адмін.ps1 (адмінський PowerShell під власником), потім цей скрипт.' }

# --- крок 0 ---
Step 'Крок 0: клон і git config'
if (-not (Test-Path "$env:USERPROFILE\kod-shi-data\.git")) {
    git clone --depth 1 https://github.com/mightyrochy/kod-shi-data "$env:USERPROFILE\kod-shi-data"
    if ($LASTEXITCODE -ne 0) { Stop-Here "git clone повернув код $LASTEXITCODE." }
} else { Write-Host 'Клон уже є.' }
if (-not (git config --global user.email)) { git config --global user.name 'gemini'; git config --global user.email "gemini@$env:COMPUTERNAME" }

# --- Codex CLI ---
Step 'Codex CLI'
if (-not (Has codex)) {
    Invoke-Expression (Invoke-RestMethod 'https://chatgpt.com/codex/install.ps1')
    Update-Path
    if (-not (Has codex)) { Stop-Here 'codex не знайдено після установки; відкрий нове вікно PowerShell і запусти скрипт знову.' }
}
Write-Host "codex: $(& codex --version)"

# --- вхід (браузер) ---
Step 'Вхід Codex (ChatGPT)'
& codex login status *> $null
if ($LASTEXITCODE -eq 0) { Write-Host 'Вхід ChatGPT вже є.' }
else {
    Write-Host 'Зараз відкриється браузер: увійди в ChatGPT. Без браузера: codex login --device-auth' -ForegroundColor Yellow
    & codex login
    & codex login status *> $null
    if ($LASTEXITCODE -ne 0) { Stop-Here 'codex login status: входу нема.' }
}

# --- крок 4 ---
Step 'Крок 4: перевірка ізоляції'
powershell -NoProfile -ExecutionPolicy Bypass -File C:\ProgramData\gemini-wrapper\gemini_run.ps1
Get-Content C:\Users\Public\gemini\out\heartbeat.json      # має бути "isolation":"OK"
$hb = Get-Content C:\Users\Public\gemini\out\heartbeat.json -Raw | ConvertFrom-Json
if ($hb.isolation -ne 'OK') {
    Stop-Here "isolation=$($hb.isolation): WHOAMI — не той користувач, NET_SESSION — права адміністратора, PROFILES — бачить чужий профіль, DRIVES — інший диск, ENV — змінна з KEY/TOKEN/SECRET/PASSWORD." }
$denied = $false
try { Add-Content C:\ProgramData\gemini-wrapper\gemini_run.ps1 '#' -ErrorAction Stop } catch { $denied = $true }   # має бути відмова в доступі
if (-not $denied) { Stop-Here 'gemini зміг дописати в gemini_run.ps1 — права теки неправильні (крок 3).' }
Write-Host 'Запис у обгортку відхилено — як і треба.' -ForegroundColor Green
agy models                                                  # список моделей (диспетчерові не треба — обгортка сама)

Write-Host "`nГОТОВО: isolation OK, Codex увійшов. Далі — ЩО_НАТИСНУТИ.md (повернутись до себе, перевірка heartbeat)." -ForegroundColor Green
