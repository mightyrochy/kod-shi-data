# Діагностика: 20 знімків кожні 30 с. Лише читає. Параметр: тека виводу.
param([string]$Out, [int]$N = 20, [int]$Step = 30)
Add-Type @'
using System; using System.Runtime.InteropServices; using System.Text;
public class W {
 [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
 [DllImport("user32.dll")] public static extern int GetWindowThreadProcessId(IntPtr h, out int pid);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
 [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
 [DllImport("user32.dll")] public static extern bool GetLastInputInfo(ref LII i);
 [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
 [StructLayout(LayoutKind.Sequential)] public struct LII { public uint cb; public uint t; }
}
'@
Add-Type -AssemblyName System.Windows.Forms
$sid = (Get-Process -Id $PID).SessionId
$scr = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
"measure_pid=$PID session=$sid screen=$($scr.Width)x$($scr.Height)" | Out-File "$Out\мета.txt" -Encoding utf8
for ($i = 0; $i -lt $N; $i++) {
  $t0 = Get-Date
  $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
  $smi = (nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free --format=csv,noheader) -join ';'
  $pmon = (nvidia-smi pmon -c 1 -s u) -join "`n"
  $rows = @()
  try {
    $cs = (Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction Stop).CounterSamples
    $agg = @{}
    foreach ($s in $cs) {
      if ($s.CookedValue -le 0) { continue }
      if ($s.InstanceName -match 'pid_(\d+)_.*engtype_(.+)$') {
        $k = "$($Matches[1])|$($Matches[2])"; $agg[$k] = [double]$agg[$k] + $s.CookedValue
      }
    }
    $byPid = @{}
    foreach ($k in $agg.Keys) { $p = $k.Split('|')[0]; $byPid[$p] = [double]$byPid[$p] + $agg[$k] }
    $rows = @()
    foreach ($e in ($byPid.GetEnumerator() | Sort-Object Value -Descending | Select-Object -First 10)) {
      $gp = [int]$e.Key
      $gn = ''; $proc = Get-Process -Id $gp -ErrorAction SilentlyContinue; if ($proc) { $gn = [string]$proc.ProcessName }
      $eng = (@($agg.Keys) | Where-Object { $_ -like "$gp|*" } | ForEach-Object { $_.Split('|')[1] + '=' + [math]::Round($agg[$_],1) }) -join ','
      $rows += [pscustomobject]@{ pid = $gp; name = $gn; sum = [math]::Round($e.Value,1); engines = $eng }
    }
  } catch { $rows = @([pscustomobject]@{ error = $_.Exception.Message }) }
  $lii = New-Object W+LII; $lii.cb = 8; [void][W]::GetLastInputInfo([ref]$lii)
  $idle = [int](([Environment]::TickCount - [int]$lii.t) / 1000)
  $h = [W]::GetForegroundWindow(); $fpid = 0; [void][W]::GetWindowThreadProcessId($h, [ref]$fpid)
  $r = New-Object W+RECT; [void][W]::GetWindowRect($h, [ref]$r)
  $sb = New-Object System.Text.StringBuilder 200; [void][W]::GetWindowText($h, $sb, 200)
  $full = ($r.R - $r.L -ge $scr.Width) -and ($r.B - $r.T -ge $scr.Height)
  $fg = [pscustomobject]@{ pid = $fpid; name = (Get-Process -Id $fpid -ErrorAction SilentlyContinue).ProcessName; title = $sb.ToString(); fullscreen = $full }
  $q = (quser 2>&1) -join ' | '
  [pscustomobject]@{ utc = $ts; smi = $smi; pmon = $pmon; top = $rows; idle_s = $idle; fg = $fg; quser = $q } |
    ConvertTo-Json -Depth 5 -Compress | Add-Content "$Out\знімки.jsonl" -Encoding utf8
  $left = $Step - ((Get-Date) - $t0).TotalSeconds
  if ($left -gt 0 -and $i -lt $N - 1) { Start-Sleep -Seconds $left }
}
