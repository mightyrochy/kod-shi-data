#Requires -Version 5.1
<# Перевіряє справжні Complete-Status і Publish-Bundle на локальних репозиторіях без мережі й рушіїв. #>
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

$cases = @('private-start', 'new-main', 'published-start', 'BUNDLE_INVALID', 'REF_MISMATCH', 'SECRET', 'GITHUB_DIR', 'WRAPPER_FILES')
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
        default { 'work.txt' }
    }
    $file = Join-Path $repo $path
    [void](New-Item -ItemType Directory -Force -Path (Split-Path $file))
    [IO.File]::WriteAllText($file, "work`n", $utf8)
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
    $want = if ($Before) { 'BUNDLE_INVALID' } elseif ($case -cmatch '^[A-Z_]+$') { $case } else { 'OK' }
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
exit ([int]($bad -gt 0))
