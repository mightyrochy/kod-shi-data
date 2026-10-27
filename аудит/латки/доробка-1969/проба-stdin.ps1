# Вимірює справжній Invoke-Native з UTF-8/BOM стандартного stdin .NET Framework, без Main і мережі.
param([string]$InputScript, [string]$PythonExe = 'python', [string]$ProbeOut)
. $InputScript
$previous = [Console]::InputEncoding
try {
    [Console]::InputEncoding = [Text.Encoding]::UTF8
    $preamble = [Console]::InputEncoding.GetPreamble().Length
    $text = 'GEMINI ОБГОРТКА: ЗАБЛОКОВАНО gemini/невідомо ISOLATION_FAILED'
    $r = Invoke-Native $PythonExe @('-c', 'import sys,json; b=sys.stdin.buffer.read(); print(json.dumps({"hex":b.hex(),"text":b.decode("utf-8")}))') '' 1 $text
    $body = $r.Out | ConvertFrom-Json
    $result = [ordered]@{ preamble = $preamble; code = $r.Code; first = [int][char]$body.text[0]; exact = [string]::Equals($body.text, $text, [StringComparison]::Ordinal); hex = $body.hex; encoding_restored = ([Console]::InputEncoding.GetPreamble().Length -eq $preamble) }
    [System.IO.File]::WriteAllText($ProbeOut, ($result | ConvertTo-Json), (New-Object System.Text.UTF8Encoding($false)))
} finally { [Console]::InputEncoding = $previous }
