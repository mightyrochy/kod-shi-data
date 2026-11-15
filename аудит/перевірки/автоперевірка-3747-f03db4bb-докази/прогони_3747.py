"""Послідовні офлайн-проби голови PR, із повним завершенням кожної команди."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
os.environ["PYTHONIOENCODING"] = "utf-8"
probe = Path(__file__).with_name("перевірити_3747.py")
tasks = [([sys.executable, "-W", "ignore", str(probe), str(root), "колір"], "колір"),
         ([sys.executable, "-W", "ignore", str(probe), str(root), "каталог"], "каталог"),
         ([sys.executable, "-W", "ignore", str(probe), str(root), "запис"], "запис"),
         ([sys.executable, "-W", "ignore", "джерела/прилади/тест_походження_запису.py"], "походження")]
skip = {"кадр_варіант_woo_факти.py", "кадр_варіант_каталог.py", "кадр_варіант_перезбір.py", "кадр_варіант_факти.py"}
for p in sorted((root / "джерела/проби").glob("кадр_варіант_*.py")):
    if p.name not in skip:
        tasks.append(([sys.executable, "-W", "ignore", str(p)], p.stem))
tasks.append(([sys.executable, "-W", "ignore", "джерела/прилади/корінь_річ_кадр_варіант.py"], "прилад"))
for args, name in tasks:
    print("ПОЧАТОК", name, flush=True)
    result = subprocess.run(args, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    (out / (name + ".txt")).write_text("команда: " + subprocess.list2cmdline(args) + "\nкод виходу: " + str(result.returncode) + "\n" + result.stdout, encoding="utf-8")
    print("КІНЕЦЬ", name, "код", result.returncode, "\n" + "\n".join(result.stdout.splitlines()[-3:]), flush=True)
