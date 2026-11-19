#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('state-diagnostic-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Кожний провал визначає ненульовий код стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Records {
    <# Читає журнал заново, тому друга відмова має дати другий запис. #>
    $file = Join-Path $OutDir 'state-failures.jsonl'
    if (Test-Path -LiteralPath $file) {
        foreach ($line in [IO.File]::ReadAllLines($file, $utf)) { ConvertFrom-Json $line }
    }
}
function Check-Record([string]$Name, [string]$Path, [string]$Code, [string]$Type, [string]$Kind) {
    <# Звіряє значення з реальною файловою системою, а не лише наявність назв полів. #>
    $records = @(Records | Where-Object { $_.path -ceq $Path -and $_.code -ceq $Code })
    Check "$Name — запис з точним шляхом" ($records.Count -gt 0)
    if (-not $records.Count) { return }
    $r = $records[-1]; $item = Get-Item -LiteralPath $Path -Force; $acl = Get-Acl -LiteralPath $Path
    Check "$Name — тип, власник, ACL, час запису й UTC" ($r.object_type -ceq $Type -and $r.owner -ceq $acl.Owner -and $r.acl -ceq $acl.Sddl -and $r.last_write_utc -ceq $item.LastWriteTimeUtc.ToString('o') -and $r.utc -cmatch '^20[0-9]{2}-.*Z$')
    Check "$Name — повний виняток і стек" ($r.exception.Contains($Kind) -and $r.script_stack -cmatch 'at (Get-MarkerState|Get-Line),' -and [bool]$r.position)
    Check "$Name — метадані прочитано" (@($r.metadata_errors).Count -eq 0)
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/update"
    $GeminiRunsDir = "$tmp/gemini-runs"
    foreach ($dir in @($WorkDir, $OutDir, $OutboxDir, "$WorkDir/seen", "$OutDir/marker-state", "$tmp/claude-run/state")) { [void][IO.Directory]::CreateDirectory($dir) }
    Write-FileAtomic "$OutDir/marker-state/ready" '1'
    $sha = 'a' * 40
    $script:MarkerLine = ''
    function Invoke-Git { [pscustomobject]@{Code=0;Out=$script:MarkerLine} }
    foreach ($case in @(
        @{name='зайнятий файл Claude';model='cc-claude-sonnet-5-5-medium';dir="$tmp/claude-run/state";directory=$false},
        @{name='зайнятий файл Gemini';model='gpt-6.1-sol-high';dir="$OutDir/marker-state";directory=$false},
        @{name='тека замість файла Claude';model='cc-claude-sonnet-5-5-medium';dir="$tmp/claude-run/state";directory=$true},
        @{name='тека замість файла Gemini';model='gpt-6.1-sol-high';dir="$OutDir/marker-state";directory=$true}
    )) {
        $ref = "gemini-queue/діагностика/$($case.model)/$(if ($case.directory) {2} else {1})"
        $script:MarkerLine = "$sha`trefs/heads/$ref"
        $path = Join-Path $case.dir ((Get-Sha256Hex "refs/remotes/origin/$ref $sha") + '.txt')
        $lock = $null
        if ($case.directory) { [void][IO.Directory]::CreateDirectory($path) }
        else { [IO.File]::WriteAllText($path, 'DONE', $utf); $lock = [IO.File]::Open($path, 'Open', 'ReadWrite', 'None') }
        try {
            $markers = @(Get-ChainMarkers 'діагностика')
            Check "$($case.name) — збирач завершився, стан UNKNOWN" ($markers.Count -eq 1 -and $markers[0].Kind -ceq 'UNKNOWN')
            $kind = $(if ($case.directory) {'UnauthorizedAccessException'} else {'IOException'})
            $type = $(if ($case.directory) {'directory'} else {'file'})
            Check-Record $case.name $path 'CHAIN_FAILED' $type $kind
            $lines = @(Get-ChildItem -LiteralPath $OutboxDir -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() })
            $suffix = ' ШЛЯХ ' + (ConvertTo-Json -InputObject $path -Compress)
            $matching = @($lines | Where-Object { $_ -clike 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED *' })
            Check "$($case.name) — один вихідний рядок на код і місце незалежно від шляху" ($matching.Count -eq 1 -and $matching[0] -notmatch '[\r\n]' -and $matching[0] -notmatch 'at Get-MarkerState' -and $matching[0].Contains(' ШЛЯХ '))
            if ($matching.Count) {
                $out = @(Get-ChildItem -LiteralPath $OutboxDir -File | Where-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() -ceq $matching[0] })[0]
                $accepted = Read-OutboxFile $out.FullName
                Check "$($case.name) — публікатор приймає створений файл вихідних" ($accepted[1] -ceq '')
            }
            $before = @(Records).Count
            [void]@(Get-ChainMarkers 'діагностика')
            Check "$($case.name) — приглушений повтор теж у журналі" (@(Records).Count -eq $before + 1)
        } finally { if ($null -ne $lock) { $lock.Dispose() } }
    }
    $id = '20261105-000000-123456789abc'; $path = Join-Path $OutDir ($id + '.json')
    [IO.File]::WriteAllText($path, '{}', $utf)
    $lock = [IO.File]::Open($path, 'Open', 'ReadWrite', 'None')
    try {
        $line = Get-Line $id
        Check 'STATE_INVALID — наявний рядок збережено' ($line.Outbox -ceq 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/невідомо STATE_INVALID')
        Check-Record 'STATE_INVALID зайнятого файла' $path 'STATE_INVALID' 'file' 'IOException'
        $before = @(Records).Count
        [void](Get-Line $id)
        Check 'STATE_INVALID — другий запис попри добове приглушення' (@(Records).Count -eq $before + 1)
        $before = @(Records).Count
        $raw = Get-Line $id -StatusOnly
        Check 'читання StatusOnly — без рядка й без змін журналу' ($null -eq $raw -and @(Records).Count -eq $before)
    } finally { $lock.Dispose() }
    [IO.File]::WriteAllText($path, '{не JSON', $utf)
    [void](Get-Line $id)
    Check-Record 'STATE_INVALID пошкодженого JSON' $path 'STATE_INVALID' 'file' 'ArgumentException'
    [IO.File]::WriteAllText($path, '{}', $utf)
    [void](Get-Line $id)
    $records = @(Records | Where-Object { $_.path -ceq $path -and $_.code -ceq 'STATE_INVALID' })
    Check 'неправильний формат без винятку — причина й стек у журналі' ($records.Count -gt 0 -and $records[-1].exception.Contains('InvalidDataException') -and $records[-1].reason -ceq 'не за форматом' -and $records[-1].script_stack.Contains('at Get-BadLine,'))
    $valid = 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED IOException Get-MarkerState ШЛЯХ ' + (ConvertTo-Json -InputObject $path -Compress)
    Check 'новий формат — без довільного хвоста чи переносу рядка' ((Test-OutboxLine $valid) -ceq '' -and (Test-OutboxLine ($valid + ' extra')) -cne '' -and (Test-OutboxLine ($valid + "`nкоманда")) -cne '' -and (Test-OutboxLine ($valid -replace '20261105', '\u000a20261105')) -cne '')
    $before = @(Records).Count
    try { throw 'CHAIN_REMOTE' } catch { Write-ChainFailure $_ }
    $records = @(Records)
    Check 'іменований код ланцюга — теж повний виняток у доступному журналі' ($records.Count -eq $before + 1 -and $records[-1].code -ceq 'CHAIN_REMOTE' -and $records[-1].exception.Contains('CHAIN_REMOTE') -and [bool]$records[-1].script_stack)
    $missing = Join-Path $tmp 'missing-state.txt'
    try { [void](Read-ChainStateText $missing) } catch { Write-ChainFailure $_ }
    $records = @(Records | Where-Object { $_.path -ceq $missing })
    Check 'недоступні метадані — явні помилки, початковий виняток збережено' ($records.Count -eq 1 -and $records[0].object_type -ceq 'unavailable' -and @($records[0].metadata_errors).Count -eq 2 -and $records[0].exception.Contains('FileNotFoundException'))
    # Збій зовнішньої команди ланцюга: причина (код виходу й stderr) лишається в журналі, а не губиться на `throw 'CHAIN_…'`.
    function Resolve-Exe([string]$Name) { $Name }
    function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDirectory = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) { $script:Native }
    function Reset-ChainLines { Get-ChildItem -LiteralPath $OutboxDir -File | Remove-Item -Force; Get-ChildItem -LiteralPath "$WorkDir/seen" -File | Remove-Item -Force }
    function Chain-Lines { @(Get-ChildItem -LiteralPath $OutboxDir -File | ForEach-Object { [IO.File]::ReadAllText($_.FullName, $utf).Trim() } | Where-Object { $_ -clike 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API*' }) }
    function Fail-ChainApi($Result) {
        $script:Native = $Result
        try { [void]@(Get-ChainPulls) } catch { Write-ChainFailure $_; return $_ }
    }
    $url = 'https://api.github.com/repos/o/r/pulls?state=open&per_page=100&page=1'
    Reset-ChainLines
    $before = @(Records).Count
    $err = Fail-ChainApi ([pscustomobject]@{Code=1;Out='';Err="gh: HTTP 502: Bad Gateway ($url)`n"})
    $rec = @(Records)[-1]
    Check 'CHAIN_API: Message винятку — точно код' ($err.Exception.Message -ceq 'CHAIN_API' -and $err.Exception.Message -cmatch '^CHAIN_[A-Z_]+$')
    Check 'CHAIN_API: у журналі код виходу й stderr gh' (@(Records).Count -eq $before + 1 -and $rec.code -ceq 'CHAIN_API' -and $rec.exit_code -eq 1 -and $rec.stderr.Contains('HTTP 502: Bad Gateway') -and $rec.stderr.Contains($url))
    $lines = @(Chain-Lines)
    Check 'CHAIN_API: у рядку диспетчерові лише HTTP 502, без stderr і адреси' ($lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API HTTP 502' -and (Test-OutboxLine $lines[0]) -ceq '')
    [void](Fail-ChainApi ([pscustomobject]@{Code=1;Out='';Err="gh: HTTP 503: Service Unavailable ($url)`n"}))
    Check 'CHAIN_API: інший stderr за годину — не новий рядок, але новий запис журналу' (@(Chain-Lines).Count -eq 1 -and @(Records).Count -eq $before + 2 -and @(Records)[-1].stderr.Contains('HTTP 503'))
    Reset-ChainLines
    $err = Fail-ChainApi ([pscustomobject]@{Code=-1;Out='';Err='межа часу'})
    $rec = @(Records)[-1]; $lines = @(Chain-Lines)
    Check 'CHAIN_API: межа часу — журнал і рядок «межа часу»' ($err.Exception.Message -ceq 'CHAIN_API' -and $rec.exit_code -eq -1 -and $rec.stderr -ceq 'межа часу' -and $lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API межа часу' -and (Test-OutboxLine $lines[0]) -ceq '')
    Reset-ChainLines
    [void](Fail-ChainApi ([pscustomobject]@{Code=1;Out='';Err="unknown flag: --foo`n"}))
    $lines = @(Chain-Lines)
    Check 'CHAIN_API: довільний stderr без ознаки — рядок без ознаки, текст лише в журналі' ($lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API' -and @(Records)[-1].stderr.Contains('unknown flag'))
    Reset-ChainLines
    $live = "Get `"https://api.github.com/repos/mightyrochy/kod-shi-data/pulls?state=open&per_page=100&page=1`": net/http: TLS handshake timeout"
    [void](Fail-ChainApi ([pscustomobject]@{Code=1;Out='';Err=$live}))
    $rec = @(Records)[-1]; $lines = @(Chain-Lines)
    Check 'CHAIN_API: живий stderr (TLS handshake timeout) — журнал повний, рядок «мережа» без адреси' ($rec.exit_code -eq 1 -and $rec.stderr -ceq $live -and $lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API мережа' -and (Test-OutboxLine $lines[0]) -ceq '')
    foreach ($go in @('dial tcp 140.82.121.6:443: i/o timeout','read tcp 10.0.0.2:5000->140.82.121.6:443: connection reset by peer','dial tcp 127.0.0.1:443: connect: connection refused','dial tcp: lookup api.github.com: no such host')) {
        Reset-ChainLines
        [void](Fail-ChainApi ([pscustomobject]@{Code=1;Out='';Err="Get `"$url`": $go"}))
        $lines = @(Chain-Lines)
        Check "CHAIN_API: Go-помилка «$go» — «мережа»" ($lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API мережа')
    }
    # Збої git (libcurl): живий stderr CHAIN_REMOTE 19.11 (state-failures.jsonl) і стандартні повідомлення з'єднання й DNS.
    Reset-ChainLines
    $liveGit = "fatal: unable to access 'https://github.com/mightyrochy/kod-shi-data.git/': Failed to connect to github.com:443 after 21084 ms: Could not connect to server`n"
    [void](Fail-ChainApi ([pscustomobject]@{Code=128;Out='';Err=$liveGit}))
    $rec = @(Records)[-1]; $lines = @(Chain-Lines)
    Check 'CHAIN_API: живий stderr git (Failed to connect to … Could not connect to server) — журнал повний, рядок «мережа»' ($rec.exit_code -eq 128 -and $rec.stderr -ceq $liveGit -and $lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API мережа' -and (Test-OutboxLine $lines[0]) -ceq '')
    foreach ($git in @("fatal: unable to access 'https://github.com/mightyrochy/kod-shi-data.git/': Could not resolve host: github.com",'fatal: unable to access ''https://github.com/o/r.git/'': Failed to connect to github.com port 443: Connection timed out','error: RPC failed; curl 56 Recv failure: Connection was reset','error: RPC failed; curl 55 Send failure: Connection was reset','fatal: unable to access ''https://github.com/o/r.git/'': Connection timed out after 300001 milliseconds')) {
        Reset-ChainLines
        [void](Fail-ChainApi ([pscustomobject]@{Code=128;Out='';Err="$git`n"}))
        $lines = @(Chain-Lines)
        Check "CHAIN_API: git/libcurl «$git» — «мережа»" ($lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API мережа')
    }
    foreach ($plain in @("fatal: couldn't find remote ref refs/heads/nope",'fatal: not a git repository (or any of the parent directories): .git',"fatal: unable to access 'https://github.com/o/r.git/': The requested URL returned error: 403")) {
        Reset-ChainLines
        [void](Fail-ChainApi ([pscustomobject]@{Code=128;Out='';Err="$plain`n"}))
        $lines = @(Chain-Lines)
        Check "CHAIN_API: звичайний fatal без мережі «$plain» — не «мережа»" ($lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API' -and @(Records)[-1].stderr.Contains('fatal:'))
    }
    Reset-ChainLines
    [void](Fail-ChainApi ([pscustomobject]@{Code=128;Out='';Err="fatal: unable to access 'https://github.com/o/r.git/': The requested URL returned error: HTTP 502: Could not connect to server"}))
    Check 'CHAIN_API: git — HTTP-код старший за «мережу»' (@(Chain-Lines).Count -eq 1 -and @(Chain-Lines)[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API HTTP 502')
    Reset-ChainLines
    [void](Fail-ChainApi ([pscustomobject]@{Code=1;Out='';Err="gh: HTTP 502: Bad Gateway ($url): i/o timeout"}))
    $lines = @(Chain-Lines)
    Check 'CHAIN_API: HTTP-код старший за «мережу»' ($lines.Count -eq 1 -and $lines[0] -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API HTTP 502')
    Reset-ChainLines
    $secret = New-ChainFailure 'CHAIN_PUSH' ([pscustomobject]@{Code=128;Out='';Err="fatal: unable to access 'https://user:token123@github.com/o/r/': HTTP 502"})
    Check 'stderr у Data — адреса без входу' ($secret.Message -ceq 'CHAIN_PUSH' -and $secret.Data['ExitCode'] -eq 128 -and -not ([string]$secret.Data['Stderr']).Contains('token123') -and ([string]$secret.Data['Stderr']).Contains('https://github.com/o/r/'))
    Reset-ChainLines
    $head = 'b' * 40
    $script:Native = [pscustomobject]@{Code=1;Out='';Err="gh: HTTP 502: Bad Gateway ($url)"}
    try { [void](Invoke-ChainApi 'repos/o/r/pulls/12') } catch { $pullErr = $_ }
    Write-ChainPullFailure $pullErr '12' $head
    $lines = @(Chain-Lines)
    Check 'один PR: рядок з HTTP 502, журнал із stderr, прохід не зупинено' ($lines.Count -eq 1 -and $lines[0] -ceq "GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_API PR 12 $head HTTP 502" -and (Test-OutboxLine $lines[0]) -ceq '' -and @(Records)[-1].stderr.Contains('HTTP 502'))
    $pushErr = New-ChainFailure 'CHAIN_PUSH' ([pscustomobject]@{Code=1;Out='';Err='rejected'})
    $rethrown = $null
    try { throw $pushErr } catch { try { Write-ChainPullFailure $_ '12' $head } catch { $rethrown = $_ } }
    Check 'CHAIN_PUSH і CHAIN_REMOTE — як і раніше, перекидаються на весь прохід з причиною' ($null -ne $rethrown -and $rethrown.Exception.Message -ceq 'CHAIN_PUSH' -and $rethrown.Exception.Data['Stderr'] -ceq 'rejected')
} catch { Check "виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    $parent = [IO.Path]::GetTempPath().TrimEnd('\','/')
    if ((Split-Path -Parent $resolved) -ceq $parent -and (Split-Path -Leaf $resolved) -cmatch '^state-diagnostic-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
exit ([int]($bad -gt 0))
