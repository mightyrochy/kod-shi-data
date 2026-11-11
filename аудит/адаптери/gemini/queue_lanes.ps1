#Requires -Version 5.1
<#
.SYNOPSIS
Спільне для двох планувальників ноутбука — `gemini_run.ps1` (під `gemini`: смуги Codex і `agy`) і `claude_run.ps1` (під
власником: смуга Claude Code): позначки черги з пріоритетом і строком, смуги й слоти, межі з файла даних, атомарне узяття
позначки, чекання скидання квоти, замок GPU, копія задачі без тек-архівів і окремий процес на наряд.

.DESCRIPTION
Підвантажується крапкою (`. queue_lanes.ps1`) після блоку параметрів скрипта; власних параметрів нема. Читає змінні
скрипта: $RepoDir, $GitExe, $LaneDir, $script:NoHooks, $script:StateDir, $script:SlotDir, $script:SelfPath, $script:Bound,
і функцію журналу Write-Log. Два облікові записи розведено жорстко, тож планувальників два; спільні між ними лише ворота й
сесія GPU та бюджет перевірок PR (тека $LaneDir — `C:\Users\Public\gemini\lanes`, де пишуть і INTERACTIVE, і BATCH) і рядок стану ноутбука.

Позначка: `gemini-queue/<наряд>/<модель>/<спроба>[/<умови>]`; умови — до трьох лексем через `-` у будь-якому порядку:
`p<0-9>` — пріоритет (0 — найвищий; без лексеми — 5), `d<РРРРММДДГГхх>` — строк у UTC, `gpu` — наряд займає відеокарту.
Порядок узяття: пріоритет, строк (без строку — останні), час першої появи позначки на ноутбуці, час коміту, назва.
Смуга — за моделлю: `cc-…` — Claude, `gpt-…` — Codex, решта — `agy`.
#>

. (Join-Path $PSScriptRoot 'wrapper_health.ps1')

$script:QueuePrefix = 'refs/remotes/origin/gemini-queue/'
$script:TaskDir = 'аудит/наряди/'
$script:SlugPattern = '^[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}\z'
$script:SlugCore = $script:SlugPattern -replace '^\^|\\z$', ''
$script:ModelPattern = '^[a-z0-9][a-z0-9.-]{1,63}$'
$script:CondPattern = '^(?:p[0-9]|d20[0-9]{10}|gpu)(?:-(?:p[0-9]|d20[0-9]{10}|gpu)){0,2}$'
$script:LanesPath = 'аудит/адаптери/gemini/смуги.json'
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:OnWindows = ($PSVersionTable.PSEdition -ne 'Core') -or [bool](Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue)
$script:TreeJobs = @{}  # pid процесу Start-Tree → його задача Windows
$script:GpuLease = $null  # замок GPU-оренди процесу наряду (Start-GpuModels → Exit-GpuLease)
# Тека версії цього процесу: після самооновлення — `<корінь>\versions\<SHA40>`, поряд із коренем — `active.txt`.
$script:VersionDir = $PSScriptRoot

# Кількість слотів задає смуги.json; 64 — захист від помилки в даних, не виміряна межа ноутбука.
# Решта меж також під хешем; значення поза ними обрізаються. Параметр задачі власника не обрізаємо.
$script:Ceil = @{
    slots = @(0, 64); poll_minutes = @(1, 5); usage_minutes = @(5, 60); quota_wait_minutes = @(15, 1440)
    agy_total_minutes = @(30, 600); agy_turn_minutes = @(10, 600); codex_stall_minutes = @(10, 240); claude_hang_minutes = @(30, 240)
}
$script:Defaults = @{
    poll_minutes = 2; usage_minutes = 15; quota_wait_minutes = 60
    agy_total_minutes = 180; agy_turn_minutes = 120; codex_stall_minutes = 60; claude_hang_minutes = 120
}
$script:LaneDefaults = [ordered]@{ codex = 2; agy = 2; claude = 2 }
# Скільки разів відмова за квотою повертає ту саму позначку в чергу: далі — кінець із кодом квоти, як до смуг.
$script:MaxRetakes = 5
# Код виходу процесу наряду: слот чи GPU зайняті до старту — позначку не взято, вона лишається в черзі.
$script:WorkerSlotBusy = 3
$script:WorkerGpuBusy = 4
# Спільний рухомий бюджет публічного REST: половина 60/год лишається іншим читачам.
$script:ReviewApiLimit = 30
$script:ReviewApiWindow = 3600
$script:ReviewApiBackoff = 120
# План живого (Get-AutoLivePlan, автоживий й Е1-нічний-живий). Вимір 07.11: `pulls?state=all` — 33 сторінки по 100 PR,
# сторінка до 2,36 млн знаків (3273 PR); повне читання на спробу — 33 запити з 60/год без входу. Тепер сторінки по 50,
# читання стоїть, щойно сторінка старіша за збірку останнього звіту (запити — з бюджету review-api.json, як у
# Get-AutoReviewState), а більше AutoPlanMaxPages сторінок на спробу — AUTO_PAGES, не мовчазне повторення.
$script:AutoPlanPerPage = 50
$script:AutoPlanMaxPages = 20
# Запас на розбіжність годинників: звіт не може згадати збірку, що старша за його оновлення; злиття — старше за збірку.
$script:AutoPlanMarginHours = 6
$script:AutoApiCalls = 0
# Збій побудови плану (Add-AutoTaskContext) — окреме чекання з лічильником retakes; на межі MaxRetakes — PLAN_FAILED.
# Вимір 07.11 (ноутбучна сесія): три відмови плану о 17:54–17:59, о 18:10 той самий план зібрався за 29 с, тобто збій минав за
# 11–16 хв; MaxRetakes × PlanBackoff = 5 × 300 с = 25 хв покриває його з запасом.
$script:PlanBackoff = 300
# Скільки секунд прохід чекає на перший результат GPU-наряду, запущеного ним, перш ніж віддати GPU наступній позначці.
# Вимір 07.11 (#1856): воркер p1 щопроходу виходив у WAIT за секунди; 120 с — стеля того очікування (числа запасу виміром
# не перевірено: часу від запуску до STARTED успішного прогону журнал не дає).
$script:GpuStartWaitSeconds = 120
$script:GpuStartPollMs = 500
# Вимір 30.10: найбільший із доступних знімків живих прогонів — 8925 MiB усієї карти.
# Джерела й прогалини (пік каталогу, навантаження гри): аудит/корені/ПК-межа-без-джерела-gpu.md.
# Це запасний бюджет за спостереженим максимумом, а не доведений пік будь-якої моделі.
$script:GpuRunMiB = 8925

# --- процеси й файли ----------------------------------------------------------------------------------------------

function Get-Sha256Hex([string]$Text) {
    <# SHA-256 рядка UTF-8 шістнадцятковими малими. #>
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { -join ($sha.ComputeHash($script:Utf8.GetBytes($Text)) | ForEach-Object { $_.ToString('x2') }) }
    finally { $sha.Dispose() }
}

function Write-FileAtomic([string]$Path, [string]$Text) {
    <# Запис через тимчасовий файл і заміну: читач не бачить половини.

    Спільні файли (стан, heartbeat, кеш квоти) пишуть водночас планувальник і процеси нарядів: зайнята ціль — кілька
    спроб, а не виняток посеред наряду. #>
    $tmp = $Path + '.' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.part'
    [System.IO.File]::WriteAllText($tmp, $Text, $script:Utf8)
    for ($i = 0; $i -lt 20; $i++) {
        try {
            if ([System.IO.File]::Exists($Path)) { [System.IO.File]::Replace($tmp, $Path, [NullString]::Value) } else { [System.IO.File]::Move($tmp, $Path) }
            return
        } catch {
            if ($i -eq 19) { Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; throw }
            Start-Sleep -Milliseconds 50
        }
    }
}

function Get-UtcStamp([datetime]$When) {
    <# Час у UTC рядком ISO з Z. #>
    $When.ToUniversalTime().ToString("yyyy-MM-dd'T'HH:mm:ss'Z'")
}

