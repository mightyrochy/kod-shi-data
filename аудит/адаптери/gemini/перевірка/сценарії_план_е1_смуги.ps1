#Requires -Version 5.1
<# Стенд наряду «обгортка-е1-план-gpu», частина смуг (07.11, #1856): справжні Invoke-Task і Start-Markers обох планувальників
(claude_run.ps1, gemini_run.ps1); підмінено лише мережу, запуск процесів наряду, git і модель. Мірила наряду:
(2) збій побудови плану — своє чекання з лічильником і код PLAN_FAILED на межі, а не вічний REVIEW_API;
(3) GPU-наряд, що за секунди пішов у чекання, не тримає GPU решти GPU-позначок того самого проходу. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('plan-e1-lanes-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:failures++ }
}
try {
    $head = 'b' * 40
    $script:Clock = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    foreach ($lane in @('agy', 'claude')) {
        $case = Join-Path $tmp $lane
        $shared = Join-Path $tmp "lanes-$lane"; [void][IO.Directory]::CreateDirectory($shared)
        $OutboxDir = Join-Path $case 'lines'; $OutDir = Join-Path $case 'out'; $WorkDir = $case
        if ($lane -eq 'claude') {
            . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $case -RepoDir $case -OutboxDir "$case/lines" -LaneDir $shared -NoStatus
        } else {
            . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir $case -RepoDir $case -OutDir "$case/out" -LaneDir $shared -EnableCodex
            $script:Lanes = @('agy')
        }
        $script:StateDir = Join-Path $case 'state'; $script:SlotDir = Join-Path $case 'slots'
        foreach ($d in @($case, $script:StateDir, $script:SlotDir, $OutDir, $OutboxDir, "$case/runs")) { [void][IO.Directory]::CreateDirectory($d) }
        $script:Limits = @{slots = @{codex = 4; agy = 4; claude = 4}; claude_laptop = @()}
        $model = $(if ($lane -eq 'claude') { 'cc-claude-sonnet-5-5-medium' } else { 'gemini-3.8-flash-high' })
        $script:Lines = New-Object Collections.ArrayList
        $script:Models = 0
        $script:PlanError = 'AUTO_PAGES'
        $script:Final = ''
        function Get-ReviewTime { $script:Clock }
        function Write-Log([string]$Text) { }
        function Add-Line([string]$Line) { [void]$script:Lines.Add($Line); $true }
        function Get-RefSha { $head }
        function Invoke-Git { [pscustomobject]@{Code = 0; Out = 'Наряд стенда'; Err = ''} }
        function Test-TaskFile { $true }
        function Get-AutoTaskPath { 'аудит/наряди/стенд.md' }
        function Get-TaskSource { 'аудит/наряди/стенд.md' }
        function Find-EngineExe { 'стенд' }
        function Find-CodexExe { 'стенд' }
        function Find-Exe { 'стенд' }
        function Get-ContinueBranch { '' }
        function Get-Quota { [pscustomobject]@{Known = $false} }
        function Get-SleepParent { '' }
        function Reset-WorkTree { }
        function Get-Prompt { 'Наряд стенда' }
        function Add-AutoTaskContext { throw $script:PlanError }
        function Invoke-Agent { $script:Models++; [pscustomobject]@{Tail = ''; Code = 'NO_REPORT'; Report = 'NONE'; Turns = 1} }
        function Invoke-Claude { $script:Models++; [pscustomobject]@{Kind = 'NO_REPORT'} }
        function Complete-Status($Status, $StatePath) {
            $script:Final = [string]$Status.code
            Write-FileAtomic $StatePath "DONE $($Status.id) $($Status.code)"
            Remove-Claim $StatePath
        }
        # Справжній Invoke-Task із перевірюваного джерела (AST), решта середовища — підміни стенда.
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir $(if ($lane -eq 'claude') { 'claude_run.ps1' } else { 'gemini_run.ps1' })), [ref]$tokens, [ref]$errors)
        $fn = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-Task' }, $false)
        . ([scriptblock]::Create($fn.Extent.Text))

        # --- (2) збій плану Е1/автоживого ---
        $m = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/Е1-нічний-живий-20261107/$model/1/gpu-p1`t$head`t$script:Clock")
        if ($lane -eq 'claude') { $m = Add-ClaudeFields $m }
        $sp = Get-StatePath (Get-MarkerKey $m)
        $id = '20261107-160000-abcdefabcdef'; $dir = Join-Path $WorkDir "runs/$id"; [void][IO.Directory]::CreateDirectory($dir)
        $job = @{id = $id; dir = $dir; slot = 'стенд-1'; head = ''; sel = @{engine = $lane; model = $model; emodel = 'стенд'; effort = 'high'; qknown = $false; qleft = 0; qgroup = ''}}
        $kinds = @(); $retakes = @()
        for ($try = 1; $try -le 6; $try++) {
            [void](New-Claim $m $id)
            $null = Invoke-Task $m $job
            $st = Get-MarkerState $m
            $kinds += $st.Kind
            $retakes += (Get-Retakes $sp)
            $script:Clock += 301
        }
        Check "$lane (2): п'ять збоїв плану — WAIT із лічильником 1..5" (($kinds[0..4] -join ',') -ceq 'WAIT,WAIT,WAIT,WAIT,WAIT' -and ($retakes[0..4] -join ',') -ceq '1,2,3,4,5')
        $planLine = @($script:Lines | Where-Object { $_ -match 'PLAN_FAILED' })
        $planDone = $(if ($lane -eq 'claude') { $planLine.Count -eq 1 -and $planLine[0] -ceq "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/Е1-нічний-живий-20261107 PLAN_FAILED" } else { $script:Final -ceq 'PLAN_FAILED' })
        Check "$lane (2): шоста спроба кінчається кодом PLAN_FAILED, а не ще одним REVIEW_API" ($kinds[5] -ne 'WAIT' -and $planDone)
        Check "$lane (2): до моделі збій плану не доходить" ($script:Models -eq 0)
        Check "$lane (2): жоден рядок диспетчерові не називає збій плану REVIEW_API" (@($script:Lines | Where-Object { $_ -match 'REVIEW_API' }).Count -eq 0)

        # Вичерпаний бюджет запитів — чекання вікна: ні лічильника, ні PLAN_FAILED.
        $script:PlanError = 'AUTO_BUDGET'; $script:Final = ''
        $m2 = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/Е1-нічний-живий-20261108/$model/1/gpu-p1`t$head`t$script:Clock")
        if ($lane -eq 'claude') { $m2 = Add-ClaudeFields $m2 }
        $sp2 = Get-StatePath (Get-MarkerKey $m2)
        $id2 = '20261107-160100-abcdefabcdef'; $dir2 = Join-Path $WorkDir "runs/$id2"; [void][IO.Directory]::CreateDirectory($dir2)
        $job2 = @{id = $id2; dir = $dir2; slot = 'стенд-1'; head = ''; sel = $job.sel}
        for ($try = 1; $try -le 10; $try++) { [void](New-Claim $m2 $id2); $null = Invoke-Task $m2 $job2; $script:Clock += 121 }
        Check "$lane (2): AUTO_BUDGET десять разів — WAIT, retakes=0, без PLAN_FAILED" ((Get-MarkerState $m2).Kind -ceq 'WAIT' -and (Get-Retakes $sp2) -eq 0 -and $script:Final -cne 'PLAN_FAILED' -and @($script:Lines | Where-Object { $_ -match 'Е1-нічний-живий-20261108' }).Count -eq 0)

        # --- (3) GPU решти позначок проходу ---
        $script:Markers = @()
        $names = @('Е1-нічний-живий-20261109', 'Річ-колір-вимір', 'Річ-кадр-варіант-кадри', 'проба-gpu')
        $conds = @('gpu-p1', 'gpu-p1', 'gpu-p2', 'gpu-p3')
        for ($i = 0; $i -lt 4; $i++) {
            $x = ConvertTo-Marker ("refs/remotes/origin/gemini-queue/$($names[$i])/$model/1/$($conds[$i])`t$head`t$($script:Clock - 600 + $i)")
            if ($lane -eq 'claude') { $x = Add-ClaudeFields $x }
            $script:Markers += $x
        }
        # Е1 — у нічної позначки gemini_run окремий шлях (Get-NightlyMarker); для смуги agy беремо три звичайні GPU-позначки.
        if ($lane -ne 'claude') { $script:Markers = @($script:Markers | Select-Object -Skip 1) }
        function Get-Markers { $script:Markers }
        function Get-NightlyMarker { }
        function Select-Engine($M, [long]$After) { [pscustomobject]@{Engine = @{Name = 'agy'; Model = 'стенд'; Effort = 'high'}; Model = $M.Model; Quota = @{Blocked = $false; Known = $false; Group = ''; Left = 0}} }
        function Get-FreeSlot { 'стенд-1' }
        function Test-SlugBusy { $false }
        function Repair-GpuModels { $true }
        function Get-GpuBusyReason($Workers, [switch]$LockHeld) {
            $script:GpuHoldReason = ''
            if (@($Workers | Where-Object { $_.Gpu -and -not $_.Proc.HasExited }).Count -gt 0) { $script:GpuHoldReason = 'замок GPU іншого наряду'; return 'GPU: її тримає власний наряд обгортки' }
            ''
        }
        $script:Behaviour = @()   # як веде себе кожен запущений процес: 'ВИЙШОВ' (пішов у чекання) чи 'ЖИВИЙ' (модель працює)
        $script:Started = New-Object Collections.ArrayList
        function Start-Worker($Job, [string]$Dir) {
            $mode = $script:Behaviour[$script:Started.Count]
            [void]$script:Started.Add($Job.name)
            if ($mode -ceq 'ВИЙШОВ') { return [pscustomobject]@{Slot = $Job.slot; Slug = $Job.slug; Gpu = [bool]$Job.gpu; Marker = $Job.name; Proc = [pscustomobject]@{HasExited = $true}} }
            # Живий процес пише STARTED із початком прогону — модель стартувала.
            Write-FileAtomic (Get-StatePath "$($Job.ref) $($Job.sha)") ('STARTED ' + (@{start = ('c' * 40); id = $Job.id} | ConvertTo-Json -Compress))
            [pscustomobject]@{Slot = $Job.slot; Slug = $Job.slug; Gpu = [bool]$Job.gpu; Marker = $Job.name; Proc = [pscustomobject]@{HasExited = $false}}
        }
        function Invoke-HealthBeat { }
        $script:GpuStartWaitSeconds = 3; $script:GpuStartPollMs = 20
        $skipFile = Join-Path $(if ($lane -eq 'claude') { $WorkDir } else { $OutDir }) 'skipped.json'
        function Read-PassSkips {
            $rows = @{}
            foreach ($r in @(ConvertFrom-Json ([IO.File]::ReadAllText($skipFile)))) { if ($null -ne $r) { $rows[[string]$r.marker] = [string]$r.why } }
            $rows
        }
        $gpuCount = @($script:Markers).Count

        # Проход 1: перший наряд пішов у чекання за секунди — GPU вільна, другий її бере й справді запускає модель, третій чекає.
        $script:Behaviour = @('ВИЙШОВ', 'ЖИВИЙ', 'ЖИВИЙ', 'ЖИВИЙ')
        $workers = New-Object Collections.ArrayList
        $script:PassSkips = @{}
        $result = @(Start-Markers $workers)
        $startedNow = $(if ($lane -eq 'claude') { [int]$result[0] } else { [int]$result[-1] })
        Check "$lane (3): GPU-наряд, що вийшов у чекання, віддав GPU наступній позначці того ж проходу (запущено 2 з $gpuCount)" ($startedNow -eq 2 -and $script:Started.Count -eq 2)
        $skips = Read-PassSkips
        Check "$lane (3): решта позначок стоїть, бо GPU тепер справді за живим нарядом" ($skips.Count -eq ($gpuCount - 2) -and @($skips.Values | Where-Object { $_ -cmatch 'її тримає власний наряд обгортки|її щойно взяв наряд цього проходу' }).Count -eq $skips.Count)
        Check "$lane (3): запущені позначки не названо «щойно взяла» через першу" (@($script:Started | Where-Object { $skips.ContainsKey($_) }).Count -eq 0)

        # Проход 2: перший наряд тримає GPU (модель стартувала) — решта стоїть із причиною, без очікування TIMEOUT.
        foreach ($mk in $script:Markers) { Remove-Item -LiteralPath (Get-StatePath (Get-MarkerKey $mk)) -Force -ErrorAction SilentlyContinue; Remove-Claim (Get-StatePath (Get-MarkerKey $mk)) }
        $script:Started.Clear(); $script:Behaviour = @('ЖИВИЙ', 'ЖИВИЙ', 'ЖИВИЙ', 'ЖИВИЙ'); $script:PassSkips = @{}
        $workers = New-Object Collections.ArrayList
        $t0 = Get-Date
        $result = @(Start-Markers $workers)
        $startedNow = $(if ($lane -eq 'claude') { [int]$result[0] } else { [int]$result[-1] })
        Check "$lane (3): живий GPU-наряд тримає GPU — запущено один, решта стоїть, чекання не довше за STARTED" ($startedNow -eq 1 -and ((Get-Date) - $t0).TotalSeconds -lt 2)
        Check "$lane (3): решта GPU-позначок названа «щойно взяв наряд цього проходу»" (@((Read-PassSkips).Values | Where-Object { $_ -cmatch 'щойно взяв наряд цього проходу' }).Count -eq ($gpuCount - 1))
    }
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^plan-e1-lanes-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($failures) { exit 1 }
