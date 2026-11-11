param([string]$Tree, [string]$TaskTmp)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$probeRoot = Join-Path $TaskTmp 'probe-3469-data'
[void][IO.Directory]::CreateDirectory($probeRoot)
$gout = Join-Path $probeRoot 'gout'
[void][IO.Directory]::CreateDirectory($gout)
. (Join-Path $Tree 'аудит/адаптери/gemini/claude_run.ps1') -WorkDir $probeRoot -RepoDir $Tree -GeminiOutDir $gout -GeminiStateDir $probeRoot -LaneDir $probeRoot -NoStatus
function Test-ClaudeBusy { $false }
function Test-GeminiBusy { $false }
function Read-ClaudeQuota { $null }
function Test-ClaudeQuotaZero { (Get-ClaudeZeroReset) -ne '' }
$now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$script:ProbeMarker = [pscustomobject]@{Valid=$true; Lane='agy'; Model='gemini-3-pro-low'; Slug='проба'; Time=$now}
function Get-Markers { $script:ProbeMarker }
function Get-MarkerStateIn { [pscustomobject]@{ Kind='WAIT'; Wait=[pscustomobject]@{group='GEMINIMODELS'; until=($now - 60)}} }
foreach ($v in @(@('24bfe920e97d5bccc509a400f6a445f1693ca687','Before'), @('01b93827156d2aba3b5e6bb14c1a97469211d1c7','Main'))) {
    $old = (git -C $Tree show ($v[0] + ':аудит/адаптери/gemini/claude_run.ps1')) -join "`n"
    $tokens=$null; $parseErrors=$null
    $ast=[Management.Automation.Language.Parser]::ParseInput($old,[ref]$tokens,[ref]$parseErrors)
    $f=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Test-IdleBusy'},$true)
    . ([scriptblock]::Create(($f.Extent.Text -replace '^function Test-IdleBusy',('function Test-IdleBusy' + $v[1]))))
}
$pools='{"groups":[{"g":"GEMINIMODELS","n":"gemini models"},{"g":"CLAUDEANDGPTMODE","n":"claude and gpt models"}]}'
[IO.File]::WriteAllText((Join-Path $gout 'pools.json'),$pools,$utf)
$bad=0
foreach ($case in @(
    @('pro: Claude має квоту','gemini-3-pro-low',40,$false,$false,$true),
    @('pro: Codex доступний','gemini-3-pro-low',0,$true,$false,$true),
    @('pro: весь каскад на нулі','gemini-3-pro-low',0,$true,$true,$false),
    @('flash: Gemini на нулі','gemini-3-flash',40,$false,$false,$false)
)) {
    $script:ProbeMarker.Model=$case[1]
    $reset=Get-UtcStamp ([datetime]::UtcNow.AddHours(2))
    $beat=@{codex_fallback=$case[3]; quota=@{windows=@(@{g='GEMINIMODELS';w='DAY';left=0;reset=$reset},@{g='CLAUDEANDGPTMODE';w='DAY';left=$case[2];reset=$reset})}}
    if ($case[4]) {$beat.codex=@{refused=(Get-UtcStamp ([datetime]::UtcNow));reset=$reset}}
    [IO.File]::WriteAllText((Join-Path $gout 'heartbeat.json'),($beat|ConvertTo-Json -Depth 8),$utf)
    $g=Read-GeminiBeat
    $base=Test-IdleBusyMain $g
    $before=Test-IdleBusyBefore $g
    $after=Test-IdleBusy $g
    if ($after -ne $case[5]) {$bad++}
    "СЦЕНА $($case[0]): main=$base; 24bfe920=$before; ec77856a=$after; причина=$script:IdleWhy"
}
"ПРОБА: 4 сцени; відхилень=$bad"
exit $bad
