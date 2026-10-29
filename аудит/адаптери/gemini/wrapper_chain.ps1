#Requires -Version 5.1
function Invoke-ChainApi([string]$Path) {
    <# Читає JSON GitHub; збій не стає порожнім успішним списком. #>
    $r = Invoke-Native (Resolve-Exe $GhExe) @('api', $Path) $WorkDir 2
    if ($r.Code -ne 0) { throw 'CHAIN_API' }
    $data = ConvertFrom-Json $r.Out
    $data
}

function Get-ChainPulls {
    <# Усі відкриті PR, включно з чернетками: рівно 100 на сторінку, до порожньої сторінки. #>
    for ($page = 1; $page -le 100; $page++) {
        $items = @(Invoke-ChainApi "repos/$GitHubRepo/pulls?state=open&per_page=100&page=$page")
        foreach ($item in $items) { $item }
        if ($items.Count -lt 100) { return }
    }
    throw 'CHAIN_PAGES'
}

function Test-ChainCodePull($Pull) {
    <# Повний список файлів API відрізняє документацію від коду; неповна відповідь лишає повтор. #>
    $code = $false; $count = 0
    for ($page = 1; $page -le 100; $page++) {
        $items = @(Invoke-ChainApi "repos/$GitHubRepo/pulls/$($Pull.number)/files?per_page=100&page=$page")
        foreach ($item in $items) {
            if ($item.filename -isnot [string] -or -not $item.filename) { throw 'CHAIN_FILES' }
            $paths = @([string]$item.filename)
            if ($null -ne $item.PSObject.Properties['status'] -and $item.status -ceq 'renamed') {
                if ($item.previous_filename -isnot [string] -or -not $item.previous_filename) { throw 'CHAIN_FILES' }
                $paths += [string]$item.previous_filename
            }
            foreach ($path in $paths) {
                if ($path -cnotmatch '^аудит/' -or $path -cmatch '^аудит/(адаптери|проби)/') { $code = $true }
            }
            $count++
        }
        if ($items.Count -lt 100) {
            if (-not $count) { throw 'CHAIN_FILES' }
            return $code
        }
    }
    throw 'CHAIN_PAGES'
}

function Get-ChainBuildStamp([string]$Commit) {
    <# Читає штамп з точного коміту; відсутня збірка чекає, пошкоджена не стає успіхом. #>
    $exists = Invoke-Git @('ls-tree','--name-only',$Commit,'--','build.txt')
    if (-not $exists.Out.Trim()) { return '' }
    $stamp = (Invoke-Git @('cat-file','blob',"${Commit}:build.txt")).Out.Trim()
    if ($stamp -cnotmatch $script:ShaPattern) { throw 'CHAIN_BUILD' }
    $stamp
}

function Save-DraftRequest([string]$Branch, [string]$Head, [string]$Model = '') {
    <# Лише підтверджена публікація DONE лишає завдання створити PR; збій API не губить його. #>
    if ($DryRun -or $Branch -cnotmatch '^gemini/[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}$' -or $Head -cnotmatch $script:ShaPattern) { return }
    if ($Model -cmatch $script:ModelPattern) {
        $models = Join-Path $WorkDir 'engine-models'; [void][IO.Directory]::CreateDirectory($models)
        Write-FileAtomic (Join-Path $models ((Get-Sha256Hex "$Branch $Head") + '.txt')) $Model
    }
    $dir = Join-Path $WorkDir 'drafts'; [void][IO.Directory]::CreateDirectory($dir)
    Write-FileAtomic (Join-Path $dir ((Get-Sha256Hex "$Branch $Head") + '.json')) ((@{branch=$Branch;head=$Head} | ConvertTo-Json -Compress))
}

