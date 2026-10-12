"""4960: запис Ж26 А/05 → картка → справжній ендпойнт мовного шару, без виклику моделі.
Запуск із джерела: python3 проби/невідоме_4960.py [тека артефактів у /tmp]. Українська якість — ЖИВИЙ ПІСЛЯ."""
import copy, json, pathlib, subprocess, sys
sys.path.insert(0, ".")
import оцінка_образу as О, мовний_шар as М, збирач_промптів as З
git = lambda шлях: subprocess.check_output(["git", "show", "origin/claude/zhyvi-26:" + шлях], text=True)
тека = "аудит/живі_26/А/05_ж1_оціни_образ_6б/"
етапи = json.loads(git(тека + "вердикти.txt"))["прогони"][0]["вердикти"][0]["етапи"]
суд = етапи["суд"]
відповідь = git(тека + "VIDPOVIDI/seed3_03_ОЦІНКА_відповідь.txt").split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1]
картка = О.прийняти_оцінку(відповідь, суд)["картка"]
старі = [х["код"] for х in етапи["відповідь"]["картка"]["не_знаю"]]
нові = [х["код"] for х in картка["не_знаю"]]
assert старі == нові and len(нові) == len(set(нові)) == 57
тексти = {"не_знаю.%d" % і: json.dumps({"review_unknown": х["контекст"]}, ensure_ascii=False) for і, х in enumerate(картка["не_знаю"])}
для = json.loads(М.мова(json.dumps({"тексти": тексти}, ensure_ascii=False)))
вхід = json.loads(для["промпт"].split("ТЕКСТИ:\n", 1)[1])
assert [х["review_unknown"] for х in вхід] == [х["контекст"] for х in картка["не_знаю"]]
assert З.НЕВІДОМЕ_КАРТКИ_EN in для["промпт"] and all(х["review_unknown"]["sources"] for х in вхід)
assert all(х["контекст"]["definition"] for х in картка["не_знаю"] if not х["код"].startswith("input:"))
дубль = copy.deepcopy(суд); б = next(б for б in суд["без_входу"] if б.get("statements")); дубль["без_входу"].append(copy.deepcopy(б))
код = О._коди_без_входу(dict(б, statements=О._заяви(б, "statements")))[0]
assert len(О._контекст_невідомого(дубль, код)["sources"]) == len(О._контекст_невідомого(суд, код)["sources"]) + 1
звичайний = М.розмітити({"опис": "An ordinary source description " * 10})
assert З.НЕВІДОМЕ_КАРТКИ_EN not in М.промпт(звичайний)
assert М.прийняти(звичайний, '{"1":"short"}')["без_відповіді"] == ["опис"]
записані = етапи["картка"]["мова_шару"][-1]["вихід"]
відповідь_шару = {str(р["н"]): записані[р["ключ"]] for р in для["розмітка"]}
після = json.loads(М.мова(json.dumps({"розмітка": для["розмітка"], "відповідь_моделі": json.dumps(відповідь_шару, ensure_ascii=False)}, ensure_ascii=False)))
assert після["тексти"] == записані and not після["без_відповіді"]
assert М.прийняти(для["розмітка"], '{"1":"…"}')["без_відповіді"]
if len(sys.argv) > 1:
    вих = pathlib.Path(sys.argv[1]); вих.mkdir(parents=True, exist_ok=True)
    for назва, дані in (("картка.json", картка), ("шар.json", для), ("записаний_вихід.json", записані)):
        (вих / назва).write_text(json.dumps(дані, ensure_ascii=False, indent=2))
print("4960: кодів 57 → 57; визначення 54/54; джерела 57/57; втрат/дублів 0; записаний переклад незмінний; ЖИВИЙ ПІСЛЯ потрібний")
