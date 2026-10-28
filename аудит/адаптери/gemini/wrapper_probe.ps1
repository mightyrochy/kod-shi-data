#Requires -Version 5.1
# Локальна проба кандидата не читає мережу, профілі, задачі чи спільну теку ноутбука.
$ErrorActionPreference = 'Stop'
foreach ($file in @(Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1' -File)) {
    $errors = $null; $tokens = $null
    [void][Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$errors)
    if ($errors.Count) { exit 1 }
}
. (Join-Path $PSScriptRoot 'queue_lanes.ps1')
$script:QueuePrefix = 'refs/remotes/origin/gemini-queue/'
$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}$'
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
$script:CondPattern = '^(?:p[0-9]|d20[0-9]{10}|gpu)(?:-(?:p[0-9]|d20[0-9]{10}|gpu)){0,2}$'
$m = ConvertTo-Marker ($script:QueuePrefix + 'проба/gpt-6.1-sol-high/1' + "`t" + ('a'*40) + "`t1")
if (-not $m.Valid -or $m.Lane -ne 'codex') { exit 1 }
if ((Get-AutoTaskPath ('автоперевірка-12-' + ('a'*40))) -cne 'аудит/наряди/автоперевірка.md') { exit 1 }
Write-Output 'WRAPPER_PROBE_OK'
