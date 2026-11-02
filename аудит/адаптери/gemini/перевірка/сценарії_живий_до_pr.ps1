#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir, [ValidateSet('ДО','ПІСЛЯ')][string]$Phase = 'ПІСЛЯ')
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false)
$utf = New-Object Text.UTF8Encoding($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('live-before-pr-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Друкує вимір і зберігає кожен провал до кінця стенда. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
function Scenario([string]$Name, [scriptblock]$Body) {
    <# Виконує всі незалежні мірила навіть після винятку одного з них. #>
    try { & $Body } catch { Check "$Name — $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
}
function Import-Functions([string]$File, [string[]]$Names) {
    <# Імпортує функції довіреного файла без запуску планувальника чи процесу моделі. #>
    $errors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $SourceDir $File), [ref]$null, [ref]$errors)
    if ($errors.Count) { throw ($errors | Out-String) }
    foreach ($name in $Names) {
        $node = $ast.Find({ param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq $name }, $true)
        if ($null -eq $node) { throw "нема $name" }
        $definition = $node.Extent.Text -replace '^function\s+', 'function script:'
        . ([scriptblock]::Create($definition))
    }
}
try {
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/box"
    foreach ($dir in @($WorkDir,"$WorkDir/drafts","$WorkDir/seen",$OutDir,$OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $parserNames = @('Get-LiveSceneRegistry','Get-LiveAfterLines')
    if ($Phase -eq 'ПІСЛЯ') { $parserNames += @('ConvertTo-LivePublicationBody','Get-HeadLivePublication','Get-LiveCorrectionPrompt') }
    Import-Functions 'queue_lanes.ps1' $parserNames
    $script:RegistryText = [IO.File]::ReadAllText((Join-Path $SourceDir '../../проби/живі_сцени.txt'), $utf)
    $registry = Get-LiveSceneRegistry $script:RegistryText
    $script:Head = 'a' * 40
    $valid = 'ЖИВИЙ ПІСЛЯ: ж3_співбесіда — чи зникла вада → повне → main → без вади'
    # Форми трьох тіл відтворено з фактів наряду; сторонні тексти PR не виконуються.
    $bodies = @{
        2806 = 'ЖИВИЙ ПІСЛЯ: ж3_співбесіда (сцена співбесіди) — питання → повне → main → краще'
        2816 = "ЖИВИЙ ПІСЛЯ: ж3_співбесіда -> чи зникла`nвада → повне →`nmain → краще"
        2802 = 'ЖИВИЙ ПІСЛЯ майбутнього прогону після злиття'
        0 = $valid
    }
    $script:Body = ''; $script:Existing = @(); $script:Calls = @(); $script:ApiFail = $false
    function Get-ChainPulls { $script:Existing }
    function Resolve-Exe([string]$Name) { 'стенд-gh' }
    function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
        <# Підміняє лише джерело байтів git; читач і всі шляхи публікації справжні. #>
        $out = ''
        if ($GitArgs[0] -eq 'ls-remote') { $out = $script:Head + "`trefs/heads/gemini/проба" }
        elseif ($GitArgs -contains '--format=%B') { $out = $script:Body }
        elseif ($GitArgs[-1] -like '*живі_сцени.txt') { $out = $script:RegistryText }
        elseif ($GitArgs[0] -eq 'diff') { $out = 'аудит/дошка/gemini/проба.md' }
        [pscustomobject]@{Code=0;Out=$out;Err=''}
    }
    function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDirectory = '', [double]$TimeoutMinutes = 10, [string]$StdIn = $null) {
        <# Перехоплює фактичні POST/PATCH; стенд не має мережевих дій. #>
        $script:Calls += @([pscustomobject]@{Args=$Arguments;Payload=(ConvertFrom-Json $StdIn)})
        [pscustomobject]@{Code=$(if ($script:ApiFail) { 1 } else { 0 });Out='{"number":91}';Err=''}
    }
    Scenario '1 три факти й правильне тіло' {
        foreach ($number in @(2806,2816,2802,0)) {
            $script:Body = $bodies[$number]; $script:Calls = @()
            Save-DraftRequest 'gemini/проба' $script:Head
            Complete-EngineDrafts
            $sent = $script:Calls[0].Payload.body
            $invalid = @(Get-LiveAfterLines $sent $registry | Where-Object { $_.error }).Count
            if ($Phase -eq 'ДО') {
                Check "ДО #${number}: опубліковано без перевірки, вадних $invalid" ($sent -ceq $script:Body -and ($invalid -gt 0) -eq ($number -ne 0))
            } else {
                Check "ПІСЛЯ #${number}: до POST вадних 0" ($script:Calls.Count -eq 1 -and $invalid -eq 0)
                if ($number) {
                    Check "ПІСЛЯ #${number}: оригінал і причина збережені, кінець ЗАБЛОКОВАНО" ($sent.Contains('оригінал: ЖИВИЙ ПІСЛЯ') -and $sent -match '(?m)^ЗАБЛОКОВАНО: LIVE_AFTER_INVALID — .+')
                } else { Check 'правильне тіло збережено дослівно' ($sent -ceq $valid) }
            }
        }
    }
    if ($Phase -eq 'ПІСЛЯ') {
        Scenario '2 межі перенесення й дані' {
            $wrapped = "ЖИВИЙ ПІСЛЯ: ж3_співбесіда`n— чи зникла вада → повне →`nmain → без вади"
            $publication = ConvertTo-LivePublicationBody $wrapped $registry
            Check 'звичайні перенесення склеєно перед розбором' ($publication.Bad.Count -eq 0 -and $publication.Body -ceq $valid)
            foreach ($boundary in @('', '- новий пункт', '1. новий пункт', '## Розділ', '> цитата', 'Перевірено: факт', '~~~text', 'ЖИВИЙ ПІСЛЯ: ж3_співбесіда — інше')) {
                $parsed = @(Get-LiveAfterLines ("ЖИВИЙ ПІСЛЯ: ж3_співбесіда`n$boundary`n— питання") $registry)
                Check "межа «$boundary» не дописує неповний рядок" ($parsed.Count -ge 1 -and [bool]$parsed[0].error -and $parsed[0].last -eq 0)
            }
            $mixed = "Передмова`r`n`r`n$($bodies[2806])`r`n`r`n$valid`r`n`r`nКінець"
            $converted = ConvertTo-LivePublicationBody $mixed $registry
            Check 'змішане тіло: правильний рядок і сусідні абзаци збережені' ($converted.Bad.Count -eq 1 -and $converted.Body.Contains($valid) -and $converted.Body.StartsWith('Передмова') -and $converted.Body.Contains('Кінець'))
            Check 'повтор підготовки тіла не додає другого блокера' ((ConvertTo-LivePublicationBody $converted.Body $registry).Body -ceq $converted.Body)
            $foreign = 'ЖИВИЙ ПІСЛЯ: ж3_співбесіда — $(throw "не виконувати"); `дані`'
            Check 'питання з метасимволами лишається даними' ((ConvertTo-LivePublicationBody $foreign $registry).Body -ceq $foreign)
        }
        Scenario '3 один хід тому самому виконавцю' {
            Import-Functions 'gemini_run.ps1' @('Invoke-Agent','Test-Report')
            $script:MaxNudges = 0; $script:TurnMinutes = 5; $script:TotalMinutes = 10
            function Write-Log([string]$Text) { }
            function Close-StreamRun($Run) { }
            function Get-Facts { [pscustomobject]@{Head=$script:Head;OnBranch=$true;Dirty=0;Ahead=1} }
            function Invoke-Turn($M, $Run, [string]$Text, [datetime]$Deadline) {
                $script:Turns++
                if ($script:Turns -eq 2) {
                    $script:Correction = $Text
                    if ($script:Fix) { $script:Body = $valid }
                }
                [pscustomobject]@{Kind='result';Result=[pscustomobject]@{status='OK';response="НОУТБУК ГОТОВО gemini/проба $script:Head"}}
            }
            $m = [pscustomobject]@{Slug='проба'}
            $sel = [pscustomobject]@{Engine=[pscustomobject]@{Name='codex';Effort='high'};Exe='не запускати'}
            foreach ($fix in @($true,$false)) {
                $script:Body=$bodies[2806]; $script:Fix=$fix; $script:Turns=0; $script:Correction=''
                $res = Invoke-Agent $m $script:Head 'той самий наряд' $tmp $sel
                Check "хід виправлення ($fix): рівно два ходи за MaxNudges=0" ($script:Turns -eq 2 -and $res.Turns -eq 2)
                Check "хід виправлення ($fix): причину й формат передано" ($script:Correction.Contains('не голий') -and $script:Correction.Contains('Формат: ЖИВИЙ ПІСЛЯ: <id> —'))
                Check "хід виправлення ($fix): правильний кінець" ($res.Code -ceq $(if ($fix) {'DONE'} else {'BLOCKED'}))
                if (-not $fix) { Check 'повторна вада названа в кінці виводу' ($res.Tail -match 'ЗАБЛОКОВАНО: LIVE_AFTER_INVALID — .*не голий') }
            }
            $script:Body=$valid; $script:Turns=0
            $res = Invoke-Agent $m $script:Head 'той самий наряд' $tmp $sel
            Check 'правильний звіт не викликає додаткового ходу' ($script:Turns -eq 1 -and $res.Code -ceq 'DONE')
        }
        Scenario '4 оновлення й автоперевірка' {
            foreach ($branch in @('gemini/проба',('gemini/автоперевірка-91-' + $script:Head),'gemini/перевірка-91')) {
                foreach ($existing in @($false,$true)) {
                    $script:Existing = @()
                    if ($existing) { $script:Existing = @([pscustomobject]@{number=91;user=@{login='mightyrochy'};head=@{ref=$branch;repo=@{full_name=$GitHubRepo}};base=@{ref='main';repo=@{full_name=$GitHubRepo}}}) }
                    $script:Body=$bodies[2816]; $script:Calls=@()
                    Save-DraftRequest $branch $script:Head
                    Complete-EngineDrafts
                    $sent = $script:Calls[0]
                    Check "$branch ($existing): спільна перевірка перед POST/PATCH" ($script:Calls.Count -eq 1 -and $sent.Args[2] -ceq $(if ($existing) {'PATCH'} else {'POST'}) -and @(Get-LiveAfterLines $sent.Payload.body $registry | Where-Object { $_.error }).Count -eq 0 -and $sent.Payload.body.Contains('ЗАБЛОКОВАНО:'))
                }
            }
            $script:Existing[0].base.ref = 'інша-база'; $script:Calls=@()
            Save-DraftRequest 'gemini/перевірка-91' $script:Head
            Complete-EngineDrafts
            Check 'PR іншої бази не отримує PATCH' ($script:Calls.Count -eq 1 -and $script:Calls[0].Args[2] -ceq 'POST')
            $script:Existing=@(); $script:ApiFail=$true
            Save-DraftRequest 'gemini/проба' $script:Head
            try { Complete-EngineDrafts; Check 'збій API не приймається' $false } catch { Check 'збій API лишає запит для повтору' (@(Get-ChildItem "$WorkDir/drafts/*.json").Count -eq 1) }
            $script:ApiFail=$false; Complete-EngineDrafts
            Import-Functions 'queue_lanes.ps1' @('Add-AutoTaskContext','ConvertTo-Marker','Get-Lane')
            $script:QueuePrefix = 'refs/remotes/origin/gemini-queue/'
            function Get-AutoReviewInput { '{}' }
            foreach ($slug in @(('автоперевірка-91-' + $script:Head),'перевірка-91')) {
                $marker = ConvertTo-Marker ("$script:QueuePrefix$slug/gpt-6.1-terra-high/1/p1`t$script:Head`t1")
                $text = Add-AutoTaskContext $marker.Slug 'наряд' $marker.Sha $marker.Model
                Check "${slug}: модель позначки є в тексті перед запуском" ($marker.Valid -and $text.Contains('Модель перевірки: `gpt-6.1-terra-high`'))
            }
            $workflow = [IO.File]::ReadAllText((Join-Path $SourceDir '../../../.github/workflows/obhortka.yml'),$utf)
            Check 'стенд підключено в матрицю CI рівно раз' ([regex]::Matches($workflow,"'сценарії_живий_до_pr.ps1'").Count -eq 1)
        }
        Scenario '5 ГОТОВО і BLOCKED_PUBLISHED проходять читач до PR' {
            function Get-RefSha { 'b' * 40 }
            function Publish-Bundle { @('OK',1) }
            function Request-SleepRetry { $false }
            $n=0
            foreach ($code in @('DONE','BLOCKED')) {
                foreach ($invalid in @($true,$false)) {
                    $n++
                    $id = '20261102-120000-' + ('{0:d12}' -f $n)
                    $slug = "тіло-$n"
                    $script:Body = $(if ($invalid) { $bodies[2806] } else { $valid })
                    $status = @{v=1;id=$id;code=$code;slug=$slug;model='gpt-6.1-terra-high';n=1;marker=('b'*40);head=$script:Head;cond='';turns=2;minutes=1;ahead=1;bundle=($id+'.bundle')}
                    Write-FileAtomic (Join-Path $OutDir ($id+'.json')) ($status | ConvertTo-Json -Compress)
                    $result = Get-Line $id
                    $requests = @(Get-ChildItem "$WorkDir/drafts/*.json" | Where-Object { (ConvertFrom-Json ([IO.File]::ReadAllText($_.FullName,$utf))).branch -ceq "gemini/$slug" })
                    Check "$code ($invalid): є запит записати перевірене тіло PR" ($requests.Count -eq 1)
                    $expected = if ($invalid) { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/$slug LIVE_AFTER_INVALID_PUBLISHED" } elseif ($code -eq 'DONE') { "GEMINI ОБГОРТКА: ГОТОВО gemini/$slug $script:Head" } else { "GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/$slug BLOCKED_PUBLISHED" }
                    Check "$code ($invalid): кінець називає ваду й проходить канал доставки" ($result.Outbox -ceq $expected -and -not (Test-OutboxLine $result.Outbox))
                }
            }
        }
    }
} finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    if ((Split-Path -Parent $resolved) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $resolved) -cmatch '^live-before-pr-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
exit [int]($bad -gt 0)
