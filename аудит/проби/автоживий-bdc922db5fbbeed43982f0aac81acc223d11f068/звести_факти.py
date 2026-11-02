"""Витяг фактів зі збережених журналів; не запускає сцен і не оцінює образів."""
import json
from pathlib import Path
import re

Т = Path(__file__).resolve().parent
план = json.loads((Т / "план.json").read_text(encoding="utf-8"))
факти = {}
for назва in план["scenes"]:
    т = Т / назва
    р = т / "результат.json"
    if not р.exists():
        факти[назва] = {"стан": "немає результату"}
        continue
    д = json.loads(р.read_text(encoding="utf-8"))
    ф = {"rc": д["rc"], "секунд": д["секунд"], "sha": д["sha"]}
    доказ = т / "знімки/доказ.json"
    if доказ.exists():
        з = json.loads(доказ.read_text(encoding="utf-8"))
        ф.update(доказ=з.get("вердикт"), вимір=з.get("факт"))
    лог = (т / "лог.txt").read_text(encoding="utf-8")
    ф["червоні"] = [р.strip() for р in лог.splitlines() if р.startswith("  ✗")]
    ф["підсумок"] = [р for р in лог.splitlines() if р.startswith(("ВПАЛО", "НГ-4", "ЗАМІНА руки", "НЕ_ЦЯ", "стенд не піднявся:"))]
    журнал = т / "вердикти.txt"
    if журнал.exists():
        ж = json.loads(журнал.read_text(encoding="utf-8"))
        с = ж.get("спільне", {})
        ф["паспорт"] = с.get("паспорт")
        випадок = с.get("випадок_моделі")
        if isinstance(випадок, str):
            try:
                випадок = json.loads(випадок)
            except json.JSONDecodeError:
                pass
        ф["випадок_моделі"] = випадок
        ф["руки"] = []
        for прогін in ж.get("прогони", []):
            for в in прогін.get("вердикти", []):
                if str(в.get("рука")) not in ("1", "2"):
                    continue
                е = в.get("етапи") or {}
                суд = е.get("суд") or {}
                рука = {"рука": в["рука"], "склад": в.get("склад"),
                    "блокує": суд.get("блокує"), "структура": суд.get("структура"),
                    "день": суд.get("день"), "повнота": суд.get("повнота"),
                    "знахідки": [з.get("правило") for з in суд.get("знахідки", [])],
                    "слід_K_CRA_04": [з for з in суд.get("слід_правил", []) if з.get("правило") == "K-CRA-04"],
                    "знахідки_K_CRA_04": [з for з in суд.get("знахідки", []) if з.get("правило") == "K-CRA-04"],
                    "знахідки_K_OUT_06": [з for з in суд.get("знахідки", []) if з.get("правило") == "K-OUT-06"],
                    "діагноз": [з for з in е.get("діагноз_руки", []) if "code_unknown=" not in з],
                    "речі": [{к: р.get(к) for к in ("id", "слот", "назва")} for р in в.get("речі_образу", [])]}
                ф["руки"].append(рука)
    ф["заміни"] = [json.loads(ф.read_text(encoding="utf-8")) for ф in (т / "знімки").glob("заміна_руки_*.json")]
    факти[назва] = ф
(Т / "факти.json").write_text(json.dumps(факти, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for н, ф in факти.items():
    print(н, "rc=" + str(ф.get("rc", "—")), "доведено=" + str((ф.get("доказ") or {}).get("доведено", "—")), "червоних=" + str(len(ф.get("червоні", []))))
