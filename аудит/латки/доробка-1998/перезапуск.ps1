#Requires -Version 5.1
param([string]$SourceDir, [string]$Root, [string]$Engine, [string]$Mode = 'main')
# Стенд замінює лише ноутбук і доставку статусу. Main, відновлення, замки,
# heartbeat, читач та побудова статусу — справжні функції з переданої бази.
$ErrorActionPreference = 'Stop'
$g = Join-Path $Root 'g'; $c = Join-Path $Root 'c'
$repo = Join-Path $Root 'clone'; $origin = Join-Path $Root 'origin.git'
$out = Join-Path $Root 'out'; $lanes = Join-Path $Root 'lanes'
if ($Engine -eq 'gemini') {
    . (Join-Path $SourceDir 'gemini_run.ps1') -RepoDir $repo -RepoUrl $origin -RunsDir $g -OutDir $out -LaneDir $lanes -AgyExe 'немає-cli-1998'
    function Test-Isolation { '' }
} else {
    . (Join-Path $SourceDir 'claude_run.ps1') -RepoDir $repo -RepoUrl $origin -WorkDir $c -GeminiOutDir $out -OutboxDir (Join-Path $Root 'outbox') -PublishDir (Join-Path $Root 'pub') -LaneDir $lanes -NoStatus
    function Test-OwnerUser { $true }
    function Get-BootStamp { 'стенд-1998' }
    function Get-TaskRows { @() }
    function Update-Status([switch]$Force) {
        [IO.File]::WriteAllText((Join-Path $Root 'status.md'), (Get-StatusBody), $script:Utf8)
    }
}
if ($Mode -eq 'read') {
    $script:StateDir = Join-Path $c 'state'; $script:SlotDir = Join-Path $c 'slots'
    $script:Limits = @{ slots = @{ claude = 0 }; source = 'код' }
    $beat = Read-GeminiBeat
    $data = [ordered]@{ lanes = @($beat.Lanes | ForEach-Object { @{ lane = $_.Lane; n = $_.N; busy = @($_.Busy | ForEach-Object { $_.Slot }) } }); status = (Get-StatusBody); busy = (Test-GeminiBusy) }
    [IO.File]::WriteAllText((Join-Path $Root 'read.json'), ($data | ConvertTo-Json -Depth 6), $script:Utf8)
    exit 0
}
exit (Main)
