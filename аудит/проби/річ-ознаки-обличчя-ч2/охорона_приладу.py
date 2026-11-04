"""Друкує, чи незмінений аналізатор розрізняє утримання за довірою й безумовний поріг."""
import json
from pathlib import Path
import sys
import tempfile

К = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(К / "джерела/прилади"))
from ознаки_аналіз import Аналіз


def main():
    """Порівнює виконання і лічбу на двох формах одного порога, не змінюючи прилад."""
    підсумок = []
    for охорона in (False, True):
        код = ('def клас(F):\n' + ('    if F["довіра"] == 0.0:\n        return None\n' if охорона else '')
               + '    return "низька" if F["L"] < 30 else "висока"\n')
        with tempfile.TemporaryDirectory(prefix="охорона-ч2-") as т:
            д = Path(т) / "джерела"
            д.mkdir()
            (д / "риси.py").write_text(код, encoding="utf8")
            а = Аналіз(т)
            а.виклик(а.модулі["риси"].функції["клас"], [frozenset({"S"})], {})
            простір = {}
            exec(код, простір)
            підсумок.append(dict(охорона=охорона, місць=len(а.місця),
                виконання=[простір["клас"]({"довіра": 0.0, "L": L}) for L in (10, 90)],
                місця=[dict(файл=ф, рядок=н, причини=sorted(п)) for (ф, н), п in а.місця.items()]))
    print(json.dumps(підсумок, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
