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
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
finally {
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmp) -cmatch '^kopiia-test-[0-9a-f]{32}$') {
        $w = Join-Path $tmp 'w/run-1/repo'
        if ($realRepo -and (Test-Path -LiteralPath $w)) { try { [void](Invoke-Native $GitExe @('-C', $realRepo, 'worktree', 'remove', '-f', '-f', $w) '' 2) } catch { $null = $_ } }
        Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}
exit [int]($bad -gt 0)