function ConvertTo-ArgString([string[]]$Items) {
    <# Рядок аргументів за правилами CommandLineToArgvW.

    .NET Framework не має ArgumentList, а вбудований виклик PowerShell 5.1 губить лапки всередині аргументів. #>
    $parts = foreach ($a in $Items) {
        if ($a -eq '') { '""'; continue }
        if ($a -notmatch '[\s"]') { $a; continue }
        $sb = New-Object System.Text.StringBuilder
        [void]$sb.Append('"')
        $bs = 0
        foreach ($ch in $a.ToCharArray()) {
            if ($ch -eq '\') { $bs++; continue }
            if ($ch -eq '"') { [void]$sb.Append('\' * ($bs * 2 + 1)); [void]$sb.Append('"'); $bs = 0; continue }
            if ($bs -gt 0) { [void]$sb.Append('\' * $bs); $bs = 0 }
            [void]$sb.Append($ch)
        }
        [void]$sb.Append('\' * ($bs * 2))
        [void]$sb.Append('"')
        $sb.ToString()
    }
    $parts -join ' '
}

function New-StartInfo([string]$Exe, [string[]]$Arguments, [string]$Dir, [switch]$NoRedirect) {
    <# Процес без вікна, UTF-8, git без питань про вхід; -NoRedirect — потоки успадковано (процес наряду). #>
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = ConvertTo-ArgString $Arguments
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true
    if (-not $NoRedirect) {
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.StandardOutputEncoding = $script:Utf8
        $psi.StandardErrorEncoding = $script:Utf8
    }
    if ($Dir) { $psi.WorkingDirectory = $Dir }
    $psi.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $psi.EnvironmentVariables['GCM_INTERACTIVE'] = 'never'
    $psi
}

function Add-TreeJobType {
    if ('GeminiWrapper.TreeJob' -as [type]) { return }
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
namespace GeminiWrapper {
    public static class TreeJob {
        [StructLayout(LayoutKind.Sequential)]
        struct BasicLimit { public long PerProcessTime; public long PerJobTime; public uint Flags; public UIntPtr MinWs; public UIntPtr MaxWs; public uint ActiveLimit; public UIntPtr Affinity; public uint Priority; public uint Scheduling; }
        [StructLayout(LayoutKind.Sequential)]
        struct ExtendedLimit { public BasicLimit Basic; public ulong R1, R2, R3, R4, R5, R6; public UIntPtr ProcessMem, JobMem, PeakProcessMem, PeakJobMem; }
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr attributes, string name);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetInformationJobObject(IntPtr job, int infoClass, ref ExtendedLimit info, int size);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool QueryInformationJobObject(IntPtr job, int infoClass, IntPtr info, int size, IntPtr returned);
        [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr OpenProcess(uint access, bool inherit, int id);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool IsProcessInJob(IntPtr process, IntPtr job, out bool result);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool TerminateProcess(IntPtr process, uint code);
        [DllImport("kernel32.dll", SetLastError = true)] static extern bool CloseHandle(IntPtr handle);

        public static IntPtr Create(IntPtr process) {
            IntPtr job = CreateJobObject(IntPtr.Zero, null);
            if (job == IntPtr.Zero) throw new Win32Exception();
            var info = new ExtendedLimit();
            info.Basic.Flags = 0x800;  // BREAKAWAY_OK: явний вихід із задачі (CREATE_BREAKAWAY_FROM_JOB) не ламає старту нащадка
            if (!SetInformationJobObject(job, 9, ref info, Marshal.SizeOf(typeof(ExtendedLimit))) || !AssignProcessToJobObject(job, process)) {
                var e = new Win32Exception(); CloseHandle(job); throw e;
            }
            return job;
        }

        public static int[] Members(IntPtr job) {
            const int max = 4096; int size = 8 + IntPtr.Size * max;
            IntPtr buf = Marshal.AllocHGlobal(size);
            try {
                if (!QueryInformationJobObject(job, 3, buf, size, IntPtr.Zero)) throw new Win32Exception();
                var ids = new int[Marshal.ReadInt32(buf, 4)];
                for (int i = 0; i < ids.Length; i++) ids[i] = (int)Marshal.ReadIntPtr(buf, 8 + i * IntPtr.Size).ToInt64();
                return ids;
            } finally { Marshal.FreeHGlobal(buf); }
        }

        public static bool Kill(IntPtr job, int id) {
            IntPtr p = OpenProcess(0x1001, false, id);  // TERMINATE | QUERY_LIMITED_INFORMATION
            if (p == IntPtr.Zero) return false;
            try { bool inJob; return IsProcessInJob(p, job, out inJob) && inJob && TerminateProcess(p, 1); }
            finally { CloseHandle(p); }
        }

        public static void Close(IntPtr job) { CloseHandle(job); }
    }
}
'@
}

function Start-Tree($Psi) {
    <# Старт процесу в задачі Windows: нащадки, відірвані від батька (nohup, start), лишаються в ній, і Stop-Tree зупиняє
    їх разом із деревом. 08.11 вимір, запущений сесією через nohup, після кінця наряду тримав 12 ГБ відеокарти й копію задачі. #>
    # Тип збирається до старту: збірка триває секунди, а нащадки, народжені до прив'язки, у задачу не потрапляють.
    $typed = $false
    if ($script:OnWindows) { try { Add-TreeJobType; $typed = $true } catch { Write-Log "задача процесів: $($_.Exception.Message)" } }
    $p = [System.Diagnostics.Process]::Start($Psi)
    if ($typed) {
        try { $script:TreeJobs[$p.Id] = [GeminiWrapper.TreeJob]::Create($p.Handle) }
        catch { Write-Log "задача процесів $($p.Id): $($_.Exception.Message) — лишки зупиняє лише дерево" }
    }
    $p
}

function Stop-TreeJob([int]$Id) {
    <# Зупиняє решту задачі Windows процесу; інструменти LM Studio лишає — це спільний сервер, а моделі наряду прибирає
    Complete-GpuModels. #>
    if (-not $script:TreeJobs.ContainsKey($Id)) { return }
    $job = $script:TreeJobs[$Id]; $script:TreeJobs.Remove($Id)
    try {
        $gone = @(foreach ($i in [GeminiWrapper.TreeJob]::Members($job)) {
                $g = $null
                try { $g = Get-Process -Id $i -ErrorAction Stop } catch { continue }
                if (Test-GpuModelProcess $g.ProcessName ([string]$g.Path)) { continue }
                if ([GeminiWrapper.TreeJob]::Kill($job, $i)) { "$($g.ProcessName) $i" }
            })
        if ($gone.Count) { Write-Log "лишки дерева $Id зупинено: $($gone -join ', ')" }
    } catch { Write-Log "лишки дерева ${Id}: $($_.Exception.Message)" }
    finally { [GeminiWrapper.TreeJob]::Close($job) }
}

function Stop-Tree($Proc) {
    <# Зупинка процесу з усім деревом нащадків і рештою його задачі Windows (Start-Tree), також після його виходу. #>
    if ($null -eq $Proc) { return }
    try {
        if (-not $Proc.HasExited) {
            if ($script:OnWindows) { & taskkill.exe /PID $Proc.Id /T /F *> $null }
            else { $Proc.Kill($true) }
        }
        [void]$Proc.WaitForExit(15000)
    } catch { Write-Log "зупинка процесу: $($_.Exception.Message)" }
    Stop-TreeJob $Proc.Id
}

function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$Dir = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) {
    <# Запуск із межею часу (по межі — зупинка дерева) і необов'язковим stdin; повертає код, ознаку межі й обидва потоки. #>
    $psi = New-StartInfo $Exe $Arguments $Dir
    $psi.RedirectStandardInput = ($null -ne $StdIn)
    # .NET Framework створює StandardInput з AutoFlush: BOM пишеться вже під час Start.
    $stdinEncoding = [Console]::InputEncoding
    try {
        [Console]::InputEncoding = $script:Utf8
        $p = Start-Tree $psi
    } finally { [Console]::InputEncoding = $stdinEncoding }
    $out = $p.StandardOutput.ReadToEndAsync()
    $err = $p.StandardError.ReadToEndAsync()
    if ($null -ne $StdIn) {
        $w = New-Object System.IO.StreamWriter($p.StandardInput.BaseStream, $script:Utf8)
        $w.Write($StdIn)
        $w.Close()
    }
    $until = [datetime]::UtcNow.AddMinutes($TimeoutMinutes)
    while (-not $p.WaitForExit(1000) -and [datetime]::UtcNow -lt $until) { Invoke-HealthBeat }
    $timedOut = -not $p.HasExited
    if (-not $timedOut) { $p.WaitForExit() }
    Stop-Tree $p
    [pscustomobject]@{ Code = $(if ($timedOut) { -1 } else { $p.ExitCode }); TimedOut = $timedOut; Out = $out.Result; Err = $err.Result }
}

function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail, [double]$TimeoutMinutes = 10, [string]$Dir = '') {
    <# git у клоні ($RepoDir) чи в робочій копії слота (-Dir) без входу й без гачків. #>
    $d = $(if ($Dir) { $Dir } else { $RepoDir })
    $all = @('-C', $d, '-c', "core.hooksPath=$script:NoHooks", '-c', 'credential.helper=', '-c', 'core.quotepath=false') + $GitArgs
    $r = Invoke-Native $GitExe $all '' $TimeoutMinutes
    if ($r.Code -ne 0 -and -not $AllowFail) { throw "git $($GitArgs -join ' ') -> $($r.Code): $($r.Err.Trim())" }
    $r
}

function Get-RefSha([string]$Ref) {
    <# SHA коміту посилання або ''. #>
    $r = Invoke-Git @('rev-parse', '-q', '--verify', "$Ref^{commit}") -AllowFail
    if ($r.Code -ne 0) { return '' }
    $r.Out.Trim()
}

# --- межі з файла даних ---------------------------------------------------------------------------------------------

function Get-JsonProp($Obj, [string]$Name) {
    <# Властивість об'єкта з JSON або $null. #>
    if ($null -eq $Obj -or $Obj -is [string] -or $Obj -is [ValueType]) { return $null }
    $p = $Obj.PSObject.Properties[$Name]
    if ($null -eq $p) { return $null }
    $p.Value
}

function ConvertTo-Bounded($Value, $Range) {
    <# Число з JSON, обрізане до стелі [min, max]; не число — $null (тоді діє попереднє прийняте чи значення з коду). #>
    if ($Value -isnot [int] -and $Value -isnot [long] -and $Value -isnot [double] -and $Value -isnot [decimal]) { return $null }
    [Math]::Min([double]$Range[1], [Math]::Max([double]$Range[0], [double]$Value))
}

# Джерело межі (п.11): «власник ДД.ММ …» чи «вимір: …» з датою ДД.ММ і ще хоч одним числом (10970).
$script:LimitDateRx = '(?<![0-9])(?:0[1-9]|[12][0-9]|3[01])\.(?:0[1-9]|1[0-2])(?![0-9])'

function Test-LimitSource([string]$Text) {
    <# $true — у межі є джерело за форматом; інакше межа без джерела. Той самий розбір — у перевірка/перевірити_хеші.py. #>
    if ($Text.Length -gt 300 -or $Text -cmatch '[\x00-\x1f]') { return $false }
    if ($Text -cmatch ('\Aвласник ' + $script:LimitDateRx + '(?:[^0-9].*)?\z')) { return $true }
    if ($Text -cnotmatch '\Aвимір: ') { return $false }
    $d = [regex]::Match($Text, $script:LimitDateRx)
    $d.Success -and $Text.Remove($d.Index, $d.Length).Substring(6) -match '[0-9]'
}

function Get-LimitFields {
    <# Усі межі файла даних: слоти смуг і решта, у сталому порядку. #>
    @($script:LaneDefaults.Keys | ForEach-Object { "slots.$_" }) + @($script:Defaults.Keys | Sort-Object)
}

function Get-Limits {
    <# Межі смуг: `смуги.json` v2 з origin/main (не з робочої копії агента), обрізаний стелями.

    v2 — кожна межа `{"n": число, "джерело": "власник ДД.ММ …" | "вимір: … ДД.ММ"}`. Межа без джерела, v1 (міграція: числа
    без джерел), нема файла, кривий чи невідомий формат — попереднє прийняте значення (стан limits.json; нема — з коду), а
    поле — в unsourced для рядка «межа без джерела» стану ноутбука. Зміна файла в main діє на наступному проході без
    перевстановлення копій: читається він після `git fetch`, який перезаписує й origin/main, змінений у клоні. #>
    $l = @{ slots = [ordered]@{}; source = 'код'; unsourced = @(); claude_laptop = @() }
    foreach ($k in $script:LaneDefaults.Keys) { $l.slots[$k] = $script:LaneDefaults[$k] }
    foreach ($k in $script:Defaults.Keys) { $l[$k] = $script:Defaults[$k] }
    # Без теки стану (читач меж поза планувальником) попереднє не зберігається.
    $sd = $(try { [string]$script:StateDir } catch { '' })
    $prevPath = $(if ($sd) { Join-Path $sd 'limits.json' } else { '' })
    $prev = $null
    if ($prevPath -and (Test-Path -LiteralPath $prevPath)) { try { $prev = [System.IO.File]::ReadAllText($prevPath, $script:Utf8) | ConvertFrom-Json } catch { $null = $_ } }
    $doc = $null
    $r = Invoke-Git @('cat-file', 'blob', "refs/remotes/origin/main:$script:LanesPath") -AllowFail
    if ($r.Code -eq 0 -and $r.Out.Length -le 8192) {
        try { $doc = $r.Out | ConvertFrom-Json } catch { Write-Log 'смуги.json не читається як JSON — попередні межі' }
    }
    if ($null -ne $doc) { $l.source = 'origin/main' }
    $v2 = $null -ne $doc -and [string](Get-JsonProp $doc 'v') -eq '2'
    $accepted = [ordered]@{}
    foreach ($f in @(Get-LimitFields)) {
        $lane = $(if ($f.StartsWith('slots.')) { $f.Substring(6) } else { '' })
        $range = $(if ($lane) { $script:Ceil.slots } else { $script:Ceil[$f] })
        $node = $null
        if ($v2) { $node = $(if ($lane) { Get-JsonProp (Get-JsonProp $doc 'slots') $lane } else { Get-JsonProp $doc $f }) }
        $v = $null
        if (Test-LimitSource ([string](Get-JsonProp $node 'джерело'))) { $v = ConvertTo-Bounded (Get-JsonProp $node 'n') $range }
        if ($null -eq $v) {
            $l.unsourced += $f
            $v = ConvertTo-Bounded (Get-JsonProp $prev $f) $range
        }
        if ($null -eq $v) { continue }
        $accepted[$f] = $v
        if ($lane) { $l.slots[$lane] = [int][Math]::Floor($v) } else { $l[$f] = $v }
    }
    $text = $accepted | ConvertTo-Json -Compress
    $old = $(if ($prevPath -and (Test-Path -LiteralPath $prevPath)) { [System.IO.File]::ReadAllText($prevPath, $script:Utf8) } else { '' })
    if ($prevPath -and $accepted.Count -gt 0 -and $text -cne $old) { Write-FileAtomic $prevPath $text }
    # Наряди Claude, яким потрібен ноутбук без відеокарти (LM Studio, фото, локальні програми): лише назви за шаблоном.
    $l.claude_laptop = @(@(Get-JsonProp $doc 'claude_laptop') | Where-Object { $_ -is [string] -and $_ -cmatch $script:SlugPattern } | Select-Object -First 64)
    $l
}

function Get-Limit($Limits, [string]$Param, [string]$Key) {
    <# Значення межі: параметр, заданий явно (задача планувальника, стенд), сильніший за файл даних. #>
    if ($script:Bound.ContainsKey($Param)) { return [double]$script:Bound[$Param] }
    if ($null -eq $Limits) { return [double]$script:Defaults[$Key] }
    [double]$Limits[$Key]
}

# --- позначки ------------------------------------------------------------------------------------------------------

function Get-Lane([string]$Model) {
    <# Смуга за назвою моделі з позначки. #>
    if ($Model.StartsWith('cc-')) { return 'claude' }
    if ($Model -cmatch '^gpt-') { return 'codex' }
    'agy'
}

function ConvertTo-Marker([string]$Line) {
    <# Рядок for-each-ref (посилання, SHA, час коміту, тема коміту) -> позначка; Valid=$false — назва не за форматом.

    Cancel — голова позначки є комітом «ЗНЯТО…» диспетчера: він може пушити в гілку позначки, але не видаляти її, тож
    зняття — новий коміт поверх; Reason — решта теми. #>
    $f = $Line -split "`t", 4
    $rest = $f[0].Substring($script:QueuePrefix.Length)
    $parts = @($rest -split '/')
    $subject = $(if ($f.Count -eq 4) { $f[3] } else { '' })
    # Тема без сталої скрипта: стенди імпортують ConvertTo-Marker окремо від решти файла.
    $cancel = $subject -cmatch '^ЗНЯТО(.*)$'
    $reason = $(if ($cancel) { $Matches[1].Trim(" `t:—-".ToCharArray()) } else { '' })
    $m = [pscustomobject]@{ Ref = $f[0]; Name = 'gemini-queue/' + $rest; Sha = $f[1]; Time = [long]$f[2]
        Slug = ''; Model = ''; N = ''; Cond = ''; Prio = 5; Deadline = ''; Gpu = $false; Lane = ''; Seen = [long]0; Valid = $false
        Cancel = $cancel; Reason = $reason }
    if ($parts.Count -lt 3 -or $parts.Count -gt 4) { return $m }
    if ($parts[0] -notmatch $script:SlugPattern -or $parts[0].Contains('..') -or $parts[0].EndsWith('.lock')) { return $m }
    if ($parts[1] -notmatch $script:ModelPattern -or $parts[2] -notmatch '^[1-9][0-9]{0,2}$') { return $m }
    if ($parts.Count -eq 4) {
        if ($parts[3] -cnotmatch $script:CondPattern) { return $m }
        $kinds = @{}
        foreach ($t in ($parts[3] -split '-')) {
            $k = $t.Substring(0, 1)
            if ($kinds.ContainsKey($k)) { return $m }
            $kinds[$k] = 1
            if ($t -eq 'gpu') { $m.Gpu = $true }
            elseif ($k -eq 'p') { $m.Prio = [int]$t.Substring(1) }
            else {
                $dt = [datetime]::MinValue
                if (-not [datetime]::TryParseExact($t.Substring(1), 'yyyyMMddHHmm', [cultureinfo]::InvariantCulture, 'None', [ref]$dt)) { return $m }
                $m.Deadline = $t.Substring(1)
            }
        }
        $m.Cond = $parts[3]
    }
    $m.Slug = $parts[0]; $m.Model = $parts[1]; $m.N = $parts[2]; $m.Lane = Get-Lane $parts[1]; $m.Valid = $true
    $m
}

function Test-MarkerCancelled($M) {
    <# Позначку знято комітом «ЗНЯТО…» (поле Cancel з ConvertTo-Marker); об'єкт позначки без цього поля — не знятий. #>
    $p = $M.PSObject.Properties['Cancel']
    $null -ne $p -and [bool]$p.Value
}

function Get-Markers([string]$Pattern = $script:QueuePrefix) {
    <# Усі позначки черги з origin (після fetch), і криві — з Valid=$false; $Pattern — одна позначка (повна назва посилання). #>
    $fmt = '%(refname)%09%(objectname)%09%(committerdate:unix)%09%(contents:subject)'
    $r = Invoke-Git @('for-each-ref', "--format=$fmt", $Pattern)
    @(foreach ($line in ($r.Out -split "`n")) { if ($line.Trim()) { ConvertTo-Marker $line.Trim() } })
}

function Get-TaskSource($M) {
    <# Усі наряди використовують спільне визначення шляху шаблону. #>
    Get-AutoTaskPath $M.Slug
}

function Get-NightlyMarker([datetime]$Now = [datetime]::UtcNow) {
    <# Після 02:00 UTC читає лише датований дозвіл із GitHub; локальний стан не дає прав. #>
    $utc = $Now.ToUniversalTime()
    if ($utc.Hour -lt 2) { return }
    $date = $utc.ToString('yyyyMMdd')
    $ref = $script:QueuePrefix + 'Е1-нічний-живий-' + $date + '/gpt-6.1-sol-high/1/gpu-p8'
    $sha = Get-RefSha $ref
    if ($sha -cnotmatch '^[0-9a-f]{40}$') { return }
    $main = Get-RefSha 'refs/remotes/origin/main'
    if ($main -cnotmatch '^[0-9a-f]{40}$') { return }
    if ((Invoke-Git @('merge-base', '--is-ancestor', $sha, $main) -AllowFail).Code -ne 0) {
        # Голова не з main — лише зняття диспетчера («ЗНЯТО…» поверх дозволу з main). Його віддають тим самим читачем, що й звичайним
        # позначкам: Cancel лишається в позначці, і Start-Markers закриває її спільним обробником скасування (стоп прогону, CANCELLED).
        $cut = @(Get-Markers $ref | Where-Object { $_.Cancel })
        if ($cut.Count -eq 1 -and (Invoke-Git @('merge-base', $sha, $main) -AllowFail).Code -eq 0) { return $cut[0] }
        return
    }
    $template = 'аудит/наряди/автоживий.md'
    $build = (Invoke-Git @('cat-file','blob',"${sha}:build.txt") -AllowFail).Out.Trim()
    if ($build -cmatch '^[0-9a-f]{40}$' -and (Invoke-Git @('for-each-ref','--format=%(refname)',($script:QueuePrefix + "автоживий-$build/"))).Out.Trim()) { return }
    if ((Invoke-Git @('cat-file', '-e', "${sha}:$template") -AllowFail).Code -ne 0) { return }
    $dir = Join-Path $RunsDir 'nightly'
    [void](New-Item -ItemType Directory -Force -Path $dir)
    $file = Join-Path $dir ($date + '.json')
    if (Test-Path -LiteralPath $file) {
        $saved = [System.IO.File]::ReadAllText($file, $script:Utf8) | ConvertFrom-Json
        if ($saved.date -cne $date -or $saved.sha -cnotmatch '^[0-9a-f]{40}$' -or
            [string]$saved.time -cnotmatch '^[0-9]{10}$') { throw 'Хибний стан нічного прогону' }
        if ($saved.sha -cne $sha) { return }
    } else {
        $stamp = ([DateTimeOffset]$utc).ToUnixTimeSeconds()
        $saved = [pscustomobject]@{ date = $date; sha = $sha; time = $stamp }
        Write-FileAtomic $file ($saved | ConvertTo-Json -Compress)
    }
    ConvertTo-Marker ($ref + "`t" + $saved.sha + "`t" + $saved.time)
}

function Get-MarkerKey($M) { "$($M.Ref) $($M.Sha)" }

function Get-StatePath([string]$Key, [string]$StateDir = $script:StateDir) { Join-Path $StateDir ((Get-Sha256Hex $Key) + '.txt') }

function Get-ClaimPath([string]$StatePath) { $StatePath -replace '\.txt$', '.claim' }

function Add-FirstSeen($Markers) {
    <# Час першої появи позначки на ноутбуці (файл `<ключ>.seen`) — «час постановки» для рівних за пріоритетом і строком. #>
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    foreach ($m in $Markers) {
        $p = (Get-StatePath (Get-MarkerKey $m)) -replace '\.txt$', '.seen'
        $t = 0L
        if (Test-Path -LiteralPath $p) { [void][long]::TryParse([System.IO.File]::ReadAllText($p).Trim(), [ref]$t) }
        if ($t -le 0) { $t = $now; Write-FileAtomic $p ([string]$now) }
        $m.Seen = $t
    }
}

function Get-OrderedMarkers($Markers) {
    <# Порядок узяття: пріоритет, строк (без строку — після всіх), перша поява, час коміту, назва.

    Sort-Object, а не [Array]::Sort(ключі, позначки): PowerShell передає масив позначок методу копією, і сортувалися лише
    ключі (стенд смуг, 26.10). #>
    Add-FirstSeen $Markers
    @($Markers | Sort-Object @{ Expression = { $_.Prio } }, @{ Expression = { if ($_.Deadline) { $_.Deadline } else { '999999999999' } } },
        @{ Expression = { $_.Seen } }, @{ Expression = { $_.Time } }, @{ Expression = { $_.Name } })
}

function Get-ReviewTime {
    <# Поточна секунда UTC; стенд підміняє годинник без реального чекання. #>
    [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
}

# Спільна політика потрібна й при самостійному завантаженні бібліотеки черги.
if (-not (Get-Command Test-ReviewBranch -ErrorAction SilentlyContinue)) { . (Join-Path $PSScriptRoot 'wrapper_health.ps1') }

function Read-AutoApiBudget([string]$Path, [long]$Now) {
    <# Спільний бюджет публічного REST (`review-api.json`): запити за рухоме вікно й спільна пауза. Файла нема — порожній
    бюджет; пошкоджений — $null (непорахованих запитів не дозволяємо). Викликач тримає замок `review-api.lock`. #>
    if (-not (Test-Path -LiteralPath $Path)) { return [pscustomobject]@{ Calls = @(); Until = 0L } }
    $saved = [IO.File]::ReadAllText($Path, $script:Utf8) | ConvertFrom-Json
    if ($null -eq $saved.calls -or $null -eq $saved.until) { return $null }
    [pscustomobject]@{ Calls = @($saved.calls | Where-Object { [long]$_ -gt ($Now - $script:ReviewApiWindow) }); Until = [long]$saved.until }
}

function Use-AutoApiBudget {
    <# Один запит публічного REST зі спільного бюджету (ті самі файл, замок і межа, що в Get-AutoReviewState): запит
    резервується до мережі, тож збій і перезапуск не обнуляють витраченого. $false — замка нема, бюджет пошкоджений, діє
    спільна пауза чи вичерпано межу: викликач у мережу не йде. #>
    $lock = $null
    try {
        $lock = Open-Lock (Join-Path $LaneDir 'review-api.lock')
        if ($null -eq $lock) { return $false }
        $path = Join-Path $LaneDir 'review-api.json'
        $now = Get-ReviewTime
        $saved = Read-AutoApiBudget $path $now
        if ($null -eq $saved -or $now -lt $saved.Until -or $saved.Calls.Count -ge $script:ReviewApiLimit) { return $false }
        Write-FileAtomic $path ([ordered]@{calls=@($saved.Calls) + @($now);until=$saved.Until} | ConvertTo-Json -Compress)
        $true
    } catch { $false }
    finally { if ($null -ne $lock) { $lock.Dispose() } }
}

function Set-AutoApiPause {
    <# Мережева відмова публічного запиту ставить спільну паузу ReviewApiBackoff с, як у Get-AutoReviewState. #>
    $lock = $null
    try {
        $lock = Open-Lock (Join-Path $LaneDir 'review-api.lock')
        if ($null -eq $lock) { return }
        $path = Join-Path $LaneDir 'review-api.json'
        $now = Get-ReviewTime
        $saved = Read-AutoApiBudget $path $now
        if ($null -eq $saved) { return }
        Write-FileAtomic $path ([ordered]@{calls=@($saved.Calls);until=($now + $script:ReviewApiBackoff)} | ConvertTo-Json -Compress)
    } catch { $null = $_ }
    finally { if ($null -ne $lock) { $lock.Dispose() } }
}

function Get-AutoReviewState([string]$Slug) {
    <# Звіряє PR один раз безпосередньо перед моделлю, лише у вже вільному слоті.

    Спільний файл під замком обох облікових записів обмежує всі три смуги 30 запитами за рухому годину.
    Успішний LIVE не кешується: кожен справжній запуск отримує свіжий стан PR. `перевірка-<PR>` несе лише номер PR:
    злитий чи закритий PR — STALE до моделі (позначки перевірок давно злитих PR інакше доїдали квоту). #>
    if ($Slug -cmatch '^автоперевірка-([1-9][0-9]{0,8})-([0-9a-f]{40})$') { $number = $Matches[1]; $head = $Matches[2] }
    elseif ($Slug -cmatch '^перевірка-([1-9][0-9]{0,8})$') { $number = $Matches[1]; $head = '' }
    else { return 'LIVE' }
    $lock = $null
    try {
        $lock = Open-Lock (Join-Path $LaneDir 'review-api.lock')
        if ($null -eq $lock) { return 'REVIEW_API' }
        $path = Join-Path $LaneDir 'review-api.json'
        $now = Get-ReviewTime
        $saved = Read-AutoApiBudget $path $now
        # Пошкоджений бюджет не дозволяє непорахованих запитів.
        if ($null -eq $saved) { return 'REVIEW_API' }
        $calls = $saved.Calls; $until = $saved.Until
        if ($now -lt $until -or $calls.Count -ge $script:ReviewApiLimit) { return 'REVIEW_API' }
        # Резервуємо запит до мережі: 403/429, тайм-аут і падіння процесу також входять у бюджет.
        $budget = [ordered]@{calls=@($calls) + @($now);until=0L}
        Write-FileAtomic $path ($budget | ConvertTo-Json -Compress)
        try {
            $pr = Invoke-RestMethod -Uri "https://api.github.com/repos/mightyrochy/kod-shi-data/pulls/$number" -Method Get -TimeoutSec 20 -MaximumRedirection 0 -Headers @{Accept='application/vnd.github+json'; 'User-Agent'='kod-shi-wrapper'}
            if ([string]$pr.number -cne $number -or $pr.state -cnotin @('open','closed') -or [string]$pr.head.sha -cnotmatch '^[0-9a-f]{40}$') { throw 'REVIEW_RESPONSE' }
            if ($pr.state -cne 'open') { return 'STALE' }
            if (-not $head) { return 'LIVE' }
            if ($pr.head.sha -cne $head) { return 'STALE' }
            if ($pr.user.login -cne 'mightyrochy' -or $null -eq $pr.head.repo -or $pr.head.repo.full_name -cne 'mightyrochy/kod-shi-data' -or $pr.base.repo.full_name -cne 'mightyrochy/kod-shi-data' -or $pr.base.ref -cne 'main' -or (Test-ReviewBranch ([string]$pr.head.ref))) { return 'STALE' }
            'LIVE'
        } catch {
            $budget.until = $now + $script:ReviewApiBackoff
            Write-FileAtomic $path ($budget | ConvertTo-Json -Compress)
            'REVIEW_API'
        }
    } catch { 'REVIEW_API' }
    finally { if ($null -ne $lock) { $lock.Dispose() } }
}

function Enter-ReviewWait($M, [string]$Head = '') {
    <# Повертає позначку після відмови REST чи вичерпання бюджету без збільшення retakes і кінцевого звіту. #>
    [void](Set-MarkerWait $M ((Get-ReviewTime) + $script:ReviewApiBackoff) @{group='REVIEW_API';head=$Head})
    Write-Log "позначка $($M.Name): REVIEW_API; спроба збережена, повтор у черзі"
}

function Get-PlanFailReason([string]$Message) {
    <# Коротка причина збою плану для стану позначки й примітки в #1856: код обгортки (AUTO_*, REVIEW_*), статус HTTP чи
    PLAN_ERROR; текст відповіді сервера в стан не йде. #>
    if ($Message -cmatch '^(?:AUTO|REVIEW)_[A-Z_]{1,30}$') { return $Message }
    if ($Message -cmatch '\(([45][0-9]{2})\)|status code does not indicate success: ([45][0-9]{2})') { return 'HTTP_' + $(if ($Matches[1]) { $Matches[1] } else { $Matches[2] }) }
    'PLAN_ERROR'
}

function Enter-PlanWait($M, [string]$Reason, [string]$Head = '') {
    <# Збій побудови плану живого (Add-AutoTaskContext для автоживого й Е1-нічного). Бюджет запитів вичерпано (AUTO_BUDGET) — це не
    вада, а чекання вікна: як REVIEW_API, без лічильника. Решта — окреме чекання PlanBackoff с з лічильником retakes
    (спільна межа MaxRetakes): повертає $false, коли межу вичерпано і чекання не записано, — викликач кінчає наряд
    кодом PLAN_FAILED, який будить диспетчера (не тихий REVIEW_API без кінця). #>
    # Автоперевірка PR (не план): її збій API лишається REVIEW_API — повтор у черзі під бюджетом, як і було.
    if ($M.Slug -cnotmatch '^(?:автоживий-[0-9a-f]{40}|Е1-нічний-живий-[0-9]{8})$' -or $Reason -ceq 'AUTO_BUDGET') { Enter-ReviewWait $M $Head; return $true }
    $why = Get-PlanFailReason $Reason
    $n = Set-MarkerWait $M ((Get-ReviewTime) + $script:PlanBackoff) @{group='PLAN_WAIT';reason=$why;head=$Head;retake=$true}
    if ($null -eq $n) { Write-Log "позначка $($M.Name): план не збудовано (${why}: $(([regex]::Replace($Reason, '[\x00-\x1f\x7f]+', ' ')).Trim())) понад $($script:MaxRetakes) разів — PLAN_FAILED"; return $false }
    Write-Log "позначка $($M.Name): план не збудовано ($why); повтор $n із $($script:MaxRetakes) за $($script:PlanBackoff) с"
    $true
}

function Get-MarkerState($M, [string]$StateDir = $script:StateDir) {
    <# NEW — не бачили; TAKEN — узята (файл `.claim`); WAIT — чекає скидання квоти (Wait.until, unix); DONE — інше. #>
    $sp = Get-StatePath (Get-MarkerKey $M) $StateDir
    if (Test-Path -LiteralPath (Get-ClaimPath $sp)) { return [pscustomobject]@{ Kind = 'TAKEN'; Wait = $null } }
    if (-not (Test-Path -LiteralPath $sp)) { return [pscustomobject]@{ Kind = 'NEW'; Wait = $null } }
    $t = [System.IO.File]::ReadAllText($sp, $script:Utf8)
    if ($t.StartsWith('WAIT {')) {
        try { return [pscustomobject]@{ Kind = 'WAIT'; Wait = ($t.Substring(5) | ConvertFrom-Json) } } catch { $null = $_ }
    }
    [pscustomobject]@{ Kind = 'DONE'; Wait = $null }
}

function Test-MarkerReady($State) {
    <# Позначку можна брати: нова або час чекання квоти минув. #>
    if ($State.Kind -eq 'NEW') { return $true }
    $State.Kind -eq 'WAIT' -and [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -ge [long]$State.Wait.until
}

function New-Claim($M, [string]$Id) {
    <# Атомарне узяття: файл `.claim` створюється лише якщо його нема (CreateNew) — дві смуги чи два слоти одну позначку
    не візьмуть. $true — узято цим викликом. #>
    $p = Get-ClaimPath (Get-StatePath (Get-MarkerKey $M))
    try { $fs = [System.IO.File]::Open($p, 'CreateNew', 'Write', 'None') } catch { return $false }
    try { $b = $script:Utf8.GetBytes($Id); $fs.Write($b, 0, $b.Length) } finally { $fs.Dispose() }
    $true
}

function Remove-Claim([string]$StatePath) {
    <# Звільнити узяття позначки (після кінця чи переходу в чекання квоти). #>
    Remove-Item -LiteralPath (Get-ClaimPath $StatePath) -Force -ErrorAction SilentlyContinue
}

function Get-Retakes([string]$StatePath) {
    <# Скільки разів позначку вже повернули в чергу за квотою: лічильник `retakes` несуть і WAIT, і STARTED (запуск не
    стирає його — інакше кожна відмова рахувалась би першою і межа MaxRetakes була б недосяжна). #>
    if (-not (Test-Path -LiteralPath $StatePath)) { return 0 }
    $t = [System.IO.File]::ReadAllText($StatePath, $script:Utf8)
    if ($t -match '^(WAIT|STARTED) .*"retakes":\s*([0-9]{1,3})') { return [int]$Matches[2] }
    0
}

function Set-MarkerWait($M, [long]$Until, [hashtable]$Extra) {
    <# Позначка чекає скидання квоти до $Until (unix): спроба не спалена, ту саму позначку візьме та сама смуга.
    Повертає число повернень у чергу; понад MaxRetakes — $null (чекання не записано, далі кінець із кодом квоти). #>
    $sp = Get-StatePath (Get-MarkerKey $M)
    $n = Get-Retakes $sp
    if ($Extra.ContainsKey('retake') -and $Extra.retake) { $n++ }
    if ($n -gt $script:MaxRetakes) { return $null }
    $j = [ordered]@{ until = $Until; until_utc = (Get-UtcStamp ([DateTimeOffset]::FromUnixTimeSeconds($Until).UtcDateTime)); marker = $M.Name; retakes = $n }
    foreach ($k in $Extra.Keys) { if ($k -ne 'retake') { $j[$k] = $Extra[$k] } }
    Write-FileAtomic $sp ('WAIT ' + ($j | ConvertTo-Json -Compress))
    Remove-Claim $sp
    $n
}

function Clear-UnstartedClaim([string]$StatePath) {
    <# Узяття без запуску: помилка до STARTED (робоча копія, запуск процесу наряду) не лишає позначку вилученою з черги —
    claim звільняється, стан (NEW чи WAIT) зберігається. Позначку з STARTED закриває Resume-Interrupted. #>
    $t = ''
    if (Test-Path -LiteralPath $StatePath) { try { $t = [System.IO.File]::ReadAllText($StatePath, $script:Utf8) } catch { $null = $_ } }
    if ($t.StartsWith('STARTED ')) { return }
    Remove-Claim $StatePath
}

function Step-FailedStart($M, [string]$StatePath) {
    <# Відмова до STARTED (робоча копія, запуск процесу наряду) — та сама ланка claim -> STARTED, що й квота: рахується
    тим самим лічильником `retakes` і тією самою межею MaxRetakes. 'NONE' — claim уже звільнено (слот чи GPU зайняті,
    кінець, чекання) або є STARTED; 'RETRY' — claim звільнено, позначка в черзі (стан WAIT, група START, без чекання);
    'LIMIT' — межа: чекання не записано, claim лишається, викликач закриває позначку кінцевим станом і рядком. #>
    $t = ''
    if (Test-Path -LiteralPath $StatePath) { try { $t = [System.IO.File]::ReadAllText($StatePath, $script:Utf8) } catch { $null = $_ } }
    if ($t.StartsWith('STARTED ') -or -not (Test-Path -LiteralPath (Get-ClaimPath $StatePath))) { return 'NONE' }
    # Голова гілки попереднього чекання за квотою — для продовження — не губиться.
    $head = ''
    if ($t.StartsWith('WAIT {')) { try { $head = [string](Get-JsonProp ($t.Substring(5) | ConvertFrom-Json) 'head') } catch { $null = $_ } }
    $n = Set-MarkerWait $M ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds()) @{ retake = $true; group = 'START'; head = $head }
    if ($null -eq $n) { return 'LIMIT' }
    Write-Log "позначка $($M.Name): відмова до запуску, повернено в чергу ($n із $script:MaxRetakes)"
    'RETRY'
}

function Clear-OrphanClaims([string]$RunsRoot) {
    <# Claim, чий процес наряду зник до STARTED (вимкнення між узяттям і запуском): старший за 10 хв, стану STARTED нема,
    замок слота (з worker.json теки прогону `<id>`) вільний — звільнити. Живий наряд тримає замок слота, свіжий claim
    ще не дійшов до запуску. #>
    foreach ($c in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.claim' -File -ErrorAction SilentlyContinue)) {
        if (((Get-Date) - $c.LastWriteTime).TotalMinutes -lt 10) { continue }
        $sp = $c.FullName -replace '\.claim$', '.txt'
        $id = ''; try { $id = [System.IO.File]::ReadAllText($c.FullName, $script:Utf8).Trim() } catch { continue }
        if ($id -notmatch '^[0-9]{8}-[0-9]{6}-[0-9a-f]{12}$') { continue }
        $wf = Join-Path (Join-Path $RunsRoot $id) 'worker.json'
        if (Test-Path -LiteralPath $wf) {
            $slot = ''; try { $slot = [string](Get-JsonProp ([System.IO.File]::ReadAllText($wf, $script:Utf8) | ConvertFrom-Json) 'slot') } catch { continue }
            if (-not (Test-SlotName $slot) -or -not (Test-LockFree (Join-Path $script:SlotDir "$slot.lock"))) { continue }
        }
        Write-Log "узяття $id без запуску — звільнено"
        Clear-UnstartedClaim $sp
    }
}

function Get-WaitingMarkers {
    <# Позначки в чеканні квоти (для стану): назва, до коли (UTC), група. #>
    @(foreach ($f in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.txt' -File -ErrorAction SilentlyContinue)) {
        $t = [System.IO.File]::ReadAllText($f.FullName, $script:Utf8)
        if (-not $t.StartsWith('WAIT {')) { continue }
        try { $j = $t.Substring(5) | ConvertFrom-Json } catch { continue }
        [pscustomobject]@{ Marker = [string]$j.marker; Until = [string]$j.until_utc; Group = [string](Get-JsonProp $j 'group') }
    })
}

# --- здоров'я машини (лише показ, узяття не гейтить) ----------------------------------------------------------------

function Measure-DirBytes([string]$Path) {
    <# Розмір названої теки без переходу за точками з'єднання (профіль має петлі); недоступні теки — лічбою Skipped. #>
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Container)) { return $null }
    $bytes = 0L; $skipped = 0
    $stack = New-Object System.Collections.Stack
    $stack.Push((New-Object System.IO.DirectoryInfo $Path))
    while ($stack.Count -gt 0) {
        $d = $stack.Pop()
        try {
            foreach ($e in $d.EnumerateFileSystemInfos()) {
                if ($e.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { continue }
                if ($e -is [System.IO.DirectoryInfo]) { $stack.Push($e) } else { $bytes += $e.Length }
            }
        } catch { $skipped++ }
    }
    [pscustomobject]@{ Bytes = $bytes; Skipped = $skipped }
}

function Get-Unsourced($Limits) {
    <# Поля меж без джерела з об'єкта Get-Limits; межі з іншого джерела (стенд, старий стан) — без поля, порожньо. #>
    $u = $(if ($Limits -is [System.Collections.IDictionary]) { $(if ($Limits.Contains('unsourced')) { $Limits['unsourced'] }) } else { Get-JsonProp $Limits 'unsourced' })
    @($u | Where-Object { $_ })
}

function Get-MarkerKind([string]$Slug) {
    <# Вид позначки за назвою наряду — для лічби в стані. #>
    if ($Slug -cmatch '^автоперевірка-') { return 'автоперевірка' }
    if ($Slug -cmatch '^автоживий-') { return 'автоживий' }
    if ($Slug -cmatch '^Е1-нічний-живий-') { return 'нічний живий' }
    if ($Slug -cmatch '^перевірка-') { return 'перевірка' }
    if ($Slug -cmatch '^pachka-') { return 'пачка' }
    if ($Slug -ceq 'ВИМКНИ-НОУТБУК') { return 'вимкнення' }
    'наряд'
}

# --- версія обгортки ------------------------------------------------------------------------------------------------

function Get-VersionSwitch {
    <# Самооновлення перемкнуло `active.txt` на іншу версію, а цей довгий процес іде зі старої теки: повертає
    «<стара8> → <нова8>», інакше ''. Запуск не з `versions\<SHA40>` (клон, стенд без підміни) чи непрочитаний,
    кривий pointer або нова тека, якої нема, — ''. Головний цикл тоді чисто виходить між проходами: свої наряди
    доробляють окремими процесами під замками слотів, нову версію запускає планувальник. #>
    $dir = [string]$script:VersionDir
    if (-not $dir) { return '' }
    $leaf = Split-Path -Leaf $dir; $versions = Split-Path -Parent $dir
    if ($leaf -cnotmatch '^[0-9a-f]{40}$' -or -not $versions -or (Split-Path -Leaf $versions) -cne 'versions') { return '' }
    $active = ''
    try { $active = [System.IO.File]::ReadAllText((Join-Path (Split-Path -Parent $versions) 'active.txt')).Trim() } catch { return '' }
    if ($active -cnotmatch '^[0-9a-f]{40}$' -or $active -ceq $leaf) { return '' }
    if (-not (Test-Path -LiteralPath (Join-Path $versions $active) -PathType Container)) { return '' }
    "$($leaf.Substring(0, 8)) → $($active.Substring(0, 8))"
}

function Write-VersionSwitch([string]$Switch) {
    <# Журнал і `state/version.txt` (його показує стан ноутбука): «<час UTC> <стара> → <нова>». #>
    Write-Log "версія: $Switch — головний процес виходить, нову запустить планувальник"
    if ($script:StateDir) {
        try { Write-FileAtomic (Join-Path $script:StateDir 'version.txt') ("$((Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')) $Switch") } catch { $null = $_ }
    }
}

# --- слоти, GPU, процес наряду -------------------------------------------------------------------------------------

function Test-SlotCount([string]$Value) {
    <# Ціла кількість слотів у спільному діапазоні; недовірені значення відкидаємо, не обрізаємо. #>
    $n = 0
    [regex]::IsMatch($Value, '\A(?:0|[1-9][0-9]*)\z') -and [int]::TryParse($Value, [ref]$n) -and
        $n -ge $script:Ceil.slots[0] -and $n -le $script:Ceil.slots[1]
}

function Test-SlotName([string]$Name, [string[]]$Lanes = @($script:LaneDefaults.Keys)) {
    <# Назва слота дозволеної смуги з додатним номером у спільному діапазоні.

    Номер не обмежуємо поточним N: після зменшення смуги вже запущені наряди мають завершитися. #>
    $m = [regex]::Match($Name, '\A([a-z]+)-([1-9][0-9]*)\z')
    $m.Success -and $Lanes -ccontains $m.Groups[1].Value -and (Test-SlotCount $m.Groups[2].Value)
}

function Open-Lock([string]$Path) {
    <# Винятковий замок-файл (FileShare None) або $null — зайнято. Звільняє ОС, коли процес-власник завершився. #>
    try { [System.IO.File]::Open($Path, 'OpenOrCreate', 'ReadWrite', 'None') } catch { $null }
}

function Get-SleepGap([datetime]$Tick, [datetime]$Now) {
    <# Цикл наряду обертається щонайменше раз на хвилину: довша пауза — сон ноутбука, а не завислість наряду. #>
    $gap = $Now - $Tick
    if ($gap.TotalMinutes -gt 5) { $gap } else { [timespan]::Zero }
}

function Test-LockFree([string]$Path) {
    <# Замок вільний зараз (відкрито й одразу закрито). #>
    $l = Open-Lock $Path
    if ($null -eq $l) { return $false }
    $l.Dispose()
    $true
}

function Get-GpuLockPath { Join-Path $LaneDir 'gpu.lock' }

function Get-LmsInstances {
    <# Читає екземпляри локального LM Studio; неповна відповідь не є порожнім сервером. #>
    $v = Invoke-RestMethod 'http://127.0.0.1:1234/api/v1/models' -TimeoutSec 15 -ErrorAction Stop
    if ((Get-JsonProp $v 'error') -or $v.models -isnot [array]) { throw 'LM Studio: немає переліку models' }
    foreach ($m in $v.models) {
        if (-not $m.key -or $m.loaded_instances -isnot [array]) { throw 'LM Studio: неповна модель' }
        foreach ($i in $m.loaded_instances) {
            if (-not ($i.id -is [string]) -or -not $i.id) { throw 'LM Studio: немає ID екземпляра' }
            [pscustomobject]@{ id = $i.id; model = $m.key }
        }
    }
}

function Get-GpuLeaseLockPath([string]$Run) {
    <# Замок життя GPU-оренди прогону: його тримає процес наряду від допуску до кінця. #>
    Join-Path $LaneDir ('gpu-lease-' + (Get-Sha256Hex $Run) + '.lock')
}

function Test-LeaseLive([string]$Path) {
    <# Чи тримає замок оренди живий процес; нема файла — оренда мертва.
    Будь-яка відмова відкрити — жива: мертву прибере наступний прохід, а в живої не можна забрати моделей. #>
    if (-not [IO.File]::Exists($Path)) { return $false }
    try { ([IO.File]::Open($Path, 'Open', 'ReadWrite', 'None')).Dispose(); $false } catch { $true }
}

function Read-GpuSession {
    <# Спільний запис GPU-сесії (`lanes/gpu-models.json`) або $null; неповний — виняток: межі власності не вгадуємо.

    Сесія триває від допуску першої GPU-оренди до кінця останньої з тих, що перекривались. Before — екземпляри LM Studio
    до неї (власника: не вивантажуються); join оренди — екземпляри в мить її допуску: те, що вже було, вона не вантажила.
    Запис v1 (одна оренда старої версії обгортки) — сесія з уже закінченою орендою: прибирання те саме, що було. #>
    $path = Join-Path $LaneDir 'gpu-models.json'
    if (-not [IO.File]::Exists($path)) { return $null }
    $s = [IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json -ErrorAction Stop
    $field = { param($Name) $p = $s.PSObject.Properties[$Name]; if ($null -ne $p) { , $p.Value } }
    $before = & $field 'before'
    if ($before -isnot [array]) { throw 'GPU: неповний знімок моделей' }
    foreach ($i in $before) { if (-not (Get-JsonProp $i 'id') -or -not (Get-JsonProp $i 'model')) { throw 'GPU: неповний початковий екземпляр' } }
    $leases = New-Object System.Collections.ArrayList
    $v = Get-JsonProp $s 'v'; $all = & $field 'leases'
    if ($v -eq 1 -and (Get-JsonProp $s 'marker') -and (Get-JsonProp $s 'run')) {
        [void]$leases.Add([pscustomobject]@{ run = [string]$s.run; marker = [string]$s.marker; join = @($before | ForEach-Object { [string]$_.id }); done = $true })
    } elseif ($v -eq 2 -and $all -is [array]) {
        foreach ($l in $all) {
            $join = $null; $p = $l.PSObject.Properties['join']; if ($null -ne $p) { $join = $p.Value }
            if (-not (Get-JsonProp $l 'run') -or -not (Get-JsonProp $l 'marker') -or $join -isnot [array]) { throw 'GPU: неповна оренда' }
            [void]$leases.Add([pscustomobject]@{ run = [string]$l.run; marker = [string]$l.marker; join = @($join | ForEach-Object { [string]$_ }); done = ((Get-JsonProp $l 'done') -eq $true) })
        }
    } else { throw 'GPU: неповний знімок моделей' }
    [pscustomobject]@{ Before = @($before); Leases = $leases; Dirty = ((Get-JsonProp $s 'dirty') -eq $true) }
}

function Save-GpuSession($Session) {
    <# Пише сесію під воротами GPU; dirty — є закінчена оренда, чиї моделі ще не перевірено. #>
    $leases = @(foreach ($l in $Session.Leases) { [ordered]@{ run = $l.run; marker = $l.marker; join = @($l.join); done = [bool]$l.done } })
    $o = [ordered]@{ v = 2; before = @($Session.Before); leases = $leases; dirty = [bool]$Session.Dirty }
    Write-FileAtomic (Join-Path $LaneDir 'gpu-models.json') (ConvertTo-Json -InputObject $o -Depth 6 -Compress)
}

function Get-LiveGpuLeases($Session) {
    <# Незакінчені оренди сесії, чий процес наряду ще тримає замок оренди. #>
    @($Session.Leases | Where-Object { -not $_.done -and (Test-LeaseLive (Get-GpuLeaseLockPath $_.run)) })
}

function Complete-GpuModels([string]$Run = '') {
    <# Під воротами GPU закінчує оренду $Run (і мертві) й вивантажує екземпляри, яких жодна жива оренда завантажити не
    могла: їх нема в before, і кожна інша жива оренда прийшла, коли вони вже були. Решту лишає останній живій оренді:
    з двох одночасних нарядів жоден не вивантажує моделі сусіда, а моделі власника (before) — ніхто. Останній видаляє
    запис. Збій лишає запис для повтору. #>
    $s = Read-GpuSession
    if ($null -eq $s) { return }
    $ended = $false
    foreach ($l in $s.Leases) {
        if ($l.done) { continue }
        $lockPath = Get-GpuLeaseLockPath $l.run
        if ($Run -and $l.run -ceq $Run) { $l.done = $true; $ended = $true }
        elseif (-not (Test-LeaseLive $lockPath)) {
            $l.done = $true; $ended = $true
            Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
        }
    }
    $live = @($s.Leases | Where-Object { -not $_.done })
    if ($live.Count -and -not $ended -and -not $s.Dirty) { return }
    # Закінчення оренди записано до REST: збій LM Studio не повертає мертву оренду в живі.
    if ($ended) { $s.Dirty = $true; Save-GpuSession $s }
    $keep = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
    foreach ($i in $s.Before) { [void]$keep.Add([string]$i.id) }
    foreach ($i in @(Get-LmsInstances)) {
        if ($keep.Contains($i.id) -or @($live | Where-Object { $_.join -cnotcontains $i.id }).Count) { continue }
        $by = @($s.Leases | Where-Object { $_.join -cnotcontains $i.id })
        Write-Log "GPU вивантаження: модель=$($i.model); екземпляр=$($i.id); наряд=$(@($by | ForEach-Object { $_.marker }) -join ','); прогін=$(@($by | ForEach-Object { $_.run }) -join ',')" -Required
        $body = @{ instance_id = $i.id } | ConvertTo-Json -Compress
        $v = Invoke-RestMethod 'http://127.0.0.1:1234/api/v1/models/unload' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120 -ErrorAction Stop
        if (Get-JsonProp $v 'error') { throw 'LM Studio: відмова вивантаження' }
    }
    if ($live.Count) { $s.Dirty = $false; Save-GpuSession $s; return }
    if (@(Get-LmsInstances | Where-Object { -not $keep.Contains($_.id) }).Count) { throw 'GPU: нові екземпляри ще завантажені' }
    Remove-Item -LiteralPath (Join-Path $LaneDir 'gpu-models.json') -Force -ErrorAction Stop
}

function Start-GpuModels($Job) {
    <# Під воротами GPU, до агента: приєднує прогін до сесії з переліком екземплярів цієї миті. Замок оренди процес наряду
    тримає до кінця: його смерть видно обом планувальникам, і прибирання не чекає на finally. #>
    $lockPath = Get-GpuLeaseLockPath ([string]$Job.id)
    $lease = Open-Lock $lockPath
    if ($null -eq $lease) { throw 'GPU: замок оренди зайнятий' }
    try {
        $now = @(Get-LmsInstances)
        $s = Read-GpuSession
        if ($null -eq $s) { $s = [pscustomobject]@{ Before = $now; Leases = (New-Object System.Collections.ArrayList); Dirty = $false } }
        [void]$s.Leases.Add([pscustomobject]@{ run = [string]$Job.id; marker = [string]$Job.name; join = @($now | ForEach-Object { [string]$_.id }); done = $false })
        Save-GpuSession $s
    } catch {
        $lease.Dispose()
        Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
        throw
    }
    $script:GpuLease = $lease
}

function Enter-GpuLease($Job) {
    <# Допуск GPU-наряду в процесі наряду; '' — допущено, інакше причина, і позначка лишається в черзі.

    Ворота `gpu.lock` тримаються лише на час рішення, а не весь прогін: наряд, що готується, качає чи думає хмарною
    моделлю, карти не займає й інших GPU-нарядів не тримає. Під воротами — прибирання мертвих оренд, карта без моделей
    живих GPU-нарядів (Get-GpuSessionReason), вільна пам'ять (Test-ExternalGpuFree), приєднання до сесії. #>
    $gate = Open-Lock (Get-GpuLockPath)
    if ($null -eq $gate) { return 'замок GPU' }
    try {
        try { Complete-GpuModels } catch { return "знімок моделей недоступний: $($_.Exception.Message)" }
        $why = Get-GpuSessionReason
        if (-not $why -and -not (Test-ExternalGpuFree -LogAcquisition)) { $why = Get-GpuBusyReason -LockHeld }
        if ($why) { return $why }
        try { Start-GpuModels $Job } catch { return "знімок моделей недоступний: $($_.Exception.Message)" }
        ''
    } finally { $gate.Dispose() }
}

function Exit-GpuLease($Job) {
    <# Кінець GPU-наряду на кожному шляху виходу: під воротами закінчує оренду й прибирає те, що вже нічиє, тоді відпускає
    замок оренди. Ворота зайняті чи збій — оренда стає мертвою, і її прибирає наступний прохід (Repair-GpuModels). #>
    $gate = Open-Lock (Get-GpuLockPath)
    try {
        if ($null -eq $gate) { Write-Log 'GPU прибирання відкладено: ворота GPU зайняті' }
        else { try { Complete-GpuModels ([string]$Job.id) } catch { Write-Log "GPU прибирання відкладено: $($_.Exception.Message)" } }
    } finally {
        if ($null -ne $gate) { $gate.Dispose() }
        if ($null -ne $script:GpuLease) {
            $script:GpuLease.Dispose(); $script:GpuLease = $null
            Remove-Item -LiteralPath (Get-GpuLeaseLockPath ([string]$Job.id)) -Force -ErrorAction SilentlyContinue
        }
    }
}

function Repair-GpuModels {
    <# Планувальник прибирає залишки мертвих оренд перед воротами GPU, навіть коли черга порожня. #>
    $gpuLock = Open-Lock (Get-GpuLockPath)
    if ($null -eq $gpuLock) { return $true }
    try { Complete-GpuModels; $true }
    catch { Write-Log "GPU прибирання відкладено: $($_.Exception.Message)"; $false }
    finally { $gpuLock.Dispose() }
}


function Get-BusySlots([string]$Lane, $Workers) {
    <# Зайняті слоти смуги: свій живий процес наряду або чужий замок слота (наряд попереднього проходу ще йде). #>
    @(for ($k = 1; $k -le $script:Ceil.slots[1]; $k++) {
        $id = "$Lane-$k"
        $own = @($Workers | Where-Object { $_.Slot -eq $id -and -not $_.Proc.HasExited }).Count -gt 0
        if ($own -or -not (Test-LockFree (Join-Path $script:SlotDir "$id.lock"))) { $id }
    })
}

function Get-FreeSlot([string]$Lane, [int]$N, $Workers) {
    <# Вільний слот смуги, коли зайнятих менше за N з файла даних; інакше ''. #>
    $busy = @(Get-BusySlots $Lane $Workers)
    if ($busy.Count -ge $N) { return '' }
    for ($k = 1; $k -le $script:Ceil.slots[1]; $k++) { if ($busy -notcontains "$Lane-$k") { return "$Lane-$k" } }
    ''
}

function Read-SlotInfo([string]$Lane) {
    <# Що йде в слотах смуги зараз: файли `<слот>.json` при зайнятому замку слота. #>
    @(for ($k = 1; $k -le $script:Ceil.slots[1]; $k++) {
        $id = "$Lane-$k"; $j = Join-Path $script:SlotDir "$id.json"
        if (-not (Test-Path -LiteralPath $j)) { continue }
        if (Test-LockFree (Join-Path $script:SlotDir "$id.lock")) { continue }
        try { [System.IO.File]::ReadAllText($j, $script:Utf8) | ConvertFrom-Json } catch { $null = $_ }
    })
}

function Test-SlugBusy([string]$Slug, [string[]]$Lanes) {
    <# Той самий наряд уже йде в одному зі слотів: дві спроби одного наряду водночас не беремо (одна гілка). #>
    foreach ($ln in $Lanes) { foreach ($s in @(Read-SlotInfo $ln)) { if ([string]$s.slug -ceq $Slug) { return $true } } }
    $false
}

function Stop-CancelledRuns($M, $Workers) {
    <# Знята позначка (голова «ЗНЯТО…»), прогін якої вже йде під попереднім SHA у слоті цього планувальника: процес наряду
    зупиняється деревом (той самий обліковий запис, що запустив, — прав адміністратора не треба), його STARTED
    закривається кінцем CANCELLED без результату — публікувати нема чого, кінець несе результат самої знятої позначки.

    Свій процес — з $Workers; процес попереднього планувальника — за pid з `<слот>.json`, поки замок слота зайнятий. #>
    $slots = New-Object System.Collections.ArrayList
    foreach ($w in @($Workers | Where-Object { $_.Marker -ceq $M.Name -and -not $_.Proc.HasExited })) { Stop-Tree $w.Proc; [void]$slots.Add([string]$w.Slot) }
    foreach ($ln in $script:Lanes) {
        foreach ($s in @(Read-SlotInfo $ln)) {
            if ([string]$s.marker -cne $M.Name -or $slots -ccontains [string]$s.slot) { continue }
            try { Stop-Tree (Get-Process -Id ([int]$s.pid) -ErrorAction Stop) } catch { Write-Log "зняття $($M.Name): процес $($s.pid) не знайдено — $($_.Exception.Message)" }
            [void]$slots.Add([string]$s.slot)
        }
    }
    if ($slots.Count -eq 0) { return }
    foreach ($f in @(Get-ChildItem -LiteralPath $script:StateDir -Filter '*.txt' -File -ErrorAction SilentlyContinue)) {
        $t = [IO.File]::ReadAllText($f.FullName, $script:Utf8)
        # gemini: `STARTED {json з id}`; claude: `STARTED <id> {json}`.
        if ($t -cnotmatch '^STARTED (?:([0-9]{8}-[0-9]{6}-[0-9a-f]{12}) )?(\{.*\})\s*$') { continue }
        $id = $Matches[1]
        try { $j = $Matches[2] | ConvertFrom-Json } catch { continue }
        $slot = [string](Get-JsonProp $j 'slot')
        if ($slots -cnotcontains $slot -or -not (Test-LockFree (Join-Path $script:SlotDir "$slot.lock"))) { continue }
        if (-not $id) { $id = [string](Get-JsonProp $j 'id') }
        Write-FileAtomic $f.FullName "DONE $id CANCELLED"
        Remove-Claim $f.FullName
        Write-Log "зняття $($M.Name): прогін $id у слоті $slot зупинено — CANCELLED"
    }
}

function Get-WorkerCommand([string]$File) {
    <# Команда процесу наряду: той самий скрипт тим самим PowerShell з -WorkerFile (стенд підміняє). #>
    @{ Exe = (Get-Process -Id $PID).Path; Args = @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $script:SelfPath, '-WorkerFile', $File) }
}

function Start-Worker([hashtable]$Job, [string]$Dir) {
    <# Наряд — окремим процесом зі своїм слотом, текою запуску й робочою копією; параметри скрипта — ті самі. #>
    $Job.params = $script:Bound
    $file = Join-Path $Dir 'worker.json'
    Write-FileAtomic $file ($Job | ConvertTo-Json -Compress -Depth 6)
    $c = Get-WorkerCommand $file
    $p = [System.Diagnostics.Process]::Start((New-StartInfo $c.Exe $c.Args '' -NoRedirect))
    [pscustomobject]@{ Slot = $Job.slot; Slug = $Job.slug; Gpu = [bool]$Job.gpu; Marker = $Job.name; Proc = $p }
}

function Read-WorkerJob([string]$File) {
    <# Завдання процесу наряду; параметри скрипта з нього стають змінними скрипта (як у планувальника). #>
    $job = [System.IO.File]::ReadAllText($File, $script:Utf8) | ConvertFrom-Json
    $p = Get-JsonProp $job 'params'
    $script:Bound = @{}
    if ($null -ne $p) {
        foreach ($x in $p.PSObject.Properties) { Set-Variable -Scope Script -Name $x.Name -Value $x.Value; $script:Bound[$x.Name] = $x.Value }
    }
    $job
}

function Wait-Workers($Workers, [double]$Minutes) {
    <# Чекати, доки скінчиться будь-який свій наряд або мине інтервал опитування. #>
    $alive = @($Workers | Where-Object { -not $_.Proc.HasExited }).Count
    $until = (Get-Date).AddMinutes($Minutes)
    while ((Get-Date) -lt $until) {
        if (@($Workers | Where-Object { -not $_.Proc.HasExited }).Count -lt $alive) { return }
        Invoke-HealthBeat
        Start-Sleep -Milliseconds 500
    }
}

function Test-RunStarted([string]$StatePath) {
    <# Наряд дійшов до моделі: стан STARTED із початком прогону (gemini: `start` — SHA, claude: `start` — час процесу).
    До цього він міг лише звіритися й піти в чекання (REVIEW_API, PLAN_WAIT), не торкнувшись GPU. #>
    try {
        if (-not [IO.File]::Exists($StatePath)) { return $false }
        $t = [IO.File]::ReadAllText($StatePath, $script:Utf8)
        $t.StartsWith('STARTED ') -and $t -cnotmatch '"start":\s*""'
    } catch { $false }
}

function Test-LaterGpuMarker($Ordered, $Current) {
    <# Після позначки в порядку проходу стоїть інша готова GPU-позначка (нова чи з минулим часом чекання). #>
    $seen = $false
    foreach ($x in @($Ordered)) {
        if (-not $seen) { if ($x.Name -ceq $Current.Name) { $seen = $true }; continue }
        if (-not $x.Gpu -or ($null -ne $x.PSObject.Properties['Off'] -and $x.Off)) { continue }
        if (Test-MarkerReady (Get-MarkerState $x)) { return $true }
    }
    $false
}

function Wait-GpuWorkerOutcome($Worker, [string]$StatePath) {
    <# Прохід віддав GPU процесові наряду, а інші GPU-позначки стоять за ним. Чекаємо його перший результат: EXITED —
    процес скінчився (звірка пішла в WAIT, замок зайнятий: GPU вільна, наступна позначка проходу може її брати);
    RUNNING — модель стартувала (GPU тримає наряд); TIMEOUT — досі готується (залишаємо GPU за ним, як і раніше).
    Вимір 07.11: p1 щопроходу йшла в чекання за секунди, а решта GPU-позначок проходу стояла «її щойно взяв наряд». #>
    $until = (Get-Date).AddSeconds($script:GpuStartWaitSeconds)
    while ($true) {
        if ($Worker.Proc.HasExited) { return 'EXITED' }
        if (Test-RunStarted $StatePath) { return 'RUNNING' }
        if ((Get-Date) -ge $until) { return 'TIMEOUT' }
        Invoke-HealthBeat
        Start-Sleep -Milliseconds $script:GpuStartPollMs
    }
}

# Теки `аудит/` від третього рівня з відстежуваними файлами від 8 МіБ — архіви прогонів, проб і перевірок: копія задачі
# їх не викладає (main 29.10: 29 тек, у копії 247 МБ із 1353). Тека, названа в наряді, лишається; іншу сесія додає
# сама — `git sparse-checkout add '/<тека>/'`.
$script:ArchiveDirBytes = 8MB
$script:TaskCopy = $null

function Get-ArchiveDirs([string]$Commit, [string]$TaskText) {
    <# Теки-архіви коміту згори вниз; частковий клон не міряємо: `ls-tree -l` довантажив би всі об'єкти. #>
    if ((Invoke-Git @('config', '--get', 'remote.origin.promisor') -AllowFail).Out.Trim() -eq 'true') { return }
    $r = Invoke-Git @('ls-tree', '-r', '-l', '-z', $Commit, '--', 'аудит') -AllowFail
    if ($r.Code -ne 0) { return }
    $size = New-Object 'System.Collections.Generic.Dictionary[string,long]' ([StringComparer]::Ordinal)
    foreach ($e in $r.Out.Split([char]0)) {
        if ($e -notmatch '^[0-7]{6} blob [0-9a-f]{40,64} +([0-9]+)\t(.+)$') { continue }
        $bytes = [long]$Matches[1]; $path = $Matches[2]; $i = -1; $depth = 0
        while (($i = $path.IndexOf('/', $i + 1)) -ge 0) {
            $depth++
            if ($depth -lt 3) { continue }
            $d = $path.Substring(0, $i); $v = 0L
            [void]$size.TryGetValue($d, [ref]$v); $size[$d] = $v + $bytes
        }
    }
    $named = @(foreach ($m in [regex]::Matches($TaskText, '`([^`\r\n]+)`')) { (($m.Groups[1].Value.Trim() -replace '\\', '/') -replace '^\./', '').TrimEnd('/') })
    $out = New-Object System.Collections.Generic.List[string]
    foreach ($d in @($size.Keys | Where-Object { $size[$_] -ge $script:ArchiveDirBytes } | Sort-Object { $_.Split('/').Count }, { $_ })) {
        $keep = $false
        foreach ($x in $out) { if ($d.StartsWith($x + '/', [StringComparison]::Ordinal)) { $keep = $true } }
        foreach ($n in $named) { if ($n -ceq $d -or $n.StartsWith($d + '/', [StringComparison]::Ordinal)) { $keep = $true } }
        if (-not $keep) { $out.Add($d) }
    }
    $out
}

function ConvertTo-SparseSkip([string]$Dir) {
    <# Шаблон sparse-checkout (синтаксис .gitignore), що не викладає теку; спецсимволи шаблону екрановано. #>
    '!/' + ($Dir -replace '([\\*?\[])', '\$1') + '/'
}

function New-TaskCopy([string]$Dir, [string]$Commit, [string]$TaskText) {
    <# Тека задачі: `repo` — git worktree клону (спільні об'єкти й посилання) без тек-архівів, `tmp` — TEMP і TMP процесу
    наряду та його нащадків. Далі git і рушій працюють у копії ($RepoDir); повертає її шлях, закриває Close-TaskCopy. #>
    $repo = Join-Path $Dir 'repo'; $tmp = Join-Path $Dir 'tmp'
    [void][IO.Directory]::CreateDirectory($tmp)
    $script:TaskCopy = @{ Dir = $Dir; Clone = $RepoDir; Temp = $env:TEMP; Tmp = $env:TMP }
    [void](Invoke-Git @('worktree', 'prune') -AllowFail)
    [void](Invoke-Git @('worktree', 'add', '-q', '-f', '--no-checkout', '--detach', $repo, $Commit))
    # sparse-checkout у worktree лише з git 2.36: раніший писав `core.sparseCheckout` у спільний конфіг клону, а
    # `--no-cone` з'явився в 2.35. Старіший git — копія повна, але так само прибирається після доставки.
    $v = [regex]::Match([string](Invoke-Git @('version') -AllowFail).Out, '([0-9]+)\.([0-9]+)')
    $skip = @()
    if ($v.Success -and [int]$v.Groups[1].Value * 1000 + [int]$v.Groups[2].Value -ge 2036) {
        $skip = @(Get-ArchiveDirs $Commit $TaskText)
        $sp = Invoke-Git (@('sparse-checkout', 'set', '--no-cone', '/*') + @(foreach ($d in $skip) { ConvertTo-SparseSkip $d })) -AllowFail -Dir $repo
        if ($sp.Code -ne 0) {
            Write-Log "копія задачі: sparse-checkout не вдався — повна ($($sp.Err.Trim()))"
            [void](Invoke-Git @('sparse-checkout', 'disable') -AllowFail -Dir $repo)
            $skip = @()
        }
    } else { Write-Log "копія задачі: git до 2.36 — повна ($([string]$v.Value))" }
    [void](Invoke-Git @('reset', '-q', '--hard') -Dir $repo)
    Set-Variable -Scope Script -Name RepoDir -Value $repo
    $env:TEMP = $tmp; $env:TMP = $tmp
    Write-Log "копія задачі $repo ($Commit): тек-архівів не викладено — $($skip.Count)"
    $repo
}

function Get-AttemptStart([string]$BranchSha, [string]$Main) {
    <# Старт нової спроби наряду: що береться за основу, коли гілка попередньої спроби вже є на origin. Нема гілки чи
    її голова — предок main (усе злито, пуш нової голови лишається швидким вперед) — основа main, `NEW`/`MERGED`; голова
    вже містить main — гілка як є, `CURRENT`; інакше гілка, куди перед агентом вливається main, `BEHIND`. Спільне для
    смуг: gemini_run.ps1 (Invoke-Job) і claude_run.ps1 (Invoke-Task). #>
    if (-not $BranchSha) { return [pscustomobject]@{ Start = $Main; Mode = 'NEW' } }
    $r = Invoke-Git @('merge-base', '--is-ancestor', $BranchSha, $Main) -AllowFail
    if ($r.Code -gt 1) { throw "git merge-base --is-ancestor $BranchSha $Main -> $($r.Code): $($r.Err.Trim())" }
    if ($r.Code -eq 0) { return [pscustomobject]@{ Start = $Main; Mode = 'MERGED' } }
    $r = Invoke-Git @('merge-base', '--is-ancestor', $Main, $BranchSha) -AllowFail
    if ($r.Code -gt 1) { throw "git merge-base --is-ancestor $Main $BranchSha -> $($r.Code): $($r.Err.Trim())" }
    [pscustomobject]@{ Start = $BranchSha; Mode = $(if ($r.Code -eq 0) { 'CURRENT' } else { 'BEHIND' }) }
}

function Merge-MainIntoCopy([string]$Main, [string]$Branch) {
    <# У копії задачі ($RepoDir, на гілці) вливає $Main комітом злиття. Повертає голову після злиття; конфлікт чи інший
    збій — `merge --abort`, копія лишається на голові гілки, повертається ''. #>
    $before = Get-RefSha 'HEAD'
    $msg = "Обгортка: влито origin/main у $Branch перед спробою наряду (гілка відстала від main)"
    $r = Invoke-Git @('-c', 'user.name=Обгортка Люстерка', '-c', 'user.email=wrapper@users.noreply.github.com', '-c', 'commit.gpgsign=false',
        'merge', '--no-ff', '-q', '-m', $msg, $Main) -AllowFail
    if ($r.Code -eq 0) { return (Get-RefSha 'HEAD') }
    Write-Log "злиття main у $Branch не вдалося — $(($r.Out + $r.Err).Trim() -replace '\s+', ' ')"
    [void](Invoke-Git @('merge', '--abort') -AllowFail)
    if ((Get-RefSha 'HEAD') -cne $before) { [void](Invoke-Git @('reset', '-q', '--hard', $before)) }
    ''
}

function Get-MergeStepText([string]$Branch) {
    <# Крок промпту, коли обгортка не влила main сама (конфлікт) чи гілку веде агент: він вливає main першим кроком. #>
    "Перший крок: влий свіжий ``origin/main`` у ``$Branch`` (``git merge origin/main``), конфлікти розв'язуй за змістом ``main``: гілка " +
    "відстала від ``main``, тож код, який у ``main`` уже змінено чи прибрано, не лагодь і не відновлюй. Далі — наряд."
}

function Get-TaskDirText([string]$TaskDir) {
    <# Рядок промпту про теку задачі (без теки — ''). #>
    if (-not $TaskDir) { return '' }
    "Тека задачі — ``$TaskDir``: робоча копія ``repo`` (поточна тека) і ``tmp`` (туди вже вказують TEMP і TMP). Клонів`n" +
    "і копій репозиторію поза нею не роби; теки-архіви ``аудит/`` не викладено — потрібну додай ``git sparse-checkout add '/<тека>/'``.`n" +
    "Після кінця прогону обгортка теку прибирає: лишається лише закомічене."
}

function Close-TaskCopy([string[]]$Delivered) {
    <# Після доставки: $RepoDir і TEMP/TMP — як до копії, копія — геть (Remove-TaskCopy). Повертає шлях теки, що
    лишилась із недоставленими комітами, або ''. #>
    $c = $script:TaskCopy
    if ($null -eq $c) { return '' }
    $script:TaskCopy = $null
    Set-Variable -Scope Script -Name RepoDir -Value $c.Clone
    $env:TEMP = $c.Temp; $env:TMP = $c.Tmp
    Remove-TaskCopy $c.Dir $Delivered
}

function Remove-TaskCopy([string]$Dir, [string[]]$Delivered) {
    <# Тека задачі чи давня робоча копія слота — геть, коли голова не несе комітів поза $Delivered (`rev-list --not`).
    Несе — тека лишається з `kept.txt`, гілку звільнено, повертає шлях теки; інакше ''. #>
    $repo = $(if (Test-Path -LiteralPath (Join-Path $Dir '.git')) { $Dir } else { Join-Path $Dir 'repo' })
    if (Test-Path -LiteralPath (Join-Path $repo '.git')) {
        $n = 0
        $r = Invoke-Git (@('rev-list', '--count', 'HEAD', '--not') + $Delivered) -AllowFail -Dir $repo
        if ($r.Code -eq 0 -and [int]::TryParse($r.Out.Trim(), [ref]$n) -and $n -gt 0) {
            [void](Invoke-Git @('checkout', '-q', '--detach') -AllowFail -Dir $repo)
            [IO.File]::WriteAllText((Join-Path $Dir 'kept.txt'), "недоставлених комітів голови: $n`n", $script:Utf8)
            Write-Log "копія задачі $Dir лишається: недоставлених комітів голови $n"
            return $Dir
        }
        [void](Invoke-Git @('worktree', 'remove', '-f', '-f', $repo) -AllowFail)
    }
    if (Test-Path -LiteralPath $Dir) {
        try { Remove-Item -LiteralPath $Dir -Recurse -Force -ErrorAction Stop } catch { Write-Log "копія задачі $Dir не прибрана: $($_.Exception.Message)" }
    }
    [void](Invoke-Git @('worktree', 'prune') -AllowFail)
    ''
}

function Clear-TaskCopies([string]$Root, [string[]]$Delivered) {
    <# Накопичене під $Root: копії задач і давні робочі копії слотів, яких не тримає зайнятий слот (замок і `copy` у
    `<слот>.json`) і без `kept.txt`, — геть за Remove-TaskCopy. Теки читаються до замків: нова копія з'являється вже
    після запису `<слот>.json`. #>
    $dirs = @(Get-ChildItem -LiteralPath $Root -Directory -ErrorAction SilentlyContinue)
    $busy = @{}
    foreach ($l in @(Get-ChildItem -LiteralPath $script:SlotDir -Filter '*.lock' -File -ErrorAction SilentlyContinue)) {
        if (Test-LockFree $l.FullName) { continue }
        $slot = [IO.Path]::GetFileNameWithoutExtension($l.Name)
        $busy[$slot] = $true
        try {
            $copy = [string](Get-JsonProp ([IO.File]::ReadAllText((Join-Path $script:SlotDir "$slot.json"), $script:Utf8) | ConvertFrom-Json) 'copy')
            if ($copy) { $busy[(Split-Path -Leaf $copy)] = $true }
        } catch { $null = $_ }
    }
    foreach ($d in $dirs) {
        if ($busy.ContainsKey($d.Name) -or (Test-Path -LiteralPath (Join-Path $d.FullName 'kept.txt'))) { continue }
        Write-Log "накопичене: $($d.FullName) прибирається"
        [void](Remove-TaskCopy $d.FullName $Delivered)
    }
}

function Get-AutoTaskPath([string]$Slug) {
    <# Лише два закриті шаблони нарядів із main; довільний slug лишається звичайним нарядом. #>
    if ($Slug -cmatch '^автоперевірка-[1-9][0-9]{0,8}-[0-9a-f]{40}$') { return 'аудит/наряди/автоперевірка.md' }
    if ($Slug -cmatch '^(?:автоживий-[0-9a-f]{40}|Е1-нічний-живий-[0-9]{8})$') { return 'аудит/наряди/автоживий.md' }
    $script:TaskDir + $Slug + '.md'
}

function Get-AutoPublicItems([string]$Path, [int]$PerPage = 100, [int]$MaxPages = 100, [scriptblock]$StopAfterPage = $null, [switch]$Budgeted) {
    <# Пагінує публічний GET; збій не стає порожнім успішним входом. StopAfterPage отримує елементи щойно прочитаної
    сторінки й повертає $true, коли далі читати не треба (порядок сторінок і доказ зупинки — на викликачі). Budgeted —
    кожен запит бере один із спільного бюджету review-api.json (нема — AUTO_BUDGET, у мережу не йдемо). Усі спроби
    запиту лічить $script:AutoApiCalls. #>
    for ($page = 1; $page -le $MaxPages; $page++) {
        if ($Budgeted -and -not (Use-AutoApiBudget)) { throw 'AUTO_BUDGET' }
        $script:AutoApiCalls++
        $separator = if ($Path.Contains('?')) { '&' } else { '?' }
        try {
            $data = Invoke-RestMethod -Uri ("https://api.github.com/repos/mightyrochy/kod-shi-data/$Path" + $separator + "per_page=$PerPage&page=$page") -Method Get -TimeoutSec 20 -MaximumRedirection 0 -Headers @{Accept='application/vnd.github+json'; 'User-Agent'='kod-shi-wrapper'}
        } catch {
            if ($Budgeted) { Set-AutoApiPause }
            throw
        }
        $items = @($data)
        foreach ($item in $items) { $item }
        if ($items.Count -lt $PerPage) { return }
        if ($null -ne $StopAfterPage) {
            $stop = @(& $StopAfterPage $items)
            if ($stop.Count -gt 0 -and $stop[-1]) { return }
        }
    }
    throw 'AUTO_PAGES'
}

function Get-AutoReviewInput([string]$Number) {
    <# Рецензії та inline зауваження лише Codex; відповідь чужому не входить. #>
    $result = @()
    foreach ($item in @(Get-AutoPublicItems "pulls/$Number/reviews")) {
        if ($item.user.login -ceq 'chatgpt-codex-connector[bot]') {
            $result += @{kind='review';id=$item.id;body=$item.body;commit=$item.commit_id}
        }
    }
    $comments = @(Get-AutoPublicItems "pulls/$Number/comments")
    foreach ($item in $comments) {
        if ($item.user.login -cne 'chatgpt-codex-connector[bot]') { continue }
        $reply = $item.PSObject.Properties['in_reply_to_id']
        if ($null -ne $reply -and $reply.Value) {
            $parent = @($comments | Where-Object { $_.id -eq $reply.Value -and $_.user.login -cin @('mightyrochy','chatgpt-codex-connector[bot]') })
            if (-not $parent.Count) { continue }
        }
        $result += @{kind='inline';id=$item.id;path=$item.path;body=$item.body;commit=$item.commit_id}
    }
    ConvertTo-Json -InputObject @($result) -Depth 6 -Compress
}

function Get-LiveSceneRegistry([string]$Text) {
    <# Реєстр `аудит/проби/живі_сцени.txt`: id — перше поле до «|», режим — п'яте; рядки `#` і короткі пропущено. #>
    $registry = @{}
    foreach ($row in ($Text -split "`n")) {
        $row = $row.TrimEnd("`r").TrimStart([char]0xFEFF)
        if (-not $row.Trim() -or $row.TrimStart().StartsWith('#')) { continue }
        $fields = $row.Split('|')
        if ($fields.Count -lt 5) { continue }
        $registry[$fields[0].Trim()] = $fields[4].Trim()
    }
    $registry
}

function Get-LiveAfterLines([string]$Body, $Registry) {
    <# Єдиний розбір рядків `ЖИВИЙ ПІСЛЯ: <id> — <питання>` для планувальника й CI на тілі PR. Рядок, що починається з
    `ЖИВИЙ ПІСЛЯ` (після пробілів, маркера списку чи виділення), або розібрано повністю, або в ньому `error`. #>
    $result = @()
    $lines = @([string]$Body -split "`n")
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i].Trim()
        if ($line -cnotmatch '^[-*+>#_\s]*ЖИВИЙ ПІСЛЯ') { continue }
        $first = $i
        # Звичайне продовження того самого абзацу склеюємо. Межі Markdown, новий рядок
        # протоколу й підпис поля не поглинаємо: вони не можуть дописати id чи питання.
        while ($i + 1 -lt $lines.Count) {
            $next = $lines[$i + 1].Trim()
            if (-not $next -or $next -cmatch '^(?:ЖИВИЙ ПІСЛЯ|[-*+>#_`~]|\d+[.)]\s|\p{Lu}[^:]*:|\|)') { break }
            $line += ' ' + $next
            $i++
        }
        $item = @{line=$line;first=$first;last=$i;id='';question='';mode='';error=''}
        if ($line -cnotmatch '^ЖИВИЙ ПІСЛЯ: (.*)$') {
            $item.error = 'рядок має починатися з «ЖИВИЙ ПІСЛЯ: » без маркера списку, виділення чи пропущеної двокрапки'
        } else {
            $rest = $Matches[1]
            $at = $rest.IndexOf(' — ', [StringComparison]::Ordinal)
            if ($at -lt 0) {
                $item.error = 'нема « — » після id'
            } else {
                $id = $rest.Substring(0, $at).Trim()
                $question = $rest.Substring($at + 3).Trim()
                if ($id -cnotmatch '^[\p{L}\p{Nd}_-]+$') {
                    $item.error = 'id «' + $id + '» не голий: лише літери, цифри, _ і -, без лапок, зворотних лапок і пояснень'
                } elseif (-not ($Registry.Keys -ccontains $id)) {
                    $item.error = 'id «' + $id + '» нема першим полем аудит/проби/живі_сцени.txt'
                } elseif (-not $question) {
                    $item.error = 'порожнє питання після « — »'
                } else {
                    $item.id = $id; $item.question = $question; $item.mode = [string]$Registry[$id]
                }
            }
        }
        $result += @($item)
    }
    $result
}

