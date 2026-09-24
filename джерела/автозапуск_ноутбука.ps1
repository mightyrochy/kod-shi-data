# Autostart for the three local services Lusterko needs. Comments are ASCII on purpose:
# powershell.exe 5.1 reads a .ps1 without BOM as ANSI.
#
# Checked 2026-09-24: NOTHING started these at login -- HKCU/HKLM Run keys, both Startup
# folders and Task Scheduler had no LM Studio, no Comfy Desktop, no :8000. The laptop
# booted 23.09 20:01 and the apps were opened by hand at 07:56/07:57 on 24.09. So this is
# the FIRST autostart, not a second one: the hook is a single shortcut in
#   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\kod-shi-autostart.lnk
# which does nothing but run this file. Delete it to turn the whole thing off.
# A .lnk rather than a .cmd because this file's own path is Cyrillic: .lnk stores it in
# UTF-16, while cmd.exe would read a .cmd in the OEM codepage and mangle it.
#
# Each service is started only if its port is silent, so running this by hand at any time
# is safe and repeatable.

function Listening($port) {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

# 1. LM Studio :1234 -- the VLM/LLM for the harvest. `lms server start` also brings up the
#    app itself (minimised) when it is not running, so this is all the login needs.
#
#    THE EXPLICIT LOAD IS NOT OPTIONAL. Just-in-time loading is on in
#    http-server-config.json, and it loads the model with n_ctx 4096 shared across 4 slots.
#    The harvest runs three threads. Measured 2026-09-24, nine real photo requests through
#    zhnyva's own _zapyt:
#      JIT (context 4096), 3 threads   -> 0 ok, 9 HTTP 400
#      -c 16384 --parallel 3, 3 threads -> 9 ok, 0 failures
#    (one at a time JIT survives -- 6 of 6 -- which is why this trap hides in single tests.)
#    So the model is loaded here with the context the harvest actually needs. It costs
#    6.19 GB of VRAM standing by; that is the state the laptop was already in and the
#    state in which the try-on measured 35.5 s per image, so ComfyUI has room.
if (-not (Listening 1234)) {
    & "$env:USERPROFILE\.lmstudio\bin\lms.exe" server start
}
$loaded = & "$env:USERPROFILE\.lmstudio\bin\lms.exe" ps 2>$null | Out-String
if ($loaded -notmatch '16384') {
    & "$env:USERPROFILE\.lmstudio\bin\lms.exe" unload --all 2>$null
    & "$env:USERPROFILE\.lmstudio\bin\lms.exe" load qwen3-vl-8b-instruct --gpu max -c 16384 --parallel 3 -y
}

# Comfy Desktop :8188 is NOT started here, and that is deliberate (tested 2026-09-24).
# Launching Comfy Desktop.exe does NOT bring up a server: v1.1.2 opens an instance PICKER
# ("New Instance / ComfyUI / Comfy Cloud") and waits for a click -- verified by screenshot
# after 7 minutes of the app sitting idle with nothing past "[core-beta] init" in its log.
# So it could never have worked at login either. And it is not needed: :8000 is a superset
# -- 1223 nodes against 958, every try-on node (TextEncodeQwenImageEditPlus,
# LoraLoaderModelOnly, ReferenceLatent) and every weight (qwen_image_edit_2511_fp8mixed,
# the Lightning 4-step LoRA, flux-2-klein, tryon-klein-4b) is there, because both read the
# same C:\Users\Admin\ComfyUI models directory. The product already agrees: OSS
# ComfyUIClient defaults to port 8000 and pipeline.py documents :8000. Starting a headless
# :8188 here would only take the port away from the owner's GUI.

# 2. ComfyUI :8000 -- everything: masks (SAM 3.1) and try-on. Hidden window: it is a
#    server, not something to look at. See the *sam_8000.ps1 next to this file for why it
#    cannot simply be started from a normal shell (Avast's SSLKEYLOGFILE).
#    The sibling is found by pattern instead of being named here: this file itself sits in
#    a Cyrillic folder, and powershell.exe 5.1 reads a BOM-less .ps1 as ANSI, so a Cyrillic
#    literal in the source would arrive mangled. Nothing but ASCII goes in these two files.
if (-not (Listening 8000)) {
    $sam = Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*sam_8000.ps1' |
        Select-Object -First 1 -ExpandProperty FullName
    if ($sam) {
        Start-Process powershell -ArgumentList @(
            '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', $sam)
    }
}
