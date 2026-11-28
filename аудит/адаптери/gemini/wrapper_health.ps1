#Requires -Version 5.1
# Спільні тривоги й ритм стану; деталі — лише з цього переліку, жодного тексту агента.
$script:HealthDetails = @{
    AUTH = @('AGY', 'CODEX', 'CLAUDE', 'CLOUD')
    ISOLATION = @('WHOAMI', 'NET_SESSION', 'PROFILES', 'DRIVES', 'ENV')
    DISK = @('FULL')
    ENGINE = @('AGY', 'CODEX', 'CLAUDE')
}
$script:HealthAlertDir = ''
# Сигнал запобіжника, що тримає позначки (queue_lanes.ps1, Update-HoldSignals), і позначка з назвою не за форматом
# (gemini_run.ps1, Start-Markers; назва — безпечними знаками): рядок рушія й шаблон публікації — тут одне місце.
$script:HoldLineTemplate = '\AGEMINI ОБГОРТКА: ЗАБЛОКОВАНО (?:(?:GPU|SLOTS): (?:замок GPU іншого наряду|незакритий знімок моделей GPU|модель GPU-наряду на карті|LM Studio недоступний на :1234|слоти зайняті|nvidia-smi не відповів|кілька GPU: потрібен вимір однієї карти|навантаження (?:100|[1-9]?[0-9]) %|вільно [0-9]{1,7} з потрібних [0-9]{1,7} MiB(?:; навантаження (?:100|[1-9]?[0-9]) %)?|GPU зайнята стороннім процесом|процес [A-Za-z0-9._+-]{1,92}|процес [A-Za-z0-9._-]{1,30} [0-9]{1,7} MiB(?:\+[A-Za-z0-9._-]{1,30} [0-9]{1,7} MiB){0,2}), позначок [1-9][0-9]{0,3}|gemini-queue/[\p{L}\p{Nd}._/-]{1,160} FORMAT)\z'

# Сторож GPU-замка (queue_lanes.ps1, Update-GpuWatch): позначка, хвилин замка, хвилин без роботи карти, змін PID власника пам'яті.
$script:GpuIdleLineTemplate = '\AGEMINI ОБГОРТКА: ЗАБЛОКОВАНО GPU_IDLE (?:gemini|codex|claude)/[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79} ЗАМОК [0-9]{1,6} СОН [0-9]{1,6} БЕЗ_РОБОТИ [0-9]{1,6} PID_ЗМІН [0-9]{1,5}\z'

# Світло зникло й повернулось (claude_run.ps1 -Light, Step-Light; пише лише тримач світла): перший рядок — ноутбук на
# батареї, засне, щойно рядок доставлено; другий — світло є, ноутбук знову доступний. Час усюди UTC; у другому — повернення й
# настінний час зникнення (сон його не стискає, на відміну від «хвилин» у журналі).
$script:PowerOffLineTemplate = '\AGEMINI ОБГОРТКА: СВІТЛА НЕМА 20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\z'
$script:PowerOnLineTemplate = '\AGEMINI ОБГОРТКА: СВІТЛО Є 20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z ПАУЗА З 20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\z'

# Перерва в роботі ноутбука (gemini_publish.ps1, Update-SleepEvents): СОН — пробудження, ВИМКНЕНО-СТАРТ — нове завантаження. СОН,
# що почався на батареї, несе «СВІТЛА НЕ БУЛО З <UTC зникнення>» і, коли пробудження вже на мережі, «ДОСТУПНИЙ З <UTC пробудження>»:
# такий СОН будить диспетчера (Test-DispatcherAction), решта йде зведенням.
$script:SleepLineStamp = '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z'
$script:SleepLineTemplate = "\AGEMINI ОБГОРТКА: (?:ВИМКНЕНО-СТАРТ $($script:SleepLineStamp) → $($script:SleepLineStamp), нарядів [0-9]{1,5}|СОН $($script:SleepLineStamp) → $($script:SleepLineStamp), нарядів [0-9]{1,5}(?: СВІТЛА НЕ БУЛО З $($script:SleepLineStamp)(?: ДОСТУПНИЙ З $($script:SleepLineStamp))?)?)\z"