function ConvertTo-LivePublicationBody([string]$Body, $Registry) {
    <# Готує тіло тим самим читачем, зберігаючи ваду й оригінал без виконуваного префікса. #>
    $items = @(Get-LiveAfterLines $Body $Registry)
    $lines = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in @($Body -split "`n")) { $lines.Add($line.TrimEnd("`r")) }
    $bad = @($items | Where-Object { $_.error })
    foreach ($item in @($items | Sort-Object first -Descending)) {
        $replacement = $item.line
        if ($item.error) { $replacement = "Вадний рядок живого прогону: $($item.error); оригінал: $($item.line)" }
        $lines.RemoveRange($item.first, $item.last - $item.first + 1)
        $lines.Insert($item.first, $replacement)
    }
    if ($bad.Count) {
        $lines.Add('')
        $lines.Add('ЗАБЛОКОВАНО: LIVE_AFTER_INVALID — ' + (($bad | ForEach-Object { $_.error }) -join '; '))
    }
    [pscustomobject]@{ Body=($lines -join "`n"); Bad=$bad }
}

function Merge-LivePublicationBody([string]$Body, [string]$ExistingBody, $Registry) {
    <# Зберігає питання чинного PR: одна сцена має один рядок із усіма різними питаннями. #>
    $items = @(Get-LiveAfterLines $Body $Registry)
    $previous = @(Get-LiveAfterLines $ExistingBody $Registry)
    $scenes = New-Object 'System.Collections.Generic.Dictionary[string,object]' ([StringComparer]::Ordinal)
    $order = New-Object 'System.Collections.Generic.List[string]'
    foreach ($item in @($items) + @($previous)) {
        if ($item.error) { continue }
        if (-not $scenes.ContainsKey($item.id)) {
            $scenes[$item.id] = @{first=-1;questions=@()}
            $order.Add($item.id)
        }
        foreach ($question in @($item.question -split ' ; ')) {
            if ($scenes[$item.id].questions -cnotcontains $question) { $scenes[$item.id].questions += $question }
        }
    }
    foreach ($item in $items) {
        if (-not $item.error -and $scenes[$item.id].first -lt 0) { $scenes[$item.id].first = $item.first }
    }
    $lines = New-Object 'System.Collections.Generic.List[string]'
    foreach ($line in @($Body -split "`n")) { $lines.Add($line.TrimEnd("`r")) }
    foreach ($item in @($items | Sort-Object first -Descending)) {
        if ($item.error) { continue }
        $scene = $scenes[$item.id]
        $lines.RemoveRange($item.first, $item.last - $item.first + 1)
        if ($scene.first -eq $item.first) {
            $lines.Insert($item.first, ('ЖИВИЙ ПІСЛЯ: ' + $item.id + ' — ' + ($scene.questions -join ' ; ')))
        }
    }
    foreach ($id in $order) {
        if ($scenes[$id].first -lt 0) {
            $lines.Add('')
            $lines.Add('ЖИВИЙ ПІСЛЯ: ' + $id + ' — ' + ($scenes[$id].questions -join ' ; '))
        }
    }
    # Вада старого тіла також проходить спільне пояснення й блокер, а не зникає під час PATCH.
    foreach ($item in @($previous | Where-Object { $_.error })) {
        $lines.Add('')
        $lines.Add($item.line)
    }
    ConvertTo-LivePublicationBody ($lines -join "`n") $Registry
}

