param([Parameter(Mandatory=$true)][string]$WrapperRoot)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$root = Join-Path $env:TEMP ('night-review-' + [guid]::NewGuid().ToString('N'))
$seed = Join-Path $root 'seed'
[void][IO.Directory]::CreateDirectory($seed)
function Git([string[]]$A) {
    $r = & git.exe -C $seed @A 2>&1
    if ($LASTEXITCODE) { throw ($r -join "`n") }
    ($r -join "`n").Trim()
}
[void](Git @('init','-q','-b','main'))
[void](Git @('config','user.name','Перевірка'))
[void](Git @('config','user.email','review@example.invalid'))
[void][IO.Directory]::CreateDirectory("$seed/аудит/наряди")
[IO.File]::WriteAllText("$seed/аудит/наряди/автоживий.md", 'Нічний Е1', [Text.Encoding]::UTF8)
$build = 'b' * 40
[IO.File]::WriteAllText("$seed/build.txt", $build, [Text.Encoding]::ASCII)
[void](Git @('add','.'))
[void](Git @('commit','-qm','Дозвіл для ізольованої проби'))
$sha = Git @('rev-parse','HEAD')
[void](Git @('update-ref','refs/remotes/origin/main',$sha))
. (Join-Path $WrapperRoot 'claude_run.ps1') -WorkDir "$root/claude" -RepoDir $seed -OutboxDir "$root/out" -PublishDir "$root/pub" -GeminiOutDir "$root/gem" -GeminiStateDir "$root/gem/state" -LaneDir "$root/lanes" -TmpDir "$root/tmp" -NoStatus
$script:NoHooks = "$root/no-hooks"
$script:StateDir = "$root/state"
$RunsDir = "$root/runs"
foreach ($d in @($script:StateDir,$WorkDir,$RunsDir)) { [void][IO.Directory]::CreateDirectory($d) }
$script:Limits = @{slots=@{claude=1};claude_laptop=@()}
# Межі проби: модель, GPU й процес не запускаються. Читач git, розбір позначки,
# порядок, стани та атомарне взяття лишаються справжніми функціями голови PR.
function Repair-GpuModels { }
function Get-FreeSlot { 'claude-1' }
function Test-SlugBusy { $false }
function Get-GpuBusyReason { '' }
function Write-Log { }
function Save-Skips { }
function Start-Worker($Job,$Dir) {
    $script:Captured = $Job
    [pscustomobject]@{Slug=$Job.slug;Proc=[pscustomobject]@{HasExited=$false}}
}
$nowUtc = [datetime]::UtcNow
$day = $nowUtc.ToString('yyyyMMdd')
$oldDay = $nowUtc.AddDays(-1).ToString('yyyyMMdd')
Write-Output ('Час проби UTC: ' + $nowUtc.ToString('o'))
foreach ($case in @('прострочена-доба','автоживий-після-перенесення','чинний-дозвіл')) {
    foreach ($ref in @(Git @('for-each-ref','--format=%(refname)',$script:QueuePrefix))) {
        foreach ($line in ($ref -split "`n")) { if ($line) { [void](Git @('update-ref','-d',$line)) } }
    }
    Get-ChildItem -LiteralPath $script:StateDir -File | Remove-Item
    $permitDay = $(if ($case -eq 'прострочена-доба') { $oldDay } else { $day })
    $slug = 'Е1-нічний-живий-' + $permitDay
    $original = $script:QueuePrefix + $slug + '/gpt-6.1-sol-high/1/gpu-p8'
    [void](Git @('update-ref',$original,$sha))
    if ($case -eq 'автоживий-після-перенесення') {
        [void](Git @('update-ref',($script:QueuePrefix + "автоживий-$build/gpt-6.1-sol-high/1/p2-gpu"),$sha))
    }
    $codex = @(Get-NightlyMarker $nowUtc).Count
    [void](Git @('update-ref','-d',$original))
    [void](Git @('update-ref',($script:QueuePrefix + $slug + '/cc-claude-sonnet-5-5-medium/1/gpu-p8'),$sha))
    $script:Captured = $null
    $workers = New-Object Collections.ArrayList
    $result = Start-Markers $workers
    Write-Output ("$case : Get-NightlyMarker=$codex; Start-Markers=$($result[0]); New-Claim=$(@(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.claim').Count); slug=$($script:Captured.slug)")
    if ($result[0] -ne 1) { throw "Не відтворено запуск: $case" }
    if ($case -ne 'чинний-дозвіл' -and $codex -ne 0) { throw "Контроль Codex не відсік $case" }
    if (Test-AutoPlanEmpty $slug "ПЛАН ЖИВОГО — ДАНІ (JSON):`n{`"scenes`":{}}") { throw 'Нічний несподівано відсікся порожнім планом' }
}
Write-Output 'Відтворено: 2 обходи обмежень; контроль чинного дозволу запускається; моделі й GPU не запускалися.'
