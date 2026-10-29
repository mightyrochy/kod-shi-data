#Requires -Version 5.1
# Спільні тривоги й ритм стану; деталі — лише з цього переліку, жодного тексту агента.
$script:HealthDetails = @{
    AUTH = @('AGY', 'CODEX', 'CLAUDE', 'CLOUD')
    ISOLATION = @('WHOAMI', 'NET_SESSION', 'PROFILES', 'DRIVES', 'ENV')
    DISK = @('FULL')
    ENGINE = @('AGY', 'CODEX', 'CLAUDE')
    TASKDIR = @('UNPUSHED')
}
$script:HealthAlertDir = ''
$script:HeartbeatAction = $null
$script:HeartbeatBusy = $false
$script:LastHealthBeat = [datetime]::MinValue

function Test-HealthAlert([string]$Line) {
    <# Лише відомі код і деталь; довільний текст не стає службовим рядком. #>
    if ($Line -cnotmatch '\AGEMINI ОБГОРТКА: ТРИВОГА ([A-Z_]{2,16}) ([A-Z_]{2,16})\z') { return $false }
    $script:HealthDetails.ContainsKey($Matches[1]) -and $script:HealthDetails[$Matches[1]] -ccontains $Matches[2]
}

function Add-HealthAlert([string]$Code, [string]$Detail) {
    <# Подія у вихідних, не частіше ніж раз на годину для тієї самої пари; стан переживає перезапуск. #>
    $line = "GEMINI ОБГОРТКА: ТРИВОГА $Code $Detail"
    if (-not $script:HealthAlertDir -or -not (Test-HealthAlert $line)) { return }
    [void][System.IO.Directory]::CreateDirectory($script:HealthAlertDir)
    $lock = $null
    try {
        # Планувальник і процеси нарядів пишуть одночасно: один замок на перевірку й запис.
        for ($i = 0; $i -lt 20 -and $null -eq $lock; $i++) {
            try { $lock = [System.IO.File]::Open((Join-Path $script:HealthAlertDir '.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
            catch { Start-Sleep -Milliseconds 50 }
        }
        if ($null -eq $lock) { throw 'замок тривог зайнятий' }
        $stamp = Join-Path $script:HealthAlertDir ".$Code-$Detail.utc"
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        if (Test-Path -LiteralPath $stamp) {
            $last = 0L
            if ([long]::TryParse([System.IO.File]::ReadAllText($stamp), [ref]$last) -and $now - $last -lt 3600) { return }
        }
        $name = '{0:yyyyMMdd-HHmmss}-{1}.txt' -f [datetime]::UtcNow, ([guid]::NewGuid().ToString('N').Substring(0, 12))
        Write-FileAtomic (Join-Path $script:HealthAlertDir $name) ($line + "`n")
        Write-FileAtomic $stamp ([string]$now)
    } finally { if ($null -ne $lock) { $lock.Dispose() } }
}

# Брак місця в тексті git (Invoke-Git кидає рядок із stderr): так git повідомляє про запис на повний диск.
$script:DiskFullRx = '(?i)No space left on device|not enough space on the disk|unable to write (new )?(index )?file|could not write|short write|Could not reset index file'

function Test-DiskFull($Exception) {
    <# Виняток чи вкладений у нього — від браку місця: системні коди 39 і 112 або текст git. #>
    for ($e = $Exception; $null -ne $e; $e = $e.InnerException) {
        if (($e.HResult -band 0xffff) -in @(39, 112) -or $e.Message -match $script:DiskFullRx) { return $true }
    }
    $false
}

function Test-StorageFault($Exception) {
    <# Минущий збій сховища: брак місця чи файл, зайнятий іншим процесом (коди 32, 33). Стійкі помилки файлової системи
    (довгий шлях, доступ) сюди не входять — вони повторювались би вічно й не дійшли б до диспетчера. #>
    if (Test-DiskFull $Exception) { return $true }
    for ($e = $Exception; $null -ne $e; $e = $e.InnerException) { if (($e.HResult -band 0xffff) -in @(32, 33)) { return $true } }
    $false
}

function Format-ErrorDetail($Err) {
    <# Повний текст винятку й місце, де він виник, — одним рядком для журналу (рядок диспетчерові лишається за шаблоном):
    тип і повідомлення з вкладеними винятками, файл і рядок скрипта, стек викликів. #>
    $e = $(if ($Err -is [System.Management.Automation.ErrorRecord]) { $Err.Exception } else { $Err })
    $parts = @()
    for ($x = $e; $null -ne $x; $x = $x.InnerException) { $parts += "$($x.GetType().FullName): $($x.Message)" }
    $where = ''
    if ($Err -is [System.Management.Automation.ErrorRecord]) {
        $ii = $Err.InvocationInfo
        if ($null -ne $ii -and $ii.ScriptName) { $where = " @ $(Split-Path -Leaf $ii.ScriptName):$($ii.ScriptLineNumber)" }
        if ($Err.ScriptStackTrace) { $where += ' | стек: ' + (($Err.ScriptStackTrace -split '\r?\n') -join ' <- ') }
    }
    (($parts -join ' <= ') + $where) -replace '\s*[\r\n]+\s*', ' '
}

function Add-HealthException($Exception) {
    <# Диск упізнається за системним кодом чи текстом git, текст винятку не пересилається. #>
    if (Test-DiskFull $Exception) { Add-HealthAlert 'DISK' 'FULL' }
}

function Invoke-HealthBeat {
    <# Серцебиття планувальника під час очікування; процеси нарядів не підміняють його свіжість. #>
    if ($null -eq $script:HeartbeatAction -or $script:HeartbeatBusy -or ([datetime]::UtcNow - $script:LastHealthBeat).TotalSeconds -lt 60) { return }
    $script:HeartbeatBusy = $true
    $script:LastHealthBeat = [datetime]::UtcNow
    try { & $script:HeartbeatAction }
    finally { $script:HeartbeatBusy = $false }
}

function Test-ReviewBranch([string]$Branch) {
    <# Звіти перевірки й пачки вже містять вердикт і не породжують рекурсії. #>
    $Branch -cmatch '/(?:авто(?:перевірка|живий)-|перевірка-|pachka-|Е1-нічний-живий-)'
}
