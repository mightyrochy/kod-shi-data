$ErrorActionPreference = 'Stop'
$utf = [Text.UTF8Encoding]::new($false)
$root = 'C:\Users\gemini\gemini-runs'
$log = 'C:\Users\Public\gemini\out\state-failures.jsonl'
$rows = @([IO.File]::ReadAllLines($log, $utf) | ForEach-Object { $_ | ConvertFrom-Json })
$events = @($rows | Where-Object { $_.utc -ge '2026-11-04' -and $_.utc -lt '2026-11-06' })
$paths = @($events.path | Sort-Object -Unique)
$inventory = @(foreach ($file in Get-ChildItem -LiteralPath "$root\state" -Filter '*.txt' -File) {
    $acl = Get-Acl -LiteralPath $file.FullName
    $text = ''; $errorText = ''
    try { $text = [IO.File]::ReadAllText($file.FullName, $utf) } catch { $errorText = $_.Exception.ToString() }
    $id = ''; $kind = ($text -split ' ', 2)[0]
    if ($text -match '^DONE (\S+)') { $id = $Matches[1] }
    elseif ($text.StartsWith('STARTED ')) { $id = ($text.Substring(8) | ConvertFrom-Json).id }
    [ordered]@{path=$file.FullName; owner=$acl.Owner; acl=$acl.Sddl; last_write_utc=$file.LastWriteTimeUtc.ToString('o');
        kind=$kind; run_id=$id; readable_as_gemini=($errorText -eq ''); error=$errorText; logged=($paths -contains $file.FullName)}
})
$parents = @(foreach ($path in @('C:\Users\gemini', $root, "$root\state", 'C:\Users\Public\gemini\out', 'C:\Users\Public\gemini\lanes')) {
    $acl = Get-Acl -LiteralPath $path
    [ordered]@{path=$path; owner=$acl.Owner; acl=$acl.Sddl}
})
$writers = @([IO.File]::ReadAllLines("$root\wrapper.log", $utf) | Where-Object { $_ -match '^2026-11-0[45] .*наряд .* -> [0-9]{8}-[0-9]{6}-[a-f0-9]+' })
$report = [ordered]@{utc=[datetime]::UtcNow.ToString('o'); identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name;
    source=$log; source_bytes=(Get-Item -LiteralPath $log).Length; events=$events.Count; first=$events[0].utc; last=$events[-1].utc;
    codes=@($events | Group-Object code | Select-Object Name,Count);
    object_types=@($events | Group-Object object_type | Select-Object Name,Count);
    event_paths=$paths; inventory=$inventory; parents=$parents; writer_log=$writers;
    event_stacks=@($events | Group-Object script_stack | ForEach-Object { @{count=$_.Count; stack=$_.Name} });
    event_exceptions=@($events | Group-Object exception | ForEach-Object { @{count=$_.Count; exception=$_.Name} });
    unavailable_metadata=@($events | Where-Object { $null -eq $_.acl }).Count;
    state_invalid=@($events | Where-Object { $_.code -eq 'STATE_INVALID' });
    event_details=@($events | Select-Object utc,path,script_stack);
    days=@($inventory | Group-Object { $_.last_write_utc.Substring(0,10) } | Select-Object Name,Count);
    marker_files=@($inventory | Where-Object { (Split-Path -Leaf $_.path) -cmatch '^[a-f0-9]{64}\.txt$' }).Count}
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'вимір.json'), ($report | ConvertTo-Json -Depth 10), $utf)
Write-Output "Подій: $($events.Count); шляхів: $($paths.Count); txt: $($inventory.Count); gemini читає: $(@($inventory | Where-Object readable_as_gemini).Count)"
