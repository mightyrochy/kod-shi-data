$ErrorActionPreference = 'Stop'
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$head = '8e15542dbf4990037529e5e99dcf6d71be3068f0'
$base = 'bbc87e297c357187afbbe16221fd94c61f590f2b'
$probeDir = Join-Path $env:TEMP ('review-2728-' + [guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $probeDir)
$bom = New-Object System.Text.UTF8Encoding($true)
function Save-Blob([string]$Ref, [string]$Path, [string]$Name) {
    $text = (& git show ($Ref + ':' + $Path)) -join "`n"
    if ($LASTEXITCODE -ne 0) { throw "Не отримано $Ref : $Path" }
    [IO.File]::WriteAllText((Join-Path $probeDir $Name), $text, $bom)
}
foreach ($name in @('queue_lanes.ps1', 'wrapper_health.ps1', 'claude_run.ps1', 'смуги.json')) {
    Save-Blob $head ('аудит/адаптери/gemini/' + $name) $name
}
Save-Blob $base 'аудит/адаптери/gemini/смуги.json' 'before.json'
Save-Blob $base 'аудит/наряди/gpu-навантаження-хто.md' 'before-task.md'
Save-Blob $head 'аудит/наряди/gpu-навантаження-хто.md' 'task.md'
. (Join-Path $probeDir 'queue_lanes.ps1')
$tokens = $null; $errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $probeDir 'claude_run.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw 'Помилки розбору PowerShell' }
foreach ($name in @('Start-Markers', 'Get-Prompt', 'Add-ClaudeFields')) {
    $fn = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    if ($null -eq $fn) { throw "Нема функції $name" }
    . ([scriptblock]::Create($fn.Extent.Text))
}
# Зовнішні дії замінено; справжні функції розбирають позначку, конфігурацію та промпт.
function Invoke-Git { param($GitArgs, [switch]$AllowFail) @{Code=0; Out=[IO.File]::ReadAllText($script:ConfigFile)} }
function Write-Log {}
function Save-Skips {}
function Get-Markers { $script:Marker }
function Get-StatePath { Join-Path $probeDir 'probe-state.txt' }
function Get-MarkerState { 'READY' }
function Test-MarkerReady { $true }
function Get-OrderedMarkers { param($Markers) $Markers }
function Get-FreeSlot { 'claude1' }
function Test-SlugBusy { $false }
function New-Id { 'probe' }
function New-Claim { $true }
function Start-Worker { [pscustomobject]@{Started=$true} }
function Complete-Task { $script:Rejected++ }
function Get-GpuBusyReason { $script:GpuChecks++; throw 'Для позначки без gpu викликано перевірку простою GPU' }
$script:StateDir = ''; $script:Rejected = 0; $script:GpuChecks = 0
$WorkDir = $probeDir; $MarkerMaxAgeDays = 7
$slug = 'gpu-навантаження-хто'
$line = $script:QueuePrefix + $slug + '/cc-claude-sonnet-5-5-medium/1/p0' + "`t$head`t" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$script:Marker = ConvertTo-Marker $line
if (-not $script:Marker.Valid -or $script:Marker.Lane -ne 'claude' -or $script:Marker.Gpu) { throw 'Некоректне розпізнавання позначки' }
foreach ($config in @('before.json', 'смуги.json')) {
    $script:ConfigFile = Join-Path $probeDir $config
    $script:Limits = Get-Limits
    $workers = New-Object System.Collections.ArrayList
    $result = @(Start-Markers $workers)
    if ($config -eq 'before.json' -and ($result[0] -ne 0 -or $script:Rejected -ne 1)) { throw 'Не відтворено відмову ДО' }
    if ($config -eq 'смуги.json' -and ($result[0] -ne 1 -or $workers.Count -ne 1)) { throw 'Не відтворено запуск ПІСЛЯ' }
    'Маршрут {0}: запущено={1}, GPU-перевірок={2}' -f $config, $result[0], $script:GpuChecks
}
function Get-TaskDirText { '' }
$task = [IO.File]::ReadAllText((Join-Path $probeDir 'task.md'))
$beforeTask = [IO.File]::ReadAllText((Join-Path $probeDir 'before-task.md'))
$prompt = Get-Prompt $script:Marker $task '' $probeDir
if (-not $prompt.Contains('Гілка — `claude/…`, запушена тобою.')) { throw 'Нема вимог смуги Claude' }
if (-not $task.Contains('Роль — ВИКОНАВЕЦЬ (`аудит/ВИКОНАВЕЦЬ.md`)') -or -not $task.Contains('адаптер — `аудит/НОУТБУК.md`')) { throw 'Договір не перенесено' }
if ($task.Contains('GEMINI.md') -or $task.Contains('Гілка `gemini/')) { throw 'Лишився суперечливий адаптер чи гілка' }
if ($beforeTask.Split(@('**Що зробити.**'), [StringSplitOptions]::None)[1] -cne $task.Split(@('**Що зробити.**'), [StringSplitOptions]::None)[1]) { throw 'Змінилося мірило діагностики' }
'Промпт: ВИКОНАВЕЦЬ + НОУТБУК.md + claude/гілка; старого договору GEMINI.md немає'
'Мірило: 10 хв, кожні 30 с, джерела вимірів і звіт збережено дослівно'
$before = [IO.File]::ReadAllText((Join-Path $probeDir 'before.json')) | ConvertFrom-Json
$after = [IO.File]::ReadAllText((Join-Path $probeDir 'смуги.json')) | ConvertFrom-Json
if (@($after.claude_laptop | Where-Object { $_ -ceq $slug }).Count -ne 1) { throw 'Назва має бути рівно один раз' }
$before.claude_laptop = @($before.claude_laptop) + $slug
if (($before | ConvertTo-Json -Depth 10 -Compress) -cne ($after | ConvertTo-Json -Depth 10 -Compress)) { throw 'Змінилися сторонні налаштування смуг' }
'Конфігурація: додано лише одну назву, решта значень незмінна'
'Проба завершилася; процесів моделей і живих GPU-вимірів не запускала'
