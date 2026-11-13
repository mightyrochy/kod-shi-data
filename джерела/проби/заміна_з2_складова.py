# -*- coding: utf-8 -*-
"""Е3-заміна-з-перевіркою з2: K-PAL-10/12/13, K-KOH-10/06, K-REG-01/02 не називають заміну без суду образу з нею.
ДО (SHA бази) — складова-заміна в ремонті; ПІСЛЯ — пояснення без заміни, діагноз той самий. Запуск: [SHA]; каталог не потрібен."""
import importlib, json, pathlib, subprocess, sys, types
Д = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(Д))
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "3bdf46d9d438bbb14e67683ec49ce22899f5d4a0"
ЗАМІНА = ("print_in_palette_or_solid", "separate_lightness_or_texture_shine", "eye_family_colour_near_face", "keep_one_open_zone",
          "cover_open_zones", "matte_item_in_slot", "one_register_leads_other_one_quote", "матову річ", "однотонна річ", "шарф, верх")
def модуль(ім, база):
    if not база: return importlib.import_module(ім)
    м = types.ModuleType(ім + "_до"); exec(subprocess.check_output(["git", "show", БАЗА + ":джерела/" + ім + ".py"]).decode("utf-8"), м.__dict__); return м
def випадки(С, рег):
    import palettes as PAL, bridge as B
    from реєстр_сила import зн as _зн
    П = PAL.палітра_практична(B._features(json.load(open(Д / "стенд_вх.json", encoding="utf-8")))[0], source="uncontrolled")
    П["прийоми"] = list(П["прийоми"]) + [dict(прийом="драматизація_м_якої", активний=True), dict(прийом="сивина", активний=True)]  # м'яка палітра, сивина
    П["вікна"]["сім_ї"]["очі"] = [(160.0, 185.0)]
    речі = [dict(id="а", слот="верх", hex="#e0207a", візерунок="квітковий"), dict(id="б", слот="шарф", hex="#2050e0"),
            dict(id="в", слот="низ", hex="#d02020"), dict(id="г", слот="сережки", hex="#d02020")]
    вих = С.палітра_образу(речі, {"_палітра": П}, {r["id"]: r for r in речі})
    вих = вих if isinstance(вих, list) else вих[0]
    одяг = [dict(id="а", слот="верх", назва="топ з паєтками", рукав_рівень="без рукавів"), dict(id="б", слот="низ", назва="спідниця", довжина_рівень="міні")]
    вих += С.доповнення_судді(одяг, dict(пора="13:00", відкриті_зони="none"), None)
    ш = [dict(id="а", назва="блейзер вовна", слот="верх"), dict(id="б", назва="софтшел мембрана", слот="низ"), dict(id="в", назва="шифон мереживо", слот="взуття")]
    вих += рег.перевірити(ш, _зн, "класика", None, False)[0]
    return [з for з in вих if з.get("правило") in ("K-PAL-10", "K-PAL-12", "K-PAL-13", "K-KOH-10", "K-KOH-06", "K-REG-01", "K-REG-02")
            and not str(з.get("суть", "")).startswith("rule_input")]
def складова(з):
    т = json.dumps([з.get("суть"), з.get("ремонт"), з.get("що_зняло_б"), з.get("ремонт_заяви")], ensure_ascii=False)
    return [x for x in ЗАМІНА if x in т]
if __name__ == "__main__":
    до, після = (випадки(модуль("суд_від_моделі", б), модуль("реєстри", б)) for б in (True, False))
    assert len(до) == len(після) == 7, (len(до), len(після))
    for з0, з1 in zip(до, після):
        assert (з0["правило"], з0["сила"], з0["речі"], з0.get("заяви")) == (з1["правило"], з1["сила"], з1["речі"], з1.get("заяви")), з0["правило"]
        print("%-8s ДО: %-40s ПІСЛЯ: %s" % (з0["правило"], ",".join(складова(з0)) or "—", ",".join(складова(з1)) or "—"))
    assert all(складова(з) for з in до) and not any(складова(з) for з in після)
    print("складова-заміна ДО: %d з 7; ПІСЛЯ: 0; правила, сила, речі й заяви ті самі" % sum(bool(складова(з)) for з in до))
