"""Повторює записані виклики мосту на базі або на робочому коді без запитів до моделей."""
import asyncio
import gzip
import importlib.abc
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent
МОДУЛІ = {"personal_palette", "аксесуари_взуття", "колір_відношення",
          "колір_простір_риси", "колір_світлота", "палітра_специфікація"}


class База(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Читає змінені модулі з Git, залишаючи дані й решту коду того самого дерева."""

    def find_spec(self, fullname, path, target=None):
        """Обирає лише шість змінених модулів продукту."""
        if fullname in МОДУЛІ:
            return importlib.util.spec_from_loader(fullname, self)

    def create_module(self, spec):
        """Делегує стандартне створення модуля Python."""
        return None

    def exec_module(self, module):
        """Виконує незмінений код базового коміту без перемикання робочого дерева."""
        шлях = К / "джерела" / (module.__name__ + ".py")
        код = subprocess.check_output(["git", "show", "6377cbcf1adc6d443bbbb830ee1af8bf7b07a5d5:джерела/" + шлях.name], cwd=К)
        module.__file__ = str(шлях)
        exec(compile(код, str(шлях), "exec"), module.__dict__)


def main():
    """Зберігає повний знімок та окремо рахує винятки й відхилені відповіді."""
    мітка = sys.argv[1]
    if мітка == "до":
        sys.meta_path.insert(0, База())
    sys.path.insert(0, str(К / "джерела/прилади"))
    import знімок_мосту as З
    З.підготувати(str(К / "джерела"))
    import feed
    feed.каталог_на_диску("каталог_brief.xml")
    feed.каталог_на_диску("каталог_повний.xml")
    кеш = Path(tempfile.gettempdir()) / ("повтор_ч2_кеш-" + мітка + ".json")
    кеш.write_text("{}", encoding="utf8")
    підсумок = []
    for сцена in ("палітра_її", "плитка_робота"):
        рядки = [json.loads(р) for р in З.прочитати(str(К / "аудит/проби/знімок_входи" / (сцена + ".jsonl.gz"))).splitlines() if р.strip()]
        for рядок in рядки:
            вхід = json.loads(рядок["вхід"])
            if "кеш_кольорів" in вхід:
                вхід["кеш_кольорів"] = str(кеш)
            рядок["вхід"] = json.dumps(вхід, ensure_ascii=False)
        знімок, час = asyncio.run(З.прогнати("\n".join(json.dumps(р, ensure_ascii=False) for р in рядки)))
        записи = [json.loads(р) for р in знімок.splitlines()][1:]
        (Д / (сцена + "-" + мітка + ".jsonl.gz")).write_bytes(gzip.compress(знімок.encode("utf8"), mtime=0))
        помилки = [dict(н=з["н"], ім=з["ім"], помилка=з["помилка"]) for з in записи if "помилка" in з]
        підсумок.append(dict(сцена=сцена, викликів=len(записи), помилки=помилки, час=час))
        print(сцена, "викликів", len(записи), "винятків", len(помилки), flush=True)
    (Д / ("сцени-" + мітка + ".json")).write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding="utf8")
    return any(с["помилки"] for с in підсумок)


if __name__ == "__main__":
    sys.exit(main())
