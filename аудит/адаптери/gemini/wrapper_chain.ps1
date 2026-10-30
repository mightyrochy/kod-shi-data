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

function Read-QuotaJson([string]$Dir, [string]$Name) {
    <# Файли квот пишуть смуги (heartbeat — недовірений): не за форматом або нема — «квоту не прочитано». #>
    try { ConvertFrom-Json ([IO.File]::ReadAllText((Join-Path $Dir $Name), $script:Utf8)) } catch { $null }
}

function ConvertFrom-QuotaStamp($Value) {
    # PowerShell 7 сам перетворює дати з JSON на DateTime, 5.1 лишає рядок.
    if ($Value -is [datetime]) { return [datetimeoffset]::new($Value.ToUniversalTime()) }
    $text = [string]$Value
    if ($text -cnotmatch '^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$') { return $null }
    $t = [datetimeoffset]::MinValue
    if ([datetimeoffset]::TryParseExact($text, "yyyy-MM-dd'T'HH:mm:ss'Z'", [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AssumeUniversal, [ref]$t)) { return $t }
    $null
}

function Test-QuotaRefused($Refused, $Reset, [datetimeoffset]$Now) {
    <# Відмова за квотою діє до скидання; скидання невідоме — годину від відмови (quota_wait_minutes за замовчуванням). #>
    $until = ConvertFrom-QuotaStamp $Reset
    if ($null -ne $until) { return $until -gt $Now }
    $at = ConvertFrom-QuotaStamp $Refused
    ($null -ne $at -and $at -le $Now -and $at -gt $Now.AddMinutes(-60))
}

function Test-ModelQuota([string]$Model, [datetimeoffset]$Now) {
    <# $true — постачальник моделі на квоті за файлами, які смуги вже ведуть: Codex — `codex` у heartbeat.json (gemini_run),
    Claude — quota-claude.json (claude_run, поруч із gemini-publish), agy — pools.json (gemini_run): усі групи саме цієї
    моделі на 0 % (Get-ModelGroups, як QUOTA0_<група> у смузі); групи моделі не розпізнано — доступний, як у смузі;
    pools.json без слів назви (до цієї зміни) — усі групи на 0 %. Не прочитано — доступний, як було до квот. Хмарний
    Claude квоти тут не має: його запускає диспетчер. #>
    $Provider = Get-ModelProvider $Model
    if ($Provider -ceq 'codex') {
        $hb = Read-QuotaJson $OutDir 'heartbeat.json'
        $c = $(if ($null -ne $hb) { Get-Prop $hb 'codex' } else { $null })
        if ($null -eq $c) { return $false }
        return (Test-QuotaRefused (Get-Prop $c 'refused') (Get-Prop $c 'reset') $Now)
    }
    if ($Provider -ceq 'claude') {
        $q = Read-QuotaJson (Join-Path (Split-Path -Parent $WorkDir) 'claude-run') 'quota-claude.json'
        if ($null -eq $q) { return $false }
        if (Test-QuotaRefused (Get-Prop $q 'refused') (Get-Prop $q 'reset') $Now) { return $true }
        foreach ($w in @(Get-Prop $q 'windows')) {
            if ($null -eq $w) { continue }
            $until = ConvertFrom-QuotaStamp (Get-Prop $w 'reset')
            if ([string](Get-Prop $w 'left') -ceq '0' -and $null -ne $until -and $until -gt $Now) { return $true }
        }
    }
    if ($Provider -ceq 'agy') {
        $p = Read-QuotaJson $OutDir 'pools.json'
        $groups = @($(if ($null -ne $p) { Get-Prop $p 'groups' }) | Where-Object { $null -ne $_ })
        $named = @(foreach ($g in $groups) {
            $n = [string](Get-Prop $g 'n')
            if ($n -cmatch '^[a-z0-9 ]{1,64}$') { [pscustomobject]@{ Name = $n; Left = [string](Get-Prop $g 'left') } }
        })
        if ($named.Count) { $groups = @(Get-ModelGroups $Model $named) }
        if ($groups.Count -and -not @($groups | Where-Object { [string](Get-Prop $_ 'left') -cne '0' }).Count) { return $true }
    }
    $false
}

# Рецензент без позначки: рядок диспетчерові, який запускає хмарну сесію Claude (Claude на ноутбуці не перевіряє).
$script:CloudReview = 'claude-cloud'


function Get-ModelProvider([string]$Model) {
    if ($Model -ceq $script:CloudReview) { return 'cloud' }
    if ($Model -cmatch '^gpt-') { return 'codex' }
    if ($Model -cmatch '^(?:cc-)?claude-') { return 'claude' }
    'agy'
}

function Get-ModelBase([string]$Model) { ($Model -creplace '^cc-','') -creplace '-(?:low|medium|high|xhigh|max)$','' }

function Select-ReviewModel([string[]]$Candidates, [datetimeoffset]$Now) {
    <# Перший кандидат, чий постачальник не на квоті (порядок — аудит/МОДЕЛІ.md). Усі на квоті — перший: позначка чекає скидання. #>
    $list = @($Candidates | Where-Object { $_ })
    foreach ($model in $list) { if (-not (Test-ModelQuota $model $Now)) { return $model } }
    $list[0]
}

function Get-ReviewModels($Pull, $Config, [datetimeoffset]$Now = [datetimeoffset]::UtcNow) {
    <# Один рецензент іншого постачальника, ніж автор, що не на квоті: робота GPT і Claude — agy, Gemini — Codex; запасний —
    Codex для Claude, хмарний Claude для GPT і Gemini (рядок диспетчерові, не claude -p на ноутбуці). Обидва для роботи
    Claude на квоті — перший: позначка чекає скидання. Фактичний автор прив'язаний до опублікованого SHA. #>
    $branch = [string]$Pull.head.ref; $head = [string]$Pull.head.sha
    if (Test-ReviewBranch $branch) { return @() }
    $file = Join-Path (Join-Path $WorkDir 'engine-models') ((Get-Sha256Hex "$branch $head") + '.txt')
    $model = ''
    foreach ($stateFile in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File -ErrorAction SilentlyContinue)) {
        $state = ConvertFrom-Json ([IO.File]::ReadAllText($stateFile.FullName, $script:Utf8))
        if ([string](Get-Prop $state 'line') -cmatch ('^GEMINI ОБГОРТКА: ГОТОВО ' + [regex]::Escape("$branch $head") + '(?: КВОТА [A-Z0-9_]+ [0-9]+)? МОДЕЛЬ ([a-z0-9.-]+)$')) { $model = $Matches[1]; break }
    }
    if (Test-Path -LiteralPath $file) { $model = [IO.File]::ReadAllText($file, $script:Utf8).Trim() }
    $author = $(if ($branch.StartsWith('claude/')) { 'claude' } elseif ($branch.StartsWith('codex/')) { 'codex' } else { Get-ModelProvider $model })
    $pick = $(if ($author -ceq 'claude') { Select-ReviewModel @([string]$Config.agy, [string]$Config.codex) $Now }
              elseif ($author -ceq 'codex') { Select-ReviewModel @([string]$Config.agy, $script:CloudReview) $Now }
              else { Select-ReviewModel @([string]$Config.codex, $script:CloudReview) $Now })
    @($pick)
}

