# -*- coding: utf-8 -*-
"""Рядок 153 (4): приміряння — поточна QIE-2511 fp8mixed 20 кроків проти Lightning 4 кроки. Вхід і граф заморожені з E-017
(`_payload_qie_board.json`, `_input_person.png` + дошка `_input_board.png`, сід 42), тож ArcFace порівнянний з E-017 (0.950).
Міряє те, на чому E-017 ловив klein: ArcFace buffalo_l до вхідного фото (поріг 0.57) І чи перенесено КОЖНУ річ дошки —
блузу, спідницю, взуття. Річ перенесено = регіони слота ATR (як у `маска_речі`: «низ» — skirt АБО pants) є на виході, і котрийсь
тон від 5 % маски ближче за dE00 10 до еталонного тону (маска E-001, `eval_references.json`). `--сам` — без ComfyUI.
`cd джерела && python проби/vymir_prymiryannya_153.py [qie20 lightning4] [--сам]`."""
import json, os, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import cv2, жнива_v2 as Ж, verify as V
ПОРТ, E017, ЛОРА = int(os.environ.get("COMFY_PORT_153", "8188")), os.path.join(Ж.OSS, "experiments", "017_editor_fidelity_benchoff"), "Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors"
ЕТАЛОНИ, ОСОБА, ДОШКА = [("блуза", "верх", "top"), ("спідниця", "низ", "bottom"), ("взуття", "взуття", "shoes")], os.path.join(E017, "results", "_input_person.png"), os.path.join(E017, "results", "_input_board.png"); двигуни, сам, ПОРІГ =[а for а in sys.argv[1:] if not а.startswith("--")] or ["qie20", "lightning4"], "--сам" in sys.argv, 10.0
sys.path.append(Ж.OSS) if Ж.OSS not in sys.path else None; from system.gates.identity import compare_faces; реф = json.load(open(os.path.join(Ж.OSS, "assets", "outfits", "outfit_001", "eval_references.json"), encoding="utf-8"))
def тони(шлях, м):
    """Тони Lab речі на фото за маскою — кластери `виміряти_колір` жнив від 5 % маски (дрібну річ маска бере з тінню)."""
    return [tuple(к["lab"]) for к in (Ж.виміряти_колір(шлях, м)[0] if м is not None else []) if к["частка"] >= 0.05]
def еталон_тон(ключ):
    """Домінантний тон Lab еталонної речі: фото + маска E-001, підігнана під фото."""
    ф, мс = [os.path.join(Ж.OSS, п.replace("/", os.sep)) for п in реф[ключ]]; м, im = cv2.imread(мс, 0), cv2.imread(ф)
    return ([*тони(ф, м if м.shape[:2] == im.shape[:2] else cv2.resize(м, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST)), None])[0]
еталон = {ім: еталон_тон(к) for ім, _, к in ЕТАЛОНИ}
if сам:
    кос = compare_faces(ОСОБА, ОСОБА)["cosine"]; print("(4) --сам · еталонні тони %d/%d · ArcFace на собі %s" % (sum(в is not None for в in еталон.values()), len(ЕТАЛОНИ), кос))
    sys.exit(0 if all(еталон.values()) and кос and кос > 0.99 else 1)
from system.clients.comfyui import ComfyUIClient; к = ComfyUIClient("127.0.0.1", ПОРТ)
особа, дошка, тимч = к.upload_image(ОСОБА), к.upload_image(ДОШКА), tempfile.mkdtemp(prefix="p153_")
for двигун in двигуни:
    п = json.load(open(os.path.join(E017, "_payload_qie_board.json"), encoding="utf-8"))["prompt"]
    п["4"]["inputs"]["image"], п["5"]["inputs"]["image"], п["11"]["inputs"]["filename_prefix"] = особа, дошка, "п153_" + двигун
    if двигун == "lightning4":
        п["18"] = dict(class_type="LoraLoaderModelOnly", inputs=dict(model=["1", 0], lora_name=ЛОРА, strength_model=1.0))
        п["14"]["inputs"]["model"], _ = ["18", 0], п["9"]["inputs"].update(steps=4, cfg=1.0)
    т0 = time.time()
    try:
        в = к.poll(к.submit(п), timeout=1800)["11"]["images"][0]
        вихід = os.path.join(тимч, двигун + ".png"); open(вихід, "wb").write(к.download(в["filename"], в.get("subfolder", ""), в.get("type", "output")))
    except Exception as e: print("(4) %-11s ЗБІЙ: %s" % (двигун, str(e)[:170])); continue
    с, кос, арр = time.time() - т0, compare_faces(вихід, ОСОБА)["cosine"], Ж._мітки_atr(вихід)
    де = {ім: round(min([V.de00(т, еталон[ім]) for т in тони(вихід, Ж.маска_atr(вихід, Ж.СЛОТ_РЕГІОНИ[сл], арр)[0])] or [99.0]), 1) for ім, сл, _ in ЕТАЛОНИ}
    vram = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=20).stdout.strip()
    print("(4) %-11s ArcFace %s (поріг 0.57) · речей %d/%d dE00 %s (поріг %.0f) · %.1f с/образ · VRAM %s · вихід %s" % (двигун, кос, sum(в <= ПОРІГ for в in де.values()), len(ЕТАЛОНИ), де, ПОРІГ, с, vram, вихід))
