param([string]$SourceDir,[string]$Fixture)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
. (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$Fixture/runs" -OutDir "$Fixture/out" -LaneDir "$Fixture/lanes" -UpdateRoot "$Fixture/update"
$script:StateDir="$RunsDir/state"; $script:SlotDir="$RunsDir/slots"
foreach($d in @($script:StateDir,$script:SlotDir,"$OutDir/marker-state")){[void][IO.Directory]::CreateDirectory($d)}
$ref='gemini-queue/історичний/gpt-6.1-sol-high/1';$sha='a'*40
$m=[pscustomobject]@{Ref="refs/remotes/origin/$ref";Sha=$sha}
$old=Get-StatePath (Get-MarkerKey $m)
Write-FileAtomic $old 'DONE 20261105-000000-123456789abc OK'
Write-FileAtomic "$OutDir/marker-state/ready" '1'
$target=Initialize-SharedMarkerState
"ПЕРЕНЕСЕННЯ: target=$target; legacy_txt=$(@(Get-ChildItem -LiteralPath $script:StateDir -File -Filter '*.txt').Count); shared_txt=$(@(Get-ChildItem -LiteralPath $target -File -Filter '*.txt').Count)"
. (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$Fixture/pub" -OutDir "$Fixture/out" -OutboxDir "$Fixture/outbox" -UpdateRoot "$Fixture/update"
$state=Get-ChainMarkerState $ref $sha 'gpt-6.1-sol-high'
"РЕЗУЛЬТАТ: історичний DONE -> $($state.Kind)"
if($state.Kind -ceq 'NEW'){exit 1}
exit 0