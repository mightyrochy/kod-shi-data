#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir, [ValidateSet('ДО','ПІСЛЯ')][string]$Phase='ПІСЛЯ')
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('tykhi-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Вимір повертає ненульовий код при порушенні договору. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutboxDir "$tmp/out" -SendRetries 1 -SendRetryDelaySeconds 0
    foreach ($dir in @($WorkDir,"$WorkDir/state","$WorkDir/seen",$OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $script:CloudCalls = 0; $script:FallbackCalls = 0; $script:Letters = @()
    $script:FailCloud = $false; $script:FailFallback = $false; $script:AddDuringSend = $false
    function Get-DispatcherId { 'session_test' }
    function Resolve-Exe([string]$Name) { $Name }
    function Invoke-Native($Exe,$Argv,$Cwd,$Seconds,$Stdin) {
        <# Лише транспорт підмінено: приймання файлів, політика й стан доставки справжні. #>
        if ($Exe -eq $ClaudeExe) {
            $script:CloudCalls++; $script:Letters += $Stdin
            if ($script:AddDuringSend) {
                $script:AddDuringSend = $false
                Save-LocalLine 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/нова-подія STALE'
            }
            return [pscustomobject]@{Code=0;Out=$(if ($script:FailCloud) {'{"ok":false}'} else {'{"ok":true}'});Err=''}
        }
        $script:FallbackCalls++; $script:Letters += (ConvertFrom-Json $Stdin).body
        [pscustomobject]@{Code=0;Out=$(if ($script:FailFallback) {'{}'} else {'{"id":123}'});Err=''}
    }
    if ($Phase -ceq 'ПІСЛЯ') {
        Write-FileAtomic "$WorkDir/local-lines.json" '[]'
        Check 'порожній попередній журнал сумісний' (@(Get-LocalSummary).Count -eq 0)
    }
    $script:EventNumber = 0
    function Deliver([string]$Line) {
        <# Подія проходить атомарний файл вихідних, приймання й збережену доставку. #>
        $script:EventNumber++
        $name = '20261029-000000-{0:x12}.txt' -f $script:EventNumber
        Write-FileAtomic (Join-Path $OutboxDir $name) $Line
        Receive-Outbox
        $file = Get-Item (Join-Path "$WorkDir/state" "o-$($name.Substring(0,$name.Length-4)).json")
        Send-Pending $file
        ConvertFrom-Json ([IO.File]::ReadAllText($file.FullName))
    }
    $facts = @(
        'gemini/автоперевірка-2122','gemini/автоперевірка-2122','gemini/автоперевірка-2122',
        'gemini/автоперевірка-2124','gemini/автоперевірка-2124','gemini/автоперевірка-2124',
        'gemini/автоперевірка-2132','gemini/автоперевірка-2133',
        'claude/1974','claude/1977','claude/1975','claude/1981','claude/1983','claude/1985'
    )
    foreach ($branch in $facts) { $null = Deliver "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО $branch STALE" }
    "ВИМІР $Phase : 14 фактів, пробуджень $script:CloudCalls"
    Check '14 фактів через доставку' ($script:CloudCalls -eq $(if ($Phase -ceq 'ДО') {14} else {0}))
    $wake = 'GEMINI ОБГОРТКА: ГОТОВО gemini/перевірка-коду ' + ('a' * 40)
    $null = Deliver $wake
    Check 'наступний дієвий рядок — одне пробудження' ($script:CloudCalls -eq $(if ($Phase -ceq 'ДО') {15} else {1}))
    Check 'перший рядок листа незмінний' (($script:Letters[-1] -split "`n")[0] -ceq $wake)
    if ($Phase -ceq 'ПІСЛЯ') {
        Check 'лист несе зведення 14 і повтори ×3' ($script:Letters[-1].Contains('ЗВЕДЕННЯ ЛОКАЛЬНИХ РЯДКІВ: 14') -and $script:Letters[-1].Contains('3 × GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/автоперевірка-2122 STALE'))
        Check 'усі 14 позначені доставленими' (@(Get-LocalSummary).Count -eq 0 -and @(Get-LocalLines).Count -eq 14)
        $null = Deliver $wake
        Check 'зведення не повторюється' ($script:Letters[-1] -ceq $wake)
        foreach ($code in @($script:RunCodes.Keys) + @($script:IsolationChecks.Keys) + @($script:PublishCodes.Keys)) {
            $expected = $code -cnotin @('STALE','REVIEW_API','QUOTA_ZERO','EMPTY')
            Check "код $code класифіковано явно" ($script:DispatcherBlockActions.ContainsKey($code) -and (Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/крок $code") -eq $expected)
        }
        foreach ($code in @('QUOTA0_CODEX_M60','QUOTA0_CLAUDE_M60','QUOTA0_AGY','QUOTA0_GEMINI_M123456')) {
            Check "$code — зведення" (-not (Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/крок $code"))
        }
        foreach ($code in @('NEW_CODE','FUTURE','QUOTA','PUSH_FAILED','NO_HEAD_PUBLISHED','STALE_PUBLISHED','QUOTA0_CODEX_M60_PUBLISHED','BOOT','NO_PUSH','BAD_BRANCH')) {
            Check "$code — дія диспетчера" (Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/крок $code")
        }
        foreach ($line in @(
            'GEMINI ОБГОРТКА: ТРИВОГА AUTH CODEX','GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API',
            ('GEMINI ОБГОРТКА: ГОТОВО claude/pachka-1 ' + ('a'*40)),
            ('GEMINI ОБГОРТКА: ГОТОВО codex/автоживий-штамп ' + ('a'*40)))) {
            Check 'вердикт, живий чи тривога будить' (Test-DispatcherAction $line)
        }
        $before = $script:CloudCalls
        $local = Deliver 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/квота QUOTA0_CODEX_M60'
        Check 'квота без спроб мережі, стан локальний' ($script:CloudCalls -eq $before -and $local.sent -and $local.attempts -eq 0 -and $local.channel -ceq 'local')
        $script:FailCloud = $true
        $null = Deliver $wake
        Check 'відмова не підтверджує зведення' (@(Get-LocalSummary).Count -eq 1)
        $script:FailCloud = $false; $script:CloudUnavailable = $false
        $null = Deliver $wake
        Check 'наступний лист повторює недоставлене' ($script:Letters[-1].Contains('QUOTA0_CODEX_M60') -and @(Get-LocalSummary).Count -eq 0)
        # Міграція попереднього формату і відсів тексту, який не є службовим рядком.
        Write-FileAtomic "$WorkDir/local-lines.json" (ConvertTo-Json -InputObject @(
            @{utc='2026-10-28T00:00:00Z';line='GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/старий STALE'},
            @{utc='2026-10-28T00:00:01Z';line="текст агента`nне передавати"}))
        $script:FailFallback = $true
        Check 'резервний канал без id не підтверджує' (-not (Send-Fallback $wake) -and @(Get-LocalSummary).Count -eq 1)
        $script:FailFallback = $false
        Check 'резервний канал доставив старий формат' ((Send-Fallback $wake) -and @(Get-LocalSummary).Count -eq 0)
        Check 'резервний лист: перший рядок і лише службові дані' (($script:Letters[-1] -split "`n")[0] -ceq $wake -and $script:Letters[-1].Contains('ЗВЕДЕННЯ ЛОКАЛЬНИХ РЯДКІВ: 1') -and -not $script:Letters[-1].Contains('текст агента'))
        for ($i=0; $i -lt 40; $i++) { Save-LocalLine 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/повтор STALE' }
        Check '40 однакових недоставлених не обрізано до 32' (@(Get-LocalSummary).Count -eq 40)
        $script:AddDuringSend = $true
        $null = Send-Line $wake
        Check 'підтверджено лише 40 зі знімка, нова подія лишилась' ($script:Letters[-1].Contains('ЗВЕДЕННЯ ЛОКАЛЬНИХ РЯДКІВ: 40') -and @(Get-LocalSummary).Count -eq 1)
        # Збережений стан повтору сам переходить на резервний канал і не губить зведення.
        $script:CloudUnavailable = $true
        $file = Join-Path "$WorkDir/state" 'aged.json'
        Write-FileAtomic $file ((@{line=$wake;sent=$false;attempts=1;first_failure_utc=[datetimeoffset]::UtcNow.AddMinutes(-11).ToString('o')}) | ConvertTo-Json)
        Send-Pending (Get-Item $file)
        $st = ConvertFrom-Json ([IO.File]::ReadAllText($file))
        Check 'Send-Pending: резерв із підтвердженням і зведенням' ($st.sent -and $st.channel -ceq 'gh' -and @(Get-LocalSummary).Count -eq 0)
    }
} catch { Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    if ($resolved.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath())) -and (Split-Path $resolved -Leaf).StartsWith('tykhi-test-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
"ПІДСУМОК: ✗ $bad"
exit ([int]($bad -gt 0))

