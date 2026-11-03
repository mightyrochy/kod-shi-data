"""Факт втрати доказу 10276 під час згортання лише фрагмента PR #2880."""
import pathlib
import subprocess
import sys
import tempfile
from unittest.mock import patch

корінь = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(корінь / "джерела" / "прилади"))
import згорнути_дошку as Д

голова = "584a370510a51a052fdb81e96f447de40c27ac11"
def читати(шлях):
    return subprocess.check_output(["git", "show", голова + ":" + шлях],
                                   cwd=корінь).decode("utf-8")

до = читати("аудит/БЕКЛОГ.md")
фрагмент = читати("аудит/дошка/gemini/Річ-колір-вимір.md")
with tempfile.TemporaryDirectory() as тека:
    тимч = pathlib.Path(тека)
    дошка, файли = тимч / "БЕКЛОГ.md", тимч / "дошка"
    файли.mkdir()
    дошка.write_text(до, encoding="utf-8")
    (файли / "Річ-колір-вимір.md").write_text(фрагмент, encoding="utf-8")
    with patch.multiple(Д, КОРІНЬ=тека, ДОШКА=str(дошка), ТЕКА=str(файли)):
        звіт, помилки = Д.згорнути()
    print(звіт)
    assert not помилки, помилки
    після = дошка.read_text(encoding="utf-8")
    рядок = lambda текст: next(р for р in текст.splitlines() if р.startswith("| 10276 |"))
    for факт in ("2.39", "річ_колір_межі_ребра_читач.md", "2.73"):
        print("%s: ДО %s; ПІСЛЯ %s" % (факт, факт in рядок(до), факт in рядок(після)))
