<# Стенд позначки давнього нічного Е1: окремого нічного прогону нема (менеджер 20.11 за словом власника 20.11), а позначки
`gemini-queue/Е1-нічний-живий-<дата>/…` ще стоять у черзі (одна йде просто зараз). Обгортка бере їх як звичайні позначки:
без шаблону наряду — кінець NO_TASK_FILE, зняті «ЗНЯТО» — CANCELLED, бандл прогону, що вже йшов, — публікація звичайним
шляхом; нічого не падає й не зависає. Справжні gemini_run.ps1 і gemini_publish.ps1 на тимчасовому origin. #>
param([Parameter(Mandatory = $true)][string]$WrapperRoot)
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
    [IO.File]::WriteAllText((Join-Path $seed 'build.txt'), ('b' * 40), [Text.Encoding]::ASCII)
    [void](Git-At $seed @('add', '.'))
    [void](Git-At $seed @('commit', '-qm', 'База стенда'))
    $base = Git-At $seed @('rev-parse', 'HEAD')
    [void](Git-At $seed @('remote', 'add', 'origin', $origin))
    [void](Git-At $seed @('push', '-q', 'origin', 'main'))
    [void](Git-At $testRoot @('clone', '-q', '-b', 'main', $origin, $clone))
    . (Join-Path $WrapperRoot 'gemini_run.ps1') -RepoDir $clone -RunsDir (Join-Path $testRoot 'runs')
    $script:NoHooks = Join-Path $testRoot 'no-hooks'
    $queue = 'gemini-queue/Е1-нічний-живий-20261027/gpt-6.1-sol-high/1/gpu-p8'
    [void](Git-At $seed @('push', '-q', 'origin', "${base}:refs/heads/$queue"))
    [void](Git-At $clone @('fetch', '-q', 'origin'))
    Assert-That (-not (Get-Command Get-NightlyMarker -ErrorAction SilentlyContinue)) 'окремого читача нічного дозволу нема'
    $night = @(Get-Markers | Where-Object { $_.Name -ceq $queue })
    Assert-That ($night.Count -eq 1 -and $night[0].Valid -and $night[0].Gpu -and $night[0].Prio -eq 8 -and $night[0].Lane -eq 'codex') 'давня нічна позначка — звичайна позначка черги: слот Codex, GPU, p8'
    $night = $night[0]
    $task = Get-TaskSource $night
    Assert-That ($task -cne 'аудит/наряди/автоживий.md' -and -not (Test-TaskFile $base $task)) "шаблону автоживого не бере: наряду $task нема — кінець NO_TASK_FILE до рушія"
    Assert-That ((Get-AutoTaskPath ('автоживий-' + ('b' * 40))) -ceq 'аудит/наряди/автоживий.md') 'автоживий бере свій шаблон, як і був'
    # Зняття поверх позначки (голова не з main) доходить до спільного обробника скасування.
    [void](Git-At $seed @('checkout', '-qb', 'зняття-ночі', $base))
    [void](Git-At $seed @('commit', '-qm', 'ЗНЯТО: нічного прогону нема', '--allow-empty'))
    $cancelSha = Git-At $seed @('rev-parse', 'HEAD')
    [void](Git-At $seed @('push', '-q', '-f', 'origin', "${cancelSha}:refs/heads/$queue"))
    [void](Git-At $seed @('checkout', '-q', 'main'))
    [void](Git-At $clone @('fetch', '-q', 'origin'))
    & {
        $script:NightClosed = 0; $script:StateDir = Join-Path $testRoot 'state'; $script:SlotDir = Join-Path $testRoot 'slots'; [void](New-Item -ItemType Directory -Force -Path $script:StateDir, $script:SlotDir)
        function Repair-GpuModels { }
        function Save-Skips($Path) { }
        function Close-CancelledMarker($M, $Workers) { if ($M.Name -ceq $queue -and $M.Cancel -and $M.Sha -ceq $cancelSha) { $script:NightClosed++ } }
        [void](Start-Markers @())
    }
    Assert-That ($script:NightClosed -eq 1) 'ЗНЯТО на нічній позначці — CANCELLED тим самим обробником, що в усіх позначок, без падіння'
    [void](Git-At $seed @('push', '-q', '-f', 'origin', "${base}:refs/heads/$queue"))
    # Прогін, що вже йшов, кінчається бандлом — публікатор приймає його проти позначки на origin, як будь-який.
    [void](Git-At $seed @('checkout', '-qb', ('gemini/' + $night.Slug), $base))
    [IO.File]::WriteAllText((Join-Path $seed 'результат.md'), 'Результат стенда', [Text.Encoding]::UTF8)
    [void](Git-At $seed @('add', '.'))
    [void](Git-At $seed @('commit', '-qm', 'Готовий результат'))
    $head = Git-At $seed @('rev-parse', 'HEAD')
    $id = '20261027-020000-aaaaaaaaaaaa'
    [void](Git-At $seed @('bundle', 'create', (Join-Path $out ($id + '.bundle')), ('refs/heads/gemini/' + $night.Slug), ('^' + $base)))
    $status = [ordered]@{v=1;id=$id;slug=$night.Slug;model=$night.Model;n=1;cond=$night.Cond;marker=$base;
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
    Assert-That ($line.Outbox -ceq "GEMINI ОБГОРТКА: ГОТОВО gemini/$($night.Slug) $head") 'бандл прогону нічної позначки опубліковано звичайним рядком ГОТОВО'
    Assert-That ((Git-At $origin @('rev-parse', ('refs/heads/gemini/' + $night.Slug))) -ceq $head) 'опублікований SHA дорівнює голові бандла'
    # Справжній бандл не надає прав наряду без його позначки.
    $status.id = '20261027-020001-bbbbbbbbbbbb'; $status.slug = 'звичайний'
    [IO.File]::WriteAllText((Join-Path $out ($status.id + '.json')), ($status | ConvertTo-Json -Compress), $script:Utf8)
    $ordinary = Get-Line $status.id
    Assert-That ($null -eq $ordinary -or $ordinary.Outbox -like '*STATE_INVALID') 'стан без позначки відхилено тим самим публікатором'
} finally {
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')
    if ([IO.Path]::GetDirectoryName($resolved) -cne $parent -or -not ([IO.Path]::GetFileName($resolved)).StartsWith('nightly-')) {
        throw 'Тека стенда поза тимчасовим коренем'
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
