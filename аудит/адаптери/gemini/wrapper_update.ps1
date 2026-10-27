#Requires -Version 5.1
# Самооновлення викликає лише публікатор власника; джерело — його щойно fetched origin/main.
function Test-UpdateRoot([string]$Root) {
    <# Відхиляє посилання та права запису gemini/загальних груп у захищеній теці. #>
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return $false }
    $item = Get-Item -LiteralPath $Root
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
        $item = $item.Parent
    }
    if (-not $script:OnWindows) { return $true }
    $sid = ([Security.Principal.NTAccount]"$env:COMPUTERNAME\$GeminiUser").Translate([Security.Principal.SecurityIdentifier]).Value
    $bad = @($sid, 'S-1-1-0', 'S-1-5-11', 'S-1-5-32-545')
    $ownerSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $writers = @('S-1-5-18','S-1-5-32-544',$ownerSid)
    $write = [Security.AccessControl.FileSystemRights]'WriteData,AppendData,WriteExtendedAttributes,WriteAttributes,Delete,ChangePermissions,TakeOwnership,DeleteSubdirectoriesAndFiles'
    foreach ($rule in (Get-Acl -LiteralPath $Root).Access) {
        $who = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        if (($who -in $bad -or $who -notin $writers) -and $rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $write)) { return $false }
    }
    $true
}

function Write-UpdatePointer([string]$Root, [string]$Sha) {
    <# Міняє єдине посилання атомарно: читач бачить стару або нову повну версію. #>
    $path = Join-Path $Root 'active.txt'; $tmp = Join-Path $Root ('active-' + [guid]::NewGuid().ToString('N') + '.part')
    [IO.File]::WriteAllText($tmp, $Sha, $script:Utf8)
    if (Test-Path -LiteralPath $path) { [IO.File]::Replace($tmp, $path, [NullString]::Value) }
    else { [IO.File]::Move($tmp, $path) }
}

