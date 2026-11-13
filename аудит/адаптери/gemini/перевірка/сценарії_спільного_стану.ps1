#Requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$SourceDir)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$utf = [Text.UTF8Encoding]::new($false)
$tmp = Join-Path ([IO.Path]::GetTempPath()) ('shared-state-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($tmp)
$bad = 0
function Check([string]$Name, [bool]$Ok) {
    <# Повертає окремий факт і ненульовий код при кожному провалі. #>
    if ($Ok) { "✓ $Name" } else { "✗ $Name"; $script:bad++ }
}
try {
    . (Join-Path $SourceDir 'gemini_run.ps1') -RunsDir "$tmp/runs" -OutDir "$tmp/out" -LaneDir "$tmp/lanes" -UpdateRoot "$tmp/update"
    $script:StateDir = "$RunsDir/state"; $script:SlotDir = "$RunsDir/slots"
    foreach ($dir in @($script:StateDir,$script:SlotDir,$OutDir,$LaneDir)) { [void][IO.Directory]::CreateDirectory($dir) }
    # Це ACL виміряного записувача: лише SYSTEM, BA та власний SID. Міняємо лише фікстури стенда.
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $privateAcl = [Security.AccessControl.DirectorySecurity]::new()
    $privateAcl.SetSecurityDescriptorSddlForm("O:${sid}D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;$sid)")
    Set-Acl -LiteralPath $script:StateDir -AclObject $privateAcl
    # Наявна тека обміну має INTERACTIVE; фікстура відтворює цей доступ.
    $sharedAcl = Get-Acl -LiteralPath $OutDir
    $sharedAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new([Security.Principal.SecurityIdentifier]::new('S-1-5-4'),'Modify','ContainerInherit,ObjectInherit','None','Allow'))
    Set-Acl -LiteralPath $OutDir -AclObject $sharedAcl
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Principal;
public static class StateReader {
    [StructLayout(LayoutKind.Sequential)] public struct SidAttr { public IntPtr Sid; public uint Attributes; }
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool CreateRestrictedToken(IntPtr token,uint flags,uint nd,IntPtr disable,uint np,IntPtr priv,uint nr,ref SidAttr restrict,out IntPtr result);
    [DllImport("advapi32.dll", SetLastError=true)] static extern bool DuplicateToken(IntPtr token,int level,out IntPtr result);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    public static bool CanRead(string path) {
        var sid = new SecurityIdentifier("S-1-5-4");
        var bytes = new byte[sid.BinaryLength]; sid.GetBinaryForm(bytes,0);
        IntPtr ptr=Marshal.AllocHGlobal(bytes.Length), restricted=IntPtr.Zero, token=IntPtr.Zero;
        try {
            Marshal.Copy(bytes,0,ptr,bytes.Length); var sa=new SidAttr { Sid=ptr, Attributes=0 };
            using (var identity=WindowsIdentity.GetCurrent()) {
                if (!CreateRestrictedToken(identity.Token,0,0,IntPtr.Zero,0,IntPtr.Zero,1,ref sa,out restricted) || !DuplicateToken(restricted,2,out token))
                    throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
            }
            using (WindowsIdentity.Impersonate(token)) {
                try { File.ReadAllText(path); return true; } catch (UnauthorizedAccessException) { return false; }
            }
        } finally { if(token!=IntPtr.Zero) CloseHandle(token); if(restricted!=IntPtr.Zero) CloseHandle(restricted); Marshal.FreeHGlobal(ptr); }
    }
}
'@
    $ref = 'gemini-queue/стан/gpt-6.1-sol-high/1'; $sha = 'a' * 40
    $marker = [pscustomobject]@{Ref="refs/remotes/origin/$ref";Name=$ref;Sha=$sha}
    $sp = Get-StatePath (Get-MarkerKey $marker)
    Write-FileAtomic $sp 'WAIT {"until":9999999999,"group":"TEST"}'
    Write-FileAtomic ($sp + '.sleep.json') '{"id":"попередній"}'
    Write-FileAtomic ($sp + '.stale.part') 'незавершено'
    Check 'ДО: читач INTERACTIVE не читає приватний файл з ACL записувача' (-not [StateReader]::CanRead($sp))
    # Функція з виробничого коду: жодної підміни переходу, читання чи запису.
    if (-not (Get-Command Initialize-SharedMarkerState -ErrorAction SilentlyContinue)) {
        Check 'ПІСЛЯ: спільний стан доступний без дозволу адміністратора' $false
    } else {
        $held = Open-Lock "$script:SlotDir/codex-1.lock"
        try { Check 'старий зайнятий слот відкладає перехід' (-not (Initialize-SharedMarkerState)) }
        finally { $held.Dispose() }
        Check 'частковий перехід не публікує ready' (-not (Test-Path "$OutDir/marker-state/ready"))
        [void](New-Claim $marker '20261105-000000-123456789abc')
        Check 'свіжий claim до запуску процесу відкладає перехід' (-not (Initialize-SharedMarkerState))
        Remove-Claim $sp
        $staleId = '20261105-000000-123456789abc'
        [void][IO.Directory]::CreateDirectory("$RunsDir/$staleId")
        Write-FileAtomic "$RunsDir/$staleId/worker.json" '{"slot":"codex-1"}'
        [void](New-Claim $marker $staleId)
        (Get-Item -LiteralPath (Get-ClaimPath $sp)).LastWriteTime = (Get-Date).AddMinutes(-11)
        $interrupted = Join-Path $script:StateDir (('b' * 64) + '.txt')
        Write-FileAtomic $interrupted 'STARTED {"id":"перерваний","slot":"codex-2"}'
        Write-FileAtomic (Get-ClaimPath $interrupted) '20261105-000000-123456789abc'
        $target = Initialize-SharedMarkerState
        Check 'застарілий claim до STARTED очищено до захоплення власних замків' (-not (Test-Path -LiteralPath (Get-ClaimPath $sp)) -and [bool]$target)
        $dest = Join-Path $target (Split-Path -Leaf $sp)
        Check 'ПІСЛЯ: INTERACTIVE справді читає файл зі спільної теки' ([StateReader]::CanRead($dest))
        Check 'приватна ACL і старий файл не змінені' (-not [StateReader]::CanRead($sp) -and (Test-Path $sp))
        Check 'історія WAIT і бічний файл збережені, part не перенесено' ([IO.File]::ReadAllText($dest) -ceq [IO.File]::ReadAllText($sp) -and (Test-Path ($dest + '.sleep.json')) -and -not (Test-Path ($dest + '.stale.part')))
        Check 'ready теж доступний читачеві' ([StateReader]::CanRead("$target/ready"))
        Check 'перерваний STARTED без живого слота переноситься разом із claim для штатного відновлення' ((Test-Path (Join-Path $target (Split-Path -Leaf $interrupted))) -and (Test-Path (Join-Path $target (Split-Path -Leaf (Get-ClaimPath $interrupted)))))
        $script:StateDir = $target
        Write-FileAtomic $dest 'DONE новий OK'
        Check 'повторний запуск не відновлює застарілу історію' ((Initialize-SharedMarkerState) -ceq $target -and [IO.File]::ReadAllText($dest) -ceq 'DONE новий OK')
        . (Join-Path $SourceDir 'gemini_publish.ps1') -WorkDir "$tmp/pub" -OutDir "$tmp/out" -OutboxDir "$tmp/outbox" -UpdateRoot "$tmp/update"
        foreach ($dir in @($WorkDir,"$WorkDir/seen",$OutboxDir)) { [void][IO.Directory]::CreateDirectory($dir) }
        $state = Get-ChainMarkerState $ref $sha 'gpt-6.1-sol-high'
        Check 'ланцюг читає чинний DONE зі спільної теки' ($state.Kind -ceq 'DONE')
        Remove-Item -LiteralPath "$target/ready"
        Check 'до готовності відсутній файл не стає NEW' ((Get-ChainMarkerState 'gemini-queue/відсутній/gpt-6.1-sol-high/1' $sha 'gpt-6.1-sol-high').Kind -ceq 'UNKNOWN')
        Write-FileAtomic "$target/ready" '1'
        Check 'після готовності відсутня позначка має NEW' ((Get-ChainMarkerState 'gemini-queue/відсутній/gpt-6.1-sol-high/1' $sha 'gpt-6.1-sol-high').Kind -ceq 'NEW')
        $script:MarkerLines = @(); $handles = @()
        try {
            foreach ($n in 1..4) {
                $r = "gemini-queue/стан/gpt-6.1-sol-high/$n"
                $script:MarkerLines += "$sha`trefs/heads/$r"
                $p = Join-Path $target ((Get-Sha256Hex "refs/remotes/origin/$r $sha") + '.txt')
                Write-FileAtomic $p 'DONE'
                $handles += [IO.File]::Open($p, 'Open', 'ReadWrite', 'None')
            }
            function Invoke-Git { [pscustomobject]@{Code=0;Out=($script:MarkerLines -join "`n")} }
            $states = @(Get-ChainMarkers 'стан')
            Check 'N зайнятих файлів: прохід завершено, усі UNKNOWN' ($states.Count -eq 4 -and @($states | Where-Object Kind -cne 'UNKNOWN').Count -eq 0)
            Check 'N зайнятих файлів: один рядок на код і місце за годину' (@(Get-ChildItem -LiteralPath $OutboxDir -File).Count -eq 1)
            $records = @([IO.File]::ReadAllLines("$OutDir/state-failures.jsonl") | ForEach-Object { $_ | ConvertFrom-Json })
            Check 'N зайнятих файлів: усі шляхи й стеки збережені' ($records.Count -eq 4 -and @($records.path | Sort-Object -Unique).Count -eq 4 -and @($records | Where-Object { -not $_.script_stack }).Count -eq 0)
        } finally { foreach ($h in $handles) { $h.Dispose() } }
        function First-FailureSite { throw 'CHAIN_REMOTE' }
        function Second-FailureSite { throw 'CHAIN_REMOTE' }
        foreach ($site in @('First-FailureSite','Second-FailureSite')) {
            try { & $site } catch { Write-ChainFailure $_ }
        }
        Check 'однаковий код у двох місцях має два різні вихідні файли' (@(Get-ChildItem -LiteralPath $OutboxDir -File).Count -eq 3)
        foreach ($site in @('First-FailureSite','Second-FailureSite')) {
            try { & $site } catch { Write-ChainFailure $_ }
        }
        Check 'повтор із кожного місця приглушено в межах години' (@(Get-ChildItem -LiteralPath $OutboxDir -File).Count -eq 3)
    }
} catch { Check "виняток: $($_.Exception.Message) $($_.ScriptStackTrace)" $false }
finally {
    $resolved = [IO.Path]::GetFullPath($tmp)
    if ((Split-Path -Parent $resolved) -ceq [IO.Path]::GetTempPath().TrimEnd('\','/') -and (Split-Path -Leaf $resolved) -cmatch '^shared-state-[0-9a-f]{32}$') { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
"ПІДСУМОК: провалів $bad"
exit ([int]($bad -gt 0))