# --- спільні запис і читання файлів ------------------------------------------------------------------------------
# Повтори запису й читання: зайнята ціль — кілька спроб, а не виняток посеред наряду. 20 × 50 мс — те, що Write-FileAtomic
# мала в queue_lanes.ps1 до перенесення сюди; нового числа тут нема.
$script:FileRetries = 20
$script:FileRetryMs = 50
$script:NativeMove = $null   # Move-FileOver: $null — ще не з'ясовано

function Move-FileOver([string]$From, [string]$To) {
    <# Переносить $From на $To одним кроком файлової системи; наявна ціль підміняється, і шлях ні на мить не лишається без
    файла. У Windows — MoveFileExW із MOVEFILE_REPLACE_EXISTING: `File.Replace` (ReplaceFileW) на NTFS на мить знімає
    ціль, і читач, що відкрив шлях саме тоді, бачив «нема файла» (вимір 28.11 у стенді: 393 з 14 тис. читань). Деінде —
    rename(2) крізь File.Replace/Move, він атомарний. Compile Add-Type — раз на процес; не склався — запасний File.Replace. #>
    if ($null -eq $script:NativeMove) {
        $script:NativeMove = $false
        if ([System.IO.Path]::DirectorySeparatorChar -eq [char]92) {
            try {
                if (-not ('KodShi.Native' -as [type])) {
                    Add-Type -Namespace KodShi -Name Native -MemberDefinition '[System.Runtime.InteropServices.DllImport("kernel32.dll", CharSet = System.Runtime.InteropServices.CharSet.Unicode, SetLastError = true)] public static extern bool MoveFileExW(string from, string to, int flags);'
                }
                $script:NativeMove = $true
            } catch { $script:NativeMove = $false }
        }
    }
    if ($script:NativeMove) {
        if (-not [KodShi.Native]::MoveFileExW($From, $To, 1)) {
            throw (New-Object System.IO.IOException((New-Object System.ComponentModel.Win32Exception([System.Runtime.InteropServices.Marshal]::GetLastWin32Error())).Message))
        }
    } elseif ([System.IO.File]::Exists($To)) { [System.IO.File]::Replace($From, $To, [NullString]::Value) }
    else { [System.IO.File]::Move($From, $To) }
}

function Write-FileAtomic([string]$Path, [string]$Text) {
    <# Запис через тимчасовий файл і заміну: читач не бачить половини, а шлях ні на мить не лишається без файла.

    Спільні файли (стан, heartbeat, кеш квоти, local-lines.json) пишуть водночас планувальник, публікатор і процеси
    нарядів. Видаляти старий і переносити новий не можна: між двома кроками читач бачив «нема файла» (28.11 16:19,
    `local-lines.json`) — підміна йде одним кроком (Move-FileOver). Зайнята ціль (читач тримає файл) — повтор, не виняток. #>
    $tmp = $Path + '.' + [guid]::NewGuid().ToString('N').Substring(0, 8) + '.part'
    [System.IO.File]::WriteAllText($tmp, $Text, $script:Utf8)
    for ($i = 0; $i -lt $script:FileRetries; $i++) {
        try { Move-FileOver $tmp $Path; return }
        catch {
            if ($i -eq $script:FileRetries - 1) { Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; throw }
            Start-Sleep -Milliseconds $script:FileRetryMs
        }
    }
}

function Read-FileText([string]$Path) {
    <# Текст файла UTF-8, який пише інший процес. Файл зайнятий (IOException, окрім «нема файла/теки») — ті самі повтори,
    що в Write-FileAtomic. Нема файла чи інша помилка — одразу, як ReadAllText. Вид винятку — через -is, не типізованим
    catch: у Windows PowerShell 5.1 `catch [DirectoryNotFoundException]` ловив зайнятість файла (вимір 28.11 у стенді). #>
    for ($i = 0; ; $i++) {
        try { return [System.IO.File]::ReadAllText($Path, $script:Utf8) }
        catch {
            $e = $_.Exception
            if ($e.InnerException) { $e = $e.InnerException }
            $busy = $e -is [System.IO.IOException] -and $e -isnot [System.IO.FileNotFoundException] -and $e -isnot [System.IO.DirectoryNotFoundException]
            if (-not $busy -or $i -ge $script:FileRetries - 1) { throw }
            Start-Sleep -Milliseconds $script:FileRetryMs
        }
    }
}

