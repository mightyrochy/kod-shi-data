# -*- coding: utf-8 -*-
"""Рядок 153: локальні моделі для Люстерка — кандидати ДАНИМИ (з позначкою «поточна» — точка відліку) і чи кожен
зараз піднятий. Ідентифікатор = що ставити: `lms get <ід>`, вага ComfyUI (models/…), файл. Питає LM Studio :1234
(`/api/v1/models`: скачано / піднято / чи думає типово; старий LM Studio — `/v1/models`), ComfyUI :8000 і :8188
(`/object_info`: вузол є і вага в списку завантажувача) і диск (ATR, LEFFA_PATH). У хмарі друкує «не піднято»."""
import json, os, urllib.request
КАНДИДАТИ = {
 "1 жнива v2: плитка, ознаки, колір": [["qwen/qwen3-vl-8b", "lms", "поточна"], ["qwen/qwen3.5-9b", "lms"], ["google/gemma-4-12b", "lms"], ["qwen/qwen3.6-35b-a3b", "lms"]],
 "2 маска речі": [["ckpts/humanparsing/parsing_atr.onnx", "файл", "поточна"], ["sam_vit_h", "comfy:GroundingDinoSAMSegment (segment anything)",
                  "поточна"], ["sam3.1_multiplex_fp16", "comfy:SAM3_Detect"], ["birefnet", "comfy:RemoveBackground"]],
 "3 паспорт з тексту": [["qwen/qwen3-vl-8b", "lms", "поточна"], ["INSAIT-Institute/MamayLM-Gemma-3-12B-IT-v2.0-GGUF", "lms"], ["google/gemma-4-26b-a4b", "lms"], ["qwen/qwen3.8-27b", "lms"]],
 "4 приміряння": [["qwen_image_edit_2511_fp8mixed", "comfy:TextEncodeQwenImageEditPlus", "поточна"], ["Qwen-Image-Edit-2511-Lightning-4steps",
                  "comfy:LoraLoaderModelOnly"], ["qwen_image_2.1_int8_convrot", "comfy:TextEncodeQwenImage21"], ["tryon-klein-4b", "comfy:LoraLoaderModelOnly"]],
 "5 фото речі: рід, рамка": [["qwen/qwen3-vl-8b", "lms", "поточна"], ["qwen/qwen3.5-9b", "lms"], ["qwen/qwen3.6-35b-a3b", "lms"], ["google/gemma-4-12b", "lms"]]}
ЧОМУ_НІ = {}
def взяти(url):
    """JSON з локального сервера; не відповідає — None, а причина в ЧОМУ_НІ (друкується вгорі). Таймаут 90 с, а не 10: `/object_info` з усіма вузлами — 1223 записи, і за 10 с на зайнятому ноутбуці проба писала «не піднято» на ваги, які є."""
    try:
        with urllib.request.urlopen(url, timeout=90) as в: return json.load(в)
    except Exception as e: ЧОМУ_НІ[url.split("/", 3)[2]] = type(e).__name__
лмс = (взяти("http://127.0.0.1:1234/api/v1/models") or {}).get("models") or [
    dict(key=м["id"], старий=1) for м in (взяти("http://127.0.0.1:1234/v1/models") or {}).get("data", [])]
комфі = {п: взяти("http://127.0.0.1:%d/object_info" % п) for п in (8000, 8188)}
print("LM Studio :1234 — %s · ComfyUI — %s%s" % ("моделей %d" % len(лмс) if лмс else "не відповідає", ", ".join(":%d %s" % (п, "вузлів %d" % len(і)
      if і else "не відповідає") for п, і in комфі.items()), " · причини: " + ", ".join("%s %s" % кв for кв in ЧОМУ_НІ.items()) if ЧОМУ_НІ else ""))
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
            вузол = де.split(":", 1)[1]
            де_є = [":%d" % п for п, і in комфі.items() if і and вузол in і and ід.lower() in json.dumps(і, ensure_ascii=False).lower()]
            стан = "ПІДНЯТО на " + ", ".join(де_є) if де_є else "вузол є, ваги нема" if any(і and вузол in і for і in комфі.values()) else \
                "вузла нема" if any(комфі.values()) else "не піднято"
        print("%-34s %-50s %-6s %s%s" % (задача if н == 0 else "", ід, де.split(":")[0], стан, " — поточна" if поточна else ""))
