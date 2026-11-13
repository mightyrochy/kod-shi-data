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
    # Простір gemini (refs/remotes/origin): ключ той самий, що й раніше, перенесення — ні-що.
    Set-RemoteRoot 'refs/remotes/origin'
    Check 'gemini: ключ = "<Ref> <sha>", як до правки' ((Get-MarkerKey $og) -ceq "$($og.Ref) $($og.Sha)")
    Check 'gemini: перенесення нічого не робить' ((Move-LegacyMarkerState @($og)) -eq 0)
    Set-RemoteRoot 'refs/claude-run'
} catch { "✗ збій сценарію: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
"ПІДСУМОК: ✗ $bad"
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit ([int]($bad -gt 0))
