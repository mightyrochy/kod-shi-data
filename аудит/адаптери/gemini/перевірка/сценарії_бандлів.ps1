#Requires -Version 5.1
<# Перевіряє справжні Complete-Status і Publish-Bundle на локальних репозиторіях без мережі й рушіїв, а також повтор
   публікації позначкою, яку диспетчер повернув після відмови (Reset-ReturnedRefusals). #>
param([string]$Root, [switch]$Before)
$ErrorActionPreference = 'Stop'
$src = Split-Path $PSScriptRoot
$utf8 = New-Object Text.UTF8Encoding($false)

function Fixture-Git([string]$At, [string[]]$Items) {
    <# Виконує команду стенда й зупиняється при помилці Git. #>
    $out = & git -C $At -c user.name=stand -c user.email=stand@example.invalid -c core.autocrlf=false @Items 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($out -join "`n") }
    ($out -join "`n").Trim()
}

$cases = @('private-start', 'new-main', 'published-start', 'BUNDLE_INVALID', 'REF_MISMATCH', 'SECRET', 'GITHUB_DIR', 'WRAPPER_FILES', 'SECRET-JWT', 'BASE64-NOT-SECRET')
if ($Before) { $cases = $cases[0..1] }
$bad = 0
foreach ($case in $cases) {
    $w = Join-Path $Root $case
    [void](New-Item -ItemType Directory -Path $w)
    foreach ($dir in @('seed', 'out', 'runs', 'pub', 'pub/inbox')) { [void](New-Item -ItemType Directory -Path (Join-Path $w $dir) -Force) }
    $origin = Join-Path $w 'origin.git'; $seed = Join-Path $w 'seed'; $repo = Join-Path $w 'clone'; $pub = Join-Path $w 'pub'
    [void](Fixture-Git $w @('init', '-q', '--bare', $origin))
    [void](Fixture-Git $origin @('symbolic-ref', 'HEAD', 'refs/heads/main'))
    [void](Fixture-Git $seed @('init', '-q', '-b', 'main'))
    [IO.File]::WriteAllText((Join-Path $seed 'base.txt'), "base`n", $utf8)
    [void](Fixture-Git $seed @('add', '.')); [void](Fixture-Git $seed @('commit', '-q', '-m', 'База позначки'))
    $marker = Fixture-Git $seed @('rev-parse', 'HEAD')
    [void](Fixture-Git $seed @('remote', 'add', 'origin', $origin)); [void](Fixture-Git $seed @('push', '-q', 'origin', 'main'))
    [void](Fixture-Git $w @('clone', '-q', $origin, $repo))
    [void](Fixture-Git $pub @('init', '-q', '--bare', 'repo.git'))
    [void](Fixture-Git (Join-Path $pub 'repo.git') @('remote', 'add', 'origin', $origin))
    [void](Fixture-Git (Join-Path $pub 'repo.git') @('fetch', '-q', 'origin', 'main:refs/remotes/origin/main'))
    # Публікатор має тільки базу позначки; main відтоді просунувся, агент його віллє.
    [IO.File]::WriteAllText((Join-Path $seed 'main.txt'), "new main`n", $utf8)
    [void](Fixture-Git $seed @('add', '.')); [void](Fixture-Git $seed @('commit', '-q', '-m', 'Свіжіший main'))
    $newMain = Fixture-Git $seed @('rev-parse', 'HEAD')
    [void](Fixture-Git $seed @('push', '-q', 'origin', 'main'))
    [void](Fixture-Git $repo @('checkout', '-q', '-b', 'gemini/probe'))
    [IO.File]::WriteAllText((Join-Path $repo 'review.txt'), "review`n", $utf8)
    [void](Fixture-Git $repo @('add', '.')); [void](Fixture-Git $repo @('commit', '-q', '-m', 'Гілка перевірки'))
    $start = Fixture-Git $repo @('rev-parse', 'HEAD')
    if ($case -ne 'private-start') {
        [void](Fixture-Git $repo @('push', '-q', 'origin', 'gemini/probe'))
        [void](Fixture-Git (Join-Path $pub 'repo.git') @('fetch', '-q', 'origin', 'gemini/probe:refs/remotes/origin/gemini/probe'))
    }
    [void](Fixture-Git $repo @('fetch', '-q', 'origin', 'main:refs/remotes/origin/main'))
    [void](Fixture-Git $repo @('merge', '-q', '--no-edit', 'origin/main'))
    if ($case -eq 'private-start') { $start = Fixture-Git $repo @('rev-parse', 'HEAD') }
    if ($case -eq 'published-start') {
        # Доробка опублікованої гілки: обидві передумови вже є у публікатора.
        [void](Fixture-Git (Join-Path $pub 'repo.git') @('fetch', '-q', 'origin', 'main:refs/remotes/origin/main'))
    }
    $path = switch ($case) {
        'SECRET' { '.codex/auth.json' }
        'GITHUB_DIR' { '.github/workflows/probe.yml' }
        'WRAPPER_FILES' { 'аудит/адаптери/gemini/probe.txt' }
        'BASE64-NOT-SECRET' { 'VIDPOVIDI/00003.json' }
        default { 'work.txt' }
    }
    # Вміст: JWT (заголовок.навантаження.підпис) — відмова; `eyJ` + 12 знаків посеред base64 без крапки (як у JPEG запису обміну) — ні.
    $body = switch ($case) {
        'SECRET-JWT' { "token eyJFAKE_HEADER_NOT_A_TOKEN.eyJFAKE_PAYLOAD_NOT_A_TOKEN.FAKE_SIGNATURE_NOT_A_TOKEN`n" }
        'BASE64-NOT-SECRET' { '{"data": "/9j/4AAQ' + ('QUJD' * 40) + 'eyJA1b2C3d4E5f6+/' + ('REVG' * 40) + '9k="}' + "`n" }
        default { "work`n" }
    }
    $file = Join-Path $repo $path
    [void](New-Item -ItemType Directory -Force -Path (Split-Path $file))
    [IO.File]::WriteAllText($file, $body, $utf8)
    [void](Fixture-Git $repo @('add', '.')); [void](Fixture-Git $repo @('commit', '-q', '-m', 'Робота агента'))
    $s = [ordered]@{ id = '20261028-000000-aaaaaaaaaaaa'; slug = 'probe'; marker = $marker; start = $start
        head = ''; ahead = 0; bundle = ''; code = 'DONE'; turns = 1; minutes = 0 }
    & {
        . (Join-Path $src 'gemini_run.ps1') -RepoDir $repo -RunsDir (Join-Path $w 'runs') -OutDir (Join-Path $w 'out')
        $script:NoHooks = Join-Path $w 'no-hooks'
        Complete-Status $s (Join-Path $w 'state.txt') '' ([datetime]::MinValue)
    }
    if (-not $s.bundle) { throw 'Complete-Status не створив бандла' }
    if ($case -eq 'BUNDLE_INVALID') {
        # Старий виробник виключив main, якого публікатор ще не отримав.
        [void](Fixture-Git $repo @('bundle', 'create', '-q', (Join-Path $w "out/$($s.bundle)"),
                'refs/heads/gemini/probe', '^refs/remotes/origin/main', "^$start"))
    }
    $head = $s.head
    if ($case -eq 'REF_MISMATCH') { $s.head = $marker }
    $result = & {
        . (Join-Path $src 'gemini_publish.ps1') -WorkDir $pub -OutDir (Join-Path $w 'out') -RepoUrl $origin
        $script:Repo = Join-Path $pub 'repo.git'; $script:NoHooks = Join-Path $w 'no-hooks'
        $verify = Invoke-Git @('bundle', 'verify', (Join-Path $OutDir $s.bundle)) -AllowFail
        Write-Host "$case verify: код $($verify.Code) $($verify.Err.Trim())"
        Publish-Bundle ([pscustomobject]$s) $s.id
    }
    $want = if ($Before) { 'BUNDLE_INVALID' } elseif ($case -eq 'SECRET-JWT') { 'SECRET' } elseif ($case -cmatch '^[A-Z_]+$') { $case } else { 'OK' }
    $published = Fixture-Git $origin @('for-each-ref', '--format=%(objectname)', 'refs/heads/gemini/probe')
    $ok = $result[0] -eq $want
    if ($want -eq 'OK') { $ok = $ok -and $published -eq $head }
    # Відмова не повинна пересунути раніше опубліковану гілку.
    elseif ($case -ne 'private-start') { $ok = $ok -and $published -eq $start }
    else { $ok = $ok -and -not $published }
    if ($case -eq 'BUNDLE_INVALID') {
        $diagnostic = [IO.File]::ReadAllText((Join-Path $pub 'publish.log'))
        $ok = $ok -and $diagnostic.Contains($newMain) -and $diagnostic.Contains('git bundle verify -> 1')
    }
    if ($ok) { Write-Host "  ✓ $case -> $want" }
    else { Write-Host "  ✗ $case -> $($result[0]), очікування $want"; $bad++ }
}

