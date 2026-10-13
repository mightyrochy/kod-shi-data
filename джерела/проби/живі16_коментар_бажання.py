"""ОЦІНКА-Ж16 (рядок 4023): «взуття не моє, хочу без каблука і без принта» — запис перекладача коментаря ЖИВІ-16 №13
(`seed3_36`) і ЖИВІ-14 №13 (`seed3_34`), плюс три бажання руками, тим швом, що й показ: `прийняти_вхід("verdict_comment")`
→ `паспорт_з_коментаря`. Друкує межі (типи, принти) і `бажання`. Після #829 бажання з `pattern: solid` цілим стає межею
принта, а решта того ж бажання (`item_type: sneakers` — «кросівки») зникає; ДО #829 воно лишалось «кросівки, однотонний».
Кращим: межа принта Є і бажання «кросівки» лишилось. Запуск: cd джерела && python3 проби/живі16_коментар_бажання.py"""
import json, re, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as МШ
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
ЗАПИСИ = (("ЖИВІ-16 №13", "claude/zhyvi-16", "аудит/живі_16/А/13_ж2_спорт_коментар/VIDPOVIDI/seed3_36_мовний_шар_вхід.txt"),
          ("ЖИВІ-14 №13", "claude/zhyvi-14", "аудит/живі_14/А/13_ж2_спорт_коментар/VIDPOVIDI/seed3_34_мовний_шар_вхід.txt"))
входи = []
for назва, гілка, шлях in ЗАПИСИ:
    git("fetch", "-q", "origin", гілка)
    т = git("show", "origin/%s:%s" % (гілка, шлях))
    входи.append((назва, т.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]))
for w in ([{"slot": "shoes", "item_type": "sneakers", "pattern": "solid"}], [{"slot": "shoes", "item_type": "sneakers"}],
          [{"slot": "shoes", "feature": "no_heels", "pattern": "solid"}]):
    входи.append(("руками", json.dumps({"wear": "one_change", "wants": w})))
for назва, відп in входи:
    р = МШ.прийняти_вхід("verdict_comment", відп)
    п = МШ.паспорт_з_коментаря(р["внутрішня"], {"перекладено_шаром": True, "вето": {}})["паспорт"]
    тв = п["вето_тверде"]
    print("%s · wants %s · причини «не моє» %s → типи %s · принти %s · бажання %s" % (назва, json.dumps(
        json.loads(re.search(r"\{.*\}", відп, re.S).group(0)).get("wants"), ensure_ascii=False), [x for x in р["незнайомі"]
        if "reasons" in x], тв.get("типи"), тв.get("принти"), п.get("бажання")))
