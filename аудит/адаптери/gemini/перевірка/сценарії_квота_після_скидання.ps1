#Requires -Version 5.1
<# Квота після скидання (gemini-run): знімок /usage, зроблений до часу скидання нульового вікна, після цього часу не діє —
Read-Usage перечитує його, тож нова позначка не чекає зайвих quota_wait_minutes. Справжні Read-Usage, Get-Quota і
Enter-StartQuotaWait; підмінено лише Update-UsageCache (свіжий /usage — текст у $script:Fresh). #>
param([Parameter(Mandatory = $true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('kvota-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$utf = New-Object Text.UTF8Encoding($false)
$bad = 0
function Check([string]$Name, [bool]$Ok) { if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ } }
try {
    . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/update"
    $script:StateDir = "$RunsDir/state"; $script:SlotDir = "$RunsDir/slots"; $script:Limits = $null
    foreach ($dir in @($RunsDir, $script:StateDir, $script:SlotDir, $OutDir, $LaneDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $script:Agy = 'стенд'; $script:Calls = 0; $script:Fresh = ''; $model = 'gemini-3.8-flash-high'
    $now = [DateTimeOffset]::UtcNow
    function UsageDoc([double]$Fraction, [DateTimeOffset]$Reset) {
        $b = @{ window = 'Five Hour Limit'; remaining_fraction = $Fraction; reset_time = $Reset.UtcDateTime.ToString('yyyy-MM-ddTHH:mm:ssZ') }
        @{ command = @{ name = 'usage'; data = @{ groups = @(@{ name = 'Gemini Models'; buckets = @($b) }) } } } | ConvertTo-Json -Compress -Depth 8
    }
    function WriteCache([long]$Time, [string]$Text) {
        [IO.File]::WriteAllText((Join-Path $RunsDir 'usage.json'), ([ordered]@{ time = $Time; text = $Text; models = @() } | ConvertTo-Json -Compress -Depth 3), $utf)
    }
    function Update-UsageCache {
        $script:Calls++
        $t = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        WriteCache $t $script:Fresh
        [pscustomobject]@{ time = $t; text = $script:Fresh; models = @() }
    }
    function Case([long]$Ago, [string]$Cached, [string]$Fresh) {
        $script:Calls = 0; $script:Fresh = $Fresh
        WriteCache ($now.ToUnixTimeSeconds() - $Ago) $Cached
        Get-Quota $model
    }
    function WaitUntil($Q) {
        $m = [pscustomobject]@{ Ref = 'refs/remotes/origin/gemini-queue/квота/x/1'; Name = 'gemini-queue/квота/x/1'; Sha = ('c' * 40); Slug = 'квота'; Model = $model; N = '1'; Cond = '' }
        Enter-StartQuotaWait $m $Q ([pscustomobject]@{ Kind = 'X' })
        ([IO.File]::ReadAllText((Get-StatePath (Get-MarkerKey $m)), $utf).Substring(5) | ConvertFrom-Json).until
    }
    $past = $now.AddSeconds(-60); $future = $now.AddHours(1)
    $zeroPast = UsageDoc 0 $past; $full = UsageDoc 1 $now.AddHours(4)

    # Кеш 2 хв тому (у межах usage_minutes), «0 %», скидання минуло 1 хв тому; свіжий /usage — 100 %.
    $q = Case 120 $zeroPast $full
    Check "знімок до скидання, що минуло: перечитано, група вільна ($($script:Calls) виклик, Blocked=$($q.Blocked))" ($script:Calls -eq 1 -and $q.Known -and -not $q.Blocked)
    # Свіжий теж «0 %» (скидання ще не дійшло в agy): поведінка як досі — чекання quota_wait_minutes.
    $q = Case 120 $zeroPast $zeroPast
    $until = WaitUntil $q
    $want = $now.ToUnixTimeSeconds() + 60 * (Get-Limit $script:Limits 'QuotaWaitMinutes' 'quota_wait_minutes')
    Check "свіжий теж 0 %: Blocked, чекання quota_wait_minutes (різниця $($until - $want) с)" ($script:Calls -eq 1 -and $q.Blocked -and [Math]::Abs($until - $want) -le 30)
    # Скидання ще попереду: кеш діє, agy не питаємо.
    $q = Case 120 (UsageDoc 0 $future) $full
    Check 'скидання попереду: кеш діє без перечитування' ($script:Calls -eq 0 -and $q.Blocked -and $q.ResetAt -gt $now.ToUnixTimeSeconds())
    # Знімок зроблено вже після скидання, група й тоді на нулі: він чинний.
    $q = Case 30 $zeroPast $full
    Check 'знімок після скидання: кеш діє без перечитування' ($script:Calls -eq 0 -and $q.Blocked)
    # Ненульове вікно з минулим скиданням перечитування не викликає.
    $q = Case 120 (UsageDoc 0.5 $past) $full
    Check 'ненульове вікно: кеш діє без перечитування' ($script:Calls -eq 0 -and -not $q.Blocked)
} catch { Check "стенд зірвано: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
exit $(if ($bad) { 1 } else { 0 })
