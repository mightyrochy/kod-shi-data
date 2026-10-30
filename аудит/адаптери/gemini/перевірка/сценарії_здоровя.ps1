#Requires -Version 5.1
<# Стенд тривог, резерву й свіжості з підробними CLI. Мережу й задачі ноутбука не зачіпає. #>
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot), [switch]$Before)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'; $env:PYTHONIOENCODING = 'utf-8'
$script:Failures = 0
$tmpRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('m9zh-' + [guid]::NewGuid().ToString('N'))
[void][System.IO.Directory]::CreateDirectory($tmpRoot)
$utf = New-Object System.Text.UTF8Encoding($false)
$python = (Get-Command python).Source
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'fake_health.py') -Destination (Join-Path $tmpRoot 'fake_health.py')
foreach ($role in @('git', 'gh', 'claude', 'agy', 'sleep')) {
    [System.IO.File]::WriteAllText((Join-Path $tmpRoot "$role.cmd"), ('@"' + $python + '" "' + $tmpRoot + '\fake_health.py" ' + $role + ' %*' + "`r`n"), $utf)
}
$env:FAKE_HEALTH_GH_LOG = Join-Path $tmpRoot 'gh.log'

function Check([string]$Name, [bool]$Ok) {
    <# Друкує результат; увесь стенд червоніє від будь-якого провалу. #>
    if ($Ok) { Write-Output "✓ $Name" } else { Write-Output "✗ $Name"; $script:Failures++ }
}
function Put-Line([string]$Dir, [string]$Line) {
    <# Атомарно готовий файл вихідних з унікальним службовим ім'ям. #>
    [void][System.IO.Directory]::CreateDirectory($Dir)
    $name = '20261027-180000-' + [guid]::NewGuid().ToString('N').Substring(0, 12) + '.txt'
    [System.IO.File]::WriteAllText((Join-Path $Dir $name), $Line + "`n", $utf)
}
function Publish([string]$Case, [int]$Limit = 4, [int]$Fallback = 2) {
    <# Справжній Main публікатора; усі зовнішні процеси — заглушки з ASCII-теки. #>
    $dir = Join-Path $tmpRoot $Case
    $params = @{ WorkDir = "$dir/pub"; OutDir = "$dir/out"; OutboxDir = "$dir/box"; UpdateRoot = "$dir/update"; GitExe = "$tmpRoot/git.cmd"; ClaudeExe = "$tmpRoot/claude.cmd"; SendRetryDelaySeconds = 0; SendRetries = 1; MaxSendAttempts = $Limit }
    if (-not $Before) { $params.GhExe = "$tmpRoot/gh.cmd"; $params.MaxFallbackAttempts = $Fallback }
    . (Join-Path $SourceDir 'gemini_publish.ps1') @params
    function Test-OwnerUser { $true }
    $code = Main
    Check "$Case Main завершився успішно" ($code -eq 0)
    if ($code -ne 0) { Get-Content "$dir/pub/publish.log" -Encoding UTF8 | Select-Object -Last 2 }
}
function States([string]$Case) {
    <# Усі збережені стани доставки цього випадку. #>
    @(Get-ChildItem "$tmpRoot/$Case/pub/state/*.json" | ForEach-Object { Get-Content $_.FullName -Encoding UTF8 -Raw | ConvertFrom-Json })
}
function Comments {
    <# Лише POST коментарів; PATCH стану не є доставкою рядка. #>
    if (Test-Path $env:FAKE_HEALTH_GH_LOG) {
        @(Get-Content $env:FAKE_HEALTH_GH_LOG -Encoding UTF8 | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $_.args -contains 'POST' })
    }
}