function Complete-EngineDrafts {
    <# Із перевірених результатів публікатора створює PR-чернетки; повтор звіряє наявний PR. #>
    $pulls = @(Get-ChainPulls)
    foreach ($file in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'drafts') -Filter '*.json' -File -ErrorAction SilentlyContinue)) {
        $job = ConvertFrom-Json ([IO.File]::ReadAllText($file.FullName, $script:Utf8))
        $branch = [string]$job.branch; $head = [string]$job.head
        if ($branch -cnotmatch '^gemini/[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}$' -or $branch.Contains('..') -or $branch.EndsWith('.lock') -or $head -cnotmatch $script:ShaPattern) { throw 'CHAIN_DRAFT' }
        # DONE вже пройшов захист Publish-Bundle; повтор усе одно перевіряє поточний ref GitHub.
        $r = Invoke-Git @('ls-remote','--heads','origin',"refs/heads/$branch") -AllowFail
        if ($r.Code -ne 0) { throw 'CHAIN_REMOTE' }
        if (-not $r.Out.StartsWith($head + "`t")) { continue }
        $existing = @($pulls | Where-Object { $_.user.login -ceq 'mightyrochy' -and $_.head.ref -ceq $branch -and $_.head.repo.full_name -ceq $GitHubRepo })
        if ($existing.Count) { Remove-Item -LiteralPath $file.FullName; continue }
        $message = (Invoke-Git @('show','-s','--format=%B',$head)).Out
        # Спецзгадка не має запускати легасі-рушій із тексту звіту.
        $message = [regex]::Replace($message, '(?i)@' + 'codex\b', 'Codex')
        $body = @{title=('Звіт ' + $branch.Substring(7));head=$branch;base='main';draft=$true;body=$message} | ConvertTo-Json -Compress
        $r = Invoke-Native (Resolve-Exe $GhExe) @('api','--method','POST',"repos/$GitHubRepo/pulls",'--input','-') $WorkDir 2 $body
        if ($r.Code -ne 0) { throw 'CHAIN_DRAFT' }
        $pr = ConvertFrom-Json $r.Out
        if ([string]$pr.number -cnotmatch '^[1-9][0-9]{0,8}$') { throw 'CHAIN_DRAFT' }
        Write-WrapperLog "ланцюг: створено PR-чернетку #$($pr.number) $branch $head"
        Remove-Item -LiteralPath $file.FullName
    }
}

function Test-LiveModels($Config) {
    <# Читає каталог локального сервера без завантаження моделей; обом не треба одночасно стояти у VRAM. #>
    $required = @($Config.models)
    if ($required.Count -ne 2) { return $false }
    foreach ($path in @('/api/v1/models','/api/v0/models','/v1/models')) {
        try {
            $r = Invoke-RestMethod -Uri ("http://127.0.0.1:1234" + $path) -Method Get -TimeoutSec 5
            if ($path -eq '/api/v1/models') { $ids = @($r.models | ForEach-Object { [string]$_.key }) }
            else { $ids = @($r.data | ForEach-Object { [string]$_.id }) }
            foreach ($id in $required) { if ($id -notin $ids) { return $false } }
            return $true
        } catch {
            # Лише відсутній endpoint дозволяє сумісний старий API. 401/403 не обходяться.
            if ($_.Exception -isnot [Net.WebException] -or $null -eq $_.Exception.Response -or [int]$_.Exception.Response.StatusCode -ne 404) { return $false }
        }
    }
    $false
}

function Add-ChainMarker([string]$Slug, [string]$Model, [string]$Main, [switch]$Gpu) {
    <# Створює сталу позначку один раз; порівняння lease не дозволяє затерти чужу/вже взяту спробу. #>
    if ($Slug -cnotmatch $script:SlugPattern -or $Model -cnotmatch $script:ModelPattern -or $Main -cnotmatch $script:ShaPattern) { throw 'CHAIN_FORMAT' }
    $ref = "refs/heads/gemini-queue/$Slug/$Model/1" + $(if ($Gpu) { '/p2-gpu' } else { '/p2' })
    $r = Invoke-Git @('ls-remote','--heads','origin',$ref) -AllowFail
    if ($r.Code -ne 0) { throw 'CHAIN_REMOTE' }
    if ($r.Out.Trim()) { return }
    $r = Invoke-Git @('push','-q','--no-verify',"--force-with-lease=${ref}:",'origin',"${Main}:$ref") -AllowFail
    if ($r.Code -ne 0) { throw 'CHAIN_PUSH' }
    Write-WrapperLog "ланцюг: поставлено $ref на $Main"
}

function Get-ReviewModels($Pull, $Config) {
    <# Один інший постачальник; фактичний каскад прив'язаний до опублікованого SHA. #>
    $branch = [string]$Pull.head.ref; $head = [string]$Pull.head.sha
    if (Test-ReviewBranch $branch) { return @() }
    if ($branch.StartsWith('claude/')) { return @([string]$Config.codex) }
    if ($branch.StartsWith('codex/')) { return @([string]$Config.claude) }
    $file = Join-Path (Join-Path $WorkDir 'engine-models') ((Get-Sha256Hex "$branch $head") + '.txt')
    $model = ''
    foreach ($stateFile in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File -ErrorAction SilentlyContinue)) {
        $state = ConvertFrom-Json ([IO.File]::ReadAllText($stateFile.FullName, $script:Utf8))
        if ([string](Get-Prop $state 'line') -cmatch ('^GEMINI ОБГОРТКА: ГОТОВО ' + [regex]::Escape("$branch $head") + '(?: КВОТА [A-Z0-9_]+ [0-9]+)? МОДЕЛЬ ([a-z0-9.-]+)$')) { $model = $Matches[1]; break }
    }
    if (Test-Path -LiteralPath $file) { $model = [IO.File]::ReadAllText($file, $script:Utf8).Trim() }
    if ($model -cmatch '^gpt-') { return @([string]$Config.claude) }
    @([string]$Config.codex)
}

