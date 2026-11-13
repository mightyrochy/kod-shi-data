#Requires -Version 5.1
<# Відмова до STARTED (gemini-run): кінцевий CRASH на межі MaxRetakes несе причину останньої відмови (blocked-reasons.json,
звідки її бере розділ «Причини ЗАБЛОКОВАНО без гілки» в #1856) і справжній рушій позначки, а не сталу `agy`. #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('vidmova-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$utf = New-Object Text.UTF8Encoding($false)
$bad = 0
function Check([string]$Name, [bool]$Ok) { if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ } }
try {
    . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/update"
    $script:StateDir = "$RunsDir/state"; $script:SlotDir = "$RunsDir/slots"
    foreach ($dir in @($RunsDir, $script:StateDir, $script:SlotDir, $OutDir, $LaneDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $script:Seq = 0
    function NewMarker([string]$Slug, [string]$Model) {
        $name = "gemini-queue/$Slug/$Model/1"
        [pscustomobject]@{ Ref = "refs/remotes/origin/$name"; Name = $name; Sha = ('c' * 40); Slug = $Slug; Model = $Model; N = '1'; Cond = '' }
    }
    function Fail($M, [string]$Reason, [string]$Engine = '') {
        <# Одна відмова до запуску: узяття позначки й Close-FailedStart, як у Start-Markers чи в процесі наряду. #>
        $script:Seq++
        $id = '20261113-100000-' + ('{0:x12}' -f $script:Seq)
        [void](New-Claim $M $id)
        [void](Close-FailedStart $M $id (Get-StatePath (Get-MarkerKey $M)) $Reason $Engine)
        $id
    }
    function Status([string]$Id) { [IO.File]::ReadAllText((Join-Path $OutDir "$Id.json"), $utf) | ConvertFrom-Json }
    function WaitJson($M) { [IO.File]::ReadAllText((Get-StatePath (Get-MarkerKey $M)), $utf).Substring(5) | ConvertFrom-Json }
    function Notes { @(Read-JsonArray (Join-Path $OutDir 'blocked-reasons.json')) }
    $limit = $script:MaxRetakes + 1

    # Чистильник причини: профіль користувача, облікові дані в URL і керівні символи не доходять до примітки.
    $raw = [IO.IOException]::new("Process cannot access 'C:\Users\Тест\gemini-runs\w\x.tmp'`nlog C:\Users\Public\gemini\out https://x-access-token:ghp_abcdefghijkl1234@github.com/o/r")
    $clean = Get-FailReason $raw
    Check 'причина: шлях профілю замінено' ($clean -notmatch 'Тест' -and $clean -match '~\\gemini-runs')
    Check 'причина: спільна тека Public лишається' ($clean -match 'C:\\Users\\Public\\gemini\\out')
    Check 'причина: облікові дані в URL прибрано' ($clean -notmatch 'ghp_|x-access-token' -and $clean -match 'https://github.com/o/r')
    Check 'причина: один рядок розумної довжини' ($clean -notmatch '[\r\n]' -and (Get-FailReason ('х' * 500)).Length -le 240 -and $clean.StartsWith('IOException: '))

    # gpt-* без вибору планувальника: рушій Codex, як у Get-Engine; перші MaxRetakes відмов — лише чекання з причиною.
    $m = NewMarker 'Живий-як-людина-1-суддя' 'gpt-6.1-astra-max'
    $sp = Get-StatePath (Get-MarkerKey $m)
    for ($i = 1; $i -le $script:MaxRetakes; $i++) {
        $id = Fail $m "відмова $i"
        Check "спроба $i з ${limit}: позначка в чекання, кінцевого стану нема" ((Get-MarkerState $m).Kind -ceq 'WAIT' -and (Get-Retakes $sp) -eq $i -and -not (Test-Path (Join-Path $OutDir "$id.json")))
        Check "спроба ${i}: причина лежить у стані чекання (група START)" ((WaitJson $m).group -ceq 'START' -and (WaitJson $m).reason -ceq "відмова $i")
    }
    Check 'до межі приміток CRASH нема' (@(Notes).Count -eq 0)
    $id = Fail $m 'остання відмова'
    $st = Status $id
    Check "спроба ${limit}: кінцевий стан CRASH" ($st.code -ceq 'CRASH' -and $st.slug -ceq $m.Slug -and (Get-Content -LiteralPath $sp -Raw).StartsWith("DONE $id CRASH"))
    Check 'engine gpt-* без вибору — codex, не стала agy' ($st.engine -ceq 'codex')
    $note = @(Notes)[-1]
    Check "нотатка: наряд gemini/<наряд>, 'CRASH до запуску ($limit спроб): <причина>'" ($note.marker -ceq "gemini/$($m.Slug)" -and $note.text -ceq "CRASH до запуску ($limit спроб): остання відмова")
    Check 'на межі claim знято' (-not (Test-Path (Get-ClaimPath $sp)))

    # Остання спроба без власної причини (збій без тексту) — несе причину попередньої з чекання.
    $m2 = NewMarker 'без-причини-в-кінці' 'gpt-6.1-astra-max'
    for ($i = 1; $i -le $script:MaxRetakes; $i++) { [void](Fail $m2 "ще відмова $i") }
    $id2 = Fail $m2 ''
    Check 'порожня причина на межі — остання з чекання' (@(Notes)[-1].text -ceq "CRASH до запуску ($limit спроб): ще відмова $script:MaxRetakes" -and (Status $id2).code -ceq 'CRASH')

    # Рушій: вибраний планувальником сильніший за назву моделі; gemini-* без вибору — agy.
    foreach ($case in @(
        @{ slug = 'рушій-agy'; model = 'gemini-4-argon-high'; sel = ''; want = 'agy' },
        @{ slug = 'рушій-каскад'; model = 'gpt-6.1-astra-max'; sel = 'agy'; want = 'agy' },
        @{ slug = 'рушій-codex'; model = 'gemini-4-argon-high'; sel = 'codex'; want = 'codex' })) {
        $mc = NewMarker $case.slug $case.model
        for ($i = 1; $i -le $script:MaxRetakes; $i++) { [void](Fail $mc 'відмова' $case.sel) }
        Check "engine $($case.model) / вибір '$($case.sel)' → $($case.want)" ((Status (Fail $mc 'відмова' $case.sel)).engine -ceq $case.want)
    }

    # Квота Codex (quota-codex.json): вимір після ходу й відмова квоти пишуть той самий файл — під одним замком, без втрат.
    $qf = Join-Path $RunsDir 'quota-codex.json'
    $ch = Join-Path $tmp 'codexhome'; $env:CODEX_HOME = $ch
    $day = Join-Path $ch 'sessions/2026/11/13'; [void][IO.Directory]::CreateDirectory($day)
    $at = [datetime]::UtcNow.AddMinutes(-2)
    # Рядок журналу Codex у звичайному (з пробілами) JSON — читач не залежить від компактного друку serde.
    $line = '{ "timestamp": "' + $at.ToString("yyyy-MM-dd'T'HH:mm:ss.fff'Z'") + '", "type": "event_msg", "payload": { "type": "token_count", "info": null, "rate_limits": { "limit_id": "codex", "primary": { "used_percent": 12.5, "window_minutes": 300, "resets_at": ' + [DateTimeOffset]::UtcNow.AddHours(1).ToUnixTimeSeconds() + ' }, "secondary": { "used_percent": 49, "window_minutes": 10080, "resets_at": null } } } }'
    [IO.File]::WriteAllText((Join-Path $day 'rollout-a.jsonl'), ('{ "token_count" "rate_limits" обірвано' + "`n$line`n"), $utf)
    $snap = @(Read-CodexRateLimits ([datetime]::UtcNow.AddHours(-1)))
    Check 'вимір Codex: журнал із пробілами в JSON читається (id codex, два вікна, 88 і 51 %)' ($snap.Count -eq 1 -and $snap[0].Id -ceq 'codex' -and @($snap[0].Windows).Count -eq 2 -and $snap[0].Windows[0].left -eq 88 -and $snap[0].Windows[1].left -eq 51 -and $snap[0].Windows[1].m -eq 10080)

    # Замок зайнятий: зміна не чекає довше за -CodexStallMinutes, файл лишається цілим; після звільнення обидва шляхи доходять.
    [IO.File]::WriteAllText($qf, '{"refused":"2026-11-13T09:00:00Z","reset":""}', $utf)
    $held = Open-Lock (Join-Path $RunsDir 'quota-codex.lock')
    $keepStall = $CodexStallMinutes; $CodexStallMinutes = 0
    $threw = $false; try { Update-CodexQuota { param($q) $q.refused = 'ПОРУШЕНО' } } catch { $threw = $_.Exception.Message -match 'зайнятий' }
    $CodexStallMinutes = $keepStall
    Check 'замок quota-codex.lock зайнятий: зміна відмовляється після -CodexStallMinutes, файл цілий' ($threw -and [IO.File]::ReadAllText($qf, $utf) -ceq '{"refused":"2026-11-13T09:00:00Z","reset":""}')
    $held.Dispose()
    Save-CodexRateLimits ([datetime]::UtcNow.AddHours(-1))
    Update-CodexQuota { param($q) $q.refused = '2026-11-13T09:30:00Z'; $q.reset = '' }
    $now = Read-CodexQuota
    Check 'після звільнення замка вимір і відмова в одному файлі: refused лишився, limits і read з''явились' ($now.refused -ceq '2026-11-13T09:30:00Z' -and $now.read -match '^20' -and @($now.limits).Count -eq 1)
    # Старіший знімок паралельного слота не затирає новішого виміру.
    $newer = $now.read
    $old = Get-Content -LiteralPath (Join-Path $day 'rollout-a.jsonl') -Raw
    [IO.File]::WriteAllText((Join-Path $day 'rollout-a.jsonl'), ($old -replace '"timestamp": "[^"]*"', ('"timestamp": "' + [datetime]::UtcNow.AddMinutes(-90).ToString("yyyy-MM-dd'T'HH:mm:ss.fff'Z'") + '"')), $utf)
    Save-CodexRateLimits ([datetime]::UtcNow.AddHours(-1))
    Check 'старіший вимір не затирає новішого в quota-codex.json' ((Read-CodexQuota).read -ceq $newer)
} catch { "✗ збій сценарію: $($_.Exception.Message) $($_.ScriptStackTrace)"; $bad++ }
"ПІДСУМОК: ✗ $bad"
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit ([int]($bad -gt 0))
