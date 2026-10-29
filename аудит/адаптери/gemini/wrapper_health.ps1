#Requires -Version 5.1
# Спільні тривоги й ритм стану; деталі — лише з цього переліку, жодного тексту агента.
$script:HealthDetails = @{
    AUTH = @('AGY', 'CODEX', 'CLAUDE', 'CLOUD')
    ISOLATION = @('WHOAMI', 'NET_SESSION', 'PROFILES', 'DRIVES', 'ENV')
    DISK = @('FULL')
    ENGINE = @('AGY', 'CODEX', 'CLAUDE')
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

function Add-HealthException($Exception) {
    <# Диск упізнається за системним кодом, текст винятку не пересилається. #>
    $e = $Exception
    while ($null -ne $e) {
        if (($e.HResult -band 0xffff) -in @(39, 112)) { Add-HealthAlert 'DISK' 'FULL'; return }
        $e = $e.InnerException
    }
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

# Група квоти agy для моделі — одне джерело для смуги (gemini_run.ps1: чекання QUOTA0_<група>, pools.json) і ланцюга
# (wrapper_chain.ps1: рецензент за групою саме обраної моделі).
# Родини моделей: група /usage без власних слів («Gemini Models», «Claude and GPT models») — спільна для родини.
$script:Families = @('gemini', 'claude', 'gpt')

# Слова назви без чисел і службових слів: група «Gemini 3.5 Flash» ↔ модель gemini-3.8-flash-high — спільне «flash».
function Get-NameTokens([string]$Name) {
    $stop = @('gemini', 'high', 'medium', 'low', 'preview', 'latest', 'thinking', 'exp', 'and', 'the', 'models', 'model')
    @(($Name.ToLowerInvariant() -split '[^a-z0-9]+') | Where-Object { $_ -and $_ -notmatch '^[0-9]+$' -and $stop -notcontains $_ })
}

# Власні слова назви — без назв родин (gemini, claude, gpt): «Gemini 4 Argon» -> argon, «Claude and GPT models» -> нічого.
function Get-SpecificTokens([string]$Name) { @(Get-NameTokens $Name | Where-Object { $script:Families -notcontains $_ }) }

# ASCII-код групи для рядка: назва → A-Z0-9, до 16 знаків.
function ConvertTo-GroupCode([string]$Name) {
    $g = ($Name.ToUpperInvariant() -replace '[^A-Z0-9]', '')
    if (-not $g) { $g = 'MODEL' }
    $g.Substring(0, [Math]::Min(16, $g.Length))
}

# Групи моделі: за власними словами («argon», «flash»); нема — група родини без власних слів («Gemini Models»).
function Get-ModelGroups([string]$Model, $Groups) {
    $mt = @(Get-SpecificTokens $Model)
    $hit = @($Groups | Where-Object { $g = $_; @(Get-SpecificTokens $g.Name | Where-Object { $mt -contains $_ }).Count -gt 0 })
    if ($hit.Count -gt 0) { return $hit }
    $fam = ($Model.ToLowerInvariant() -split '-')[0]
    if ($script:Families -notcontains $fam) { return @() }
    @($Groups | Where-Object { @(Get-SpecificTokens $_.Name).Count -eq 0 -and @($_.Name.ToLowerInvariant() -split '[^a-z0-9]+') -contains $fam })
}
