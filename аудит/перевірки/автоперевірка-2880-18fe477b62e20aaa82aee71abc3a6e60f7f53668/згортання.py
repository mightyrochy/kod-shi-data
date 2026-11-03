"""Звірка збереження доказів 10276 і закриття 12528 на призначеній голові."""
import pathlib
import subprocess
import sys
import tempfile
from unittest.mock import patch

корінь = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(корінь / "джерела" / "прилади"))
import згорнути_дошку as Д

голова = "18fe477b62e20aaa82aee71abc3a6e60f7f53668"


def читати(шлях):
    return subprocess.check_output(
        ["git", "show", голова + ":" + шлях], cwd=корінь).decode("utf-8")


до = читати("аудит/БЕКЛОГ.md")
шляхи = subprocess.check_output(
    ["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only",
     голова, "--", "аудит/дошка"], cwd=корінь).decode("utf-8").splitlines()
with tempfile.TemporaryDirectory() as тека:
    тимч = pathlib.Path(тека)
    дошка, файли = тимч / "БЕКЛОГ.md", тимч / "дошка"
    дошка.write_text(до, encoding="utf-8")
    for шлях in шляхи:
        файл = файли / pathlib.PurePosixPath(шлях).relative_to("аудит/дошка")
        файл.parent.mkdir(parents=True, exist_ok=True)
        файл.write_text(читати(шлях), encoding="utf-8")
    with patch.multiple(Д, КОРІНЬ=str(тимч), ДОШКА=str(дошка), ТЕКА=str(файли)):
        звіт, помилки = Д.згорнути()
    print(звіт)
    assert not помилки, помилки
    після = дошка.read_text(encoding="utf-8")

    def рядок(текст, номер):
        return next(р for р in текст.splitlines() if р.startswith(f"| {номер} |"))

    for факт in ("2.39", "річ_колір_межі_ребра_читач.md", "2.73"):
        print("%s: ДО %s; ПІСЛЯ %s" % (
            факт, факт in рядок(до, 10276), факт in рядок(після, 10276)))
        assert факт in рядок(після, 10276)
    assert "**ЗАКРИТО**" in рядок(після, 12528)
    assert "**ЧАСТКОВО**" in рядок(після, 11288)
    print("12528: ЗАКРИТО; 11288: ЧАСТКОВО")