function Get-ReviewDiff([string]$Head, [string]$Main) {
    <# Хеш повного diff проти merge-base не змінюється від чистого злиття main. #>
    if ((Invoke-Git @('cat-file','-e',"$Head^{commit}") -AllowFail).Code -ne 0) {
        [void](Invoke-Git @('fetch','-q','origin',$Head))
    }
    $base = (Invoke-Git @('merge-base',$Main,$Head)).Out.Trim()
    Get-Sha256Hex (Invoke-Git @('-c','core.quotePath=true','diff','--binary','--full-index','--no-ext-diff','--no-textconv','--no-renames',$base,$Head,'--')).Out
}

function Test-ReviewedMerge($Pull, $Reviewed, [string]$Main) {
    <# Пропускає лише нащадка перевіреної голови з незмінним diff і самими merge у першій лінії. #>
    $n = [string]$Pull.number; $head = [string]$Pull.head.sha
    if (-not $Reviewed.ContainsKey($n)) { return $false }
    $old = $Reviewed[$n]
    $verdict = $false
    foreach ($file in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File -ErrorAction SilentlyContinue)) {
        $state = ConvertFrom-Json ([IO.File]::ReadAllText($file.FullName, $script:Utf8))
        if ([string](Get-Prop $state 'line') -cmatch ('^GEMINI ОБГОРТКА: ГОТОВО (?:gemini|claude|codex)/автоперевірка-' + $n + '-' + [string]$old.head + ' ')) { $verdict = $true; break }
    }
    if (-not $verdict) { return $false }
    if ((Invoke-Git @('merge-base','--is-ancestor',[string]$old.head,$head) -AllowFail).Code -ne 0) { return $false }
    if ((Invoke-Git @('rev-list','--first-parent','--no-merges',"$($old.head)..$head")).Out.Trim()) { return $false }
    (Get-ReviewDiff $head $Main) -ceq [string]$old.diff
}

function Get-LiveCompletion($Active) {
    <# Кінець — прийнятий опублікований звіт, а не взяття позначки чи вихід процесу. #>
    foreach ($file in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File -ErrorAction SilentlyContinue)) {
        $state = ConvertFrom-Json ([IO.File]::ReadAllText($file.FullName, $script:Utf8))
        if ([string](Get-Prop $state 'line') -cmatch ('^GEMINI ОБГОРТКА: (ГОТОВО|ЗАБЛОКОВАНО) (?:gemini|claude)/автоживий-' + [regex]::Escape([string]$Active.stamp) + ' ')) {
            return $file.CreationTimeUtc.ToString('o')
        }
    }
    ''
}

function Get-LatestLivePending($Pending) {
    <# Єдина черга зберігає останню готову збірку; проміжні штампи лише журналює. #>
    $items = @($Pending)
    if (-not $items.Count) { return @() }
    foreach ($job in @($items | Select-Object -SkipLast 1)) { Write-WrapperLog "ланцюг: пропущено проміжний штамп $($job.stamp)" }
    @($items[-1])
}

function Test-RecentReviewHead($Pull, $Heads, [datetimeoffset]$Installed, [datetimeoffset]$Now, [int]$Hours) {
    <# Новий PR після встановлення, спостережена зміна SHA або свіжа голова у першому знімку.

    updated_at PR змінюють і коментарі, тому для початкового вікна читаємо дату committer точного SHA. #>
    $n = [string]$Pull.number; $head = [string]$Pull.head.sha
    $old = $Heads[$n]
    if ($null -ne $old -and $old.sha -ceq $head) { return [bool]$old.eligible }
    $eligible = $null -ne $old
    if (-not $eligible) {
        $created = [datetimeoffset]::Parse([string]$Pull.created_at, [Globalization.CultureInfo]::InvariantCulture)
        $eligible = $created -ge $Installed -and $created -le $Now
        if (-not $eligible) {
            $commit = Invoke-ChainApi "repos/$GitHubRepo/commits/$head"
            if ($commit.sha -cne $head) { throw 'CHAIN_HEAD' }
            $time = [datetimeoffset]::Parse([string]$commit.commit.committer.date, [Globalization.CultureInfo]::InvariantCulture)
            $eligible = $time -ge $Now.AddHours(-$Hours) -and $time -le $Now
        }
    }
    $Heads[$n] = @{sha=$head;eligible=$eligible}
    $eligible
}

