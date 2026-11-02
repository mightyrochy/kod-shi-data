#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('review-2831-scenes-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)

# Виконується справжній публікатор; git і GitHub замінені даними фікстури.
# Справжніх POST/PATCH, процесів моделей і змін у перевірюваному дереві немає.
. (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/box"
foreach ($dir in @($WorkDir,"$WorkDir/drafts","$WorkDir/seen",$OutDir,$OutboxDir)) {
    [void][IO.Directory]::CreateDirectory($dir)
}
$script:FixtureHead = 'a' * 40
$script:FixtureScene = 'ЖИВИЙ ПІСЛЯ: ж3_співбесіда — питання перевірки → повне → main → без вади'
$script:FixtureCommit = 'Оновлений звіт виконавця без доданої перевіркою сцени'
$script:FixtureRegistry = [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf)
$script:FixtureExisting = [pscustomobject]@{
    number=91; user=@{login='mightyrochy'}
    head=@{ref='gemini/проба';repo=@{full_name=$GitHubRepo}}
    base=@{ref='main';repo=@{full_name=$GitHubRepo}}
    body=("Попередній звіт`n`n" + $script:FixtureScene)
}
$script:FixtureCalls = @()
function Get-ChainPulls { $script:FixtureExisting }
function Resolve-Exe([string]$Name) { 'перехоплено-без-запуску-gh' }
function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
    $out = ''
    if ($GitArgs[0] -eq 'ls-remote') { $out = $script:FixtureHead + "`trefs/heads/gemini/проба" }
    elseif ($GitArgs -contains '--format=%B') { $out = $script:FixtureCommit }
    elseif ($GitArgs[-1] -like '*живі_сцени.txt') { $out = $script:FixtureRegistry }
    elseif ($GitArgs[0] -eq 'diff') { $out = 'аудит/дошка/gemini/проба.md' }
    [pscustomobject]@{Code=0;Out=$out;Err=''}
}
function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDirectory = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) {
    $script:FixtureCalls += [pscustomobject]@{Arguments=$Arguments;Payload=(ConvertFrom-Json $StdIn)}
    [pscustomobject]@{Code=0;Out='{"number":91}';Err=''}
}

Save-DraftRequest 'gemini/проба' $script:FixtureHead
Complete-EngineDrafts
$after = $script:FixtureExisting.body
if ($script:FixtureCalls.Count) { $after = $script:FixtureCalls[-1].Payload.body }
$beforeCount = [int]($script:FixtureExisting.body.Contains($script:FixtureScene))
$afterCount = [int]($after.Contains($script:FixtureScene))
"Записів API: $($script:FixtureCalls.Count)"
if ($script:FixtureCalls.Count) { "Метод: $($script:FixtureCalls[-1].Arguments[2])" }
"Сцен перевірки до: $beforeCount; після: $afterCount"
"Тіло після: $after"
"Запитів у черзі після: $(@(Get-ChildItem -LiteralPath "$WorkDir/drafts" -Filter '*.json').Count)"

# Фікстура лишається в TEMP задачі; її прибирає обгортка разом із задачею.
