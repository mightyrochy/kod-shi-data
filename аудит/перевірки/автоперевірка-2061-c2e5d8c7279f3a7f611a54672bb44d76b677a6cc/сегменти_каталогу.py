"""Звірити кожен сегмент справжнього каталогу після штатного перетворення до суду."""
import json
from pathlib import Path
import sys


def головна():
    """Порахувати втрати вимірів, підміну типів та найбільшу похибку Lab."""
    sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "джерела"))
    import колір_річ as К
    import композитор_річ as П
    import outfit as О
    import colorspace as С
    тека = Path(__file__).resolve().parent
    каталог = json.loads((тека / "ПІСЛЯ-каталог.json").read_text(encoding="utf-8"))["каталог"]
    вимірів, сегментів, максимум, вади = 0, 0, 0.0, []
    for р in каталог:
        if not р.get("colors"):
            continue
        елементи = О.елементи([П.у_річ(р, р["слот"], {})], стан="надворі")
        if len(елементи) != len(р["colors"]):
            вади.append(dict(id=р["id"], причина="втрата сегмента"))
        for колір, е in zip(р["colors"], елементи):
            сегментів += 1
            т, о = К.точка_кольору(колір), К.точка_кольору(е)
            if т is not None:
                вимірів += 1
                if о is None:
                    вади.append(dict(id=р["id"], причина="втрата виміру"))
                else:
                    максимум = max(максимум, С.de00(т, о))
            if К.тип_кольору(колір) != К.тип_кольору(е) or К.межі_кольору(колір) != К.межі_кольору(е):
                вади.append(dict(id=р["id"], причина="зміна типу чи меж"))
    результат = dict(сегментів=сегментів, виміряних=вимірів, найбільша_ΔE00=максимум, вади=вади)
    текст = json.dumps(результат, ensure_ascii=False, indent=2)
    (тека / "сегменти-каталогу.json").write_text(текст, encoding="utf-8")
    print(текст)
    assert вимірів and not вади and максимум < 1


if __name__ == "__main__":
    головна()
