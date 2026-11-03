"""Витягає факти з готових записів; моделей не викликає й оцінок образам не ставить."""
import json
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent


def особи(значення, шлях="$"):
    if isinstance(значення, dict):
        for ключ, вміст in значення.items():
            де = шлях + "." + ключ
            if ключ == "person":
                yield {"шлях": де, "значення": вміст}
            else:
                yield from особи(вміст, де)
    elif isinstance(значення, list):
        for і, вміст in enumerate(значення):
            yield from особи(вміст, шлях + "[" + str(і) + "]")


вихід = []
for сцена in ("б1_концерт_стримано", "ж4_робота", "ж1_свято_тріада", "ж2_побачення_вечір"):
    тека = ТЕКА / сцена
    if not (тека / "результат.json").exists():
        continue
    результат = json.loads((тека / "результат.json").read_text(encoding="utf-8"))
    лог = (тека / "лог.txt").read_text(encoding="utf-8")
    доказ = json.loads((тека / "знімки/доказ.json").read_text(encoding="utf-8"))
    запис = {"сцена": сцена, "rc": результат["rc"], "секунд": результат["секунд"],
             "sha": результат["sha"], "факт": доказ["факт"], "доведення_запису": доказ["вердикт"],
             "червоні": [р.strip() for р in лог.splitlines() if р.strip().startswith("✗")],
             "палітра": [р.strip() for р in лог.splitlines() if "П-7 вибір" in р or "чипів основи:" in р],
             "person": [], "обмінів": 0, "транспортні_статуси": []}
    for файл in sorted((тека / "VIDPOVIDI/обмін").glob("*.json")):
        обмін = json.loads(файл.read_text(encoding="utf-8"))
        запис["обмінів"] += 1
        запис["транспортні_статуси"].append(обмін["відповідь"].get("status"))
        for повідомлення in обмін["запит"].get("messages", []):
            вміст = повідомлення.get("content", [])
            блоки = вміст if isinstance(вміст, list) else [{"text": вміст}]
            for блок in блоки:
                текст = блок.get("text", "")
                try:
                    дані = json.loads(текст)
                except (ValueError, TypeError):
                    continue
                знайдені = list(особи(дані))
                if знайдені:
                    запис["person"].append({"файл": str(файл.relative_to(ТЕКА)),
                        "названо_виміром_коду": "her colouring as the code measured it" in текст,
                        "особи": знайдені})
    вихід.append(запис)

(ТЕКА / "огляд-записів.json").write_text(json.dumps(вихід, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for запис in вихід:
    print(запис["сцена"], "rc=", запис["rc"], "червоних=", len(запис["червоні"]),
          "обмінів=", запис["обмінів"], "person=", len(запис["person"]))
