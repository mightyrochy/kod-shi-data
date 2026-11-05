param(
    [string]$КаталогЗапусків = 'C:\Users\gemini\gemini-runs',
    [string]$КаталогЗнімків = (Join-Path $PSScriptRoot 'знімки')
)

# Один вимір без запуску навантаження, зміни меж смуги чи чужих процесів.
# Викликати щонайменше п'ять разів з інтервалом >=300 с за повної смуги.
$ErrorActionPreference = 'Stop'
$початок = [datetime]::UtcNow
$записувач = 'Codex / gemini/вимір-памяті-смуги-codex'
$помилки = [Collections.Generic.List[string]]::new()
$метадані = @(Get-CimInstance Win32_Process)
$процеси = @{}
foreach ($п in $метадані) { $процеси[[int]$п.ProcessId] = $п }
# Win32_Service у цьому обліковому записі повернув 0x80041003 Access denied.
# Повторів і підвищення прав немає; нижче лише видимі системні ознаки.
$межіШлях = Join-Path $КаталогЗапусків 'state\limits.json'
$межі = Get-Content -LiteralPath $межіШлях -Raw -Encoding UTF8 | ConvertFrom-Json
$межа = [int]$межі.'slots.codex'
if ($межа -le 0) { throw 'Немає додатної фактичної межі Codex' }
$слоти = @()
foreach ($файл in @(Get-ChildItem -LiteralPath (Join-Path $КаталогЗапусків 'slots') -Filter 'codex-*.json')) {
    $замок = [IO.Path]::ChangeExtension($файл.FullName, '.lock')
    if (-not (Test-Path -LiteralPath $замок)) { continue }
    $зайнято = $false
    try {
        $потік = [IO.File]::Open($замок, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::None)
        $потік.Dispose()
    } catch [IO.IOException] {
        # Лише sharing/lock violation свідчить про зайнятий слот.
        $код = $_.Exception.HResult -band 65535
        if ($код -in @(32,33)) { $зайнято = $true }
        else { throw }
    }
    if (-not $зайнято) { continue }
    $с = Get-Content -LiteralPath $файл.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    $слоти += [pscustomobject]@{
        слот = $с.slot; позначка = $с.marker; модель = $с.model
        початок_utc = $с.since; pid_обгортки = [int]$с.pid
        обгортка_жива = $процеси.ContainsKey([int]$с.pid)
    }
}

function Знайти-Предка([int]$Номер, [scriptblock]$Умова) {
    # Перевіряє також час створення: повторно використаний PID не є предком.
    $відвідано = @{}
    while ($процеси.ContainsKey($Номер) -and -not $відвідано.ContainsKey($Номер)) {
        $відвідано[$Номер] = $true
        $рядок = $процеси[$Номер]
        if (& $Умова $рядок) { return $Номер }
        $батько = [int]$рядок.ParentProcessId
        if ($процеси.ContainsKey($батько) -and $процеси[$батько].CreationDate -gt $рядок.CreationDate) { break }
        $Номер = $батько
    }
    return $null
}

$сесії = @{}
foreach ($п in $метадані) {
    if ($п.Name -ine 'codex.exe') { continue }
    $слот = $null
    $предок = Знайти-Предка ([int]$п.ProcessId) {
        param($р)
        @($слоти | Where-Object { $_.pid_обгортки -eq [int]$р.ProcessId }).Count -gt 0
    }
    if ($null -ne $предок) { $слот = @($слоти | Where-Object { $_.pid_обгортки -eq $предок })[0].слот }
    $сесії[[int]$п.ProcessId] = $слот
}

