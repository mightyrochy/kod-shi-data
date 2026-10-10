"""КАРТКА-СЛОВА (рядок 3660): сторож письма показу (`латинськіЗалишкиП`) на латиниці карток руки 3 ЖИВІ-14 №11 —
ДО (база c1b03ae2) і ПІСЛЯ; картка з самими вигаданими речами — `безСкорочень`, картка з крамницею — без нього.
Друкує знайдене. Запуск: cd джерела && python3 проби/латиниця_рук_3_4.py"""
import os, re, subprocess, json
ДЖ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ПРИКЛАДИ = [("сира індиго бавовна з легким вибілюванням 14oz.", True), ("водонепроникний нейлон та піна EVA.", True),
            ("латунь з покриттям 14k переробленого золота.", True), ("колготи 40 den, V-подібний виріз, сумка A4", True),
            ("крем SPF 30 і сукня 2XL", False), ("піна EVA", False),
            ("крем SPF 30 і сукня 2XL", True)]

def прогін(т):
    поч = т.index("const ЗАКОННА_ЛАТИНКА_П"); кін = т.index("/* ТЕКСТ ЧАТУ ПРОХОДИТЬ ТОЙ САМИЙ СТОРОЖ")
    код = re.search(r"function словаП\(т\)\{.*?\}\n", т).group(0) + т[поч:кін] + (
        "for (const [т, в] of %s){ const с = new Set(); if (в) с.безСкорочень = true;"
        " console.log(JSON.stringify(латинськіЗалишкиП(т, с))); }" % json.dumps(ПРИКЛАДИ, ensure_ascii=False))
    вих = subprocess.run(["node", "-e", код], capture_output=True, text=True)
    if вих.returncode:
        raise SystemExit("node: " + вих.stderr[-400:])
    return [json.loads(р) for р in вих.stdout.splitlines()]

до = прогін(subprocess.run(["git", "show", "c1b03ae2:джерела/показ.html"], cwd=ДЖ, capture_output=True,
                           text=True).stdout)
після = прогін(open(os.path.join(ДЖ, "показ.html"), encoding="utf-8").read())
for (текст, вигадані), д, п in zip(ПРИКЛАДИ, до, після):
    print("%-50s %-9s ДО %-12s ПІСЛЯ %s" % (текст, "руки 3–4" if вигадані else "крамниця", д or "чисто", п or "чисто"))