function Get-HeadLivePublication([string]$Head, [string]$ExistingBody = '') {
    <# Читає коміт і реєстр із довіреної бази перед прийманням звіту або записом тіла PR. #>
    $body = (Invoke-Git @('show','-s','--format=%B',$Head)).Out
    if (($body + "`n" + $ExistingBody) -cnotmatch '(?m)^[-*+>#_\s]*ЖИВИЙ ПІСЛЯ') {
        return (ConvertTo-LivePublicationBody $body @{})
    }
    $registryText = (Invoke-Git @('show', 'refs/remotes/origin/main:аудит/проби/живі_сцени.txt')).Out
    $registry = Get-LiveSceneRegistry $registryText
    if (-not $registry.Count) { throw 'LIVE_AFTER_REGISTRY' }
    # Повний рядок сцени — стільки полів, скільки в шапці реєстру «# Поля: …»; коротший рядок гілки не додаємо.
    $header = @(($registryText -split "`n") | Where-Object { $_.TrimStart([char]0xFEFF).StartsWith('# Поля:') })
    if (-not $header.Count) { throw 'LIVE_AFTER_REGISTRY' }
    $width = $header[0].TrimEnd("`r").Split('|').Count
    # Лише додані рядки від спільної бази: зміни й видалення сцен main не змінюють їхній режим.
    $base = (Invoke-Git @('merge-base', 'refs/remotes/origin/main', $Head)).Out.Trim()
    if (-not $base) { throw 'LIVE_AFTER_MERGE_BASE' }
    $baseRegistry = Get-LiveSceneRegistry ((Invoke-Git @('show', ($base + ':аудит/проби/живі_сцени.txt'))).Out)
    $diff = (Invoke-Git @('diff', '--no-ext-diff', '--unified=0', $base, $Head, '--', 'аудит/проби/живі_сцени.txt')).Out
    foreach ($line in ($diff -split "`n")) {
        if (-not $line.StartsWith('+') -or $line.StartsWith('+++')) { continue }
        $row = $line.Substring(1).TrimEnd("`r").TrimStart([char]0xFEFF)
        if (-not $row.Trim() -or $row.TrimStart().StartsWith('#')) { continue }
        $fields = $row.Split('|')
        if ($fields.Count -lt $width -or -not $fields[0].Trim()) { continue }
        $added = Get-LiveSceneRegistry $row
        foreach ($id in $added.Keys) {
            if (-not $registry.ContainsKey($id) -and -not $baseRegistry.ContainsKey($id)) { $registry[$id] = $added[$id] }
        }
    }
    Merge-LivePublicationBody $body $ExistingBody $registry
}

