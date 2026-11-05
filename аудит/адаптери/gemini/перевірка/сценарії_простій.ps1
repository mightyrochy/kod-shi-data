#Requires -Version 5.1
<# Стенд наряду «обгортка-простій» (31.10): увімкнений ноутбук без роботи будить диспетчера рядком ПРОСТІЙ.
Справжні функції обгортки; підмінено лише перелік позначок, зайнятість рушіїв і квоту Claude. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('prostii-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$utf = New-Object Text.UTF8Encoding($false)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}

Scenario 'а простій' {
    $work = Join-Path $tmp 'cr'; $box = Join-Path $tmp 'box'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir $box -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -GeminiStateDir "$tmp/gstate" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", $box, "$tmp/lanes", "$tmp/gstate")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"; $script:Limits = $null
    $send = { param($l) [bool](Add-Line $l) }
    $rows = { @(Get-ChildItem -LiteralPath $box -Filter '*.txt' -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() }) }
    $idle = "$work/state/idle.json"
    $back = { param([int]$Min)
        $o = [IO.File]::ReadAllText($idle, $utf) | ConvertFrom-Json
        $t = Get-UtcStamp ((Get-Date).AddMinutes(-$Min))
        if ($o.since) { $o.since = $t } else { $o.busy_utc = $t }
        [IO.File]::WriteAllText($idle, ($o | ConvertTo-Json -Compress), $utf) }

    # --- рядок: раз на простій -------------------------------------------------------------------------------------
    Update-Idle $true $send $false
    Check 'а є робота — рядка нема' (@(& $rows).Count -eq 0)
    & $back 7
    Update-Idle $false $send $false
    $r = @(& $rows)
    Check "а робота скінчилась — рівно один рядок ПРОСТІЙ від останньої роботи (~7 хв): $($r -join ' | ')" ($r.Count -eq 1 -and $r[0] -cmatch '^GEMINI ОБГОРТКА: ПРОСТІЙ 20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ [67]$')
    Update-Idle $false $send $false
    Update-Idle $false $send $false
    Check 'а повторне опитування без змін — нового рядка нема' (@(& $rows).Count -eq 1)
    Check 'а стан показує простій з якого часу' ((@(Get-IdleLines) -join "`n") -cmatch 'Простій: з 20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ · \d+ хв · рядок ПРОСТІЙ надіслано')
    Update-Idle $true $send $false
    Check 'а нова робота знімає простій у стані' ((@(Get-IdleLines) -join "`n") -cmatch 'Простій: нема')
    Update-Idle $false $send $false
    Check 'а нова робота й новий простій — другий рядок' (@(& $rows).Count -eq 2)
    & $back 90
    Update-Idle $false $send $true
    $r = @(& $rows)
    Check "а після ввімкнення (Reset) простій з першого проходу, не від давньої роботи: $($r -join ' | ')" ($r.Count -eq 3 -and @($r | Where-Object { $_ -cmatch ' 0$' }).Count -eq 2)
    Update-Idle $false $send $false
    Check 'а другий прохід після ввімкнення — без нового рядка' (@(& $rows).Count -eq 3)
    Remove-Item -LiteralPath $idle -Force
    Update-Idle $false $send $false
    Check 'а перший прохід без стану — рядок одразу з 0 хв' (@(& $rows).Count -eq 4)
    $failed = { param($l) $false }
    Remove-Item -LiteralPath $idle -Force
    Update-Idle $false $failed $false
    Update-Idle $false $send $false
    Check 'а недоставлений рядок повторюється наступного проходу, а не губиться' (@(& $rows).Count -eq 5)

    # --- що є роботою ----------------------------------------------------------------------------------------------
    $script:Busy = @{ Claude = $false; Gemini = $false }
    function Test-ClaudeBusy { $script:Busy.Claude }
    function Test-GeminiBusy { $script:Busy.Gemini }
    $script:Marks = @()
    function Get-Markers { $script:Marks }
    $script:Zero = $null
    function Read-ClaudeQuota { $script:Zero }
    $g = [pscustomobject]@{ Codex = $null }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $mk = { param($lane, $n) [pscustomobject]@{ Valid = $true; Lane = $lane; Ref = "gemini-queue/н$n/m/1"; Name = "gemini-queue/н$n/m/1"; Sha = ('{0:x}' -f $n).PadLeft(40, 'a'); Time = $now } }
    $put = { param($m, [string]$dir, [string]$text) Write-FileAtomic (Join-Path $dir ((Get-Sha256Hex (Get-MarkerKey $m)) + '.txt')) $text }
    Check 'а черга порожня, прогонів нема — простій' (-not (Test-IdleBusy $g))
    $script:Busy.Gemini = $true
    Check 'а прогін gemini-run — робота' (Test-IdleBusy $g)
    $script:Busy.Gemini = $false; $script:Busy.Claude = $true
    Check 'а свій наряд — робота' (Test-IdleBusy $g)
    $script:Busy.Claude = $false
    $m1 = & $mk 'claude' 1; $script:Marks = @($m1)
    Check 'а нова позначка Claude — робота' (Test-IdleBusy $g)
    & $put $m1 "$work/state" 'DONE NOT_ON_MAIN'
    Check 'а виконана позначка (стоїть, доки не зняли) — простій' (-not (Test-IdleBusy $g))
    Remove-Item "$work/state/*.txt" -Force
    $script:Zero = [pscustomobject]@{ windows = @([pscustomobject]@{ w = 'WEEK'; left = 0; reset = (Get-UtcStamp ((Get-Date).AddHours(5))) }) }
    Check 'а нова позначка Claude на нульовій квоті — не робота, простій' (-not (Test-IdleBusy $g))
    $script:Zero = [pscustomobject]@{ windows = @([pscustomobject]@{ w = 'WEEK'; left = 0; reset = (Get-UtcStamp ((Get-Date).AddHours(-1))) }) }
    Check 'а нуль зі скиданням у минулому — робота' (Test-IdleBusy $g)
    $script:Zero = $null
    $until = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + 3600
    & $put $m1 "$work/state" ('WAIT {"until":' + $until + ',"marker":"x"}')
    Check 'а позначка чекає скидання квоти — не робота' (-not (Test-IdleBusy $g))
    & $put $m1 "$work/state" ('WAIT {"until":' + ($until - 7200) + ',"marker":"x"}')
    Check 'а чекання минуло — робота' (Test-IdleBusy $g)
    Remove-Item "$work/state/*.txt" -Force
    $m2 = & $mk 'agy' 2; $script:Marks = @($m2)
    Check 'а нова позначка agy — робота' (Test-IdleBusy $g)
    & $put $m2 "$tmp/gstate" 'DONE'
    Check 'а виконана позначка agy (стан у теці gemini-run) — простій' (-not (Test-IdleBusy $g))
    $m3 = & $mk 'codex' 3; $script:Marks = @($m3)
    $gz = [pscustomobject]@{ Codex = [pscustomobject]@{ Refused = (Get-UtcStamp (Get-Date)); Reset = (Get-UtcStamp ((Get-Date).AddHours(2))) } }
    Check 'а нова позначка Codex на нульовій квоті — простій' (-not (Test-IdleBusy $gz))
    Check 'а та сама позначка Codex без відмови — робота' (Test-IdleBusy $g)
    $old = & $mk 'claude' 4; $old.Time = $now - 30 * 86400; $script:Marks = @($old)
    Check 'а позначка старша за MarkerMaxAgeDays — не робота' (-not (Test-IdleBusy $g))
    $bad1 = & $mk 'claude' 5; $bad1.Valid = $false; $script:Marks = @($bad1)
    Check 'а крива позначка — не робота' (-not (Test-IdleBusy $g))

    # --- рядок проходить шаблони обох скриптів і будить диспетчера -------------------------------------------------
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pubw" -OutDir "$tmp/pgo" -OutboxDir "$tmp/pubo" -UpdateRoot "$tmp/upd" -GeminiRunsDir "$tmp/gruns"
    $all = @(& $rows | Where-Object { $_ -match 'ПРОСТІЙ' })
    Check "а усі $($all.Count) рядки приймає публікатор" ($all.Count -ge 3 -and @($all | Where-Object { (Test-OutboxLine $_) -eq '' }).Count -eq $all.Count)
    Check 'а Test-DispatcherAction на ПРОСТІЙ — будить' ((Test-DispatcherAction 'GEMINI ОБГОРТКА: ПРОСТІЙ 2026-10-31T10:00:00Z 3') -eq $true)
    Check 'а чужий текст у рядку ПРОСТІЙ відкидає шаблон' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ПРОСТІЙ 2026-10-31T10:00:00Z 3; rm -rf') -ne '' -and (Test-OutboxLine 'GEMINI ОБГОРТКА: ПРОСТІЙ вчора 3') -ne '')
    Check 'а ГОТОВО виконавця, як і раніше, не будить' (-not (Test-DispatcherAction ('GEMINI ОБГОРТКА: ГОТОВО gemini/крок ' + ('a' * 40))))
}

"ПІДСУМОК: ✗ $bad"
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit ([int]($bad -gt 0))
