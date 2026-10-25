#Requires -Version 5.1
<#
.SYNOPSIS
М.9-В, підготовка, частина gemini: крок 0 (клон, git config), Codex CLI, вхід, крок 4. Запуск — під gemini.

.DESCRIPTION
Запускається один раз, ПІСЛЯ 1_адмін.ps1 (обгортка в C:\ProgramData\gemini-wrapper уже стоїть); повторний запуск безпечний.
Паролів і токенів не читає й не виводить: про вхід судить лише наявність файлу чи код `codex login status`.
Codex без `-WithCodex` скрипт не ставить і не входить. Рішення власника 25.10 (9738): Codex під gemini вмикається з основним
акаунтом ChatGPT власника, ризик прийнято (токен лежить у `~/.codex/auth.json` профілю gemini — секрет у межі цього
користувача, у репозиторій не йде, 9739; ізоляцію рушіїв веде М.9-Г). З `-WithCodex`:
  Codex CLI  — інсталятор закріплено за релізом (без Node.js, https://github.com/openai/codex): файл
               https://releases.openai.com/codex/releases/<CodexRelease>/install.ps1 качається у файл, sha256 звіряється з
               `CodexInstaller` у хеші.psd1 і лише тоді виконується з `-Release <CodexRelease>` (9741); хеш порожній чи інший —
               СТОП, інсталятор не виконується (сам інсталятор несе блок підпису Authenticode — не перевірено — і звіряє SHA256SUMS пакета);
               вхід — `codex login --device-auth` (код на сторінці, без браузера на цьому ноутбуці):
               https://learn.chatgpt.com/docs/developer-commands?surface=cli
Gemini CLI не ставимо (рішення диспетчера 25.10: для Google One його замінено Antigravity CLI з 18.06.2026, README google-gemini/gemini-cli); другий рушій Gemini — наявний agy.
Команди кроків 0 і 4 — дослівно з НАЛАШТУВАННЯ.md.
#>
# Continue, не Stop: у Windows PowerShell 5.1 stderr рідних команд (git clone, npm) при Stop — виняток; коди виходу перевіряються вручну
param([switch]$WithCodex)
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
    # М.9-Г: частковий клон без дерева — розріджене дерево без даних крамниць пише сама обгортка (Initialize-Clone).
    git clone --filter=blob:none --no-checkout https://github.com/mightyrochy/kod-shi-data "$env:USERPROFILE\kod-shi-data"
    if ($LASTEXITCODE -ne 0) { Stop-Here "git clone повернув код $LASTEXITCODE." }
    git -C "$env:USERPROFILE\kod-shi-data" config gemini.m9g partial
} else { Write-Host 'Клон уже є.' }
if (-not (git config --global user.email)) { git config --global user.name 'gemini'; git config --global user.email "gemini@$env:COMPUTERNAME" }

# --- Codex CLI (лише -WithCodex, після рішення власника про акаунт, 9738) ---
if (-not $WithCodex) {
    Write-Host "`nCodex пропущено: без -WithCodex не ставиться й не входить (рішення власника 25.10, 9738: вмикати з -WithCodex)." -ForegroundColor Yellow
} else {
    Step 'Codex CLI'
    if (-not (Has codex)) {
        $expected = Import-PowerShellDataFile (Join-Path $PSScriptRoot 'хеші.psd1') -ErrorAction SilentlyContinue
        $want = $(if ($expected -and $expected.ContainsKey('CodexInstaller')) { [string]$expected['CodexInstaller'] } else { '' })
        $rel = $(if ($expected -and $expected.ContainsKey('CodexRelease')) { [string]$expected['CodexRelease'] } else { '' })
        if ($rel -notmatch '^\d+\.\d+\.\d+$') { Stop-Here "CodexRelease у хеші.psd1 порожній чи не виду x.y.z ('$rel'). Інсталятор не виконано." }
        $inst = "$env:TEMP\codex_install.ps1"
        Invoke-WebRequest "https://releases.openai.com/codex/releases/$rel/install.ps1" -OutFile $inst -UseBasicParsing
        $got = (Get-FileHash $inst -Algorithm SHA256).Hash
        Write-Host "sha256 інсталятора: $got"
        if (-not $want) { Stop-Here "хеш інсталятора Codex не зафіксовано в хеші.psd1 (CodexInstaller). Звір sha256 вище з офіційним джерелом, запиши його PR-ом; інсталятор не виконано." }
        if ($got -ne $want) { Stop-Here "sha256 інсталятора не збігся з хеші.psd1 (чекав $want). Інсталятор не виконано." }
        $env:CODEX_NON_INTERACTIVE = '1'
        & powershell -NoProfile -ExecutionPolicy Bypass -File $inst -Release $rel
        Update-Path
        if (-not (Has codex)) { Stop-Here 'codex не знайдено після установки; відкрий нове вікно PowerShell і запусти скрипт знову.' }
    }
    Write-Host "codex: $(& codex --version)"

    Step 'Вхід Codex (ChatGPT, --device-auth)'
    & codex login status *> $null
    if ($LASTEXITCODE -eq 0) { Write-Host 'Вхід ChatGPT вже є.' }
    else {
        Write-Host 'Відкрий показану адресу на телефоні, введи код і увійди основним акаунтом ChatGPT (рішення власника 25.10, 9738).' -ForegroundColor Yellow
        & codex login --device-auth
        & codex login status *> $null
        if ($LASTEXITCODE -ne 0) { Stop-Here 'вхід Codex не вдався (код не введено чи сплив): запусти цей самий рядок ще раз.' }
    }
    Write-Host 'Рушій Codex у задачі gemini-run вмикає 1_адмін.ps1 -EnableCodex (НАЛАШТУВАННЯ.md, «Пули й каскад»).'
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

Write-Host "`nГОТОВО: isolation OK$(if ($WithCodex) { ', Codex увійшов' } else { ', Codex вимкнено' }). Далі — ЩО_НАТИСНУТИ.md (повернутись до себе, перевірка heartbeat)." -ForegroundColor Green
