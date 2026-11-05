#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot), [switch]$Before, [string]$EvidenceDir = '')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Utf8 = New-Object Text.UTF8Encoding($false)
$errors = $null; $tokens = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'claude_run.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
. (Join-Path $SourceDir 'queue_lanes.ps1')
$names = @('Remove-ReportDecoration', 'Get-Report', 'Get-ClaudeText', 'Get-ClaudeReport', 'Read-ClaudeEvent', 'Protect-ClaudeText', 'Save-ClaudeNoReport', 'Get-ClaudeNoReportLines', 'Get-ErrorCode', 'Invoke-ClaudeTask')
foreach ($name in $names) {
    $node = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    if ($node) { . ([scriptblock]::Create($node.Extent.Text)) }
}
$script:bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Невиконане твердження дає ненульовий код у кінці всього стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Get-Prompt { 'синтетичний наряд' }
function Write-Log { param($Text) }
function Get-BranchPath { param($Slug) Join-Path $WorkDir 'branch.txt' }
function Get-RemoteSha { param($Branch) if ($Branch -eq 'claude/проба-звіту') { $script:remote } else { '' } }
function Test-ClaudeBranch { param($Branch) $Branch -cmatch '^claude/[\p{L}\p{Nd}._-]+$' }
function Complete-Task {
    param($M, $StatePath, $Id, $Code, $Branch = '', $Sha = '')
    $script:completed = [pscustomobject]@{ Code = $Code; Branch = $Branch; Sha = $Sha }
}
function Enter-ClaudeQuotaWait { $false }
function Invoke-Claude { $script:response }
$WorkDir = Join-Path $env:TEMP ('no-report-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($WorkDir)
$runDir = Join-Path $WorkDir 'run'
[void][IO.Directory]::CreateDirectory($runDir)
$script:remote = 'a' * 40
$branch = 'claude/проба-звіту'
$line = "НОУТБУК ГОТОВО $branch $script:remote"
$script:SlugCore = '[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}'
$m = [pscustomobject]@{ Name = 'gemini-queue/проба-звіту/cc-модель/1'; Slug = 'проба-звіту'; Claude = 'модель'; Effort = ''; Model = 'cc-модель' }
$job = [pscustomobject]@{ id = '20261030-120000-0123456789ab'; slot = 'claude-1' }
$cases = @(
    @('простий', $line, '', 'DONE'),
    @('жирний', "**$line**", '', 'DONE'),
    @('крапка', "$line.", '', 'DONE'),
    @('пояснення', "$line — виконано", '', 'DONE'),
    @('жирний-пояснення', "**$line — виконано**", '', 'DONE'),
    @('короткий-SHA', "НОУТБУК ГОТОВО $branch aaaaaaaa", '', 'DONE'),
    @('CRLF-пробіли', "$line   `r`n", '', 'DONE'),
    @('список', "- $line", '', 'DONE'),
    @('список-жирний', "- **$line**", '', 'DONE'),
    @('після-коду', ('```' + "`nкод`n" + '```' + "`n$line"), '', 'DONE'),
    @('після-наряду', "----- НАРЯД -----`nприклад`n----- КІНЕЦЬ НАРЯДУ -----`n$line", '', 'DONE'),
    @('порожній-result', '', $line, 'DONE'),
    @('null-result', $null, $line, 'DONE'),
    @('масив-result', @('не текст'), $line, 'DONE'),
    @('урізаний-result', "НОУТБУК ГОТОВО $branch aaaa", $line, 'DONE'),
    @('немає-події-result', '__відсутня__', $line, 'DONE'),
    @('без-звіту', 'Зроблено, без звіту.', 'працюю', 'NO_REPORT'),
    @('немає-відповіді', '', '', 'NO_REPORT'),
    @('приклад', "Приклад:`n$line", $line, 'NO_REPORT'),
    @('приклад-після-SHA', "$line — приклад", '', 'NO_REPORT'),
    @('код', ('```' + "`n$line`n" + '```'), $line, 'NO_REPORT'),
    @('цитата', "> $line", $line, 'NO_REPORT'),
    @('старий-assistant', 'Остаточна відповідь без звіту.', $line, 'NO_REPORT'),
    @('два-звіти', "$line`nНОУТБУК ЗАБЛОКОВАНО: причина", '', 'NO_REPORT'),
    @('чужа-гілка', ('НОУТБУК ГОТОВО main ' + $script:remote), '', 'BAD_BRANCH'),
    @('хибний-SHA', ('НОУТБУК ГОТОВО ' + $branch + ' ' + ('b' * 40)), '', 'NO_PUSH'),
    @('хибний-короткий-SHA', "НОУТБУК ГОТОВО $branch bbbbbbbb", '', 'NO_PUSH'),
    @('SHA-надто-короткий', "НОУТБУК ГОТОВО $branch aaa", '', 'NO_REPORT'),
    @('блокер', 'НОУТБУК ЗАБЛОКОВАНО: причина', '', 'BLOCKED'),
    @('блокер-без-префікса', 'ЗАБЛОКОВАНО: причина', '', 'NO_REPORT'),
    @('exit', '', '', 'EXIT')
)
if ($EvidenceDir) { [void][IO.Directory]::CreateDirectory($EvidenceDir) }
foreach ($case in $cases) {
    $script:response = [pscustomobject]@{ Code = 0; Kind = ''; Result = $null; AssistantText = $case[2]; Err = ''; Limit = $null }
    if ($case[0] -eq 'exit') { $script:response.Code = 3 }
    if ($case[0] -ne 'немає-події-result') { $script:response.Result = [pscustomobject]@{ type = 'result'; result = $case[1]; is_error = $false } }
    if ($EvidenceDir) {
        $record = [ordered]@{ name = $case[0]; response = $script:response; expected = $case[3] }
        [IO.File]::AppendAllText((Join-Path $EvidenceDir 'варіанти.jsonl'), ($record | ConvertTo-Json -Depth 8 -Compress) + "`n", $script:Utf8)
    }
    $script:completed = $null
    Invoke-ClaudeTask $m $job 'синтетичний' 'наряд' '' $runDir 'стан' $WorkDir
    $got = $script:completed.Code
    $expected = $case[3]
    if ($Before) {
        $expected = switch ($case[0]) {
            { $_ -in @('пояснення', 'жирний-пояснення', 'короткий-SHA', 'список', 'список-жирний', 'порожній-result', 'null-result', 'масив-result', 'урізаний-result', 'немає-події-result', 'хибний-короткий-SHA', 'блокер-без-префікса') } { 'NO_REPORT'; break }
            default { $case[3] }
        }
    }
    Check "$($case[0]): $got" ($got -ceq $expected)
    if ($got -eq 'DONE') { Check "$($case[0]): повний SHA origin" ($script:completed.Sha -ceq $script:remote) }
    "ВИМІР | $($case[0]) | $got"
}
if (-not $Before) {
    $r = [pscustomobject]@{ Result = $null; AssistantText = '' }
    Read-ClaudeEvent $r ([pscustomobject]@{ type = 'assistant'; message = [pscustomobject]@{ content = @([pscustomobject]@{ type = 'text'; text = $line }) } })
    Read-ClaudeEvent $r ([pscustomobject]@{ type = 'assistant'; message = [pscustomobject]@{ content = @([pscustomobject]@{ type = 'tool_use'; input = $line }) } })
    Check 'попередній звіт не зберігається після нового assistant' (-not $r.AssistantText)
    Read-ClaudeEvent $r ([pscustomobject]@{ message = [pscustomobject]@{ content = @([pscustomobject]@{ type = 'thinking'; thinking = $line }, [pscustomobject]@{ type = 'text'; text = $line }) }; type = 'assistant' })
    Read-ClaudeEvent $r ([pscustomobject]@{ result = ''; is_error = $false; type = 'result' })
    Check 'події з довільним порядком полів; лише текст' ((Get-ClaudeReport $r).Kind -eq 'DONE')
    $secrets = @(
        ('ey' + 'J' + ('a' * 20)), ('s' + 'k-' + ('b' * 20)), ('g' + 'hp_' + ('c' * 25)),
        ('github' + '_pat_' + ('d' * 25)), ('re' + 'fresh_token=значення'),
        ('-----BE' + 'GIN RSA PRIVATE KEY-----' + "`n" + ('приховано' + "`n") * 50 + '-----END RSA PRIVATE KEY-----'),
        'api_key=значення', 'Authorization: Bearer значення', 'password=значення'
    )
    # Значення секретних полів у всіх формах запису: у файлі, журналі й публічному стані їх бути не може.
    $values = @('значення-а', 'значення-б', 'значення-в', 'значення-г', 'значення-д', 'значення-е', 'значення-є', 'значення-ж')
    $forms = @(
        '{"password":"значення-а"}', '{"Authorization":"Bearer значення-б"}', '{"api_key":"значення-в","ok":1}',
        '  "client_secret" : "значення-г",', 'password: значення-д', "api-key: 'значення-е'",
        'curl -H "Authorization: Bearer значення-є"', 'access_token=значення-ж'
    )
    $script:capturedLog = ''
    function Write-Log { param($Text) $script:capturedLog += "$Text`n" }
    $r = [pscustomobject]@{ Code = 0; Result = [pscustomobject]@{ result = ($forms -join "`n") + "`n<b>хвіст</b>" }; AssistantText = ''; Err = '' }
    Save-ClaudeNoReport $m "$($job.id)-форми" $r
    $rawForms = [IO.File]::ReadAllText((Join-Path $WorkDir "no-report/$($job.id)-форми.json"), $script:Utf8)
    $publicForms = @(Get-ClaudeNoReportLines) -join "`n"
    foreach ($place in @(@('файл', $rawForms), @('журнал', $script:capturedLog), @('публічний стан', $publicForms))) {
        Check "значення секретних полів вилучено: $($place[0])" (@($values | Where-Object { $place[1].Contains($_) }).Count -eq 0)
    }
    Remove-Item -LiteralPath (Join-Path $WorkDir "no-report/$($job.id)-форми.json")
    $r = [pscustomobject]@{ Code = 0; Result = [pscustomobject]@{ result = ($secrets -join "`n") + "`n<b>хвіст</b>" }; AssistantText = ''; Err = '' }
    Save-ClaudeNoReport $m $job.id $r
    $raw = [IO.File]::ReadAllText((Join-Path $WorkDir "no-report/$($job.id).json"), $script:Utf8)
    $diagnostic = $raw | ConvertFrom-Json
    Check 'код і тип result доступні' ($diagnostic.exit -eq 0 -and $diagnostic.result_type -eq 'System.String')
    Check 'приватний блок вилучено до обрізання хвоста' (-not $raw.Contains('приховано'))
    Check 'усі секретні форми вилучено' (@($secrets | Where-Object { $raw.Contains($_) }).Count -eq 0)
    $public = @(Get-ClaudeNoReportLines) -join "`n"
    Check 'діагностика йде в публічний стан із екрануванням' ($public.Contains('&lt;b&gt;хвіст&lt;/b&gt;') -and $public.Contains('result_type=System.String'))
    $r.Result.result = (1..60 | ForEach-Object { "рядок $_" }) -join "`n"
    Save-ClaudeNoReport $m $job.id $r
    $diagnostic = [IO.File]::ReadAllText((Join-Path $WorkDir "no-report/$($job.id).json"), $script:Utf8) | ConvertFrom-Json
    Check 'хвіст до 40 рядків; останні рядки збережено' (($diagnostic.tail -split "`n").Count -eq 40 -and $diagnostic.tail.Contains('рядок 60') -and -not $diagnostic.tail.Contains('рядок 1'))
    Check 'AUTH збережено' ((Get-ErrorCode 'Not logged in /login') -eq 'AUTH')
    Check 'квота збережена' ((Get-ErrorCode 'rate_limit_error 429') -eq 'QUOTA')
}
exit [int]($script:bad -gt 0)
