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
    foreach ($dir in @($WorkDir, $OutDir, $OutboxDir, "$WorkDir/seen", "$GeminiRunsDir/state", "$tmp/claude-run/state")) { [void][IO.Directory]::CreateDirectory($dir) }
    $sha = 'a' * 40
    $script:MarkerLine = ''
    function Invoke-Git { [pscustomobject]@{Code=0;Out=$script:MarkerLine} }
    foreach ($case in @(
        @{name='зайнятий файл Claude';model='cc-claude-sonnet-5-5-medium';dir="$tmp/claude-run/state";directory=$false},
        @{name='зайнятий файл Gemini';model='gpt-6.1-sol-high';dir="$GeminiRunsDir/state";directory=$false},
        @{name='тека замість файла Claude';model='cc-claude-sonnet-5-5-medium';dir="$tmp/claude-run/state";directory=$true},
        @{name='тека замість файла Gemini';model='gpt-6.1-sol-high';dir="$GeminiRunsDir/state";directory=$true}
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
            $matching = @($lines | Where-Object { $_.EndsWith($suffix) })
            Check "$($case.name) — вихідний рядок містить шлях без стеку" ($matching.Count -eq 1 -and $matching[0] -notmatch '[\r\n]' -and $matching[0] -notmatch 'at Get-MarkerState')
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
} catch { Check "виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    $parent = [IO.Path]::GetTempPath().TrimEnd('\','/')
    if ((Split-Path -Parent $resolved) -ceq $parent -and (Split-Path -Leaf $resolved) -cmatch '^state-diagnostic-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
exit ([int]($bad -gt 0))