function Get-LiveCorrectionPrompt($Publication) {
    <# Дає тому самому виконавцю один хід із причинами та точним форматом. #>
    $details = ($Publication.Bad | ForEach-Object { "Вада: $($_.error)`nРядок: $($_.line)" }) -join "`n"
    "Тіло останнього коміту не розбирається до публікації PR.`n$details`n" +
        'Один хід на виправлення в тій самій гілці й тому самому наряді. Формат: ЖИВИЙ ПІСЛЯ: <id> — <питання правки> → <режим> → <ДО звідки> → <що вважати кращим>. ' +
        'id — голе перше поле аудит/проби/живі_сцени.txt; одна сцена — один рядок. Закоміть виправлений звіт; останній рядок — за адаптером.'
}

function Test-AutoTrustedPull($Pull) {
    <# PR довіреного автора з цього репозиторію в main: лише такі читає план живого. #>
    $Pull.user.login -ceq 'mightyrochy' -and $null -ne $Pull.head.repo -and $Pull.head.repo.full_name -ceq 'mightyrochy/kod-shi-data' -and
        $Pull.base.repo.full_name -ceq 'mightyrochy/kod-shi-data' -and $Pull.base.ref -ceq 'main'
}

function ConvertTo-AutoTime($Value) {
    <# Час із відповіді GitHub: PowerShell 5.1 дає рядок, 7 — DateTime; обидва в UTC-момент. #>
    if ($Value -is [datetimeoffset]) { return $Value }
    if ($Value -is [datetime]) {
        $utc = $(if ($Value.Kind -eq [DateTimeKind]::Unspecified) { [datetime]::SpecifyKind($Value, [DateTimeKind]::Utc) } else { $Value.ToUniversalTime() })
        return [datetimeoffset]::new($utc)
    }
    [datetimeoffset]::Parse([string]$Value, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal)
}