function Invoke-WrapperUpdate([string]$Root) {
    <# Бере архів лише origin/main, перевіряє хеші та окремий процес проби; тоді перемикає версію. #>
    if ($DryRun) { return }
    $sha = Get-RefSha 'refs/remotes/origin/main'
    if ($sha -cnotmatch '^[0-9a-f]{40}$') { throw 'UPDATE_MAIN' }
    $stage = ''; $lock = $null
    try {
        if (-not (Test-OwnerUser) -or -not (Test-UpdateRoot $Root)) { throw 'UPDATE_ACL' }
        try { $lock = [IO.File]::Open((Join-Path $Root 'update.lock'), 'OpenOrCreate', 'ReadWrite', 'None') } catch { return }
        $active = ''; $pointer = Join-Path $Root 'active.txt'
        if (Test-Path -LiteralPath $pointer) { $active = [IO.File]::ReadAllText($pointer).Trim() }
        $prefix = 'аудит/адаптери/gemini'
        $tree = (Invoke-Git @('rev-parse', "${sha}:$prefix")).Out.Trim()
        if ($active -cmatch '^[0-9a-f]{40}$') {
            $prior = Join-Path (Join-Path (Join-Path $Root 'versions') $active) 'source-tree.txt'
            if ((Test-Path -LiteralPath $prior) -and [IO.File]::ReadAllText($prior).Trim() -ceq $tree) { return }
        }
        $stage = Join-Path $Root ('.stage-' + [guid]::NewGuid().ToString('N'))
        [void][IO.Directory]::CreateDirectory($stage)
        $zip = Join-Path $stage 'main.zip'
        [void](Invoke-Git @('-c','core.autocrlf=false','-c','core.eol=lf','archive', '--format=zip', "--output=$zip", $sha, '--', $prefix))
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::ExtractToDirectory($zip, (Join-Path $stage 'archive'))
        $src = Join-Path (Join-Path $stage 'archive') $prefix
        $manifest = Import-PowerShellDataFile (Join-Path $src 'm9v/хеші.psd1')
        $dest = Join-Path $stage 'version'; [void][IO.Directory]::CreateDirectory($dest)
        $files = @($manifest.Keys | Where-Object { $_ -cmatch '^[a-z][a-z0-9_]*\.ps1$' })
        foreach ($needed in @('gemini_run.ps1','gemini_publish.ps1','gemini_watch.ps1','claude_run.ps1','queue_lanes.ps1','wrapper_health.ps1','wrapper_update.ps1','wrapper_chain.ps1','wrapper_probe.ps1')) {
            if ($needed -notin $files) { throw 'UPDATE_MANIFEST' }
        }
        foreach ($name in $files) {
            $file = Join-Path $src $name
            if ($manifest[$name] -cnotmatch '^[0-9A-F]{64}$' -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -cne $manifest[$name]) { Write-WrapperLog "хеш кандидата не збігся: $name"; throw 'UPDATE_HASH' }
            [IO.File]::Copy($file, (Join-Path $dest $name))
        }
        $ps = (Get-Process -Id $PID).Path
        $probe = Invoke-Native $ps @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',(Join-Path $dest 'wrapper_probe.ps1')) $dest 2
        if ($probe.Code -ne 0 -or $probe.Out.Trim() -cne 'WRAPPER_PROBE_OK') { throw 'UPDATE_PROBE' }
        foreach ($name in $files) {
            if ((Get-FileHash -LiteralPath (Join-Path $dest $name) -Algorithm SHA256).Hash -cne $manifest[$name]) { throw 'UPDATE_HASH' }
        }
        [IO.File]::WriteAllText((Join-Path $dest 'source-tree.txt'), $tree, $script:Utf8)
        $versions = Join-Path $Root 'versions'; [void][IO.Directory]::CreateDirectory($versions)
        $final = Join-Path $versions $sha
        # Уже створену версію не переписуємо: її може читати живий наряд.
        if (Test-Path -LiteralPath $final) {
            foreach ($name in $files) {
                if ((Get-FileHash -LiteralPath (Join-Path $final $name) -Algorithm SHA256).Hash -cne $manifest[$name]) { throw 'UPDATE_EXISTS' }
            }
        } else { [IO.Directory]::Move($dest, $final) }
        Write-UpdatePointer $Root $sha
        $stamp = [long](Invoke-Git @('log','--first-parent','-1','--format=%ct',$sha,'--',$prefix)).Out.Trim()
        $seconds = [Math]::Max(0, [DateTimeOffset]::UtcNow.ToUnixTimeSeconds() - $stamp)
        Add-OutboxLine ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + (Get-Sha256Hex "update $sha").Substring(0,12) + '.txt') "GEMINI ОБГОРТКА: ОНОВЛЕНО $sha СЕКУНД $seconds"
        Write-WrapperLog "самооновлення $sha; від коміту origin/main $seconds с; попередня $active"
    } catch {
        $code = [string]$_.Exception.Message
        if ($code -cnotmatch '^UPDATE_[A-Z_]+$') { $code = 'UPDATE_FAILED' }
        Write-WrapperLog "самооновлення $sha — $code; чинну версію збережено; $($_.Exception.Message)"
        if (-not (Test-Seen "update-failed $sha $code")) {
            Add-OutboxLine ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + (Get-Sha256Hex "update-failed $sha $code").Substring(0,12) + '.txt') "GEMINI ОБГОРТКА: ОНОВЛЕННЯ $sha $code"
        }
    } finally {
        if ($null -ne $lock) { $lock.Dispose() }
        # Лише власна випадкова тека під перевіреним коренем; чужих версій не видаляємо.
        if ($stage -and (Test-Path -LiteralPath $stage) -and (Split-Path -Parent $stage) -eq $Root -and (Split-Path -Leaf $stage) -cmatch '^\.stage-[0-9a-f]{32}$') { Remove-Item -LiteralPath $stage -Recurse -Force }
    }
}
