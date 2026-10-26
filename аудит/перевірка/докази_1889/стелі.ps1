param([string]$Root,[string]$Temp)
$ErrorActionPreference='Stop'
[void](New-Item -ItemType Directory -Force -Path $Temp)
. (Join-Path $Root 'аудит/адаптери/gemini/gemini_run.ps1') -RepoDir $Temp -RunsDir $Temp -OutDir $Temp -LaneDir $Temp -EnableCodex -CodexFallbackModel 'gpt-test-high'
$script:StateDir=$Temp
$script:SlotDir=$Temp
$script:Limits=@{ slots=@{codex=2;agy=2;claude=2} }
$script:Agy='fake'
function Write-Log([string]$Text) {}
function Find-CodexExe { 'fake-codex' }
function Get-Quota { [pscustomobject]@{Known=$true;Blocked=$true;Group='GEMINIMODELS';ResetMin=60;ResetAt=2000000000;Left=0} }
function Get-Markers {
  foreach($i in 1..4) {
    $model=$(if($i -le 2){'gpt-test-high'}else{'gemini-flash-high'})
    $line='refs/remotes/origin/gemini-queue/probe'+$i+'/'+$model+'/1'+"`t"+('a'*40)+"`t"+[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    ConvertTo-Marker $line
  }
}
$script:Engines=@()
function Start-Worker([hashtable]$Job,[string]$Dir) {
  $script:Engines += $Job.sel.engine
  [pscustomobject]@{Slot=$Job.slot;Slug=$Job.slug;Gpu=$false;Marker=$Job.name;Proc=[pscustomobject]@{HasExited=$false}}
}
$workers=New-Object Collections.ArrayList
$started=Start-Markers $workers
Write-Output ('FALLBACK_CAP started='+$started+'; actual_codex='+@($script:Engines|Where-Object{$_ -eq 'codex'}).Count+'; codex_limit=2; slots='+(($workers|ForEach-Object{$_.Slot}) -join ','))
