#Requires -Version 5.1
<# Стенд «потрібен вхід без вузла входу»: текст рушія «authentication required» без мережі не є виходом з акаунта.
Справжні Update-UsageCache, Get-ErrorCode й Test-EngineReachable; підроблено лише agy (fake_health.py) і адреси вузлів входу:
слухач на loopback — вузол досяжний, закритий порт — нема. Мережі й теки обгортки не чіпає: усе в тимчасовій теці. #>
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'
$script:Failures = 0
$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('m9an-' + [guid]::NewGuid().ToString('N'))
[void][System.IO.Directory]::CreateDirectory($tmpRoot)
$utf = New-Object System.Text.UTF8Encoding($false)
$python = (Get-Command python).Source
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'fake_health.py') -Destination (Join-Path $tmpRoot 'fake_health.py')
[System.IO.File]::WriteAllText((Join-Path $tmpRoot 'agy.cmd'), ('@"' + $python + '" "' + $tmpRoot + '\fake_health.py" agy %*' + "`r`n"), $utf)

function Check([string]$Name, [bool]$Ok) {
    if ($Ok) { Write-Output "✓ $Name" } else { Write-Output "✗ $Name"; $script:Failures++ }
}
function New-LocalPort {
    <# Вільний порт loopback: слухач піднято — повертає слухача; зупинений слухач лишає порт закритим. #>
    $l = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, 0)
    $l.Start()
    $l
}
function Alerts([string]$Dir) { @(Get-ChildItem "$Dir/*.txt" -ErrorAction SilentlyContinue) }

$listener = New-LocalPort
$open = '127.0.0.1:' + $listener.LocalEndpoint.Port
$dead = New-LocalPort; $closed = '127.0.0.1:' + $dead.LocalEndpoint.Port; $dead.Stop()
$text = "Error: authentication required. Run 'agy' to log in."
try {
    # --- agy: /usage і шлях наряду (gemini_run.ps1) ---
    . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmpRoot/gem/runs" -OutDir "$tmpRoot/gem/out" -RepoDir $tmpRoot -AgyExe "$tmpRoot/agy.cmd" -LaneDir "$tmpRoot/lanes" -ProfileDir "$tmpRoot/profile"
    foreach ($dir in @($RunsDir, $OutDir, $LaneDir)) { [void][System.IO.Directory]::CreateDirectory($dir) }
    $script:StateDir = Join-Path $RunsDir 'state'; [void][System.IO.Directory]::CreateDirectory($script:StateDir)
    $script:SlotDir = Join-Path $RunsDir 'slots'; [void][System.IO.Directory]::CreateDirectory($script:SlotDir)
    $script:HealthAlertDir = Join-Path $OutDir 'alerts'
    $script:Agy = "$tmpRoot/agy.cmd"
    $script:Limits = $null
    $env:FAKE_HEALTH_MODE = ''
    [void](Update-UsageCache)

    $env:FAKE_HEALTH_MODE = 'agy_login'
    $script:EngineAuthHosts['agy'] = $closed; $script:EngineAuthHosts['codex'] = $closed
    [void](Update-UsageCache)
    $log = Get-Content "$RunsDir/wrapper.log" -Encoding UTF8 -Raw
    Check 'вузол входу agy недосяжний: тривоги AUTH нема' (@(Alerts "$OutDir/alerts").Count -eq 0)
    Check 'журнал проби квоти: код, NETWORK і початок тексту рушія' ($log -match "квота: agy /usage -> 1 \(NETWORK\): $([regex]::Escape($text))")
    Check 'Get-ErrorCode: недосяжний вузол — NETWORK' ((Get-ErrorCode $text) -ceq 'NETWORK' -and (Get-ErrorCode $text 'codex') -ceq 'NETWORK')
    Check 'NETWORK — код кінця без звіту: текст рушія йде в причину' ('NETWORK' -in $script:EngineErrorCodes -and $script:CauseOfCode.ContainsKey('NETWORK'))

    $script:EngineAuthHosts['agy'] = $open
    [void](Update-UsageCache)
    $log = Get-Content "$RunsDir/wrapper.log" -Encoding UTF8 -Raw
    $files = @(Alerts "$OutDir/alerts")
    Check 'вузол входу agy досяжний: «ТРИВОГА AUTH AGY» лишається' ($files.Count -eq 1 -and (Get-Content $files[0].FullName -Encoding UTF8 -Raw).Trim() -ceq 'GEMINI ОБГОРТКА: ТРИВОГА AUTH AGY')
    Check 'журнал: досяжний вузол — код AUTH і той самий початок тексту' ($log -match "квота: agy /usage -> 1 \(AUTH\): $([regex]::Escape($text))")
    Check 'Get-ErrorCode: досяжний вузол — AUTH' ((Get-ErrorCode $text) -ceq 'AUTH')

    # codex ходить до свого вузла: недосяжний agy-вузол за досяжного codex-вузла NETWORK не дає.
    $script:EngineAuthHosts['agy'] = $closed; $script:EngineAuthHosts['codex'] = $open
    Check 'вузол свого рушія: codex досяжний — AUTH, хоч вузол agy закритий' ((Get-ErrorCode 'Not logged in' 'codex') -ceq 'AUTH')
    $script:EngineAuthHosts['codex'] = $closed
    Check 'codex недосяжний — NETWORK' ((Get-ErrorCode 'Not logged in' 'codex') -ceq 'NETWORK')

    # --- claude: шлях наряду (claude_run.ps1), власні визначення — в дочірньому блоці ---
    & {
        . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$tmpRoot/cr" -RepoDir $tmpRoot -OutboxDir "$tmpRoot/cbox" -PublishDir "$tmpRoot/pub" -GeminiOutDir "$tmpRoot/gout" -LaneDir "$tmpRoot/lanes" -TmpDir "$tmpRoot/ctmp" -NoStatus
        $script:EngineAuthHosts['claude'] = $closed
        Check 'claude: «Not logged in» без вузла входу — NETWORK, не AUTH' ((Get-ErrorCode 'Not logged in · Please run /login') -ceq 'NETWORK')
        $script:EngineAuthHosts['claude'] = $open
        Check 'claude: вузол входу досяжний — AUTH' ((Get-ErrorCode 'Not logged in · Please run /login') -ceq 'AUTH')
        Check 'claude: клас NETWORK за текстом мережі лишився' ((Get-ErrorCode 'getaddrinfo ENOTFOUND api.anthropic.com') -ceq 'NETWORK')
    }

    # --- публікатор знає код NETWORK, і рядок «ЗАБЛОКОВАНО … NETWORK» не тихий ---
    $pub = Get-Content (Join-Path $SourceDir 'gemini_publish.ps1') -Encoding UTF8 -Raw
    Check 'публікатор: NETWORK у RunCodes; тихі коди лишились NETWORK_WAIT тощо' ($pub -cmatch '(?m)^\s+NETWORK = ' -and $pub -cmatch [regex]::Escape("QuietBlockedCodes = '^(?:STALE|REVIEW_API|EMPTY_PLAN|NETWORK_WAIT|CANCELLED)`$'"))
} finally {
    $listener.Stop()
    # Видаляється лише створена цим стендом тека, після перевірки абсолютного шляху.
    $resolved = [System.IO.Path]::GetFullPath($tmpRoot)
    $parent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolved.StartsWith($parent, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolved -Leaf) -like 'm9an-*') {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
if ($script:Failures) { exit 1 }
Write-Output 'ВСЕ ✓'
