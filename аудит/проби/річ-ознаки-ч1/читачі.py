"""Повтор читачів на записаних профілях без звернення до моделей."""
import json
import os
import pathlib
import sys

К = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(К / "джерела"))
if os.environ.get("Ч1_КОД_ДО"):
    sys.path.insert(0, os.environ["Ч1_КОД_ДО"])
import міст_вхід as М
import palettes as П
import profile as Р
import palette as С
import colorspace as Ц
import face_features as О


def main():
    """Друкує факти утримання та контрольний зріз фізичного вводу."""
    база = json.loads((К / "джерела/стенд_вх.json").read_text("utf8"))
    профілі = sorted((К / "аудит/проби/жінки").glob("*.json"))
    assert len(профілі) == 9, len(профілі)
    результати, помилки = [], []
    for шлях in профілі:
        ж = json.loads(шлях.read_text("utf8"))
        вхід = dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"])
        for дж in ("model_hex", "spectro", "protocolized", "uncontrolled"):
            F = М.features(dict(вхід, source=дж))[0]
            осі = П.осі(F, "protocolized")
            палітра = П._палітра_практична(F, source="protocolized")
            тон = С.тон_від_рис(F, "аналогова", "protocolized")
            аудит = Р.аудит(F, "protocolized")
            гейт = Ц.gate_conclusions(дж)
            запис = dict(профіль=шлях.stem, джерело=дж, осі=осі,
                         вікна=палітра["вікна"], метал=палітра["метал"],
                         тон=тон, аудит=аудит, гейт=гейт)
            результати.append(запис)
            if дж != "model_hex":
                continue
            факти = {
                "вісь світлоти": осі["коди"]["value"] == "withheld",
                "вісь хроми": осі["коди"]["chroma"] == "withheld",
                "домінанта": осі["домінанта"] is None,
                "дріт осей": all(v is None for v in П.для_пакета(палітра)["axes"]["positions"].values()),
                "метал": палітра["метал"] is None,
                "колір очей": палітра["вікна"]["очі"] is None,
                "тон": not тон["придатно"] and not тон["риси"] and not тон["перегуки"],
                "невизначеність": аудит["σ_профілю"] is None,
                "аудит": all(р["джерело"] == "оцінка моделі" and р["σ"] is None for р in аудит["риси"]),
                "пояснення": all("регіональний шум по обличчю перевищує" not in п for п in гейт["примітки"]),
            }
            помилки.extend(f"{шлях.stem}: {к}" for к, добре in факти.items() if not добре)
    print(json.dumps(dict(профілів=len(профілі), випадків=len(результати),
                         порушень=len(помилки), помилки=помилки, результати=результати),
                     ensure_ascii=False, indent=2))
    return bool(помилки) if "--вимагати" in sys.argv else 0


if __name__ == "__main__":
    sys.exit(main())
