#Requires -Version 5.1
<#
.SYNOPSIS
М.9-Г: пісочниця Codex під gemini і проба мірила. «PowerShell від імені адміністратора», після кроку 3 ЩО_НАТИСНУТИ.md.

.DESCRIPTION
1. `codex sandbox setup --elevated --user <ПК>\gemini --codex-home C:\Users\gemini\.codex` — розгортання від адміністратора
   для користувача без прав (документація Codex «Windows sandbox»: окремий офлайн-користувач пісочниці й правило
   брандмауера; без нього `[windows] sandbox = "elevated"` профілю m9g не діє).
2. Разова задача під gemini (пароль — Get-Credential, як у 1_адмін.ps1) запускає пробу: профіль m9g дослівно з
   C:\ProgramData\gemini-wrapper\gemini_run.ps1, команди через `codex sandbox -P m9g`: стороння адреса, токен Codex, вхід
   agy, `.git/config` і хуки — відмова; коміт і гілка — є. `agy` у пісочниці й збірка Windows — лише міра (9754).
3. Сканер gemini_publish.ps1 на підкинутому фальшивому токені — SECRET. 4. Клон gemini частковий, файлів даних крамниць 0.
Результат — рядки ok/FAIL/МІРА тут і в C:\Users\Public\gemini\out\m9g_proba.txt; задача й скрипт проби знімаються.
Ідемпотентний: повторний запуск повторює пробу.
#>
$ErrorActionPreference = 'Stop'
function Stop-Here([string]$m) { Write-Host "СТОП: $m" -ForegroundColor Red; Write-Host 'Напиши диспетчерові: ЗАБЛОКОВАНО + цей текст.'; exit 1 }
function Step([string]$m) { Write-Host "`n== $m" -ForegroundColor Cyan }

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Stop-Here 'потрібен PowerShell від імені адміністратора (Пуск → PowerShell → правий клік → «Запуск від імені адміністратора» → Так).' }
if ($env:USERNAME -eq 'gemini') { Stop-Here 'це вікно відкрито під gemini; відкрий від свого облікового запису.' }
$g = 'C:\Users\gemini'; $wrap = 'C:\ProgramData\gemini-wrapper'; $out = 'C:\Users\Public\gemini\out\m9g_proba.txt'
if (-not (Test-Path "$wrap\gemini_run.ps1")) { Stop-Here "нема $wrap\gemini_run.ps1: спершу кроки 1–2." }
$codex = Get-ChildItem "$g\AppData\Local", "$g\.codex" -Recurse -Filter codex.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $codex) { Stop-Here "codex.exe у профілі gemini не знайдено: спершу крок 3 (2_під_gemini.ps1 -WithCodex)." }
$codex = $codex.FullName
Write-Host "codex: $codex"

Step 'Пісочниця Codex для gemini (elevated)'
& $codex sandbox setup --elevated --user "$env:COMPUTERNAME\gemini" --codex-home "$g\.codex"
if ($LASTEXITCODE -ne 0) { Stop-Here "codex sandbox setup повернув код $LASTEXITCODE (текст вище)." }

