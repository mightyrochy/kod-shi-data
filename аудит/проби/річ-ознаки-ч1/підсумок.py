"""Зводить первинні журнали без підміни відхилених відповідей успішними образами."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from запуск_мірила import лічба

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent


def прочитати(шлях):
    """Читає JSONL-знімок записаних викликів мосту."""
    return [json.loads(р) for р in gzip.decompress(шлях.read_bytes()).decode("utf8").splitlines()][1:]


def помилки(рядки):
    """Розділяє винятки відтворення й повернені мостом відмови."""
    вих = {}
    for р in рядки:
        в = р.get("результат")
        if "помилка" in р:
            вих[р["н"]] = dict(вид="виняток", текст=р["помилка"])
        elif isinstance(в, dict) and в.get("помилка"):
            вих[р["н"]] = dict(вид="відмова", текст=в["помилка"])
        elif isinstance(в, dict) and в.get("відповідь_помилки"):
            вих[р["н"]] = dict(вид="відповідь не прийнято", текст=в["відповідь_помилки"])
    return вих


def main():
    """Друкує факти мірила, власних повторів і відбитки продуктового коду."""
    вих = dict(база="b694ac2d2469b4191978e4e716ac2a912715dd58",
               код=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=К, text=True).strip(),
               прилад_до=лічба(Д / "до.txt"))
    if (Д / "після.txt").stat().st_size:
        вих["прилад_після"] = лічба(Д / "після.txt")
    читачі = [json.loads((Д / f"читачі-{м}.json").read_text("utf8")) for м in ("до", "після")]
    вих["читачі"] = dict(профілів=читачі[1]["профілів"], випадків=читачі[1]["випадків"],
                          до=читачі[0]["порушень"], після=читачі[1]["порушень"])
    вих["повтор"] = []
    for сцена in ("палітра_її", "плитка_робота"):
        а, б = [прочитати(Д / f"{сцена}-{м}.jsonl.gz") for м in ("до", "після")]
        до, після = помилки(а), помилки(б)
        вих["повтор"].append(dict(сцена=сцена, викликів_до=len(а), викликів_після=len(б),
                                 відмов_до=len(до), відмов_після=len(після),
                                 нові_відмови={k: v for k, v in після.items() if k not in до}))
    свої = ("palettes.py", "profile.py", "колір_простір_надійність.py", "палітра_запити.py", "палітра_розвилка.py", "суд_від_моделі.py")
    вих["sha256"] = {ім: hashlib.sha256((К / "джерела" / ім).read_bytes()).hexdigest() for ім in свої}
    (Д / "підсумок.json").write_text(json.dumps(вих, ensure_ascii=False, indent=2), "utf8")
    print(json.dumps({k: v for k, v in вих.items() if k != "sha256"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
