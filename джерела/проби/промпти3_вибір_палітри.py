"""Рядок 6223 (наряд Е.10): replay записаних промптів вибору палітри (`*_вибір_палітри_*`; живі ж15 `12_…`, `13_…`
гілки origin/claude/zhyvi-pachka-15, і теки стенда аргументами) тим самим кодом, без моделі. ДО — дані запису, зібрані
`ВИБІР` з origin/main; ПІСЛЯ — «occasion» і «day» через `вибір_палітри._назване` (без `unknown`). Суддя: відповідь
запису (`scheme`, `base`, `saturation`) — у `прийняти` ДО (модуль з main) і ПІСЛЯ на профілі ж2 (`аудит/проби/жінки`);
поруч — колір названої основи в записі й у переліку ж2 цього дерева. Запуск: cd джерела && python3 проби/промпти3_вибір_палітри.py [тека …]"""
import glob, json, subprocess, sys, types
sys.path.insert(0, "."); import вибір_палітри as ВП, збирач_промптів as З
Г = "origin/claude/zhyvi-pachka-15"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
до_м = types.ModuleType("вибір_до"); exec(compile(git("show", "origin/main:джерела/вибір_палітри.py"), "до", "exec"), до_м.__dict__)
ж2 = json.load(open("../аудит/проби/жінки/ж2.json", encoding="utf-8"))
вхід = dict(зріст=168, обхвати={"плечі": 98, "груди": 92, "талія": 74, "стегна": 99}, шкіра=ж2["skin"], волосся=ж2["hair"], очі=ж2["eyes"])
основи_ж2 = ВП.дані_промпта(ВП.перелік(вхід))["bases"]
записи = [(ф.split("/")[-3][:22], git("show", "%s:%s" % (Г, ф))) for ф in git("ls-tree", "-r", "--name-only", Г, "../аудит/живі_пачка_15/").split("\n")
          if "/VIDPOVIDI/" in ф and "_вибір_палітри_" in ф and ("/12_" in ф or "/13_" in ф)]
записи += [("стенд/" + ф.split("/")[-1][:8], open(ф, encoding="utf-8").read()) for т in sys.argv[1:] for ф in sorted(glob.glob(т + "/*_вибір_палітри_*"))]
зб = lambda о, д: len(json.dumps(З.зібрати(о, д), ensure_ascii=False))
вирок = lambda м, в: (lambda р: (р["вибір"]["схема"], р["вибір"]["основа_ранг"], р["вибір"]["гама"], р["вибір"]["обрала"], р["відхилено"]))(м.прийняти(в, відповідь))
for назва, т in записи:
    п, відповідь = т.split("── ВІДПОВІДЬ", 1); відповідь = відповідь.split("──\n", 1)[1]
    д, _ = json.JSONDecoder().raw_decode(п[п.index('{"task"'):]); дані = {к: v for к, v in д.items() if к != "task"}
    після_ = dict(дані, occasion=ВП._назване(дані.get("occasion")), **({"day": ВП._назване(дані["day"])} if дані.get("day") else {}))
    після = {к: v for к, v in після_.items() if v}
    до, пс = зб(до_м.ВИБІР, дані), зб(ВП.ВИБІР, після)
    б = str((json.loads(відповідь[відповідь.index("{"):відповідь.rindex("}") + 1]) or {}).get("base"))
    колір = lambda бази: next((о["colour"] for о in бази if о["id"] == б), None)
    в = вирок(до_м, вхід)
    сказ = "ДО %s · ПІСЛЯ %s · %s · основа %s: у записі %s, у переліку ж2 %s" % (
        в[:3], вирок(ВП, вхід)[:3], "однаково" if в == вирок(ВП, вхід) else "РІЗНО", б, колір(дані["bases"]), колір(основи_ж2))
    print("%s | %d → %d симв. (%+d) | прибрано: %s | суддя: %s" % (назва, до, пс, пс - до, sorted(set(дані["occasion"]) - set(після["occasion"]))
          + (["day." + к for к in set(дані.get("day") or {}) - set(після.get("day") or {})]), сказ))
