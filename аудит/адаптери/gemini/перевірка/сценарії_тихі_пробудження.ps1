#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('tykhi-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutboxDir "$tmp/out"
    foreach ($dir in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $sha = 'a' * 40
    $script:Calls = @()
    function Get-DispatcherId { 'session_test' }
    function Resolve-Exe { 'test-native' }
    function Invoke-Native {
        param($Exe, $Arguments, $WorkDirectory, $TimeoutMinutes, $StdIn)
        $script:Calls += , [string]$StdIn
        [pscustomobject]@{Code = 0; Out = '{"ok":true}'; Err = ''}
    }
    function Reset-Run {
        $script:Calls = @()
        foreach ($f in @(Get-ChildItem "$WorkDir/state" -File -ErrorAction SilentlyContinue)) { Remove-Item -LiteralPath $f.FullName -Force }
        Remove-Item -LiteralPath "$WorkDir/local-lines.json" -Force -ErrorAction SilentlyContinue
    }
    function Deliver([string[]]$Lines) {
        <# Рядок проходить справжню доставку: стан → Send-Pending. #>
        foreach ($l in $Lines) {
            $path = "$WorkDir/state/{0:D4}.json" -f ($script:Seq++)
            Write-FileAtomic $path ((@{line = $l; sent = $false; attempts = 0}) | ConvertTo-Json -Compress)
            Send-Pending (Get-Item $path)
        }
    }
    $script:Seq = 1

    # Факти 28–29.10: 14 рядків STALE за автоперевірками й пачкою.
    $facts = @('автоперевірка-2122-aaa', 'автоперевірка-2122-bbb', 'автоперевірка-2122-ccc', 'автоперевірка-2124-aaa', 'автоперевірка-2124-bbb',
        'автоперевірка-2124-ccc', 'автоперевірка-2132-aaa', 'автоперевірка-2133-aaa') | ForEach-Object { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/$_ STALE" }
    $facts += @(1974, 1977, 1975, 1981, 1983, 1985) | ForEach-Object { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/автоперевірка-$_-aaa STALE" }
    $quota = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО codex/крок QUOTA0_CODEX_M60'
    $wake = "GEMINI ОБГОРТКА: ГОТОВО gemini/автоперевірка-9-$sha $sha"

    Scenario '1 закритий перелік кодів' {
        # Усі коди з $script:RunCodes, $script:IsolationChecks, кодів публікації та службових рядків.
        $quiet = @('STALE', 'REVIEW_API')
        foreach ($code in @($script:RunCodes.Keys | Where-Object { $_ -notin @('QUOTA_ZERO', 'DONE', 'BLOCKED') })) {
            $want = $code -notin $quiet
            Check "1 $code — $(if ($want) { 'будить' } else { 'зведення' })" ((Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/крок $code") -eq $want)
        }
        foreach ($code in @('BLOCKED', 'DONE_PUBLISHED', 'BLOCKED_PUBLISHED', 'NO_HEAD_PUBLISHED', 'STATE_INVALID', 'ISOLATION_FAILED', 'BOOT', 'НЕВІДОМИЙ')) {
            Check "1 $code — будить" (Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/крок $code")
        }
        foreach ($code in @($script:PublishCodes.Keys)) { Check "1 публікація $code — будить" (Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/крок $code") }
        foreach ($code in @('QUOTA0_CODEX_M60', 'QUOTA0_CLAUDE_M5', 'QUOTA0_GPT', 'QUOTA0_A1_M0')) {
            Check "1 $code — зведення" (-not (Test-DispatcherAction "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/крок $code"))
        }
        Check '1 нерозібраний ЗАБЛОКОВАНО будить' (Test-DispatcherAction 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО')
        Check '1 STALE із зайвим словом у рядку будить' (Test-DispatcherAction 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/крок X STALE')
        Check '1 ТРИВОГА будить' (Test-DispatcherAction 'GEMINI ОБГОРТКА: ТРИВОГА AUTH CLOUD')
        Check '1 ЛАНЦЮГ будить' (Test-DispatcherAction 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API')
        foreach ($kind in @('перевірка-12', 'pachka-3', 'автоживий-штамп', 'автоперевірка-9', 'Е1-нічний-живий-1')) {
            Check "1 ГОТОВО $kind — будить" (Test-DispatcherAction "GEMINI ОБГОРТКА: ГОТОВО gemini/$kind $sha")
        }
        Check '1 ГОТОВО виконавця — зведення' (-not (Test-DispatcherAction "GEMINI ОБГОРТКА: ГОТОВО gemini/крок $sha"))
    }
    Scenario '2 проба: 14 рядків фактів — пробуджень' {
        Reset-Run
        Deliver ($facts)
        Check "2 факти: рядків $($facts.Count)" ($facts.Count -eq 14)
        Check "2 пробуджень диспетчера: $($script:Calls.Count) (ДО 14 → ПІСЛЯ 0)" ($script:Calls.Count -eq 0)
        $stored = @(ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/local-lines.json")))
        Check '2 усі 14 лишились у local-lines.json' ($stored.Count -eq 14)
        Deliver @($quota)
        Check '2 QUOTA0 теж без пробудження' ($script:Calls.Count -eq 0)
    }
    Scenario '3 рядок, що будить, — одне пробудження зі зведенням' {
        Reset-Run
        Deliver ($facts)
        Deliver @($wake)
        Check "3 пробуджень: $($script:Calls.Count) (рівно 1)" ($script:Calls.Count -eq 1)
        if ($script:Calls.Count -ge 1) {
            $parts = $script:Calls[0] -split "`n"
            Check '3 перший рядок листа не змінений' ($parts[0] -ceq $wake)
            Check '3 зведення: 14 і 14 рядків' ($parts[1] -ceq 'ЗВЕДЕННЯ БЕЗ ПРОБУДЖЕННЯ: 14' -and $parts.Count -eq 16)
            Check '3 рядки зведення — це рядки фактів' ((($parts[2..15]) -join "`n") -ceq ($facts -join "`n"))
        }
        $stored = @(ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/local-lines.json")))
        Check '3 накопичене позначено доставленим' (@($stored | Where-Object { $_.delivered -ne $true }).Count -eq 0)
        Deliver @($wake)
        Check '3 наступний рядок, що будить, — без повторного зведення' ($script:Calls.Count -eq 2 -and $script:Calls[1] -ceq $wake)
        Deliver @($facts[0])
        Deliver @($wake)
        Check '3 нове накопичене — нове зведення з 1' ($script:Calls.Count -eq 3 -and ($script:Calls[2] -split "`n")[1] -ceq 'ЗВЕДЕННЯ БЕЗ ПРОБУДЖЕННЯ: 1')
    }
    Scenario '4 недоставлене зведення не губиться' {
        Reset-Run
        Deliver ($facts)
        function Invoke-Native { param($Exe, $Arguments, $WorkDirectory, $TimeoutMinutes, $StdIn) $script:Calls += , [string]$StdIn; [pscustomobject]@{Code = 1; Out = ''; Err = 'збій'} }
        $script:SendRetries = 1; $script:SendRetryDelaySeconds = 0
        Deliver @($wake)
        $stored = @(ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/local-lines.json")))
        Check '4 збій доставки — зведення лишається недоставленим' (@($stored | Where-Object { $_.delivered -ne $true }).Count -eq 14)
    }
    Scenario '5 запасний канал теж несе зведення' {
        Reset-Run
        Deliver ($facts)
        $script:GhBodies = @()
        function Invoke-Native { param($Exe, $Arguments, $WorkDirectory, $TimeoutMinutes, $StdIn) $script:GhBodies += , [string]$StdIn; [pscustomobject]@{Code = 0; Out = '{"id":7}'; Err = ''} }
        Check '5 запасний канал підтверджено' (Send-Fallback $wake)
        $body = ($script:GhBodies[0] | ConvertFrom-Json).body
        Check '5 у тілі коментаря — основний рядок і зведення 14' (($body -split "`n")[0] -ceq $wake -and ($body -split "`n")[1] -ceq 'ЗВЕДЕННЯ БЕЗ ПРОБУДЖЕННЯ: 14')
        Check '5 локальний рядок через запасний канал — лише в зведення' (Send-Fallback $facts[0])
    }
} finally {
    $script:CloudUnavailable = $false
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
if ($bad) { "ПІДСУМОК: ✗ $bad"; exit 1 }
'ПІДСУМОК: ✗ 0'
exit 0
