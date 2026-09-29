# RZ-2: retry of catalogue-parse violators BY REASON, on the laptop (LM Studio :1234).
# Comments are ASCII on purpose; the file is saved WITH a UTF-8 BOM so that powershell.exe 5.1
# reads the Cyrillic paths below as UTF-8 and not as ANSI.
#
# WHAT IT DOES. Runs `каталог_розбір_прогін.py --повтор` (targeted mode, RZ-2) as its own
# process, pushes the retry's `прогін.json` + `підсумок.txt` every -PushEveryMin minutes and once
# at the end (never the raw *.txt, never tar), and restarts the SAME command when the python
# process dies or leaves failed calls: a stopped run is resumed by the same command, because an
# item whose answer already sits in its file under the same request is not sent again (`_готова`).
# Starting this file again after a reboot is the same command too.
#
#   pilot (40 items, foreground):
#     .\джерела\повтор_рз2.ps1 -Perelik аудит\розбір_каталогу\mamaylm-gemma-3-12b-it-v2.0_uk_povnyi_pilot\порушники.txt -Kudy аудит\розбір_каталогу\mamaylm-gemma-3-12b-it-v2.0_uk_povnyi_pilot_povtor2
#   full retry (detached OS process, survives closing the terminal):
#     Start-Process powershell -WindowStyle Minimized -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','C:\Users\Admin\kod-shi-rz2\джерела\повтор_рз2.ps1'
param(
    [string]$Perelik = "",
    [string]$Kudy = "аудит\розбір_каталогу\mamaylm-gemma-3-12b-it-v2.0_uk_povnyi_povtor2",
    [string]$Model = "mamaylm-gemma-3-12b-it-v2.0",
    [int]$PushEveryMin = 60,
    [int]$MaxRestarts = 5,
    [string]$Branch = "claude/rz2-povtor-sposib"
)
$ErrorActionPreference = "Continue"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"; $env:GIT_NO_LAZY_FETCH = "1"
$py = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }
$src = "аудит\розбір_каталогу\mamaylm-gemma-3-12b-it-v2.0_uk_povnyi"
$script = "джерела\каталог_розбір_прогін.py"
New-Item -ItemType Directory -Force -Path $Kudy | Out-Null
$log = Join-Path $Kudy "log.txt"

# One runner per retry folder: a second start while the first is alive would send the same items
# twice and race on прогін.json.
$lock = Join-Path $Kudy "runner.pid"
if (Test-Path $lock) {
    $old = Get-Content $lock -ErrorAction SilentlyContinue
    if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) {
        Write-Host "already running as PID $old -- nothing to do"; exit 0
    }
}
Set-Content -Path $lock -Value $PID

function Push-Progress {
    & $py $script --підсумок $Kudy $src | Out-Null
    $sum = Join-Path $Kudy "підсумок.txt"
    if (-not (Test-Path $sum)) { return }
    git add -- (Join-Path $Kudy "прогін.json") $sum
    git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { return }
    $line = (Get-Content -Encoding UTF8 $sum -TotalCount 2)[1]
    $msg = "РЗ-2 повтор за причиною (ноутбук): $line`n`nЩо міняє: прогін.json і підсумок.txt повтору $(Split-Path -Leaf $Kudy); сирі відповіді лишаються на ноутбуці.`n"
    $f = Join-Path $env:TEMP "rz2_msg.txt"
    [IO.File]::WriteAllText($f, $msg, (New-Object Text.UTF8Encoding $false))
    git commit -q -F $f
    git pull -q --no-rebase --no-edit origin $Branch
    git push -q --no-thin origin "HEAD:$Branch"
    Add-Content -Encoding UTF8 -Path $log -Value "$(Get-Date -Format s) pushed: $line (exit $LASTEXITCODE)"
}

$argv = @($script, "--модель", $Model, "--повтор", $src, "--куди", $Kudy, "--паралельно", "2")
if ($Perelik) { $argv += @("--перелік", $Perelik) }
for ($try = 0; $try -le $MaxRestarts; $try++) {
    Add-Content -Encoding UTF8 -Path $log -Value "$(Get-Date -Format s) start #$try"
    $p = Start-Process -FilePath $py -ArgumentList $argv -NoNewWindow -PassThru `
        -RedirectStandardOutput (Join-Path $Kudy "out.txt") -RedirectStandardError (Join-Path $Kudy "err.txt")
    $null = $p.Handle   # without touching Handle, PS 5.1 leaves ExitCode empty after exit
    while (-not $p.WaitForExit($PushEveryMin * 60 * 1000)) { Push-Progress }
    Push-Progress
    # exit 0 = done with every call answered; 3 = done but some calls failed (LM Studio down,
    # HTTP 400) -- those are sent again by the same command; anything else = python died.
    Add-Content -Encoding UTF8 -Path $log -Value "$(Get-Date -Format s) exit $($p.ExitCode)"
    if ($p.ExitCode -eq 0) { break }
    Start-Sleep -Seconds 60
}
Remove-Item $lock -ErrorAction SilentlyContinue
