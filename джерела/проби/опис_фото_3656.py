"""Рядок 3656: опис ЖИВІ-14 №11 рука 1 (−15 °C) — що бачила модель про пальто й шапку. Записаний промпт і відповідь
опису 26 + запис пальта з файла вердиктів (`кадр_кольору`) → промпт опису з тих самих речей: на базі — ДО, на гілці — ПІСЛЯ.
Пальто «кемел»: кадр картки сірий (галерея іншого кольору), код це знав (R-FEED-01); шапка: тип класифікатора «светр»."""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import розбір_відповідей as РВ, внутрішня_мова as ВМ
тека = "origin/claude/zhyvi-14:аудит/живі_14/А/11_ж7_мороз_без_відкритого/"


def git(ім):
    try:
        return subprocess.run(["git", "show", тека + ім], capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError as e:
        sys.exit("нема гілки ЖИВІ-14 (git fetch origin claude/zhyvi-14): %s" % e)


п, в = git("VIDPOVIDI/seed3_26_ОПИС_V1_ОПИС_ВІДПОВІДЬ_V1.txt").split("── ВІДПОВІДЬ", 1)
речі = json.JSONDecoder(strict=False).raw_decode(п[п.index("{"):])[0]["outfit"]["items"]
про = {x["n"]: x["text"] for x in json.loads(в.split("\n", 1)[1])["about_items"]}
вер = git("вердикти.txt")
поч = [м.start() for м in re.finditer(r'\{"id":"ж-05315@bella-bicchi.com","назва"', вер)]
кадр = next(json.loads(м.group(1)) for і in поч for м in [re.search(r'"кадр_кольору":(\{[^}]*\})', вер[і:вер.find('{"id":', і + 1)])] if м)
тип_каталогу = {"#159·16": "светр"}            # шапка: `фід_слот.тип_речі` → «светр» (укладка запису ж-07685)
вхід = [dict(н=r["n"], назва=r["name"], слот=ВМ.ключ("slot", r["kind"]),
             тип=тип_каталогу.get(r["n"]) or ВМ.ключ("item_type", r.get("type")), магазин=r["shop"],
             колір=ВМ.ключ("color_name", r["color"]), фото_номери=r["photos"],
             **({"кадр_колір": кадр["фото"]} if r["n"] == "#239·04" and кадр.get("стан") == "інший_колір" else {}))
        for r in речі]
пром = РВ.опис_v1(вхід, образ="о1", мова_тексту="English")
пром = пром if isinstance(пром, dict) else json.loads(пром)
print("запис вердиктів, пальто: кадр_кольору=%s" % кадр)
for н in ("#239·04", "#159·16"):
    р = next(x for x in пром["outfit"]["items"] if x["n"] == н)
    print("%s у промпті: %s" % (н, {к: р.get(к) for к in ("kind", "type", "color", "photo_colour", "photos")}))
    print("   записана відповідь ДО: %s" % про[н][:110])
т = json.dumps(пром.get("task") or {}, ensure_ascii=False)
print("рядок поля «photo_colour» у завданні промпта: %s" % ("є" if "photo_colour" in т else "нема"))
