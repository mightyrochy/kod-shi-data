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
        # Спроба /2 теж знімається: найбільша спроба з ЗНЯТО віддається як зняття, а не губиться на користь /1 з main.
        $q2 = $queue -replace '/1/gpu-p8$', '/2/gpu-p8'
        [void](Git-At $seed @('push', '-q', 'origin', "${cancelSha}:refs/heads/$q2"))
        [void](Git-At $clone @('fetch', '-q', 'origin'))
        $c2 = @(Get-NightlyMarker $clock)
        Assert-That ($c2.Count -eq 1 -and $c2[0].Cancel -and $c2[0].Ref.EndsWith('/2/gpu-p8')) 'ЗНЯТО на спробі /2 віддається як зняття /2'
        [void](Git-At $origin @('update-ref', '-d', "refs/heads/$q2"))
        [void](Git-At $clone @('fetch', '-q', '--prune', 'origin'))
    }
    if (-not $Before) {
        # Живий ноутбук 10.11: /1 кінчилась CRASH (сон), диспетчер поставив /2 на тому самому коміті; стан — у теці стенда.
        $nState = Join-Path $testRoot 'state'; [void](New-Item -ItemType Directory -Force -Path $nState)
        $nFile = Join-Path $testRoot 'runs/nightly/20261027.json'; $nFile2 = Join-Path $testRoot 'runs/nightly/20261027-2.json'
        $first = [IO.File]::ReadAllText($nFile, $script:Utf8)
        Write-FileAtomic (Get-StatePath (Get-MarkerKey $night) $nState) 'DONE 20261027-020000-aaaaaaaaaaaa CRASH'
        Assert-That (-not (Test-MarkerReady (Get-MarkerState $night $nState))) '/1 після CRASH — кінцевий стан, сама не береться'
        $queue2 = $queue -replace '/1/gpu-p8$', '/2/gpu-p8'; $queue3 = $queue -replace '/1/gpu-p8$', '/3/gpu-p8'
        [void](Git-At $seed @('push', '-q', 'origin', "${base}:refs/heads/$queue2"))
        [void](Git-At $clone @('fetch', '-q', 'origin'))
        $two = @(Get-NightlyMarker $clock)
        Assert-That ($two.Count -eq 1 -and $two[0].N -ceq '2' -and $two[0].Sha -ceq $night.Sha) '/1 DONE CRASH і /2 на тому ж коміті — бере /2'
        Assert-That ($two[0].Slug -ceq $night.Slug -and $two[0].Gpu -and $two[0].Prio -eq 8) '/2 — той самий slug (його тримає Test-SlugBusy), GPU, p8'
        Assert-That ((Get-MarkerKey $two[0]) -cne (Get-MarkerKey $night) -and (Test-MarkerReady (Get-MarkerState $two[0] $nState))) '/2 має свій ключ стану: кінець /1 її не блокує'
        Assert-That ((Test-Path -LiteralPath $nFile2) -and ([IO.File]::ReadAllText($nFile, $script:Utf8) -ceq $first)) 'стан /2 у своєму файлі, файл /1 (старий формат) не змінено'
        $good = [IO.File]::ReadAllText($nFile2, $script:Utf8)
        [IO.File]::WriteAllText($nFile2, '{"date":"20261027","sha":"x","time":"1"}', $script:Utf8)
        $threw = $false; try { [void](Get-NightlyMarker $clock) } catch { $threw = $_.Exception.Message -ceq 'Хибний стан нічного прогону' }
        Assert-That $threw 'хибний стан спроби /2 лишає захист «Хибний стан нічного прогону»'
        [IO.File]::WriteAllText($nFile2, $good, $script:Utf8)
        $off = Git-At $seed @('commit-tree', "${base}^{tree}", '-p', $base, '-m', 'Поза main')
        [void](Git-At $seed @('push', '-q', 'origin', "${off}:refs/heads/$queue3"))
        [void](Git-At $clone @('fetch', '-q', 'origin'))
        Assert-That (@(Get-NightlyMarker $clock)[0].N -ceq '2') '/3 не на main — не бере, лишається /2'
        [void](Git-At $origin @('update-ref', '-d', "refs/heads/$queue2"))
        [void](Git-At $clone @('fetch', '-q', '--prune', 'origin'))
        $one = @(Get-NightlyMarker $clock)
        Assert-That ($one.Count -eq 1 -and $one[0].N -ceq '1' -and (Get-MarkerKey $one[0]) -ceq (Get-MarkerKey $night)) 'тільки /1 (а /3 не на main) — як раніше: /1'
        [void](Git-At $origin @('update-ref', '-d', "refs/heads/$queue3"))
        [void](Git-At $clone @('fetch', '-q', '--prune', 'origin'))
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