function Test-HoldLine([string]$Line) { $Line -cmatch $script:HoldLineTemplate }

function Add-HoldLine([string]$Line) {
    <# Рядок сигналу запобіжника в теку тривог рушія (gemini-run → out/alerts); публікатор перевіряє його заново. #>
    if (-not $script:HealthAlertDir -or -not (Test-HoldLine $Line)) { return '' }
    [void][System.IO.Directory]::CreateDirectory($script:HealthAlertDir)
    $name = '{0:yyyyMMdd-HHmmss}-{1}.txt' -f [datetime]::UtcNow, ([guid]::NewGuid().ToString('N').Substring(0, 12))
    Write-FileAtomic (Join-Path $script:HealthAlertDir $name) ($Line + "`
")
    $name
}
$script:HeartbeatAction = $null
$script:HeartbeatBusy = $false
$script:LastHealthBeat = [datetime]::MinValue

function Test-HealthAlert([string]$Line) {
    <# Лише відомі код і деталь; довільний текст не стає службовим рядком. #>
    if ($Line -cnotmatch '\AGEMINI ОБГОРТКА: ТРИВОГА ([A-Z_]{2,16}) ([A-Z_]{2,16})\z') { return $false }
    $script:HealthDetails.ContainsKey($Matches[1]) -and $script:HealthDetails[$Matches[1]] -ccontains $Matches[2]
}

function Add-HealthAlert([string]$Code, [string]$Detail) {
    <# Подія у вихідних, не частіше ніж раз на годину для тієї самої пари; стан переживає перезапуск. #>
    $line = "GEMINI ОБГОРТКА: ТРИВОГА $Code $Detail"
    if (-not $script:HealthAlertDir -or -not (Test-HealthAlert $line)) { return }
    [void][System.IO.Directory]::CreateDirectory($script:HealthAlertDir)
    $lock = $null
    try {
        # Планувальник і процеси нарядів пишуть одночасно: один замок на перевірку й запис.
        for ($i = 0; $i -lt 20 -and $null -eq $lock; $i++) {
            try { $lock = [System.IO.File]::Open((Join-Path $script:HealthAlertDir '.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
            catch { Start-Sleep -Milliseconds 50 }
        }
        if ($null -eq $lock) { throw 'замок тривог зайнятий' }
        $stamp = Join-Path $script:HealthAlertDir ".$Code-$Detail.utc"
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        if (Test-Path -LiteralPath $stamp) {
            $last = 0L
            if ([long]::TryParse([System.IO.File]::ReadAllText($stamp), [ref]$last) -and $now - $last -lt 3600) { return }
        }
        $name = '{0:yyyyMMdd-HHmmss}-{1}.txt' -f [datetime]::UtcNow, ([guid]::NewGuid().ToString('N').Substring(0, 12))
        Write-FileAtomic (Join-Path $script:HealthAlertDir $name) ($line + "`n")
        Write-FileAtomic $stamp ([string]$now)
    } finally { if ($null -ne $lock) { $lock.Dispose() } }
}

function Add-HealthException($Exception) {
    <# Диск упізнається за системним кодом, текст винятку не пересилається. #>
    $e = $Exception
    while ($null -ne $e) {
        if (($e.HResult -band 0xffff) -in @(39, 112)) { Add-HealthAlert 'DISK' 'FULL'; return }
        $e = $e.InnerException
    }
}

function Invoke-HealthBeat {
    <# Серцебиття планувальника під час очікування; процеси нарядів не підміняють його свіжість. #>
    if ($null -eq $script:HeartbeatAction -or $script:HeartbeatBusy -or ([datetime]::UtcNow - $script:LastHealthBeat).TotalSeconds -lt 60) { return }
    $script:HeartbeatBusy = $true
    $script:LastHealthBeat = [datetime]::UtcNow
    try { & $script:HeartbeatAction }
    finally { $script:HeartbeatBusy = $false }
}

function Add-FinishedMarker([string]$Dir, [string]$Name, [string]$Sha) {
    <# Позначка дійшла кінцевого стану, її рядок опубліковано: запис «<позначка> <SHA>» для публікатора
    (`gemini_publish.ps1`, Remove-FinishedMarkers), який знімає гілку з черги під lease на цей SHA. Пишуть процеси
    власника (публікатор, claude-run) — у gemini прав пушу нема. #>
    if ($Name -cnotmatch '^gemini-queue/\S+$' -or $Name.Contains('..') -or $Sha -cnotmatch '^[0-9a-f]{40}$') { return }
    [void][IO.Directory]::CreateDirectory($Dir)
    Write-FileAtomic (Join-Path $Dir ((Get-Sha256Hex "$Name $Sha") + '.txt')) "$Name $Sha"
}

function Test-OldChainMarker($M) {
    <# Позначка автоперевірки в тій формі, яку ставив ланцюг обгортки (`/p2` без `gpu` і строку): ланцюг її
    більше не ставить (слово власника 08.11 15:47) — лишилися давні, і їх смуги не беруть. Позначка диспетчера має іншу умову
    (p0, p1, строк): коміт, на який вказує позначка, автора не лишає — це `main` на мить постановки в обох. #>
    $M.Slug -cmatch '^автоперевірка-[1-9][0-9]{0,8}-[0-9a-f]{40}$' -and $M.Cond -ceq 'p2'
}

function Test-ReviewBranch([string]$Branch) {
    <# Звіти перевірки й пачки вже містять вердикт і не породжують рекурсії: кирилицею й латинкою (avtoperevirka-,
    perevirka-), зокрема нова форма `<рушій>/перевірка-<ДДММ>-<N>`. #>
    $Branch -cmatch '/(?:авто(?:перевірка|живий)-|перевірка-|avtoperevirka-|perevirka-|pachka-|Е1-нічний-живий-)'
}

# Група квоти agy для моделі — одне джерело для смуги (gemini_run.ps1: чекання QUOTA0_<група>, pools.json) і ланцюга
# (wrapper_chain.ps1: рецензент за групою саме обраної моделі).
# Родини моделей: група /usage без власних слів («Gemini Models», «Claude and GPT models») — спільна для родини.
$script:Families = @('gemini', 'claude', 'gpt')

# Слова назви без чисел і службових слів: група «Gemini 3.5 Flash» ↔ модель gemini-3.8-flash-high — спільне «flash».
function Get-NameTokens([string]$Name) {
    $stop = @('gemini', 'high', 'medium', 'low', 'preview', 'latest', 'thinking', 'exp', 'and', 'the', 'models', 'model')
    @(($Name.ToLowerInvariant() -split '[^a-z0-9]+') | Where-Object { $_ -and $_ -notmatch '^[0-9]+$' -and $stop -notcontains $_ })
}

# Власні слова назви — без назв родин (gemini, claude, gpt): «Gemini 4 Argon» -> argon, «Claude and GPT models» -> нічого.
function Get-SpecificTokens([string]$Name) { @(Get-NameTokens $Name | Where-Object { $script:Families -notcontains $_ }) }

# ASCII-код групи для рядка: назва → A-Z0-9, до 16 знаків.
function ConvertTo-GroupCode([string]$Name) {
    $g = ($Name.ToUpperInvariant() -replace '[^A-Z0-9]', '')
    if (-not $g) { $g = 'MODEL' }
    $g.Substring(0, [Math]::Min(16, $g.Length))
}

# Групи моделі: за власними словами («argon», «flash»); нема — група родини без власних слів («Gemini Models»).
function Get-ModelGroups([string]$Model, $Groups) {
    $mt = @(Get-SpecificTokens $Model)
    $hit = @($Groups | Where-Object { $g = $_; @(Get-SpecificTokens $g.Name | Where-Object { $mt -contains $_ }).Count -gt 0 })
    if ($hit.Count -gt 0) { return $hit }
    $fam = ($Model.ToLowerInvariant() -split '-')[0]
    if ($script:Families -notcontains $fam) { return @() }
    @($Groups | Where-Object { @(Get-SpecificTokens $_.Name).Count -eq 0 -and @($_.Name.ToLowerInvariant() -split '[^a-z0-9]+') -contains $fam })
}
