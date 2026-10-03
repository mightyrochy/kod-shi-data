#requires -Version 7.0
<#
.SYNOPSIS
One explicit Codex worker, authenticated with the existing ChatGPT login.
.DESCRIPTION
No retries, scheduler, commits or merges. Logs stay local in .agent-runs/.
CLI overrides apply only to this process; user settings and auth are not changed.
Standard speed requests service_tier=default; logs do not prove server routing.
.EXAMPLE
pwsh -File ./джерела/кооперація.ps1 -PromptFile ./task.txt -WorkDir .
pwsh -File ./джерела/кооперація.ps1 -PromptFile ./task.txt -WorkDir . -Effort medium -TimeoutSeconds 120
pwsh -File ./джерела/кооперація.ps1 -PromptFile ./task.txt -WorkDir . -Sandbox workspace-write
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$PromptFile,
    [Parameter(Mandatory)][string]$WorkDir,
    [ValidateSet('gpt-6.1-sol')][string]$Model = 'gpt-6.1-sol',
    [ValidateSet('medium', 'high')][string]$Effort = 'high',
    [ValidateSet('read-only', 'workspace-write')][string]$Sandbox = 'read-only',
    [ValidateRange(1, 3600)][int]$TimeoutSeconds = 300,
    [string]$OutputRoot = (Join-Path (Split-Path $PSScriptRoot -Parent) '.agent-runs')
)
$ErrorActionPreference = 'Stop'
$runDir = Join-Path ([IO.Path]::GetFullPath($OutputRoot)) ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
$null = New-Item -ItemType Directory -Path $runDir
$watch = [Diagnostics.Stopwatch]::StartNew()
$summary = [ordered]@{
    started_utc = [DateTime]::UtcNow.ToString('o'); requested_model = $Model; requested_effort = $Effort
    service_tier = 'default'; sandbox = $Sandbox; timeout_seconds = $TimeoutSeconds
    auth = $null; arguments = @(); work_dir = $null; status = 'error'; error = $null
    exit_code = $null; timed_out = $false; thread_id = $null; tokens_reported = $null
    elapsed_seconds = $null; run_dir = $runDir
}
$returnCode = 1

