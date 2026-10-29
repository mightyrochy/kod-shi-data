# Стенд спостерігача: локальний origin і fake_gh, користувач ОС підмінено як у side.ps1 та side_claude.ps1.
param([string]$Script, [string]$ArgsJson, [int]$MaxRows = 20, [int]$MaxDiffKB = 128)
# UTF-8 із BOM у стандартному stdin .NET Framework, як у раннера Windows.
if ($env:OS -eq 'Windows_NT') { [Console]::InputEncoding = [Text.Encoding]::UTF8 }
$p = @{}
(ConvertFrom-Json $ArgsJson).PSObject.Properties | ForEach-Object { $p[$_.Name] = $_.Value }
$script:HarnessPython = $p['HarnessPython']
$script:HarnessGh = $p['HarnessGh']
$script:HarnessGhExe = $p['GhExe']
$p.Remove('HarnessPython')
$p.Remove('HarnessGh')
$p['MaxRows'] = $MaxRows
$p['MaxDiffKB'] = $MaxDiffKB
# Файл, що не завантажився, — провал стенда з причиною: без Main PowerShell знайшов би main.cpl (PATHEXT має .CPL)
# і відкрив "Миша – властивості" поверх вікон власника (29.10, 20 разів за 2 хв).
try { . $Script @p } catch { [Console]::Error.WriteLine("СТЕНД: $Script не завантажився: $($_.Exception.Message)"); exit 2 }
if (-not (Get-Command Main -CommandType Function -ErrorAction SilentlyContinue)) { [Console]::Error.WriteLine("СТЕНД: $Script не визначив Main"); exit 2 }
function Test-OwnerUser { $true }
# Справжній gh.exe — нативний процес. .cmd-заглушка розбиває URL із & ще до Python;
# зберігаємо справжній Invoke-Native й лише додаємо інтерпретатор для цієї заглушки.
$script:HarnessNative = ${function:Invoke-Native}
function Invoke-Native([string]$Exe, [string[]]$Arguments, [string]$WorkDirectory = '', [double]$TimeoutMinutes = 5, [string]$StdIn = $null) {
    if ($Exe -eq $script:HarnessGhExe) {
        $Exe = $script:HarnessPython
        $Arguments = @($script:HarnessGh) + $Arguments
    }
    & $script:HarnessNative $Exe $Arguments $WorkDirectory $TimeoutMinutes $StdIn
}
exit (Main)
