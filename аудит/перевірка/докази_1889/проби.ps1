param([string]$Root, [string]$Temp)
$ErrorActionPreference = 'Stop'
[void](New-Item -ItemType Directory -Force -Path $Temp)
$source = Join-Path $Root 'аудит/адаптери/gemini'
. (Join-Path $source 'gemini_run.ps1') -RepoDir $Temp -RunsDir $Temp -OutDir $Temp -LaneDir $Temp -QuotaWaitMinutes 0.001
$script:StateDir = $Temp
$script:SlotDir = $Temp
$script:Limits = $null
function Write-Log([string]$Text) {}
function Invoke-Git { [pscustomobject]@{ Code = 0; Out = 'наряд'; Err = '' } }
function Get-RefSha { 'a' * 40 }
function Find-CodexExe { 'fake' }
function Find-EngineExe { 'fake' }
function Reset-WorkTree {}
function Get-Prompt { 'проба' }
function Get-Facts { [pscustomobject]@{ Ahead = 0; Head = ('a' * 40) } }
function Invoke-Agent { [pscustomobject]@{ Code = 'QUOTA'; Report = 'NONE'; Turns = 1; Tail = 'resets_in_seconds: 1' } }
$m = [pscustomobject]@{ Ref = 'refs/remotes/origin/gemini-queue/probe/gpt-test/1'; Sha = ('a' * 40); Slug = 'probe'; Model = 'gpt-test'; N = '1'; Cond = ''; Name = 'gemini-queue/probe/gpt-test/1'; Time = 0; Gpu = $false }
$job = [pscustomobject]@{ id = '20261026-000000-000000000001'; slot = 'codex-1'; dir = $Temp; head = ''; sel = [pscustomobject]@{ engine = 'codex'; emodel = 'gpt-test'; effort = ''; qknown = $false; qgroup = ''; qleft = -1; model = 'gpt-test' } }
$sp = Get-StatePath (Get-MarkerKey $m)
$counts = @()
for ($i = 1; $i -le 7; $i++) {
    Invoke-Task $m $job
    $st = Get-MarkerState $m
    $counts += $st.Wait.retakes
}
Write-Output ('GEMINI_QUOTA seven Invoke-Task calls: retakes=' + ($counts -join ',') + '; final=' + $st.Kind)

# Помилка створення worktree після CreateNew: реальний Invoke-Worker, зовнішню роботу підмінено винятком.
$m.Ref += '-crash'
$statePath = Get-StatePath (Get-MarkerKey $m)
[void](New-Claim $m 'probe-crash')
$script:Job = [pscustomobject]@{ ref = $m.Ref; sha = $m.Sha; slot = 'codex-1'; gpu = $true; lane = 'codex'; name = $m.Name; slug = $m.Slug; model = $m.Model; prio = 5; n = '1'; cond = ''; deadline = ''; time = 0; limits = [pscustomobject]@{ slots = [pscustomobject]@{}; agy_turn_minutes = 10; agy_total_minutes = 30; codex_stall_minutes = 10 } }
function Enter-WorkTree { throw 'штучна помилка створення worktree' }
$rc = Invoke-Worker
Resume-Interrupted
$st = Get-MarkerState $m
Write-Output ('WORKER_FAILURE exit=' + $rc + '; marker=' + $st.Kind + '; state_exists=' + (Test-Path -LiteralPath $statePath) + '; gpu_free=' + (Test-LockFree (Get-GpuLockPath)))

# Файл STARTED Claude записує Invoke-Claude перед читанням подій. Відтворюємо цей запис дослівно між реальними Enter-ClaudeQuotaWait.
. (Join-Path $source 'claude_run.ps1') -WorkDir $Temp -RepoDir $Temp -LaneDir $Temp -OutboxDir $Temp -QuotaWaitMinutes 0.001
$script:StateDir = $Temp
$script:Limits = $null
function Write-Log([string]$Text) {}
$m.Ref += '-claude'
$m.Model = 'cc-claude-test'
$m.Name = 'gemini-queue/probe/cc-claude-test/1'
$sp = Get-StatePath (Get-MarkerKey $m)
$id = '20261026-000000-000000000002'
[void](New-Item -ItemType Directory -Force -Path (Join-Path (Join-Path $Temp 'runs') $id))
$counts = @()
for ($i = 1; $i -le 7; $i++) {
    Write-FileAtomic $sp ('STARTED ' + $id + ' ' + (([ordered]@{ pid = $PID; start = (Get-UtcStamp (Get-Date)); marker = $m.Name; slot = 'claude-1' }) | ConvertTo-Json -Compress))
    [void](Enter-ClaudeQuotaWait $m $sp $id ([pscustomobject]@{ Limit = $null }) 'usage limit')
    $st = Get-MarkerState $m
    $counts += $st.Wait.retakes
}
Write-Output ('CLAUDE_QUOTA seven STARTED -> Enter-ClaudeQuotaWait: retakes=' + ($counts -join ',') + '; final=' + $st.Kind)

# Недовірений heartbeat: приклади шляху й секрету мають відсіктися до тіла issue.
$script:SlotDir = Join-Path $Temp 'status-slots'
[void](New-Item -ItemType Directory -Force -Path $script:SlotDir)
$GeminiOutDir = $Temp
Write-FileAtomic (Join-Path $Temp 'heartbeat.json') '{"time":"2026-10-26T10:00:00","isolation":"FAKE_TOKEN=C:/private","marker":"C:/private","engine":"C:/private","model":"FAKE_TOKEN=C:/private","lanes":[{"lane":"codex","n":2,"busy":[{"slot":"codex-1","marker":"C:/private","model":"FAKE_TOKEN=C:/private"}]}],"codex":{"refused":"FAKE_TOKEN=C:/private","reset":"C:/private"},"wait":[{"marker":"C:/private","until":"FAKE_TOKEN=C:/private","g":"C:/private"}]}'
$beat = Read-GeminiBeat | ConvertTo-Json -Depth 8 -Compress
Write-Output ('UNTRUSTED_HEARTBEAT contains_test_secret_or_path=' + ($beat -match 'FAKE_TOKEN|C:/private'))
