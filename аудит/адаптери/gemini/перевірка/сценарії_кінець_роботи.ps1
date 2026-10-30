#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir, [switch]$Before)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('end-test-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0; $lock = $null
function Check([string]$Name, [bool]$Ok) {
    <# Провал мірила визначає код завершення стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutboxDir "$tmp/out"
    $OutDir = "$tmp/gem-out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/seen", "$WorkDir/state", $OutboxDir, $OutDir, "$tmp/claude-run/slots", "$tmp/claude-run/state")) {
        [void][IO.Directory]::CreateDirectory($dir)
    }
    $script:Main = 'a' * 40; $script:Pulls = @(); $script:Markers = @(); $script:Logs = @()
    function Get-RefSha { <# Повертає сталий main синтетичного стенда. #> $script:Main }
    function Invoke-Git {
        <# Відтворює лише потрібні відповіді Git без зовнішніх процесів. #>
        param([string[]]$GitArgs, [switch]$AllowFail)
        $out = ''
        if ($GitArgs[0] -ceq 'cat-file' -and $GitArgs[-1] -like '*ланцюг.json') {
            $out = '{"v":1,"codex":"gpt-review","agy":"gemini-review","claude":"cc-claude-review"}'
        }
        [pscustomobject]@{Code=0;Out=$out;Err=''}
    }
    function Complete-EngineDrafts { <# Виключає створення зовнішніх PR зі стенда. #> }
    function Get-ChainPulls { <# Дає поточний знімок синтетичних PR. #> $script:Pulls }
    function Invoke-ChainApi([string]$Path) {
        <# Дає свіжу дату синтетичної голови для початкового знімка. #>
        [pscustomobject]@{sha=($Path -split '/')[-1];commit=@{committer=@{date=[datetimeoffset]::UtcNow.AddMinutes(-1).ToString('o')}}}
    }
    function Test-LiveModels { <# Лишає GPU-прогони поза пробою автоперевірки. #> $false }
    function Test-ChainCodePull { <# Позначає синтетичні PR як зміни коду. #> $true }
    function Test-ReviewedMerge { <# Виключає окремий випадок чистого злиття main. #> $false }
    function Get-ReviewDiff { <# Повертає сталий diff для синтетичних голів. #> 'стенд-diff' }
    function Add-ChainMarker($Slug, $Model, $Main, [switch]$Gpu) { <# Рахує позначки без зовнішнього push. #> $script:Markers += [string]$Slug }
    function Write-WrapperLog([string]$Text) { <# Зберігає журнал і показує несподівані збої. #> $script:Logs += $Text; if ($Text -like "*CHAIN_*") { Write-Host $Text } }
    function Pull([int]$N, [string]$Branch, [string]$Head) {
        <# Довірений PR-чернетка з трьома послідовними головами. #>
        [pscustomobject]@{number=$N;title='Код';draft=$true;created_at=[datetimeoffset]::UtcNow.ToString('o');user=@{login='mightyrochy'};
            head=@{ref=$Branch;sha=$Head;repo=@{full_name=$GitHubRepo}};base=@{ref='main';repo=@{full_name=$GitHubRepo}}}
    }
    function Tick([string]$Head, [string]$Branch='claude/5.3-повний-обхід') {
        <# Один справжній прохід ланцюга з незмінним хмарним PR поруч. #>
        $script:Pulls = @((Pull 2386 $Branch $Head), (Pull 2400 'codex/хмара' ('e' * 40)))
        Invoke-WrapperChain
    }
    function CountReviews([string]$N) { <# Рахує всі перевірки одного PR. #> @($script:Markers | Where-Object { $_ -like "автоперевірка-$N-*" }).Count }
    $slug = '5.3-повний-обхід-каталогу'
    $marker = "gemini-queue/$slug/cc-claude-sonnet-5-5-medium/8/p1"
    $info = "$tmp/claude-run/slots/claude-1.json"
    Write-FileAtomic $info ((@{slug=$slug;marker=$marker}) | ConvertTo-Json -Compress)
    Write-FileAtomic ("$tmp/claude-run/state/branch-" + (Get-Sha256Hex $slug) + '.txt') 'claude/5.3-повний-обхід'
    $lock = [IO.File]::Open("$tmp/claude-run/slots/claude-1.lock", 'OpenOrCreate', 'ReadWrite', 'None')
    foreach ($head in @(('b'*40), ('c'*40), ('d'*40))) { Tick $head }
    $state = ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/chain.json"))
    Check 'активна голова лишається придатною в heads' ($state.heads.'2386'.sha -ceq ('d'*40) -and $state.heads.'2386'.eligible)
    Check "проміжних позначок: $(CountReviews 2386)" ((CountReviews 2386) -eq $(if ($Before) { 3 } else { 0 }))
    Check 'хмарний PR без смуги: рівно 1' ((CountReviews 2400) -eq 1)
    # Complete-Task записує кінець до звільнення слота; SHA3 вже є головою PR.
    Write-FileAtomic "$WorkDir/state/done.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО claude/5.3-повний-обхід $('d'*40) МОДЕЛЬ cc-claude-sonnet-5-5-medium"}) | ConvertTo-Json)
    $lock.Dispose(); $lock = $null
    Tick ('d'*40); Tick ('d'*40)
    Check "три голови й ГОТОВО: перевірок $(CountReviews 2386) (ДО 3 → ПІСЛЯ 1)" ((CountReviews 2386) -eq $(if ($Before) { 3 } else { 1 }))
    Check 'перевірка кінцевої SHA3' (@($script:Markers | Where-Object { $_ -ceq "автоперевірка-2386-$('d'*40)" }).Count -eq 1)
    Check 'PR без смуги: ДО 1 → ПІСЛЯ 1' ((CountReviews 2400) -eq 1)
    if (-not $Before) {
        Check 'пропуск і хмарний шлях видимі в журналі' (@($script:Logs | Where-Object { $_ -like '*смуга ще пише*' }).Count -eq 3 -and
            @($script:Logs | Where-Object { $_ -like '*#2400*активної смуги нема*' }).Count -gt 0)
        Check 'старий JSON слота з вільним замком не блокує' (-not (Get-ChainBranchWork 'claude/5.3-повний-обхід'))
        $lock = [IO.File]::Open("$tmp/claude-run/slots/claude-1.lock", 'Open', 'ReadWrite', 'None')
        # Перша спроба ще не має branch-<hash>: гілка вже видима в HEAD її робочої копії.
        $copy = "$tmp/claude-copy"; [void][IO.Directory]::CreateDirectory("$copy/repo/.git")
        Write-FileAtomic "$copy/repo/.git/HEAD" 'ref: refs/heads/claude/нова-гілка'
        Write-FileAtomic $info ((@{slug=$slug;marker=$marker;copy=$copy}) | ConvertTo-Json -Compress)
        Check 'HEAD копії першої спроби повʼязує іншу гілку' ((Get-ChainBranchWork 'claude/нова-гілка') -ceq $marker)
        # Worktree має .git-файл з gitdir, а не теку.
        Move-Item -LiteralPath "$copy/repo/.git" -Destination "$copy/meta"
        Write-FileAtomic "$copy/repo/.git" 'gitdir: ../meta'
        Check 'HEAD worktree читається через gitdir' ((Get-ChainBranchWork 'claude/нова-гілка') -ceq $marker)
        $lock.Dispose(); $lock = $null
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir 'gemini_run.ps1'), [ref]$tokens, [ref]$errors)
        $heartbeat = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq 'Write-Heartbeat' }, $true)
        Invoke-Expression $heartbeat.Extent.Text
        function Get-UtcStamp($Date) { <# Форматує час справжнього Write-Heartbeat. #> $Date.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
        [void][IO.Directory]::CreateDirectory("$GeminiRunsDir/slots")
        foreach ($lane in @('codex','agy')) {
            $gm = "gemini-queue/спільний-$lane/gpt-test/2/p1"
            $head = $(if ($lane -ceq 'codex') { 'f'*40 } else { '1'*40 })
            Write-FileAtomic "$GeminiRunsDir/slots/$lane-1.json" ((@{slot="$lane-1";lane=$lane;slug="спільний-$lane";marker=$gm}) | ConvertTo-Json)
            $lock = [IO.File]::Open("$GeminiRunsDir/slots/$lane-1.lock", 'OpenOrCreate', 'ReadWrite', 'None')
            Write-Heartbeat 'TEST_ISOLATION'
            $hb = ConvertFrom-Json ([IO.File]::ReadAllText("$OutDir/heartbeat.json"))
            Check "${lane}: heartbeat ізоляції не має lanes" ($null -eq $hb.PSObject.Properties['lanes'])
            Check "${lane}: зайнятий слот повʼязує гілку без heartbeat.lanes" ((Get-ChainBranchWork "gemini/спільний-$lane") -ceq $gm)
            $n = CountReviews 2386
            Tick $head "gemini/спільний-$lane"
            Check "${lane}: активна голова — 0 перевірок" ((CountReviews 2386) -eq $n)
            Write-FileAtomic "$OutDir/heartbeat.json" ((@{lanes=@(@{lane=$lane;busy=@(@{marker=$gm})})}) | ConvertTo-Json -Depth 6)
            Write-FileAtomic "$WorkDir/state/done-$lane.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО gemini/спільний-$lane $head МОДЕЛЬ gpt-test"}) | ConvertTo-Json)
            $lock.Dispose(); $lock = $null
            Check "${lane}: старий busy з вільним замком не блокує" (-not (Get-ChainBranchWork "gemini/спільний-$lane"))
            Tick $head "gemini/спільний-$lane"; Tick $head "gemini/спільний-$lane"
            Check "${lane}: після ГОТОВО зі старим busy — 1 перевірка" ((CountReviews 2386) -eq ($n+1))
            $blockedHead = $(if ($lane -ceq 'codex') { '2'*40 } else { '3'*40 })
            $lock = [IO.File]::Open("$GeminiRunsDir/slots/$lane-1.lock", 'Open', 'ReadWrite', 'None')
            Tick $blockedHead "gemini/спільний-$lane"
            Check "${lane}: наступна активна голова — 0 перевірок" ((CountReviews 2386) -eq ($n+1))
            Write-FileAtomic "$WorkDir/state/blocked-$lane.json" ((@{line="GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/спільний-$lane BLOCKED"}) | ConvertTo-Json)
            $lock.Dispose(); $lock = $null
            Tick $blockedHead "gemini/спільний-$lane"; Tick $blockedHead "gemini/спільний-$lane"
            Check "${lane}: після ЗАБЛОКОВАНО — 1 перевірка" ((CountReviews 2386) -eq ($n+2))
        }
    }
} finally {
    if ($null -ne $lock) { $lock.Dispose() }
    if (-not ([IO.Path]::GetFullPath($tmp)).StartsWith([IO.Path]::GetFullPath([IO.Path]::GetTempPath()), [StringComparison]::OrdinalIgnoreCase)) { throw 'Тека стенда поза TEMP' }
    Remove-Item -LiteralPath $tmp -Recurse -Force
}
if ($bad) { "ПІДСУМОК: ✗ $bad"; exit 1 }
exit 0
