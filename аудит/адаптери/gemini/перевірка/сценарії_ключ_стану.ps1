#Requires -Version 5.1
<# Ключ стану позначки не залежить від простору посилань (13.11, #3527): claude-run (refs/claude-run) і gemini-run
(refs/remotes/origin) дають один ключ; стан під старим ключем claude-run після перенесення видно під канонічним. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('klyuch-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$utf = New-Object Text.UTF8Encoding($false)
$bad = 0
function Check([string]$Name, [bool]$Ok) { if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ } }
try {
    $work = Join-Path $tmp 'cr'
    . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $work -RepoDir $tmp -OutboxDir "$tmp/box" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -GeminiStateDir "$tmp/gstate" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
    foreach ($d in @($work, "$work/state", "$work/slots", "$tmp/lanes")) { [void][IO.Directory]::CreateDirectory($d) }
    $script:StateDir = "$work/state"; $script:SlotDir = "$work/slots"
    $sha = 'b' * 40; $name = 'gemini-queue/ВИМКНИ-НОУТБУК/cc-off/874'
    function Mk([string]$Root, [string]$Q = $name) { ConvertTo-Marker "$Root/$Q`t$sha`t1700000000" }
    $cr = Mk 'refs/claude-run'; $og = Mk 'refs/remotes/origin'
    Check 'ключ: Ref у refs/claude-run і в refs/remotes/origin дають однаковий ключ' ((Get-MarkerKey $cr) -ceq (Get-MarkerKey $og))
    Check 'ключ: канонічний вигляд — refs/remotes/origin/<назва> <sha>' ((Get-MarkerKey $cr) -ceq "refs/remotes/origin/$name $sha")
    Check 'claude-run справді в refs/claude-run' ($script:RemoteRoot -ceq 'refs/claude-run' -and $cr.Ref.StartsWith('refs/claude-run/'))
    # Стан, записаний claude-run під ключем refs/claude-run (#3527): виконана позначка, перша поява, рядок OWNER, живе узяття.
    $legacy = Get-StatePath "refs/claude-run/$name $sha"; $canon = Get-StatePath (Get-MarkerKey $cr)
    Write-FileAtomic $legacy 'DONE 20261110-100000-aaaaaaaaaaaa OFF'
    Write-FileAtomic ($legacy -replace '\.txt$', '.seen') '1700000123'
    Write-FileAtomic ($legacy -replace '\.txt$', '.owner') 'OWNER'
    Write-FileAtomic ($legacy -replace '\.txt$', '.claim') '20261110-100000-aaaaaaaaaaaa'
    Check 'ДО: виконана позначка під ключем refs/claude-run — для claude-run NEW, береться вдруге' (Test-MarkerReady (Get-MarkerState $cr))
    $cnt = Move-LegacyMarkerState @($cr)
    Check "ПІСЛЯ: перенесено три файли (.txt, .seen, .owner): $cnt" ($cnt -eq 3)
    Check 'ПІСЛЯ: стан видно під канонічним ключем' ([IO.File]::ReadAllText($canon, $utf) -ceq 'DONE 20261110-100000-aaaaaaaaaaaa OFF')
    Check 'ПІСЛЯ: виконана позначка вдруге не береться' (-not (Test-MarkerReady (Get-MarkerState $cr)) -and -not (Test-MarkerReady (Get-MarkerState $og)))
    [void](Get-OrderedMarkers @($cr))
    Check 'ПІСЛЯ: перша поява перенесена, а не перелічена заново' ($cr.Seen -eq 1700000123)
    Check 'ПІСЛЯ: .owner перенесено' ([IO.File]::Exists(($canon -replace '\.txt$', '.owner')))
    Check 'ПІСЛЯ: .claim не перенесено' (-not [IO.File]::Exists((Get-ClaimPath $canon)))
    Check 'ПІСЛЯ: старі файли не видалено' ([IO.File]::Exists($legacy) -and [IO.File]::Exists(($legacy -replace '\.txt$', '.claim')))
    # Ідемпотентність: другий прохід не міняє й не перезаписує.
    Write-FileAtomic $canon 'DONE 20261111-100000-cccccccccccc CRASH'
    Check 'повторно: нічого не перенесено' ((Move-LegacyMarkerState @($cr)) -eq 0)
    Check 'повторно: канонічний стан не перезаписано старим' ([IO.File]::ReadAllText($canon, $utf) -ceq 'DONE 20261111-100000-cccccccccccc CRASH')
    # STARTED не переноситься (його кінець запише старий ключ); після DONE — переноситься.
    $run = Mk 'refs/claude-run' 'gemini-queue/йде/cc-x/1'; $runLegacy = Get-StatePath "refs/claude-run/gemini-queue/йде/cc-x/1 $sha"
    Write-FileAtomic $runLegacy 'STARTED {"id":"x","slot":"claude-1"}'
    Check 'STARTED: не переноситься' ((Move-LegacyMarkerState @($run)) -eq 0 -and -not [IO.File]::Exists((Get-StatePath (Get-MarkerKey $run))))
    Write-FileAtomic $runLegacy 'DONE 20261112-100000-dddddddddddd OK'
    Check 'STARTED → DONE: наступний прохід переносить' ((Move-LegacyMarkerState @($run)) -eq 1 -and [IO.File]::Exists((Get-StatePath (Get-MarkerKey $run))))
    # Узяття під канонічним ключем: стан не чіпаємо.
    $taken = Mk 'refs/claude-run' 'gemini-queue/узята/cc-x/1'
    Write-FileAtomic (Get-StatePath "refs/claude-run/gemini-queue/узята/cc-x/1 $sha") 'DONE 20261112-100000-eeeeeeeeeeee OK'
    Write-FileAtomic ((Get-StatePath (Get-MarkerKey $taken)) -replace '\.txt$', '.claim') '20261112-100000-ffffffffffff'
    Check 'канонічне .claim є: стан не переноситься' ((Move-LegacyMarkerState @($taken)) -eq 0)
    # Процес наряду (Invoke-Worker): шлях стану з job (name, sha), а не з job.ref (refs/claude-run) — той самий, що в планувальника.
    foreach ($f in @('claude_run.ps1', 'gemini_run.ps1')) {
        $src = [IO.File]::ReadAllText((Join-Path $SourceDir $f), $utf)
        Check "$f : шлях стану не рахується від ref/sha напряму" ($src -cnotmatch 'Get-StatePath\s+"[^"]*\.ref\b')
    }
    $fw = Mk 'refs/claude-run' 'gemini-queue/воркер/cc-x/1'; $jb = @{ ref = $fw.Ref; name = $fw.Name; sha = $fw.Sha }
    $wp = Get-StatePath (Get-MarkerKey @{ Name = $jb.name; Sha = $jb.sha })
    Check 'воркер: шлях стану збігається з планувальниковим' ($wp -ceq (Get-StatePath (Get-MarkerKey $fw)))
    Check 'воркер: шлях не від refs/claude-run' ($wp -cne (Get-StatePath "$($jb.ref) $($jb.sha)"))
    Check 'узяття планувальником лишає .claim під шляхом воркера' ((New-Claim $fw '20261113-100000-aaaaaaaaaaaa') -and [IO.File]::Exists((Get-ClaimPath $wp)) -and (Get-MarkerState $fw).Kind -ceq 'TAKEN')
    Remove-Claim $wp
    Check 'Remove-Claim воркера звільняє узяття планувальника' (-not [IO.File]::Exists((Get-ClaimPath $wp)) -and (Get-MarkerState $fw).Kind -ceq 'NEW')
    [void](New-Claim $fw '20261113-100001-bbbbbbbbbbbb')
    Close-FailedStart ([pscustomobject]@{ Ref = $jb.ref; Name = $jb.name; Sha = $jb.sha; Slug = 'воркер'; Model = 'cc-x' }) '20261113-100001-bbbbbbbbbbbb' $wp
    Check 'Close-FailedStart воркера знімає .claim і повертає позначку в чергу (WAIT)' (-not [IO.File]::Exists((Get-ClaimPath $wp)) -and (Get-MarkerState $fw).Kind -ceq 'WAIT' -and (Get-Retakes $wp) -eq 1)
    # Відмова до старту × (MaxRetakes+1): кінцевий CRASH несе причину останньої відмови в blocked-reasons.json (#1856).
    foreach ($d in @("$tmp/box", "$tmp/gout")) { [void][IO.Directory]::CreateDirectory($d) }
    $wj = [IO.File]::ReadAllText($wp, $utf).Substring(5) | ConvertFrom-Json
    Check 'відмова до старту: причина між спробами — у стані чекання (група START)' ($wj.group -ceq 'START' -and $wj.PSObject.Properties['reason'])
    for ($i = 2; $i -le $script:MaxRetakes; $i++) {
        [void](New-Claim $fw '20261113-100002-cccccccccccc')
        Close-FailedStart ([pscustomobject]@{ Ref = $jb.ref; Name = $jb.name; Sha = $jb.sha; Slug = 'воркер'; Model = 'cc-x' }) '20261113-100002-cccccccccccc' $wp "відмова $i"
    }
    Check 'відмова до старту: до межі приміток CRASH нема' (-not [IO.File]::Exists("$tmp/gout/blocked-reasons.json") -and (Get-Retakes $wp) -eq $script:MaxRetakes)
    [void](New-Claim $fw '20261113-100003-dddddddddddd')
    Close-FailedStart ([pscustomobject]@{ Ref = $jb.ref; Name = $jb.name; Sha = $jb.sha; Slug = 'воркер'; Model = 'cc-x' }) '20261113-100003-dddddddddddd' $wp (Get-FailReason ([IO.IOException]::new('не відкрилось C:\Users\Тест\claude-run\w\x')))
    $crash = @(Read-NoteRows "$tmp/gout/blocked-reasons.json" @('utc', 'marker', 'text'))
    Check 'відмова до старту: кінцевий стан CRASH' ([IO.File]::ReadAllText($wp, $utf).StartsWith('DONE 20261113-100003-dddddddddddd CRASH'))
    Check 'відмова до старту: нотатка «CRASH до запуску (6 спроб): <причина>» без шляху профілю, в розділі #1856' ($crash.Count -eq 1 -and $crash[0][1] -ceq 'claude/воркер' -and $crash[0][2] -ceq 'CRASH до запуску (6 спроб): IOException: не відкрилось ~\claude-run\w\x')
    # Простір gemini (refs/remotes/origin): ключ той самий, що й раніше, перенесення — ні-що.
    Set-RemoteRoot 'refs/remotes/origin'
    Check 'gemini: ключ = "<Ref> <sha>", як до правки' ((Get-MarkerKey $og) -ceq "$($og.Ref) $($og.Sha)")
    Check 'gemini: перенесення нічого не робить' ((Move-LegacyMarkerState @($og)) -eq 0)
    Set-RemoteRoot 'refs/claude-run'
    # Чекання квоти без позначки на origin: показ і прибирання звіряються з отриманими посиланнями (ключ «посилання sha»).
    $keepDir = $script:StateDir; $script:StateDir = "$tmp/ws"; [void][IO.Directory]::CreateDirectory($script:StateDir)
    $future = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() + 3600; $past = 1700000000L
    $script:Refs = ''
    function Invoke-Git { if ($script:Refs -ceq 'FAIL') { throw 'git for-each-ref -> 128' }; [pscustomobject]@{ Code = 0; Out = $script:Refs; Err = '' } }
    function Put-Wait([string]$Q, [string]$Sha, [long]$Until) {
        $j = [ordered]@{ until = $Until; until_utc = '2026-11-15T20:00:00Z'; marker = $Q; retakes = 1; group = 'G1' }
        $p = Get-StatePath "refs/remotes/origin/$Q $Sha"; Write-FileAtomic $p ('WAIT ' + ($j | ConvertTo-Json -Compress)); $p
    }
    function Shown { @(Get-WaitingMarkers | ForEach-Object { $_.Marker }) | Sort-Object }
    $s1 = 'c' * 40; $s2 = 'd' * 40
    $qLive = 'gemini-queue/чекає-жива/cc-x/1'; $qLiveReady = 'gemini-queue/чекає-готова/cc-x/1'; $qGone = 'gemini-queue/знята-давно/cc-x/1'
    $qGoneSoon = 'gemini-queue/знята-чекає/cc-x/1'; $qGoneTaken = 'gemini-queue/знята-узята/cc-x/1'; $qMoved = 'gemini-queue/інша-голова/cc-x/1'; $qDone = 'gemini-queue/знята-кінець/cc-x/1'
    $script:Refs = (@($qLive, $qLiveReady, $qMoved) | ForEach-Object { "refs/claude-run/$_`t$s2`t1700000000`tтема" }) -join "`n"
    $pLive = Put-Wait $qLive $s2 $future; $pReady = Put-Wait $qLiveReady $s2 $past
    $pGone = Put-Wait $qGone $s1 $past; $pSoon = Put-Wait $qGoneSoon $s1 $future; $pTaken = Put-Wait $qGoneTaken $s1 $past
    $pMoved = Put-Wait $qMoved $s1 $past
    Write-FileAtomic (Get-ClaimPath $pTaken) '20261115-100000-aaaaaaaaaaaa'
    $pDone = Get-StatePath "refs/remotes/origin/$qDone $s1"; Write-FileAtomic $pDone 'DONE 20261115-100000-bbbbbbbbbbbb OK'
    $raw = @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.txt' -File | Where-Object { [IO.File]::ReadAllText($_.FullName, $utf).StartsWith('WAIT {') })
    Check "ДО: у теці стану $($raw.Count) файлів WAIT (їх усі й показував розділ «Чекають скидання квоти»)" ($raw.Count -eq 6)
    $shown = @(Shown)
    Check "ПІСЛЯ: показано лише позначки, що є на origin з тим самим sha ($($shown.Count) із 6): жива, готова; знята й стара голова — ні" (($shown -join '|') -ceq ((@($qLive, $qLiveReady) | Sort-Object) -join '|'))
    $removed = Remove-OrphanWaits
    Check "ПІСЛЯ: прибрано знятих із минулим чеканням: $removed (знята-давно, інша-голова)" ($removed -eq 2 -and -not [IO.File]::Exists($pGone) -and -not [IO.File]::Exists($pMoved))
    Check 'ПІСЛЯ: лишились живі, знята з чеканням, що триває, знята з узяттям, кінцевий DONE' ([IO.File]::Exists($pLive) -and [IO.File]::Exists($pReady) -and [IO.File]::Exists($pSoon) -and [IO.File]::Exists($pTaken) -and [IO.File]::Exists($pDone))
    Check 'ПІСЛЯ: стан живої позначки читає та сама смуга, що й раніше (WAIT, до часу — не готова)' ((Get-MarkerState (ConvertTo-Marker "refs/claude-run/$qLive`t$s2`t1700000000")).Kind -ceq 'WAIT' -and -not (Test-MarkerReady (Get-MarkerState (ConvertTo-Marker "refs/claude-run/$qLive`t$s2`t1700000000"))))
    Check 'ПІСЛЯ: повторне прибирання — нічого' ((Remove-OrphanWaits) -eq 0)
    $back = ConvertTo-Marker "refs/claude-run/$qGone`t$s1`t1700000000"
    Check 'перепушена позначка з тим самим комітом після прибирання — NEW, береться відразу' ((Get-MarkerState $back).Kind -ceq 'NEW' -and (Test-MarkerReady (Get-MarkerState $back)))
    Check 'знята з чеканням, що триває, не показується, але стан не зник — після `until` станеться прибирання' ((Shown) -cnotcontains $qGoneSoon -and [IO.File]::Exists($pSoon))
    $script:Refs = ''
    Check 'порожній набір посилань: нічого не видалено (fetch нічого не дав)' ((Remove-OrphanWaits) -eq 0 -and [IO.File]::Exists($pReady))
    $script:Refs = 'FAIL'
    Check 'посилання не прочитано: прибирання нічого не видаляє, показ порожній без винятку' ((Remove-OrphanWaits) -eq 0 -and [IO.File]::Exists($pReady) -and @(Get-WaitingMarkers).Count -eq 0)
    $script:StateDir = $keepDir
} catch { "✗ збій сценарію: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
"ПІДСУМОК: ✗ $bad"
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit ([int]($bad -gt 0))
