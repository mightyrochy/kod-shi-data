# Вимірює справжній Invoke-Native з UTF-8/BOM стандартного stdin .NET Framework, без Main і мережі.
param([string]$InputScript, [string]$PythonExe = 'python', [string]$ProbeOut)
. $InputScript
$previous = [Console]::InputEncoding
try {
    [Console]::InputEncoding = [Text.Encoding]::UTF8
    $preamble = [Console]::InputEncoding.GetPreamble().Length
    # Читає лише 3 байти в дочірньому процесі; батько навіть не звертається до StandardInput.
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $PythonExe
    $psi.Arguments = '-c "import sys;print(sys.stdin.buffer.read(3).hex(),flush=True)"'
    $psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
    $psi.RedirectStandardInput = $true; $psi.RedirectStandardOutput = $true
    $raw = [Diagnostics.Process]::Start($psi)
    try {
        if (-not $raw.WaitForExit(3000)) { $raw.Kill(); throw 'Start не надіслав преамбулу' }
        $prefix = $raw.StandardOutput.ReadToEnd().Trim()
    } finally { $raw.Dispose() }
    $text = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/невідомо ISOLATION_FAILED'
    $r = Invoke-Native $PythonExe @('-c', 'import sys,json; b=sys.stdin.buffer.read(); print(json.dumps({"hex":b.hex(),"text":b.decode("utf-8")}))') '' 1 $text
    $body = $r.Out | ConvertFrom-Json
    $result = [ordered]@{ preamble = $preamble; start_prefix = $prefix; code = $r.Code; first = [int][char]$body.text[0]; exact = [string]::Equals($body.text, $text, [StringComparison]::Ordinal); hex = $body.hex; encoding_restored = ([Console]::InputEncoding.GetPreamble().Length -eq $preamble) }
    [System.IO.File]::WriteAllText($ProbeOut, ($result | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))
} finally { [Console]::InputEncoding = $previous }
