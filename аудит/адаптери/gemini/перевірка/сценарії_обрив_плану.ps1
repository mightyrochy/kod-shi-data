#Requires -Version 5.1
<# Стенд наряду «Обгортка-автоживий-обрив-не-губить» (18.11): 17.11 нічний автоживий обірвався (`NO_REPORT`) після
частини сцен, записи лишились лише на диску ноутбука, і наступний план брав усі сцени збірки знову. Тут — справжні
`Get-AutoLivePlan` обгортки і справжній `аудит/проби/записати_план.py` (підмінено лише прилад сцени: повний запис сцени,
а на сцені після N-ї — обрив батька, як світло чи зупинка рушія) і мережа GitHub (`Get-AutoPublicItems`).
Мірила: обрив після N сцен із M → наступний план має M − N (ДО — M); повтор на тій самій гілці не губить сцен першої
спроби; сцена найновішого PR — перша; хмарна тека в дереві збірки лічить пару прогнаною. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('obryv-planu-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожен провал мірила лишається червоним і впливає на код завершення. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Write-Log([string]$Text) {
    <# queue_lanes.ps1 вимагає від хазяїна функцію журналу. #>
    Write-Host "  журнал обгортки: $Text"
}
function Scenario([string]$Name, [scriptblock]$Body) {
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/gem-out" -OutboxDir "$tmp/out"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, "$WorkDir/state", "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $LaneDir = Join-Path $tmp 'lanes'; [void][IO.Directory]::CreateDirectory($LaneDir)
    . (Join-Path $SourceDir 'queue_lanes.ps1')
    $python = $(if (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { 'python3' })
    $repo = Join-Path $tmp 'repo'; $origin = Join-Path $tmp 'origin.git'
    & git init -q -b main $repo; & git init -q --bare $origin
    & git -C $repo config user.name 'Стенд'; & git -C $repo config user.email 'stand@local'; & git -C $repo config core.autocrlf false
    & git -C $repo remote add origin $origin
    $script:RepoDir = $repo; $script:Repo = $repo; $script:NoHooks = Join-Path $tmp 'no-hooks'
    [void][IO.Directory]::CreateDirectory("$repo/аудит/проби")
    [IO.File]::WriteAllText("$repo/аудит/проби/живі_сцени.txt", [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf), $utf)
    function Repo-Commit([string]$Date, [string]$Name) {
        $author = $env:GIT_AUTHOR_DATE; $committer = $env:GIT_COMMITTER_DATE
        try {
            $env:GIT_AUTHOR_DATE = $Date; $env:GIT_COMMITTER_DATE = $Date
            & git -C $repo add -A
            & git -C $repo commit -q --allow-empty -m $Name
            if ($LASTEXITCODE) { throw 'Не створено коміт' }
            (& git -C $repo rev-parse HEAD).Trim()
        } finally { $env:GIT_AUTHOR_DATE = $author; $env:GIT_COMMITTER_DATE = $committer }
    }
    $null = Repo-Commit '2026-11-01T00:00:00Z' 'Реєстр'
    # П'ять злитих PR на чотири сцени; PR 105 — найновіший, другим питанням до сцени PR 102.
    $ids = @('ж1_робота', 'ж2_побачення_вечір', 'ж2_похорон', 'ж3_свято_др')
    $scenesOf = @{101 = $ids[0]; 102 = $ids[1]; 103 = $ids[2]; 104 = $ids[3]; 105 = $ids[1]}
    $merges = @{}
    $script:Merged = @()
    foreach ($n in 101..105) {
        $date = '2026-11-01T0' + ($n - 100) + ':00:00Z'
        $merges[$n] = Repo-Commit $date "Злиття $n"
        $script:Merged += [pscustomobject]@{number = $n; user = @{login = 'mightyrochy'}; head = @{ref = "claude/код-$n"; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merge_commit_sha = $merges[$n]; merged_at = $date; created_at = $date; updated_at = $date
            body = "ЖИВИЙ ПІСЛЯ: $($scenesOf[$n]) — питання $n"}
    }
    $build = $merges[105]
    $branch = "claude/автоживий-$build"
    function Report-Pull([string]$Head) {
        <# Звіт обірваного прогону: гілка автоживого, голова — що встигло в гілку, без рядка `ПЕРЕВІРЕНО ЗБІРКУ`. #>
        [pscustomobject]@{number = 900; user = @{login = 'mightyrochy'}; head = @{ref = $branch; sha = $Head; repo = @{full_name = 'mightyrochy/kod-shi-data'}}
            base = @{ref = 'main'; repo = @{full_name = 'mightyrochy/kod-shi-data'}}; merged_at = $null; created_at = '2026-11-01T06:00:00Z'
            updated_at = '2026-11-01T07:00:00Z'; body = 'Звіт обірвано: NO_REPORT'}
    }
    $script:PlanPulls = @($script:Merged)
    function Get-AutoPublicItems { $script:PlanPulls }
    function Plan-Scenes([string]$Main) { @((ConvertFrom-Json (Get-AutoLivePlan $Main)).scenes.PSObject.Properties | ForEach-Object { $_.Name }) }
    # Справжній записувач плану поруч із підміною приладу сцени.
    $runner = Join-Path $tmp 'runner'; [void][IO.Directory]::CreateDirectory($runner)
    Copy-Item -LiteralPath (Join-Path $SourceDir '../../проби/записати_план.py') -Destination (Join-Path $runner 'записати_план.py')
    $fake = @'
"""Підміна приладу сцени: повний запис сцени, а на сцені після STAND_BREAK-ї — початок запису й обрив батька."""
import json, os, signal, sys
from pathlib import Path


def режим_питання(питання):
    return None


def сцена_реєстру(id_, режим):
    return None


def вхід_реєстру(id_):
    return ""


def змінні_режиму(id_, режим, вхід):
    return {}


if __name__ == "__main__":
    тека = Path(sys.argv[3])
    лічильник = Path(os.environ["STAND_COUNTER"])
    номер = int(лічильник.read_text() if лічильник.exists() else "0") + 1
    лічильник.write_text(str(номер))
    тека.mkdir(parents=True, exist_ok=True)
    (тека / "лог.txt").write_text("сцена\n", encoding="utf-8")
    if номер > int(os.environ["STAND_BREAK"]):
        os.kill(os.getppid(), signal.SIGTERM)
        sys.exit(1)
    for шлях, вміст in {"результат.json": json.dumps({"rc": 0, "sha": os.environ["STAND_CODE"]}), "повтор.json": "{}",
                        "знімки/доказ.json": "{}", "VIDPOVIDI/обмін/1.json": "{}"}.items():
        (тека / шлях).parent.mkdir(parents=True, exist_ok=True)
        (тека / шлях).write_text(вміст, encoding="utf-8")
'@
    [IO.File]::WriteAllText((Join-Path $runner 'записати_сцену.py'), $fake, $utf)
    $out = Join-Path $repo "аудит/проби/автоживий-$build"
    $planPath = Join-Path $out 'ПЛАН.json'
    function Run-Plan([string]$Plan, [int]$Break, [string[]]$Extra) {
        <# Пише план у теку прогону й запускає записувач; обрив на сцені Break+1. #>
        [void][IO.Directory]::CreateDirectory($out)
        [IO.File]::WriteAllText($planPath, $Plan, $utf)
        $counter = Join-Path $tmp ('counter-' + [guid]::NewGuid().ToString('N'))
        $env:STAND_COUNTER = $counter; $env:STAND_BREAK = [string]$Break; $env:STAND_CODE = $build
        & $python (Join-Path $runner 'записати_план.py') $planPath (Join-Path $tmp 'build') (Join-Path $tmp 'cache') $out @Extra 2>&1 | ForEach-Object { "  записувач: $_" } | Out-Host
        [int](Get-Content -LiteralPath $counter -Raw)
    }
    $plan1 = Get-AutoLivePlan $build
    $order1 = @(Plan-Scenes $build)
    $M = $order1.Count
    $N = 2

    Scenario '1 порядок' {
        Check '1 план: чотири сцени на п''ять питань' ($M -eq 4 -and @((ConvertFrom-Json $plan1).scenes.($ids[1])).Count -eq 2)
        "ДАНІ порядок: $($order1 -join ', ') (за злиттям — $($ids -join ', '))"
        Check '1 сцена найновішого PR (105) — перша, далі від новішого злиття до давнішого' (($order1 -join ',') -ceq (@($ids[1], $ids[3], $ids[2], $ids[0]) -join ','))
    }
    Scenario '2 обрив' {
        & git -C $repo checkout -q -b $branch
        # ДО: записувач без коміту (як до наряду: усе — комітом агента в кінці) — у гілці звіту нічого.
        $calls = Run-Plan $plan1 $N @('--без-коміту')
        Check '2 ДО: обрив на сцені N+1' ($calls -eq $N + 1)
        $script:PlanPulls = @($script:Merged) + @(Report-Pull ((& git -C $repo rev-parse HEAD).Trim()))
        $before = (Plan-Scenes $build).Count
        Remove-Item -LiteralPath $out -Recurse -Force
        # ПІСЛЯ: коміт і пуш після кожної сцени.
        $calls = Run-Plan $plan1 $N @('--пуш', $branch)
        $script:Head1 = (& git -C $origin rev-parse "refs/heads/$branch").Trim()
        Check '2 ПІСЛЯ: записане до обриву — у гілці звіту на origin' ($calls -eq $N + 1 -and $script:Head1 -ceq (& git -C $repo rev-parse HEAD).Trim())
        $script:PlanPulls = @($script:Merged) + @(Report-Pull $script:Head1)
        $script:Plan2 = Get-AutoLivePlan $build
        $after = @((ConvertFrom-Json $script:Plan2).scenes.PSObject.Properties | ForEach-Object { $_.Name })
        "ДАНІ обрив: після $N записаних сцен із $M наступний план — $($after.Count) (ДО — $before)"
        Check '2 ДО: наступний план — усі M сцен' ($before -eq $M)
        Check '2 ПІСЛЯ: наступний план — M − N, непрогнані в тому самому порядку' ($after.Count -eq $M - $N -and ($after -join ',') -ceq (@($order1 | Select-Object -Skip $N) -join ','))
    }
    Scenario '3 повтор на тій самій гілці' {
        # Друга спроба з планом після обриву: сцена N+1 (почата й обірвана) відкладається в `спроби/`, далі — ще обрив.
        $calls = Run-Plan $script:Plan2 1 @('--пуш', $branch)
        $head2 = (& git -C $origin rev-parse "refs/heads/$branch").Trim()
        $script:PlanPulls = @($script:Merged) + @(Report-Pull $head2)
        $third = @(Plan-Scenes $build)
        "ДАНІ повтор: після другої спроби план — $($third.Count) ($($third -join ', '))"
        Check '3 записи першої спроби (за її головою з reports плану) і другої — прогнані' ($calls -eq 2 -and ($third -join ',') -ceq $order1[-1])
        $moved = @((& git -C $repo -c core.quotepath=false ls-tree -d --name-only $head2 -- "аудит/проби/автоживий-$build/спроби/") | ForEach-Object { ($_ -split '/')[-1] })
        Check '3 обірвана тека сцени відкладена в спроби/, а не змішана з новим записом' ($moved -contains ($order1[$N] + '-1'))
    }
    Scenario '4 хмарна тека' {
        & git -C $repo checkout -q main
        $cloudDir = "$repo/аудит/проби/Тестовий-прогін-хмара-стенд"
        $record = "$cloudDir/$($ids[0])"
        foreach ($sub in @('знімки', 'VIDPOVIDI/обмін')) { [void][IO.Directory]::CreateDirectory("$record/$sub") }
        [IO.File]::WriteAllText("$cloudDir/ПЛАН.json", (ConvertTo-Json -Compress -Depth 5 @{build = $build; scenes = @{$ids[0] = @(@{pr = 101; question = 'питання 101'})}}), $utf)
        [IO.File]::WriteAllText("$cloudDir/done.txt", ('{"сцена": "' + $ids[0] + '", "rc": 0, "секунд": 300}' + "`n"), $utf)
        [IO.File]::WriteAllText("$record/результат.json", ('{"rc": 0, "sha": "' + $build + '"}'), $utf)
        foreach ($file in @('повтор.json', 'лог.txt', 'знімки/доказ.json', 'VIDPOVIDI/обмін/1.json')) { [IO.File]::WriteAllText("$record/$file", '{}', $utf) }
        $withCloud = Repo-Commit '2026-11-02T00:00:00Z' 'Хмарний прогін'
        $script:PlanPulls = @($script:Merged)
        $without = (Get-AutoRanPairs @() ([datetimeoffset]::MinValue)).Count
        $pairs = Get-AutoRanPairs @() ([datetimeoffset]::MinValue) $withCloud
        Check '4 без дерева збірки хмарних пар нема (ДО)' ($without -eq 0)
        Check '4 пара хмарного прогону — прогнана' ($pairs.ContainsKey("101|$($ids[0])") -and $pairs.Count -eq 1)
        $cloudPlan = @(Plan-Scenes $withCloud)
        "ДАНІ хмара: сцен у плані збірки з хмарною текою — $($cloudPlan.Count) (без неї — $M)"
        Check '4 план не повторює сцену, яку прогнала хмара' ($cloudPlan.Count -eq $M - 1 -and $ids[0] -cnotin $cloudPlan)
    }
} finally {
    $env:STAND_COUNTER = $null; $env:STAND_BREAK = $null; $env:STAND_CODE = $null
    if ((Split-Path -Parent $tmp) -eq [IO.Path]::GetTempPath().TrimEnd('\', '/') -and (Split-Path -Leaf $tmp) -cmatch '^obryv-planu-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmp -Recurse -Force }
}
if ($bad) { exit 1 }