function Test-ChainReviewDone([string]$Number, [string]$Head) {
    <# Опублікований звіт автоперевірки цієї голови — кінець; позначку іншого рушія вже не ставимо. #>
    foreach ($file in @(Get-ChildItem -LiteralPath (Join-Path $WorkDir 'state') -Filter '*.json' -File -ErrorAction SilentlyContinue)) {
        $state = ConvertFrom-Json ([IO.File]::ReadAllText($file.FullName, $script:Utf8))
        if ([string](Get-Prop $state 'line') -cmatch ('^GEMINI ОБГОРТКА: ГОТОВО (?:gemini|claude|codex)/автоперевірка-' + $Number + '-' + $Head + ' ')) { return $true }
    }
    $false
}

function Move-BlockedMarkers([string]$Slug, [string]$Model, [string]$Main, [datetimeoffset]$Now, [switch]$Gpu) {
    <# Усі позначки наряду чекають вичерпаної квоти, а $Model — на доступного постачальника: ставить позначку $Model, старі
    знімає (без дубля). Є позначка доступного постачальника чи нема старих — нічого не робить. $true — переведено. #>
    if (Test-ModelQuota $Model $Now) { return $false }
    $r = Invoke-Git @('ls-remote','--heads','origin',"refs/heads/gemini-queue/$Slug/*") -AllowFail
    if ($r.Code -ne 0) { throw 'CHAIN_REMOTE' }
    $old = @(foreach ($line in ($r.Out -split "`n")) {
        if ($line -cmatch ('\trefs/heads/(gemini-queue/' + [regex]::Escape($Slug) + '/([a-z0-9][a-z0-9.-]{1,63})/1(?:/p2(?:-gpu)?)?)$')) { [pscustomobject]@{ Ref = $Matches[1]; Model = $Matches[2] } }
    })
    if (-not $old.Count -or @($old | Where-Object { $_.Model -ceq $Model -or -not (Test-ModelQuota $_.Model $Now) }).Count) { return $false }
    if ($Gpu) { Add-ChainMarker $Slug $Model $Main -Gpu } else { Add-ChainMarker $Slug $Model $Main }
    foreach ($m in $old) {
        $d = Invoke-Git @('push','-q','--no-verify','origin',":refs/heads/$($m.Ref)") -AllowFail
        if ($d.Code -ne 0) { throw 'CHAIN_PUSH' }
        Write-WrapperLog "ланцюг: $($m.Ref) знято — квота постачальника вичерпана, роботу бере $Model"
    }
    $true
}