$рядки = @(foreach ($п in $метадані) {
    $номер = [int]$п.ProcessId
    $корінь = Знайти-Предка $номер { param($р) $р.Name -ieq 'codex.exe' }
    $лм = Знайти-Предка $номер {
        param($р)
        $р.Name -match '^(LM Studio|llmster|lms)(\.exe)?$' -or
        $р.ExecutablePath -match '(?i)[\\/](LM Studio|\.lmstudio)[\\/]'
    }
    $група = 'решта'
    if ($null -ne $корінь) {
        $група = $(if ($номер -eq $корінь) { 'codex' } else { 'дочірні_codex' })
    } elseif ($null -ne $лм) { $група = 'LM_Studio' }
    elseif ($п.SessionId -eq 0 -or
        $п.ExecutablePath -like "$env:windir\*" -or
        $п.Name -in @('System','Registry','Memory Compression','Secure System')) { $група = 'Windows_і_служби' }
    $набір = $null; $приватні = $null; $джерело = 'Get-Process'
    try {
        $живий = Get-Process -Id $номер -ErrorAction Stop
        # Метадані й лічильники знімаються послідовно, тому PID треба звіряти.
        if ($живий.ProcessName -ine [IO.Path]::GetFileNameWithoutExtension($п.Name)) { throw 'PID змінив власника' }
        if ($п.CreationDate -and [math]::Abs(($живий.StartTime.ToUniversalTime() - $п.CreationDate.ToUniversalTime()).TotalSeconds) -gt 1) { throw 'PID змінив час створення' }
        $набір = [long]$живий.WorkingSet64
        $приватні = [long]$живий.PrivateMemorySize64
        $живий.Dispose()
    } catch {
        # CIM містить ті самі величини для захищених чи вже завершених процесів.
        $набір = $(if ($null -ne $п.WorkingSetSize) { [long]$п.WorkingSetSize } else { $null })
        $приватні = $(if ($null -ne $п.PrivatePageCount) { [long]$п.PrivatePageCount } else { $null })
        $джерело = 'Win32_Process (час переліку процесів)'
        $помилки.Add("PID ${номер}: Get-Process недоступний; збережено CIM")
    }
    [pscustomobject]@{
        pid = $номер; ppid = [int]$п.ParentProcessId; назва = [string]$п.Name
        створено_utc = $(if ($п.CreationDate) { $п.CreationDate.ToUniversalTime().ToString('o') } else { $null })
        шлях = $п.ExecutablePath; група = $група; pid_сесії = $корінь
        слот = $(if ($null -ne $корінь) { $сесії[[int]$корінь] } else { $null })
        робочий_набір_байт = $набір; приватні_байти = $приватні; джерело = $джерело
    }
})
$ос = Get-CimInstance Win32_OperatingSystem
$групи = @(foreach ($г in @($рядки | Group-Object група)) {
    [pscustomobject]@{
        група = $г.Name; процесів = $г.Count
        робочий_набір_байт = ($г.Group | Measure-Object робочий_набір_байт -Sum).Sum
        приватні_байти = ($г.Group | Measure-Object приватні_байти -Sum).Sum
        невідомий_набір = @($г.Group | Where-Object { $null -eq $_.робочий_набір_байт }).Count
        невідомі_приватні = @($г.Group | Where-Object { $null -eq $_.приватні_байти }).Count
    }
})
$знімок = [ordered]@{
    версія = 1; записувач = $записувач; початок_utc = $початок.ToString('o')
    кінець_utc = [datetime]::UtcNow.ToString('o'); машина = $ос.CSName
    джерело_межі = 'gemini-runs/state/limits.json'; фактична_межа = $межа
    зайнято = $слоти.Count; повна_смуга = ($слоти.Count -eq $межа)
    слотів_без_живої_обгортки = @($слоти | Where-Object { -not $_.обгортка_жива }).Count
    слотів_без_codex = @($слоти | Where-Object { $сесії.Values -notcontains $_.слот }).Count
    слотів = $слоти; процесів = $рядки; групи = $групи
    фізична_всього_байт = [long]$ос.TotalVisibleMemorySize * 1024
    фізична_вільна_байт = [long]$ос.FreePhysicalMemory * 1024
    фізична_зайнята_байт = ([long]$ос.TotalVisibleMemorySize - [long]$ос.FreePhysicalMemory) * 1024
    віртуальна_всього_байт = [long]$ос.TotalVirtualMemorySize * 1024
    віртуальна_вільна_байт = [long]$ос.FreeVirtualMemory * 1024
    зауваження = @(
        'Робочі набори містять спільні сторінки: їх сума не дорівнює зайнятій фізичній RAM.'
        "Приватні байти — зобов’язання процесу, включно з вивантаженими сторінками, не фізична RAM."
        'Windows_і_служби — процеси; ядро, кеш і драйвери окремо цим знімком не виміряні.'
        'Win32_Service: 0x80041003 Access denied; системна група за SessionId=0, шляхом Windows і системними назвами.'
        'Командні рядки, оточення й вміст задач не записуються.'
    ); запасне_джерело = @($помилки)
}
New-Item -ItemType Directory -Path $КаталогЗнімків -Force | Out-Null
$шлях = Join-Path $КаталогЗнімків ($початок.ToString('yyyyMMddTHHmmssfffZ') + '.json')
[IO.File]::WriteAllText($шлях, ($знімок | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
[pscustomobject]@{
    файл = $шлях; зайнято = $слоти.Count; межа = $межа; повна_смуга = $знімок.повна_смуга
    процесів = $рядки.Count; сесій = $сесії.Count; групи = $групи
} | ConvertTo-Json -Depth 4
