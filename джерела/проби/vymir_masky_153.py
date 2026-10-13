# -*- coding: utf-8 -*-
"""Рядок 153 (2): маска речі — поточна (ATR -> SAM -> запасна) проти SAM 3.1 і BiRefNet у ComfyUI :8188. Набір — кадри
вибірки v2 з git (`аудит/фото_v2/`), ті самі, що в (1) і (5). «Маска — сама річ» рахується без ока: шкіри ATR у масці
<= 2 %, пікселів кольору рамки кадру (тло) <= 10 %, сім'я тону виміру — у словах крамниці. Окремо «ціла_річ» і «на_моделі»:
BiRefNet бере передній план цілком. Фото в %TEMP% латиницею (cv2 на Windows не читає кирилиці в шляху). `--сам` — лише поточна,
без ComfyUI. `cd джерела && python проби/vymir_masky_153.py [поточна sam3 birefnet] [--сам]`."""
import json, os, shutil, sys, tempfile, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cv2, numpy as np, жнива_v2 as Ж, жнива_маски as М, verify as V
ПОРТ, ТЕКА = int(os.environ.get("COMFY_PORT_153", "8188")), os.path.join(Ж.ТУТ, "аудит")
методи = [а for а in sys.argv[1:] if not а.startswith("--")] or (["поточна"] if "--сам" in sys.argv else ["поточна", "sam3", "birefnet"])
ХВІСТ = '"3":{"class_type":"LoadImage","inputs":{"image":"ІМЯ"}},"5":{"class_type":"MaskToImage","inputs":{"mask":["4",0]}},"6":{"class_type":"SaveImage","inputs":{"images":["5",0],"filename_prefix":"м153"}}}'
ГРАФИ = {"sam3": '{"1":{"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"sam3.1_multiplex_fp16.safetensors"}},"2":{"class_type":"CLIPTextEncode","inputs":{"text":"СЛОВО","clip":["1",1]}},"4":{"class_type":"SAM3_Detect","inputs":{"model":["1",0],"image":["3",0],"threshold":0.5,"refine_iterations":2,"individual_masks":false,"conditioning":["2",0]}},' + ХВІСТ,
         "birefnet": '{"1":{"class_type":"LoadBackgroundRemovalModel","inputs":{"bg_removal_name":"birefnet.safetensors"}},"4":{"class_type":"RemoveBackground","inputs":{"bg_removal_model":["1",0],"image":["3",0]}},' + ХВІСТ}
def сама_річ(шлях, м, арр, слова):
    """Маска — сама річ: без шкіри ATR, без кольору рамки кадру, і виміряний колір у сім'ї слова крамниці."""
    bgr = cv2.imread(шлях); h, w = bgr.shape[:2]
    б = None if м is None else (м if м.shape[:2] == (h, w) else cv2.resize(м, (w, h), interpolation=cv2.INTER_NEAREST)) > 127
    if б is None or int(б.sum()) < 300: return False
    шк, к = М._шкіра_atr(арр, (w, h)), max(4, min(h, w) // 40); тло = float((np.linalg.norm(bgr.astype("float32") - np.median(np.concatenate([bgr[:к].reshape(-1, 3), bgr[-к:].reshape(-1, 3), bgr[:, :к].reshape(-1, 3), bgr[:, -к:].reshape(-1, 3)]), axis=0), axis=2)[б] <= 28).mean())
    if (0.0 if шк is None else float((б & шк).sum()) / int(б.sum())) > 0.02 or тло > 0.10: return False
    кл, _ = Ж.виміряти_колір(шлях, б.astype("uint8") * 255)
    return (not слова) or bool(кл) and V.сім_я_слова(кл[0]["слово"]) in {V.сім_я_слова(с) for с in слова}
речі = [з for з in json.load(open(os.path.join(ТЕКА, "збагачення_v2_вибірка.json"), encoding="utf-8"))["речі"] if os.path.exists(os.path.join(ТЕКА, з.get("фото_показу") or "-"))]
тимч = tempfile.mkdtemp(prefix="m153_"); фото = [(shutil.copy(os.path.join(ТЕКА, з["фото_показу"]), os.path.join(тимч, "%03d.jpg" % н)), з) for н, з in enumerate(речі)]
sys.path.append(Ж.OSS) if Ж.OSS not in sys.path else None; from system.clients.comfyui import ComfyUIClient; к = ComfyUIClient("127.0.0.1", ПОРТ)
for метод in методи:
    лік, збої, т0 = {"ціла_річ": [0, 0], "на_моделі": [0, 0]}, {}, time.time()
    for шлях, з in фото:
        арр, кадр = Ж._мітки_atr(шлях), з.get("кадр") or {}
        try:
            if метод == "поточна": м = Ж.маска_речі(шлях, з["слот"])[0]
            else:
                г = ГРАФИ[метод].replace("ІМЯ", к.upload_image(шлях)).replace("СЛОВО", Ж._sam_слово(з["слот"], арр) or "clothing")
                в = к.poll(к.submit(json.loads(г)), timeout=300)["6"]["images"][0]
                м = cv2.imdecode(np.frombuffer(к.download(в["filename"], в.get("subfolder", ""), в.get("type", "output")), np.uint8), cv2.IMREAD_GRAYSCALE)
        except Exception as e: м = None; збої[type(e).__name__] = збої.get(type(e).__name__, 0) + 1
        вид = "ціла_річ" if кадр.get("плитки", {}).get(str(кадр.get("обрано"))) == "ціла_річ" else "на_моделі"
        лік[вид][0] += bool(сама_річ(шлях, м, арр, з.get("слова_крамниці") or [])); лік[вид][1] += 1
    print("(2) %-9s %d кадрів · сама річ %d/%d · ціла_річ %d/%d · на_моделі %d/%d · %.2f с/кадр%s" % (метод, len(фото), sum(в[0] for в in лік.values()), sum(в[1] for в in лік.values()), *лік["ціла_річ"], *лік["на_моделі"], (time.time() - т0) / max(1, len(фото)), " · збої %s" % збої if збої else ""))
