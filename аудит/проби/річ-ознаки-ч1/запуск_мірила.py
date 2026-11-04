"""Незмінений прилад кореня та лічба своїх шести файлів із повного виводу."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent
СВОЇ = {"palettes.py", "палітра_запити.py", "палітра_розвилка.py", "profile.py",
        "колір_простір_надійність.py", "суд_від_моделі.py"}


def лічба(шлях):
    """Читає повний журнал, підтримуючи первинний вивід PowerShell UTF-16."""
    байти = шлях.read_bytes()
    текст = байти.decode("utf16" if байти.startswith(b"\xff\xfe") else "utf-8-sig").replace("\r\n", "\n")
    місця = re.findall(r"^джерела/([^:]+):(\d+) ·", текст, re.M)
    усі = re.findall(r"^місць: (\d+)$", текст, re.M)
    assert усі, "немає підсумку приладу"
    свої = [f"{ф}:{н}" for ф, н in місця if ф in СВОЇ]
    шлях.write_text(текст, encoding="utf8", newline="\n")
    return dict(усі=int(усі[-1]), свої=len(свої), решта=int(усі[-1])-len(свої), місця=свої)


def main():
    """Виконує прилад на поточному дереві, потім зіставляє повні виводи."""
    початок = time.monotonic()
    with (Д / "після.txt").open("w", encoding="utf8") as ф:
        p = subprocess.run([sys.executable, "-W", "ignore", "джерела/прилади/корінь_річ_ознаки_обличчя.py"],
                           cwd=К, stdout=ф, stderr=subprocess.STDOUT,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    результат = dict(код=p.returncode, секунд=round(time.monotonic()-початок, 2),
                     після=лічба(Д / "після.txt"))
    if (Д / "до.txt").stat().st_size:
        результат["до"] = лічба(Д / "до.txt")
    (Д / "прилад.json").write_text(json.dumps(результат, ensure_ascii=False, indent=2), "utf8")
    print(json.dumps(результат, ensure_ascii=False), flush=True)
    return p.returncode


if __name__ == "__main__":
    sys.exit(main())