# Повтор публікації позначкою: відмова SECRET знімає позначку, диспетчер повертає її тим самим SHA. Версії обгортки —
# підміною $script:WrapperVersion, хибний збіг — давня перша альтернатива SECRET (`eyJ` і ≥10 знаків) на base64 запису обміну.
$oldSecret = 'eyJ[A-Za-z0-9_-]{10,}|sk-[A-Za-z0-9_-]{16,}'
$v1 = '1' * 40; $v2 = '2' * 40
$queue = 'gemini-queue/probe/gpt-test/1'; $id = '20261114-003351-e70acf423fa9'
$repubCases = @('оновлення', 'без-оновлення', 'друга-відмова', 'без-версії', 'не-знімали')
if ($Before) { $repubCases = @() }
foreach ($case in $repubCases) {
    $w = Join-Path $Root "повтор-$case"
    foreach ($dir in @('seed', 'out/marker-state', 'pub/inbox', 'pub/state', 'pub/seen', 'outbox')) { [void](New-Item -ItemType Directory -Path (Join-Path $w $dir) -Force) }
    $origin = Join-Path $w 'origin.git'; $seed = Join-Path $w 'seed'; $agent = Join-Path $w 'agent'; $pub = Join-Path $w 'pub'; $out = Join-Path $w 'out'
    [void](Fixture-Git $w @('init', '-q', '--bare', $origin))
    [void](Fixture-Git $origin @('symbolic-ref', 'HEAD', 'refs/heads/main'))
    [void](Fixture-Git $seed @('init', '-q', '-b', 'main'))
    [IO.File]::WriteAllText((Join-Path $seed 'base.txt'), "base`n", $utf8)
    [void](Fixture-Git $seed @('add', '.')); [void](Fixture-Git $seed @('commit', '-q', '-m', 'База позначки'))
    $marker = Fixture-Git $seed @('rev-parse', 'HEAD')
    [void](Fixture-Git $seed @('push', '-q', $origin, 'main', "main:refs/heads/$queue"))
    [void](Fixture-Git $w @('clone', '-q', $origin, $agent))
    [void](Fixture-Git $agent @('checkout', '-q', '-b', 'gemini/probe'))
    [IO.File]::WriteAllText((Join-Path $agent '00003.json'), ('{"data": "/9j/4AAQ' + ('QUJD' * 40) + 'eyJA1b2C3d4E5f6+/' + ('REVG' * 40) + '9k="}' + "`n"), $utf8)
    [void](Fixture-Git $agent @('add', '.')); [void](Fixture-Git $agent @('commit', '-q', '-m', 'Запис обміну'))
    $head = Fixture-Git $agent @('rev-parse', 'HEAD')
    [void](Fixture-Git $agent @('bundle', 'create', '-q', (Join-Path $out "$id.bundle"), 'refs/heads/gemini/probe', '^origin/main'))
    $status = [ordered]@{ v = 1; id = $id; slug = 'probe'; model = 'gpt-test'; n = 1; marker = $marker; head = $head; code = 'BLOCKED'
        bundle = "$id.bundle"; ahead = 1; turns = 1; minutes = 1 }
    [IO.File]::WriteAllText((Join-Path $out "$id.json"), ($status | ConvertTo-Json -Compress), $utf8)
    [void](Fixture-Git $pub @('init', '-q', '--bare', 'repo.git'))
    [void](Fixture-Git (Join-Path $pub 'repo.git') @('remote', 'add', 'origin', $origin))
    $checks = & {
        . (Join-Path $src 'gemini_publish.ps1') -WorkDir $pub -OutDir $out -OutboxDir (Join-Path $w 'outbox') -RepoUrl $origin
        $script:Repo = Join-Path $pub 'repo.git'; $script:NoHooks = Join-Path $w 'no-hooks'
        $newSecret = $script:SecretContentPattern
        $script:SecretContentPattern = $oldSecret; $script:WrapperVersion = $v1
        Write-FileAtomic (Join-Path $out ('marker-state/' + (Get-Sha256Hex "refs/remotes/origin/$queue $marker") + '.txt')) "DONE $id BLOCKED"
        function Pass {
            <# Прохід публікатора без мережі й доставки: fetch, повернуті відмови, стан, зняття, вихідні. #>
            $fetched = [datetime]::UtcNow
            [void](Invoke-Git @('fetch', '-q', '--prune', '--no-tags', 'origin', '+refs/heads/main:refs/remotes/origin/main',
                    '+refs/heads/gemini/*:refs/remotes/origin/gemini/*', '+refs/heads/gemini-queue/*:refs/remotes/origin/gemini-queue/*'))
            Reset-ReturnedRefusals
            Receive-RunState $id
            Confirm-PendingMarkers
            Remove-FinishedMarkers $fetched
            Receive-Outbox
        }
        function Lines([string]$Line) { @(Get-ChildItem -LiteralPath (Join-Path $OutboxDir 'done') -Filter '*.txt' -File -ErrorAction SilentlyContinue | Where-Object { ([IO.File]::ReadAllText($_.FullName, $utf8)).Trim() -ceq $Line }).Count }
        function Ref([string]$Name) { Fixture-Git $origin @('for-each-ref', '--format=%(objectname)', "refs/heads/$Name") }
        function Refusals { @([IO.File]::ReadAllLines((Join-Path $WorkDir 'publish.log'), $utf8) | Where-Object { $_.Contains("кінець $id — НЕ ОПУБЛІКОВАНО") }).Count }
        function Back { [void](Fixture-Git $seed @('push', '-q', $origin, "${marker}:refs/heads/$queue")) }
        $secret = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/probe SECRET'
        Pass
        if ($case -eq 'не-знімали') {
            # Давня відмова, після якої позначку не знімали: записів відмови й зняття нема, лише ключ seen.
            Remove-Item -Path (Join-Path $WorkDir 'finished/*'), (Join-Path $WorkDir 'refused/*') -Force -ErrorAction SilentlyContinue
            Pass; Pass
            [pscustomobject]@{ Name = 'давню незняту позначку повтор не публікує й не чіпає'; Ok = (Refusals) -eq 1 -and (Ref $queue) -ceq $marker -and -not (Ref 'gemini/probe') }
            return
        }
        Pass
        [pscustomobject]@{ Name = 'відмова SECRET: рядок, позначку знято'; Ok = (Lines $secret) -eq 1 -and -not (Ref $queue) }
        if ($case -eq 'без-версії') { Remove-Item -Path (Join-Path $WorkDir 'refused/*') -Force -ErrorAction SilentlyContinue }
        if ($case -eq 'оновлення') { $script:SecretContentPattern = $newSecret }
        if ($case -in @('оновлення', 'друга-відмова')) { $script:WrapperVersion = $v2 }
        Back; Pass; Pass
        switch ($case) {
            'оновлення' {
                [pscustomobject]@{ Name = 'нова версія: повторна публікація, рядок BLOCKED_PUBLISHED, позначку знято'
                    Ok = (Ref 'gemini/probe') -ceq $head -and (Lines 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/probe BLOCKED_PUBLISHED') -eq 1 -and -not (Ref $queue) -and (Refusals) -eq 1 }
            }
            'без-оновлення' {
                [pscustomobject]@{ Name = 'та сама версія: без повтору, рядок NO_REPUBLISH, позначку знято'
                    Ok = -not (Ref 'gemini/probe') -and (Refusals) -eq 1 -and (Lines 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/probe NO_REPUBLISH') -eq 1 -and -not (Ref $queue) }
            }
            default {
                # Друга відмова (нова версія чи запис без версії) — звичайний рядок; третього повтору немає.
                [pscustomobject]@{ Name = 'один повтор: друга відмова — рядок SECRET, позначку знято'; Ok = (Refusals) -eq 2 -and (Lines $secret) -eq 2 -and -not (Ref $queue) }
                Back; Pass; Pass
                [pscustomobject]@{ Name = 'після другої відмови позначка вдруге — без третього повтору, знято'; Ok = (Refusals) -eq 2 -and -not (Ref 'gemini/probe') -and -not (Ref $queue) }
            }
        }
    }
    foreach ($c in $checks) {
        if ($c.Ok) { Write-Host "  ✓ повтор-$case — $($c.Name)" } else { Write-Host "  ✗ повтор-$case — $($c.Name)"; $bad++ }
    }
}
exit ([int]($bad -gt 0))
