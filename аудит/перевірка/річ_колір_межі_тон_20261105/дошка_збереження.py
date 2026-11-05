"""Перевіряє згортання повтору 1870 зі збереженням усіх попередніх фактів."""
from pathlib import Path
import re
import shutil
import sys
import tempfile


def головна():
    """Згортає копію фрагмента в tmp задачі й звіряє всю попередню клітинку."""
    корінь = Path.cwd().resolve()
    sys.path.insert(0, str(корінь / "джерела/прилади"))
    import згорнути_дошку as ЗД
    джерело = корінь / "аудит/БЕКЛОГ.md"
    фрагмент = корінь / "аудит/дошка/gemini/Річ-колір-межі.md"
    попереднє = джерело.read_bytes()
    дані = фрагмент.read_bytes()
    збіги = [p for p in (корінь / "аудит/дошка").rglob("*.md") if any(
        re.match(r"^стан!? +1870:", р) for р in p.read_text(encoding="utf-8").splitlines())]
    assert збіги == [фрагмент], збіги
    тимчасова = (корінь.parent / "tmp").resolve()
    копія = Path(tempfile.mkdtemp(prefix="тон-дошка-", dir=тимчасова)).resolve()
    assert копія.is_relative_to(тимчасова)
    shutil.copyfile(джерело, копія / "БЕКЛОГ.md")
    (копія / "дошка/gemini").mkdir(parents=True)
    shutil.copyfile(фрагмент, копія / "дошка/gemini/Річ-колір-межі.md")
    ЗД.ДОШКА, ЗД.ТЕКА = str(копія / "БЕКЛОГ.md"), str(копія / "дошка")
    звіт, помилки = ЗД.згорнути()
    assert not помилки, помилки
    до = джерело.read_text(encoding="utf-8").splitlines()
    після = (копія / "БЕКЛОГ.md").read_text(encoding="utf-8").splitlines()
    зміни = [(a, b) for a, b in zip(до, після) if a != b]
    assert len(до) == len(після) and len(зміни) == 1
    a, b = зміни[0]
    assert re.match(r"^\| *1870 *\|", a)
    x, y = ЗД.межі_стану(a)
    x1, y1 = ЗД.межі_стану(b)
    assert a[x:y].strip() in b[x1:y1]
    assert a[:x] == b[:x1] and a[y:] == b[y1:]
    assert "11.3/16.0/25.3" in b and "виявлено: проба; внесено: давнє" in b
    assert джерело.read_bytes() == попереднє and фрагмент.read_bytes() == дані
    return звіт + "; 1870: попередня клітинка повністю збережена; інші рядки незмінні"


if __name__ == "__main__":
    результат = головна()
    Path(__file__).with_suffix(".txt").write_text(результат + "\n", encoding="utf-8")
    print(результат)
