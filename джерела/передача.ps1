#requires -Version 7.0
<#
.SYNOPSIS
Explicit local handoffs; execution records, never another backlog.
.DESCRIPTION
Prepare -InputFile task.json; Quota -Service codex -InputFile quota.json;
Export/Show/Run -TaskId ID; Result/Accept/Reject/Recover -TaskId ID -InputFile evidence.json.
No polling, retries, check-command execution or external service invocation except
one explicit Run of кооперація.ps1 for Codex. Logs/state stay in .agent-runs.
Task: id, goal, owner, controller, approved_by, backlog_ref, allowed_files[],
acceptance[], checks[], work_dir, baseline_commit, service, next_step;
optional sandbox (read-only/workspace-write, default read-only), effort (high/medium).
Quota: source, checked_utc, valid_until_utc, status (available/unknown/exhausted),
windows[] with name and used_percent (null means unknown). No CLI token conversion.
Evidence: actor, evidence[] (paths/links), next_step; Result also status
(review/blocked/failed/interrupted). Accept requires actor=controller and
checks_passed=true; controller Reject records blocked with evidence.
Recover requires processes_stopped=true after manual inspection.
Run enters review on worker completion; only separate controller acceptance closes
the task. Scope is a post-run review gate, not per-file sandbox enforcement.
Interrupted/failed tasks need a new explicitly approved task, never automatic retry.
.EXAMPLE
pwsh -File ./джерела/передача.ps1 Prepare -InputFile ./.agent-runs/task.json
pwsh -File ./джерела/передача.ps1 Quota -Service codex -InputFile ./.agent-runs/quota.json
pwsh -File ./джерела/передача.ps1 Run -TaskId narrow-task -TimeoutSeconds 180
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position=0)]
    [ValidateSet('Prepare','Quota','Export','Show','Run','Result','Accept','Reject','Recover')][string]$Action,
    [ValidatePattern('^[a-z0-9][a-z0-9-]{0,63}$')][string]$TaskId,
    [ValidateSet('codex','claude','lm-studio','comfyui')][string]$Service,
    [string]$InputFile,
    [ValidateRange(1,3600)][int]$TimeoutSeconds = 300,
    [string]$StateRoot = (Join-Path (Split-Path $PSScriptRoot -Parent) '.agent-runs/handoffs')
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($StateRoot)
$null = [IO.Directory]::CreateDirectory($root)
$lock = $null; $workspaceLock = $null; $quotaLock = $null