function Test-CloudMove([string]$Slug, [datetimeoffset]$Now) {
    <# Хмарний Claude бере голову, коли всі її позначки чекають вичерпаної квоти (без позначок — нічого не переводимо). #>
    $r = Invoke-Git @('ls-remote','--heads','origin',"refs/heads/gemini-queue/$Slug/*") -AllowFail
    if ($r.Code -ne 0) { throw 'CHAIN_REMOTE' }
    $models = @(foreach ($line in ($r.Out -split "`n")) { if ($line -cmatch ('\trefs/heads/gemini-queue/' + [regex]::Escape($Slug) + '/([a-z0-9][a-z0-9.-]{1,63})/')) { $Matches[1] } })
    $models.Count -and -not @($models | Where-Object { -not (Test-ModelQuota $_ $Now) }).Count
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
    # Голову, віддану хмарному Claude, перевіряє диспетчер: чисте злиття main нового рядка не породжує.
    if (-not $verdict -and (Test-Path -LiteralPath (Get-SeenPath "cloud-review $n $($old.head)"))) { $verdict = $true }
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

function Test-ChainReviewPull($Pull) {
    <# PR, чию голову перевіряє ланцюг: власника, у main цього репозиторію, з гілки рушія (не звіт перевірки), без «[НЕ ЗЛИВАТИ]». #>
    if ($Pull.user.login -cne 'mightyrochy' -or $null -eq $Pull.head.repo -or $Pull.head.repo.full_name -cne $GitHubRepo -or $Pull.base.repo.full_name -cne $GitHubRepo -or $Pull.base.ref -cne 'main') { return $false }
    $branch = [string]$Pull.head.ref
    if ($branch -cnotmatch '^(gemini|claude|codex)/([\p{L}\p{Nd}][\p{L}\p{Nd}._-]{0,79})$' -or [string]$Pull.head.sha -cnotmatch $script:ShaPattern) { return $false }
    if ((Test-ReviewBranch $branch) -or $branch.Contains('..') -or $branch.EndsWith('.lock')) { return $false }
    if (([string]$Pull.title).Contains('[НЕ ЗЛИВАТИ]')) { return $false }
    [string]$Pull.number -cmatch '^[1-9][0-9]{0,8}$'
}

function Remove-DeadReviewMarkers($Pulls, $Seen, [datetimeoffset]$Now) {
    <# Позначки автоперевірки, яких смуги не мають брати, знімаються до узяття: голова — не поточна голова відкритого PR
    (злито, закрито, новий пуш), PR без коду чи вже не перевіряється, позначка Claude на ноутбуці (`cc-`: перевіряє
    хмарний Claude чи інший постачальник — ключ знято з $Seen, тож голова отримає рецензента наново), друга позначка
    тієї самої голови (лишається одна — постачальника не на квоті). Кожна знята — рядок журналу, а кількість за прохід —
    рядок у зведенні обгортки; невдале зняття повторить наступний прохід. #>
    $live = @{}
    foreach ($pr in @($Pulls)) { if (Test-ChainReviewPull $pr) { $live[[string]$pr.number] = $pr } }
    $r = Invoke-Git @('ls-remote','--heads','origin','refs/heads/gemini-queue/автоперевірка-*') -AllowFail
    if ($r.Code -ne 0) { throw 'CHAIN_REMOTE' }
    $refs = @(foreach ($line in ($r.Out -split "`n")) {
        if ($line.Trim() -cmatch '^([0-9a-f]{40})\trefs/heads/(gemini-queue/автоперевірка-([1-9][0-9]{0,8})-([0-9a-f]{40})/([a-z0-9][a-z0-9.-]{1,63})/\S+)$') {
            [pscustomobject]@{ Sha = $Matches[1]; Ref = $Matches[2]; N = $Matches[3]; Head = $Matches[4]; Model = $Matches[5] }
        }
    })
    $drop = @()
    foreach ($g in @($refs | Group-Object -CaseSensitive { "$($_.N) $($_.Head)" })) {
        $first = $g.Group[0]; $pr = $live[$first.N]; $why = ''
        if ($null -eq $pr) { $why = 'PR не відкритий чи не перевіряється' }
        elseif ([string]$pr.head.sha -cne $first.Head) { $why = 'голова PR змінилась' }
        elseif (-not @($Seen.Keys | Where-Object { $_ -cmatch ('^' + $first.N + ' ' + $first.Head + ' ') }).Count -and -not (Test-ChainCodePull $pr)) { $why = 'PR без коду' }
        $keep = ''
        if (-not $why) {
            $sorted = @($g.Group | Where-Object { $_.Model -cnotmatch '^cc-' } | Sort-Object Ref)
            $free = @($sorted | Where-Object { -not (Test-ModelQuota $_.Model $Now) })
            $keep = $(if ($free.Count) { $free[0].Ref } elseif ($sorted.Count) { $sorted[0].Ref } else { '' })
        }
        foreach ($m in $g.Group) {
            if ($m.Ref -ceq $keep) { continue }
            $cc = $m.Model -cmatch '^cc-'
            $drop += [pscustomobject]@{ Ref = $m.Ref; Sha = $m.Sha; Key = "$($m.N) $($m.Head) $($m.Model)"; Cc = (-not $why -and $cc)
                Why = $(if ($why) { $why } elseif ($cc) { 'Claude на ноутбуці не перевіряє' } else { 'друга позначка тієї самої голови' }) }
        }
    }
    $removed = 0
    # Пачками: перший прохід нової версії знімає сотні позначок, а кожен push — окремий вхід на origin.
    for ($i = 0; $i -lt $drop.Count; $i += 40) {
        $batch = @($drop[$i..([Math]::Min($i + 40, $drop.Count) - 1)])
        $a = @('push','-q','--no-verify') + @(foreach ($m in $batch) { "--force-with-lease=refs/heads/$($m.Ref):$($m.Sha)" }) + @('origin') + @(foreach ($m in $batch) { ":refs/heads/$($m.Ref)" })
        $d = Invoke-Git $a -AllowFail
        if ($d.Code -ne 0) { Write-WrapperLog "ланцюг: зняття $($batch.Count) позначок не вдалося — повтор наступним проходом"; continue }
        foreach ($m in $batch) {
            Write-WrapperLog "ланцюг: $($m.Ref) знято — $($m.Why)"
            if ($m.Cc) { $Seen.Remove($m.Key) }
        }
        $removed += $batch.Count
    }
    if ($removed) {
        Add-OutboxLine ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + (Get-Sha256Hex ("removed $removed " + [guid]::NewGuid())).Substring(0,12) + '.txt') "GEMINI ОБГОРТКА: ЗНЯТО ПОЗНАЧОК ПЕРЕВІРКИ $removed"
    }
}

