"""Незалежна проба PR 4031: записані коментарі, сусідні форми й повний каталог.

Вжиток: python межі.py <тека дерева> <вихід.json> [--каталог].
"""
import contextlib
import gzip
import io
import json
from pathlib import Path
import sys

дерево = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(дерево / "джерела"))
import мовний_шар as М
import пакет_моделі as П
import дріт_моделі as Д


def паспорт(записи, досі=None):
    return М.паспорт_з_коментаря(
        {"vetoes": записи}, паспорт_досі=досі or {"вето": {}, "бажання": []}
    )["паспорт"]


рез = {"записані": {}, "форми": {}}
for номер in (2, 3):
    файли = sorted((дерево / f"аудит/проби/живий-як-людина-{номер}/стенд/службове").glob("*/обміни.jsonl.gz"))
    кількість = глобально = 0
    for файл in файли:
        for рядок in gzip.open(файл, "rt", encoding="utf8"):
            з = json.loads(рядок)
            try:
                т = json.loads(з["відповідь"])["content"][0]["text"]
            except (KeyError, IndexError, TypeError, ValueError):
                continue
            if '"vetoes"' not in т or '"about_items"' not in т:
                continue
            об = json.loads(т[т.index("{"):т.rindex("}") + 1])
            тв = паспорт(об.get("vetoes") or []).get("вето_тверде") or {}
            слова = {М._ВМ.ключ("length", р.get("length")) for р in об.get("vetoes") or []
                     if isinstance(р, dict) and р.get("slot")} - {None}
            кількість += 1
            глобально += any(w in слова and w not in (тв.get("слоти") or {}) for w in тв.get("типи") or [])
    рез["записані"][str(номер)] = {"файлів": len(файли), "коментарів": кількість, "довжина_на_весь_образ": глобально}

форми = {
    "пальто_міді": [{"slot": "outerwear", "length": "midi"}],
    "ознака_лише_взуття": [{"slot": "shoes", "feature": "heels"}],
    "принт_два_слоти": [{"slot": "dress", "feature": "large_print"}, {"slot": "top", "feature": "large_print"}],
    "міді_два_слоти": [{"slot": "outerwear", "length": "midi"}, {"slot": "dress", "length": "midi"}],
    "міді_два_слоти_навпаки": [{"slot": "dress", "length": "midi"}, {"slot": "outerwear", "length": "midi"}],
    "міді_без_слота": [{"length": "midi"}],
    "міді_слот_і_глобально": [{"slot": "outerwear", "length": "midi"}, {"length": "midi"}],
}
паспорти = {}
for назва, записи in форми.items():
    п = паспорти[назва] = паспорт(записи)
    в = П.випадок_для_пакета(п, "")
    рез["форми"][назва] = {"вето": п.get("вето_тверде"), "дріт": Д.випадок(в).get("refusals")}

п = паспорт([{"slot": "dress", "length": "midi"}], паспорти["пальто_міді"])
рез["форми"]["міді_два_ходи"] = п.get("вето_тверде")
рез["форми"]["розмова_без_міні"] = М._межі([{"length": "mini"}])

if "--каталог" in sys.argv:
    import feed as Ф
    шлях = Ф.каталог_на_диску("каталог_повний.xml", тека=str(дерево))
    with contextlib.redirect_stdout(io.StringIO()):
        каталог = Ф._прочитати_каталог(шлях, ліміт_фото=0)["каталог"]
    рез["каталог"] = {"речей": len(каталог), "форми": {}}
    for назва in ("пальто_міді", "міді_два_слоти", "міді_два_слоти_навпаки", "міді_без_слота"):
        тв = паспорти[назва]["вето_тверде"]
        групи = {}
        for р in каталог:
            if П.жорстке_відсічення(р):
                continue
            причина = П.жорстке_відсічення(р, вето=тв)
            if причина:
                сл = р.get("слот")
                г = групи.setdefault(сл, {"відсічено": 0, "приклади": []})
                г["відсічено"] += 1
                if len(г["приклади"]) < 2:
                    г["приклади"].append({к: р.get(к) for к in ("id", "назва", "фото", "ціна", "слот")})
        рез["каталог"]["форми"][назва] = групи

Path(sys.argv[2]).write_text(json.dumps(рез, ensure_ascii=False, indent=2), encoding="utf8")
print(json.dumps({"записані": рез["записані"], "форми": {к: в.get("вето", в) if isinstance(в, dict) else в for к, в in рез["форми"].items()},
                  "каталог": {"речей": рез.get("каталог", {}).get("речей"), "форми": {
                      н: {с: г["відсічено"] for с, г in групи.items()}
                      for н, групи in рез.get("каталог", {}).get("форми", {}).items()}}}, ensure_ascii=False))