function Restore-DateStrings($Value) {
    if ($Value -is [DateTime]) { return $Value.ToUniversalTime().ToString('o') }
    if ($Value -is [Collections.IDictionary]) {
        foreach ($key in @($Value.Keys)) { $Value[$key] = Restore-DateStrings $Value[$key] }
    } elseif ($Value -is [Collections.IList]) {
        for ($index = 0; $index -lt $Value.Count; $index++) { $Value[$index] = Restore-DateStrings $Value[$index] }
    }
    return ,$Value
}
function Read-Json([string]$Path) {
    $options = @{ AsHashtable=$true }
    if ((Get-Command ConvertFrom-Json).Parameters.ContainsKey('DateKind')) { $options.DateKind = 'String' }
    return Restore-DateStrings ([IO.File]::ReadAllText($Path) | ConvertFrom-Json @options)
}
function Read-Input {
    if (-not $InputFile) { throw 'InputFile required.' }
    return Read-Json (Resolve-Path -LiteralPath $InputFile).ProviderPath
}
function Require-Text($Object, [string[]]$Names) {
    foreach ($name in $Names) {
        if ($Object[$name] -isnot [string] -or [string]::IsNullOrWhiteSpace($Object[$name])) { throw "Required text: $name" }
    }
}
function Require-List($Object, [string]$Name) {
    if ($Object[$Name] -isnot [array] -or $Object[$Name].Count -eq 0) { throw "Required list: $Name" }
    foreach ($entry in $Object[$Name]) {
        if ($entry -isnot [string] -or [string]::IsNullOrWhiteSpace($entry)) { throw "Invalid list: $Name" }
    }
}
function Take-Lock([string]$Path) {
    try { return [IO.File]::Open($Path, 'OpenOrCreate', 'ReadWrite', 'None') }
    catch { throw "Concurrent operation blocked: $Path" }
}
function Save-Json($Object, [string]$Path) {
    $temporary = "$Path.$([guid]::NewGuid().ToString('N')).tmp"
    try {
        [IO.File]::WriteAllText($temporary, ($Object | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false))
        [IO.File]::Move($temporary, $Path, $true)
    } finally { if ([IO.File]::Exists($temporary)) { [IO.File]::Delete($temporary) } }
}
function Invoke-Git([string]$Directory, [string[]]$Arguments) {
    $result = @(& git -C $Directory -c core.quotepath=false @Arguments 2>&1)
    if ($LASTEXITCODE -ne 0) { throw "Git failed: $($Arguments -join ' ')" }
    return $result
}
function Git-Root([string]$Directory) {
    return (Resolve-Path -LiteralPath @(Invoke-Git $Directory @('rev-parse','--show-toplevel'))[0]).ProviderPath
}
function Changes($Task) {
    $paths = @(Invoke-Git $Task.work_dir @('diff','--no-renames','--name-only', $Task.baseline_commit, '--'))
    $paths += @(Invoke-Git $Task.work_dir @('ls-files','--others','--exclude-standard'))
    return @($paths | Where-Object { $_ } | Sort-Object -Unique)
}
function Scope-Report($Task) {
    $Task.changed_files = @(Changes $Task)
    $Task.out_of_scope = @($Task.changed_files | Where-Object { $_ -cnotin $Task.allowed_files })
}
function Record($Task, [string]$Status, [string]$Actor, [string]$Note) {
    $Task.status = $Status; $Task.updated_utc = [DateTime]::UtcNow.ToString('o')
    $Task.history += @{ utc=$Task.updated_utc; status=$Status; actor=$Actor; note=$Note }
    Save-Json $Task $taskPath
}
function Clear-WorkspaceMarker([string]$Path) {
    if ([IO.File]::Exists($Path)) {
        $marker = Read-Json $Path
        if ($marker.task_path -ne $taskPath) { throw 'Workspace marker belongs to another task.' }
        [IO.File]::Delete($Path)
    }
}
function Export-Prompt($Task) {
    $prompt = @"
Explicit approved task: $($Task.goal)
Owner: $($Task.owner); controller: $($Task.controller); approval recorded by: $($Task.approved_by)
Existing backlog reference: $($Task.backlog_ref)
Workspace: $($Task.work_dir); baseline: $($Task.baseline_commit)
Allowed exact repository-relative files: $($Task.allowed_files -join ', ')
Acceptance: $($Task.acceptance -join '; ')
Checks (perform deliberately, never implicit script evaluation): $($Task.checks -join '; ')
Next step: $($Task.next_step)
Read AGENTS.md and CLAUDE.md; read only relevant handoff history. Stay in this
workspace and scope. No subagents, recurring polling, APIs, scheduler, dispatch,
automatic retries/merges, purchases, access or global config changes. Stop your
background jobs. Push immediately after each commit. Report commit, changed files,
checks and limitations, evidence and next step. Worker completion awaits controller
review and is not acceptance. Do not invoke Claude/LM Studio/ComfyUI yourself.
"@
    $path = Join-Path $taskDir 'prompt.txt'
    [IO.File]::WriteAllText($path, $prompt, [Text.UTF8Encoding]::new($false))
    return $path
}