function Get-AutoCheckedBuild($Pulls, $History) {
    <# Збірка, яку перевірив найновіший звіт (`автоживий-<штамп>` чи `Е1-нічний-живий-<дата>`): найближча до голови в історії.
    Звіт з кількома `ПЕРЕВІРЕНО ЗБІРКУ` не береться; старий нічний звіт без SHA нічого не відсікає. #>
    $checked = ''
    foreach ($report in $Pulls) {
        if ([string]$report.head.ref -cnotmatch '^(?:gemini|claude|codex)/(?:автоживий-([0-9a-f]{40})|Е1-нічний-живий-[0-9]{8})$') { continue }
        $stamp = [string]$Matches[1]
        $declared = [regex]::Matches([string]$report.body, '(?m)^ПЕРЕВІРЕНО ЗБІРКУ: ([0-9a-f]{40})\r?$')
        if ($declared.Count -gt 1) { continue }
        $candidate = if ($declared.Count -eq 1) { $declared[0].Groups[1].Value } else { $stamp }
        # Старий нічний звіт без SHA не може відсікти неперевірений код.
        if ($candidate -and $History.ContainsKey($candidate) -and
            (-not $checked -or $History[$candidate] -lt $History[$checked])) { $checked = $candidate }
    }
    $checked
}

