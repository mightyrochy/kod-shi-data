"""Перевіряє записані профілі через справжній ендпойнт палітри й бриф."""
import json
import gzip
from pathlib import Path
import sys

К = Path(__file__).resolve().parents[3]
ВИХІД = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(К / "джерела/прилади"))
import знімок_мосту as З
З.підготувати(str(К / "джерела"))
import міст_основи as О
import міст_вхід as М
import вибір_палітри as В
import palette as П
import brief as Б

база = json.loads((К / "джерела/стенд_вх.json").read_text("utf8"))
записи = []
for шлях in sorted((К / "аудит/проби/жінки").glob("*.json")):
    ж = json.loads(шлях.read_text("utf8"))
    for слова in ({}, {"метал": "срібло"}):
        d = dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source="model_hex", самозвіт=слова)
        вихід = О.палітри(d)
        if isinstance(вихід, str): вихід = json.loads(вихід)
        assert not вихід.get("помилка"), вихід
        assert вихід["гейт"]["джерело"] == "model_hex" and not вихід["гейт"]["можна_стверджувати"]
        F = М.features(d)[0]
        п = В.перелік(d)
        особа = п["особа"]
        for г in П.розвилка_специфікацій(F, ["верх", "низ", "взуття"])["розвилка"]:
            for слот in (г.get("спец") or {}).get("слоти", {}).values():
                if слот.get("дуга_тону") is None:
                    assert Б.колір_слота(слот)[0] is None
        записи.append(dict(профіль=шлях.stem, самозвіт=слова, особа=особа, палітра=вихід))
    print(шлях.stem, "пройдено", flush=True)
ВИХІД.write_bytes(gzip.compress(json.dumps(записи, ensure_ascii=False).encode("utf8"), mtime=0))
print("ендпойнт палітри та перелік:", len(записи), "випадків")