Step 'Проба під gemini (разова задача)'
$probe = @'
param([string]$Codex)
$ErrorActionPreference = 'Continue'
$res = New-Object System.Collections.Generic.List[string]
function Say([string]$s) { $res.Add($s) }
$g = $env:USERPROFILE; $ch = Join-Path $g '.codex'; $repo = Join-Path $g 'm9g-proba'
$src = [IO.File]::ReadAllText('C:\ProgramData\gemini-wrapper\gemini_run.ps1')
if ($src -notmatch "(?s)\`$script:CodexConfig = @'\r?\n(.*?)\r?\n'@") { Say 'FAIL config: профілю m9g у gemini_run.ps1 нема' }
else {
    $cfg = $Matches[1]
    # m9g-agy — лише для міри: m9g з мережею й без заборони входу agy.
    $agyCfg = "`n[permissions.m9g-agy.network]`nenabled = true`n`n[permissions.m9g-agy.filesystem]`n"":root"" = ""read""`n"":tmpdir"" = ""write""`n""~/.codex/auth.json"" = ""deny""`n`n[permissions.m9g-agy.filesystem."":workspace_roots""]`n""."" = ""write""`n"
    New-Item -ItemType Directory -Force $ch | Out-Null
    [IO.File]::WriteAllText((Join-Path $ch 'config.toml'), $cfg + "`n" + $agyCfg)
    Remove-Item -Recurse -Force $repo -ErrorAction SilentlyContinue
    git init -q $repo; 'a' | Set-Content (Join-Path $repo 'a.txt'); git -C $repo add a.txt
    git -C $repo -c user.name=t -c user.email=t@x commit -q -m init
    function Box([string]$P, [string]$Cmd) {
        $enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Cmd))
        (& $Codex sandbox -P $P -C $repo -- powershell -NoProfile -EncodedCommand $enc 2>&1 | Out-String)
    }
    function Chk([string]$Name, [string]$Want, [string]$Cmd) {
        $got = Box 'm9g' $Cmd
        if ($got -like "*$Want*") { Say "ok   $Name" } else { Say "FAIL $Name`: чекав $Want, є $($got.Trim() -replace '\s+', ' ')" }
    }
    Chk net-web NET_DENIED "try { Invoke-WebRequest https://example.com -UseBasicParsing -TimeoutSec 15 | Out-Null; 'NET_OPEN' } catch { 'NET_DENIED' }"
    Chk net-curl NET_DENIED "curl.exe -s -m 15 -o NUL https://1.1.1.1; if (`$LASTEXITCODE -eq 0) { 'NET_OPEN' } else { 'NET_DENIED' }"
    if (Test-Path "$ch\auth.json") { Chk codex-token AUTH_DENIED "try { [IO.File]::ReadAllText('$ch\auth.json') | Out-Null; 'AUTH_READ' } catch { 'AUTH_DENIED' }" }
    else { Say 'МІРА codex-token: auth.json нема (вхід Codex не зроблено)' }
    $gem = Get-ChildItem "$g\.gemini" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($gem) { Chk agy-login GEM_DENIED "try { [IO.File]::ReadAllBytes('$($gem.FullName)') | Out-Null; 'GEM_READ' } catch { 'GEM_DENIED' }" }
    else { Say 'МІРА agy-login: у ~\.gemini файлів нема — вхід agy лежить деінде (9754)' }
    Chk codex-cfg CFG_RO "try { [IO.File]::AppendAllText('$ch\config.toml', '#'); 'CFG_W' } catch { 'CFG_RO' }"
    Chk git-hooks HOOK_RO "try { New-Item -ItemType File -Force .git\hooks\pre-commit -ErrorAction Stop | Out-Null; 'HOOK_W' } catch { 'HOOK_RO' }"
    Box 'm9g' 'git config core.fsmonitor pwn' | Out-Null
    if (git -C $repo config --get core.fsmonitor) { Say 'FAIL git-config: core.fsmonitor записано' } else { Say 'ok   git-config' }
    Chk commit COMMIT_OK "'b' | Set-Content b.txt; git add b.txt; git -c user.name=g -c user.email=g@x commit -q -m b; git checkout -q -b gemini/x; if (`$LASTEXITCODE -eq 0) { 'COMMIT_OK' }"
    Chk tmp TMP_OK "[IO.Path]::GetTempFileName() | Out-Null; 'TMP_OK'"
    $agy = (Get-Command agy -ErrorAction SilentlyContinue).Source
    if ($agy) { Say "МІРА agy у пісочниці m9g-agy: $((Box 'm9g-agy' "& '$agy' -p '/usage'; 'AGY_RC=' + `$LASTEXITCODE").Trim() -replace '\s+', ' ')" }
    [IO.File]::WriteAllText((Join-Path $ch 'config.toml'), $cfg)
    Remove-Item -Recurse -Force $repo -ErrorAction SilentlyContinue
}
$k = Join-Path $g 'kod-shi-data'
$data = @(Get-ChildItem $k -Recurse -File -Include *.gz, *.jsonl, *.xml -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "$k\.git\*" }).Count
if ((git -C $k config --get gemini.m9g) -eq 'partial' -and $data -eq 0) { Say 'ok   clone: частковий, файлів даних крамниць 0' }
else { Say "FAIL clone: gemini.m9g=$(git -C $k config --get gemini.m9g), файлів даних $data (обгортка ще не пройшла з М.9-Г?)" }
$v = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
Say "МІРА windows: $($v.DisplayVersion) збірка $($v.CurrentBuild)"
[IO.File]::WriteAllLines('C:\Users\Public\gemini\out\m9g_proba.txt', $res)
'@
[IO.File]::WriteAllText("$wrap\m9g_proba.ps1", $probe, (New-Object Text.UTF8Encoding($true)))
Remove-Item $out -ErrorAction SilentlyContinue
$c = Get-Credential -UserName "$env:COMPUTERNAME\gemini" -Message 'Пароль gemini (той самий, що в кроці 2)'
$a = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$wrap\m9g_proba.ps1`" -Codex `"$codex`""
try {
    Register-ScheduledTask -TaskName 'gemini-m9g-proba' -Action $a -User $c.UserName -Password $c.GetNetworkCredential().Password -RunLevel Limited -Force | Out-Null
    Start-ScheduledTask 'gemini-m9g-proba'
    $t0 = Get-Date
    while (-not (Test-Path $out) -and ((Get-Date) - $t0).TotalMinutes -lt 10) { Start-Sleep 5 }
} finally {
    Unregister-ScheduledTask 'gemini-m9g-proba' -Confirm:$false -ErrorAction SilentlyContinue
    Remove-Item "$wrap\m9g_proba.ps1" -ErrorAction SilentlyContinue
}
if (-not (Test-Path $out)) { Stop-Here 'проба під gemini не дописала результату за 10 хв.' }
$lines = @(Get-Content $out -Encoding UTF8)

Step 'Сканер секретів gemini_publish.ps1 (фальшивий токен)'
$pub = "$env:USERPROFILE\gemini-publish\gemini_publish.ps1"
$tmp = Join-Path $env:TEMP 'm9g-secret'
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
git init -q $tmp; 'a' | Set-Content "$tmp\a.txt"; git -C $tmp add a.txt; git -C $tmp -c user.name=t -c user.email=t@x commit -q -m init; git -C $tmp branch -M main
git -C $tmp checkout -q -b fake; ('key = sk-' + ('Q' * 24)) | Set-Content "$tmp\b.txt"; git -C $tmp add b.txt; git -C $tmp -c user.name=t -c user.email=t@x commit -q -m b
$secret = & { . $pub -WorkDir $tmp; $script:Repo = "$tmp\.git"; $script:NoHooks = (New-Item -ItemType Directory -Force "$tmp\no-hooks").FullName; Test-SecretObjects 'fake' 'main' }
$lines += $(if ($secret) { 'ok   secret: фальшивий токен затримано (SECRET)' } else { 'FAIL secret: фальшивий токен пройшов сканер' })
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
[IO.File]::WriteAllLines($out, $lines)

Step 'Результат'
$lines | ForEach-Object { Write-Host $_ -ForegroundColor $(if ($_ -like 'FAIL*') { 'Red' } elseif ($_ -like 'ok*') { 'Green' } else { 'Yellow' }) }
$bad = @($lines | Where-Object { $_ -like 'FAIL*' }).Count
if ($bad) { Stop-Here "проба М.9-Г: $bad FAIL (рядки вище; файл $out)." }
Write-Host "`nГОТОВО: М.9-Г — пісочниця Codex діє, проба пройдена ($out)." -ForegroundColor Green
