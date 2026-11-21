"""Знімає весь обсяг прикрас і їхнє старе збагачення до переопису."""
import gzip
import json
from pathlib import Path
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import feed as Ф
import жнива_промпти as П


def main():
    """Зберігає всі ювелірні слоти без вибірки й обмеження за наявністю збагачення."""
    офери, _ = Ф.читати_yml(Ф.каталог_на_диску("каталог_повний.xml"))
    прикраси = [о for о in офери if П.набір_слота(Ф.слоти(о).get("слот")) == "прикраса"]
    with gzip.open(КОРІНЬ / "джерела/каталог_збагачення.json.gz", "rt", encoding="utf-8") as ф:
        зб = json.load(ф)
    дані = {"каталог": len(офери), "прикраси": прикраси,
            "збагачення": {о["id"]: зб.get(о["id"]) for о in прикраси}}
    (ТЕКА / "прикраси_до.json").write_text(json.dumps(дані, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Записів:", len(офери), "прикрас:", len(прикраси))


if __name__ == "__main__":
    main()
