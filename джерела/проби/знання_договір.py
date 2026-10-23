"""Факти договору та два живі переходи каталог → пакет → дріт, траур → картка."""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import знання_речі as З
import пакет_моделі as П
import дріт_моделі as Д


def головна():
    """Відрізнити вимір, діапазон, брак знання, явну відсутність і NA."""
    вікно = {"lab": (20, 0, 0), "колір_не_вимір": {"вікно": [10, 30, 0, 5, None]}}
    for р, стан in (({"lab": (0, 0, 0)}, "measured"), (вікно, "range"), ({}, "unknown")):
        р.update(id="fixture", тип="dress_generic")
        факт = З.властивість(р, "color")
        дріт = Д.річ(П.річ_пулу(р, {}))
        assert факт["status"] == стан and дріт["knowledge"]["color"]["status"] == стан
        if стан == "range":
            assert дріт["color_range"] == факт["value"]
        print("color", стан, "→", дріт["knowledge"]["color"])
    рядок = П.рядки_кандидатів({}, {}, None, {"_кандидати": {"сукня": [dict(вікно, id="projection", тип="dress_generic", метал="gold")]}})["сукня"][0]
    дріт = Д.річ(П.річ_пулу(рядок, {}))
    assert дріт["knowledge"]["color"]["status"] == "range" and дріт["metal"] == "gold"
    assert З.властивість({"hex": "#123456", "осі": {"L_from": "word"}}, "color")["status"] == "unknown"
    р = {"тип": "jewelry_generic", "матеріал": "raw fixture", "метал": None}
    assert З.властивість(р, "composition")["status"] == "unknown"
    assert З.властивість(р, "metal")["status"] == "unknown"
    assert З.МАТРИЦЯ["shirt"]["metal"]["applicability"] == "unknown"
    assert З.МАТРИЦЯ["jewelry_generic"]["composition"]["applicability"] == "unknown"
    assert З.властивість({"метал": "gold"}, "metal")["value"] == "gold"
    assert З.властивість({"метал_варіанти": ["gold", "silver"]}, "metal")["status"] == "range"
    відсутність = З.факт("measured", "absent", "explicit_fixture")
    незастосовне = З.факт("not_applicable", None, "explicit_fixture")
    assert відсутність != незастосовне != З.факт("unknown", None, "fixture_missing")
    print("матриця", len(З.МАТРИЦЯ), "типів; одяг/метал unknown; прикраса/склад unknown")
    print("явна відсутність ≠ unknown ≠ not_applicable; живі читачі пройдено")


if __name__ == "__main__":
    головна()
