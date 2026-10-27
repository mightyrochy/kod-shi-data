"""Показати нові українські рядки з пробілами в показі проти вхідної пачки."""
import re
import subprocess
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
БАЗА = "68e5ef3e799d37cd84cf8ea0793edb0e25d75e53"
ЛЕКСЕМИ = re.compile(r'''//[^\n]*|/\*[\s\S]*?\*/|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`''')


def рядки(код):
    """Літерали зі словами й пробілами; коментарі не є текстом показу."""
    return {м[0] for м in ЛЕКСЕМИ.finditer(код) if м[0][0] in "'\"`"
            and re.search(r"[А-Яа-яІіЇїЄєҐґ]", м[0]) and re.search(r"\s", м[0])}


if __name__ == "__main__":
    нові = []
    for шлях in sorted((КОРІНЬ / "джерела/показ").glob("*.js")):
        імʼя = шлях.relative_to(КОРІНЬ).as_posix()
        було = subprocess.check_output(["git", "show", БАЗА + ":" + імʼя], cwd=КОРІНЬ).decode("utf-8")
        нові.extend((імʼя, т) for т in рядки(шлях.read_text(encoding="utf-8")) - рядки(було))
    for імʼя, т in нові:
        print(імʼя, repr(т))
    print("Нових рядків-фраз у джерела/показ/: %d" % len(нові))
    raise SystemExit(bool(нові))
