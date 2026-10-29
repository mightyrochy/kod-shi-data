"""Завантажити справжні фото кількох записів мірила для огляду очима."""
import json
from pathlib import Path
import urllib.request


def головна():
    """Записати URL, результат завантаження й локальний файл без підміни фото."""
    тека = Path(__file__).resolve().parent
    речі = json.loads((тека / "ПІСЛЯ-каталог.json").read_text(encoding="utf-8"))["каталог"]
    індекс = {р["id"]: р for р in речі}
    фото = тека / "фото"
    фото.mkdir(exist_ok=True)
    ід = ["ж-07553@brenda.ua", "ж-00378@vilni.store"]
    ід += [р["id"] for р in речі if р.get("колір_тип") == "інтервал"
           and р.get("слот") == "намисто" and р.get("метал") == "золото"][:1]
    ід += [р["id"] for р in речі if р.get("колір_тип") == "інтервал"
           and р.get("слот") == "верх" and р.get("колір_не_вимір", {}).get("слово") == "червоний"][:1]
    результати = []
    for і in dict.fromkeys(ід):
        адреса = next(iter(індекс[і].get("фото") or []), None)
        файл = фото / (і.replace("@", "_") + ".jpg")
        запис = dict(id=і, адреса=адреса, файл=файл.name)
        try:
            with urllib.request.urlopen(адреса, timeout=20) as відповідь:
                файл.write_bytes(відповідь.read())
            запис["байтів"] = файл.stat().st_size
        except (OSError, ValueError) as помилка:
            запис["помилка"] = str(помилка)
        результати.append(запис)
    (тека / "фото.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(результати, ensure_ascii=False))


if __name__ == "__main__":
    головна()
