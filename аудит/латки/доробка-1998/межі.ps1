#Requires -Version 5.1
param([string]$SourceDir)
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('bounds-1998-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($root)
. (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $root -GeminiOutDir $root -OutboxDir $root -LaneDir $root -NoStatus
$script:StateDir = Join-Path $root 'state'; $script:SlotDir = Join-Path $root 'slots'
foreach ($p in @($script:StateDir, $script:SlotDir)) { [void][IO.Directory]::CreateDirectory($p) }
$bad = 0; $locks = @()
function Check([string]$Name, [bool]$Ok) {
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    $busy = @('codex-1', 'codex-4', 'codex-5', 'codex-6', 'codex-10', 'codex-12', 'codex-64', 'codex-65',
        'codex-0', 'codex-01', 'Codex-1', 'agy-1', '../codex-1', 'codex-99999999999999999999', "codex-1`n")
    $doc = @{ lanes = @(@{ lane = 'codex'; n = 0; busy = @($busy | ForEach-Object {
        @{ slot = $_; marker = 'gemini-queue/межі/gpt-6.1-sol-high/1'; model = 'gpt-6.1-sol-high'; since = '2026-10-28T00:00:00Z'; gpu = $true }
    }) }) }
    Write-FileAtomic (Join-Path $root 'heartbeat.json') ($doc | ConvertTo-Json -Depth 6)
    $beat = Read-GeminiBeat
    Check 'n=0 зберігає зайняті слоти до 64, відкидає чужу смугу, регістр, шлях, 0, 01, 65, переповнення та LF' (
        $beat.Lanes.Count -eq 1 -and ($beat.Lanes[0].Busy.Slot -join ',') -ceq 'codex-1,codex-4,codex-5,codex-6,codex-10,codex-12,codex-64')
    # Тимчасова зміна єдиної межі має змінити і числовий читач, і busy.
    $saved = $script:Ceil.slots; $script:Ceil.slots = @(0, 12)
    $doc.lanes[0].n = 12
    Write-FileAtomic (Join-Path $root 'heartbeat.json') ($doc | ConvertTo-Json -Depth 6)
    $beat = Read-GeminiBeat
    Check 'зміна Ceil.slots до 12 змінює також читання назв і busy' (
        $beat.Lanes.Count -eq 1 -and ($beat.Lanes[0].Busy.Slot -join ',') -ceq 'codex-1,codex-4,codex-5,codex-6,codex-10,codex-12')
    $doc.lanes[0].n = 13
    Write-FileAtomic (Join-Path $root 'heartbeat.json') ($doc | ConvertTo-Json -Depth 6)
    Check 'зміна Ceil.slots до 12 відкидає n=13' ((Read-GeminiBeat).Lanes.Count -eq 0)
    $script:Ceil.slots = $saved
    $i = 0
    foreach ($lane in @('codex', 'agy', 'claude')) {
        foreach ($k in @(1, 4, 5, 6, 10, 12, 64)) {
            $i++; $id = '20261028-020000-{0:x12}' -f $i
            $dir = Join-Path $root $id; [void][IO.Directory]::CreateDirectory($dir)
            Write-FileAtomic (Join-Path $dir 'worker.json') (@{ slot = "$lane-$k" } | ConvertTo-Json)
            $claim = Join-Path $script:StateDir "$lane-$k.claim"
            Write-FileAtomic $claim $id
            (Get-Item -LiteralPath $claim).LastWriteTime = (Get-Date).AddMinutes(-20)
            $locks += Open-Lock (Join-Path $script:SlotDir "$lane-$k.lock")
        }
    }
    Clear-OrphanClaims $root
    Check '21 прострочений claim із живими замками слотів 1,4,5,6,10,12,64 збережено' (@(Get-ChildItem $script:StateDir -Filter '*.claim').Count -eq 21)
    foreach ($l in $locks) { $l.Dispose() }; $locks = @()
    Clear-OrphanClaims $root
    Check 'усі 21 claim після звільнення замків очищено' (@(Get-ChildItem $script:StateDir -Filter '*.claim').Count -eq 0)
} finally {
    foreach ($l in $locks) { $l.Dispose() }
    # Тека створена тут під GetTempPath із непередбачуваним GUID; видаляємо лише її.
    $resolved = [IO.Path]::GetFullPath($root)
    if ($resolved.StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()), [StringComparison]::OrdinalIgnoreCase) -and
        (Split-Path -Leaf $resolved) -match '^bounds-1998-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
exit [int]($bad -gt 0)
