param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$SourceDir = (Resolve-Path -LiteralPath $SourceDir).Path
$probeDir = Join-Path $env:TEMP ('idle-cascade-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($probeDir)
. (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir $probeDir -RepoDir $probeDir -OutDir "$probeDir/out" -LaneDir "$probeDir/lanes"
function Write-Log([string]$Text) { }
$script:Agy = 'unused-agy'
$script:AgyModels = @('gemini-3-pro-high', 'claude-opus-5-5-high')
$reset = [DateTimeOffset]::UtcNow.AddDays(1)
$script:ProbeUsage = [pscustomobject]@{ Known=$true; Text=''; Windows=@(
    [pscustomobject]@{Name='Gemini Models'; Left=0; Reset=$reset},
    [pscustomobject]@{Name='Claude and GPT models'; Left=40; Reset=$reset}
)}
function Read-Usage { $script:ProbeUsage }
$past = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 60
$m = [pscustomobject]@{Valid=$true; Lane='agy'; Slug='каскад'; Model='gemini-3-pro-high'; Time=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds(); Ref='refs/remotes/origin/gemini-queue/каскад/gemini-3-pro-high/1'; Name='gemini-queue/каскад/gemini-3-pro-high/1'; Sha=('a' * 40)}
$selected = Select-Engine $m $past
"Select-Engine: model=$($selected.Model); blocked=$($selected.Quota.Blocked); left=$($selected.Quota.Left)"
. (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$probeDir/claude" -RepoDir $probeDir -OutboxDir "$probeDir/box" -PublishDir "$probeDir/pub" -GeminiOutDir "$probeDir/out" -GeminiStateDir "$probeDir/gstate" -LaneDir "$probeDir/lanes" -TmpDir "$probeDir/tmp" -NoStatus
[void][IO.Directory]::CreateDirectory("$probeDir/gstate")
[void][IO.Directory]::CreateDirectory("$probeDir/claude/state")
$script:StateDir = "$probeDir/claude/state"
function Test-ClaudeBusy { $false }
function Test-GeminiBusy { $false }
function Read-ClaudeQuota { $null }
$script:ProbeMarker = $m
function Get-Markers { $script:ProbeMarker }
Write-FileAtomic (Get-StatePath (Get-MarkerKey $m) "$probeDir/gstate") ('WAIT {"until":' + $past + ',"group":"GEMINIMODELS"}')
$beat = [pscustomobject]@{Codex=$null; Quota=[pscustomobject]@{Windows=@(
    [pscustomobject]@{G='GEMINIMODELS'; Left=0; Reset=$reset.UtcDateTime.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")},
    [pscustomobject]@{G='CLAUDEANDGPTMODE'; Left=40; Reset=$reset.UtcDateTime.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")}
)}}
$script:IdleWhy = ''
$busy = Test-IdleBusy $beat
$why = Get-Variable IdleWhy -Scope Script -ErrorAction SilentlyContinue
"Test-IdleBusy: busy=$busy; why=$($why.Value)"
"runnable=$(-not $selected.Quota.Blocked); idle=$(-not $busy)"
if (-not $selected.Quota.Blocked -and -not $busy) {
    'ПОРУШЕННЯ: доступний каскад оголошено простоєм'
    exit 1
}
'ІНВАРІАНТ: доступний каскад лишається роботою'
exit 0
