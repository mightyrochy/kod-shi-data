param([string]$Root, [string]$Temp, [ValidateSet('gemini','claude')][string]$Engine)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[void](New-Item -ItemType Directory -Force -Path $Temp)
$source = Join-Path $Root 'аудит/адаптери/gemini'
if ($Engine -eq 'gemini') {
    . (Join-Path $source 'gemini_run.ps1') -RepoDir $Temp -RunsDir $Temp -OutDir $Temp -LaneDir $Temp
} else {
    . (Join-Path $source 'claude_run.ps1') -WorkDir $Temp -RepoDir $Temp -LaneDir $Temp -OutboxDir $Temp
}
$script:StateDir = $Temp
$script:SlotDir = $Temp
function Write-Log([string]$Text) {}
$model = $(if ($Engine -eq 'gemini') { 'gpt-test-high' } else { 'cc-claude-test-high' })
$m = ConvertTo-Marker ('refs/remotes/origin/gemini-queue/probe/' + $model + '/1' + "`t" + ('a' * 40) + "`t" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
if ($Engine -eq 'claude') { $m = Add-ClaudeFields $m }
$id = '20261027-000000-000000000002'
$sp = Get-StatePath (Get-MarkerKey $m)
$claim = Get-ClaimPath $sp
[void](New-Claim $m $id)
foreach ($age in 0,9) {
    (Get-Item -LiteralPath $claim).LastWriteTime = (Get-Date).AddMinutes(-$age)
    foreach ($pass in 1..3) {
        Clear-OrphanClaims $Temp
        $exists = Test-Path -LiteralPath $claim
        $kind = (Get-MarkerState $m).Kind
        Write-Output "LIVE $Engine age=$age pass=$pass marker=$kind claim=$exists"
        if (-not $exists -or $kind -ne 'TAKEN') { throw 'Живий claim звільнено' }
    }
}
# Старий claim із живим замком слота теж має лишатися за працівником.
$dir = Join-Path $Temp $id
[void](New-Item -ItemType Directory -Path $dir)
[System.IO.File]::WriteAllText((Join-Path $dir 'worker.json'), '{"slot":"codex-1"}', $script:Utf8)
$lock = Open-Lock (Join-Path $Temp 'codex-1.lock')
if ($null -eq $lock) { throw 'Не вдалося взяти пробний замок' }
try {
    (Get-Item -LiteralPath $claim).LastWriteTime = (Get-Date).AddMinutes(-11)
    Clear-OrphanClaims $Temp
    $exists = Test-Path -LiteralPath $claim
    Write-Output "LOCKED $Engine age=11 claim=$exists"
    if (-not $exists) { throw 'Claim живого працівника звільнено' }
} finally { $lock.Dispose() }
Clear-OrphanClaims $Temp
$exists = Test-Path -LiteralPath $claim
Write-Output ("RELEASED $Engine age=11 marker=" + (Get-MarkerState $m).Kind + "; claim=$exists")
if ($exists) { throw 'Сирітський claim не звільнено' }
