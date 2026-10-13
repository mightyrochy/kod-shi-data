# -*- coding: utf-8 -*-
"""Рядок 153 (4б): tryon-klein-4b — LoRA (92 МБ, Apache-2.0) до FLUX.2-klein-4B, на тому самому вході E-017, що й QIE-2511
у `vymir_prymiryannya_153.py`, і тими самими мірками: ArcFace buffalo_l і dE00 кожної речі до еталонної маски E-001.
Картка LoRA вимагає ТРЬОХ входів у порядку «людина без одягу в масці, верх, низ» — проба їх і робить: agnostic (регіони
одягу ATR зафарбовані сірим) і дві речі за маскою E-001 на білому. Граф — `_payload_flux2klein.json` E-017 плюс третій
ReferenceLatent і LoRA. Взуття ця LoRA не несе за побудовою, і це має бути видно числом. `--сам` — входи без ComfyUI.
`cd джерела && python проби/vymir_klein_153.py [--сам]`."""
import json, os, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); import cv2, numpy as np, жнива_v2 as Ж, verify as V
ПОРТ, E017, ЛОРА = int(os.environ.get("COMFY_PORT_153", "8188")), os.path.join(Ж.OSS, "experiments", "017_editor_fidelity_benchoff"), "tryon-klein-4b.safetensors"
ОСОБА, ПРОМПТ = os.path.join(E017, "results", "_input_person.png"), "TRYON a full-body photo of a person. Replace the outfit with the top and bottom as shown in the reference images. The final image is a full body shot."; sys.path.append(Ж.OSS) if Ж.OSS not in sys.path else None; from system.gates.identity import compare_faces; реф = json.load(open(os.path.join(Ж.OSS, "assets", "outfits", "outfit_001", "eval_references.json"), encoding="utf-8"))
ЕТАЛОНИ, тимч = [("блуза", "верх", "top"), ("спідниця", "низ", "bottom"), ("взуття", "взуття", "shoes")], tempfile.mkdtemp(prefix="k153_")
def річ(ключ, ім):
    """(фото речі на білому для входу LoRA, домінантний тон Lab еталона) — за маскою E-001 з `eval_references.json`."""
    ф, мс = [os.path.join(Ж.OSS, п.replace("/", os.sep)) for п in реф[ключ]]; bgr, м = cv2.imread(ф), cv2.imread(мс, 0)
    м = м if м.shape[:2] == bgr.shape[:2] else cv2.resize(м, (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_NEAREST)
    біле = np.full_like(bgr, 255); біле[м > 127] = bgr[м > 127]; п = os.path.join(тимч, ім + ".png"); cv2.imwrite(п, біле)
    return п, ([tuple(к["lab"]) for к in Ж.виміряти_колір(ф, м)[0] if к["частка"] >= 0.05] + [None])[0]
def agnostic(шлях):
    """Людина без одягу: регіони одягу ATR (одяг, пояс, взуття) зафарбовані сірим — як просить картка LoRA."""
    bgr = cv2.imread(шлях); bgr[cv2.resize(np.isin(Ж._мітки_atr(шлях), [4, 5, 6, 7, 8, 9, 10]).astype("uint8"), (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_NEAREST) > 0] = 128
    п = os.path.join(тимч, "agnostic.png"); cv2.imwrite(п, bgr); return п
верх, низ, взуття = річ("top", "top"), річ("bottom", "bottom"), річ("shoes", "shoes"); еталон, особа_ф = {"блуза": верх[1], "спідниця": низ[1], "взуття": взуття[1]}, agnostic(ОСОБА)
if "--сам" in sys.argv: print("(4б) --сам · входи %d/3 (agnostic %s) · еталонні тони %d/3" % (sum(os.path.exists(ф) for ф in (особа_ф, верх[0], низ[0])), os.path.exists(особа_ф), sum(в is not None for в in еталон.values()))); sys.exit(0 if all(еталон.values()) and all(os.path.exists(ф) for ф in (особа_ф, верх[0], низ[0])) else 1)
from system.clients.comfyui import ComfyUIClient; к = ComfyUIClient("127.0.0.1", ПОРТ)
п = json.load(open(os.path.join(E017, "_payload_flux2klein.json"), encoding="utf-8"))["prompt"]
п["76"]["inputs"]["image"], п["81"]["inputs"]["image"] = к.upload_image(особа_ф), к.upload_image(верх[0])
п["113"]["inputs"]["text"], п["9"]["inputs"]["filename_prefix"] = ПРОМПТ, "к153"
п["200"] = dict(class_type="LoadImage", inputs=dict(image=к.upload_image(низ[0])))
п["201"] = dict(class_type="ImageScaleToTotalPixels", inputs=dict(image=["200", 0], upscale_method="nearest-exact", megapixels=1.0, resolution_steps=1))
п["202"] = dict(class_type="VAEEncode", inputs=dict(pixels=["201", 0], vae=["107", 0]))
п["203"] = dict(class_type="ReferenceLatent", inputs=dict(conditioning=["130", 0], latent=["202", 0]))
п["204"] = dict(class_type="ReferenceLatent", inputs=dict(conditioning=["128", 0], latent=["202", 0]))
п["205"] = dict(class_type="LoraLoaderModelOnly", inputs=dict(model=["106", 0], lora_name=ЛОРА, strength_model=1.0))
п["114"]["inputs"].update(model=["205", 0], positive=["203", 0], negative=["204", 0])
т0 = time.time(); в = к.poll(к.submit(п), timeout=1800)["9"]["images"][0]
вихід = os.path.join(тимч, "klein.png"); open(вихід, "wb").write(к.download(в["filename"], в.get("subfolder", ""), в.get("type", "output")))
с, кос, арр = time.time() - т0, compare_faces(вихід, ОСОБА)["cosine"], Ж._мітки_atr(вихід)
де = {ім: round(min([V.de00(tuple(к_["lab"]), еталон[ім]) for к_ in Ж.виміряти_колір(вихід, Ж.маска_atr(вихід, Ж.СЛОТ_РЕГІОНИ[сл], арр)[0])[0] if к_["частка"] >= 0.05] or [99.0]), 1) for ім, сл, _ in ЕТАЛОНИ}
print("(4б) tryon-klein-4b · ArcFace %s (поріг 0.57) · речей %d/3 dE00 %s (поріг 10) · %.1f с/образ · вихід %s" % (кос, sum(в_ <= 10 for в_ in де.values()), де, с, вихід))
