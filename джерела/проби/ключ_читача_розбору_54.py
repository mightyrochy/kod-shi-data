"""Ключ читача розбору 5.4: річ фіда (id з «@» + id_жниварки) читає лише свій запис, без чужого магазину."""
import json, os, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import catalog_fields as К, каталог_коди as КК
A = dict(id="ж-08403@sarahberlin.com", id_жниварки="ж-08403", магазин="sarahberlin.com", назва="A")
Б = dict(id="ж-08403@otaje.com", id_жниварки="ж-08403", магазин="otaje.com", назва="Б")
В = dict(id="ж-00001@otaje.com", id_жниварки="ж-00001", магазин="otaje.com", назва="В")
def тип(файл, річ):
    with tempfile.TemporaryDirectory() as д:
        ш = os.path.join(д, "р.json"); json.dump(файл, open(ш, "w"), ensure_ascii=False)
        os.environ["ROZBIR_KODY"] = ш; КК._КЕШ.clear()
        return К.код_типу(річ)
повний = {A["id"]: {"item_type": "dress_generic"}, "причини": {}}   # частковий файл: Б, В ще нема
assert тип(повний, A) == "dress_generic", "річ фіда не читає свого запису"
assert тип(повний, Б) == "unknown" and тип(повний, В) == "unknown", "річ читає запис чужого магазину"
assert тип({"ж-08403": {"item_type": "dress_generic"}}, A) == "dress_generic", "старий еталон без «@» зламано"
assert тип({"ж-08403": {"item_type": "dress_generic"}}, Б) == "dress_generic"
print("ключ читача: повний id читає своє; частковий файл — чужого магазину нема; старий еталон живий")
