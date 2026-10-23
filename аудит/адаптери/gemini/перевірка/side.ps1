# Стенд: підвантажує обгортку крапкою, підміняє перевірки Windows (ізоляція, користувач) і запускає Main.
param([string]$Script, [string]$ArgsJson)
$p = @{}
(ConvertFrom-Json $ArgsJson).PSObject.Properties | ForEach-Object { $p[$_.Name] = $_.Value }
. $Script @p
function Test-Isolation { [string]$env:FAKE_ISOLATION }
function Test-OwnerUser { $true }
exit (Main)