function Request-CloudReview([string]$Number, [string]$Head) {
    <# Перевірку бере хмарний Claude: позначки тієї самої голови, що чекають вичерпаної квоти, знімаються, диспетчер
    отримує рядок «ПОТРІБНА ПЕРЕВІРКА CLAUDE #PR <SHA>» один раз на голову. #>
    $r = Invoke-Git @('ls-remote','--heads','origin',"refs/heads/gemini-queue/автоперевірка-$Number-$Head/*") -AllowFail
    if ($r.Code -ne 0) { throw 'CHAIN_REMOTE' }
    foreach ($line in ($r.Out -split "`n")) {
        if ($line.Trim() -cnotmatch '^([0-9a-f]{40})\trefs/heads/(gemini-queue/\S+)$') { continue }
        $sha = $Matches[1]; $ref = $Matches[2]
        $d = Invoke-Git @('push','-q','--no-verify',"--force-with-lease=refs/heads/${ref}:$sha",'origin',":refs/heads/$ref") -AllowFail
        if ($d.Code -ne 0) { throw 'CHAIN_PUSH' }
        Write-WrapperLog "ланцюг: $ref знято — перевірку бере хмарний Claude"
    }
    # Позначка «відправлено» — після рядка: збій між ними повторить рядок, а не загубить його.
    $sent = Get-SeenPath "cloud-review $Number $Head"
    if (-not (Test-Path -LiteralPath $sent)) {
        Add-OutboxLine ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + (Get-Sha256Hex "cloud-review $Number $Head").Substring(0,12) + '.txt') "GEMINI ОБГОРТКА: ПОТРІБНА ПЕРЕВІРКА CLAUDE #$Number $Head"
        Write-FileAtomic $sent "cloud-review $Number $Head"
    }
    Write-WrapperLog "ланцюг: #$Number $Head — перевірка хмарним Claude, рядок диспетчерові"
}

