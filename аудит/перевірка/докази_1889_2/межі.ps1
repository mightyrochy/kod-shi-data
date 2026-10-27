param([string]$Root, [string]$Temp, [ValidateSet('gemini','claude')][string]$Engine = 'gemini', [ValidateSet('quota','worker','spawn','orphan','directory')][string]$Case = 'quota')
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[void](New-Item -ItemType Directory -Force -Path $Temp)
$source = Join-Path $Root 'аудит/адаптери/gemini'
if ($Engine -eq 'gemini') {
    . (Join-Path $source 'gemini_run.ps1') -RepoDir $Temp -RunsDir $Temp -OutDir $Temp -LaneDir $Temp -QuotaWaitMinutes 0.001 -EnableCodex
} else {
    . (Join-Path $source 'claude_run.ps1') -WorkDir $Temp -RepoDir $Temp -LaneDir $Temp -OutboxDir $Temp -QuotaWaitMinutes 0.001
}
$script:StateDir = $Temp
$script:SlotDir = $Temp
$script:Limits = $null
function Write-Log([string]$Text) {}
function Invoke-Git { [pscustomobject]@{ Code = 0; Out = 'наряд'; Err = '' } }
function Get-RefSha { 'a' * 40 }
function Reset-WorkTree {}
function Get-Facts { [pscustomobject]@{ Ahead = 0; Head = ('a' * 40) } }
function Get-Prompt { 'аудит/наряди/probe.md' }
function Get-ContinueBranch { '' }
function Find-CodexExe { 'fake' }
function Find-EngineExe { 'fake' }
function Invoke-Agent { [pscustomobject]@{ Code = 'QUOTA'; Report = 'NONE'; Turns = 1; Tail = 'resets_in_seconds: 1' } }
$model = $(if ($Engine -eq 'gemini') { 'gpt-test-high' } else { 'cc-claude-test-high' })
$m = ConvertTo-Marker ('refs/remotes/origin/gemini-queue/probe/' + $model + '/1' + "`t" + ('a' * 40) + "`t" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds())
if ($Engine -eq 'claude') { $m = Add-ClaudeFields $m }
$lane = $(if ($Engine -eq 'gemini') { 'codex' } else { 'claude' })
$id = '20261027-000000-000000000001'
$job = [pscustomobject]@{ id = $id; slot = "$lane-1"; dir = $Temp; head = ''; ref = $m.Ref; sha = $m.Sha; gpu = $true; lane = $lane; name = $m.Name; slug = $m.Slug; model = $m.Model; prio = 5; n = '1'; cond = ''; deadline = ''; time = 0; claude = 'claude-test'; effort = 'high'; limits = [pscustomobject]@{ slots = [pscustomobject]@{}; agy_turn_minutes = 10; agy_total_minutes = 30; codex_stall_minutes = 10 }; sel = [pscustomobject]@{ engine = 'codex'; emodel = 'gpt-test'; effort = ''; qknown = $false; qgroup = ''; qleft = -1; model = 'gpt-test' } }
$sp = Get-StatePath (Get-MarkerKey $m)
if ($Case -eq 'directory') {
    # Виняток New-Item після New-Claim, до try/Start-Worker; решта планувальника справжня.
    function New-Item { throw 'штучна відмова створення теки прогону' }
}
if ($Case -eq 'quota' -and $Engine -eq 'claude') {
    # Підміна лише зовнішнього CLI; справжні Invoke-Task -> Invoke-Claude записують STARTED і читають події.
    $py = (Get-Command python).Source
    $fake = Join-Path $Temp 'fake_cc.py'
    Copy-Item -LiteralPath (Join-Path $source 'перевірка/fake_cc.py') -Destination $fake
    $cmd = Join-Path $Temp 'fake_cc.cmd'
    [System.IO.File]::WriteAllText($cmd, ('@"' + $py + '" "' + $fake + '" %*' + "`r`n"), [System.Text.Encoding]::ASCII)
    $script:FakeExe = $cmd
    function Find-Exe { $script:FakeExe }
    $env:FAKE_CC_SCENARIO = 'quota'
    $env:FAKE_CC_LOG = Join-Path $Temp 'cc.log'
    $env:PYTHONUTF8 = '1'
    $env:PYTHONIOENCODING = 'utf-8'
}
if ($Case -eq 'orphan') {
    [void](New-Claim $m $id)
    (Get-Item -LiteralPath (Get-ClaimPath $sp)).LastWriteTime = (Get-Date).AddMinutes(-11)
    Clear-OrphanClaims $Temp
    Write-Output ("ORPHAN $Engine marker=" + (Get-MarkerState $m).Kind + '; claim=' + (Test-Path -LiteralPath (Get-ClaimPath $sp)))
    exit
}
$states = @(); $counts = @(); $rc = 0
for ($i = 1; $i -le 7; $i++) {
    if ($Case -eq 'quota') {
        Invoke-Task $m $job
    } elseif ($Case -eq 'worker') {
        [void](New-Claim $m $id)
        $script:Job = $job
        function Enter-WorkTree { throw 'штучна помилка створення worktree' }
        $rc = Invoke-Worker
    } elseif ($Case -in @('spawn','directory')) {
        $script:Limits = @{ slots = @{ codex = 1; agy = 1; claude = 1 } }
        $script:ProbeMarker = $m
        function Get-Markers { $script:ProbeMarker }
        function Get-Quota { [pscustomobject]@{ Known = $false; Blocked = $false; Group = ''; ResetMin = 0; ResetAt = 0; Left = -1 } }
        function Start-Worker { throw 'штучна відмова запуску процесу' }
        $workers = New-Object Collections.ArrayList
        try { $null = Start-Markers $workers } catch { Write-Output ('SPAWN_ERROR ' + $_.Exception.Message) }
    }
    $st = Get-MarkerState $m
    $states += $st.Kind
    if ($st.Kind -eq 'WAIT') { $counts += $st.Wait.retakes } else { $counts += '-' }
    if ($st.Kind -eq 'DONE') { break }
}
$raw = $(if (Test-Path -LiteralPath $sp) { [System.IO.File]::ReadAllText($sp, $script:Utf8) } else { '<none>' })
Write-Output ("BOUND $Engine $Case attempts=$($states.Count); retakes=" + ($counts -join ',') + '; states=' + ($states -join ',') + '; final=' + $raw + '; claim=' + (Test-Path -LiteralPath (Get-ClaimPath $sp)) + '; gpu_free=' + (Test-LockFree (Get-GpuLockPath)) + '; rc=' + $rc)
if ($Engine -eq 'claude') {
    $lines = @(Get-ChildItem -LiteralPath $Temp -Filter '*.txt' | Where-Object { $_.Name -notmatch '^[a-f0-9]{64}\.txt$' } | ForEach-Object { [System.IO.File]::ReadAllText($_.FullName, $script:Utf8).Trim() })
    Write-Output ('LINES ' + ($lines -join ' / '))
} else {
    $codes = @(Get-ChildItem -LiteralPath $Temp -Filter '*.json' | ForEach-Object { ([System.IO.File]::ReadAllText($_.FullName, $script:Utf8) | ConvertFrom-Json) | ForEach-Object { if ($_.PSObject.Properties['code']) { $_.code } } })
    Write-Output ('STATUS_CODES ' + ($codes -join ','))
}
