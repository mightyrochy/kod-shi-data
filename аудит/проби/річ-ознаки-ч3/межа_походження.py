"""Звіряє втрату джерела на межі файлів Ч3 без зміни продукту чи приладу."""
import json
from pathlib import Path
import subprocess
import sys

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent
sys.path.insert(0, str(К / "джерела"))
import міст_вхід as В
import face_features as О
import palette as П
import колір_річ as Р
import colorspace as С
import вибір_палітри as М
import bases as Б


def main():
    """Доводить нерозрізненність входів моделі й спектрофотометра після зняття джерела."""
    факти = []
    for шлях in sorted((К / "аудит/проби/жінки").glob("*.json")):
        ж = json.loads(шлях.read_text("utf8"))
        пари = []
        for дж in ("model_hex", "spectro"):
            F = В.features(dict(шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source=дж))[0]
            оз = О.ознаки(F)
            очі = оз["риси"]["очі"]
            lab = (очі["L"], очі["a"], очі["b"])
            голий = dict(lab=lab)
            к = оз["контраст"]
            gap = max(к["value_gap"], к["gap_рівня"])
            зсув = П.зсув_мисматчу(gap, драбина=к["value_gap"])
            розвилка = П.розвилка(к, явні=(П.МИСМАТЧ,))
            мисматч = next(г["мисматч"] for г in розвилка["гілки"] if г["схема"] == П.МИСМАТЧ)
            assert мисматч == зсув
            звʼязки = []
            for hex in (ж["eyes"], "#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff", "#777777"):
                основа = dict(hex=hex, ахром=С.lch(С.hx(hex))[1] < Б.АХРОМАТИЧНА_МЕЖА)
                звʼязок = М._до_очей(основа, F)
                if звʼязок is not None:
                    звʼязки.append(dict(hex=hex, висновок=звʼязок))
            пари.append(dict(джерело=дж, довіра=оз["надійність"],
                             позначена_риса=Р.тип_кольору(очі), голий_вхід=голий,
                             голий_тип=Р.тип_кольору(голий), gap=gap,
                             драбина=к["value_gap"], мисматч=мисматч, до_очей=звʼязки))
        м, ф = пари
        assert not any(м["довіра"].values())
        assert м["позначена_риса"] == "невідомо" and ф["позначена_риса"] == "вимір"
        assert м["голий_вхід"] == ф["голий_вхід"] and м["голий_тип"] == ф["голий_тип"] == "вимір"
        assert (м["gap"], м["драбина"]) == (ф["gap"], ф["драбина"])
        assert м["мисматч"] == ф["мисматч"] and м["мисматч"]["власний"] is not None
        факти.append(dict(профіль=шлях.stem, пара=пари))
    assert len(факти) == 9
    незмінне = subprocess.check_output([
        "git", "--work-tree=" + str(К), "diff", "--name-only",
        "0ff48e75eb9e0bf60b6831622ff155a48f061b76", "--", "джерела"
    ], cwd=К).decode("utf8").strip()
    assert not незмінне, незмінне
    вихід = dict(профілів=len(факти), однакових_голих_Lab=len(факти),
                 однакових_скалярних_входів=len(факти),
                 мисматчів_за_нульової_довіри=len(факти),
                 висновків_до_очей_за_нульової_довіри=sum(len(ф["пара"][0]["до_очей"]) for ф in факти),
                 код_тотожний_виміряному="0ff48e75eb9e0bf60b6831622ff155a48f061b76",
                 факти=факти)
    (Д / "межа-походження.json").write_text(json.dumps(вихід, ensure_ascii=False, indent=2) + "\n", "utf8")
    print(json.dumps({к: з for к, з in вихід.items() if к != "факти"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
