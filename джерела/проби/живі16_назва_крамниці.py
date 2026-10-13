"""ТЕКСТИ-КАРТОК-3 (рядок 4022): перекладач (мовний шар) переписує українську назву речі з крамниці, яка стоїть у
тексті входу перед « — » (рядки ремонту й заміни картки): «Срібна підвіска з медальйоном» → «Срібна кулонна
каблучка з медальйоном» (ЖИВІ-16 №11, `seed3_27`). Записані виклики перекладача ЖИВІ-15/16 №11–13: на кожен текст
входу, що починається кириличною назвою й « — », — чи переклад починається тією самою назвою. Кращим: 0 змінених.
Запуск: cd джерела && python3 проби/живі16_назва_крамниці.py"""
import json, re, subprocess
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
for ж in ("15", "16"):
    Г = "origin/claude/zhyvi-%s" % ж
    git("fetch", "-q", "origin", "claude/zhyvi-%s" % ж)
    назв = змінено = 0
    for ф in [ф for ф in git("ls-tree", "-r", "--name-only", Г, ":/аудит/живі_%s/А" % ж).split("\n")
              if re.search(r"/1[123]_.*VIDPOVIDI/.*_мовний_шар\.txt$", ф)]:
        т = git("show", "%s:%s" % (Г, ф))
        з = т.split("── ВІДПОВІДЬ")[0]
        вх, ви = re.search(r"\[\s*\{.*\}\s*\]", з[з.rfind("\n["):], re.S), re.search(r"\{.*\}", т.split("── ВІДПОВІДЬ", 1)[-1], re.S)
        try:
            вх, ви = json.loads(вх.group(0)), json.loads(ви.group(0))
        except (AttributeError, ValueError):
            continue
        for о in вх if isinstance(вх, list) else []:
            м = re.match(r"([^a-zA-Z—\n]+?) — ", str(о.get("текст") or ""))
            if not м:
                continue
            назв += 1
            uk = str(ви.get(str(о.get("н"))) or "")
            if not uk.startswith(м.group(1)):
                змінено += 1
                print("Ж%s %s/%s: %r → %r" % (ж, ф.split("/")[-3][:2], ф.split("/")[-1][:8], м.group(1)[:50], uk.split(" — ")[0][:60]))
    print("Ж%s: назв крамниці перед « — » %d · у перекладі змінено %d" % (ж, назв, змінено))
