"""QA 7501/7502: живі читачі оцінки, турніру й заміни; Lab-only fallback каталогу."""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import пакет_моделі as П
import дріт_моделі as Д
import уважний_вибір as У
import знання_дріт as ЗД


def головна():
    """Довести значення measured і спільну легенду до кожного фактичного читача."""
    точка = П.річ_пулу(dict(id="qa-lab", тип="dress_generic", lab=(20, 1, 2)), {})
    дріт = Д.річ(точка)
    assert дріт["lab"] == (20, 1, 2) and дріт["knowledge"]["color"]["status"] == "measured"
    assert "lab" not in Д.річ(П.річ_пулу(dict(id="hex", hex="#123456"), {}))
    вікно = П.річ_пулу(dict(id="qa-range", тип="dress_generic", hex="#123456",
                            колір_не_вимір={"вікно": [10, 30, 0, 5, None]}), {})
    for заміна in (False, True):
        пак = {"пул": {"сукня": [точка if заміна else вікно]}}
        if заміна:
            пак["заміна"] = {"ід": "qa-old", "слот": "сукня", "речі": [
                dict(точка, id="qa-old", слот="сукня"), dict(вікно, id="fixed", слот="шарф")]}
        річ = пак["пул"]["сукня"][0]
        запити = У.запити_оцінки(пак, {річ["н"]}, 1, 0) + У.запити_турніру(
            пак, {"dress-1": [річ["н"]]}, {"dress-1"}, 1, 0)
        for зап in запити:
            дані = json.loads(зап["текст"])
            assert дані["item_keys"]["knowledge"] == Д.ОПИС_КЛЮЧІВ["knowledge"]
            assert дані["item_keys"]["color_range"] == Д.ОПИС_КЛЮЧІВ["color_range"]
            assert "in_arc" not in дані["item_keys"]
            assert ЗД.ОПИС in дані["task"]["input"] and дані["knowledge_legend"]["sections"]
            assert "color_window" in json.dumps(ЗД.відновити(дані))
        print("оцінка/турнір", "replacement-only range" if заміна else "range", "легенда є")
    print("Lab-only каталог → пакет → дріт: measured + value; hex не дублюється")


if __name__ == "__main__":
    головна()