try {
    if ($Action -eq 'Quota') {
        if (-not $Service) { throw 'Service required.' }
        $quotaLock = Take-Lock (Join-Path $root "quota-$Service.lock")
        $quota = Read-Input
        Require-Text $quota @('source','checked_utc','valid_until_utc','status')
        if ($quota.status -notin @('available','unknown','exhausted')) { throw 'Invalid quota status.' }
        foreach ($field in @('checked_utc','valid_until_utc')) {
            if ($quota[$field] -notmatch '(Z|\+00:00)$') { throw 'Quota timestamps must explicitly be UTC.' }
            $quota[$field] = [DateTimeOffset]::Parse($quota[$field]).UtcDateTime.ToString('o')
        }
        if ([DateTimeOffset]::Parse($quota.checked_utc) -gt [DateTimeOffset]::UtcNow -or
            [DateTimeOffset]::Parse($quota.valid_until_utc) -le [DateTimeOffset]::Parse($quota.checked_utc)) { throw 'Invalid quota interval.' }
        if ($quota.windows -isnot [array]) { throw 'Quota windows array required (empty when unknown).' }
        foreach ($window in $quota.windows) {
            Require-Text $window @('name')
            if (-not $window.ContainsKey('used_percent')) { throw 'used_percent required; use null when unknown.' }
            $value = $window.used_percent
            if ($null -ne $value -and ($value -isnot [ValueType] -or $value -is [bool] -or $value -lt 0 -or $value -gt 100)) { throw 'Invalid used_percent.' }
        }
        $quota.service = $Service
        Save-Json $quota (Join-Path $root "quota-$Service.json")
        Write-Output "Quota recorded: $Service"; exit 0
    }
    if ($Action -eq 'Prepare') {
        $task = Read-Input
        Require-Text $task @('id','goal','owner','controller','approved_by','backlog_ref','work_dir','baseline_commit','service','next_step')
        if ($task.id -notmatch '^[a-z0-9][a-z0-9-]{0,63}$') { throw 'Invalid task id.' }
        if ($TaskId -and $TaskId -ne $task.id) { throw 'TaskId differs from input id.' }
        $TaskId = $task.id
    }
    if (-not $TaskId) { throw 'TaskId required.' }
    $taskDir = Join-Path $root $TaskId
    $lock = Take-Lock (Join-Path $root "$TaskId.lock")
    $taskPath = Join-Path $taskDir 'state.json'
    if ($Action -eq 'Prepare') {
        if (Test-Path -LiteralPath $taskPath) { throw 'Task already exists; no duplicate/retry preparation.' }
        if ($task.service -notin @('codex','claude','lm-studio','comfyui')) { throw 'Invalid service.' }
        if ($task.backlog_ref -notmatch '^аудит/БЕКЛОГ\.md([#: ].+)?$') { throw 'Reference existing аудит/БЕКЛОГ.md.' }
        foreach ($list in @('allowed_files','acceptance','checks')) { Require-List $task $list }
        $task.allowed_files = @($task.allowed_files | ForEach-Object { $_.Replace('\','/') })
        foreach ($file in $task.allowed_files) {
            if ($file -match '(^/|^[A-Za-z]:|(^|/)\.\.?(/|$)|[\r\n*?\[\]])' -or $file.StartsWith('.agent-runs/')) { throw 'Scope requires exact relative file names.' }
        }
        $task.work_dir = Git-Root $task.work_dir
        $task.baseline_commit = @(Invoke-Git $task.work_dir @('rev-parse','--verify', "$($task.baseline_commit)^{commit}"))[0]
        if (-not $task.sandbox) { $task.sandbox = 'read-only' }
        if (-not $task.effort) { $task.effort = 'high' }
        if ($task.sandbox -notin @('read-only','workspace-write') -or $task.effort -notin @('high','medium')) { throw 'Invalid sandbox/effort.' }
        # Build trusted execution state rather than retaining caller-supplied status/run fields.
        $prepared = @{}
        foreach ($field in @('id','goal','owner','controller','approved_by','backlog_ref','allowed_files','acceptance','checks','work_dir','baseline_commit','service','next_step','sandbox','effort')) { $prepared[$field] = $task[$field] }
        $task = $prepared
        $task.schema_version = 1; $task.evidence = @(); $task.history = @(); $task.changed_files = @(); $task.out_of_scope = @()
        $null = [IO.Directory]::CreateDirectory($taskDir)
        Record $task 'ready' $task.approved_by 'Explicit approved task prepared.'
        Write-Output (Export-Prompt $task); exit 0
    }
    if (-not (Test-Path -LiteralPath $taskPath)) { throw 'Unknown task.' }
    $task = Read-Json $taskPath
    switch ($Action) {
        'Show' { $task | ConvertTo-Json -Depth 20 }
        'Export' { Write-Output (Export-Prompt $task) }
        'Run' {
            if ($task.status -ne 'ready') { throw "Run requires ready; current state: $($task.status). No retry." }
            if ($task.service -ne 'codex') { throw 'Only Codex has an explicit local Run; other services use Export and Result.' }
            $quotaPath = Join-Path $root 'quota-codex.json'
            $quotaLock = Take-Lock (Join-Path $root 'quota-codex.lock')
            $reason = 'Quota unknown.'
            if (Test-Path -LiteralPath $quotaPath) {
                $quota = Read-Json $quotaPath
                $known = @($quota.windows | Where-Object { $null -ne $_.used_percent })
                if ($quota.status -ne 'available') { $reason = "Quota $($quota.status)." }
                elseif ([DateTimeOffset]::Parse($quota.valid_until_utc) -le [DateTimeOffset]::UtcNow) { $reason = 'Quota stale.' }
                elseif ($known.Count -ne $quota.windows.Count -or $known.Count -eq 0) { $reason = 'Quota windows unknown.' }
                elseif (@($known | Where-Object { $_.used_percent -ge 100 }).Count) { $reason = 'Quota exhausted.' }
                else { $reason = $null; $task.quota_snapshot = $quota }
            }
            $quotaLock.Dispose(); $quotaLock = $null
            if ($reason) { Record $task 'blocked' $task.controller $reason; throw $reason }
            $workspace = Git-Root $task.work_dir
            if ($workspace -ne $task.work_dir) { throw 'Workspace root changed.' }
            if ($task.sandbox -eq 'workspace-write') {
                $original = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'kod-shi-data'
                if ($workspace.TrimEnd('\','/') -eq [IO.Path]::GetFullPath($original).TrimEnd('\','/')) { throw 'Original main workspace cannot receive write launches.' }
                $branch = (Invoke-Git $workspace @('branch','--show-current')) -join ''
                if (-not $branch -or $branch -in @('main','master')) { throw 'Write launch requires an isolated named branch.' }
            }
            $workspaceState = Join-Path $workspace '.agent-runs'
            $null = [IO.Directory]::CreateDirectory($workspaceState)
            $null = Invoke-Git $workspace @('check-ignore','.agent-runs/')
            $workspaceLock = Take-Lock (Join-Path $workspaceState 'workspace.lock')
            $markerPath = Join-Path $workspaceState 'workspace-run.json'
            if (Test-Path -LiteralPath $markerPath) { throw 'Workspace has an unfinished launch marker; inspect processes and Recover its task explicitly.' }
            if (@(Invoke-Git $workspace @('rev-parse','HEAD'))[0] -ne $task.baseline_commit) { throw 'HEAD differs from explicit baseline.' }
            if (@(Invoke-Git $workspace @('status','--porcelain')).Count) { throw 'Launch requires a clean workspace.' }
            $promptPath = Export-Prompt $task
            $runRoot = Join-Path $taskDir 'run'
            $task.run = @{ owner_pid=$PID; owner_started_utc=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o'); launcher_pid=$null; launcher_started_utc=$null; output_root=$runRoot }
            Record $task 'running' $task.owner 'One explicit Codex launch.'
            Save-Json @{ task_path=$taskPath; run=$task.run } $markerPath
            try {
                $info = [Diagnostics.ProcessStartInfo]::new((Get-Process -Id $PID).Path)
                $info.UseShellExecute = $false; $info.CreateNoWindow = $true
                foreach ($arg in @('-NoProfile','-File',(Join-Path $PSScriptRoot 'кооперація.ps1'),'-PromptFile',$promptPath,'-WorkDir',$workspace,'-Effort',$task.effort,'-Sandbox',$task.sandbox,'-TimeoutSeconds',"$TimeoutSeconds",'-OutputRoot',$runRoot)) { $info.ArgumentList.Add($arg) }
                $process = [Diagnostics.Process]::Start($info)
                $task.run.launcher_pid = $process.Id; $task.run.launcher_started_utc = $process.StartTime.ToUniversalTime().ToString('o')
                Save-Json @{ task_path=$taskPath; run=$task.run } $markerPath
                Save-Json $task $taskPath
                $process.WaitForExit(); $task.run.exit_code = $process.ExitCode; $process.Dispose()
                $summaryFile = @(Get-ChildItem -LiteralPath $runRoot -Filter summary.json -Recurse)[0].FullName
                $task.evidence += $summaryFile
                $summary = Read-Json $summaryFile
                $task.run.summary = $summaryFile; $task.run.cli_tokens = $summary.tokens_reported
                Scope-Report $task
                $status = if ($task.out_of_scope.Count) { 'blocked' } elseif ($summary.status -eq 'completed') { 'review' } elseif ($summary.timed_out) { 'interrupted' } else { 'failed' }
                Record $task $status $task.owner 'Inspect launcher summary and baseline changed_files; completion is not acceptance.'
                Clear-WorkspaceMarker $markerPath
                if ($status -ne 'review') { throw "Run ended in $status; no retry." }
            } catch {
                if ($task.status -eq 'running') { Record $task 'interrupted' $task.owner 'Launch/capture interrupted; inspect processes and recover explicitly.' }
                throw
            }
            Write-Output $taskPath
        }
        { $_ -in @('Result','Accept','Reject','Recover') } {
            $entry = Read-Input
            Require-Text $entry @('actor','next_step'); Require-List $entry 'evidence'
            $workspaceState = Join-Path $task.work_dir '.agent-runs'
            $null = [IO.Directory]::CreateDirectory($workspaceState)
            $null = Invoke-Git $task.work_dir @('check-ignore','.agent-runs/')
            $workspaceLock = Take-Lock (Join-Path $workspaceState 'workspace.lock')
            if ($Action -eq 'Recover') {
                $markerPath = Join-Path $workspaceState 'workspace-run.json'
                $marker = if (Test-Path -LiteralPath $markerPath) { Read-Json $markerPath } else { $null }
                if ($marker -and $marker.task_path -ne $taskPath) { throw 'Workspace marker belongs to another task.' }
                if (($task.status -ne 'running' -and -not $marker) -or $entry.processes_stopped -ne $true) { throw 'Recover requires abandoned running/marker and manual processes_stopped=true evidence.' }
                foreach ($prefix in @('owner','launcher')) {
                    foreach ($run in @($task.run,$marker.run)) {
                        if (-not $run -or -not $run["${prefix}_pid"]) { continue }
                        $active = Get-Process -Id $run["${prefix}_pid"] -ErrorAction SilentlyContinue
                        if ($active -and $active.StartTime.ToUniversalTime().ToString('o') -eq $run["${prefix}_started_utc"]) { throw 'Recorded process is still active; recovery refused.' }
                    }
                }
                Clear-WorkspaceMarker $markerPath
                Scope-Report $task
                $status = if ($task.status -eq 'running') { 'interrupted' } else { $task.status }
            } elseif ($Action -in @('Accept','Reject')) {
                if ($task.status -ne 'review' -or $entry.actor -cne $task.controller) { throw 'Accept/Reject requires review and controller evidence.' }
                if ($Action -eq 'Accept' -and $entry.checks_passed -ne $true) { throw 'Accept requires checks_passed=true with evidence.' }
                if (Test-Path -LiteralPath (Join-Path $task.work_dir '.agent-runs/workspace-run.json')) { throw 'Recover unfinished workspace marker before acceptance.' }
                Scope-Report $task
                $status = if ($Action -eq 'Reject' -or $task.out_of_scope.Count) { 'blocked' } else { 'accepted' }
            } else {
                if ($task.service -eq 'codex' -or $task.status -ne 'ready') { throw 'Result is a one-time manual external service handoff from ready.' }
                if (Test-Path -LiteralPath (Join-Path $workspaceState 'workspace-run.json')) { throw 'Recover unfinished workspace marker before external result.' }
                if ($entry.status -notin @('review','blocked','failed','interrupted')) { throw 'Invalid result status; worker cannot accept.' }
                $status = $entry.status
                Scope-Report $task
                if ($task.out_of_scope.Count) { $status = 'blocked' }
            }
            $task.evidence += $entry.evidence; $task.next_step = $entry.next_step
            Record $task $status $entry.actor 'Explicit evidence handoff.'
            if ($Action -eq 'Accept' -and $status -eq 'blocked') { throw 'Scope violation; controller evidence recorded, acceptance blocked.' }
            Write-Output $taskPath
        }
    }
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
} finally {
    foreach ($held in @($quotaLock,$workspaceLock,$lock)) { if ($held) { $held.Dispose() } }
}