function Get-AutoLivePlan([string]$BuildMain) {
    <# Один план для автоживого й Е1: сцена один раз, питання всіх злитих довірених PR.
    Список `pulls` іде за оновленням від найновішого й читається лише до доведеної межі: звіт не може згадати збірку,
    що старша за його оновлення, а злиття, якого збірка звіту ще не містить, не старше за неї — тож, коли остання
    прочитана сторінка старіша за збірку найновішого звіту (мінус запас), решта PR плану не змінить. Те саме, що читати
    всі сторінки, але ~7 запитів замість 33. Не дійшли до межі за AutoPlanMaxPages сторінок — AUTO_PAGES, плану нема. #>
    $calls0 = $script:AutoApiCalls
    $until = [datetimeoffset]::Parse((Invoke-Git @('show','-s','--format=%cI',$BuildMain)).Out.Trim())
    # Час звіту не визначає склад прогону: PR міг злитися, поки модель ще працювала.
    $history = @{}
    $rank = 0
    foreach ($commit in ((Invoke-Git @('rev-list','--topo-order',$BuildMain,'--')).Out -split "`n")) {
        if ($commit.Trim()) { $history[$commit.Trim()] = $rank; $rank++ }
    }
    $planScan = @{ Seen = (New-Object System.Collections.ArrayList); Dates = @{}; Pages = 0 }
    $planStop = {
        param($pagePulls)
        $planScan.Pages++
        foreach ($one in @($pagePulls)) { if (Test-AutoTrustedPull $one) { [void]$planScan.Seen.Add($one) } }
        $reportBuild = Get-AutoCheckedBuild $planScan.Seen $history
        if (-not $reportBuild) { return $false }
        if (-not $planScan.Dates.ContainsKey($reportBuild)) {
            $planScan.Dates[$reportBuild] = [datetimeoffset]::Parse((Invoke-Git @('show','-s','--format=%cI',$reportBuild)).Out.Trim())
        }
        $lastUpdate = @($pagePulls)[-1].PSObject.Properties['updated_at']
        if ($null -eq $lastUpdate -or $null -eq $lastUpdate.Value) { return $false }
        (ConvertTo-AutoTime $lastUpdate.Value) -lt $planScan.Dates[$reportBuild].AddHours(-$script:AutoPlanMarginHours)
    }
    $pulls = @(Get-AutoPublicItems 'pulls?state=all&sort=updated&direction=desc' -PerPage $script:AutoPlanPerPage -MaxPages $script:AutoPlanMaxPages -StopAfterPage $planStop -Budgeted | Where-Object { Test-AutoTrustedPull $_ })
    $checked = Get-AutoCheckedBuild $pulls $history
    $since = [datetimeoffset]::MinValue
    $covered = @{}
    if ($checked) {
        $since = [datetimeoffset]::Parse((Invoke-Git @('show','-s','--format=%cI',$checked)).Out.Trim())
        foreach ($commit in ((Invoke-Git @('rev-list',$checked,'--')).Out -split "`n")) {
            if ($commit.Trim()) { $covered[$commit.Trim()] = $true }
        }
    }
    $registryText = (Invoke-Git @('cat-file','blob',"${BuildMain}:аудит/проби/живі_сцени.txt")).Out
    $registry = Get-LiveSceneRegistry $registryText
    if (-not $registry.Count) { throw 'AUTO_REGISTRY' }
    $scenes = [ordered]@{}
    $cloud = [ordered]@{}
    $bad = @()
    foreach ($pr in @($pulls | Sort-Object merged_at,number)) {
        if (-not $pr.merged_at) { continue }
        $merge = [string]$pr.merge_commit_sha
        if ($merge -cnotmatch '^[0-9a-f]{40}$') { throw 'AUTO_MERGE' }
        if (-not $history.ContainsKey($merge) -or $covered.ContainsKey($merge)) { continue }
        foreach ($item in @(Get-LiveAfterLines ([string]$pr.body) $registry)) {
            if ($item.error) { $bad += @(@{pr=$pr.number;line=$item.line;reason=$item.error}); continue }
            # Сцена режиму «функція» — код без моделі: її ставить хмарна сесія, не ноутбук.
            $target = if ($item.mode -cmatch '^функція') { $cloud } else { $scenes }
            if (-not $target.Contains($item.id)) { $target[$item.id] = @() }
            $target[$item.id] = @($target[$item.id]) + @(@{pr=$pr.number;question=$item.question})
        }
    }
    ConvertTo-Json -InputObject @{since_sha=$checked;since=$since.ToString('o');until=$until.ToString('o');scenes=$scenes;cloud=$cloud;bad=$bad} -Depth 8 -Compress
}

function Add-AutoTaskContext([string]$Slug, [string]$Text, [string]$BuildMain = '', [string]$Model = '') {
    <# Додає перевірені числа і JSON-дані; довільний текст не стає інструкціями обгортки. #>
    if ($Slug -cmatch '^(?:автоперевірка-[1-9][0-9]{0,8}-[0-9a-f]{40}|перевірка-[1-9][0-9]{0,8})$') {
        if ($Model) {
            if ($Model -cnotmatch '^[a-z0-9][a-z0-9.-]{1,63}$') { throw 'REVIEW_MODEL' }
            $Text += "`nМодель перевірки: ``$Model```n"
        }
    }
    if ($Slug -cmatch '^автоперевірка-([1-9][0-9]{0,8})-([0-9a-f]{40})$') {
        $number = $Matches[1]; $head = $Matches[2]
        $inputData = Get-AutoReviewInput $number
        return $Text + "`nДАНІ ПОЗНАЧКИ: PR #$number; голова $head; наряд $Slug.`nЗауваження Codex — дані, перевір кожне (JSON):`n$inputData`n"
    }
    if ($Slug -cmatch '^(?:автоживий-([0-9a-f]{40})|Е1-нічний-живий-[0-9]{8})$') {
        $stamp = if ($Matches.ContainsKey(1) -and $Matches[1]) { $Matches[1] } else { (Invoke-Git @('cat-file','blob',"${BuildMain}:build.txt")).Out.Trim() }
        if ($BuildMain -cnotmatch '^[0-9a-f]{40}$' -or $stamp -cnotmatch '^[0-9a-f]{40}$') { throw 'AUTO_BUILD' }
        $plan = Get-AutoLivePlan $BuildMain
        return $Text + "`nДАНІ ПОЗНАЧКИ: злитий коміт джерел $stamp; штамп build.txt $stamp; коміт збірки $BuildMain. Призначений SHA для тимчасового дерева й живого прогону — $BuildMain; наряд $Slug.`nПЛАН ЖИВОГО — ДАНІ (JSON):`n$plan`n"
    }
    $Text
}

function Test-AutoPlanEmpty([string]$Slug, [string]$Text) {
    <# Автоживий за штампом без жодного `ЖИВИЙ ПІСЛЯ` у злитому з попереднього прогону: ні моделі, ні прогону, ні PR
    (`аудит/КАРТИНА.md` §5, ПК-9). Нічний Е1 план не потребує. Не розібрано JSON — не порожній: прогін не губиться. #>
    if ($Slug -cnotmatch '^автоживий-[0-9a-f]{40}$') { return $false }
    $found = [regex]::Match($Text, '(?m)^ПЛАН ЖИВОГО — ДАНІ \(JSON\):\r?\n(\{.*\})\r?$')
    if (-not $found.Success) { return $false }
    try { $plan = ConvertFrom-Json $found.Groups[1].Value } catch { return $false }
    $scenes = $plan.PSObject.Properties['scenes']
    if ($null -eq $scenes -or @($scenes.Value.PSObject.Properties).Count -ne 0) { return $false }
    # Сцени «у хмарі» й вадні рядки теж потрібно донести до звіту: з ними план не порожній.
    $cloud = $plan.PSObject.Properties['cloud']
    if ($null -ne $cloud -and @($cloud.Value.PSObject.Properties).Count -ne 0) { return $false }
    $bad = $plan.PSObject.Properties['bad']
    -not ($null -ne $bad -and @($bad.Value).Count -ne 0)
}

