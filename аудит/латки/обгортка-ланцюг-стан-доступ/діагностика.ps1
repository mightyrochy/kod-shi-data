function Get-StateFailurePath($Failure) {
    <# Бере шлях із контексту читача або цільового об'єкта помилки, не з довільного повідомлення. #>
    if ($null -eq $Failure) { return '' }
    for ($e = $Failure.Exception; $null -ne $e; $e = $e.InnerException) {
        if ($e.Data.Contains('StatePath')) { return [string]$e.Data['StatePath'] }
    }
    $target = $Failure.TargetObject
    if ($target -is [IO.FileSystemInfo]) { return $target.FullName }
    if ($target -is [string] -and [IO.Path]::IsPathRooted($target)) { return $target }
    ''
}

function Read-ChainStateText([string]$Path) {
    <# Зберігає точний шлях невдалого читання, лишаючи початковий виняток і стек. #>
    try { [IO.File]::ReadAllText($Path, $script:Utf8) }
    catch { $_.Exception.Data['StatePath'] = [IO.Path]::GetFullPath($Path); throw }
}

function Write-StateFailureDiagnostic([string]$Code, $Failure, [string]$Path = '', [string]$Why = '') {
    <# Дописує кожен збій окремим JSON-рядком у наявну теку обміну, доступну gemini.

    Відмова читання метаданих записується окремо; вона не підміняє початковий виняток. #>
    if (-not $Path) { $Path = Get-StateFailurePath $Failure }
    $record = [ordered]@{
        utc = [datetime]::UtcNow.ToString('o'); code = $Code; reason = $Why
        path = $Path; object_type = 'unavailable'; owner = $null; acl = $null; last_write_utc = $null
        exception = ''; script_stack = ''; position = ''; metadata_errors = @()
    }
    if ($null -ne $Failure) {
        $record.exception = $Failure.Exception.ToString()
        $record.script_stack = [string]$Failure.ScriptStackTrace
        $record.position = [string]$Failure.InvocationInfo.PositionMessage
    }
    if ($Path) {
        try {
            $Path = [IO.Path]::GetFullPath($Path); $record.path = $Path
            $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
            $record.object_type = $(if ($item.PSIsContainer) { 'directory' } else { 'file' })
            $record.last_write_utc = $item.LastWriteTimeUtc.ToString('o')
        } catch { $record.metadata_errors += 'item: ' + $_.Exception.ToString() }
        try {
            $acl = Get-Acl -LiteralPath $Path -ErrorAction Stop
            $record.owner = $acl.Owner; $record.acl = $acl.Sddl
        } catch { $record.metadata_errors += 'acl: ' + $_.Exception.ToString() }
    }
    try {
        [void][IO.Directory]::CreateDirectory($OutDir)
        [IO.File]::AppendAllText((Join-Path $OutDir 'state-failures.jsonl'), (($record | ConvertTo-Json -Compress -Depth 6) + "`n"), $script:Utf8)
    } catch { Write-WrapperLog ("діагностику $Code не записано: " + $_.Exception.Message) }
    $Path
}

