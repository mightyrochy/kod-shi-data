#Requires -Version 5.1
<# Атомарний запис спільних файлів (28.11, claude-run.log 16:19:16): публікатор писав `local-lines.json` як «видалити старий →
перенести .part», між двома кроками шляху без файла не було, а claude-run читав його між Test-Path і ReadAllText і падав
на «Could not find file». Тепер Write-FileAtomic одна (wrapper_health.ps1), заміна — MoveFileEx (Move-FileOver), читання — Read-FileText.
Стенд: перезапис наявного файла під паралельним читачем у циклі (окремі потоки) ні разу не бачить «нема файла» й не бачить
половини запису; читач Read-FileText не отримує жодного винятку; зайнятий файл читається з повтором; нема файла — одразу.
Контроль на старій заміні лише друкується: чи побачить її читач збій, залежить від планувальника ОС. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('atom-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$script:Utf8 = New-Object Text.UTF8Encoding($false)
$bad = 0
$health = Join-Path $SourceDir 'wrapper_health.ps1'
function Kind($E) { if ($E.InnerException) { $E.InnerException.GetType().Name } else { $E.GetType().Name } }
function Check([string]$Name, [bool]$Ok) { if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ } }
# Читач в окремому потоці: у циклі читає файл і рахує, що побачив. Запис — 4096 однакових літер; інша довжина чи суміш
# літер — половина запису.
$readerCode = @'
param($Path, $Sync, $Health, $Mode)
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
. $Health
while (-not $Sync.stop) {
    try {
        $t = if ($Mode -eq 'raw') { [System.IO.File]::ReadAllText($Path, $script:Utf8) } else { Read-FileText $Path }
        $Sync.reads++
        if ($t.Length -ne 4096 -or $t.Replace([string]$t[0], '').Length -ne 0) { $Sync.torn++ }
    }
    catch {
        $e = $_.Exception; if ($e.InnerException) { $e = $e.InnerException }
        if ($e -is [System.IO.FileNotFoundException] -or $e -is [System.IO.DirectoryNotFoundException]) { $Sync.missing++ }
        elseif ($e -is [System.IO.IOException]) { $Sync.busy++ }
        else { $Sync.other++ }
    }
}
'@
$writerCode = @'
param($Path, $Sync, $Health, $Count, $Seed)
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
. $Health
for ($i = 0; $i -lt $Count; $i++) {
    try { Write-FileAtomic $Path (([string][char](97 + (($i + $Seed) % 26))) * 4096); $Sync.writes++ } catch { $Sync.errors++ }
}
'@
function New-Sync { [hashtable]::Synchronized(@{ stop = $false; reads = 0; torn = 0; missing = 0; busy = 0; other = 0; writes = 0; errors = 0 }) }
function Start-Part([string]$Code, [object[]]$Arguments) {
    $ps = [powershell]::Create(); [void]$ps.AddScript($Code)
    foreach ($a in $Arguments) { [void]$ps.AddArgument($a) }
    [pscustomobject]@{ Ps = $ps; Handle = $ps.BeginInvoke() }
}
function Stop-Part($Part) { $Part.Ps.EndInvoke($Part.Handle); $Part.Ps.Dispose() }
function Write-Old([string]$Path, [string]$Text) {
    $p = $Path + '.part'
    [System.IO.File]::WriteAllText($p, $Text, $script:Utf8)
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Force }
    Move-Item -LiteralPath $p -Destination $Path
}
try {
    . $health
    $copies = @(Get-ChildItem -LiteralPath $SourceDir -Filter '*.ps1' -File | Where-Object { (Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8) -match '(?m)^function Write-FileAtomic\b' })
    Check 'одна Write-FileAtomic на всю обгортку — у wrapper_health.ps1' ($copies.Count -eq 1 -and $copies[0].Name -ceq 'wrapper_health.ps1')
    $loaders = @('gemini_publish.ps1', 'gemini_watch.ps1', 'queue_lanes.ps1') | Where-Object { (Get-Content -LiteralPath (Join-Path $SourceDir $_) -Raw -Encoding UTF8) -match "wrapper_health\.ps1'\)" }
    Check 'публікатор, спостерігач і queue_lanes підвантажують wrapper_health.ps1' (@($loaders).Count -eq 3)

    # 1. Перезапис наявного файла: читач, що крутиться в циклі, шлях без файла не бачить.
    $path = Join-Path $tmp 'local-lines.json'
    Write-FileAtomic $path ('a' * 4096)
    Check 'новий файл створено, `.part` не лишилось' ((Get-Content -LiteralPath $path -Raw) -ceq ('a' * 4096) -and @(Get-ChildItem -LiteralPath $tmp -Filter '*.part').Count -eq 0)
    $raw = New-Sync; $safe = New-Sync; $w = New-Sync
    $r1 = Start-Part $readerCode @($path, $raw, $health, 'raw')
    $r2 = Start-Part $readerCode @($path, $safe, $health, 'safe')
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $wr = Start-Part $writerCode @($path, $w, $health, 300, 0)
    Stop-Part $wr
    $raw.stop = $true; $safe.stop = $true; Stop-Part $r1; Stop-Part $r2
    "  300 перезаписів за $([int]$sw.Elapsed.TotalSeconds) с; сирий читач: читань $($raw.reads), зайнято $($raw.busy); Read-FileText: читань $($safe.reads)"
    Check 'запис поверх наявного: шлях ні разу не лишився без файла (сирий читач: нема файла = 0)' ($w.writes -eq 300 -and $w.errors -eq 0 -and $raw.missing -eq 0 -and $safe.missing -eq 0)
    Check 'читачі справді працювали під час записів (понад 100 читань кожен)' ($raw.reads -gt 100 -and $safe.reads -gt 100)
    Check 'половини запису ніхто не бачив' ($raw.torn -eq 0 -and $safe.torn -eq 0)
    Check 'Read-FileText під записами не дав жодного винятку' ($safe.busy -eq 0 -and $safe.other -eq 0 -and $safe.missing -eq 0)
    Check 'інших винятків сирий читач не мав (лише зайнятість, яку Read-FileText повторює)' ($raw.other -eq 0)

    # 2. Кілька писарів одного файла водночас: ні винятку, ні половини, ні осиротілих `.part`.
    $m = New-Sync; $rd = Start-Part $readerCode @($path, $m, $health, 'raw')
    $ws = @(1..3 | ForEach-Object { $s = New-Sync; [pscustomobject]@{ S = $s; P = (Start-Part $writerCode @($path, $s, $health, 100, $_)) } })
    foreach ($x in $ws) { Stop-Part $x.P }
    $m.stop = $true; Stop-Part $rd
    Check 'три писарі одного файла: 300 записів без винятку' ((@($ws | ForEach-Object { $_.S.writes } | Measure-Object -Sum).Sum -eq 300) -and (@($ws | ForEach-Object { $_.S.errors } | Measure-Object -Sum).Sum -eq 0))
    Check 'три писарі: читач не бачив ні відсутності файла, ні половини' ($m.missing -eq 0 -and $m.torn -eq 0)
    Check 'три писарі: тимчасових `.part` не лишилось' (@(Get-ChildItem -LiteralPath $tmp -Filter '*.part').Count -eq 0)

    # 3. Читання: зайнятий файл — з повтором, нема файла — одразу.
    $held = Join-Path $tmp 'held.txt'; [IO.File]::WriteAllText($held, 'готово', $script:Utf8)
    $fs = New-Object IO.FileStream($held, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    $release = Start-Part '$s = $args[0]; Start-Sleep -Milliseconds 300; $s.Dispose()' @($fs)
    $raw1 = ''; try { [void][IO.File]::ReadAllText($held, $script:Utf8) } catch { $raw1 = Kind $_.Exception }
    $got = ''; try { $got = Read-FileText $held } catch { $got = 'ВИНЯТОК ' + (Kind $_.Exception) + ' ' + $_.Exception.Message }
    Stop-Part $release
    Check 'зайнятий файл: ReadAllText падає IOException, Read-FileText дочекався й прочитав' ($raw1 -ceq 'IOException' -and $got -ceq 'готово')
    $sw = [Diagnostics.Stopwatch]::StartNew(); $miss = ''
    try { [void](Read-FileText (Join-Path $tmp 'нема.json')) } catch { $miss = Kind $_.Exception }
    Check 'нема файла: FileNotFoundException одразу, без повторів' ($miss -ceq 'FileNotFoundException' -and $sw.ElapsedMilliseconds -lt ($script:FileRetries * $script:FileRetryMs))

    # Контроль: стара заміна (видалити → перенести) під тим самим читачем. Лише друк.
    $old = Join-Path $tmp 'old.json'; Write-Old $old ('a' * 4096)
    $c = New-Sync; $rc = Start-Part $readerCode @($old, $c, $health, 'raw')
    $oldFail = 0
    for ($i = 0; $i -lt 300; $i++) { try { Write-Old $old (([string][char](97 + ($i % 26))) * 4096) } catch { $oldFail++ } }
    $c.stop = $true; Stop-Part $rc
    "  контроль, стара заміна: читач бачив «нема файла» $($c.missing) разів із $($c.reads) читань, збоїв запису $oldFail (на MoveFileEx — «нема файла» 0)"
} catch { "✗ збій сценарію: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
"ПІДСУМОК: ✗ $bad"
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit ([int]($bad -gt 0))