function Invoke-CodexProcess([string[]]$CliArguments, [string]$Prefix, [string]$InputText = '') {
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $script:codexPath
    $info.WorkingDirectory = $script:resolvedWorkDir
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardInputEncoding = [Text.UTF8Encoding]::new($false)
    foreach ($argument in $CliArguments) { $info.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    $stdout = [IO.File]::Create((Join-Path $runDir "$Prefix.stdout.jsonl"))
    $stderr = [IO.File]::Create((Join-Path $runDir "$Prefix.stderr.log"))
    $outputTask = $null; $errorTask = $null; $started = $false; $timedOut = $false
    $processWatch = [Diagnostics.Stopwatch]::StartNew()
    try {
        $started = $process.Start()
        $outputTask = $process.StandardOutput.BaseStream.CopyToAsync($stdout)
        $errorTask = $process.StandardError.BaseStream.CopyToAsync($stderr)
        $inputTask = $process.StandardInput.WriteAsync($InputText)
        if (-not $inputTask.Wait($TimeoutSeconds * 1000)) { $timedOut = $true }
        if (-not $timedOut) {
            $process.StandardInput.Close()
            $remaining = [Math]::Max(0, $TimeoutSeconds * 1000 - [int]$processWatch.ElapsedMilliseconds)
            $timedOut = -not $process.WaitForExit($remaining)
        }
        if ($timedOut) {
            if (-not $process.HasExited) { $process.Kill($true) }
            if (-not $process.WaitForExit(5000)) { throw 'Process termination failed.' }
        }
        if (-not [Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($outputTask, $errorTask), 5000)) {
            throw 'Log capture did not finish.'
        }
        return @{ exit_code = $process.ExitCode; timed_out = $timedOut }
    }
    finally {
        if ($started -and -not $process.HasExited) { $process.Kill($true); $null = $process.WaitForExit(5000) }
        $stdout.Dispose(); $stderr.Dispose(); $process.Dispose()
    }
}

try {
    $script:resolvedWorkDir = (Resolve-Path -LiteralPath $WorkDir).ProviderPath
    if (-not [IO.Directory]::Exists($resolvedWorkDir)) { throw 'WorkDir must be a directory.' }
    $summary.work_dir = $resolvedWorkDir
    $resolvedPrompt = (Resolve-Path -LiteralPath $PromptFile).ProviderPath
    $prompt = [IO.File]::ReadAllText($resolvedPrompt)
    if ([string]::IsNullOrWhiteSpace($prompt)) { throw 'PromptFile must contain an explicit task.' }
    # Never print environment values or silently fall back to paid API authentication.
    $blockedVariables = @(Get-ChildItem Env: | Where-Object {
        $_.Name -match '(?i)(API_?KEY|^CODEX_ACCESS_TOKEN$|^OPENAI_IDENTITY_TOKEN$|^OPENAI_WIF_)' -and
        -not [string]::IsNullOrWhiteSpace($_.Value)
    })
    if ($blockedVariables.Count) {
        $summary.error = 'API-key or alternate authentication environment detected; use a clean ChatGPT-authenticated environment.'
        throw $summary.error
    }
    $command = Get-Command codex -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $command -or $command.Source -match '\.(cmd|bat)$') {
        $summary.error = 'Native Codex CLI missing. Install or locate codex.exe before running.'
        throw $summary.error
    }
    $script:codexPath = $command.Source
    $authResult = Invoke-CodexProcess @('login', 'status') 'auth'
    if ($authResult.timed_out) {
        $summary.timed_out = $true; $summary.status = 'timeout'; $returnCode = 124
        $summary.error = 'Codex login status timed out.'; throw $summary.error
    }
    $authText = [IO.File]::ReadAllText((Join-Path $runDir 'auth.stdout.jsonl')) +
        [IO.File]::ReadAllText((Join-Path $runDir 'auth.stderr.log'))
    if ($authResult.exit_code -ne 0 -or $authText.Trim() -ne 'Logged in using ChatGPT') {
        $summary.error = 'ChatGPT login required. Run codex login interactively, then retry explicitly.'
        throw $summary.error
    }
    $summary.auth = 'ChatGPT'
    $cliArguments = @('exec', '--json', '--color', 'never', '-C', $resolvedWorkDir,
        '-m', $Model, '-s', $Sandbox, '-c', "model_reasoning_effort=$Effort",
        '-c', 'service_tier=default', '-c', 'approval_policy=never',
        '-c', 'model_provider=openai', '-c', 'forced_login_method=chatgpt',
        '-o', (Join-Path $runDir 'final.txt'), '-')
    $summary.arguments = $cliArguments
    $result = Invoke-CodexProcess $cliArguments 'worker' $prompt
    $summary.exit_code = $result.exit_code
    $summary.timed_out = $result.timed_out
    $completed = $false; $failed = $false
    foreach ($line in [IO.File]::ReadLines((Join-Path $runDir 'worker.stdout.jsonl'))) {
        try { $event = $line | ConvertFrom-Json -AsHashtable } catch { continue }
        if ($event.type -eq 'thread.started') { $summary.thread_id = $event.thread_id }
        if ($event.type -eq 'turn.completed') { $summary.tokens_reported = $event.usage; $completed = $true }
        if ($event.type -in @('turn.failed', 'error')) { $failed = $true }
    }
    if ($result.timed_out) {
        $summary.status = 'timeout'; $summary.error = 'Worker exceeded timeout; process tree terminated.'; $returnCode = 124
    } elseif ($result.exit_code -ne 0 -or $failed -or -not $completed -or -not (Test-Path -LiteralPath (Join-Path $runDir 'final.txt'))) {
        $summary.error = 'Worker failed or did not complete; inspect local worker logs.'
    } else { $summary.status = 'completed'; $returnCode = 0 }
}
catch {
    if (-not $summary.error) { $summary.error = 'Launcher failed during input validation, process startup or log capture.' }
}
finally {
    $watch.Stop()
    $summary.elapsed_seconds = [Math]::Round($watch.Elapsed.TotalSeconds, 3)
    $summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runDir 'summary.json') -Encoding utf8
}
Write-Output ("{0}: {1}" -f $summary.status, (Join-Path $runDir 'summary.json'))
if ($summary.error) { Write-Output $summary.error }
exit $returnCode