function Get-ChainBusySlots([string]$Dir, [string]$Pattern) {
    <# Читає JSON лише зайнятих слотів: той самий замок worker визначає активність усіх смуг.

    Heartbeat може не мати lanes або лишитися старим після завершення, тому не визначає активність. #>
    $slots = Join-Path $Dir 'slots'
    if (-not (Test-Path -LiteralPath $slots)) { return }
    foreach ($file in @(Get-ChildItem -LiteralPath $slots -Filter '*.json' -File -ErrorAction Stop)) {
        if ($file.BaseName -cnotmatch $Pattern) { continue }
        $lockPath = [IO.Path]::ChangeExtension($file.FullName, '.lock')
        if (-not (Test-Path -LiteralPath $lockPath)) { continue }
        try { $lock = [IO.File]::Open($lockPath, 'Open', 'ReadWrite', 'None'); $lock.Dispose(); continue }
        catch [IO.IOException] { $null = $_ }
        $slot = ConvertFrom-Json ([IO.File]::ReadAllText($file.FullName, $script:Utf8))
        $slug = [string](Get-Prop $slot 'slug'); $marker = [string](Get-Prop $slot 'marker')
        if ($slug -cnotmatch $script:SlugPattern -or $slug.Contains('..') -or $slug.EndsWith('.lock') -or
            $marker -cnotmatch ('^gemini-queue/' + [regex]::Escape($slug) + '/[a-z0-9][a-z0-9.-]{1,63}/[1-9][0-9]*(?:/[^/]+)?$')) { throw 'CHAIN_LANE_STATE' }
        $slot
    }
}

