"""Рядок 4622: replay старого raw; варіанти нового контракту СИНТЕТИЧНІ, без моделі.
Аргумент — справжній *_мовний_шар_хід_розмови.txt; не доводить живої якості ПІСЛЯ."""
import copy, json, pathlib, sys
sys.path.insert(0, ".")
import мовний_шар as М
import сценарій as С, паспорт_нагоди as П

def main():
    """Звіряє відхилення конфлікту, незалежні канали й незмінність старого raw."""
    сире = pathlib.Path(sys.argv[1]).read_text()
    вхід = json.loads(сире.split("\n", 1)[1].split("\n── ВІДПОВІДЬ")[0])
    слова = вхід["her_new_message"]
    raw = сире.split("── ВІДПОВІДЬ", 1)[1].split("──", 1)[1]
    об = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
    def replay(відповідь, досі=None, сц=None):
        """Справжні розбір і шов; текст моделі без змін."""
        р = М.прийняти_розмову(відповідь)
        return М.паспорт_з_шару(р["внутрішня"], сц or {}, паспорт_досі=досі,
                               слова_ходу=[слова], частини=р["частини"])
    старий = replay(raw)
    assert старий["паспорт"]["нагода"] == "спорт"
    for намір, нагода, місце in (("other", "sport", "cafe"), ("other", "everyday", "cafe"),
                               ("sport", "sport", "park"), ("unknown", "sport", "cafe"),
                               ("other", "travel", "cafe"), ("other", "celebration", "cafe")):
        нове = copy.deepcopy(об)
        нове["update"].update(occasion_part={"quote": нове["update"]["movement" if намір == "sport" else "place"]["quote"], "value": намір})
        нове["update"]["occasion"]["value"] = нагода
        нове["update"]["place"]["value"] = місце
        ш = replay(json.dumps(нове, ensure_ascii=False), старий["паспорт"], {"нагода": "спорт"})
        п = ш["паспорт"]
        конфлікт = намір == "other" and нагода == "sport"
        assert п["виміри"]["occasion"] == ("unknown" if конфлікт else нагода)
        assert п["виміри"]["place"] == місце and п["виміри"]["movement"] == "sport"
        assert ("occasion" in ш["не_записано"]) == конфлікт and П.з_показу({"нагода": "спорт"}, п)[0].get("нагода") == (None if конфлікт else п.get("нагода"))
        assert П.виміри_нагоди(п, {"нагода": "спорт"})[0]["occasion"] == п["виміри"]["occasion"]
        print("SYNTHETIC", намір, нагода, місце, "→", п["виміри"]["occasion"], ш["не_записано"])
    print("RECORDED old raw remains sport; LIVE AFTER pending")

if __name__ == "__main__":
    main()
