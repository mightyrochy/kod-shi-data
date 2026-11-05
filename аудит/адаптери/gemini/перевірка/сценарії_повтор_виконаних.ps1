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
    # Старий WAIT не заступає завершений результат; WAIT, записаний після результату (повтор), — заступає.
    $w1 = Mk 'wait-старий/gpt-6.1-sol-high/1/p0'; $w2 = Mk 'wait-новий/gpt-6.1-sol-high/1/p0'
    foreach ($w in @($w1, $w2)) { Write-FileAtomic (Get-StatePath (Get-MarkerKey $w) $old) 'WAIT {"until":9999999999,"group":"TEST"}' }
    (Get-Item -LiteralPath (Get-StatePath (Get-MarkerKey $w1) $old)).LastWriteTimeUtc = [datetime]::UtcNow.AddHours(-3)
    foreach ($w in @(@('wait-старий','20261105-120000-eeeeeeeeeeee'), @('wait-новий','20261105-120000-ffffffffffff'))) {
        $f = "$OutDir/$($w[1]).json"
        Write-FileAtomic $f (@{ v=1; id=$w[1]; slug=$w[0]; model='gpt-6.1-sol-high'; n=1; marker=$script:sha; cond='p0'; code='BLOCKED' } | ConvertTo-Json -Compress)
        (Get-Item -LiteralPath $f).LastWriteTimeUtc = [datetime]::UtcNow.AddHours(-1)
    }
    Remove-Item -LiteralPath "$target/restored"
    Restore-FinishedMarkerState $target
    Check 'старий WAIT не заступає пізніший завершений результат' ([IO.File]::ReadAllText((Get-StatePath (Get-MarkerKey $w1) $target)).StartsWith('DONE '))
    Check 'WAIT, записаний після результату, лишається WAIT' ([IO.File]::ReadAllText((Get-StatePath (Get-MarkerKey $w2) $target)).StartsWith('WAIT '))
    # Стан після перенесення в свіжій теці: Initialize + Restore разом.
    Remove-Item -LiteralPath $target -Recurse -Force
    $script:StateDir = $old
    $target = Initialize-SharedMarkerState
    $script:StateDir = $target
    Restore-FinishedMarkerState $target
    Check 'свіже перенесення: виконані не беруться, нова береться' ((-not (Takes $done)) -and (-not (Takes $res)) -and (Takes $fresh))
} catch { Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    if ((Split-Path -Parent $resolved) -ceq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $resolved) -cmatch '^shared-state-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
exit ([int]($bad -gt 0))
