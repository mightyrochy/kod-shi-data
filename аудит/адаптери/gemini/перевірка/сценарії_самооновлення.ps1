#Requires -Version 5.1
param([string]$SourceDir = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$utf = New-Object Text.UTF8Encoding($false)
$tmpRoot = Join-Path ([IO.Path]::GetTempPath()) ('e0-update-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmpRoot)
$failures = 0
function Check([string]$Name, [bool]$Ok) {
    <# Один результат стенда; будь-який провал робить весь запуск червоним. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:failures++ }
}
try {
    $seed = Join-Path $tmpRoot 'seed'; $root = Join-Path $tmpRoot 'protected'
    [void][IO.Directory]::CreateDirectory($root)
    & git init -q -b main $seed
    & git -C $seed config core.autocrlf false
    & git -C $seed config user.name 'стенд'; & git -C $seed config user.email 'stend@example.invalid'
    $prefix = 'аудит/адаптери/gemini'; $src = Join-Path $seed $prefix
    [void][IO.Directory]::CreateDirectory((Join-Path $src 'm9v'))
    Copy-Item -Path (Join-Path $SourceDir '*.ps1') -Destination $src
    function Manifest {
        <# Відбитки точних кандидатів зберігаються в main разом із ними. #>
        $lines = @('@{')
        foreach ($f in @(Get-ChildItem -LiteralPath $src -Filter '*.ps1' -File)) { $lines += "'$($f.Name)' = '$((Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash)'" }
        $lines += '}'; [IO.File]::WriteAllText((Join-Path $src 'm9v/хеші.psd1'), ($lines -join "`n"), $utf)
    }
    function Commit([string]$Message) {
        <# Створює наступний стан локального main і освіжає лише його ref у клона власника. #>
        & git -C $seed add -A; & git -C $seed commit -q -m $Message
        $sha = (& git -C $seed rev-parse HEAD).Trim()
        [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
        $sha
    }
    Manifest
    & git -C $seed add -A; & git -C $seed commit -q -m 'початкова'
    $bare = Join-Path $tmpRoot 'repo.git'
    & git clone -q --bare $seed $bare
    . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmpRoot/pub" -OutboxDir "$tmpRoot/out" -UpdateRoot $root
    foreach ($dir in @($WorkDir, "$WorkDir/seen", $OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    $script:RealRootCheck = (Get-Command Test-UpdateRoot).ScriptBlock
    $script:Repo = $bare; $script:NoHooks = Join-Path $tmpRoot 'no-hooks'
    # Лише ОС/ACL підмінено; git archive, хеші, процес PowerShell, атомарний pointer — справжні.
    function Test-OwnerUser { $true }
    function Test-UpdateRoot([string]$Root) { $true }
    [void](Invoke-Git @('fetch','-q','origin','+refs/heads/main:refs/remotes/origin/main'))
    $first = Get-RefSha 'refs/remotes/origin/main'
    Invoke-WrapperUpdate $root
    Get-Content "$WorkDir/publish.log" -Encoding UTF8
    $pointer = Join-Path $root 'active.txt'
    Check 'перша перевірена версія взята з origin/main' ((Test-Path $pointer) -and [IO.File]::ReadAllText($pointer) -ceq $first)
    Check 'рядок містить SHA і секунди від коміту main' (@(Get-ChildItem "$OutboxDir/*.txt" | Where-Object { (Get-Content $_.FullName -Raw -Encoding UTF8) -match "ОНОВЛЕНО $first СЕКУНД [0-9]+" }).Count -eq 1)
    Invoke-WrapperUpdate $root
    Check 'повтор не створює нової версії' (@(Get-ChildItem "$root/versions" -Directory).Count -eq 1)
    $queue = 'refs/remotes/origin/gemini-queue/ворожа/gpt-6.1-sol-high/1'
    [void](Invoke-Git @('update-ref',$queue,$first))
    [IO.File]::AppendAllText((Join-Path $src 'gemini_watch.ps1'), "`n# нова версія`n", $utf)
    Manifest; $second = Commit 'нова версія'
    Invoke-WrapperUpdate $root
    Get-Content "$WorkDir/publish.log" -Encoding UTF8
    Check 'злиту версію увімкнено без дії власника' ([IO.File]::ReadAllText($pointer) -ceq $second)
    Check 'стару версію збережено для живих процесів' (Test-Path "$root/versions/$first/gemini_run.ps1")
    [IO.File]::AppendAllText((Join-Path $src 'gemini_run.ps1'), "`n# неузгоджені байти`n", $utf)
    $badHash = Commit 'хеш не збігається'
    Invoke-WrapperUpdate $root
    Check 'незбіг хешу зберігає попередню версію' ([IO.File]::ReadAllText($pointer) -ceq $second)
    Check 'відмова хешу дала тривогу' (@(Get-ChildItem "$OutboxDir/*.txt" | Where-Object { (Get-Content $_.FullName -Raw -Encoding UTF8) -match "$badHash UPDATE_HASH" }).Count -eq 1)
    [IO.File]::WriteAllText((Join-Path $src 'wrapper_probe.ps1'), 'exit 7', $utf)
    Manifest; $badProbe = Commit 'проба відмовляє'
    Invoke-WrapperUpdate $root
    Check 'проба з ненульовим кодом не перемикає pointer' ([IO.File]::ReadAllText($pointer) -ceq $second)
    Check 'відмова проби дала тривогу' (@(Get-ChildItem "$OutboxDir/*.txt" | Where-Object { (Get-Content $_.FullName -Raw -Encoding UTF8) -match "$badProbe UPDATE_PROBE" }).Count -eq 1)
    Invoke-WrapperUpdate $root
    Check 'повтор відмови не дублює тривогу' (@(Get-ChildItem "$OutboxDir/*.txt" | Where-Object { (Get-Content $_.FullName -Raw -Encoding UTF8) -match "$badProbe UPDATE_PROBE" }).Count -eq 1)
    # Перевіряємо справжній алгоритм ACL на синтетичних правилах, без Set-Acl чи зміни ОС.
    $script:AclRules = @([pscustomobject]@{IdentityReference=[Security.Principal.SecurityIdentifier]'S-1-1-0';AccessControlType='Allow';FileSystemRights=[Security.AccessControl.FileSystemRights]'ReadAndExecute'})
    function Get-Acl { [pscustomobject]@{Access=$script:AclRules} }
    Check 'RX загальної групи допускається справжньою перевіркою ACL' ([bool](& $script:RealRootCheck $root))
    $script:AclRules[0].FileSystemRights = [Security.AccessControl.FileSystemRights]'WriteData'
    Check 'запис загальної групи відхиляється справжньою перевіркою ACL' (-not [bool](& $script:RealRootCheck $root))
    $script:AclRules[0].IdentityReference = [Security.Principal.SecurityIdentifier]'S-1-5-32-547'
    Check 'невідома привілейована група з записом теж відхиляється' (-not [bool](& $script:RealRootCheck $root))
    function Test-UpdateRoot([string]$Root) { $false }
    Invoke-WrapperUpdate $root
    Check 'небезпечний ACL не змінює версії' ([IO.File]::ReadAllText($pointer) -ceq $second)
    Check 'тимчасові дерева прибрано' (@(Get-ChildItem -LiteralPath $root -Directory -Filter '.stage-*').Count -eq 0)
} catch { "✗ виняток стенда: $($_.Exception.Message) $($_.ScriptStackTrace)"; $failures++ }
finally {
    if ((Split-Path -Parent $tmpRoot) -eq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $tmpRoot) -cmatch '^e0-update-[0-9a-f]{32}$') { Remove-Item -LiteralPath $tmpRoot -Recurse -Force }
}
if ($failures) { exit 1 }