function Invoke-WrapperChain {
    <# PR коду -> незалежна перевірка; новий штамп збірки -> один GPU-прогін на коміті збірки. #>
    if ($DryRun) { return }
    $main = Get-RefSha 'refs/remotes/origin/main'
    $r = Invoke-Git @('cat-file','blob',"${main}:аудит/адаптери/gemini/ланцюг.json") -AllowFail
    if ($r.Code -ne 0) { return }
    try {
        $config = ConvertFrom-Json $r.Out
        if ($config.v -ne 1 -or $config.codex -cnotmatch '^gpt-[a-z0-9.-]+$' -or $config.claude -cnotmatch '^cc-claude-[a-z0-9.-]+$') { throw 'CHAIN_CONFIG' }
        foreach ($path in @('аудит/наряди/автоперевірка.md','аудит/наряди/автоживий.md')) {
            if ((Invoke-Git @('cat-file','-e',"${main}:$path") -AllowFail).Code -ne 0) { throw 'CHAIN_TEMPLATE' }
        }
        $hours = 24
        $hoursProp = $config.PSObject.Properties['review_hours']
        if ($null -ne $hoursProp) {
            if ($hoursProp.Value -isnot [int] -and $hoursProp.Value -isnot [long]) { throw 'CHAIN_CONFIG' }
            $hours = [int]$hoursProp.Value
            if ($hours -lt 1 -or $hours -gt 168) { throw 'CHAIN_CONFIG' }
        }
        $now = [datetimeoffset]::UtcNow; $installed = $now; $heads = @{}
        $statePath = Join-Path $WorkDir 'chain.json'
        $reviewed = @{}; $liveActive = $null; $liveSince = ''; $last = $main; $seen = @{}; $liveStamps = @{}; $livePending = @(); $hasLiveState = $false
        if (Test-Path -LiteralPath $statePath) {
            $state = ConvertFrom-Json ([IO.File]::ReadAllText($statePath, $script:Utf8))
            $last = [string]$state.main
            if ($null -ne $state.PSObject.Properties['reviewed']) { foreach ($entry in $state.reviewed.PSObject.Properties) { $reviewed[$entry.Name] = $entry.Value } }
            if ($null -ne $state.PSObject.Properties['live_active']) { $liveActive = $state.live_active }
            if ($null -ne $state.PSObject.Properties['live_since']) { $liveSince = [string]$state.live_since }
            if ($null -ne $state.PSObject.Properties['live_stamps']) {
                $hasLiveState = $true
                foreach ($stamp in @($state.live_stamps)) {
                    if ($stamp -isnot [string] -or $stamp -cnotmatch $script:ShaPattern) { throw 'CHAIN_STATE' }
                    $liveStamps[$stamp] = $true
                }
                $livePending = @($state.live_pending)
                foreach ($job in $livePending) {
                    if ($job.stamp -cnotmatch $script:ShaPattern -or $job.main -cnotmatch $script:ShaPattern -or -not $liveStamps.ContainsKey([string]$job.stamp)) { throw 'CHAIN_STATE' }
                }
            }
            if ($null -ne $state.PSObject.Properties['installed_utc']) {
                $installed = [datetimeoffset]::Parse([string]$state.installed_utc, [Globalization.CultureInfo]::InvariantCulture)
                if ($installed -gt $now) { throw 'CHAIN_STATE' }
            }
            if ($null -ne $state.PSObject.Properties['heads']) {
                foreach ($entry in $state.heads.PSObject.Properties) { $heads[$entry.Name] = $entry.Value }
            }
            foreach ($key in @($state.reviews)) { if ($key -is [string]) { $seen[$key] = $true } }
        }
        if ($last -cnotmatch $script:ShaPattern -or (Invoke-Git @('merge-base','--is-ancestor',$last,$main) -AllowFail).Code -ne 0) { throw 'CHAIN_HISTORY' }
        $build = Get-ChainBuildStamp $last
        # Перший запуск або старий формат стану: поточна збірка — початкова межа, не історичний наряд.
        if (-not $hasLiveState -and $build) { $liveStamps[$build] = $true }
        if ($last -cne $main) {
            $commits = (Invoke-Git @('rev-list','--first-parent','--reverse',"$last..$main")).Out
            foreach ($commit in @($commits -split '\s+' | Where-Object { $_ })) {
                $stamp = Get-ChainBuildStamp $commit
                if ($stamp -and $stamp -cne $build -and -not $liveStamps.ContainsKey($stamp)) {
                    $livePending += @{stamp=$stamp;main=$commit}
                    $liveStamps[$stamp] = $true
                }
                $build = $stamp
            }
        }
        $livePending = @(Get-LatestLivePending $livePending)
        if ($null -ne $liveActive) {
            $completed = Get-LiveCompletion $liveActive
            if ($completed) { $liveSince = $completed; $liveActive = $null }
        }
        # Запис до мережі лишає ту саму роботу для повтору після падіння.
        Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 7)
        if ($null -eq $liveActive -and $livePending.Count -and (Test-LiveModels $config)) {
            $job = $livePending[0]
            $liveActive = [pscustomobject]@{stamp=$job.stamp;main=$job.main;published=$false}; $livePending = @()
            # Резерв до push: падіння після прийнятого ref не перетворює його на пропущений штамп.
            Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 7)
        }
        if ($null -ne $liveActive -and $null -ne $liveActive.PSObject.Properties['published'] -and -not $liveActive.published) {
            Add-ChainMarker "автоживий-$($liveActive.stamp)" ([string]$config.codex) ([string]$liveActive.main) -Gpu
            $liveActive.published = $true
            Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 7)
        }
        Complete-EngineDrafts
        foreach ($pr in @(Get-ChainPulls)) {
            if ($pr.user.login -cne 'mightyrochy' -or $null -eq $pr.head.repo -or $pr.head.repo.full_name -cne $GitHubRepo -or $pr.base.repo.full_name -cne $GitHubRepo -or $pr.base.ref -cne 'main') { continue }
            $branch = [string]$pr.head.ref; $head = [string]$pr.head.sha
            if ($branch -cnotmatch '^(gemini|claude|codex)/([\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79})$' -or $head -cnotmatch $script:ShaPattern) { continue }
            if ((Test-ReviewBranch $branch) -or $branch.Contains('..') -or $branch.EndsWith('.lock')) { continue }
            if (([string]$pr.title).Contains('[НЕ ЗЛИВАТИ]')) { continue }
            $n = [string]$pr.number
            if ($n -cnotmatch '^[1-9][0-9]{0,8}$') { continue }
            $eligible = Test-RecentReviewHead $pr $heads $installed $now $hours
            Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
            if (-not $eligible) { continue }
            if (-not $reviewed.ContainsKey($n)) {
                foreach ($key in @($seen.Keys | Where-Object { $_ -cmatch ('^' + $n + ' [0-9a-f]{40} ') })) {
                    $oldHead = ($key -split ' ')[1]
                    if ((Invoke-Git @('cat-file','-e',"$oldHead^{commit}") -AllowFail).Code -eq 0 -and
                        (Invoke-Git @('merge-base','--is-ancestor',$oldHead,$head) -AllowFail).Code -eq 0) {
                        $reviewed[$n] = @{head=$oldHead;diff=(Get-ReviewDiff $oldHead $main)}
                        if (Test-ReviewedMerge $pr $reviewed $main) { break }
                    }
                }
            }
            if (Test-ReviewedMerge $pr $reviewed $main) { Write-WrapperLog "ланцюг: #$n $head — незмінний diff після злиття main"; continue }
            $models = @(Get-ReviewModels $pr $config)
            if (-not @($models | Where-Object { -not $seen.ContainsKey("$n $head $_") }).Count) { continue }
            if (-not (Test-ChainCodePull $pr)) { continue }
            $diff = Get-ReviewDiff $head $main
            foreach ($model in $models) {
                $key = "$n $head $model"
                if ($seen.ContainsKey($key)) { continue }
                Add-ChainMarker "автоперевірка-$n-$head" $model $main
                $seen[$key] = $true
                $reviewed[$n] = @{head=$head;diff=$diff}
                Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
            }
        }
    } catch {
        $code = [string]$_.Exception.Message
        if ($code -cnotmatch '^CHAIN_[A-Z_]+$') { $code = 'CHAIN_FAILED' }
        Write-WrapperLog "ланцюг: $code; наступний прохід повторить незавершене"
        if (-not (Test-Seen ("chain-failed $code " + [datetime]::UtcNow.ToString('yyyyMMddHH')))) {
            Add-OutboxLine ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + (Get-Sha256Hex "chain $code").Substring(0,12) + '.txt') "GEMINI ОБГОРТКА: ЛАНЦЮГ $code"
        }
    }
}