function Set-BrowserGpuPolicy([string]$Directory) {
    <# Усі дочірні Node/Python Chromium працюють без GPU, включно з довільними пробами агента. #>
    [void][IO.Directory]::CreateDirectory($Directory)
    $node = Join-Path $Directory 'browser.cjs'
    Write-FileAtomic $node @'
const Module = require('module');
const load = Module._load;
const seen = new WeakSet();
Module._load = function (...args) {
  const result = load.apply(this, args);
  const chromium = result && result.chromium;
  if (chromium && !seen.has(chromium)) {
    seen.add(chromium);
    for (const name of ['launch', 'launchPersistentContext']) {
      const original = chromium[name];
      chromium[name] = function (...values) {
        const i = name === 'launch' ? 0 : 1;
        const options = values[i] || {};
        values[i] = {...options, args: [...(options.args || []), '--disable-gpu']};
        return original.apply(this, values);
      };
    }
  }
  return result;
};
'@
    $python = Join-Path $Directory 'sitecustomize.py'
    Write-FileAtomic $python @'
import builtins
import functools
_import = builtins.__import__
_seen = set()
def _gpu_import(name, *args, **kwargs):
    result = _import(name, *args, **kwargs)
    if name in ('playwright.sync_api', 'playwright.async_api'):
        import sys
        module = sys.modules.get(name)
        cls = getattr(module, 'BrowserType', None)
        if cls is not None and cls not in _seen:
            _seen.add(cls)
            for method in ('launch', 'launch_persistent_context'):
                original = getattr(cls, method)
                def decorate(fn):
                    @functools.wraps(fn)
                    def launch(*a, **kw):
                        kw['args'] = [*(kw.get('args') or []), '--disable-gpu']
                        return fn(*a, **kw)
                    return launch
                setattr(cls, method, decorate(original))
    return result
builtins.__import__ = _gpu_import
'@
    $env:NODE_OPTIONS = ($env:NODE_OPTIONS + ' --require "' + $node.Replace('\','/') + '"').Trim()
    $env:PYTHONPATH = $Directory + [IO.Path]::PathSeparator + $env:PYTHONPATH
}

function Get-GpuTelemetry {
    <# Один знімок вільної пам'яті й обчислень єдиної карти; невідомі дані не означають простій.
    Місткості різних карт не складаємо: цей вимір і бюджет стосуються єдиної RTX 4090 ноутбука. #>
    $errorResult = [pscustomobject]@{ Error = 'nvidia-smi не відповів'; TotalMiB = 0; FreeMiB = 0; Percent = 0 }
    $exe = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($null -eq $exe) { return $errorResult }
    $r = Invoke-Native $exe.Source @('--query-gpu=memory.total,memory.free,utilization.gpu', '--format=csv,noheader,nounits') '' 1
    if ($r.Code -ne 0) { return $errorResult }
    $lines = @($r.Out -split '\r?\n' | Where-Object { $_.Trim() })
    if ($lines.Count -gt 1) {
        $errorResult.Error = 'кілька GPU: потрібен вимір однієї карти'
        return $errorResult
    }
    if ($lines.Count -ne 1 -or $lines[0] -notmatch '^\s*([0-9]+)\s*,\s*([0-9]+)\s*,\s*([0-9]+)\s*$') { return $errorResult }
    $total = 0L; $free = 0L; $percent = 0
    if (-not [long]::TryParse($Matches[1], [ref]$total) -or -not [long]::TryParse($Matches[2], [ref]$free) -or
        -not [int]::TryParse($Matches[3], [ref]$percent) -or $total -le 0 -or $free -gt $total -or $percent -gt 100) { return $errorResult }
    [pscustomobject]@{ Error = ''; TotalMiB = $total; FreeMiB = $free; Percent = $percent }
}

function Test-GpuModelProcess([string]$Name, [string]$Path = '') {
    <# Чи це інструмент LM Studio: лише його виміряну пам'ять можна повторно використати в наряді.
    Робочий стіл і браузер також займають фізичну пам'ять, але потребу наряду не зменшують. #>
    $n = ([string]$Name -replace '(?i)\.exe$', '').Trim()
    if (-not $n) { return $false }
    if ($n -match '(?i)^(LM[ _]?Studio|lms|llmster)$') { return $true }
    [string]$Path -match '(?i)[\\/](LM[ _-]?Studio|\.lmstudio)[\\/]'
}

function Get-GpuCounterRows {
    <# Рядки лічильника (Name `pid_<PID>_luid_…_phys_<N>`, DedicatedUsage у байтах) — назви класу WMI не перекладаються, на
    відміну від шляху Get-Counter; $null — лічильника нема (не Windows 10 1709+ чи збій WMI). Стенд підміняє. #>
    if (-not $script:OnWindows) { return $null }
    try { , @(Get-CimInstance -ClassName 'Win32_PerfFormattedData_GPUPerformanceCounters_GPUProcessMemory' -ErrorAction Stop) } catch { $null }
}

function Get-GpuProcessInfo([int]$ProcessId) {
    <# Назва (як у Get-Process) і шлях процесу за PID; шляху процесу іншого
    облікового запису не видно — ''; процес уже вийшов — без назви. #>
    try { $p = Get-Process -Id $ProcessId -ErrorAction Stop } catch { return [pscustomobject]@{ Name = ''; Path = '' } }
    $path = ''
    try { $path = [string]$p.Path } catch { $path = '' }
    [pscustomobject]@{ Name = [string]$p.ProcessName; Path = $path }
}

function Get-GpuLoad {
    <# Єдине рішення за вільною VRAM і залишковою потребою наряду.
    Пам'ять неактивної LM Studio вже належить інструменту прогону; без лічильника процесів її не зараховуємо.
    Навантаження карти — показник журналу й причини нестачі памʼяті, без порога запуску. #>
    $gpu = Get-GpuTelemetry
    $required = [long]$script:GpuRunMiB
    $modelBytes = 0L
    if (-not $gpu.Error) {
        $rows = Get-GpuCounterRows
        $seen = @{}
        foreach ($row in @($rows)) {
            if ($null -eq $row -or [string]$row.Name -notmatch '^pid_([0-9]{1,10})_.*_phys_0$') { continue }
            $processId = 0; $bytes = 0L
            if (-not [int]::TryParse($Matches[1], [ref]$processId) -or
                -not [long]::TryParse([string]$row.DedicatedUsage, [ref]$bytes) -or $bytes -lt 0 -or $seen.ContainsKey([string]$row.Name)) { continue }
            $seen[[string]$row.Name] = $true
            $p = Get-GpuProcessInfo $processId
            if (Test-GpuModelProcess $p.Name $p.Path) {
                # Обмеження фізично зайнятою пам'яттю захищає від переповнення й розбіжності двох знімків.
                $modelBytes = [long][Math]::Min(($gpu.TotalMiB - $gpu.FreeMiB) * 1MB, $modelBytes + [double]$bytes)
            }
        }
        $required = [long][Math]::Max(0, $required - [Math]::Floor($modelBytes / 1MB))
    }
    $reason = [string]$gpu.Error
    if (-not $reason) {
        if ($gpu.FreeMiB -lt $required) { $reason = "вільно $($gpu.FreeMiB) з потрібних $required MiB; навантаження $($gpu.Percent) %" }
    }
    [pscustomobject]@{ FreeMiB = $gpu.FreeMiB; RequiredMiB = $required; Percent = $gpu.Percent; Reason = $reason }
}

function Test-ExternalGpuFree([switch]$LogAcquisition) {
    <# Те саме рішення для воркера після узяття замка: зміна стану карти повертає наряд у чергу.
    Журнал узяття містить показники того самого знімка, за яким дозволено старт. #>
    $load = Get-GpuLoad
    $free = $load.Reason -eq ''
    if ($free -and $LogAcquisition) {
        Write-Log "GPU взято: вільно $($load.FreeMiB) з потрібних $($load.RequiredMiB) MiB; навантаження $($load.Percent) %"
    }
    $free
}

function Get-GpuSessionReason {
    <# Чи тримають карту GPU-наряди: живий наряд обох облікових записів має на ній модель, завантажену після початку сесії
    (екземпляр LM Studio поза before), — зайнята; запис без живих оренд чи пошкоджений — прибирання ще не відбулось.
    Оренда без моделі карти не тримає: така карта ділиться за пам'яттю (Get-GpuLoad). '' — сесія не заважає. #>
    try { $s = Read-GpuSession } catch { $s = $false }
    if ($null -eq $s) { return '' }
    if ($false -eq $s -or @(Get-LiveGpuLeases $s).Count -eq 0) {
        $script:GpuHoldReason = 'незакритий знімок моделей GPU'
        return 'GPU: незакритий знімок моделей попереднього наряду (lanes/gpu-models.json)'
    }
    $before = @($s.Before | ForEach-Object { [string]$_.id })
    try { $new = @(Get-LmsInstances | Where-Object { $before -cnotcontains $_.id }) }
    catch {
        $script:GpuHoldReason = 'LM Studio недоступний на :1234'
        return 'GPU: LM Studio недоступний на :1234 — неможливо перевірити моделі живих GPU-нарядів'
    }
    if ($new.Count) {
        $script:GpuHoldReason = 'модель GPU-наряду на карті'
        return "GPU: модель GPU-наряду на карті ($(@($new | ForEach-Object { $_.model }) -join ', '))"
    }
    ''
}

$script:GpuHoldReason = ''

function Get-GpuBusyReason([switch]$LockHeld) {
    <# Чому GPU не віддати наряду зараз; '' — вільна. Єдине місце для планувальників обох облікових записів.
    GpuHoldReason — причина для рядка сигналу (Update-HoldSignals порівнює її без числових показників). LockHeld — ворота GPU
    тримає сам викликач (процес наряду в Enter-GpuLease): причина — сторонній процес, а не «замок тримає інший процес».
    Свій живий GPU-наряд сам по собі карти не тримає — лише його модель на карті (Get-GpuSessionReason) чи пам'ять. #>
    $script:GpuHoldReason = ''
    if (-not $LockHeld -and -not (Test-LockFree (Get-GpuLockPath))) { $script:GpuHoldReason = 'замок GPU іншого наряду'; return "GPU: замок $(Get-GpuLockPath) тримає інший процес" }
    $why = Get-GpuSessionReason
    if ($why) { return $why }
    try { $null = @(Get-LmsInstances) }
    catch {
        $script:GpuHoldReason = 'LM Studio недоступний на :1234'
        return 'GPU: LM Studio недоступний на :1234 — неможливо зберегти початкові екземпляри'
    }
    $load = Get-GpuLoad
    if ($load.Reason) {
        $script:GpuHoldReason = $load.Reason
        return "GPU: $($load.Reason)"
    }
    ''
}

# --- позначки, що стоять без старту ---------------------------------------------------------------------------------

$script:PassSkips = [ordered]@{}

function Read-JsonArray([string]$Path) {
    <# Елементи JSON-масиву з файла в конвеєр (викликач бере @(Read-JsonArray …)); нема файла чи не JSON — нічого.
    PowerShell 5.1 пише масив з ConvertFrom-Json у конвеєр одним об'єктом: @(… | ConvertFrom-Json) давав масив у масиві, і
    таблиця «Позначки без старту» в #1856 31.10 мала по рядку з порожніми клітинками на файл. #>
    try { $parsed = ConvertFrom-Json ([System.IO.File]::ReadAllText($Path, $script:Utf8)) } catch { return }
    foreach ($x in @($parsed)) { if ($null -ne $x) { $x } }
}

function Add-Skip($M, [string]$Why) {
    <# Позначку цього проходу не взято з названої причини; Save-Skips у кінці проходу пише журнал і файл для #1856. #>
    $script:PassSkips[[string]$M.Name] = $Why
}

function Save-Skips([string]$Path) {
    <# Файл «що стоїть і чому» (замінюється щопроходу); рядок журналу — лише коли причина нова для позначки: попередній
    файл несе `since`, бо процес планувальника живе недовго. #>
    $old = @{}
    foreach ($r in @(Read-JsonArray $Path)) { $old[[string](Get-JsonProp $r 'marker')] = $r }
    $now = Get-UtcStamp (Get-Date)
    $rows = @(foreach ($n in $script:PassSkips.Keys) {
        $why = [string]$script:PassSkips[$n]; $since = $now
        if ($old.ContainsKey($n) -and [string]$old[$n].why -ceq $why) { $since = [string]$old[$n].since }
        else { Write-Log "позначка ${n}: не стартує — $why" }
        [ordered]@{ marker = $n; why = $why; since = $since }
    })
    $script:PassSkips = [ordered]@{}
    Write-FileAtomic $Path (ConvertTo-Json -InputObject $rows -Compress)
}

function ConvertTo-NoteText([string]$Text) {
    <# Вільний текст причини (рядок агента, тема коміту ЗНЯТО) для приміток і результату: один рядок, без керівних
    символів, до 240 знаків. #>
    $clean = ([regex]::Replace($Text, '[\x00-\x1f\x7f]+', ' ')).Trim()
    if ($clean.Length -gt 240) { $clean = $clean.Substring(0, 240) }
    $clean
}

function Add-Note([string]$Path, [string]$Marker, [string]$Text) {
    <# Останні 12 приміток до #1856 (причина BLOCKED без гілки), текст — ConvertTo-NoteText. #>
    $rows = @(Read-JsonArray $Path)
    $clean = ConvertTo-NoteText $Text
    $rows = @($rows | Select-Object -Last 11) + @([pscustomobject]@{ utc = (Get-UtcStamp (Get-Date)); marker = $Marker; text = $clean })
    Write-FileAtomic $Path (ConvertTo-Json -InputObject $rows -Compress)
}

function Test-TaskFile([string]$Sha, [string]$TaskPath) {
    <# Чи є файл наряду на коміті позначки. Вирок «нема» — лише коли git так сказав; будь-який інший збій (блокування
    об'єктів під час fetch сусіднього процесу, таймаут) після трьох спроб — виняток, і позначка вертається в чергу, а не
    пишеться кінцем NO_TASK_FILE (29.10 19:36 UTC: 28 с до вироку на виклик, що тепер триває 0,1 с). #>
    for ($i = 1; $i -le 3; $i++) {
        $r = Invoke-Git @('cat-file', '-e', "${Sha}:$TaskPath") -AllowFail
        if ($r.Code -eq 0) { return $true }
        if ((-not $r.TimedOut) -and ($r.Code -eq 1 -or $r.Err -match 'does not exist|Not a valid object name|exists on disk, but not in')) { return $false }
        if ($i -lt 3) { Start-Sleep -Seconds 3 }
    }
    throw "git cat-file -e ${Sha}:$TaskPath -> $($r.Code): $($r.Err.Trim())"
}

# --- сигнал про запобіжник, що тримає позначки ----------------------------------------------------------------------
# 29.10 GPU-наряд стояв у черзі з 15:06 UTC: журнал 144 рази "GPU зайнята", а диспетчер не знав. Запобіжник сам пише
# диспетчерові рядок, коли тримає позначки понад quota_wait_minutes (смуги.json, з джерелом).

function Add-Hold([hashtable]$Held, [string]$Resource, [string]$Reason, [string]$Marker) {
    <# Ресурс тримає позначку за цього проходу; причина — перша за проходом. #>
    if (-not $Held.ContainsKey($Resource)) { $Held[$Resource] = @{ Reason = $Reason; Markers = (New-Object System.Collections.ArrayList) } }
    [void]$Held[$Resource].Markers.Add($Marker)
}

function Update-HoldSignals([hashtable]$Held, [scriptblock]$Send) {
    <# Рядок "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО <ресурс>: <причина>, позначок N" — один на причину, повтор лише при зміні причини.
    Утримання зникло — запис знято, нове сигналить знову. Стан — holds.json у теці стану (переживає перезапуск проходу). #>
    $path = Join-Path $script:StateDir 'holds.json'
    $prev = @{}
    if (Test-Path -LiteralPath $path) {
        try { foreach ($p in ([System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json).PSObject.Properties) { $prev[$p.Name] = $p.Value } } catch { $null = $_ }
    }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $after = [double](Get-Limit $script:Limits 'QuotaWaitMinutes' 'quota_wait_minutes') * 60
    $next = [ordered]@{}
    foreach ($res in @($Held.Keys | Sort-Object)) {
        $h = $Held[$res]; $old = $prev[$res]
        $since = $(if ($null -ne $old) { [long]$old.since } else { $now })
        $sent = $(if ($null -ne $old) { [string]$old.sent } else { '' })
        # Числові показники гуляють між проходами: повтор лише при зміні причини, не MiB чи відсотка.
        if (($now - $since) -ge $after -and ($sent -replace ' [0-9]+(?= MiB| %| з потрібних)', '') -cne ($h.Reason -replace ' [0-9]+(?= MiB| %| з потрібних)', '')) {
            if (& $Send "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО ${res}: $($h.Reason), позначок $($h.Markers.Count)") { $sent = $h.Reason }
        }
        $next[$res] = [ordered]@{ since = $since; reason = $h.Reason; sent = $sent }
    }
    if ($next.Count -eq 0) { Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue; return }
    $text = $next | ConvertTo-Json -Compress
    $cur = $(if (Test-Path -LiteralPath $path) { [System.IO.File]::ReadAllText($path, $script:Utf8) } else { '' })
    if ($text -cne $cur) { Write-FileAtomic $path $text }
}

# --- простій увімкненого ноутбука ---------------------------------------------------------------------------------------
# У ніч на 31.10 ноутбук за 13 год працював ~3 год 15 хв і стояв увімкненим до 2 год 20 хв поспіль, а диспетчер не знав
# (власник 31.10 07:52: увімкнений ноутбук працює доцільно, без роботи — вимикається). Простій — ні прогону, ні позначки
# в черзі поза нульовою квотою; початок — остання мить, коли прохід бачив роботу (≤ poll_minutes від кінця прогону чи
# зняття позначки), після ввімкнення — перший прохід (вимкнений час не рахується). Межі в хвилинах нема: джерела для неї
# нема (ядро, «Межа роботи»), тож рядок іде одразу, раз на простій.

function Get-UtcProp($Obj, [string]$Name) {
    <# Поле з idle.json як UTC-рядок: PowerShell 7 перетворює ISO-рядок JSON на дату, 5.1 лишає рядком. #>
    $v = Get-JsonProp $Obj $Name
    if ($v -is [datetime]) { return Get-UtcStamp $v }
    [string]$v
}

function Update-Idle([bool]$Busy, [scriptblock]$Send, [bool]$Reset = $false) {
    <# idle.json у теці стану: busy_utc — останній прохід із роботою; since — початок простою (порожній, доки є робота);
    sent — рядок ПРОСТІЙ цього простою доставлено в теку вихідних. Новий рядок — лише після нової роботи. #>
    $path = Join-Path $script:StateDir 'idle.json'
    $now = Get-UtcStamp (Get-Date)
    $prev = $null
    if (Test-Path -LiteralPath $path) { try { $prev = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json } catch { $null = $_ } }
    if ($Busy) {
        Write-FileAtomic $path ((@{ busy_utc = $now; since = ''; sent = $false }) | ConvertTo-Json -Compress)
        return
    }
    $since = ''; $sent = $false
    if ($null -ne $prev -and -not $Reset) {
        $since = Get-UtcProp $prev 'since'; $sent = ((Get-JsonProp $prev 'sent') -eq $true)
        if ($since -cnotmatch '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$') {
            $b = Get-UtcProp $prev 'busy_utc'; $since = $(if ($b -cmatch '^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$') { $b } else { $now }); $sent = $false
        }
    } else { $since = $now }
    if (-not $sent) {
        $from = [datetime]::ParseExact($since, "yyyy-MM-dd'T'HH:mm:ss'Z'", [cultureinfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal -bor [Globalization.DateTimeStyles]::AdjustToUniversal)
        $min = [Math]::Max(0, [int][Math]::Floor(([datetime]::UtcNow - $from).TotalMinutes))
        if (& $Send "GEMINI ОБГОРТКА: ПРОСТІЙ $since $min") { $sent = $true }
    }
    $busyUtc = $(if ($null -ne $prev -and -not $Reset) { (Get-UtcProp $prev 'busy_utc') } else { '' })
    Write-FileAtomic $path ((@{ busy_utc = $busyUtc; since = $since; sent = $sent }) | ConvertTo-Json -Compress)
}
