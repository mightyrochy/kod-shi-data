# Download Marqo FashionSigLIP model files for garment_fidelity.py
# Uses HttpWebRequest streaming - no timeout/memory issues.

$modelDir = "C:\Users\Admin\Open Source Stylist\system\gates\models\marqo-fashionSigLIP"
$hfBase   = "https://huggingface.co/Marqo/marqo-fashionSigLIP/resolve/main"

function Download-File($url, $dest) {
    if ((Test-Path $dest) -and ((Get-Item $dest).Length -gt 0)) {
        Write-Host "  SKIP ($([math]::Round((Get-Item $dest).Length/1MB,1)) MB): $(Split-Path $dest -Leaf)"
        return
    }
    $dir = Split-Path $dest -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

    Write-Host "  GET  $(Split-Path $dest -Leaf) ..."
    $req = [System.Net.HttpWebRequest]::Create($url)
    $req.Timeout          = 7200000   # 2 h
    $req.ReadWriteTimeout = 600000    # 10 min per read
    $req.UserAgent        = "Mozilla/5.0"

    try {
        $resp      = $req.GetResponse()
        $totalMB   = [math]::Round($resp.ContentLength / 1MB, 1)
        $inStream  = $resp.GetResponseStream()
        $outStream = [System.IO.File]::Create($dest)
        $buf       = New-Object byte[] (1048576)
        $done      = 0
        while ($true) {
            $r = $inStream.Read($buf, 0, $buf.Length)
            if ($r -eq 0) { break }
            $outStream.Write($buf, 0, $r)
            $done += $r
        }
        $outStream.Close(); $inStream.Close(); $resp.Close()
        Write-Host "  DONE $([math]::Round($done/1MB,1)) MB / $totalMB MB"
    } catch {
        if ($outStream) { $outStream.Close() }
        Write-Host "  ERROR: $_"
        if (Test-Path $dest) { Remove-Item $dest -Force }
        throw
    }
}

Write-Host "`n=== Marqo FashionSigLIP (~350 MB) ==="
Download-File "$hfBase/open_clip_config.json"        "$modelDir\open_clip_config.json"
Download-File "$hfBase/open_clip_pytorch_model.bin"  "$modelDir\open_clip_pytorch_model.bin"

Write-Host "`n=== FashionSigLIP download complete ==="
