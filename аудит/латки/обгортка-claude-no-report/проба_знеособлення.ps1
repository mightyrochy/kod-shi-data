#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Utf8 = New-Object Text.UTF8Encoding($false)
$errors = $null; $tokens = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'claude_run.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
. (Join-Path $SourceDir 'queue_lanes.ps1')
foreach ($name in @('Get-ClaudeText','Protect-ClaudeText','Save-ClaudeNoReport','Get-ClaudeNoReportLines')) {
    $node = $ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name}, $true)
    . ([scriptblock]::Create($node.Extent.Text))
}
function Write-Log { param($Text) $script:capturedLog = $Text }
$WorkDir = Join-Path $env:TEMP ('review-redaction-' + [guid]::NewGuid().ToString('N'))
$taskRoot = [IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
if (-not ([IO.Path]::GetFullPath($WorkDir).StartsWith($taskRoot,[StringComparison]::OrdinalIgnoreCase))) { throw 'Тека поза TEMP задачі' }
[void][IO.Directory]::CreateDirectory($WorkDir)
$m = [pscustomobject]@{Name='синтетична-перевірка'}
foreach ($case in @(
    @('поле без лапок', 'password=СИНТЕТИЧНИЙ_ПАРОЛЬ', 'СИНТЕТИЧНИЙ_ПАРОЛЬ'),
    @('поле JSON', '{"password":"СИНТЕТИЧНИЙ_ПАРОЛЬ"}', 'СИНТЕТИЧНИЙ_ПАРОЛЬ'),
    @('авторизація JSON', '{"Authorization":"Bearer СИНТЕТИЧНИЙ_ДОСТУП"}', 'СИНТЕТИЧНИЙ_ДОСТУП'),
    @('ключ JSON', '{"api_key":"СИНТЕТИЧНИЙ_КЛЮЧ"}', 'СИНТЕТИЧНИЙ_КЛЮЧ')
)) {
    $r = [pscustomobject]@{Code=0;Result=[pscustomobject]@{result=$case[1]};AssistantText='';Err=''}
    Save-ClaudeNoReport $m 'синтетика' $r
    $raw = [IO.File]::ReadAllText((Join-Path $WorkDir 'no-report/синтетика.json'),$script:Utf8)
    $public = @(Get-ClaudeNoReportLines) -join "`n"
    'ВИМІР | {0} | файл={1} | журнал={2} | публічний стан={3}' -f $case[0],$raw.Contains($case[2]),$script:capturedLog.Contains($case[2]),$public.Contains($case[2])
}
