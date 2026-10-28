param([Parameter(Mandatory = $true)][string]$WrapperRoot)
$ErrorActionPreference = 'Stop'
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('nightly-' + [guid]::NewGuid().ToString('N'))
. (Join-Path $WrapperRoot 'gemini_run.ps1') -RunsDir $testRoot
$script:TestMain = '1111111111111111111111111111111111111111'
$script:HasTemplate = $true
function Get-RefSha([string]$Ref) { $script:TestMain }
function Invoke-Git([string[]]$GitArgs, [switch]$AllowFail) {
    [pscustomobject]@{ Code = $(if ($script:HasTemplate) { 0 } else { 1 }) }
}
function Assert-That($Condition, [string]$Text) {
    if (-not $Condition) { throw $Text }
    Write-Output ('✔ ' + $Text)
}
$a = @(Get-NightlyMarker ([datetime]'2026-10-27T01:59:00Z'))
Assert-That ($a.Count -eq 0) 'до 02:00 UTC позначки немає'
$a = @(Get-NightlyMarker ([datetime]'2026-10-27T02:00:00Z'))
Assert-That ($a.Count -eq 1 -and $a[0].Valid -and $a[0].Gpu -and $a[0].Prio -eq 8 -and $a[0].Lane -eq 'codex') 'ніч займає звичайну смугу та GPU'
$script:TestMain = '2222222222222222222222222222222222222222'
$b = @(Get-NightlyMarker ([datetime]'2026-10-27T23:59:00Z'))
Assert-That ((Get-MarkerKey $a[0]) -ceq (Get-MarkerKey $b[0])) 'новий main тієї самої доби не створює другий запуск'
$c = @(Get-NightlyMarker ([datetime]'2026-10-28T02:00:00Z'))
Assert-That ($c.Count -eq 1 -and $c[0].Slug -cne $a[0].Slug -and $c[0].Sha -ceq $script:TestMain) 'наступна доба має власну гілку й чинний main'
Assert-That ((Get-TaskSource $c[0]) -ceq 'аудит/проби/нічний_наряд.md') 'нічна гілка читає постійний шаблон'
$ordinary = [pscustomobject]@{ Slug = 'звичайний' }
Assert-That ((Get-TaskSource $ordinary) -ceq ($script:TaskDir + 'звичайний.md')) 'звичайний наряд читає власний файл'
foreach ($slug in @(('автоперевірка-1981-' + ('a' * 40)), ('автоживий-' + ('b' * 40)))) {
    $auto = [pscustomobject]@{ Slug = $slug }
    Assert-That ((Get-TaskSource $auto) -ceq (Get-AutoTaskPath $slug)) 'автонаряд зберігає шлях шаблону Е0'
}
$prompt = Get-Prompt $c[0] 'Роль — ВИКОНАВЕЦЬ' 'codex'
Assert-That ($prompt.Contains('аудит/проби/нічний_наряд.md')) 'адаптер називає справжнє джерело нічного наряду'
$script:HasTemplate = $false
$d = @(Get-NightlyMarker ([datetime]'2026-10-29T02:00:00Z'))
Assert-That ($d.Count -eq 0) 'без шаблону в main запуску немає'
