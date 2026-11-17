#Requires -Version 5.1
<# Одноразове встановлення після перевірки й злиття латок. Працює під власником із наявними правами ProgramData;
не змінює ACL, задачі чи облікові дані. Наступні версії встановлює gemini-publish сам. #>
param([string]$RepoDir = (Join-Path $env:USERPROFILE 'kod-shi-data'), [string]$Root = 'C:\ProgramData\gemini-wrapper')
$ErrorActionPreference = 'Stop'
$repo = Join-Path $RepoDir '.git'
$source = Split-Path -Parent $PSScriptRoot
. (Join-Path $source 'gemini_publish.ps1')
. (Join-Path $PSScriptRoot 'читач.ps1')
if (-not (Test-OwnerUser) -or -not (Test-UpdateRoot $Root)) { throw 'UPDATE_ACL' }
$script:Repo = $repo
$script:NoHooks = Join-Path $env:TEMP ('no-hooks-' + [guid]::NewGuid().ToString('N'))
$script:OutboxDir = Join-Path $env:USERPROFILE 'gemini-outbox'
foreach ($d in @($WorkDir, (Join-Path $WorkDir 'seen'), $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
[void](Invoke-Git @('fetch','-q','--no-tags','origin','+refs/heads/main:refs/remotes/origin/main'))
Invoke-WrapperUpdate $Root
$main = Get-RefSha 'refs/remotes/origin/main'
$active = Join-Path $Root 'active.txt'
if (-not (Test-Path -LiteralPath $active)) { throw 'UPDATE_NOT_INSTALLED' }
$installed = [IO.File]::ReadAllText($active).Trim()
$tree = (Invoke-Git @('rev-parse', "${main}:аудит/адаптери/gemini")).Out.Trim()
if ($installed -cnotmatch '^[0-9a-f]{40}$' -or [IO.File]::ReadAllText((Join-Path (Join-Path (Join-Path $Root 'versions') $installed) 'source-tree.txt')).Trim() -cne $tree) { throw 'UPDATE_NOT_INSTALLED' }
foreach ($pair in @(@('gemini_run.ps1',$Root), @('gemini_publish.ps1',(Join-Path $env:USERPROFILE 'gemini-publish')), @('gemini_watch.ps1',(Join-Path $env:USERPROFILE 'gemini-watch')), @('claude_run.ps1',(Join-Path $env:USERPROFILE 'claude-run')))) {
    $name = $pair[0]; $dir = $pair[1]
    Install-EntryReader $dir $name $Root
}
[IO.File]::WriteAllText((Join-Path $Root 'selfupdate.ready'), '1', $script:Utf8)
Write-Output "Самооновлення встановлено: $main. Наступні запуски чотирьох задач читатимуть active.txt."
