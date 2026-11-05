"""Вердикт верхнього шару на кожній смузі погоди без числового перетворення коду."""
import json
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(КОРІНЬ))
import міст_вхід as ВХ
import річ_з_фото as РФ
import сценарій as С
import пакет_моделі as М
from outfit import ТЕМП_МАПА

if __name__ == "__main__":
    вхід = json.loads((КОРІНЬ / "стенд_вх.json").read_text(encoding="utf-8"))
    особа, тіло = ВХ.збірка(ВХ.нормалізувати_вхід(вхід))[:2]
    річ = dict(ід="жакет", слот="верхній_шар", тип="жакет", назва="Жакет")
    збої = []
    for смуга in (*С.СМУГИ_ПОГОДИ, None):
        try:
            вердикт = РФ.вердикт(річ, особа, тіло, dict(нагода="робота", смуга_погоди=смуга))
            підказки = [з for з in вердикт["знахідки"] if з.get("правило") == "K-WEA-01"]
            очікуємо = bool(смуга and ТЕМП_МАПА[смуга]["шари"] <= 1)
            assert bool(підказки) == очікуємо, підказки
            assert "°C" not in json.dumps(вердикт, ensure_ascii=False)
            print(смуга, "підказок K-WEA-01:", len(підказки))
        except Exception as збій:
            збої.append((смуга, type(збій).__name__, str(збій)))
    print("збоїв:", len(збої), збої)
    for форма in (tuple, list):
        assert М.жорстке_відсічення(dict(id="тк", ціна=100, слот="верх", сезон_тканини=форма(("cold", "cool"))), смуга_погоди="hot") == "fabric_off_temperature"
    try:
        М.жорстке_відсічення(dict(id="тк", ціна=100, слот="верх", сезон_тканини=[2, 10]), смуга_погоди="hot")
    except ValueError as збій:
        assert str(збій) == "fabric_band_unreadable:тк"
    else:
        raise AssertionError("Пошкоджена смуга тканини пройшла без сигналу")
    sys.exit(bool(збої))
