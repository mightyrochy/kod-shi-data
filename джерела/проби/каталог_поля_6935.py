# -*- coding: utf-8 -*-
"""6935: друкує поля ДО/ПІСЛЯ та контролі цитат; це механіка контракту, не якість моделі."""
import json, pathlib, subprocess, sys  # noqa: E401
Д = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Д))
import каталог_розбір as КР, внутрішня_мова as ВМ  # noqa: E401,E402


def main():
    """Звіряє породжені схеми й кожний код трьох полів із чинним сторожем цитат."""
    групи = {"listing_kind": "listing_kind", "audience": "catalog_audience", "name_language": "name_language"}
    до = json.loads(subprocess.check_output(["git", "-C", str(Д), "show", "origin/main:джерела/каталог_розбір.schema.json"]))
    схема = json.loads((Д / "каталог_розбір.schema.json").read_text())
    assert схема == КР.схема()
    assert json.loads((Д / "внутрішня_мова.schema.json").read_text()) == ВМ.схема()
    після = схема["$defs"]["catalog_parse"]["properties"]
    відповідь = схема["$defs"]["model_answer"]
    assert ВМ.ТАБЛИЦЯ["audience"] == {"usual": "usual", "conservative": "conservative"}
    вхід = КР.вхід({"назва": "СУКНЯ №1081 ШОКОЛАД"})  # текст ж-01232, не еталон її кодів
    перевірено = 0
    for поле, група in групи.items():
        коди = list(ВМ.ТАБЛИЦЯ[група]) + [КР.UNKNOWN]
        лист = відповідь["properties"][поле]
        assert після[поле]["enum"] == лист["properties"]["value"]["enum"] == коди
        assert поле in відповідь["required"] and лист["required"] == ["quote", "value"]
        for код in коди:
            for цитата, очікуване in ((вхід["name"], код), ("", КР.UNKNOWN), ("НЕМА ТАКОЇ ЦИТАТИ", КР.UNKNOWN)):
                розбір, причини = КР.з_відповіді(json.dumps({поле: {"quote": цитата, "value": код}}), вхід)
                assert розбір[поле] == очікуване, (поле, код, цитата, причини)
                перевірено += 1
        for сире in (None, "unknown", "not_applicable", "invalid_code"):
            assert КР.з_відповіді(json.dumps({поле: сире}), вхід)[0][поле] == КР.UNKNOWN
            перевірено += 1
    assert all(КР.з_відповіді("{}", вхід)[0][поле] == КР.UNKNOWN for поле in групи)
    print("6935 · полів ДО %d → ПІСЛЯ %d · схеми узгоджено · контролів кодів/цитат/unknown %d · audience сценарію збережено"
          % (sum(п in до["$defs"]["catalog_parse"]["properties"] for п in групи), sum(п in після for п in групи), перевірено))


if __name__ == "__main__":
    main()