function Get-ChainBranchWork([string]$Branch) {
    <# Повертає активну позначку гілки з наявного стану смуг, без нового таймера чи реєстру.

    Gemini/Codex пишуть gemini/<slug>; Claude може продовжувати іншу гілку зі state/branch-<hash>.txt.
    Поточний HEAD копії Claude враховує і першу спробу, яка ще не зберегла гілку продовження. #>
    if ($Branch.StartsWith('gemini/')) {
        foreach ($slot in @(Get-ChainBusySlots $GeminiRunsDir '^(codex|agy)-[1-9][0-9]*$')) {
            if ($Branch -ceq "gemini/$($slot.slug)") { return [string]$slot.marker }
        }
    }
    if ($Branch.StartsWith('claude/')) {
        $dir = Join-Path (Split-Path -Parent $WorkDir) 'claude-run'
        foreach ($slot in @(Get-ChainBusySlots $dir '^claude-[1-9][0-9]*$')) {
            $slug = [string]$slot.slug; $marker = [string]$slot.marker
            $branches = @("claude/$slug")
            $saved = Join-Path (Join-Path $dir 'state') ('branch-' + (Get-Sha256Hex $slug) + '.txt')
            if (Test-Path -LiteralPath $saved) { $branches += [IO.File]::ReadAllText($saved, $script:Utf8).Trim() }
            $copy = [string](Get-Prop $slot 'copy')
            if ($copy) {
                $gitDir = Join-Path (Join-Path $copy 'repo') '.git'
                if (Test-Path -LiteralPath $gitDir -PathType Leaf) {
                    $link = [IO.File]::ReadAllText($gitDir, $script:Utf8).Trim()
                    if ($link -cmatch '^gitdir: (.+)$') {
                        $gitDir = $Matches[1]
                        if (-not [IO.Path]::IsPathRooted($gitDir)) { $gitDir = Join-Path (Join-Path $copy 'repo') $gitDir }
                    }
                }
                $headPath = Join-Path $gitDir 'HEAD'
                if (Test-Path -LiteralPath $headPath) {
                    $ref = [IO.File]::ReadAllText($headPath, $script:Utf8).Trim()
                    if ($ref -cmatch '^ref: refs/heads/(claude/[^/]+)$') { $branches += $Matches[1] }
                }
            }
            if ($branches -ccontains $Branch) { return $marker }
        }
    }
    ''
}

