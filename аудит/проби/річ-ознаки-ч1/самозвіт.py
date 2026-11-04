"""Її вибір металу лишається доступним при утриманій оцінці портрета."""
import json
from pathlib import Path
import sys

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent
sys.path.insert(0, str(К / "джерела"))
import міст_вхід as М
import palettes as П


def main():
    """Друкує число перевірених відповідей та звірку фізичних вікон L/C."""
    база = json.loads((К / "джерела/стенд_вх.json").read_text("utf8"))
    число = 0
    for шлях in (К / "аудит/проби/жінки").glob("*.json"):
        ж = json.loads(шлях.read_text("utf8"))
        F = М.features(dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source="model_hex"))[0]
        for метал, очікуваний in (("золото", "золото"), ("срібло", "срібло"), ("не знаю", None)):
            палітра = П._палітра_практична(F, самозвіт={"метал": метал})
            assert палітра["метал"] == очікуваний, (шлях.name, метал, палітра["метал"])
            число += 1
    до, після = [json.loads((Д / f"читачі-{м}.json").read_text("utf8")) for м in ("до", "після")]
    фізичних = 0
    for а, б in zip(до["результати"], після["результати"]):
        if а["джерело"] == "model_hex":
            continue
        assert а["осі"] == б["осі"]
        assert all(а["вікна"][k] == б["вікна"][k] for k in ("L", "C"))
        фізичних += 1
    print(f"самозвіт: {число}; фізичних профілів × джерел: {фізичних}; порушень: 0")


if __name__ == "__main__":
    main()
