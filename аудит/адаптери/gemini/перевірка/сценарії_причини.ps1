#Requires -Version 5.1
<# Кожен клас причини запуску без результату доходить до `cause.json` теки прогону через справжні Complete-Status і
Write-RunCause — звідти його бере вивантаження витрат. До правки файла причини нема. #>
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('cause-' + [guid]::NewGuid().ToString('N'))
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожна перевірка впливає на код виходу стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    foreach ($d in @('runs', 'out', 'repo')) { [void][IO.Directory]::CreateDirectory("$tmp/$d") }
    . (Join-Path $SourceDir 'gemini_run.ps1') -RepoDir "$tmp/repo" -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes"
    $past = [datetime]::UtcNow.AddYears(-5).ToString('o')
    $future = [datetime]::UtcNow.AddMinutes(5).ToString('o')
    # порожній код Complete-Status читає як INTERRUPTED (вимкнення зупинило конвеєр).
    # код кінця, хвіст звіту, причина догонки, старт → очікуваний клас і початок тексту
    $cases = @(
        @('QUOTA', '', '', $future, 'квота', 'QUOTA'),
        @('STALL', '', '', $future, 'модель', 'STALL'),
        @('NO_REPORT', '', 'none', $future, 'модель', 'NO_REPORT: нема звіту'),
        @('BLOCKED', "зроблено частину`nЗАБЛОКОВАНО: голова PR #1 змінилася; чекаю нової позначки", '', $future, 'умови наряду', 'ЗАБЛОКОВАНО: голова PR #1'),
        @('BLOCKED', 'ЗАБЛОКОВАНО: LIVE_AFTER_INVALID — рядок без сцени', '', $future, 'модель', 'ЗАБЛОКОВАНО: LIVE_AFTER_INVALID'),
        @('BLOCKED', "зроблено`n**ЗАБЛОКОВАНО: чекаю номера дошки**", '', $future, 'умови наряду', 'ЗАБЛОКОВАНО: чекаю номера дошки'),
        @('BLOCKED', "зроблено`n``ЗАБЛОКОВАНО: чекаю номера дошки``", '', $future, 'умови наряду', 'ЗАБЛОКОВАНО: чекаю номера дошки'),
        @('INTERRUPTED', '', '', $past, 'ноутбук і обгортка', 'INTERRUPTED: перезавантаження ОС'),
        @('INTERRUPTED', '', '', $future, 'ноутбук і обгортка', 'INTERRUPTED: процес наряду зник без'),
        @('NO_REPORT', '', 'mismatch', $future, 'ноутбук і обгортка', 'NO_REPORT: звіт не прийнято'),
        @('AGY_ERROR', '', '', $future, 'невідомо', 'AGY_ERROR'),
        @('', '', '', $future, 'ноутбук і обгортка', 'INTERRUPTED: процес наряду зник без'),
        @('DONE', '', '', $future, '', ''))
    $i = 0
    foreach ($c in $cases) {
        $i++
        $id = '20261113-0000{0:00}-aaaaaaaaaaaa' -f $i
        [void][IO.Directory]::CreateDirectory("$tmp/runs/$id")
        $s = [ordered]@{ v = 1; id = $id; slug = 'probe'; marker = ''; start = ''; head = ''; ahead = 0; bundle = ''; code = $c[0]
            turns = 1; minutes = 0; started_utc = $c[3]; ended_utc = '' }
        Complete-Status $s "$tmp/runs/state-$i.txt" $c[1] ([datetime]::MinValue) $c[2]
        $f = "$tmp/runs/$id/cause.json"
        $j = $(if (Test-Path -LiteralPath $f) { [IO.File]::ReadAllText($f) | ConvertFrom-Json } else { $null })
        $ok = $null -ne $j -and $j.class -ceq $c[4] -and ([string]$j.text).StartsWith($c[5]) -and $j.code -ceq $(if ($c[0]) { $c[0] } else { 'INTERRUPTED' })
        Check "$($c[0]) ($($c[2])) → «$($c[4])»: $(if ($j) { "$($j.class) | $($j.text)" } else { 'cause.json нема' })" $ok
    }
    # Текст помилки рушія без звіту агента: повний хвіст — у <id>.tail.txt, один рядок без приватного — у <id>.json (`reason`)
    # і в примітці blocked-reasons.json (#1856), коли гілки нема. До правки кінець AGY_ERROR не лишав тексту ніде.
    $engineText = @('stream disconnected before completion', 'Cannot open C:\Users\Тест\gemini-runs\w\x.tmp', 'останній рядок помилки рушія') -join "`n"
    foreach ($ec in @('AGY_ERROR', 'TIMEOUT', 'QUOTA', 'AUTH', 'EFFORT_INVALID')) {
        $i++
        $id = '20261113-0000{0:00}-dddddddddddd' -f $i
        [void][IO.Directory]::CreateDirectory("$tmp/runs/$id")
        $s = [ordered]@{ v = 1; id = $id; slug = "рушій-$ec"; marker = ''; start = ''; head = ''; ahead = 0; bundle = ''; code = $ec
            turns = 1; minutes = 0; started_utc = $future; ended_utc = '' }
        Complete-Status $s "$tmp/runs/state-$i.txt" $engineText ([datetime]::MinValue) '' $engineText
        $j = [IO.File]::ReadAllText("$tmp/out/$id.json") | ConvertFrom-Json
        $full = $(if (Test-Path -LiteralPath "$tmp/out/$id.tail.txt") { [IO.File]::ReadAllText("$tmp/out/$id.tail.txt") } else { '' })
        $note = @(Read-JsonArray "$tmp/out/blocked-reasons.json" | Where-Object { $_.marker -ceq "gemini/рушій-$ec" })
        Check "${ec}: tail.txt — повний хвіст помилки рушія" ($full.Contains('stream disconnected') -and $full.Contains('Тест') -and $full.Contains('останній рядок'))
        Check "${ec}: <id>.json reason — останній рядок" ([bool]$j.PSObject.Properties['reason'] -and $j.reason -ceq 'останній рядок помилки рушія')
        Check "${ec}: примітка #1856 «${ec}: <рядок>»" ($note.Count -eq 1 -and $note[0].text -ceq "${ec}: останній рядок помилки рушія")
    }
    # Приватне не йде в публічні поля: шлях профілю, заголовок авторизації, ключ, облікові дані URL (подія error Codex — JSON).
    $private = '{"type":"error","message":"Cannot open C:\\Users\\Тест\\x.tmp: Authorization: Bearer abcdefghijkl1234 api_key=abcdefghijklmnop12345 https://u:p@host/x"}'
    $i++
    $id = '20261113-0000{0:00}-eeeeeeeeeeee' -f $i
    [void][IO.Directory]::CreateDirectory("$tmp/runs/$id")
    $s = [ordered]@{ v = 1; id = $id; slug = 'рушій-приватне'; marker = ''; start = ''; head = ''; ahead = 0; bundle = ''; code = 'AUTH'
        turns = 1; minutes = 0; started_utc = $future; ended_utc = '' }
    Complete-Status $s "$tmp/runs/state-$i.txt" '' ([datetime]::MinValue) '' $private
    $j = [IO.File]::ReadAllText("$tmp/out/$id.json") | ConvertFrom-Json
    $note = @(Read-JsonArray "$tmp/out/blocked-reasons.json" | Where-Object { $_.marker -ceq 'gemini/рушій-приватне' })
    Check 'публічні поля: шлях профілю, Bearer, ключ і облікові дані URL прибрано' ($note.Count -eq 1 -and "$($j.reason) $($note[0].text)" -notmatch 'Тест|abcdefghijkl|u:p@' -and $j.reason -match 'Cannot open')
    # З комітами в гілці гілка йде бандлом, а не рядком «без гілки»; код без помилки рушія (DONE) reason не отримує.
    foreach ($case in @(@('AGY_ERROR', 2, 'рушій-з-гілкою'), @('DONE', 0, 'рушій-готово'))) {
        $i++
        $id = '20261113-0000{0:00}-ffffffffffff' -f $i
        [void][IO.Directory]::CreateDirectory("$tmp/runs/$id")
        $s = [ordered]@{ v = 1; id = $id; slug = $case[2]; marker = ''; start = ''; head = ''; ahead = $case[1]; bundle = ''; code = $case[0]
            turns = 1; minutes = 0; started_utc = $future; ended_utc = '' }
        Complete-Status $s "$tmp/runs/state-$i.txt" '' ([datetime]::MinValue) '' $engineText
        $j = [IO.File]::ReadAllText("$tmp/out/$id.json") | ConvertFrom-Json
        $hasNote = @(Read-JsonArray "$tmp/out/blocked-reasons.json" | Where-Object { $_.marker -ceq "gemini/$($case[2])" }).Count
        $want = $case[0] -ceq 'AGY_ERROR'
        Check "$($case[0]) з комітами $($case[1]): примітки нема, reason $(if ($want) { 'є' } else { 'нема' })" ($hasNote -eq 0 -and ([bool]$j.PSObject.Properties['reason']) -eq $want)
    }
    # Обрамлення не потрапляє в текст причини, а Test-Report і пошук причини читають рядок однаково.
    $t = "зроблено`n**ЗАБЛОКОВАНО: чекаю номера дошки**"
    Check 'обрамлення `**…**` знято з тексту причини' ((Get-RunCause 'BLOCKED' $t).Text -ceq 'ЗАБЛОКОВАНО: чекаю номера дошки')
    Check 'Get-BlockedLine: без рядка — $null' ($null -eq (Get-BlockedLine "зроблено`nнічого"))
    # Прогін, чия позначка вертається в чергу (квота посеред прогону, стан PR), кінця в теці обміну не має — причина є.
    foreach ($w in @(@('QUOTA', 'квота'), @('REVIEW_API', 'ноутбук і обгортка'), @('PLAN_WAIT', 'умови наряду'), @('COPY_FAILED', 'ноутбук і обгортка'))) {
        $i++
        $id = '20261113-0000{0:00}-bbbbbbbbbbbb' -f $i
        [void][IO.Directory]::CreateDirectory("$tmp/runs/$id")
        Write-RunCause $id $w[0] (Get-RunCause $w[0])
        $j = [IO.File]::ReadAllText("$tmp/runs/$id/cause.json") | ConvertFrom-Json
        Check "чекання $($w[0]) → «$($w[1])»" ($j.class -ceq $w[1] -and -not (Test-Path -LiteralPath "$tmp/out/$id.json"))
    }
    Write-RunCause '20261113-999999-cccccccccccc' 'CRASH' (Get-RunCause 'CRASH')
    Check 'прогін без теки — файла не створено' (-not (Test-Path -LiteralPath "$tmp/runs/20261113-999999-cccccccccccc"))
} catch {
    "✗ збій стенда: $($_.Exception.Message)"; $bad++
} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
exit ([int]($bad -gt 0))
