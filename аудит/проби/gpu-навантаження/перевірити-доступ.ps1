$ErrorActionPreference = 'Stop'
$capture = [ordered]@{
    utc = [DateTime]::UtcNow.ToString('o')
    session_id = [Diagnostics.Process]::GetCurrentProcess().SessionId
    process_64_bit = [Environment]::Is64BitProcess
}
function Read-Probe([scriptblock]$Action) {
    try { @(& $Action) } catch { [ordered]@{ error = $_.ToString(); error_id = $_.FullyQualifiedErrorId } }
}
$capture.gpu = Read-Probe { & nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.free --format=csv,noheader }
$capture.pmon = Read-Probe { & nvidia-smi pmon -c 1 -s u }
$capture.nvidia_processes = Read-Probe { & nvidia-smi }
$capture.engine_counters = Read-Probe {
    Get-Counter '\GPU Engine(*)\Utilization Percentage' | Select-Object -ExpandProperty CounterSamples |
        Select-Object InstanceName, CookedValue
}
$capture.counter_sets = Read-Probe {
    Get-Counter -ListSet '*GPU*' | Select-Object CounterSetName, Paths
}
$capture.cim_formatted = Read-Probe {
    Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine |
        Select-Object Name, UtilizationPercentage
}
$capture.cim_raw = Read-Probe {
    Get-CimInstance Win32_PerfRawData_GPUPerformanceCounters_GPUEngine |
        Select-Object Name, UtilizationPercentage
}
$capture.quser = Read-Probe { & quser 2>&1 }
$capture.desktop_processes = Read-Probe {
    Get-Process dwm,explorer | Select-Object Id, SessionId, ProcessName
}
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class GpuDiagnosticDesktop {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [StructLayout(LayoutKind.Sequential)]
    public struct LASTINPUTINFO { public uint cbSize; public uint dwTime; }
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool GetLastInputInfo(ref LASTINPUTINFO value);
}
'@
$capture.foreground_handle = [GpuDiagnosticDesktop]::GetForegroundWindow().ToInt64()
$lastInput = New-Object GpuDiagnosticDesktop+LASTINPUTINFO
$lastInput.cbSize = [Runtime.InteropServices.Marshal]::SizeOf($lastInput)
$capture.last_input_success = [GpuDiagnosticDesktop]::GetLastInputInfo([ref]$lastInput)
$capture.last_input_tick = $lastInput.dwTime
$capture.last_input_error = [Runtime.InteropServices.Marshal]::GetLastWin32Error()
$capture.utc_end = [DateTime]::UtcNow.ToString('o')
$capture | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $PSScriptRoot 'raw.json')
