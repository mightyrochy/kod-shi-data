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
    # код кінця, хвіст звіту, причина догонки, старт → очікуваний клас і початок тексту
    $cases = @(
        @('QUOTA', '', '', $future, 'квота', 'QUOTA'),
        @('STALL', '', '', $future, 'модель', 'STALL'),
        @('NO_REPORT', '', 'none', $future, 'модель', 'NO_REPORT: нема звіту'),
        @('BLOCKED', "зроблено частину`nЗАБЛОКОВАНО: голова PR #1 змінилася; чекаю нової позначки", '', $future, 'умови наряду', 'ЗАБЛОКОВАНО: голова PR #1'),
        @('BLOCKED', 'ЗАБЛОКОВАНО: LIVE_AFTER_INVALID — рядок без сцени', '', $future, 'модель', 'ЗАБЛОКОВАНО: LIVE_AFTER_INVALID'),
        @('INTERRUPTED', '', '', $past, 'ноутбук і обгортка', 'INTERRUPTED: перезавантаження ОС'),
        @('INTERRUPTED', '', '', $future, 'ноутбук і обгортка', 'INTERRUPTED: процес наряду зник без'),
        @('NO_REPORT', '', 'mismatch', $future, 'ноутбук і обгортка', 'NO_REPORT: звіт не прийнято'),
        @('AGY_ERROR', '', '', $future, 'невідомо', 'AGY_ERROR'),
        @('', '', '', $future, 'ноутбук і обгортка', 'код кінця порожній: процес наряду зупинено'),
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
        $ok = $null -ne $j -and $j.class -ceq $c[4] -and ([string]$j.text).StartsWith($c[5]) -and $j.code -ceq $c[0]
        Check "$($c[0]) ($($c[2])) → «$($c[4])»: $(if ($j) { "$($j.class) | $($j.text)" } else { 'cause.json нема' })" $ok
    }
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
