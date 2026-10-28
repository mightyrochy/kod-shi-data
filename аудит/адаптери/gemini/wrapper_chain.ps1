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

function Save-DraftRequest([string]$Branch, [string]$Head) {
    <# Лише підтверджена публікація DONE лишає завдання створити PR; збій API не губить його. #>
    if ($DryRun -or $Branch -cnotmatch '^gemini/[\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79}$' -or $Head -cnotmatch $script:ShaPattern) { return }
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
    <# Інший постачальник; для невідомого каскаду Gemini — два рушії, один гарантовано незалежний. #>
    $branch = [string]$Pull.head.ref
    if ($branch.StartsWith('claude/')) { return @([string]$Config.codex) }
    if ($branch.StartsWith('codex/')) { return @([string]$Config.claude) }
    # Gemini може каскадувати між GPT і Claude через agy; назва гілки цього не доводить.
    @([string]$Config.codex, [string]$Config.claude)
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
    <# Чернетка -> незалежна перевірка; зміни продукту в main -> один GPU-прогін, щойно моделі доступні. #>
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
        $last = $main; $pending = ''; $seen = @{}
        if (Test-Path -LiteralPath $statePath) {
            $state = ConvertFrom-Json ([IO.File]::ReadAllText($statePath, $script:Utf8))
            $last = [string]$state.main; $pending = [string]$state.pending
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
        if ($last -cne $main) {
            $paths = Get-Paths @('diff','--name-only','-z',$last,$main)
            if (@($paths | Where-Object { $_ -match '^(джерела/|каталог/|index\.html$|build\.txt$)' }).Count) { $pending = $main }
        }
        # Спершу зберігаємо виявлене злиття: збій API PR не губить наступний живий прогін.
        Write-FileAtomic $statePath (([ordered]@{ main=$main; pending=$pending; reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
        if ($pending) {
            if ($pending -cnotmatch $script:ShaPattern) { throw 'CHAIN_STATE' }
            if (Test-LiveModels $config) {
                Add-ChainMarker "автоживий-$pending" ([string]$config.codex) $main -Gpu
                $pending = ''
            } else { Write-WrapperLog "ланцюг: живий $pending чекає доступу до моделей; пульсу диспетчера не потребує" }
            Write-FileAtomic $statePath (([ordered]@{ main=$main; pending=$pending; reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
        }
        Complete-EngineDrafts
        foreach ($pr in @(Get-ChainPulls)) {
            if ($pr.user.login -cne 'mightyrochy' -or $null -eq $pr.head.repo -or $pr.head.repo.full_name -cne $GitHubRepo -or $pr.base.repo.full_name -cne $GitHubRepo -or $pr.base.ref -cne 'main') { continue }
            $branch = [string]$pr.head.ref; $head = [string]$pr.head.sha
            if ($branch -cnotmatch '^(gemini|claude|codex)/([\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79})$' -or $head -cnotmatch $script:ShaPattern) { continue }
            if ($branch -match '/авто(перевірка|живий)-' -or $branch.Contains('..') -or $branch.EndsWith('.lock')) { continue }
            $n = [string]$pr.number
            if ($n -cnotmatch '^[1-9][0-9]{0,8}$') { continue }
            $eligible = Test-RecentReviewHead $pr $heads $installed $now $hours
            Write-FileAtomic $statePath (([ordered]@{ main=$main; pending=$pending; reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
            if (-not $eligible) { continue }
            foreach ($model in @(Get-ReviewModels $pr $config)) {
                $key = "$n $head $model"
                if ($seen.ContainsKey($key)) { continue }
                Add-ChainMarker "автоперевірка-$n-$head" $model $main
                $seen[$key] = $true
                Write-FileAtomic $statePath (([ordered]@{ main=$main; pending=$pending; reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
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
