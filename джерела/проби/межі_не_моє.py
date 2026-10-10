"""Рядок 4281 (ОЦІНКА-Ж19): replay записаних відповідей перекладача коментаря на «взуття не моє, хочу без каблука і без
принта» (сцена №13 ЖИВІ-19/18/17/16/14) швом показу — `прийняти_вхід("verdict_comment", слоти речей образу)` →
`паспорт_з_коментаря` → пул стенда (сід 4242): межі паспорта, бажання, `перенесено` і скільки у пулі взуття на каблуці
та з візерунком. Ж19 (`seed3_33`): ознаки в `about_items[].features/patterns`, `wants[].features/patterns`, `vetoes: []`;
Ж18 (`seed3_32`): межі у `vetoes` і `reasons: [heels, print]`. Ще — рядок промпту про «не моє» (той, що міняв #863).
Код — з теки аргументу. Запуск: cd джерела && python3 проби/межі_не_моє.py [тека джерел іншої збірки]   (~1 хв)"""
import json, os, re, subprocess, sys
Д = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "."); sys.path.insert(0, Д); os.chdir(Д)
import feed as Ф, bridge as B, міст_пакет as МП, мовний_шар as М
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
кат = Ф.каталог_на_диску("каталог_повний.xml")
def пул(п):
    вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), сід=4242, каталог=кат, паспорт=п)
    МП._КЕШ_ПАКЕТА.clear(); B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    вз = [p for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати")][0]["кандидати"].get("взуття") or []
    return "взуття %d: на каблуці %d, з візерунком %d" % (len(вз), sum(1 for r in вз if str(r.get("каблук")).startswith(
        "каблук: є")), sum(1 for r in вз if (r.get("візерунок") or "solid") != "solid"))
print("промпт:", re.search(r"У reasons — .*", М.ВИДИ_ВХОДУ["verdict_comment"]["межа"]).group(0))
print("без меж:", пул({"перекладено_шаром": True, "вето": {}}))
for назва, б, сід in (("Ж19", 19, 33), ("Ж18", 18, 32), ("Ж17", 17, 36), ("Ж16", 16, 36), ("Ж14", 14, 34)):
    git("fetch", "-q", "origin", "claude/zhyvi-%d" % б)
    т = git("show", "origin/claude/zhyvi-%d:аудит/живі_%d/А/13_ж2_спорт_коментар/VIDPOVIDI/seed3_%d_мовний_шар_вхід.txt"
            % (б, б, сід))
    речі = json.loads(re.search(r'"items": *(\[.*?\])\s*[,}]', т, re.S).group(1))
    р = М.прийняти_вхід("verdict_comment", т.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1],
                        слоти_речей={x["id"]: x["slot"] for x in речі})
    п = М.паспорт_з_коментаря(р["внутрішня"], {"перекладено_шаром": True, "вето": {}})["паспорт"]
    тв = п["вето_тверде"]
    print("%s №13 · типи %s принти %s слоти %s · бажання %s · перенесено %s · незнайомі %d → %s" % (
        назва, тв.get("типи"), тв.get("принти"), тв.get("слоти"), п.get("бажання"), р.get("перенесено"),
        len(р["незнайомі"]), пул(п)))
