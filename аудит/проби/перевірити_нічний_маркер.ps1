param([Parameter(Mandatory = $true)][string]$WrapperRoot, [switch]$Before)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$WrapperRoot = (Resolve-Path -LiteralPath $WrapperRoot).Path
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('nightly-' + [guid]::NewGuid().ToString('N'))
$seed = Join-Path $testRoot 'seed'; $origin = Join-Path $testRoot 'origin.git'
$clone = Join-Path $testRoot 'clone'; $pub = Join-Path $testRoot 'pub'; $out = Join-Path $testRoot 'out'
function Git-At([string]$Dir, [string[]]$Items) {
    $lines = & git -C $Dir -c core.autocrlf=false -c core.quotepath=false @Items 2>&1
    if ($LASTEXITCODE -ne 0) { throw "git $($Items -join ' '): $lines" }
    ($lines -join "`n").Trim()
}
function Assert-That($Condition, [string]$Text) {
    if (-not $Condition) { throw $Text }
    Write-Output ('✓ ' + $Text)
}
try {
    [void](New-Item -ItemType Directory -Force -Path $testRoot, $seed, $pub, $out)
    [void](Git-At $testRoot @('init', '-q', '--bare', $origin))
    [void](Git-At $seed @('init', '-q', '-b', 'main'))
    [void](Git-At $seed @('config', 'user.name', 'Стенд'))
    [void](Git-At $seed @('config', 'user.email', 'stand@local'))
    [void](New-Item -ItemType Directory -Force -Path (Join-Path $seed 'аудит/наряди'))
    [IO.File]::WriteAllText((Join-Path $seed 'аудит/наряди/автоживий.md'), 'Роль — ВИКОНАВЕЦЬ', [Text.Encoding]::UTF8)
    $build = 'b' * 40
    [IO.File]::WriteAllText((Join-Path $seed 'build.txt'), $build, [Text.Encoding]::ASCII)
    [void](Git-At $seed @('add', '.'))
    [void](Git-At $seed @('commit', '-qm', 'База нічного стенда'))
    $base = Git-At $seed @('rev-parse', 'HEAD')
    [void](Git-At $seed @('remote', 'add', 'origin', $origin))
    [void](Git-At $seed @('push', '-q', 'origin', 'main'))
    [void](Git-At $testRoot @('clone', '-q', '-b', 'main', $origin, $clone))
    . (Join-Path $WrapperRoot 'gemini_run.ps1') -RepoDir $clone -RunsDir (Join-Path $testRoot 'runs')
    $script:NoHooks = Join-Path $testRoot 'no-hooks'
    $clock = [datetime]'2026-10-27T02:00:00Z'
    $queue = 'gemini-queue/Е1-нічний-живий-20261027/gpt-6.1-sol-high/1/gpu-p8'
    $none = @(Get-NightlyMarker $clock)
    if (-not $Before) { Assert-That ($none.Count -eq 0) 'без віддаленого дозволу обгортка не запускає ніч' }
    # Диспетчер / workflow — єдина сторона стенда, яка пише гілки черги.
    [void](Git-At $seed @('push', '-q', 'origin', "${base}:refs/heads/$queue"))
    [void](Git-At $clone @('fetch', '-q', 'origin'))
    $early = @(Get-NightlyMarker ([datetime]'2026-10-27T01:59:00Z'))
    Assert-That ($early.Count -eq 0) 'дозвіл не запускає ніч до 02:00 UTC'
    $nights = @(Get-NightlyMarker $clock)
    Assert-That ($nights.Count -eq 1) 'датований дозвіл зі спільним шаблоном повертає одну ніч'
    $night = $nights[0]
    Assert-That ($night.Valid -and $night.Gpu -and $night.Prio -eq 8 -and $night.Lane -eq 'codex') 'ніч має звичайний слот Codex і GPU'
    Assert-That ((Get-TaskSource $night) -ceq 'аудит/наряди/автоживий.md') 'ніч читає постійний шаблон автоживого'
    $autoQueue = "gemini-queue/автоживий-$build/gpt-6.1-sol-high/1/gpu-p2"
    [void](Git-At $seed @('push', '-q', 'origin', "${base}:refs/heads/$autoQueue"))
    [void](Git-At $clone @('fetch', '-q', 'origin'))
    Assert-That (@(Get-NightlyMarker $clock).Count -eq 0) 'автоживий тієї самої збірки прибирає повторний нічний прогін'
    [void](Git-At $origin @('update-ref', '-d', "refs/heads/$autoQueue"))
    $otherQueue = 'gemini-queue/автоживий-' + ('c' * 40) + '/gpt-6.1-sol-high/1/gpu-p2'
    [void](Git-At $seed @('push', '-q', 'origin', "${base}:refs/heads/$otherQueue"))
    [void](Git-At $clone @('fetch', '-q', '--prune', 'origin'))
    Assert-That (@(Get-NightlyMarker $clock).Count -eq 1) 'автоживий іншої збірки не прибирає дозволену ніч'
    [void](Git-At $seed @('commit', '-qm', 'Новий main', '--allow-empty'))
    [void](Git-At $seed @('push', '-q', 'origin', 'main'))
    [void](Git-At $clone @('fetch', '-q', 'origin'))
    $same = @(Get-NightlyMarker ([datetime]'2026-10-27T23:59:00Z'))[0]
    Assert-That ((Get-MarkerKey $night) -ceq (Get-MarkerKey $same)) 'новий main і перезапуск зберігають ключ доби'
    foreach ($slug in @('звичайний', ('автоперевірка-1981-' + ('a' * 40)), ('автоживий-' + ('b' * 40)))) {
        Assert-That ((Get-TaskSource ([pscustomobject]@{Slug=$slug})) -ceq (Get-AutoTaskPath $slug)) 'звичайний та автоматичні Е0 зберігають джерело'
    }
    $tomorrow = @(Get-NightlyMarker ([datetime]'2026-10-28T02:00:00Z'))
    if (-not $Before) { Assert-That ($tomorrow.Count -eq 0) 'дата без окремого дозволу не запускається' }
    # Диспетчер знімає нічну позначку комітом «ЗНЯТО…» поверх дозволу з main: голова не з main, але зняття має дійти до обробника скасування.
    if (-not $Before) {
        [void](Git-At $seed @('checkout', '-qb', 'зняття-ночі', $base))
        [void](Git-At $seed @('commit', '-qm', 'ЗНЯТО: проба нічного зняття', '--allow-empty'))
        $cancelSha = Git-At $seed @('rev-parse', 'HEAD')
        [void](Git-At $seed @('push', '-q', 'origin', "${cancelSha}:refs/heads/$queue"))
        [void](Git-At $seed @('checkout', '-q', 'main'))
        [void](Git-At $clone @('fetch', '-q', 'origin'))
        $cn = @(Get-NightlyMarker $clock)
        Assert-That ($cn.Count -eq 1 -and $cn[0].Cancel -and $cn[0].Sha -ceq $cancelSha) 'нічне ЗНЯТО поверх дозволу читається як зняття з SHA знімального коміту'
        [void](Git-At $origin @('update-ref', '-d', "refs/heads/$otherQueue"))
        [void](Git-At $clone @('fetch', '-q', '--prune', 'origin'))
        $nightReader = ${function:Get-NightlyMarker}
        & {
            $script:NightClosed = 0; $script:StateDir = Join-Path $testRoot 'state'; $script:SlotDir = Join-Path $testRoot 'slots'; [void](New-Item -ItemType Directory -Force -Path $script:StateDir, $script:SlotDir)
            function Get-NightlyMarker { & $nightReader $clock }
            function Repair-GpuModels { }
            function Save-Skips($Path) { }
            function Close-CancelledMarker($M, $Workers) { $script:NightClosed++ }
            [void](Start-Markers @())
        }
        Assert-That ($script:NightClosed -eq 1) 'нічне ЗНЯТО доходить до обробника скасування (Close-CancelledMarker) у Start-Markers'
        [void](Git-At $seed @('push', '-q', '-f', 'origin', "${base}:refs/heads/$queue"))
        [void](Git-At $clone @('fetch', '-q', 'origin'))
        Assert-That (@(Get-NightlyMarker $clock).Count -eq 1 -and -not @(Get-NightlyMarker $clock)[0].Cancel) 'повернений дозвіл знову дає звичайну ніч без скасування'
    }
    # У режимі ДО позначка є лише в локальному JSON, як у старій латці 02.
    if ($Before) {
        [void](Git-At $origin @('update-ref', '-d', "refs/heads/$queue"))
    } else {
        [void](Git-At $origin @('update-ref', '-d', "refs/heads/$queue"))
        [void](Git-At $clone @('fetch', '-q', '--prune', 'origin'))
        Assert-That (@(Get-NightlyMarker $clock).Count -eq 0) 'локальний JSON не відновлює знятий дозвіл'
        [void](Git-At $seed @('push', '-q', 'origin', "${base}:refs/heads/$queue"))
    }
    [void](Git-At $seed @('checkout', '-qb', ('gemini/' + $night.Slug), $base))
    [IO.File]::WriteAllText((Join-Path $seed 'результат.md'), 'Результат нічного стенда', [Text.Encoding]::UTF8)
    [void](Git-At $seed @('add', '.'))
    [void](Git-At $seed @('commit', '-qm', 'Готовий нічний результат'))
    $head = Git-At $seed @('rev-parse', 'HEAD')
    $id = '20261027-020000-aaaaaaaaaaaa'
    [void](Git-At $seed @('bundle', 'create', (Join-Path $out ($id + '.bundle')), ('refs/heads/gemini/' + $night.Slug), ('^' + $base)))
    $status = [ordered]@{v=1;id=$id;slug=$night.Slug;model=$night.Model;n=1;cond=$night.Cond;marker=$night.Sha;
        head=$head;start=$base;code='DONE';report='DONE';ahead=1;turns=1;minutes=1;bundle=($id + '.bundle')}
    [IO.File]::WriteAllText((Join-Path $out ($id + '.json')), ($status | ConvertTo-Json -Compress), $script:Utf8)
    [void](Git-At $pub @('init', '-q', '--bare'))
    [void](Git-At $pub @('remote', 'add', 'origin', $origin))
    [void](Git-At $pub @('fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*'))
    . (Join-Path $WrapperRoot 'gemini_publish.ps1') -WorkDir $pub -OutDir $out -RepoUrl $origin
    $script:NoHooks = Join-Path $testRoot 'no-hooks'
    $script:Repo = $pub
    [void](New-Item -ItemType Directory -Force -Path (Join-Path $pub 'seen'), (Join-Path $pub 'inbox'))
    $line = Get-Line $id
    if ($Before) {
        Assert-That ($line.Outbox -like '*STATE_INVALID') 'ДО: нічний бандл відхилено без віддаленої позначки'
    } else {
        Assert-That ($line.Outbox -ceq "GEMINI ОБГОРТКА: ГОТОВО gemini/$($night.Slug) $head") 'ПІСЛЯ: справжній бандл опубліковано з рядком ГОТОВО'
        Assert-That ((Git-At $origin @('rev-parse', ('refs/heads/gemini/' + $night.Slug))) -ceq $head) 'опублікований SHA дорівнює голові бандла'
    }
    # Навіть справжній бандл не надає прав іншому звичайному наряду без його позначки.
    $status.id = '20261027-020001-bbbbbbbbbbbb'; $status.slug = 'звичайний'
    [IO.File]::WriteAllText((Join-Path $out ($status.id + '.json')), ($status | ConvertTo-Json -Compress), $script:Utf8)
    $ordinary = Get-Line $status.id
    Assert-That ($null -eq $ordinary -or $ordinary.Outbox -like '*STATE_INVALID') 'звичайний стан без позначки відхилено тим самим публікатором'
    if (-not $Before) {
        [void](Git-At $seed @('push', '-q', 'origin', "${base}:refs/heads/gemini-queue/звичайний/gpt-6.1-sol-high/1/gpu-p8"))
        [void](Git-At $pub @('fetch', '-q', 'origin', '+refs/heads/*:refs/remotes/origin/*'))
        $status.bundle = ''; $status.code = 'BLOCKED'
        [IO.File]::WriteAllText((Join-Path $out ($status.id + '.json')), ($status | ConvertTo-Json -Compress), $script:Utf8)
        Assert-That ((Get-Line $status.id).Outbox -like '*gemini/звичайний BLOCKED') 'звичайна справжня позначка приймається'
        [void](Git-At $origin @('update-ref', '-d', 'refs/heads/gemini-queue/звичайний/gpt-6.1-sol-high/1/gpu-p8'))
        [void](Git-At $pub @('fetch', '-q', '--prune', 'origin', '+refs/heads/*:refs/remotes/origin/*'))
        $status.id = '20261027-020002-cccccccccccc'
        $status.code = 'CRASH'
        [IO.File]::WriteAllText((Join-Path $out ($status.id + '.json')), ($status | ConvertTo-Json -Compress), $script:Utf8)
        Assert-That ($null -eq (Get-Line $status.id)) 'знята звичайна позначка знову не дає прав'
    }
} finally {
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    if ([IO.Path]::GetDirectoryName($resolved) -cne $parent -or -not ([IO.Path]::GetFileName($resolved)).StartsWith('nightly-')) {
        throw 'Тека стенда поза тимчасовим коренем'
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
