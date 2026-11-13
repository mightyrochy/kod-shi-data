#Requires -Version 5.1
# Мірило наряду обгортка-ресурс-слотів: місце теки задачі під час задачі й після доставки на справжньому дереві
# репозиторію (CI — його checkout), а також давні копії, що лишаються чи прибираються першим проходом.
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('kopiia-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
function Get-DirBytes([string]$Dir) {
    <# Байти файлів теки (без .git-файлу worktree); нема теки — 0. #>
    if (-not (Test-Path -LiteralPath $Dir)) { return 0L }
    $sum = 0L
    foreach ($f in [IO.Directory]::EnumerateFiles($Dir, '*', [IO.SearchOption]::AllDirectories)) { $sum += (New-Object IO.FileInfo $f).Length }
    $sum
}
function MB([long]$Bytes) { [Math]::Round($Bytes / 1MB, 1) }
$realRepo = ''
try {
    $GitExe = (Get-Command git).Source
    $RepoDir = (Resolve-Path (Join-Path $SourceDir '../../..')).Path; $realRepo = $RepoDir
    $LaneDir = Join-Path $tmp 'lanes'
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $script:NoHooks = Join-Path $tmp 'no-hooks'; $script:SlotDir = Join-Path $tmp 'slots'
    foreach ($d in @($script:NoHooks, $script:SlotDir)) { [void][IO.Directory]::CreateDirectory($d) }
    $script:Log = New-Object System.Collections.Generic.List[string]
    function Write-Log([string]$Text) { $script:Log.Add($Text) }

    Scenario 'копія задачі на дереві репозиторію' {
        $commit = (Invoke-Git @('rev-parse', 'HEAD')).Out.Trim()
        $sizes = @{}; $full = 0L
        foreach ($e in (Invoke-Git @('ls-tree', '-r', '-l', '-z', $commit)).Out.Split([char]0)) {
            if ($e -match '^[0-7]{6} blob [0-9a-f]{40,64} +([0-9]+)\t(.+)$') { $sizes[$Matches[2]] = [long]$Matches[1]; $full += [long]$Matches[1] }
        }
        $skip = @(Get-ArchiveDirs $commit '')
        $skipBytes = 0L
        foreach ($p in $sizes.Keys) { foreach ($d in $skip) { if ($p.StartsWith($d + '/', [StringComparison]::Ordinal)) { $skipBytes += $sizes[$p]; break } } }
        $dir = Join-Path (Join-Path $tmp 'w') 'run-1'
        $temp0 = $env:TEMP; $clone = $script:RepoDir
        $repo = New-TaskCopy $dir $commit ''
        $during = Get-DirBytes $repo
        "  ДО: повна копія слота $(MB $full) МБ (усі відстежувані файли), лишалась після задачі"
        "  ПІСЛЯ під час задачі: $(MB $during) МБ ($($skip.Count) тек-архівів не викладено, $(MB $skipBytes) МБ)"
        Check 'git і TEMP/TMP — у теці задачі' ($script:RepoDir -ceq $repo -and $env:TEMP -ceq (Join-Path $dir 'tmp') -and $env:TMP -ceq $env:TEMP)
        Check 'копія чиста й на коміті задачі' ((Invoke-Git @('status', '--porcelain')).Out.Trim() -eq '' -and (Invoke-Git @('rev-parse', 'HEAD')).Out.Trim() -ceq $commit)
        Check 'теки-архіви не викладено' ($skip.Count -gt 0 -and -not (Test-Path -LiteralPath (Join-Path $repo $skip[0])))
        Check 'решта дерева на місці' ((Test-Path -LiteralPath (Join-Path $repo 'AGENTS.md')) -and (Test-Path -LiteralPath (Join-Path $repo 'аудит/адаптери/gemini/queue_lanes.ps1')))
        Check 'копія менша за половину повної' ($during -gt 0 -and $during -lt $full / 2)
        $small = $skip[-1]
        [void](Invoke-Git @('sparse-checkout', 'add', "/$small/"))
        Check "сесія додає потрібну теку сама ($small)" ((Test-Path -LiteralPath (Join-Path $repo $small)) -and (Invoke-Git @('status', '--porcelain')).Out.Trim() -eq '')
        Check 'тека, названа в наряді, лишається у копії' (-not (@(Get-ArchiveDirs $commit "Дивись ``$($skip[0])/звіт.md``.") -ccontains $skip[0]))
        Check 'промпт називає теку задачі й sparse-checkout' ((Get-TaskDirText $dir).Contains($dir) -and (Get-TaskDirText $dir).Contains('git sparse-checkout add'))
        $kept = Close-TaskCopy @($commit)
        $after = Get-DirBytes $dir
        "  ПІСЛЯ доставки: $(MB $after) МБ"
        Check 'після доставки теки задачі нема, клон і TEMP — як були' ($kept -eq '' -and $after -eq 0 -and $script:RepoDir -ceq $clone -and $env:TEMP -ceq $temp0)
        Check 'worktree копії знято з клону' (-not ((Invoke-Git @('worktree', 'list', '--porcelain')).Out.Contains($repo.Replace('\', '/'))) -and -not ((Invoke-Git @('worktree', 'list', '--porcelain')).Out.Contains($repo)))
    }

    Scenario 'недоставлене лишається, накопичене прибирається' {
        $origin = Join-Path $tmp 'origin.git'; $clone = Join-Path $tmp 'clone'
        & git init -q --bare $origin; & git init -q -b main $clone
        & git -C $clone config user.name 'стенд'; & git -C $clone config user.email 'stend@example.invalid'
        & git -C $clone remote add origin $origin
        [void][IO.Directory]::CreateDirectory("$clone/аудит/проби/архів")
        [IO.File]::WriteAllText("$clone/a.txt", '1', $utf); [IO.File]::WriteAllText("$clone/аудит/проби/архів/x.txt", 'x', $utf)
        & git -C $clone add -A; & git -C $clone commit -q -m 'початкова'; & git -C $clone push -q origin main
        & git -C $clone fetch -q origin
        $script:RepoDir = $clone; $root = Join-Path $tmp 'w2'
        $dir = Join-Path $root 'run-kept'
        $repo = New-TaskCopy $dir 'refs/remotes/origin/main' ''
        & git -C $repo -c user.name=стенд -c user.email=stend@example.invalid commit -q --allow-empty -m 'незапушене'
        $kept = Close-TaskCopy @('--remotes')
        Check 'тека з незапушеним комітом лишається з kept.txt' ($kept -ceq $dir -and (Test-Path -LiteralPath (Join-Path $dir 'kept.txt')) -and $script:RepoDir -ceq $clone)
        $busy = Join-Path $root 'run-busy'
        [void](New-TaskCopy $busy 'refs/remotes/origin/main' ''); $script:TaskCopy = $null; $script:RepoDir = $clone
        $lock = Open-Lock (Join-Path $script:SlotDir 'claude-1.lock')
        [IO.File]::WriteAllText((Join-Path $script:SlotDir 'claude-1.json'), (@{ slot = 'claude-1'; copy = $busy } | ConvertTo-Json -Compress), $utf)
        & git -C $clone worktree add -q --detach (Join-Path $root 'agy-1') 'refs/remotes/origin/main'
        $before = @(Get-ChildItem -LiteralPath $root -Directory).Count
        Clear-TaskCopies $root @('--remotes')
        $lock.Dispose()
        Check 'перший прохід прибрав давню копію слота' (-not (Test-Path -LiteralPath (Join-Path $root 'agy-1')) -and $before -eq 3)
        Check 'копію зайнятого слота й недоставлене не чіпає' ((Test-Path -LiteralPath (Join-Path $busy 'repo/a.txt')) -and (Test-Path -LiteralPath (Join-Path $dir 'kept.txt')))
        Clear-TaskCopies $root @('--remotes')
        Check 'звільнений слот: копію прибрано наступним проходом' (-not (Test-Path -LiteralPath $busy) -and (Test-Path -LiteralPath $dir))
    }
    function Put([string]$Dir, [string]$Name, [string]$Text, [string]$Msg) {
        [IO.File]::WriteAllText((Join-Path $Dir $Name), $Text, $utf)
        & git -C $Dir add -A; & git -C $Dir commit -q -m $Msg
    }
    function Rev([string]$Dir, [string]$Ref) { (& git -C $Dir rev-parse $Ref).Trim() }
    function Get-FnText([string]$File, [string]$Name) {
        <# Справжня функція з джерела (AST) — для промптів обох смуг без запуску самих планувальників. #>
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir $File), [ref]$tokens, [ref]$errors)
        $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $Name }, $false).Extent.Text
    }

    Scenario 'старт нової спроби: від свіжого main, коли гілка злита чи відстала' {
        $origin = Join-Path $tmp 'o3.git'; $clone = Join-Path $tmp 'c3'
        & git init -q --bare $origin; & git init -q -b main $clone
        & git -C $clone config user.name 'стенд'; & git -C $clone config user.email 'stend@example.invalid'; & git -C $clone config core.autocrlf false
        & git -C $clone remote add origin $origin
        Put $clone 'a.txt' "1`n" 'початкова'
        & git -C $clone push -q origin main
        $script:RepoDir = $clone; $root = Join-Path $tmp 'w3'
        $base = Rev $clone 'HEAD'
        # Гілки попередніх спроб: злита в main; відстала без конфлікту; відстала з конфліктом; вже з main.
        foreach ($b in @('zlyta', 'vidstala', 'konflikt')) {
            & git -C $clone checkout -q -b "gemini/$b" $base
            Put $clone $(if ($b -eq 'konflikt') { 'a.txt' } else { "$b.txt" }) "гілка`n" "робота $b"
            & git -C $clone push -q origin "gemini/$b"
        }
        & git -C $clone checkout -q main
        & git -C $clone merge -q --no-ff -m 'злито zlyta' 'gemini/zlyta'
        Put $clone 'a.txt' "main`n" 'main правит a.txt'
        Put $clone 'g.txt' "g`n" 'свіжий main'
        & git -C $clone push -q origin main
        & git -C $clone checkout -q -b 'gemini/z-main' main
        Put $clone 'z.txt' "z`n" 'гілка вже з main'
        & git -C $clone push -q origin 'gemini/z-main'
        & git -C $clone checkout -q main
        & git -C $clone fetch -q origin '+refs/heads/*:refs/remotes/origin/*'
        $main = Rev $clone 'refs/remotes/origin/main'
        $tip = @{}; foreach ($b in @('zlyta', 'vidstala', 'konflikt', 'z-main')) { $tip[$b] = Rev $clone "refs/remotes/origin/gemini/$b" }

        $n = Get-AttemptStart '' $main
        Check 'гілки нема — від main' ($n.Mode -ceq 'NEW' -and $n.Start -ceq $main)
        $z = Get-AttemptStart $tip['zlyta'] $main
        Check 'гілка злита — від main, а не від її голови' ($z.Mode -ceq 'MERGED' -and $z.Start -ceq $main -and $z.Start -cne $tip['zlyta'])
        $c = Get-AttemptStart $tip['z-main'] $main
        Check 'гілка вже містить main — гілка як є, злиття не треба' ($c.Mode -ceq 'CURRENT' -and $c.Start -ceq $tip['z-main'])
        $v = Get-AttemptStart $tip['vidstala'] $main
        Check 'гілка не злита й відстала — від гілки, main буде влито' ($v.Mode -ceq 'BEHIND' -and $v.Start -ceq $tip['vidstala'])

        # Злита: нова спроба від main, пуш звичайний (без force) проходить, бо нова голова — нащадок старої.
        $repo = New-TaskCopy (Join-Path $root 'zlyta') $z.Start ''
        [void](Invoke-Git @('checkout', '-q', '-f', '--ignore-other-worktrees', '-B', 'gemini/zlyta', $z.Start))
        Put $repo 'nova.txt' "нова`n" 'нова спроба'
        & git -C $repo push -q --no-thin origin 'HEAD:refs/heads/gemini/zlyta'
        Check 'злита гілка: пуш нової спроби без force проходить, голова на origin — нова' ($LASTEXITCODE -eq 0 -and (Rev $origin 'refs/heads/gemini/zlyta') -ceq (Rev $repo 'HEAD') -and (Test-Path -LiteralPath (Join-Path $repo 'g.txt')))
        [void](Close-TaskCopy @('--branches', '--remotes'))

        # Відстала без конфлікту: гілка + злиття main до агента; роботу агента рахують від злиття.
        $repo = New-TaskCopy (Join-Path $root 'vidstala') $v.Start ''
        [void](Invoke-Git @('checkout', '-q', '-f', '--ignore-other-worktrees', '-B', 'gemini/vidstala', $v.Start))
        $h = Merge-MainIntoCopy $main 'gemini/vidstala'
        $parents = @((& git -C $repo log -1 --format=%P $h).Trim() -split ' ')
        Check 'відстала без конфлікту: копія — голова гілки з влитим main (злиття двома батьками)' ($h -and $h -cne $v.Start -and $parents.Count -eq 2 -and $parents -ccontains $v.Start -and $parents -ccontains $main -and (Test-Path -LiteralPath (Join-Path $repo 'g.txt')) -and (Test-Path -LiteralPath (Join-Path $repo 'vidstala.txt')))
        Check 'коміт злиття — з повідомленням обгортки, дерево чисте' ((& git -C $repo log -1 --format=%s $h) -cmatch '^Обгортка: влито origin/main у gemini/vidstala' -and (Invoke-Git @('status', '--porcelain')).Out.Trim() -eq '')
        Put $repo 'agent.txt' "агент`n" 'робота агента'
        Check 'роботу агента рахують від злиття (1 коміт), а не від старої голови' ((Invoke-Git @('rev-list', '--count', "$h..HEAD")).Out.Trim() -eq '1')
        & git -C $repo push -q --no-thin origin 'HEAD:refs/heads/gemini/vidstala'
        Check 'відстала гілка: пуш після злиття — без force, швидкий вперед' ($LASTEXITCODE -eq 0 -and (Rev $origin 'refs/heads/gemini/vidstala') -ceq (Rev $repo 'HEAD'))
        [void](Close-TaskCopy @('--branches', '--remotes'))

        # Відстала з конфліктом: копія — голова гілки без напівзлиття, агентові першим кроком «влий main».
        $k = Get-AttemptStart $tip['konflikt'] $main
        $repo = New-TaskCopy (Join-Path $root 'konflikt') $k.Start ''
        [void](Invoke-Git @('checkout', '-q', '-f', '--ignore-other-worktrees', '-B', 'gemini/konflikt', $k.Start))
        $h = Merge-MainIntoCopy $main 'gemini/konflikt'
        $mid = (& git -C $repo rev-parse -q --verify MERGE_HEAD 2>$null)
        Check 'конфлікт: злиття скасовано, копія — голова гілки, дерево чисте' ($k.Mode -ceq 'BEHIND' -and $h -ceq '' -and (Rev $repo 'HEAD') -ceq $tip['konflikt'] -and -not $mid -and (Invoke-Git @('status', '--porcelain')).Out.Trim() -eq '')
        $step = Get-MergeStepText 'gemini/konflikt'
        . ([scriptblock]::Create((Get-FnText 'gemini_run.ps1' 'Get-TaskRole'))); function Get-TaskSource { 'аудит/наряди/стенд.md' }
        $gem = & ([scriptblock]::Create((Get-FnText 'gemini_run.ps1' 'Get-Prompt') + "`nGet-Prompt @args")) ([pscustomobject]@{ Slug = 'konflikt'; Sha = 'a' * 40 }) 'НАРЯД' 'codex' '' $step
        $gemPlain = & ([scriptblock]::Create((Get-FnText 'gemini_run.ps1' 'Get-Prompt') + "`nGet-Prompt @args")) ([pscustomobject]@{ Slug = 'konflikt'; Sha = 'a' * 40 }) 'НАРЯД' 'codex' '' ''
        Check 'gemini: turn1 несе крок «влий origin/main, за змістом main» лише при конфлікті' ($step -cmatch 'origin/main' -and $step -cmatch 'за змістом' -and $gem.Contains($step) -and -not $gemPlain.Contains('Перший крок'))
        $cl = & ([scriptblock]::Create((Get-FnText 'claude_run.ps1' 'Get-Prompt') + "`nGet-Prompt @args")) ([pscustomobject]@{ Slug = 'konflikt'; Sha = 'a' * 40 }) 'НАРЯД' 'claude/konflikt' '' $main
        $clPlain = & ([scriptblock]::Create((Get-FnText 'claude_run.ps1' 'Get-Prompt') + "`nGet-Prompt @args")) ([pscustomobject]@{ Slug = 'konflikt'; Sha = 'a' * 40 }) 'НАРЯД' 'claude/konflikt' '' ''
        Check 'claude: відстала гілка — у промпті крок влити отриманий SHA main (не origin/main спільного клону); без цього — як було' ($cl.Contains((Get-MergeStepText 'claude/konflikt' $main)) -and $cl.Contains("git merge $main") -and -not $cl.Contains('origin/main') -and $cl.Contains('Продовжуй з гілки') -and -not $clPlain.Contains('Перший крок'))
        [void](Close-TaskCopy @('--branches', '--remotes'))
        Check 'обидві смуги обирають старт спільним Get-AttemptStart, без власної копії правила' ((Get-FnText 'gemini_run.ps1' 'Invoke-Task').Contains('Get-AttemptStart') -and (Get-FnText 'claude_run.ps1' 'Invoke-Task').Contains('Get-AttemptStart') -and (Get-FnText 'gemini_run.ps1' 'Invoke-Task').Contains('Merge-MainIntoCopy'))
    }

    function New-DeniedCopy([string]$Dir) {
        <# Копія з вкладеною `.git`, вміст якої власнику заборонено читати, — як лишає її обірваний стенд кінця роботи
        (With-DeniedRead): tmp\end-test-x\access-copy\repo\.git. Повертає суму байтів файлів копії. #>
        $git = Join-Path $Dir 'tmp/end-test-x/access-copy/repo/.git'
        [void][IO.Directory]::CreateDirectory((Join-Path $git 'objects')); [void][IO.Directory]::CreateDirectory((Join-Path $Dir 'repo'))
        [IO.File]::WriteAllBytes((Join-Path $git 'objects/pack.bin'), (New-Object byte[] 1048576))
        [IO.File]::WriteAllText((Join-Path $git 'HEAD'), 'ref: refs/heads/x', $utf)
        [IO.File]::WriteAllText((Join-Path $Dir 'repo/a.txt'), 'абв', $utf)
        if ($env:OS -eq 'Windows_NT') {
            $acl = Get-Acl -LiteralPath $git
            $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule([Security.Principal.WindowsIdentity]::GetCurrent().User, 'ListDirectory,ReadData', 'ContainerInherit,ObjectInherit', 'None', 'Deny')))
            Set-Acl -LiteralPath $git -AclObject $acl
        } else { & chmod 000 -- $git }
        1048576L + 17 + $utf.GetByteCount('абв')
    }

    Scenario 'копія із забороною читання вкладеної .git: прибирається, а не лишається назавжди' {
        $root = Join-Path $tmp 'w4'
        # ДО: Remove-Item лишав таку копію щоразу (у журналі обгортки — «не прибрана … .git … is denied»).
        $before = Join-Path $root 'run-before'; [void](New-DeniedCopy $before)
        $msg = ''
        try { Remove-Item -LiteralPath $before -Recurse -Force -ErrorAction Stop } catch { $msg = $_.Exception.Message }
        # Піднятий токен (раннер CI) видаляє й таку копію сам: тоді ДО не відтворюється — це видно в назві, а не червоніє.
        $effective = (Test-Path -LiteralPath $before) -and $msg -match 'denied|Permission|доступ'
        if ($effective) { Check "ДО: Remove-Item не прибирає копію, лишається в журналі «не прибрана»: $msg" $true }
        else { "- ДО не відтворено: Remove-Item з цим токеном прибрав копію з забороною сам (піднятий токен)" }
        if (Test-Path -LiteralPath $before) { [void](Reset-TreeAcl $before); Remove-Item -LiteralPath $before -Recurse -Force }
        # ПІСЛЯ: Remove-TaskCopy скидає ACL і прибирає; журнал каже, скільки звільнено.
        $dir = Join-Path $root 'run-after'; $size = New-DeniedCopy $dir
        $script:Log.Clear()
        $kept = Remove-TaskCopy $dir @('--remotes')
        Check "ПІСЛЯ: копію прибрано ($($dir)), не лишилась" ($kept -eq '' -and -not (Test-Path -LiteralPath $dir))
        $line = @($script:Log | Where-Object { $_ -like "копія задачі $dir *" })
        Check "журнал: звільнено $size байт, ACL скинуто, «не прибрана» нема" ($line.Count -eq 1 -and ($line[0] -ceq "копія задачі $dir прибрана: звільнено $size байт (ACL скинуто)" -or (-not $effective -and $line[0] -ceq "копія задачі $dir прибрана: звільнено $size байт")))
        # Те саме через накопичене: давня копія слота з забороною.
        $old = Join-Path $root 'run-old'; [void](New-DeniedCopy $old)
        Clear-TaskCopies $root @('--remotes')
        Check 'накопичене: давня копія з забороною прибирається першим проходом' (-not (Test-Path -LiteralPath $old))
        if ($env:OS -eq 'Windows_NT') {
            # Зайнятий іншим процесом файл — тимчасовий стан: копія лишається до наступного прибирання.
            $busy = Join-Path $root 'run-busy'; [void][IO.Directory]::CreateDirectory("$busy/repo")
            $h = [IO.File]::Open((Join-Path $busy 'repo/open.bin'), 'Create', 'ReadWrite', 'None')
            try {
                $kept = Remove-TaskCopy $busy @('--remotes')
                Check 'зайнятий файл: копія лишається до наступного прибирання, журнал каже «не прибрана»' ($kept -eq '' -and (Test-Path -LiteralPath $busy) -and @($script:Log | Where-Object { $_ -like "копія задачі $busy не прибрана*" }).Count -eq 1)
            } finally { $h.Dispose() }
            [void](Remove-TaskCopy $busy @('--remotes'))
            Check 'зайнятий файл звільнено: наступне прибирання знімає копію' (-not (Test-Path -LiteralPath $busy))
        }
    }

    Scenario 'агент у копії пише файли з CRLF — у коміті LF, як у репозиторії' {
        # Прогін 03d38720: агент на Windows переписав паспорти текстовим записом (`\n` → `\r\n`), клон ноутбука тримає
        # core.autocrlf=false — git add поклав CRLF у блоби: +5421/−5351 замість +70. Агент-підставка — окремий процес за
        # тим самим New-StartInfo, що й справжній рушій: пише файли з CRLF і сам кличе git add/commit (PowerShell і Git Bash).
        $origin = Join-Path $tmp 'o6.git'; $clone = Join-Path $tmp 'c6'
        & git init -q --bare $origin; & git init -q -b main $clone
        & git -C $clone config user.name 'стенд'; & git -C $clone config user.email 'stend@example.invalid'
        & git -C $clone config core.autocrlf false; & git -C $clone config core.safecrlf false
        & git -C $clone remote add origin $origin
        [IO.File]::WriteAllText("$clone/p.md", "a`nb`nc`n", $utf)
        [IO.File]::WriteAllText("$clone/q.md", "a`nb`nc`n", $utf)
        [IO.File]::WriteAllText("$clone/k.csv", "x;y`r`n1;2`r`n", $utf)
        [IO.File]::WriteAllBytes("$clone/b.dat", [byte[]](0, 1, 13, 10, 0, 2))
        & git -C $clone add -A; & git -C $clone commit -q -m 'початкова'; & git -C $clone push -q origin main
        & git -C $clone fetch -q origin
        $script:RepoDir = $clone
        $repo = New-TaskCopy (Join-Path (Join-Path $tmp 'w6') 'run-1') 'refs/remotes/origin/main' ''
        $ps = (Get-Process -Id $PID).Path
        $agent = Join-Path $tmp 'agent.ps1'
        [IO.File]::WriteAllText($agent, @'
param([string]$Repo)
$u = New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText("$Repo/p.md", "a`r`nb`r`nc`r`nd`r`n", $u)
[IO.File]::WriteAllText("$Repo/k.csv", "x;y`r`n1;2`r`n3;4`r`n", $u)
[IO.File]::WriteAllText("$Repo/new.md", "n1`r`nn2`r`n", $u)
& git -C $Repo add -A
& git -C $Repo commit -q -m 'agent: PowerShell'
'@, $utf)
        $r = Invoke-Native $ps @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $agent, $repo) $repo
        $r1 = (Invoke-Git @('rev-parse', 'HEAD')).Out.Trim()
        $blob = { param($Rev, $Path) (Invoke-Git @('show', "${Rev}:$Path")).Out }
        Check "PowerShell-агент: p.md і new.md у коміті без CR (код $($r.Code))" ($r.Code -eq 0 -and -not (& $blob 'HEAD' 'p.md').Contains("`r") -and -not (& $blob 'HEAD' 'new.md').Contains("`r"))
        Check 'PowerShell-агент: дифф p.md — один доданий рядок, а не весь файл' ((Invoke-Git @('diff', '--numstat', 'HEAD~1', 'HEAD', '--', 'p.md')).Out.Trim() -match '^1\s+0\s+p\.md$')
        Check 'навмисний CRLF у репозиторії (k.csv) лишається CRLF' ((& $blob 'HEAD' 'k.csv').Contains("`r"))
        # Git Bash — оболонка, якою агент кличе git; шукаємо bash.exe вгору від git.exe (cmd\, bin\ чи mingw64\bin\ Git for Windows).
        $git = (Get-Command git).Source; $bash = $null
        for ($d = Split-Path -Parent $git; $d -and -not $bash; $d = Split-Path -Parent $d) {
            $bash = @('bin/bash.exe', 'usr/bin/bash.exe') | ForEach-Object { Join-Path $d $_ } | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
        }
        if ($bash) {
            $script = "printf 'a\r\nb\r\nc\r\nd\r\ne\r\n' > p.md; printf 'a\r\nb\r\nc\r\nd\r\n' > q.md; printf '\000\001\r\n\000\002' > b.dat; git add -A; git commit -q -m 'agent: Git Bash'"
            $r = Invoke-Native $bash @('-c', $script) $repo
            Check "Git Bash-агент: p.md і q.md у коміті без CR (код $($r.Code))" ($r.Code -eq 0 -and -not (& $blob 'HEAD' 'p.md').Contains("`r") -and -not (& $blob 'HEAD' 'q.md').Contains("`r"))
            Check 'Git Bash-агент: бінарний файл не чіпано (6 байтів)' ((Invoke-Git @('cat-file', '-s', 'HEAD:b.dat')).Out.Trim() -ceq '6')
        } else { "  Git Bash не знайдено — Git Bash-агента не перевірено" }
        $head = (Invoke-Git @('rev-parse', 'HEAD')).Out.Trim()
        [void](Close-TaskCopy @('--remotes', $head))
        Check 'середовище обгортки не забруднене налаштуванням git' (-not [Environment]::GetEnvironmentVariable('GIT_CONFIG_COUNT'))
        $keep = @{}; foreach ($k in 'GIT_CONFIG_COUNT', 'GIT_CONFIG_KEY_0', 'GIT_CONFIG_VALUE_0') { $keep[$k] = [Environment]::GetEnvironmentVariable($k) }
        try {
            $env:GIT_CONFIG_COUNT = '1'; $env:GIT_CONFIG_KEY_0 = 'a.b'; $env:GIT_CONFIG_VALUE_0 = 'c'
            $psi = New-StartInfo $git @('--version') ''
            Check 'чуже GIT_CONFIG_* середовища лишається, наше дописується після нього' ($psi.EnvironmentVariables['GIT_CONFIG_KEY_0'] -ceq 'a.b' -and $psi.EnvironmentVariables['GIT_CONFIG_COUNT'] -ceq '3' -and $psi.EnvironmentVariables['GIT_CONFIG_KEY_1'] -ceq 'core.autocrlf')
        } finally { foreach ($k in $keep.Keys) { [Environment]::SetEnvironmentVariable($k, $keep[$k]) } }
    }

    Scenario 'розбивка розміру: діти першого рівня й діти теки копій — тим самим обходом' {
        $p = Join-Path $tmp 'prof'
        foreach ($f in @(@('a/x.bin', 3000), @('b/x.bin', 500), @('runs/w/c1/x.bin', 7000), @('runs/w/c1/sub/y.bin', 100), @('runs/w/c2/x.bin', 200), @('root.bin', 10))) {
            $full = Join-Path $p $f[0]; [void][IO.Directory]::CreateDirectory((Split-Path -Parent $full))
            [IO.File]::WriteAllBytes($full, (New-Object byte[] $f[1]))
        }
        $r = Measure-DirBytes $p (Join-Path $p 'runs/w') -Breakdown
        Check "сума профілю $($r.Bytes) (10810), недоступних 0" ($r.Bytes -eq 10810 -and $r.Skipped -eq 0)
        Check "першого рівня за спаданням, усе з вагою (файли в корені — _файли_): $(ConvertTo-SizeList $r.Top)" ((ConvertTo-SizeList $r.Top) -ceq 'runs=7300;a=3000;b=500;_файли_=10')
        Check "копії за спаданням: $(ConvertTo-SizeList $r.Under)" ((ConvertTo-SizeList $r.Under) -ceq 'c1=7100;c2=200')
        Check 'без -Breakdown обхід не збирає розбивки (Bytes/Skipped, як було)' ((Measure-DirBytes $p).Bytes -eq 10810 -and @((Measure-DirBytes $p).Top).Count -eq 0)
        $back = @(ConvertFrom-SizeList (ConvertTo-SizeList @([pscustomobject]@{ Name = 'a|b`<c>'; Bytes = 5 }, [pscustomobject]@{ Name = 'Дані'; Bytes = 7 })))
        Check 'назви без службових знаків, кирилиця лишається; чужий рядок відкидається' ($back.Count -eq 2 -and $back[0].Name -ceq 'a_b__c_' -and $back[1].Name -ceq 'Дані' -and @(ConvertFrom-SizeList 'x|y=1;ok=2;bad=-1;z=').Count -eq 1)
    }
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^kopiia-test-[0-9a-f]{32}$') {
        $w = Join-Path $tmp 'w/run-1/repo'
        if ($realRepo -and (Test-Path -LiteralPath $w)) { try { [void](Invoke-Native $GitExe @('-C', $realRepo, 'worktree', 'remove', '-f', '-f', $w) '' 2) } catch { $null = $_ } }
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $tmp) { [void](Reset-TreeAcl $tmp); Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }
    }
}
exit [int]($bad -gt 0)
