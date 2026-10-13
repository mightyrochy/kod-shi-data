[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13
$url = "https://huggingface.co/Comfy-Org/flux1-kontext-dev_ComfyUI/resolve/main/split_files/diffusion_models/flux1-dev-kontext_fp8_scaled.safetensors"
$out = "C:\Users\Admin\ComfyUI\models\diffusion_models\flux1-dev-kontext_fp8_scaled.safetensors"
$log = "C:\Users\Admin\Open Source Stylist\experiments\017_editor_fidelity_benchoff\_kontext_download.log"
"START $(Get-Date -Format o)" | Out-File -FilePath $log -Encoding utf8
Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromHours(3)
try {
  $resp = $client.GetAsync($url, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).Result
  $resp.EnsureSuccessStatusCode() | Out-Null
  $total = $resp.Content.Headers.ContentLength
  "TOTAL $total" | Out-File -FilePath $log -Append -Encoding utf8
  $in = $resp.Content.ReadAsStreamAsync().Result
  $fs = [System.IO.File]::Create($out)
  $buf = New-Object byte[] (8388608)
  $sum = 0L; $mark = 0L; $read = 0
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  while (($read = $in.Read($buf,0,$buf.Length)) -gt 0) {
    $fs.Write($buf,0,$read); $sum += $read
    if (($sum - $mark) -ge 536870912) {
      $mark = $sum
      $mb = [math]::Round($sum/1MB,0); $pct = if($total){[math]::Round(100*$sum/$total,1)}else{0}
      $rate = [math]::Round($mb/$sw.Elapsed.TotalSeconds,1)
      "PROGRESS ${mb}MB / $([math]::Round($total/1MB,0))MB  ${pct}%  ${rate}MB/s" | Out-File -FilePath $log -Append -Encoding utf8
    }
  }
  $fs.Close(); $in.Close()
  "DONE bytes=$sum expected=$total ok=$([bool]($sum -eq $total)) elapsed=$([math]::Round($sw.Elapsed.TotalMinutes,1))min" | Out-File -FilePath $log -Append -Encoding utf8
} catch {
  "ERROR $($_.Exception.Message)" | Out-File -FilePath $log -Append -Encoding utf8
  exit 1
}
