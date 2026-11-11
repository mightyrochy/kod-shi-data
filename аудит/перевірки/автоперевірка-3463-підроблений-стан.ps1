param([Parameter(Mandatory = $true)][string]$WrapperRoot)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$probe = Join-Path $env:TEMP ('forged-marker-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($probe)
$seed = Join-Path $probe 'seed'
$remote = Join-Path $probe 'origin.git'
& git init -q --bare $remote
& git init -q -b main $seed
& git -C $seed config user.name 'Стенд'
& git -C $seed config user.email 'stand@example.invalid'
& git -C $seed remote add origin $remote
& git -C $seed commit -qm 'База' --allow-empty
if ($LASTEXITCODE) { throw 'Не створено базу проби' }
$sha = (& git -C $seed rev-parse HEAD).Trim()
$queue = 'gemini-queue/forged-marker/gpt-6.1-sol-high/1'
& git -C $seed push -q origin "HEAD:refs/heads/$queue"
if ($LASTEXITCODE) { throw 'Не створено локальну позначку' }
. (Join-Path $WrapperRoot 'gemini_publish.ps1') -WorkDir "$probe/pub" -OutDir "$probe/out" -RepoUrl $remote
foreach ($d in @($WorkDir, $OutDir, "$OutDir/marker-state", "$WorkDir/seen")) { [void][IO.Directory]::CreateDirectory($d) }
$script:Repo = Join-Path $seed '.git'
$script:NoHooks = Join-Path $probe 'no-hooks'
[void](Invoke-Git @('fetch', '-q', 'origin', "+refs/heads/${queue}:refs/remotes/origin/$queue"))
$id = '20261111-200000-0123456789ab'
$status = @{v=1; id=$id; code='NO_REPORT'; slug='forged-marker'; model='gpt-6.1-sol-high'; n=1; marker=$sha; head=''; cond=''; bundle=''; turns=0; minutes=0; ahead=0}
Write-FileAtomic (Join-Path $OutDir "$id.json") ($status | ConvertTo-Json -Compress)
$stateFile = Join-Path "$OutDir/marker-state" ((Get-Sha256Hex "refs/remotes/origin/$queue $sha") + '.txt')
Write-FileAtomic $stateFile 'STARTED {}'
[void](Get-Line $id)
Remove-FinishedMarkers ([datetime]::UtcNow.AddSeconds(1))
$before = (& git -C $remote for-each-ref '--format=%(refname)' "refs/heads/$queue")
if (-not $before) { throw 'Позначку знято вже за підробленим JSON' }
Write-Output 'Лише підроблений JSON: позначка на origin є.'
# Другий файл лежить у тій самій недовіреній теці OutDir.
Write-FileAtomic $stateFile "DONE $id NO_REPORT"
Confirm-PendingMarkers
Remove-FinishedMarkers ([datetime]::UtcNow.AddSeconds(1))
$after = (& git -C $remote for-each-ref '--format=%(refname)' "refs/heads/$queue")
if ($after) { throw 'Проблему не відтворено: позначка лишилася' }
Write-Output 'Підроблений JSON і marker-state: позначки на origin немає.'
Write-Output 'Справжній прогін не завершувався; бандла немає. Відтворено 14488.'
