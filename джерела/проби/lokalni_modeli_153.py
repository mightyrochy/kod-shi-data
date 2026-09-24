# -*- coding: utf-8 -*-
"""Рядок 153: локальні моделі для Люстерка — кандидати ДАНИМИ (з позначкою «поточна» — точка відліку) і чи кожен
зараз піднятий. Ідентифікатор = що ставити: `lms get <ід>`, вага ComfyUI (models/…), файл. Питає LM Studio :1234
(`/api/v1/models`: скачано / піднято / чи думає типово; старий LM Studio — `/v1/models`), ComfyUI :8000 і :8188 (вузол є і вага в списку завантажувача) і диск (ATR, LEFFA_PATH). У хмарі друкує «не піднято»."""
import json, os, urllib.parse, urllib.request
КАНДИДАТИ = {
 "1 жнива v2: плитка, ознаки, колір": [["qwen/qwen3-vl-8b", "lms", "поточна"], ["qwen/qwen3.5-9b", "lms"], ["google/gemma-4-12b", "lms"], ["qwen/qwen3.6-35b-a3b", "lms"]],
 "2 маска речі": [["ckpts/humanparsing/parsing_atr.onnx", "файл", "поточна"], ["sam_vit_h", "comfy:GroundingDinoSAMSegment (segment anything)"], ["sam3.1_multiplex_fp16", "comfy:SAM3_Detect", "поточна"], ["birefnet", "comfy:RemoveBackground"]],
 "3 паспорт з тексту": [["qwen/qwen3-vl-8b", "lms", "поточна"], ["INSAIT-Institute/MamayLM-Gemma-3-12B-IT-v2.0-GGUF", "lms"], ["google/gemma-4-26b-a4b", "lms"], ["qwen/qwen3.8-27b", "lms"]],
 "4 приміряння": [["qwen_image_edit_2511_fp8mixed", "comfy:TextEncodeQwenImageEditPlus", "поточна"], ["Qwen-Image-Edit-2511-Lightning-4steps", "comfy:LoraLoaderModelOnly", "поточна"], ["qwen_image_2.1_int8_convrot", "comfy:TextEncodeQwenImage21"], ["tryon-klein-4b", "comfy:LoraLoaderModelOnly"]],
 "5 фото речі: рід, рамка": [["qwen/qwen3-vl-8b", "lms", "поточна"], ["qwen/qwen3.5-9b", "lms"], ["qwen/qwen3.6-35b-a3b", "lms"], ["google/gemma-4-12b", "lms"]]}
ЗАВАНТАЖУВАЧІ = ("CheckpointLoaderSimple", "UNETLoader", "LoraLoaderModelOnly", "VAELoader", "CLIPLoader", "SAMModelLoader (segment anything)", "GroundingDinoModelLoader (segment anything)", "LoadBackgroundRemovalModel")
ЧОМУ_НІ, _кеш = {}, {}
def взяти(url):
    """JSON з локального сервера; не відповідає — None, а причина в ЧОМУ_НІ (друкується вгорі). Таймаут 90 с: ноутбук буває зайнятий."""
    try:
        with urllib.request.urlopen(url, timeout=90) as в: return json.load(в)
    except Exception as e: ЧОМУ_НІ[url.split("/", 3)[2] + "/" + url.split("/", 4)[3][:11]] = type(e).__name__
def схема(порт, вузол):
    """Схема ОДНОГО вузла. Цілий `/object_info` на :8000 не читається: 3.5 МБ, і urllib щоразу рве на 3 473 408 байтах (ConnectionResetError за 20.7 с), тоді як curl ті самі 3 553 042 бере за 1.8 с — тобто це не сервер. Поштучно — 0.01 с."""
    return _кеш.setdefault((порт, вузол), (взяти("http://127.0.0.1:%d/object_info/%s" % (порт, urllib.parse.quote(вузол))) or {}).get(вузол))
лмс = (взяти("http://127.0.0.1:1234/api/v1/models") or {}).get("models") or [dict(key=м["id"], старий=1) for м in (взяти("http://127.0.0.1:1234/v1/models") or {}).get("data", [])]
комфі = {п: (взяти("http://127.0.0.1:%d/system_stats" % п) or {}).get("system") for п in (8000, 8188)}
print("LM Studio :1234 — %s · ComfyUI — %s%s" % ("моделей %d" % len(лмс) if лмс else "не відповідає", ", ".join(":%d %s" % (п, с["comfyui_version"] if с else "не відповідає") for п, с in комфі.items()), " · причини: " + ", ".join("%s %s" % кв for кв in ЧОМУ_НІ.items()) if ЧОМУ_НІ else ""))
for задача, список in КАНДИДАТИ.items():
    for н, (ід, де, *поточна) in enumerate(список):
        if де == "lms":
            хвіст = ід.split("/")[-1].lower().replace("-gguf", "")
            м = next((м for м in лмс if хвіст in (м["key"] + " ".join(і["id"] for і in м.get("loaded_instances", []))).lower()), None)
            стан = ("не скачано" if лмс else "не піднято") if not м else "є у /v1/models" if м.get("старий") else "скачано, не піднято" if not м["loaded_instances"] \
                else "ПІДНЯТО %s%s" % ((м.get("quantization") or {}).get("name"), ", ДУМАЄ типово — вимкнути" if ((м.get("capabilities") or {}).get("reasoning") or {}).get("default") == "on" else "")
        elif де == "файл":
            стан = "файл є" if os.path.exists(os.path.join(os.environ.get("LEFFA_PATH", r"C:/Users/Admin/Leffa"), ід)) else "не піднято (файла нема)"
        else:
            # Ім'я ваги живе у випадайці ЗАВАНТАЖУВАЧА, а не у вузлі, що її вживає: `sam3.1…` — у CheckpointLoaderSimple, не в SAM3_Detect.
            схеми = {п: схема(п, де.split(":", 1)[1]) for п, с in комфі.items() if с}
            ваги = {п: json.dumps([схема(п, з) for з in ЗАВАНТАЖУВАЧІ], ensure_ascii=False).lower() for п in схеми}
            де_є = [":%d" % п for п, сх in схеми.items() if сх and ід.lower() in ваги[п]]
            стан = "ПІДНЯТО на " + ", ".join(де_є) if де_є else "вузол є, ваги нема" if any(схеми.values()) else "вузла нема" if any(комфі.values()) else "не піднято"
        print("%-34s %-50s %-6s %s%s" % (задача if н == 0 else "", ід, де.split(":")[0], стан, " — поточна" if поточна else ""))
