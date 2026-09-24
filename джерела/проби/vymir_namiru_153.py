# -*- coding: utf-8 -*-
"""Рядок 153 (3): обгортка над `namir_zhyva_88.py` — та сама батарея (12 текстів наміру + 4 K-IO-02), той самий промпт і розбір
паспорта, лише ІНША МОДЕЛЬ LM Studio; друкує с/текст і VRAM. Сам файл рядка 88 не міняється: обгортка виконує його текст, у якому
назва моделі підмінена, і падає, якщо назви там уже нема. `--сам`: замість LM Studio відповідає очікування самого тексту
(мусить вийти «намір: 12/12 · K-IO-02 … 4/4» — перевірка підрахунку обгортки). `--t0` передається далі.
`cd джерела && python проби/vymir_namiru_153.py <модель>`"""
import io, json, os, subprocess, sys, time, urllib.request
ШЛЯХ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "namir_zhyva_88.py")
мод, сам = next((a for a in sys.argv[1:] if not a.startswith("--")), "qwen3-vl-8b-instruct"), "--сам" in sys.argv
текст = open(ШЛЯХ, encoding="utf-8").read()
if текст.count('"qwen3-vl-8b-instruct"') != 1: sys.exit("у namir_zhyva_88.py назва моделі вже інша — обгортка не знає, що підміняти")
простір = {"__name__": "__main__", "__file__": ШЛЯХ}
def відповідь_очікуванням(запит, timeout=None):
    """Підміна `urlopen` для `--сам`: відповідь у форматі LM Studio, де JSON паспорта — рівно очікування тексту з ТЕКСТИ рядка 88."""
    оч = next(о for с, о in простір["ТЕКСТИ"] if с in json.loads(запит.data)["messages"][0]["content"])
    від = {"намір": оч} if isinstance(оч, str) else {"мета": оч[0], "макіяж": оч[1] and {"рівень": оч[1]}, "прикраси": оч[2]}
    return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(від, ensure_ascii=False)}}]}).encode("utf-8"))
if сам: urllib.request.urlopen = відповідь_очікуванням
else:
    try: urllib.request.urlopen("http://127.0.0.1:1234/v1/models", timeout=10)
    except Exception as e: sys.exit("LM Studio не відповідає (%s) — модель «%s» не виміряти" % (type(e).__name__, мод))
т0 = time.time()
exec(compile(текст.replace('"qwen3-vl-8b-instruct"', json.dumps(мод)), ШЛЯХ, "exec"), простір)
try: vram = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=20).stdout.strip()
except Exception as e: vram = "nvidia-smi: " + type(e).__name__
print("(3) модель %s%s · %.1f с/текст (%d текстів) · VRAM %s" % (мод, " --сам (очікування замість моделі)" if сам else "",
      (time.time() - т0) / len(простір["ТЕКСТИ"]), len(простір["ТЕКСТИ"]), vram))
sys.exit(1 if сам and (простір["влучень"], простір["чисто"]) != (12, 4) else 0)