function Invoke-WrapperChain {
    <# PR коду -> незалежна перевірка; новий штамп збірки -> один GPU-прогін на коміті збірки. #>
    if ($DryRun) { return }
    $main = Get-RefSha 'refs/remotes/origin/main'
    $r = Invoke-Git @('cat-file','blob',"${main}:аудит/адаптери/gemini/ланцюг.json") -AllowFail
    if ($r.Code -ne 0) { return }
    try {
        $config = ConvertFrom-Json $r.Out
        # codex і agy — рецензенти PR; claude — лише автоживий (GPU ноутбука).
        if ($config.v -ne 1 -or $config.codex -cnotmatch '^gpt-[a-z0-9.-]+$' -or $config.claude -cnotmatch '^cc-claude-[a-z0-9.-]+$' -or
            $config.PSObject.Properties['agy'] -eq $null -or $config.agy -isnot [string] -or $config.agy -cnotmatch '^gemini-[a-z0-9.-]+$') { throw 'CHAIN_CONFIG' }
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
            Add-ChainMarker "автоживий-$($liveActive.stamp)" (Select-ReviewModel @([string]$config.codex, [string]$config.claude) $now) ([string]$liveActive.main) -Gpu
            $liveActive.published = $true
            Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 7)
        }
        elseif ($null -ne $liveActive -and $null -ne $liveActive.PSObject.Properties['published'] -and $liveActive.published) {
            # Позначка, що чекає вичерпаної квоти, переходить до доступного рушія.
            [void](Move-BlockedMarkers "автоживий-$($liveActive.stamp)" (Select-ReviewModel @([string]$config.codex, [string]$config.claude) $now) ([string]$liveActive.main) $now -Gpu)
        }
        Complete-EngineDrafts
        $pulls = @(Get-ChainPulls)
        Remove-DeadReviewMarkers $pulls $seen $now
        foreach ($pr in $pulls) {
            if (-not (Test-ChainReviewPull $pr)) { continue }
            $head = [string]$pr.head.sha; $n = [string]$pr.number
            $eligible = Test-RecentReviewHead $pr $heads $installed $now $hours
            Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
            if (-not $eligible) { continue }
            $work = Get-ChainBranchWork ([string]$pr.head.ref)
            if ($work) { Write-WrapperLog "ланцюг: #$n $head — смуга ще пише ($work), перевірка після кінця"; continue }
            Write-WrapperLog "ланцюг: #$n $head — активної смуги нема, звичайна перевірка голови"
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
            $models = @(Get-ReviewModels $pr $config $now)
            if (-not @($models | Where-Object { -not $seen.ContainsKey("$n $head $_") }).Count) { continue }
            if (-not (Test-ChainCodePull $pr)) { continue }
            # Перевірку, що вже дала звіт, інший рушій не повторює.
            if (Test-ChainReviewDone $n $head) { continue }
            $diff = Get-ReviewDiff $head $main
            foreach ($model in $models) {
                $key = "$n $head $model"
                if ($seen.ContainsKey($key)) { continue }
                # Одна перевірка на голову: позначка будь-якого рушія вже стоїть — нової не ставимо, лише переводимо позначки, що чекають вичерпаної квоти.
                $marked = @($seen.Keys | Where-Object { $_ -cmatch ('^' + $n + ' ' + $head + ' ') }).Count
                if ($model -ceq $script:CloudReview) { if (-not $marked -or (Test-CloudMove "автоперевірка-$n-$head" $now)) { Request-CloudReview $n $head } }
                elseif ($marked) { [void](Move-BlockedMarkers "автоперевірка-$n-$head" $model $main $now) }
                else { Add-ChainMarker "автоперевірка-$n-$head" $model $main }
                $seen[$key] = $true
                $reviewed[$n] = @{head=$head;diff=$diff}
                Write-FileAtomic $statePath (([ordered]@{ main=$main; reviewed=$reviewed; live_active=$liveActive; live_since=$liveSince; live_stamps=@($liveStamps.Keys); live_pending=@($livePending); reviews=@($seen.Keys); installed_utc=$installed.ToString('o'); heads=$heads }) | ConvertTo-Json -Compress -Depth 5)
            }
        }
    } catch {
        $code = [string]$_.Exception.Message
        $detail = ''
        if ($code -cnotmatch '^CHAIN_[A-Z_]+$') {
            # Причина збою: тип винятку й рядок скрипту — у рядку; повний текст і позиція — лише в журналі (він може нести шляхи й дані).
            $kind = [string]$_.Exception.GetType().Name
            $at = $_.InvocationInfo
            $where = $(if ($null -ne $at -and $at.ScriptName) { (Split-Path -Leaf $at.ScriptName) + ':' + $at.ScriptLineNumber } else { '' })
            Write-WrapperLog ("ланцюг: CHAIN_FAILED {0}: {1}`n{2}" -f $_.Exception.GetType().FullName, $_.Exception.Message, $_.ScriptStackTrace)
            $code = 'CHAIN_FAILED'
            if ($kind -cmatch '^[A-Za-z0-9]{1,40}$' -and $where -cmatch '^[a-z_]{1,40}\.ps1:[0-9]{1,5}$') { $detail = " $kind $where" }
        }
        Write-WrapperLog "ланцюг: $code$detail; наступний прохід повторить незавершене"
        if (-not (Test-Seen ("chain-failed $code$detail " + [datetime]::UtcNow.ToString('yyyyMMddHH')))) {
            Add-OutboxLine ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + (Get-Sha256Hex "chain $code$detail").Substring(0,12) + '.txt') "GEMINI ОБГОРТКА: ЛАНЦЮГ $code$detail"
        }
    }
}
