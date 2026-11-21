"""Знімає офіційний прилад на базовому коді та правці без перемикання робочих файлів."""
from pathlib import Path
import os
import hashlib
import json
import subprocess
import sys
import tempfile

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
БАЗА = "9663cf56fd16dc3a6db7a21d9a02e090520f5f16"
ФАЙЛИ = [КОРІНЬ / "джерела" / ім for ім in ("жнива_промпти.py", "жнива_розбір.py")]


def main():
    """Міряє ДО і ПІСЛЯ послідовно, зберігаючи повний stdout і stderr."""
    sys.path.insert(0, str(КОРІНЬ / "джерела/прилади"))
    import корінь_річ_колір_межі as прилад
    база = Path(tempfile.mkdtemp(prefix="прилад_база-", dir=КОРІНЬ.parent / "tmp"))
    маніфест = {}
    # Лише код повного обсягу приладу, без каталогу, архівів аудиту й залежностей.
    for шлях, відносний, _ in прилад.файли(str(КОРІНЬ)):
        джерело = Path(шлях)
        байти = (subprocess.check_output(["git", "show", БАЗА + ":" + джерело.relative_to(КОРІНЬ).as_posix()], cwd=КОРІНЬ)
                 if джерело in ФАЙЛИ else джерело.read_bytes())
        ціль = база / відносний
        ціль.parent.mkdir(parents=True, exist_ok=True)
        ціль.write_bytes(байти)
        маніфест[джерело.relative_to(КОРІНЬ).as_posix()] = hashlib.sha256(байти).hexdigest()
    (ТЕКА / "прилад_база_маніфест.json").write_text(json.dumps(маніфест, ensure_ascii=False, indent=1), encoding="utf-8")
    зняти("до", база)
    зняти("після")


def зняти(мітка, дерево=КОРІНЬ):
    """Пише вимір у файл і показує код виходу та підсумок."""
    середовище = dict(os.environ)
    # Внутрішній Python -I не успадковує PYTHONUTF8. На Windows його cp1251
    # повинен читати батько з тією ж локаллю; UTF-8 файлу логу задаємо окремо.
    середовище.pop("PYTHONUTF8", None)
    середовище["PYTHONIOENCODING"] = "utf-8"
    with (ТЕКА / ("прилад_" + мітка + ".txt")).open("w", encoding="utf-8") as лог:
        р = subprocess.run([sys.executable, "джерела/прилади/корінь_річ_колір_межі.py", str(дерево)], cwd=КОРІНЬ,
                           stdout=лог, stderr=subprocess.STDOUT, timeout=900, env=середовище)
    текст = (ТЕКА / ("прилад_" + мітка + ".txt")).read_text(encoding="utf-8")
    print(мітка, "код", р.returncode, (текст.strip().splitlines() or ["порожній лог"])[-1], flush=True)
    if р.returncode:
        raise SystemExit(р.returncode)


if __name__ == "__main__":
    main()
