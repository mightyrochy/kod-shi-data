# -*- coding: utf-8 -*-
"""ПРОБА: скільки пам'яті GPU бере вимір маски речі (ATR → SAM 3.1) і чи вміщується він
ПОРУЧ із мовною моделлю в LM Studio — від цього залежить, чи підуть розбір каталогу і
вимір кольору на одній карті водночас (наряд Н-6, 27.09.2026).
ДРУКУЄ: базу, пік і приріст пам'яті карти в МіБ, джерело маски й час на кадр.
ЗАПУСК (тека `джерела`): python проби/gpu_vymir_maska.py [кадрів]"""
import glob, os, subprocess, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from жнива_маски import маска_речі


def смі():
    """Зайнята пам'ять карти в МіБ — з драйвера, а не з /system_stats ComfyUI.

    ЧОМУ НЕ ComfyUI: доки в його процесі не піднято CUDA (`torch_vram_total` близько 0),
    він показує майже всю карту вільною — виміряно 27.09 двічі: 14.55 ГБ «вільних» при
    13972 МіБ зайнятих і 14.64 ГБ «вільних» при 10831 МіБ зайнятих. Коли SAM уже
    завантажено, його число сходиться з драйвером (0.37 ГБ вільних при 15924 МіБ).
    """
    в = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True).stdout.strip().splitlines()
    return int(в[0])


база = смі()
пік, стоп = [база], threading.Event()
сторож = threading.Thread(target=lambda: [пік.append(max(пік[-1], смі())) or time.sleep(0.2)
                                          for _ in iter(lambda: not стоп.is_set(), False)], daemon=True)
сторож.start()
кеш = os.path.join(os.environ.get("TEMP", "."), "zhnyva_v2_cache")
кадри = sorted(glob.glob(os.path.join(кеш, "kadry-*.jpg")))[:int(sys.argv[1] if len(sys.argv) > 1 else 3)]
print("база %d МіБ, кадрів %d" % (база, len(кадри)))
for слот in ("upper", "сережки"):          # upper — шлях ATR (CPU), сережки — шлях SAM (ComfyUI, GPU)
    for ш in кадри:
        т0 = time.time()
        try:
            м, частка, чому, дж = маска_речі(ш, слот)
            print("%-9s %-26s джерело %s, частка %.3f, %.1f с, GPU %d МіБ" % (
                слот, os.path.basename(ш)[:26], дж, частка, time.time() - т0, смі()))
        except Exception as e:
            print("%-9s %-26s ПОМИЛКА %s: %s" % (слот, os.path.basename(ш)[:26], type(e).__name__, str(e)[:90]))
стоп.set(); сторож.join(1)
print("GPU: база %d МіБ, пік %d МіБ, приріст виміру %d МіБ (карта 16376 МіБ)" % (база, max(пік), max(пік) - база))
