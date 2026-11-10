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
    $g = [pscustomobject]@{ Codex = $null; Quota = $null }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $mk = { param($lane, $n) [pscustomobject]@{ Valid = $true; Lane = $lane; Slug = "н$n"; Ref = "gemini-queue/н$n/m/1"; Name = "gemini-queue/н$n/m/1"; Sha = ('{0:x}' -f $n).PadLeft(40, 'a'); Time = $now } }
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
    $gz = [pscustomobject]@{ Codex = [pscustomobject]@{ Refused = (Get-UtcStamp (Get-Date)); Reset = (Get-UtcStamp ((Get-Date).AddHours(2))) }; Quota = $null }
    Check 'а нова позначка Codex на нульовій квоті — простій' (-not (Test-IdleBusy $gz))
    Check 'а та сама позначка Codex без відмови — робота' (Test-IdleBusy $g)
    $old = & $mk 'claude' 4; $old.Time = $now - 30 * 86400; $script:Marks = @($old)
    Check 'а позначка старша за MarkerMaxAgeDays — не робота' (-not (Test-IdleBusy $g))
    $bad1 = & $mk 'claude' 5; $bad1.Valid = $false; $script:Marks = @($bad1)
    Check 'а крива позначка — не робота' (-not (Test-IdleBusy $g))

    # --- позначки, яких смуга не візьме, і причина простою (ніч 09→10.11: 14 год без рядка) ------------------------------
    $script:Marks = @(); Remove-Item "$tmp/gstate/*.txt" -Force -ErrorAction SilentlyContinue
    $day = { param([int]$Ago) [datetime]::UtcNow.AddDays(-$Ago).ToString('yyyyMMdd') }
    $putG = { param($m, [string]$grp, [long]$until) & $put $m "$tmp/gstate" ('WAIT {"until":' + $until + ',"marker":"x","retakes":1,"group":"' + $grp + '"}') }
    $past = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - 7200; $futS = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + 7200
    $n1 = & $mk 'codex' 11; $n1.Slug = 'Е1-нічний-живий-' + (& $day 1); $n1.Name = "gemini-queue/$($n1.Slug)/gpt/1"; $n1.Ref = $n1.Name
    $script:Marks = @($n1); & $putG $n1 'CODEX' $past
    Check 'а нічний прохід учорашнього дня зі скінченим чеканням (смуга його не бере) — простій' (-not (Test-IdleBusy $g))
    $n2 = & $mk 'codex' 12; $n2.Slug = 'Е1-нічний-живий-' + (& $day 0); $n2.Name = "gemini-queue/$($n2.Slug)/gpt/1"; $n2.Ref = $n2.Name
    $script:Marks = @($n2); & $putG $n2 'CODEX' $past
    Check 'а нічний прохід сьогодні зі скінченим чеканням (смуга його візьме) — робота' (Test-IdleBusy $g)
    $nc = & $mk 'claude' 13; $nc.Slug = 'Е1-нічний-живий-' + (& $day 1); $nc.Name = "gemini-queue/$($nc.Slug)/cc-x/1"; $nc.Ref = $nc.Name
    $script:Marks = @($nc)
    Check 'а нічний прохід учорашнього дня на смузі Claude (її правило дати інше) — робота' (Test-IdleBusy $g)

    $a1 = & $mk 'agy' 14; $a2 = & $mk 'agy' 15; $a3 = & $mk 'codex' 16
    $gq = { param([string]$grp, [int]$left, [int]$h) [pscustomobject]@{ Codex = $null; Quota = [pscustomobject]@{ Read = ''; Windows = @([pscustomobject]@{ G = $grp; W = 'WEEK'; Left = $left; Reset = (Get-UtcStamp ((Get-Date).AddHours($h))) }) } } }
    $script:Marks = @($a1, $a2); & $putG $a1 'GEMINIMODELS' $past; & $putG $a2 'GEMINIMODELS' $past
    Check 'а скінчене чекання, а група agy досі на нулі за heartbeat — не робота' (-not (Test-IdleBusy (& $gq 'GEMINIMODELS' 0 5)))
    Check 'а причина простою: усі позначки на нульовій квоті' ($script:IdleWhy -cmatch '^ QUOTA0 2 GEMINIMODELS 20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ$')
    Check 'а скінчене чекання, а скидання групи вже минуло — робота' (Test-IdleBusy (& $gq 'GEMINIMODELS' 0 -1))
    Check 'а скінчене чекання, а група має квоту — робота' (Test-IdleBusy (& $gq 'GEMINIMODELS' 40 5))
    Check 'а скінчене чекання іншої групи, нуль у GEMINIMODELS — робота' (Test-IdleBusy (& $gq 'GEMINI4ARGON' 0 5))
    $script:Marks = @($a1, $a3); & $putG $a1 'GEMINIMODELS' $futS
    & $putG $a3 'CODEX' $past
    Check 'а чекання квоти agy й Codex на нулі — не робота, причина з обох груп' (-not (Test-IdleBusy $gz) -and $script:IdleWhy -cmatch '^ QUOTA0 2 CODEX,GEMINIMODELS 20\d\d-')
    $a4 = & $mk 'agy' 17; $script:Marks = @($a1, $a3, $a4)
    Check 'а одна нова позначка (черга не вся на нулі, хай чекає GPU) — робота, рядка простою нема' (Test-IdleBusy $gz)
    $script:Marks = @($a1); & $putG $a1 'NETWORK' $futS
    Check 'а чекання мережі — не робота, але й не квота: причини нема' (-not (Test-IdleBusy $g) -and $script:IdleWhy -ceq '')
    $script:Marks = @(); Check 'а порожня черга — простій без причини' (-not (Test-IdleBusy $g) -and $script:IdleWhy -ceq '')
    Remove-Item "$tmp/gstate/*.txt" -Force -ErrorAction SilentlyContinue
    Update-Idle $true $send $false
    Update-Idle $false $send $false ' QUOTA0 3 CODEX,GEMINIMODELS 2026-11-14T09:48:19Z'
    $r = @(& $rows | Where-Object { $_ -cmatch 'QUOTA0 3 CODEX,GEMINIMODELS' })
    Check "а рядок ПРОСТІЙ несе причину: $($r -join ' | ')" ($r.Count -eq 1 -and $r[0] -cmatch '^GEMINI ОБГОРТКА: ПРОСТІЙ 20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ \d+ QUOTA0 3 CODEX,GEMINIMODELS 2026-11-14T09:48:19Z$')
    Update-Idle $true $send $false
    Update-Idle $false $send $false ' QUOTA0 1 CLAUDE -'
    Check 'а скидання невідоме — тире, рядок проходить шаблон' (@(& $rows | Where-Object { $_ -cmatch 'QUOTA0 1 CLAUDE -$' }).Count -eq 1)

    # --- рядок проходить шаблони обох скриптів і будить диспетчера -------------------------------------------------
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pubw" -OutDir "$tmp/pgo" -OutboxDir "$tmp/pubo" -UpdateRoot "$tmp/upd" -GeminiRunsDir "$tmp/gruns"
    $all = @(& $rows | Where-Object { $_ -match 'ПРОСТІЙ' })
    Check "а усі $($all.Count) рядки приймає публікатор" ($all.Count -ge 5 -and @($all | Where-Object { (Test-OutboxLine $_) -eq '' }).Count -eq $all.Count)
    Check 'а Test-DispatcherAction на ПРОСТІЙ — будить' ((Test-DispatcherAction 'GEMINI ОБГОРТКА: ПРОСТІЙ 2026-10-31T10:00:00Z 3') -eq $true)
    Check 'а Test-DispatcherAction на ПРОСТІЙ з причиною — будить' ((Test-DispatcherAction 'GEMINI ОБГОРТКА: ПРОСТІЙ 2026-10-31T10:00:00Z 3 QUOTA0 4 CODEX,GEMINIMODELS 2026-11-14T09:48:19Z') -eq $true)
    Check 'а чужий текст після причини ПРОСТІЙ відкидає шаблон' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ПРОСТІЙ 2026-10-31T10:00:00Z 3 QUOTA0 4 CODEX; rm -rf 2026-11-14T09:48:19Z') -ne '')
    Check 'а чужий текст у рядку ПРОСТІЙ відкидає шаблон' ((Test-OutboxLine 'GEMINI ОБГОРТКА: ПРОСТІЙ 2026-10-31T10:00:00Z 3; rm -rf') -ne '' -and (Test-OutboxLine 'GEMINI ОБГОРТКА: ПРОСТІЙ вчора 3') -ne '')
    Check 'а ГОТОВО виконавця, як і раніше, не будить' (-not (Test-DispatcherAction ('GEMINI ОБГОРТКА: ГОТОВО gemini/крок ' + ('a' * 40))))
}

"ПІДСУМОК: ✗ $bad"
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit ([int]($bad -gt 0))
