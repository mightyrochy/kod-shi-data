"""Найдовша відповідь, яку пускає граматика `КР.схема_відповіді`, у токенах MamayLM (5.4-Г), без моделі.
python3 проби/межа_відповіді_54г.py <tokenizer.json>  (huggingface.co/INSAIT-Institute/MamayLM-Gemma-3-12B-IT-v1.0)
Цитата й фрагмент — найгірший уривок тієї довжини з текстів каталогу; число — найдовше, що пускає граматика
llama.cpp (`number` — 16+16 цифр і показник); пробіли між токенами JSON (SPACE_RULE) — лише лічбою місць."""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tokenizers import Tokenizer
import каталог_розбір as КР, фід_каталог as ФК, фід_розбір as ФР
ТОК = Tokenizer.from_file(sys.argv[1])
т = lambda s: len(ТОК.encode(s, add_special_tokens=False).ids)
ЧИСЛО = "-1234567890123456.1234567890123456e-1234567890123456"
компакт = lambda x: json.dumps(x, ensure_ascii=False, separators=(",", ":")).replace("NaN", ЧИСЛО)
тексти = [json.dumps(х, ensure_ascii=False)[1:-1] for o in ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0]
          for в in [КР.вхід(o)] for х in [в.get("name"), в.get("description"), *(в.get("params") or {}).values()] if х]
кодовані = [(с, ТОК.encode(с, add_special_tokens=False).offsets) for с in тексти]
@__import__("functools").cache
def уривок(L):
    best = (0, "x" * L)
    for с, оф in кодовані:
        j = 0
        for i in range(len(оф)):
            while j < len(оф) and оф[j][1] <= оф[i][0] + L: j += 1
            if j - i > best[0]: best = (j - i, с[оф[i][0]:оф[i][0] + L])
    return best[1]
def найдовше(в):
    if "anyOf" in в or "enum" in в:
        return max(map(найдовше, в["anyOf"]) if "anyOf" in в else в["enum"], key=lambda x: т(компакт(x)))
    тип = в["type"]
    if тип == "object": return {к: найдовше(п) for к, п in в["properties"].items()}
    if тип == "array": return [найдовше(в["items"])] * в["maxItems"]
    if тип == "string": return уривок(в["maxLength"])
    return в["maximum"] if тип == "integer" else math.nan
def місць(в):
    if "anyOf" in в: return max(map(місць, в["anyOf"]))
    if в.get("type") == "object": return 2 + sum(3 + місць(п) for п in в["properties"].values())
    return 2 + в["maxItems"] * (1 + місць(в["items"])) if в.get("type") == "array" else 0
с = КР.схема_відповіді()
print("найдовша відповідь: %d токенів (%d знаків) · місць пробілу SPACE_RULE %d · стеля виходу 1 600 · цитата %d, фрагмент %d"
      % (т(компакт(найдовше(с))), len(компакт(найдовше(с))), місць(с), КР.СТЕЛЯ_ЦИТАТИ, КР.СТЕЛЯ_ФРАГМЕНТА))
