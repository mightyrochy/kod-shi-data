# Brings up the two local servers Lusterko needs. BY HAND, when you sit down to work.
# Comments are ASCII on purpose: powershell.exe 5.1 reads a .ps1 without BOM as ANSI.
#
# NOTHING HERE IS HOOKED TO THE WINDOWS LOGIN (owner's word 2026-09-24: "I will start
# things myself"). Checked the same day: HKCU/HKLM Run and RunOnce keys, both Startup
# folders and Task Scheduler hold nothing of this project.
#
# ORDER OF THINGS: this file first, the harvest second. Forgetting this file is not
# fatal -- the harvest checks the loaded model itself at startup and reloads it when the
# context is too small (see zhnyva_prompty.zviryty_model), and stops with a plain line
# when it cannot. This file is simply the faster way, and it also brings up :8000.
#
# Each server is started only if its port is silent, so running this twice is safe.

function Listening($port) {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

# 1. LM Studio :1234 -- the VLM/LLM for the harvest. `lms server start` also brings up the
#    app itself (minimised) when it is not running, so this one line is all it takes.
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
#    VERIFIED COLD 2026-09-24, twice: with every "LM Studio" process killed and :1234 silent,
#    this file alone brought the app up and left the model loaded at 16384 / 3 slots, 6.19 GB
#    -- about 80 s the first time, 9.5 s the second (same cold app, warm file cache).
#    So the one line really is all it takes, and the caller gets the prompt back.
#    Start-Process, not "&": the app `lms server start` spawns outlives lms.exe and INHERITS
#    stdout, so `powershell -File this.ps1 | ...` never saw end-of-stream and looked hung
#    (it was not -- the script had finished). A human at a console got the prompt back
#    either way; anything that CAPTURED the output did not. Measured the same day.
#    AND NOT -Wait, measured too: -Wait puts the target in a job object and waits for the
#    whole TREE, i.e. for the LM Studio app, which never exits -- with it the script itself
#    hung for 7 min instead of just the pipe. We wait for the PORT, which is the thing we
#    actually need, and say so plainly when it never answers.
if (-not (Listening 1234)) {
    Start-Process -FilePath "$env:USERPROFILE\.lmstudio\bin\lms.exe" `
        -ArgumentList 'server', 'start' -WindowStyle Hidden
    for ($i = 0; $i -lt 120 -and -not (Listening 1234); $i++) { Start-Sleep -Seconds 1 }
    if (-not (Listening 1234)) {
        Write-Host 'LM Studio is still silent on :1234 after 120 s -- open the app by hand, then run this file again.'
    }
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
# So no script can raise it without a human at the mouse. And it is not needed: :8000 is a superset
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
