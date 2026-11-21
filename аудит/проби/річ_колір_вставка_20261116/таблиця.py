"""Готує таблицю прямих відповідей на точно відтвореному історичному контролі."""
import hashlib
import json
from pathlib import Path
import shutil


def main():
    """Звіряє SHA JPEG, копіює контрольні кадри й друкує 6 + 14 рядків без оцінки приймання."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    контроль = json.loads((тека / "контроль.json").read_text(encoding="utf-8"))
    відповіді = json.loads((тека / "відповіді.json").read_text(encoding="utf-8"))
    групи = [("Шість хроматичних вставок c68cfea3", контроль["хроматичні"]),
             ("Прикраси 14 точок вікна золота c68cfea3", [т["id"] for т in контроль["точки_золота"]])]
    рядки, підсумок = [], {}
    for назва, іди in групи:
        рядки += ["## " + назва, "", "| id | фото моделі · оригінал | відповідь моделі в полі `вставка` |", "|---|---|---|"]
        for ід in іди:
            з = відповіді[ід]
            фото = корінь.parent / "tmp/вставки_кадри" / (ід + ".jpg")
            assert hashlib.sha256(фото.read_bytes()).hexdigest() == з["sha256_jpeg"]
            shutil.copyfile(фото, тека / "фото" / фото.name)
            поле = json.dumps(з["вставка"], ensure_ascii=False, separators=(",", ":"))
            рядки.append(f"| {ід} | [JPEG](фото/{фото.name}) · [оригінал]({з['фото']}) | `{поле}` |")
        рядки += [""]
        підсумок[назва] = {"рядків": len(іди), "вставка": sum(відповіді[і]["вставка"] is not None for і in іди),
                          "null": sum(відповіді[і]["вставка"] is None for і in іди)}
    (тека / "таблиця.md").write_text("\n".join(рядки), encoding="utf-8")
    (тека / "контроль_підсумок.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(підсумок, ensure_ascii=False))


if __name__ == "__main__":
    main()
