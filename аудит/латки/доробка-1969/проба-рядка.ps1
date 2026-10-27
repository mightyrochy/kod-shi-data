param([string]$InputScript, [string]$ProbeOut)
. $InputScript -OutboxDir $ProbeOut -WorkDir $ProbeOut
[void][IO.Directory]::CreateDirectory($ProbeOut)
$script:HealthAlertDir = $ProbeOut
[void](Add-Line 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/проба-рушія-claude ENGINE_MISSING')
Add-HealthAlert 'ENGINE' 'CLAUDE'
