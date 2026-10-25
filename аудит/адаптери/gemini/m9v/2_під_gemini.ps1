#Requires -Version 5.1
<#
.SYNOPSIS
М.9-В, підготовка, частина gemini: крок 0 (клон, git config), Gemini CLI, Codex CLI, входи, крок 4. Запуск — під gemini.

.DESCRIPTION
Запускається двічі (ідемпотентний): 1) до 1_адмін.ps1 — крок 0, установка, входи; крок 4 пропускається, бо обгортки в
C:\ProgramData ще нема; 2) після 1_адмін.ps1 — решта пропускається (вже зроблено), іде крок 4.
Паролів і токенів не читає й не виводить: про вхід судить лише наявність файлу чи код `codex login status`.
Джерела установки (Windows):
  Gemini CLI — Node.js 20+, `npm install -g @google/gemini-cli`: https://www.geminicli.com/docs/get-started/installation
               (README: https://github.com/google-gemini/gemini-cli). УВАГА: для безкоштовного тарифу й Google One
               Gemini CLI з 18.06.2026 замінено Antigravity CLI; Sign in with Google працює з платною ліцензією Code Assist.
  Codex CLI  — `irm https://chatgpt.com/codex/install.ps1 | iex` (без Node.js): https://github.com/openai/codex ;
               вхід — `codex login` (браузер; `--device-auth` — без браузера): https://learn.chatgpt.com/docs/developer-commands?surface=cli
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
Step 'Вимоги: git 2.30+ і Node.js 20+'
Update-Path
if (-not (Has git)) { Stop-Here 'git не знайдено під gemini (НАЛАШТУВАННЯ.md, крок 0: git має бути).' }
if ((git --version) -notmatch '(\d+\.\d+\.\d+)') { Stop-Here 'git --version не розібрано.' }
$gv = [version]$Matches[1]
if ($gv -lt [version]'2.30') { Stop-Here "git $gv старіший за 2.30." }
$nodeOk = $false
if (Has node) { $nv = node --version; if ($nv -match '^v(\d+)\.' -and [int]$Matches[1] -ge 20) { $nodeOk = $true; Write-Host "git $gv, node $nv — ок." } }
if (-not $nodeOk) { Stop-Here 'Node.js 20+ нема (потрібен Gemini CLI). Його ставить 1_адмін.ps1 (winget) чи власник з https://nodejs.org/en/download ; після цього відкрий нове вікно PowerShell і запусти скрипт знову.' }

# --- крок 0 ---
Step 'Крок 0: клон і git config'
if (-not (Test-Path "$env:USERPROFILE\kod-shi-data\.git")) {
    git clone --depth 1 https://github.com/mightyrochy/kod-shi-data "$env:USERPROFILE\kod-shi-data"
    if ($LASTEXITCODE -ne 0) { Stop-Here "git clone повернув код $LASTEXITCODE." }
} else { Write-Host 'Клон уже є.' }
if (-not (git config --global user.email)) { git config --global user.name 'gemini'; git config --global user.email "gemini@$env:COMPUTERNAME" }

# --- Gemini CLI ---
Step 'Gemini CLI'
if (Has gemini.cmd) { Write-Host "gemini вже встановлено: $(& gemini.cmd --version)" }
else {
    npm install -g '@google/gemini-cli'
    if ($LASTEXITCODE -ne 0) { Stop-Here "npm install повернув код $LASTEXITCODE." }
    Update-Path; $env:Path += ";$env:APPDATA\npm"
    if (-not (Has gemini.cmd)) { Stop-Here 'gemini.cmd не знайдено після установки (шукай у %APPDATA%\npm).' }
}

# --- Codex CLI ---
Step 'Codex CLI'
if (-not (Has codex)) {
    Invoke-Expression (Invoke-RestMethod 'https://chatgpt.com/codex/install.ps1')
    Update-Path
    if (-not (Has codex)) { Stop-Here 'codex не знайдено після установки; відкрий нове вікно PowerShell і запусти скрипт знову.' }
}
Write-Host "codex: $(& codex --version)"

# --- входи (браузер) ---
Step 'Вхід Gemini CLI (Google)'
$gcred = "$env:USERPROFILE\.gemini\oauth_creds.json"
if (Test-Path $gcred) { Write-Host 'Вхід Google вже є.' }
else {
    Write-Host 'Зараз відкриється gemini. Обери «Sign in with Google», заверши вхід у браузері, потім вийди з gemini: /quit (чи Ctrl+C двічі).' -ForegroundColor Yellow
    Write-Host 'Якщо gemini напише, що безкоштовний тариф переведено на Antigravity CLI, — не продовжуй, скажи диспетчерові.' -ForegroundColor Yellow
    & gemini.cmd
    if (-not (Test-Path $gcred)) { Write-Host 'УВАГА: файлу входу Google не видно (вхід міг піти іншим способом). Скажи диспетчерові, що gemini показав.' -ForegroundColor Yellow }
}
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
if (-not (Test-Path 'C:\ProgramData\gemini-wrapper\gemini_run.ps1')) {
    Write-Host 'Обгортки в C:\ProgramData\gemini-wrapper ще нема: покажи власнику крок «1_адмін.ps1», потім запусти цей скрипт ще раз.' -ForegroundColor Yellow
    exit 0
}
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

Write-Host "`nГОТОВО: isolation OK, входи є. Далі — ЩО_НАТИСНУТИ.md (повернутись до себе, перевірка heartbeat)." -ForegroundColor Green
