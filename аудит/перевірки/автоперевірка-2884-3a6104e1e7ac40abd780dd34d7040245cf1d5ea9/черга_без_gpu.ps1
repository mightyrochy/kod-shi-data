#Requires -Version 5.1
<# Відтворює один прохід справжнього планувальника з CPU-позначкою й незавершеним GPU-знімком.
REST, перелік позначок і запуск агента підробні; жодних живих моделей чи агентів не запускає. #>
param([string]$SourceDir, [ValidateSet('gemini', 'claude')][string]$Lane,
    [ValidateSet('json', 'rest')][string]$Fault)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$caseDir = Join-Path $env:TEMP ('cpu-queue-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($caseDir)
try {
    . (Join-Path $SourceDir ($Lane + '_run.ps1'))
    $LaneDir = $caseDir; $RunsDir = $caseDir; $WorkDir = $caseDir; $OutDir = $caseDir
    $script:StateDir = $caseDir; $script:SlotDir = $caseDir
    $script:Limits = @{ slots = @{ claude = 1; codex = 1; agy = 1 }; claude_laptop = @('стенд-cpu') }
    $script:Started = 0; $script:ReadMarkers = 0; $script:Saved = 0
    $script:Marker = [pscustomobject]@{ Valid = $true; Lane = $(if ($Lane -eq 'claude') { 'claude' } else { 'codex' })
        Ref = 'ref'; Name = 'gemini-queue/стенд-cpu/gpt-test/1'; Slug = 'стенд-cpu'; Model = 'gpt-test'; Sha = 'a' * 40
        Time = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Gpu = $false; Prio = 1; Deadline = ''; N = '1'; Cond = ''
        Off = $false; Claude = 'claude-test'; Effort = 'high' }
    function Get-Markers { $script:ReadMarkers++; $script:Marker }
    function Get-NightlyMarker { }
    function Get-OrderedMarkers($Markers) { $Markers }
    function Add-ClaudeFields($Marker) { $Marker }
    function Get-MarkerState { [pscustomobject]@{ Kind = 'NEW' } }
    function Test-MarkerReady { $true }
    function Test-SlugBusy { $false }
    function Get-FreeSlot { 'test-1' }
    function New-Id { 'test-run' }
    function New-RunId { 'test-run' }
    function New-Claim { $true }
    function Select-Engine { [pscustomobject]@{ Engine = [pscustomobject]@{ Name = 'codex'; Model = 'gpt-test'; Effort = 'high' }
        Model = 'gpt-test'; Quota = [pscustomobject]@{ Blocked = $false; Known = $true; Left = 100; Group = 'test' } } }
    function Start-Worker { $script:Started++; [pscustomobject]@{ Slug = 'стенд-cpu'; Gpu = $false; Proc = [pscustomobject]@{ HasExited = $false } } }
    function Save-Skips { $script:Saved++ }
    function Write-Log([string]$Text, [switch]$Required) { }
    function Invoke-RestMethod { throw 'стенд: REST недоступний' }
    $snapshot = $(if ($Fault -eq 'json') { '{' } else {
        '{"v":1,"marker":"gpu-job","run":"old-run","before":[{"id":"owner-id","model":"owner-model"}]}' })
    [IO.File]::WriteAllText((Join-Path $caseDir 'gpu-models.json'), $snapshot)
    $workers = New-Object System.Collections.ArrayList
    $result = @(Start-Markers $workers)
    "${Lane}/${Fault}: CPU_запущено=$script:Started; чергу_прочитано=$script:ReadMarkers; пропуски_збережено=$script:Saved; результат=$($result[0])"
} finally {
    # Знімає лише файли власного сценарію в TEMP, без рекурсивного прибирання.
    if ([IO.Directory]::Exists($caseDir)) {
        foreach ($file in [IO.Directory]::GetFiles($caseDir)) { [IO.File]::Delete($file) }
        $runDir = Join-Path $caseDir 'runs/test-run'
        if ([IO.Directory]::Exists($runDir)) { [IO.Directory]::Delete($runDir) }
        $runs = Join-Path $caseDir 'runs'
        if ([IO.Directory]::Exists($runs)) { [IO.Directory]::Delete($runs) }
        $directRun = Join-Path $caseDir 'test-run'
        if ([IO.Directory]::Exists($directRun)) { [IO.Directory]::Delete($directRun) }
        [IO.Directory]::Delete($caseDir)
    }
}
