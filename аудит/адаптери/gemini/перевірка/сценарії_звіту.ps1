#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot), [string]$EvidenceDir = '')
$ErrorActionPreference = 'Stop'
$utf = New-Object Text.UTF8Encoding($false)
$errors = $null; $tokens = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'claude_run.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
foreach ($name in @('Remove-ReportDecoration', 'Get-Report')) {
    $node = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    if ($node) { . ([scriptblock]::Create($node.Extent.Text)) }
}
$script:SlugCore = '[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}'
$sha = 'a' * 40; $branch = 'claude/проба-рушія-claude'; $line = "НОУТБУК ГОТОВО $branch $sha"
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Друкує факт і збирає код завершення всього стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
$cases = @(
    @('простий', $line, 'DONE'),
    @('жирний', "**$line**", 'DONE'),
    @('inline-бектики', ('`' + $line + '`'), 'DONE'),
    @('лапки', ('"' + $line + '"'), 'DONE'),
    @('українські лапки', "«$line»", 'DONE'),
    @('крапка', "$line.", 'DONE'),
    @('жирний з крапкою', "**$line.**", 'DONE'),
    @('лапки з крапкою', "«$line».", 'DONE'),
    @('поля з бектиками', ('НОУТБУК ГОТОВО `' + $branch + '` `' + $sha + '`'), 'DONE'),
    @('після підсумку', "Підсумок: перевірено.`n`n$line", 'DONE'),
    @('не останній рядок', "$line`n`nПідсумок: перевірено.", 'DONE'),
    @('CRLF', "Зроблено.`r`n`r`n$line.`r`n", 'DONE'),
    @('порожня відповідь', '', ''),
    @('звичайна проза', 'Зроблено, усе гаразд.', ''),
    @('префікс', "Очікується: $line", ''),
    @('суфікс', "$line — приклад", ''),
    @('цитата markdown', "> $line", ''),
    @('продовження цитати markdown', "> У наряді написано:`n$line", ''),
    @('цитата багаторядкова', "«У наряді написано:`n$line`nце цитата»", ''),
    @('огорожа бектиками', ('```text' + "`n$line`n" + '```'), ''),
    @('огорожа тильдами', "~~~text`n$line`n~~~", ''),
    @('довша огорожа', ('````text' + "`n$line`n" + '```' + "`n$line`n" + '````'), ''),
    @('відступ коду', "    $line", ''),
    @('табуляція коду', "`t$line", ''),
    @('цитований наряд', "----- НАРЯД -----`n$line`n----- КІНЕЦЬ НАРЯДУ -----", ''),
    @('приклад', "Приклад:`n$line", ''),
    @('приклад після порожнього рядка', "Приклад:`n`n$line", ''),
    @('жирна назва прикладу', "**Приклад:**`n`n$line", ''),
    @('приклад у розділі', "## Приклад`n`n$line`n`nНе звіт.", ''),
    @('цитата у розділі', "## Цитата наряду`n$line", ''),
    @('HTML-коментар', "<!--`n$line`n-->", ''),
    @('два звіти', "$line`n`n$line", ''),
    @('зайва крапка', "$line..", ''),
    @('короткий SHA', "НОУТБУК ГОТОВО $branch abc", ''),
    @('незбалансоване оформлення', "**$line", ''),
    @('після прикладу справжній звіт', ('```' + "`n$line`n" + '```' + "`n`n$line"), 'DONE'),
    @('після розділу прикладу', "## Приклад`n$line`n## Результат`n$line", 'DONE'),
    @('результат наряду', "## Результат наряду`n$line", 'DONE'),
    @('наряд усередині блока коду', ('```' + "`n----- НАРЯД -----`n$line`n" + '```' + "`n`n$line"), 'DONE'),
    @('блокер', "НОУТБУК ЗАБЛОКОВАНО: немає входу, гілка $branch.", 'BLOCKED')
)
if ($EvidenceDir) { [void][IO.Directory]::CreateDirectory($EvidenceDir) }
foreach ($case in $cases) {
    # Записані форми stream-json 2.1.300, синтетичні дані; журнали Admin недоступні.
    $event = [ordered]@{ type = 'result'; subtype = 'success'; is_error = $false; result = $case[1] }
    $json = $event | ConvertTo-Json -Compress
    if ($EvidenceDir) { [IO.File]::AppendAllText((Join-Path $EvidenceDir 'форми.jsonl'), $json + "`n", $utf) }
    $report = Get-Report (($json | ConvertFrom-Json).result)
    $ok = if ($case[2]) { $null -ne $report -and $report.Kind -ceq $case[2] -and $report.Branch -ceq $branch } else { $null -eq $report }
    if ($ok -and $case[2] -eq 'DONE') { $ok = $report.Sha -ceq $sha }
    Check $case[0] $ok
}
. (Join-Path $SourceDir 'queue_lanes.ps1')
function Invoke-Git { [pscustomobject]@{ Code = 0; Out = $script:LaneJson } }
foreach ($n in @(0, 6, 8, 16, 99)) {
    $script:LaneJson = '{"v":1,"slots":{"codex":' + $n + ',"agy":' + $n + ',"claude":' + $n + '}}'
    $limits = Get-Limits
    $expected = [Math]::Min($n, 64)
    foreach ($lane in @('codex', 'agy', 'claude')) { Check "$lane з даних $n → $expected" ($limits.slots[$lane] -eq $expected) }
}
exit [int]($bad -gt 0)
