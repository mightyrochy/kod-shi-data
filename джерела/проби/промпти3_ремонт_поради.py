"""Рядки 6192, 6193: replay двох записаних ремонтів поради ж15 (`claude/zhyvi-pachka-15`, ж2 «новорічна» і «йога») тим
самим кодом, без моделі. З промпту запису — вхід ремонту (теми, вада, її лист); промпт збирається наново
(`промпт_поради`, розмір у знаках: tokenizer.json Gemma 3 у хмарі нема), записана відповідь іде в `прийняти_пораду` —
що вона прочитала б. Кращим: промпт коротший, показано те саме, у темі goal — «to look taller».
Запуск: cd джерела && python3 проби/промпти3_ремонт_поради.py"""
import json, subprocess, sys
sys.path.insert(0, "."); import мовний_шар as М
Г, Т = "origin/claude/zhyvi-pachka-15", "../аудит/живі_пачка_15"
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", "claude/zhyvi-pachka-15")
вади = {v: k for k, v in М.ВАДИ_ПОРАДИ_EN.items()}
for ф in sorted(ф for ф in git("ls-tree", "-r", "--name-only", Г, Т).split("\n") if "_ремонт_поради" in ф):
    т = git("show", "%s:%s" % (Г, ф))
    промпт, відповідь = т.split("── ПРОМПТ", 1)[1].split("──", 1)[1].split("── ВІДПОВІДЬ", 1)
    вх = json.loads(промпт.strip())
    рем = dict(вада=вади.get(вх.get("defect")), дозволені=list(вх.get("advice_topics") or {}),
               запрошення=вх.get("your_invitation") or "")
    новий = М.промпт_поради(рем, вх.get("her_new_message") or "")
    р = М.прийняти_пораду(відповідь.split("──", 1)[1], рем)
    print(ф.split("/")[-3][:22], "| вада:", рем["вада"], "| промпт записаний:", len(промпт.strip()), "знаків → зараз:",
          len(новий), "| «taller» у goal:", "taller" in json.loads(новий)["advice_topics"].get("goal", ""),
          "| «?» у правилах:", "question marks" in новий, "| показано:", р["теми_поради"], repr(р["запрошення"][:90]))
