# ComfyUI :8000 -- GroundingDINO + SAM for the harvest masks (zhnyva_masky.маска_sam).
# Comments are ASCII on purpose: powershell.exe 5.1 reads a .ps1 without BOM as ANSI.
#
# The SSLKEYLOGFILE line below is the whole reason this file exists. Avast injects
#   SSLKEYLOGFILE=\\.\aswMonFltProxy\<id>
# into every process it watches. It is NOT in the registry -- neither HKCU\Environment
# nor HKLM ...\Session Manager\Environment -- so it cannot be seen or removed there.
# Python's ssl module honours that variable and opens the keylog through OpenSSL
# BIO_new_fp, which needs an "applink" that python.exe does not export, so the first
# ssl.create_default_context() during ComfyUI startup kills the process with
#   OPENSSL_Uplink(00007FF915239C60,08): no OPENSSL_Applink
# Measured 2026-09-24 with this very venv:
#   var as inherited -> that error, exit 1;  var cleared -> "ok", exit 0.
# Clearing it here touches THIS process only; the global variable stays as Avast set it
# (removing it system-wide is the owner's call, not ours).
$env:SSLKEYLOGFILE = $null
Remove-Item Env:SSLKEYLOGFILE -ErrorAction SilentlyContinue

# --base-directory holds models/ and custom_nodes/ (comfyui_segment_anything lives there);
# the code is the Comfy Desktop checkout, run from its own .venv rather than the app.
$py = 'C:\Users\Admin\ComfyUI-Installs\ComfyUI\ComfyUI\.venv\Scripts\python.exe'
Set-Location 'C:\Users\Admin\ComfyUI-Installs\ComfyUI'
& $py -s 'ComfyUI\main.py' --port 8000 --base-directory 'C:\Users\Admin\ComfyUI' --disable-auto-launch
