#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('shared-state-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Повертає окремий факт і ненульовий код при кожному провалі. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/update"
    $script:StateDir = "$RunsDir/state"; $script:SlotDir = "$RunsDir/slots"
    foreach ($dir in @($script:StateDir,$script:SlotDir,$OutDir,$LaneDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $script:sha = 'a' * 40; $old = $script:StateDir
    function Mk([string]$Name) { [pscustomobject]@{ Ref = "refs/remotes/origin/gemini-queue/$Name"; Sha = $script:sha } }
    # Смуга бере позначку, коли Get-MarkerState/Test-MarkerReady (Start-Markers) бачать її готовою: NEW — береться.
    function Takes($M) { Test-MarkerReady (Get-MarkerState $M) }
    $done = Mk 'хук-збій/gpt-6.1-sol-high/2/p0'; $res = Mk 'живий/gpt-6.1-sol-high/3/gpu-p0'
    $quota = Mk 'квота/gpt-6.1-sol-high/1/p0'; $fresh = Mk 'нова/gpt-6.1-sol-high/1/p0'
    $started = Mk 'перервана/gpt-6.1-sol-high/1/p0'
    # Стан до переходу: завершене у старій теці; ще одне відоме лише з результату прогону <OutDir>\<id>.json.
    Write-FileAtomic (Get-StatePath (Get-MarkerKey $done) $old) 'DONE 20261103-100000-aaaaaaaaaaaa BLOCKED'
    Write-FileAtomic (Get-StatePath (Get-MarkerKey $started) $old) 'STARTED {"id":"x","slot":"codex-1"}'
    Write-FileAtomic "$OutDir/20261103-110000-bbbbbbbbbbbb.json" (@{ v=1; id='20261103-110000-bbbbbbbbbbbb'; slug='живий'; model='gpt-6.1-sol-high'; n=3; marker=$sha; cond='gpu-p0'; code='STALL' } | ConvertTo-Json -Compress)
    Write-FileAtomic "$OutDir/20261104-110000-cccccccccccc.json" (@{ v=1; id='20261104-110000-cccccccccccc'; slug='квота'; model='gpt-6.1-sol-high'; n=1; marker=$sha; cond='p0'; code='QUOTA_ZERO' } | ConvertTo-Json -Compress)
    # ДО (8683de77): «ready» уже є, а перенесення не відбулося (порожнє чи інше джерело) — Main далі лише читає спільну теку.
    $target = Join-Path $OutDir 'marker-state'
    [void][IO.Directory]::CreateDirectory($target)
    Write-FileAtomic "$target/ready" '1'
    Check 'ДО: Initialize лише повертає теку' ((Initialize-SharedMarkerState) -ceq $target)
    $script:StateDir = $target
    Check 'ДО: виконана позначка зі старого стану — NEW, береться вдруге' (Takes $done)
    Check 'ДО: виконана за результатом — NEW, береться вдруге' (Takes $res)
    # ПІСЛЯ: Main після Initialize відновлює завершене.
    Restore-FinishedMarkerState $target
    Check 'ПІСЛЯ: виконана зі старого стану не береться' (-not (Takes $done))
    Check 'ПІСЛЯ: виконана за результатом прогону не береться' (-not (Takes $res))
    Check 'ПІСЛЯ: квота без кінця лишається NEW' (Takes $quota)
    Check 'ПІСЛЯ: нова позначка береться' (Takes $fresh)
    Check 'ПІСЛЯ: перервана STARTED зі старої теки не переноситься' (-not (Test-Path -LiteralPath (Get-StatePath (Get-MarkerKey $started) $target)))
    Check 'ПІСЛЯ: стан відновлено рівно з двох джерел' ([IO.File]::ReadAllText("$target/restored") -ceq '2')
    # Виконане вже після переходу — лише в marker-state — не повторюється й не перезаписується.
    $later = Mk 'пізня/gpt-6.1-sol-high/1/p0'
    Write-FileAtomic (Get-StatePath (Get-MarkerKey $later) $target) 'DONE 20261105-140000-dddddddddddd OK'
    Write-FileAtomic "$OutDir/20261105-140000-dddddddddddd.json" (@{ v=1; id='20261105-140000-dddddddddddd'; slug='пізня'; model='gpt-6.1-sol-high'; n=1; marker=$sha; cond='p0'; code='BLOCKED' } | ConvertTo-Json -Compress)
    Check 'після переходу: виконана в marker-state не береться' (-not (Takes $later))
    Remove-Item -LiteralPath "$target/restored"
    Restore-FinishedMarkerState $target
    Check 'відновлення не перезаписує наявний стан' ([IO.File]::ReadAllText((Get-StatePath (Get-MarkerKey $later) $target)) -ceq 'DONE 20261105-140000-dddddddddddd OK')
    # Разовість: прапор не дає воскресити свідомо знятий стан.
    Remove-Item -LiteralPath (Get-StatePath (Get-MarkerKey $done) $target) -Force
    Restore-FinishedMarkerState $target
    Check 'прапор restored: знятий стан не воскресає' (Takes $done)
    # Стан після перенесення в свіжій теці: Initialize + Restore разом.
    Remove-Item -LiteralPath $target -Recurse -Force
    $script:StateDir = $old
    $target = Initialize-SharedMarkerState
    $script:StateDir = $target
    Restore-FinishedMarkerState $target
    Check 'свіже перенесення: виконані не беруться, нова береться' ((-not (Takes $done)) -and (-not (Takes $res)) -and (Takes $fresh))
} catch { Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally { if(token!=IntPtr.Zero) CloseHandle(token); if(restricted!=IntPtr.Zero) CloseHandle(restricted); Marshal.FreeHGlobal(ptr); }
    }
}
'@
    $ref = 'gemini-queue/стан/gpt-6.1-sol-high/1'; $sha = 'a' * 40
    $marker = [pscustomobject]@{Ref="refs/remotes/origin/$ref";Sha=$sha}
    $sp = Get-StatePath (Get-MarkerKey $marker)
    Write-FileAtomic $sp 'WAIT {"until":9999999999,"group":"TEST"}'
    Write-FileAtomic ($sp + '.sleep.json') '{"id":"попередній"}'
    Write-FileAtomic ($sp + '.stale.part') 'незавершено'
    Check 'ДО: читач INTERACTIVE не читає приватний файл з ACL записувача' (-not [StateReader]::CanRead($sp))
    # Функція з виробничого коду: жодної підміни переходу, читання чи запису.
    if (-not (Get-Command Initialize-SharedMarkerState -ErrorAction SilentlyContinue)) {
        Check 'ПІСЛЯ: спільний стан доступний без дозволу адміністратора' $false
    } else {
        $held = Open-Lock "$script:SlotDir/codex-1.lock"
        try { Check 'старий зайнятий слот відкладає перехід' (-not (Initialize-SharedMarkerState)) }
        finally { $held.Dispose() }
        Check 'частковий перехід не публікує ready' (-not (Test-Path "$OutDir/marker-state/ready"))
        [void](New-Claim $marker '20261105-000000-123456789abc')
        Check 'свіжий claim до запуску процесу відкладає перехід' (-not (Initialize-SharedMarkerState))
        Remove-Claim $sp
        $staleId = '20261105-000000-123456789abc'
        [void][IO.Directory]::CreateDirectory("$RunsDir/$staleId")
        Write-FileAtomic "$RunsDir/$staleId/worker.json" '{"slot":"codex-1"}'
        [void](New-Claim $marker $staleId)
        (Get-Item -LiteralPath (Get-ClaimPath $sp)).LastWriteTime = (Get-Date).AddMinutes(-11)
        $interrupted = Join-Path $script:StateDir (('b' * 64) + '.txt')
        Write-FileAtomic $interrupted 'STARTED {"id":"перерваний","slot":"codex-2"}'
        Write-FileAtomic (Get-ClaimPath $interrupted) '20261105-000000-123456789abc'
        $target = Initialize-SharedMarkerState
        Check 'застарілий claim до STARTED очищено до захоплення власних замків' (-not (Test-Path -LiteralPath (Get-ClaimPath $sp)) -and [bool]$target)
        $dest = Join-Path $target (Split-Path -Leaf $sp)
        Check 'ПІСЛЯ: INTERACTIVE справді читає файл зі спільної теки' ([StateReader]::CanRead($dest))
        Check 'приватна ACL і старий файл не змінені' (-not [StateReader]::CanRead($sp) -and (Test-Path $sp))
        Check 'історія WAIT і бічний файл збережені, part не перенесено' ([IO.File]::ReadAllText($dest) -ceq [IO.File]::ReadAllText($sp) -and (Test-Path ($dest + '.sleep.json')) -and -not (Test-Path ($dest + '.stale.part')))
        Check 'ready теж доступний читачеві' ([StateReader]::CanRead("$target/ready"))
        Check 'перерваний STARTED без живого слота переноситься разом із claim для штатного відновлення' ((Test-Path (Join-Path $target (Split-Path -Leaf $interrupted))) -and (Test-Path (Join-Path $target (Split-Path -Leaf (Get-ClaimPath $interrupted)))))
        $script:StateDir = $target
        Write-FileAtomic $dest 'DONE новий OK'
        Check 'повторний запуск не відновлює застарілу історію' ((Initialize-SharedMarkerState) -ceq $target -and [IO.File]::ReadAllText($dest) -ceq 'DONE новий OK')
        . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/update"
        foreach ($dir in @($WorkDir,"$WorkDir/seen",$OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
        $state = Get-ChainMarkerState $ref $sha 'gpt-6.1-sol-high'
        Check 'ланцюг читає чинний DONE зі спільної теки' ($state.Kind -ceq 'DONE')
        Remove-Item -LiteralPath "$target/ready"
        Check 'до готовності відсутній файл не стає NEW' ((Get-ChainMarkerState 'gemini-queue/відсутній/gpt-6.1-sol-high/1' $sha 'gpt-6.1-sol-high').Kind -ceq 'UNKNOWN')
        Write-FileAtomic "$target/ready" '1'
        Check 'після готовності відсутня позначка має NEW' ((Get-ChainMarkerState 'gemini-queue/відсутній/gpt-6.1-sol-high/1' $sha 'gpt-6.1-sol-high').Kind -ceq 'NEW')
        $script:MarkerLines = @(); $handles = @()
        try {
            foreach ($n in 1..4) {
                $r = "gemini-queue/стан/gpt-6.1-sol-high/$n"
                $script:MarkerLines += "$sha`trefs/heads/$r"
                $p = Join-Path $target ((Get-Sha256Hex "refs/remotes/origin/$r $sha") + '.txt')
                Write-FileAtomic $p 'DONE'
                $handles += [IO.File]::Open($p, 'Open', 'ReadWrite', 'None')
            }
            function Invoke-Git { [pscustomobject]@{Code=0;Out=($script:MarkerLines -join "`n")} }
            $states = @(Get-ChainMarkers 'стан')
            Check 'N зайнятих файлів: прохід завершено, усі UNKNOWN' ($states.Count -eq 4 -and @($states | Where-Object Kind -cne 'UNKNOWN').Count -eq 0)
            Check 'N зайнятих файлів: один рядок на код і місце за годину' (@(Get-ChildItem -LiteralPath $OutboxDir -File).Count -eq 1)
            $records = @([IO.File]::ReadAllLines("$OutDir/state-failures.jsonl") | ForEach-Object { $_ | ConvertFrom-Json })
            Check 'N зайнятих файлів: усі шляхи й стеки збережені' ($records.Count -eq 4 -and @($records.path | Sort-Object -Unique).Count -eq 4 -and @($records | Where-Object { -not $_.script_stack }).Count -eq 0)
        } finally { foreach ($h in $handles) { $h.Dispose() } }
        function First-FailureSite { throw 'CHAIN_REMOTE' }
        function Second-FailureSite { throw 'CHAIN_REMOTE' }
        foreach ($site in @('First-FailureSite','Second-FailureSite')) {
            try { & $site } catch { Write-ChainFailure $_ }
        }
        Check 'однаковий код у двох місцях має два різні вихідні файли' (@(Get-ChildItem -LiteralPath $OutboxDir -File).Count -eq 3)
        foreach ($site in @('First-FailureSite','Second-FailureSite')) {
            try { & $site } catch { Write-ChainFailure $_ }
        }
        Check 'повтор із кожного місця приглушено в межах години' (@(Get-ChildItem -LiteralPath $OutboxDir -File).Count -eq 3)
    }
} catch { Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    if ((Split-Path -Parent $resolved) -ceq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $resolved) -cmatch '^shared-state-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
exit ([int]($bad -gt 0))
