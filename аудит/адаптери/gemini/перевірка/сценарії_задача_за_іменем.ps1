#Requires -Version 5.1
<# Стенд «задача процесів за іменем»: процес наряду (окремий powershell з queue_lanes.ps1) через Start-Tree запускає корінь,
корінь — дочірній процес, той — онука й виходить, тож онук відірваний (батька нема, taskkill /T за батьком його не бачить).
Зупиняє цей процес, у чиєму $script:TreeJobs задачі нема, — як новий планувальник після самооновлення (Stop-CancelledRuns)
чи наступний прохід claude-run після смерті процесу наряду (Resume-Interrupted). Лише Windows: задача процесів — Windows. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('treejob-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
$script:Logged = New-Object System.Collections.ArrayList
$script:Pids = New-Object System.Collections.Generic.List[int]
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
function Write-Log([string]$Text) { [void]$script:Logged.Add($Text) }

# Вузол дерева: root — запускає child і живе; child — запускає grand, пише його pid і виходить; grand — спить.
[IO.File]::WriteAllText((Join-Path $tmp 'node.ps1'), @'
param([string]$Role, [string]$Dir, [string]$Tag)
function Spawn([string]$Next) {
    $psi = New-Object Diagnostics.ProcessStartInfo ((Get-Process -Id $PID).Path), ("-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Role $Next -Dir `"$Dir`" -Tag $Tag")
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    [Diagnostics.Process]::Start($psi)
}
if ($Role -eq 'root') { $c = Spawn 'child'; $c.WaitForExit(); Start-Sleep -Seconds 600 }
elseif ($Role -eq 'child') { $g = Spawn 'grand'; [IO.File]::WriteAllText("$Dir\$Tag.grand", [string]$g.Id) }
else { Start-Sleep -Seconds 600 }
'@)
# Процес наряду: справжні New-StartInfo і Start-Tree обгортки; дескриптор задачі — лише в ньому (і копія в корені).
[IO.File]::WriteAllText((Join-Path $tmp 'worker.ps1'), @'
param([string]$Src, [string]$Dir, [string]$Tag)
function Write-Log([string]$Text) { [IO.File]::AppendAllText("$Dir\$Tag.log", $Text + "`n") }
. (Join-Path $Src 'queue_lanes.ps1')
$p = Start-Tree (New-StartInfo (Get-Process -Id $PID).Path @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "$Dir\node.ps1", '-Role', 'root', '-Dir', $Dir, '-Tag', $Tag) '' -NoRedirect)
[IO.File]::WriteAllText("$Dir\$Tag.root", [string]$p.Id)
Start-Sleep -Seconds 600
'@)

function Test-Alive([int]$Id) { try { $null = Get-Process -Id $Id -ErrorAction Stop; $true } catch { $false } }
function Wait-Until([scriptblock]$Cond) { for ($i = 0; $i -lt 300 -and -not (& $Cond); $i++) { Start-Sleep -Milliseconds 200 }; [bool](& $Cond) }
function Read-Pid([string]$Path) { if (Test-Path -LiteralPath $Path) { [int]([IO.File]::ReadAllText($Path).Trim()) } else { 0 } }
function Start-Lane([string]$Tag) {
    <# Процес наряду, як Start-Worker планувальника (без задачі); чекає кореня й відірваного онука. #>
    $psi = New-Object Diagnostics.ProcessStartInfo ((Get-Process -Id $PID).Path), ("-NoProfile -ExecutionPolicy Bypass -File `"$tmp\worker.ps1`" -Src `"$SourceDir`" -Dir `"$tmp`" -Tag $Tag")
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $w = [Diagnostics.Process]::Start($psi); $script:Pids.Add($w.Id)
    $ok = Wait-Until { (Read-Pid "$tmp\$Tag.root") -gt 0 -and (Read-Pid "$tmp\$Tag.grand") -gt 0 }
    $r = [pscustomobject]@{ Worker = $w; Root = (Read-Pid "$tmp\$Tag.root"); Grand = (Read-Pid "$tmp\$Tag.grand") }
    foreach ($i in @($r.Root, $r.Grand)) { if ($i -gt 0) { $script:Pids.Add($i) } }
    if (-not $ok) { throw "дерево $Tag не піднялося: $(try { [IO.File]::ReadAllText("$tmp\$Tag.log") } catch { 'журналу нема' })" }
    $parent = [int](Get-CimInstance Win32_Process -Filter "ProcessId=$($r.Grand)").ParentProcessId
    $detached = Wait-Until { -not (Test-Alive $parent) }
    Check "$Tag відірваний онук: батько $parent вийшов, онук $($r.Grand) живий" ($detached -and (Test-Alive $r.Grand))
    $r
}

try {
    . (Join-Path $SourceDir 'queue_lanes.ps1')

    Scenario 'а ДО' {
        # Те, що робив Stop-Tree для чужого процесу до задачі за іменем: taskkill дерева за батьком, своєї задачі нема.
        $t = Start-Lane 'a'
        & taskkill.exe /PID $t.Worker.Id /T /F *> $null
        $gone = Wait-Until { -not (Test-Alive $t.Worker.Id) -and -not (Test-Alive $t.Root) }
        Check "а ДО: taskkill /T процесу наряду зупинив його й корінь, відірваний онук живий" ($gone -and (Test-Alive $t.Grand))
        Stop-Process -Id $t.Grand -Force -ErrorAction SilentlyContinue
    }

    Scenario 'б зняття' {
        # Stop-CancelledRuns: новий планувальник зупиняє процес наряду попереднього за pid з <слот>.json.
        $t = Start-Lane 'b'
        $script:Logged.Clear()
        Stop-Tree (Get-Process -Id $t.Worker.Id)
        $gone = Wait-Until { -not (Test-Alive $t.Worker.Id) -and -not (Test-Alive $t.Root) -and -not (Test-Alive $t.Grand) }
        Check "б ПІСЛЯ: Stop-Tree процесу наряду з іншого процесу зупинив і відірваного онука $($t.Grand): $($script:Logged -join ' | ')" ($gone -and @($script:Logged -match "^лишки дерева $($t.Root) зупинено: .*\b$($t.Grand)\b").Count -eq 1)
        Check 'б дескрипторів задач у процесі, що зупиняв, не лишилось' ($script:TreeJobs.Count -eq 0)
    }

    Scenario 'в перерваний' {
        # Resume-Interrupted: процес наряду вже мертвий (тримав задачу), корінь живий — задачу тримає копія в корені.
        $t = Start-Lane 'c'
        & taskkill.exe /PID $t.Worker.Id /F *> $null
        $dead = Wait-Until { -not (Test-Alive $t.Worker.Id) }
        Check 'в процес наряду зупинено без дерева: корінь і онук живі' ($dead -and (Test-Alive $t.Root) -and (Test-Alive $t.Grand))
        $script:Logged.Clear()
        Stop-Tree (Get-Process -Id $t.Root)
        $gone = Wait-Until { -not (Test-Alive $t.Root) -and -not (Test-Alive $t.Grand) }
        Check "в ПІСЛЯ: Stop-Tree кореня після смерті творця задачі зупинив відірваного онука $($t.Grand): $($script:Logged -join ' | ')" $gone
    }
} finally {
    # Лише живі powershell стенда: pid процесу, що вже вийшов, міг дістатися іншому процесу раннера.
    foreach ($i in $script:Pids) { Get-Process -Id $i -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -eq 'powershell' } | Stop-Process -Force -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
if ($bad -gt 0) { exit 1 }
exit 0
