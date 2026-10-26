# Стенд: підвантажує обгортку крапкою, підміняє перевірки Windows (ізоляція, користувач) і запускає Main.
param([string]$Script, [string]$ArgsJson)
$p = @{}
(ConvertFrom-Json $ArgsJson).PSObject.Properties | ForEach-Object { $p[$_.Name] = $_.Value }
# Стенд не чіпає справжньої спільної теки ноутбука (C:\Users\Public\gemini\lanes): без LaneDir — тимчасова тека.
if ((Get-Command $Script).Parameters.ContainsKey('LaneDir') -and -not $p.ContainsKey('LaneDir')) {
    $p['LaneDir'] = Join-Path ([System.IO.Path]::GetTempPath()) ('lanes-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
}
. $Script @p
function Test-Isolation { [string]$env:FAKE_ISOLATION }
function Test-OwnerUser { $true }
exit (Main)