try {
    $line = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/проба CRASH'
    $env:FAKE_HEALTH_MODE = '401'
    Put-Line "$tmpRoot/auth/box" $line
    Publish 'auth'
    if ($Before) {
        Check 'ДО: 401 — коментарів #1690 немає, рядок не доставлено' (@(Comments).Count -eq 0 -and -not (States 'auth').sent)
        . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmpRoot/gem/runs" -OutDir "$tmpRoot/gem/out" -RepoDir $tmpRoot -LaneDir "$tmpRoot/lanes" -ProfileDir "$tmpRoot/profile"
        foreach ($dir in @($RunsDir, $OutDir, $LaneDir)) { [void][System.IO.Directory]::CreateDirectory($dir) }
        $script:Limits = $null
        $env:FAKE_HEALTH_MODE = 'agy_auth'
        $r = Invoke-Native "$tmpRoot/agy.cmd" @('-p', '/usage') '' 0.1
        [void](Get-ErrorCode ($r.Out + $r.Err))
        Check 'ДО: agy без входу — тривог немає' (@(Get-ChildItem "$OutDir/alerts/*.txt" -ErrorAction SilentlyContinue).Count -eq 0)
        Write-Heartbeat ''
        $hb = Get-Content "$OutDir/heartbeat.json" -Encoding UTF8 -Raw | ConvertFrom-Json
        Check 'ДО: heartbeat не має часу зчитування UTC' ($null -eq $hb.PSObject.Properties['read_utc'])
        if ($script:Failures) { exit 1 }
        if ($script:Failures) { exit 1 }
        return
    }
    $comments = @(Comments)
    Check '401: той самий рядок і тривога CLOUD у #1690 негайно' ($comments.Count -eq 2 -and $comments.body.body -contains $line -and $comments.body.body -contains 'GEMINI ОБГОРТКА: ТРИВОГА AUTH CLOUD' -and @($comments | Where-Object { $_.args -notcontains 'repos/mightyrochy/kod-shi-data/issues/1690/comments' }).Count -eq 0)
    Publish 'auth'
    Check 'повторний запуск не дублює доставленого' (@(Comments).Count -eq 2)
    Put-Line "$tmpRoot/auth/box" ($line -replace 'CRASH', 'TIMEOUT')
    Publish 'auth'
    Check 'нова подія не дублює ту саму тривогу протягом години' (@(Comments).Count -eq 3)

    $env:FAKE_HEALTH_MODE = 'fail'
    Put-Line "$tmpRoot/delay/box" $line
    Publish 'delay' 1
    Check 'до 10 хв запасний канал мовчить' (@(Comments).Count -eq 3)
    $sf = Get-ChildItem "$tmpRoot/delay/pub/state/*.json" | Select-Object -First 1
    $s = Get-Content $sf.FullName -Encoding UTF8 -Raw | ConvertFrom-Json
    $s.first_failure_utc = [DateTimeOffset]::UtcNow.AddMinutes(-11).ToString('o')
    [System.IO.File]::WriteAllText($sf.FullName, ($s | ConvertTo-Json -Compress), $utf)
    Publish 'delay' 1
    Check 'після 10 хв gh доставляє і після вичерпання спроб claude' ((States 'delay').sent -eq $true -and (States 'delay').channel -eq 'gh' -and @(Comments).Count -eq 4)

    $env:FAKE_HEALTH_MODE = 'both_fail'
    Put-Line "$tmpRoot/exhaust/box" $line
    Publish 'exhaust' 1 1
    $sf = Get-ChildItem "$tmpRoot/exhaust/pub/state/*.json" | Select-Object -First 1
    $s = Get-Content $sf.FullName -Encoding UTF8 -Raw | ConvertFrom-Json
    $s.first_failure_utc = [DateTimeOffset]::UtcNow.AddMinutes(-11).ToString('o')
    [System.IO.File]::WriteAllText($sf.FullName, ($s | ConvertTo-Json -Compress), $utf)
    Publish 'exhaust' 1 1
    $s = States 'exhaust'
    $summary = Get-Content "$tmpRoot/exhaust/pub/delivery.json" -Encoding UTF8 -Raw | ConvertFrom-Json
    Check 'вичерпані спроби: рядок, стан, підсумок і журнал збережено' (-not $s.sent -and $s.exhausted -and $s.line -eq $line -and $summary.exhausted -eq 1 -and (Select-String -LiteralPath "$tmpRoot/exhaust/pub/publish.log" -Pattern 'спроби доставки вичерпано' -Quiet))
    $count = @(Comments).Count
    Publish 'exhaust' 1 1
    Check 'після вичерпання спроб немає нових викликів gh' (@(Comments).Count -eq $count)

    $env:FAKE_HEALTH_MODE = 'string'
    Put-Line "$tmpRoot/ack/box" $line
    Publish 'ack'
    Check 'рядкове ok замість булевого true не підтверджує доставку' (-not (States 'ack').sent)

    $env:FAKE_HEALTH_MODE = 'ok401'
    Put-Line "$tmpRoot/response/box" $line
    Publish 'response'
    Check '401 у відповіді з успішним ok не стає тривогою з тексту агента' ((States 'response').sent -and @(States 'response').Count -eq 1)

    . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmpRoot/gem/runs" -OutDir "$tmpRoot/gem/out" -RepoDir $tmpRoot -AgyExe "$tmpRoot/agy.cmd" -LaneDir "$tmpRoot/lanes" -ProfileDir "$tmpRoot/profile"
    foreach ($dir in @($RunsDir, $OutDir, $LaneDir)) { [void][System.IO.Directory]::CreateDirectory($dir) }
    $script:StateDir = Join-Path $RunsDir 'state'; [void][System.IO.Directory]::CreateDirectory($script:StateDir)
    $script:SlotDir = Join-Path $RunsDir 'slots'; [void][System.IO.Directory]::CreateDirectory($script:SlotDir)
    $script:HealthAlertDir = Join-Path $OutDir 'alerts'
    $script:Agy = "$tmpRoot/agy.cmd"
    $env:FAKE_HEALTH_MODE = ''
    $c = Update-UsageCache
    $u = ConvertFrom-UsageText $c.text $c.time
    Check 'JSON agy: групи успадковано, 4 вікна, 92/100/50/0 %, UTC; response ігнорується' ($u.Known -and $u.Windows.Count -eq 4 -and ($u.Windows.Left -join ',') -eq '92,100,50,0' -and $u.Windows[0].Name -eq 'Gemini Models' -and $u.Windows[0].Reset.UtcDateTime.ToString('s') -eq '2026-11-02T22:01:25')
    $env:FAKE_HEALTH_MODE = 'agy_auth'
    [void](Update-UsageCache)
    # Відмова /usage є тим самим виробничим шляхом, що відмова входу перед нарядом.
    Check 'agy без входу створює тривогу AUTH AGY без виводу CLI' (@(Get-ChildItem "$OutDir/alerts/*.txt").Count -eq 1 -and (Get-Content (Get-ChildItem "$OutDir/alerts/*.txt")[0].FullName -Encoding UTF8 -Raw).Trim() -eq 'GEMINI ОБГОРТКА: ТРИВОГА AUTH AGY')
    [void](Get-ErrorCode '401' 'codex')
    Write-IsolationStatus 'ENV'
    Add-HealthException (New-Object System.IO.IOException('довільний текст', -2147024784))
    Check 'окремі тривоги Codex, ізоляції й диска' (@(Get-ChildItem "$OutDir/alerts/*.txt").Count -eq 4)
    Add-HealthAlert 'AUTH' 'AGY'
    Check 'повтор AUTH AGY раніше години придушено' (@(Get-ChildItem "$OutDir/alerts/*.txt").Count -eq 4)
    [System.IO.File]::WriteAllText("$OutDir/alerts/.AUTH-AGY.utc", [string]([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 3601), $utf)
    Add-HealthAlert 'AUTH' 'AGY'
    Check 'після години повтор дозволено' (@(Get-ChildItem "$OutDir/alerts/*.txt").Count -eq 5)
    Check 'довільна деталь і невідомий код відкидаються' (-not (Test-HealthAlert 'GEMINI ОБГОРТКА: ТРИВОГА AUTH текст агента') -and -not (Test-HealthAlert 'GEMINI ОБГОРТКА: ТРИВОГА OTHER AGY'))
    [void][System.IO.Directory]::CreateDirectory("$tmpRoot/import/out/alerts")
    Copy-Item "$OutDir/alerts/*.txt" "$tmpRoot/import/out/alerts/"
    $env:FAKE_HEALTH_MODE = '401'
    Publish 'import'
    $imported = @(Comments)
    Check 'тривоги Gemini проходять перевірений шаблон і резерв; джерело обміну лишається тільки для читання' ($imported.body.body -contains 'GEMINI ОБГОРТКА: ТРИВОГА AUTH AGY' -and @(Get-ChildItem "$tmpRoot/import/out/alerts/*.txt").Count -eq 5)
    $importCount = @(Comments).Count
    Publish 'import'
    Check 'повторне читання теки Gemini не дублює тривог' (@(Comments).Count -eq $importCount)
    $script:Limits = @{ slots = @{ agy = 2; codex = 2 }; source = 'код' }
    $script:HeartbeatAction = { Write-Heartbeat '' }
    $script:LastHealthBeat = [datetime]::MinValue
    $env:FAKE_HEALTH_MODE = ''
    [void](Invoke-Native "$tmpRoot/sleep.cmd" @() '' 0.1)
    $beat = Get-Content "$OutDir/heartbeat.json" -Encoding UTF8 -Raw | ConvertFrom-Json
    Check 'gemini-run: під час очікування CLI пише UTC, смуги й слоти' ($beat.read_utc -match 'Z$' -and $beat.lanes.Count -eq 2)

    $gemOut = $OutDir
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$tmpRoot/owner" -RepoDir $tmpRoot -GeminiOutDir $gemOut -PublishDir "$tmpRoot/exhaust/pub" -GhExe "$tmpRoot/gh.cmd" -LaneDir "$tmpRoot/lanes"
    foreach ($dir in @($WorkDir, $LaneDir)) { [void][System.IO.Directory]::CreateDirectory($dir) }
    $script:StateDir = Join-Path $WorkDir 'state'; [void][System.IO.Directory]::CreateDirectory($script:StateDir)
    $script:SlotDir = Join-Path $WorkDir 'slots'; [void][System.IO.Directory]::CreateDirectory($script:SlotDir)
    function Get-TaskRows { @() }
    $script:Limits = @{ slots = @{ claude = 2 }; source = 'код' }
    $script:HeartbeatAction = { Update-Status }
    $script:LastHealthBeat = [datetime]::MinValue
    [void](Invoke-Native "$tmpRoot/sleep.cmd" @() '' 0.1)
    $owner = Get-Content "$WorkDir/heartbeat.json" -Encoding UTF8 -Raw | ConvertFrom-Json
    Check 'claude-run: під час очікування CLI пише UTC й публікує стан через gh PATCH' ($owner.read_utc -match 'Z$' -and (Select-String $env:FAKE_HEALTH_GH_LOG -Pattern 'PATCH' -Quiet))
    $beat.read_utc = [datetime]::UtcNow.AddMinutes(-6).ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
    [System.IO.File]::WriteAllText("$gemOut/heartbeat.json", ($beat | ConvertTo-Json -Depth 8), $utf)
    $body = Get-StatusBody
    Check 'зупинене джерело: за зсуву часу на 6 хв вік >5; свіжа задача власника не освіжає його' ($body -match 'вік: 6 хв' -and $body -match 'джерело застаріле' -and (Read-GeminiBeat).Time -eq $beat.read_utc)
    Check 'стан ноутбука показує вичерпану доставку' ($body -match 'спроби вичерпано 1')
} finally {
    # Видаляється лише створена цим стендом тека, після перевірки абсолютного шляху.
    $resolved = [System.IO.Path]::GetFullPath($tmpRoot)
    $parent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolved.StartsWith($parent, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolved -Leaf) -like 'm9zh-*') {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
if ($script:Failures) { exit 1 }
Write-Output 'ВСЕ ✓'
