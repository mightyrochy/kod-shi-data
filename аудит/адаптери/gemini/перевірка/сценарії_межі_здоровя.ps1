#Requires -Version 5.1
<# Стенд наряду «обгортка-межі-й-здоровя»: межа без джерела, аварії однієї причини одним рядком, «Здоров'я» в стані #1856.
Справжні функції обгортки; підмінено лише git (вміст смуги.json), мережу доставки, диск і перелік позначок. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('mezhi-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$utf = New-Object Text.UTF8Encoding($false)
$bad = 0
$script:Seq = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
function Put-Line([string]$Dir, [string]$Line) {
    <# Готовий файл вихідних зі службовим ім'ям, як пишуть скрипти власника. #>
    [void][IO.Directory]::CreateDirectory($Dir)
    $name = '20261029-120000-{0:x12}.txt' -f $script:Seq++
    [IO.File]::WriteAllText((Join-Path $Dir $name), $Line + "`n", $utf)
}
function Lanes([string]$ClaudeNode) {
    <# смуги.json v2: slots.claude — заданий вузол, решта — з джерелом. #>
    $src = '"джерело": "вимір: стенд 29.10 — 3 копії"'
    '{"v": 2, "slots": {"codex": {"n": 3, ' + $src + '}, "agy": {"n": 3, ' + $src + '}, "claude": ' + $ClaudeNode + '}, "poll_minutes": {"n": 2, "джерело": ""}}'
}

try {
    # --- 1–2: межі (claude_run.ps1 з queue_lanes.ps1) і «Здоров'я» в тілі стану ------------------------------------
    Scenario 'межі й здоров''я' {
        . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$tmp/cr" -RepoDir $tmp -OutboxDir "$tmp/cbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
        foreach ($d in @("$tmp/cr", "$tmp/cr/state", "$tmp/cr/slots", "$tmp/gout", "$tmp/ctmp", "$tmp/pub")) { [void][IO.Directory]::CreateDirectory($d) }
        $script:StateDir = "$tmp/cr/state"; $script:SlotDir = "$tmp/cr/slots"
        $script:LanesText = ''
        function Invoke-Git { param([string[]]$GitArgs, [switch]$AllowFail, [double]$TimeoutMinutes = 10, [string]$Dir = '')
            [pscustomobject]@{ Code = $(if ($script:LanesText) { 0 } else { 128 }); Out = $script:LanesText; Err = '' } }

        foreach ($t in @(@('власник 29.10', $true), @('власник 29.10 09:46 UTC: «…»', $true), @('вимір: диск 29.10 — (346,2 − 127) / 4,05 = 54', $true),
                @('вимір: диск 29.10', $false), @('вимір: 54', $false), @('власник', $false), @('власник 32.10', $false), @('', $false), @('рука 29.10 4', $false))) {
            Check "1 джерело «$($t[0])» — $(if ($t[1]) { 'є' } else { 'нема' })" ((Test-LimitSource $t[0]) -eq $t[1])
        }

        $script:LanesText = Lanes '{"n": 7, "джерело": "власник 29.10"}'
        $l = Get-Limits
        Check "1 з джерелом slots.claude = $($l.slots['claude']) (7); слоти з джерелом, poll_minutes — без" ($l.slots['claude'] -eq 7 -and @($l.unsourced | Where-Object { $_ -like 'slots.*' }).Count -eq 0 -and @($l.unsourced) -ccontains 'poll_minutes')
        # Мірило: slots.claude без джерела — ДО (v1: число бралось як є) 40, ПІСЛЯ попереднє 7 і рядок у стані.
        $script:LanesText = Lanes '{"n": 40, "джерело": ""}'
        $l = Get-Limits
        Check "1 без джерела slots.claude = $($l.slots['claude']) (ДО 40 → ПІСЛЯ попереднє 7)" ($l.slots['claude'] -eq 7 -and @($l.unsourced) -ccontains 'slots.claude')
        $script:LanesText = Lanes '40'
        Check '1 число без вузла (міграція v1) — попереднє 7' ((Get-Limits).slots['claude'] -eq 7)
        $script:LanesText = '{"v": 1, "slots": {"codex": 9, "agy": 9, "claude": 9}}'
        $l = Get-Limits
        Check "1 файл v1 — усі 10 полів без джерела, попередні значення" (@($l.unsourced).Count -eq 10 -and $l.slots['claude'] -eq 7 -and $l.slots['codex'] -eq 3)
        $script:LanesText = 'не json'
        Check '1 кривий файл — попередні значення' ((Get-Limits).slots['agy'] -eq 3)
        $script:LanesText = [IO.File]::ReadAllText((Join-Path $SourceDir 'смуги.json'), $utf)
        $script:Limits = Get-Limits
        Check "1 смуги.json main: слоти з виміру $($script:Limits.slots['claude'])/$($script:Limits.slots['codex'])/$($script:Limits.slots['agy']), без джерела $(@($script:Limits.unsourced).Count)" ($script:Limits.slots['claude'] -eq 54 -and $script:Limits.slots['codex'] -eq 10 -and @($script:Limits.unsourced).Count -eq 7 -and @($script:Limits.unsourced) -cnotcontains 'slots.claude')
        $script:LanesText = Lanes '{"n": 40, "джерело": ""}'
        $script:Limits = Get-Limits

        # Стан: диск, теки, позначки, квота — підставні; решта — справжня Get-StatusBody.
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        $gb = [long]1GB
        [IO.File]::WriteAllText("$tmp/cr/health.json", (@{ time = $now - 90000; samples = @(@{ t = $now - 90000; free = 105 * $gb }); dirs = @() } | ConvertTo-Json -Compress -Depth 4), $utf)
        [IO.File]::WriteAllBytes("$tmp/ctmp/a.bin", (New-Object byte[] 2048))
        function Get-FreeBytes { 100 * [long]1GB }
        function Get-TaskRows { @() }
        $sha = 'b' * 40
        $script:FakeMarkers = @(
            @('наряд-а/cc-claude-sonnet-5-5-medium/1', 600), @('перевірка-12/gpt-6.1-sol-high/1', 7200), @('автоперевірка-9-x/gpt-6.1-sol-high/1', 259200),
            @('автоперевірка-9-y/gpt-6.1-sol-high/1', 172800), @('наряд-б/gemini-3.8-flash-high/1', 100)
        ) | ForEach-Object { ConvertTo-Marker ("refs/remotes/origin/gemini-queue/$($_[0])`t$sha`t$($now - $_[1])") }
        function Get-Markers { $script:FakeMarkers }
        $stamp = { param($s) [DateTimeOffset]::FromUnixTimeSeconds($now + $s).UtcDateTime.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'") }
        [IO.File]::WriteAllText("$tmp/cr/quota-claude.json", (@{ read = (& $stamp -60); refused = (& $stamp -60); reset = (& $stamp 3600); windows = @() } | ConvertTo-Json -Compress), $utf)
        [IO.File]::WriteAllText("$tmp/gout/heartbeat.json", (@{ read_utc = (& $stamp 0); time = (Get-Date).ToString('s'); isolation = 'OK'; limits = 'origin/main'
                    unsourced = @('poll_minutes', 'slots.claude', 'вигадане'); health = @{ profile = [string](3 * $gb); skipped = '2'; read = (& $stamp -30); zero = '4'; top = ('AppData=' + (2 * $gb) + ';gemini-runs=' + $gb + ';x|y=5;' + 'bad'); copies = ('20261030-184723-7915b6610cfb=' + $gb) } } | ConvertTo-Json -Compress -Depth 4), $utf)
        $body = Get-StatusBody
        [IO.File]::WriteAllText("$tmp/status.md", $body, $utf)
        Check '2 межа без джерела: slots.claude (claude-run, gemini-run)' ($body.Contains('- межа без джерела: slots.claude (claude-run, gemini-run)'))
        Check '2 чужого поля з heartbeat у межах нема' (-not $body.Contains('вигадане'))
        Check "2 розділ «Здоров'я»" ($body.Contains("### Здоров'я"))
        Check '2 показник 1: вільне місце C: і зміна за добу −5.0 ГБ' ($body.Contains('- вільне місце на C: 100.0 ГБ · зміна за добу: −5.0 ГБ'))
        Check '2 показник 2: розміри C:\tmp, claude-run, профілю gemini' ($body -cmatch '- розміри: C:\\tmp 0\.0 ГБ · claude-run [0-9.]+ ГБ · профіль gemini 3\.0 ГБ \(недоступних тек 2\)')
        Check '2 розбивка профілю gemini: найбільші теки першого рівня; чужий рядок відкинуто' ($body.Contains('- профіль gemini за теками: AppData 2.0 ГБ · gemini-runs 1.0 ГБ' + "`n"))
        Check '2 розбивка копій задач gemini: найбільші копії в gemini-runs\w' ($body.Contains('- копії задач gemini (gemini-runs\w): 20261030-184723-7915b6610cfb 1.0 ГБ' + "`n"))
        $ok3 = $body.Contains('Позначки черги: 5') -and $body.Contains('| codex | автоперевірка | 0 | 0 | 2 |') -and $body.Contains('| codex | перевірка | 0 | 1 | 0 |') -and $body.Contains('| claude | наряд | 1 | 0 | 0 |')
        Check '2 показник 3: позначки за рушієм, видом і віком' $ok3
        if (-not $ok3) { @($body -split "`n" | Where-Object { $_ -match '^Позначки|^\| (claude|codex|agy|\?) \|' }) | ForEach-Object { "    $_" } }
        Check '2 показник 4: позначки на рушії з нульовою квотою' ($body.Contains('Позначки на рушії з нульовою квотою: claude 1 · codex 0 · agy 4'))
        $h1 = [IO.File]::ReadAllText("$tmp/cr/health.json", $utf)
        function Get-FreeBytes { 1 }
        [void](Get-StatusBody)
        Check '2 показник 5: повторний вимір раніше за usage_minutes не міряє' ([IO.File]::ReadAllText("$tmp/cr/health.json", $utf) -ceq $h1)
        Check '2 узяття не гейтить: Start-Markers і Get-FreeSlot без здоров''я' (-not ((Get-Command Start-Markers).Definition -match 'Health|Здоров') -and -not ((Get-Command Get-FreeSlot).Definition -match 'Health|Здоров'))
    }

    # --- 3: аварії однієї причини (gemini_publish.ps1) --------------------------------------------------------------
    $crash = @(1..12 | ForEach-Object { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/наряд-$_ CRASH" })
    $quiet = @('M60', 'M30', 'M5') | ForEach-Object { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО codex/квота-$_ QUOTA0_CODEX_$_" }
    $other = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО claude/інше MODEL_INVALID'
    foreach ($phase in @('ДО', 'ПІСЛЯ')) {
        Scenario "3 $phase" {
            $dir = "$tmp/p-$phase"
            . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir $(if ($phase -eq 'ПІСЛЯ') { "$tmp/pub" } else { "$dir/pub" }) -OutboxDir "$dir/box" -SendRetries 1 -SendRetryDelaySeconds 0
            foreach ($d in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($d) }
            $script:Calls = @()
            function Get-DispatcherId { 'session_test' }
            function Resolve-Exe { 'test-native' }
            function Invoke-Native { param($Exe, $Arguments, $WorkDirectory, $TimeoutMinutes, $StdIn)
                $script:Calls += , [string]$StdIn; [pscustomobject]@{ Code = 0; Out = '{"ok":true}'; Err = '' } }
            foreach ($l in @($crash + $quiet + $other)) { Put-Line $OutboxDir $l }
            Receive-Outbox
            if ($phase -eq 'ПІСЛЯ') { Merge-BlockedLines }
            foreach ($sf in @(Get-ChildItem -LiteralPath "$WorkDir/state" -Filter '*.json' -File | Sort-Object Name)) { Send-Pending $sf }
            $wake = @($script:Calls | ForEach-Object { ($_ -split "`n")[0] })
            $local = @()
            if (Test-Path -LiteralPath "$WorkDir/local-lines.json") { $local = @((ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/local-lines.json")))) }
            if ($phase -eq 'ДО') {
                Check "3 ДО: 12 збоїв CRASH за прохід — пробуджень $(@($wake | Where-Object { $_ -like '*CRASH' }).Count) (12), QUOTA0 — перший будить, у зведенні $($local.Count) (2)" (@($wake | Where-Object { $_ -like '*CRASH' }).Count -eq 12 -and $local.Count -eq 2 -and @($wake | Where-Object { $_ -like '*QUOTA0*' }).Count -eq 1)
                return
            }
            $agg = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО CRASH ×12: claude/наряд-1, claude/наряд-2, claude/наряд-3, claude/наряд-4, claude/наряд-5 …'
            Check "3 ПІСЛЯ: пробуджень $($wake.Count) — один «×12», один QUOTA0 «×3» і окремий інший код" ($wake.Count -eq 3 -and $wake -ccontains $agg -and $wake -ccontains $other -and $wake -ccontains 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО QUOTA0_CODEX ×3: codex/квота-M60, codex/квота-M30, codex/квота-M5')
            Check '3 зведений рядок — за шаблоном вихідних' ((Test-OutboxLine $agg) -eq '')
            Check '3 QUOTA0 трьох хвилин — один зведений рядок, одне пробудження, у зведенні без пробудження нічого' ($local.Count -eq 0)
            $groups = @((ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/blocked-groups.json"))))
            $cr = @($groups | Where-Object { $_.code -ceq 'CRASH' })
            Check '3 лічба й повний перелік (12 гілок) — у blocked-groups.json' ($cr.Count -eq 1 -and [int]$cr[0].n -eq 12 -and @($cr[0].branches).Count -eq 12)
            Merge-BlockedLines
            foreach ($sf in @(Get-ChildItem -LiteralPath "$WorkDir/state" -Filter '*.json' -File | Sort-Object Name)) { Send-Pending $sf }
            Check '3 повторний прохід — без нового зведення й листа' ($script:Calls.Count -eq 3 -and @((ConvertFrom-Json ([IO.File]::ReadAllText("$WorkDir/blocked-groups.json")))).Count -eq 2)
            Check '3 одиничний рядок не зводиться' (Test-DispatcherAction $other)
            Check '3 зведений QUOTA0 у відкритому вікні тихий, CRASH будить' (-not (Test-DispatcherAction 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО QUOTA0_CODEX ×3: codex/а, codex/б') -and (Test-DispatcherAction $agg))
        }
    }

    Scenario '4 стан показує аварії однієї причини' {
        . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$tmp/cr" -RepoDir $tmp -OutboxDir "$tmp/cbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
        $script:StateDir = "$tmp/cr/state"; $script:SlotDir = "$tmp/cr/slots"; $script:Limits = $null
        function Get-TaskRows { @() }
        function Get-Markers { @() }
        $body = Get-StatusBody
        Check '4 #1856: розділ «Аварії однієї причини» з лічбою 12 і всіма гілками' ($body.Contains('### Аварії однієї причини') -and $body -cmatch '\| CRASH \| 12 \| claude/наряд-1, .*claude/наряд-12 \|')
    }

    Scenario '4б стан несе вимір відеокарти, а не лише замок' {
        . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir "$tmp/cr" -RepoDir $tmp -OutboxDir "$tmp/cbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
        $script:StateDir = "$tmp/cr/state"; $script:SlotDir = "$tmp/cr/slots"; $script:Limits = $null
        function Get-TaskRows { @() }
        function Get-Markers { @() }
        $script:Tel = [pscustomobject]@{ Error = ''; TotalMiB = 16376; FreeMiB = 2376; Percent = 83 }
        $script:Rows = @(
            [pscustomobject]@{ Name = 'pid_111_luid_0x0_0x1_phys_0'; DedicatedUsage = [string](10240 * 1MB) },
            [pscustomobject]@{ Name = 'pid_222_luid_0x0_0x1_phys_0'; DedicatedUsage = [string](512 * 1MB) },
            [pscustomobject]@{ Name = 'pid_333_luid_0x0_0x1_phys_0'; DedicatedUsage = '4096' },
            [pscustomobject]@{ Name = 'pid_444_luid_0x0_0x1_phys_1'; DedicatedUsage = [string](900 * 1MB) })
        function Get-GpuTelemetry { $script:Tel }
        function Get-GpuCounterRows { $script:Rows }
        function Get-GpuProcessInfo([int]$ProcessId) { [pscustomobject]@{ Name = @{ 111 = 'ollama'; 222 = 'dwm' }[$ProcessId]; Path = '' } }
        # Замок вільний (ніхто з наряду GPU не тримає), а карта зайнята на 83 %: ДО стан казав «GPU: вільна», ПІСЛЯ — вимір.
        $body = Get-StatusBody
        Check '4б вимір карти: UTC, завантаження 83 %, зайнято 14000 з 16376 MiB' ($body -cmatch '(?m)^- вимір карти \(nvidia-smi, UTC 20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z\): завантаження 83 % · пам.ять зайнято 14000 з 16376 MiB \(вільно 2376\)$')
        Check '4б процеси-власники: PID, ім''я, MiB за спаданням; <1 MiB і чужа карта (phys_1) не входять' ($body.Contains('(лічильник Windows, PID ім''я MiB): 111 ollama 10240 · 222 dwm 512') -and -not $body.Contains(' 333 ') -and -not $body.Contains(' 444 '))
        Check '4б замок — окреме поле з назвою замка, вільний при зайнятій карті' ($body.Contains('- замок GPU обгортки (запис слотів нарядів, не вимір карти): вільний'))
        Check '4б старого рядка «GPU: вільна/зайнята» нема, межі — окремим рядком' (-not ($body -cmatch '(?m)^GPU: ') -and $body -cmatch '(?m)^межі: claude-run — ')
        $script:Tel = [pscustomobject]@{ Error = 'nvidia-smi не відповів'; TotalMiB = 0; FreeMiB = 0; Percent = 0 }
        $body = Get-StatusBody
        Check '4б помилка виміру названа з часом UTC, чисел карти й процесів нема' ($body -cmatch '(?m)^- вимір карти \(UTC 20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z\): nvidia-smi не відповів' -and -not $body.Contains('процеси-власники'))
        $script:Tel = [pscustomobject]@{ Error = ''; TotalMiB = 16376; FreeMiB = 16376; Percent = 0 }
        $script:Rows = $null
        $body = Get-StatusBody
        Check '4б лічильник процесів недоступний — названо, пам''ять карти лишається' ($body.Contains('завантаження 0 % · пам''ять зайнято 0 з 16376 MiB') -and $body -cmatch '(?m)^- процеси-власники пам.яті: лічильник Windows недоступний \(UTC ')
        Check '4б вимір не гейтить узяття: Start-Markers і Get-FreeSlot без Get-GpuStateLines' (-not ((Get-Command Start-Markers).Definition -match 'Get-GpuStateLines') -and -not ((Get-Command Get-FreeSlot).Definition -match 'Get-GpuStateLines'))
    }

    # --- 5–6: головний цикл claude-run (Main) зі справжнім Get-VersionSwitch і прибиранням; підмінено git, позначки, ---
    # --- чекання й стан ----------------------------------------------------------------------------------------------
    $old = 'a' * 40; $new = 'b' * 40
    $vroot = "$tmp/wrapper"
    foreach ($v in @($old, $new)) { [void][IO.Directory]::CreateDirectory("$vroot/versions/$v") }
    function Use-Main([string]$Dir) {
        <# claude_run.ps1 у теці $Dir з підмінами всього, що виходить за процес. #>
        . (Join-Path $SourceDir 'claude_run.ps1') -WorkDir $Dir -RepoDir $tmp -OutboxDir "$tmp/cbox" -PublishDir "$tmp/pub" -GeminiOutDir "$tmp/gout" -LaneDir "$tmp/lanes" -TmpDir "$tmp/ctmp" -NoStatus
        $script:Fetches = 0; $script:FailFetch = 0; $script:Starts = 0; $script:Cleans = 0; $script:Waits = 0
        $script:OnStart = {}; $script:Fake = $null
        function Test-OwnerUser { $true }
        function Get-BootStamp { 'boot' }
        function Resume-Interrupted { }
        function Clear-OrphanClaims { }
        function Update-Status { param([switch]$Force) }
        function Get-Limits { $null }
        function Get-Limit { 2 }
        function Invoke-Git { param([string[]]$GitArgs, [switch]$AllowFail, [double]$TimeoutMinutes = 10, [string]$Dir = '')
            if ($GitArgs[0] -eq 'fetch') {
                $script:Fetches++
                if ($script:Fetches -le $script:FailFetch) { throw 'fatal: unable to access github.com' }
            }
            [pscustomobject]@{ Code = 0; Out = $RepoUrl; Err = '' } }
        function Clear-TaskCopies { $script:Cleans++ }
        function Start-Markers { $script:Starts++; & $script:OnStart; @(0, $null) }
        function Wait-Workers { $script:Waits++; if ($script:Waits -ge 2 -and $null -ne $script:Fake) { $script:Fake.Proc.HasExited = $true } }
    }

    Scenario '5 нова версія в довгому процесі' {
        . Use-Main "$tmp/m5"
        [IO.File]::WriteAllText("$vroot/active.txt", $old, $utf)
        $script:VersionDir = "$vroot/versions/$old"
        Check '5 версія та сама — перемикання нема' ((Get-VersionSwitch) -eq '')
        $script:VersionDir = $SourceDir
        [IO.File]::WriteAllText("$vroot/active.txt", $new, $utf)
        Check '5 запуск не з versions\<SHA> (клон) — перемикання нема' ((Get-VersionSwitch) -eq '')
        $script:VersionDir = "$vroot/versions/$old"
        [IO.File]::WriteAllText("$vroot/active.txt", 'c' * 40, $utf)
        Check '5 pointer на теку, якої нема, — перемикання нема' ((Get-VersionSwitch) -eq '')
        [IO.File]::WriteAllText("$vroot/active.txt", 'кривий', $utf)
        Check '5 кривий pointer — перемикання нема' ((Get-VersionSwitch) -eq '')
        # Живий 29.10: самооновлення о 13:14 записало новий active.txt, а claude-run з 08:34 далі брав позначки старою
        # версією. Тут: перший прохід веде наряд (живий процес), під час нього pointer перемикається.
        [IO.File]::WriteAllText("$vroot/active.txt", $old, $utf)
        $script:Fake = [pscustomobject]@{ Slot = 'claude-1'; Slug = 'x'; Gpu = $false; Marker = 'gemini-queue/x/cc-claude-sonnet-5-5-medium/1'; Proc = [pscustomobject]@{ HasExited = $false } }
        $script:OnStart = { if ($script:Starts -eq 1) { [void]$script:Workers.Add($script:Fake); [IO.File]::WriteAllText("$vroot/active.txt", $new, $utf) } }
        $rc = @(Main)[-1]
        Check "5 після перемикання позначок старою версією не взято: проходів $($script:Starts) (ДО — 2: другий прохід старим кодом, ПІСЛЯ — 1)" ($script:Starts -eq 1)
        Check "5 головний процес чисто вийшов (код $rc), живий наряд не зупинено — доробляє під своїм замком" ($rc -eq 0 -and -not $script:Fake.Proc.HasExited)
        $log = [IO.File]::ReadAllText("$tmp/m5/claude-run.log", $utf)
        Check '5 журнал: «версія: aaaaaaaa → bbbbbbbb»' ($log.Contains('версія: aaaaaaaa → bbbbbbbb'))
        function Get-TaskRows { @() }
        function Get-Markers { @() }
        $body = Get-StatusBody
        Check '5 #1856: рядок «- версія: aaaaaaaa → bbbbbbbb (<UTC>)»' ($body -cmatch '(?m)^- версія: aaaaaaaa → bbbbbbbb \(20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9:]{8}Z\)$')
    }

    Scenario '6 прибирання накопиченого після збою fetch' {
        . Use-Main "$tmp/m6"
        $script:VersionDir = $SourceDir
        # Живий 29.10 13:17–13:24: кожен прохід — «unable to access github.com».
        $script:FailFetch = 1
        $rc = @(Main)[-1]
        Check "6 перший прохід упав на fetch: прибирання нема (origin/* застарілі), процес без нарядів вийшов (код $rc)" ($script:Fetches -eq 1 -and $script:Cleans -eq 0 -and $rc -eq 0)
        $rc = @(Main)[-1]
        Check "6 наступний запуск, fetch успішний: прибирань $($script:Cleans) (1), код $rc" ($script:Fetches -eq 2 -and $script:Cleans -eq 1 -and $rc -eq 0)
        # Процес із живим нарядом: fetch падає на другому проході — прибирання першого проходу не повторюється.
        $script:Fake = [pscustomobject]@{ Slot = 'claude-1'; Slug = 'x'; Gpu = $false; Marker = 'gemini-queue/x/cc-claude-sonnet-5-5-medium/1'; Proc = [pscustomobject]@{ HasExited = $false } }
        $script:OnStart = { if ($script:Starts -eq 1) { [void]$script:Workers.Add($script:Fake) } }
        $script:Fetches = 0; $script:Cleans = 0; $script:Starts = 0; $script:Waits = 0; $script:FailFetch = 0
        $rc = @(Main)[-1]
        Check "6 довгий процес: прибирань $($script:Cleans) за $($script:Fetches) fetch (1 — на першому успішному)" ($script:Fetches -ge 3 -and $script:Cleans -eq 1 -and $rc -eq 0)
    }
} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
if ($bad) { "ПІДСУМОК: ✗ $bad"; exit 1 }
'ПІДСУМОК: ✗ 0'
exit 0
