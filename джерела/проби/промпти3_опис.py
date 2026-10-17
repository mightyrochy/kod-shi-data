"""Рядки 6219, 6220 (наряд Е.10): replay записаних промптів опису картки (`*ОПИС_V1*`, живі ж15 `12_ж2_новорічна_мороз`,
`13_ж2_йога_зранку`, гілка origin/claude/zhyvi-pachka-15) тим самим кодом, без моделі. ДО — ті самі дані, зібрані `ОПИС`
з origin/main (поруч — довжина запису: main після прогону дописав правила інших рядків, тож різниця — не ця правка). ПІСЛЯ — ті самі дані, палітра —
`дріт_моделі.палітра_опису` (метал, найдальші, поєднання), правила — `розбір_відповідей.ОПИС` цього дерева.
Друкує: симв. на виклик ДО → ПІСЛЯ, палітру ДО → ПІСЛЯ, сталу частину ОПИС (ті самі дані, правила ДО → ПІСЛЯ). Запуск: cd джерела && python3 проби/промпти3_опис.py"""
import json, subprocess, sys, types
sys.path.insert(0, "."); import розбір_відповідей as Р, дріт_моделі as Д, збирач_промптів as З
Г = "origin/claude/zhyvi-pachka-15"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
до_м = types.ModuleType("розбір_до"); exec(compile(git("show", "origin/main:джерела/розбір_відповідей.py"), "до", "exec"), до_м.__dict__)
ф_ = [ф for ф in git("ls-tree", "-r", "--name-only", Г, "../аудит/живі_пачка_15/").split("\n")
      if "/VIDPOVIDI/" in ф and "ОПИС_V1" in ф and ("/12_" in ф or "/13_" in ф)]
сума = [0, 0]
for ф in ф_:
    п = git("show", "%s:%s" % (Г, ф)).split("── ВІДПОВІДЬ")[0].split("──\n", 1)[1]
    і = п.index('{"version"'); д, к = json.JSONDecoder().raw_decode(п[і:])
    мова = д["task"].get("language")
    дані = {x: v for x, v in д.items() if x not in ("version", "task")}
    збір = lambda о, дн: len(п[:і]) + len(json.dumps(З.зібрати(о, дн, мова_тексту=мова), ensure_ascii=False)) + len(п[і + к:])
    до, до_зб = len(п), збір(до_м.ОПИС, дані)
    після = збір(Р.ОПИС, dict(дані, palette=Д.палітра_опису(дані.get("palette"))))
    сума[0] += до_зб; сума[1] += після
    print("%s | запис %d · ДО (main) %d → ПІСЛЯ %d (%+.0f %%) | стала %+d | palette %d → %d, ключі ПІСЛЯ %s" % (
        ф.split("/")[-3][:22] + "/" + ф.split("/")[-1][:8], до, до_зб, після,
        100.0 * (після - до_зб) / до_зб, збір(Р.ОПИС, дані) - до_зб, len(json.dumps(дані.get("palette"), ensure_ascii=False)),
        len(json.dumps(Д.палітра_опису(дані.get("palette")), ensure_ascii=False)), sorted(Д.палітра_опису(дані.get("palette")) or {})))
print("усього %d записів: ДО %d → ПІСЛЯ %d симв. (%+.1f %%)" % (len(ф_), сума[0], сума[1], 100.0 * (сума[1] - сума[0]) / max(1, сума[0])))
