"""Е2 п.5: вада коду не стає «браком входу», той самий збій кеша обидва шляхи судять однаково."""
import json, pathlib, sys, tempfile, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import feed as F, розбір_відповідей as РВ, таблиця_каталогу as ТК, жнива_маски as ЖМ, жнива_колір as ЖК
import жнива_збагачення as ЖЗ, жнива_промпти as ЖП, жнива_прогін as ЖПР

assert РВ.речі_переліку(None) == (None, None) and РВ.речі_переліку('["сукня"]') == (["сукня"], None)
assert РВ.речі_переліку("просто текст") == (None, "invalid_json(line=1,col=1)")
р = РВ.речі_з_тексту("Сукня шовкова, #112233", перелік='{"items": [обрив')
assert р["перелік_не_прочитано"].startswith("invalid_json(") and р["перелік_моделі"] is None, р
assert "перелік_не_прочитано" not in РВ.речі_з_тексту("Сукня шовкова, #112233", перелік='["Сукня, #112233"]')
т = dict(версія=ТК.ВЕРСІЯ, ключ={})
with tempfile.TemporaryDirectory() as д:
    кеш, фід = pathlib.Path(д, "кеш.json"), pathlib.Path(д, "фід.xml")
    assert ТК._розбіжність(т, str(фід), д, 0, str(кеш)).startswith("фід не читається")  # кеша нема — порожній
    кеш.write_text("{бите", encoding="utf-8")
    try:
        ТК._розбіжність(т, str(фід), д, 0, str(кеш))
    except ValueError:
        pass
    else:
        raise AssertionError("битий кеш кольорів таблиця пропустила, а фід_каталог на ньому падає")


def вада(*_):
    raise RuntimeError("вада коду")


о = dict(id="1", назва="Сукня", категорія="Сукні", фото=["x"])
for виклик in (lambda: ЖЗ.тип_для_промпту(о), lambda: ЖП.тип_речі(о), lambda: ЖПР.вибірка([о]),
               lambda: ЖК.поверхня_фото("кадр.jpg", "верх")):
    F.слоти, ЖМ._мітки_atr, ЖК.маска_речі, sys.modules["cv2"] = вада, вада, lambda *_: (1, 0.5, "", "ATR"), types.ModuleType("cv2")
    try:
        виклик()
    except RuntimeError:
        continue
    raise AssertionError("вада коду стала звичайним значенням")
print("Е2 п.5: вади коду не ковтаються; перелік не JSON — причина; битий кеш — збій на обох шляхах")
