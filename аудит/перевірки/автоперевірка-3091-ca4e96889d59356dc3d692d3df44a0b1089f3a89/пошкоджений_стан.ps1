param([string]$SourceDir, [string]$TestRoot)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
. (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$TestRoot/pub" -OutDir "$TestRoot/out" -OutboxDir "$TestRoot/outbox" -UpdateRoot "$TestRoot/update"
foreach ($dir in @("$WorkDir/state", "$WorkDir/seen", $OutDir, $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
$path = Join-Path $WorkDir 'state/broken.json'
[IO.File]::WriteAllText($path, '{не JSON', $utf)
try { [void]@(Get-ChainTaskResults) } catch { Write-ChainFailure $_ }
$record = Get-Content -LiteralPath (Join-Path $OutDir 'state-failures.jsonl') -Encoding UTF8 | Select-Object -Last 1 | ConvertFrom-Json
[pscustomobject]@{ expected_path = $path; actual_path = $record.path; object_type = $record.object_type; owner = $record.owner; acl = $record.acl; last_write_utc = $record.last_write_utc; exception_recorded = [bool]$record.exception; stack_recorded = [bool]$record.script_stack } | ConvertTo-Json -Compress
Get-ChildItem -LiteralPath $OutboxDir -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() }
