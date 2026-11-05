#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir, [switch]$Before, [switch]$AccessBefore)
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

    $slug = 'гонка-кінця'
    $branch = "gemini/$slug"
    $marker = "gemini-queue/$slug/gpt-test/1/p1"
    [void][IO.Directory]::CreateDirectory("$GeminiRunsDir/slots")
    Write-FileAtomic "$GeminiRunsDir/slots/codex-1.json" ((@{slug=$slug;marker=$marker}) | ConvertTo-Json)
    $script:WorkerLock = [IO.File]::Open("$GeminiRunsDir/slots/codex-1.lock", 'OpenOrCreate', 'ReadWrite', 'None')
    $script:FinishOnFetch = $true
    function Get-ChainPulls {
        <# Знімок PR зроблено на SHA1; до повернення відповіді worker опублікував SHA3 і закінчив. #>
        if ($script:FinishOnFetch) {
            $script:FinishOnFetch = $false
            Write-FileAtomic "$WorkDir/state/done-race.json" ((@{line="GEMINI ОБГОРТКА: ГОТОВО $branch $('d'*40) МОДЕЛЬ gpt-test"}) | ConvertTo-Json)
            $script:WorkerLock.Dispose()
            $script:WorkerLock = $null
            Write-Host "ПОДІЯ: після знімка PR SHA1 worker опублікував ГОТОВО SHA3 і звільнив слот"
        }
        $script:Pulls
    }
    Tick ('b'*40) $branch
    Tick ('d'*40) $branch
    $reviews = @($script:Markers | Where-Object { $_ -like 'автоперевірка-2386-*' })
    Write-Host "ФАКТ: одна робота, перевірок $($reviews.Count)"
    $reviews | ForEach-Object { Write-Host "ПОЗНАЧКА: $_" }
    Check 'після кінця роботи є лише перевірка кінцевої SHA3' ($reviews.Count -eq 1 -and $reviews[0] -ceq "автоперевірка-2386-$('d'*40)")
} finally {
    if ($null -ne $script:WorkerLock) { $script:WorkerLock.Dispose() }
    $full = [IO.Path]::GetFullPath($tmp)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\','/') + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($parent, [StringComparison]::OrdinalIgnoreCase)) { throw 'Тека проби поза TEMP' }
    Remove-Item -LiteralPath $tmp -Recurse -Force
}
if ($bad) { exit 1 }
exit 0
