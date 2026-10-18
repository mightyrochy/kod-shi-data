"""Збирач бере переліки вибраного checkout; дві теки не ділять кеш імпортів."""
import json
import sys
import tempfile
from pathlib import Path

ДЖЕРЕЛА = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ДЖЕРЕЛА))
import build_артефакт as Б

with tempfile.TemporaryDirectory() as тека:
    значення = []
    for номер in (1, 2):
        дж = Path(тека) / str(номер)
        дж.mkdir()
        маркер = "checkout_%d</script>" % номер
        модулі = {
            "bridge": 'ПОЛЯ_ДРАПУ = ("метал", %r)' % маркер,
            "pipeline": 'ЗОНИ_ВЕТО = (%r,)\nГРУПИ_ВЕТО = ()\nТЕКСТОВІ_ГРУПИ_ВЕТО = ()' % маркер,
            "silhouette": 'ОСНОВНІ_ОБХВАТИ = (%r,)' % маркер,
            "brief": 'НАСИЧЕНІСТЬ = {%r: 1}' % маркер,
            "слоти": 'def група(*args, **kwargs): return (%r,)' % маркер,
        }
        for ім, код in модулі.items():
            (дж / (ім + ".py")).write_text(код, encoding="utf-8")
        експорт = Б._переліки_показу(str(дж))
        факт = json.loads(експорт)
        assert "</script>" not in експорт
        assert факт["драп"] == ["метал", маркер]
        assert факт["зони_вето"] == [маркер]
        assert факт["гами"] == [маркер]
        assert Б._переліки_показу(str(дж)) == експорт
        значення.append(експорт)
    assert значення[0] != значення[1]
print("ПЕРЕЛІКИ: дві теки незалежні; експорт повторюється; тег script екрановано")
