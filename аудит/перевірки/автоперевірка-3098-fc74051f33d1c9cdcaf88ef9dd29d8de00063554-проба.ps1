param([Parameter(Mandatory=$true)][string]$SourceDir, [Parameter(Mandatory=$true)][string]$Label)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path $env:TEMP ('probe3098-' + $Label)
if (Test-Path -LiteralPath $tmp) { throw 'Тека проби вже існує' }
[void][IO.Directory]::CreateDirectory($tmp)
. (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/update"
foreach ($d in @($WorkDir, "$WorkDir/seen", $OutDir, $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
function Make-Failure([string]$Path, [string]$Where = 'Get-MarkerState', [string]$Kind = 'access') {
    $e = if ($Kind -eq 'access') { [UnauthorizedAccessException]::new('blocked') } else { [IO.IOException]::new('busy') }
    $e.Data['StatePath'] = $Path
    [pscustomobject]@{ Exception=$e; InvocationInfo=[pscustomobject]@{ScriptName='';PositionMessage='штучна проба'}; ScriptStackTrace="at $Where, probe: line 1"; TargetObject=$Path }
}
$paths = @()
foreach ($n in 1..4) {
    $path = Join-Path $tmp "стан $n ШЛЯХ файл.txt"
    [IO.File]::WriteAllText($path, 'DONE', $script:Utf8)
    $paths += $path
    Write-ChainFailure (Make-Failure $path)
}
$out = @(Get-ChildItem -LiteralPath $OutboxDir -File)
$records = @([IO.File]::ReadAllLines("$OutDir/state-failures.jsonl", $script:Utf8) | ForEach-Object { ConvertFrom-Json $_ })
$keys = @(Get-ChildItem -LiteralPath "$WorkDir/seen" -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $script:Utf8) })
$expected = 'chain-failed CHAIN_FAILED UnauthorizedAccessException Get-MarkerState ' + [datetime]::UtcNow.ToString('yyyyMMddHH')
$validLines = @($out | Where-Object { (Test-OutboxLine ([IO.File]::ReadAllText($_.FullName, $script:Utf8).Trim())) -ceq '' }).Count
$pathsOk = @($records | Where-Object { $paths -ccontains $_.path }).Count
"${Label}: однакові тип і місце, різні шляхи: повідомлень $($out.Count); діагностик $($records.Count); точних шляхів $pathsOk; прийнятих рядків $validLines; ключ без шляху $($keys -ccontains $expected)"
Write-ChainFailure (Make-Failure $paths[0] 'Get-OtherState')
Write-ChainFailure (Make-Failure $paths[0] 'Get-MarkerState' 'io')
try { throw 'CHAIN_REMOTE' } catch { Write-ChainFailure $_; Write-ChainFailure $_ }
$after = @(Get-ChildItem -LiteralPath $OutboxDir -File).Count
"${Label}: додано інше місце, інший тип, іменований код двічі: нових повідомлень $($after - $out.Count)"
if ($Label -eq 'HEAD' -and ($out.Count -ne 1 -or $records.Count -ne 4 -or $pathsOk -ne 4 -or $validLines -ne 1 -or $keys -cnotcontains $expected -or $after -ne 4)) { exit 1 }
