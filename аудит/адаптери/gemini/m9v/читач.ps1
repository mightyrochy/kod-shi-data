#Requires -Version 5.1
<# Спільне для кроків m9v (підключається крапкою): читач входу задачі й перевірка, що самооновлення встановлено.
Читач — малий файл на місці входу задачі: бере з `<корінь>\active.txt` версію й запускає її файл із тими самими
аргументами. Текст читача — лише тут: його ставлять 0_власник.ps1, 1_адмін.ps1 і 3_самооновлення.ps1. Нічого не виконує
при завантаженні. #>

function Get-ReaderText([string]$Root, [string]$Name) {
    <# Текст читача входу $Name. #>
    $text = @'
#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
$root = '__ROOT__'
$sha = [IO.File]::ReadAllText((Join-Path $root 'active.txt')).Trim()
if ($sha -cnotmatch '^[0-9a-f]{40}$') { throw 'UPDATE_POINTER' }
$file = Join-Path (Join-Path (Join-Path $root 'versions') $sha) '__NAME__'
& $file @args
exit $LASTEXITCODE
'@
    $text.Replace('__ROOT__', $Root.Replace("'", "''")).Replace('__NAME__', $Name)
}

function Test-SelfUpdate([string]$Root = 'C:\ProgramData\gemini-wrapper') {
    <# $true — самооновлення встановлено (`selfupdate.ready`) і активна версія має файл кожного з чотирьох входів.

    Без `selfupdate.ready` — мовчки $false: перша установка, входи — повні файли. З ним, але з битим указівником чи без
    файла входу у версії — $false з попередженням: читач на такій версії впав би, а повний файл хоч працює. #>
    if (-not (Test-Path -LiteralPath (Join-Path $Root 'selfupdate.ready'))) { return $false }
    $pointer = Join-Path $Root 'active.txt'
    $sha = if (Test-Path -LiteralPath $pointer) { [IO.File]::ReadAllText($pointer).Trim() } else { '' }
    $missing = @('gemini_run.ps1', 'gemini_publish.ps1', 'gemini_watch.ps1', 'claude_run.ps1')
    if ($sha -cmatch '^[0-9a-f]{40}$') {
        $dir = Join-Path (Join-Path $Root 'versions') $sha
        $missing = @($missing | Where-Object { -not (Test-Path -LiteralPath (Join-Path $dir $_) -PathType Leaf) })
    }
    if ($missing.Count) {
        Write-Host "УВАГА: selfupdate.ready є, але активна версія '$sha' не має входів: $($missing -join ', '). Входи лишено повними файлами; після виправлення версії запусти 3_самооновлення.ps1." -ForegroundColor Yellow
        return $false
    }
    $true
}

function Install-EntryReader([string]$Dir, [string]$Name, [string]$Root = 'C:\ProgramData\gemini-wrapper') {
    <# Кладе в $Dir читач входу $Name. Попередній файл при першій заміні зберігається як `.before-update`; повторний
    виклик із тим самим текстом нічого не пише. #>
    [void][IO.Directory]::CreateDirectory($Dir)
    $target = Join-Path $Dir $Name
    $text = Get-ReaderText $Root $Name
    if (Test-Path -LiteralPath $target) {
        if ([IO.File]::ReadAllText($target) -ceq $text) { return }
        if (-not (Test-Path -LiteralPath ($target + '.before-update'))) { Copy-Item -LiteralPath $target -Destination ($target + '.before-update') }
    }
    [IO.File]::WriteAllText($target, $text, (New-Object Text.UTF8Encoding($false)))
}
