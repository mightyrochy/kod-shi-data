"""Рядки 5885, 5315: зона мети в описі рук 1–2. Записи живого Г (`claude/zhyvi-1510-g`): ж4_робота_живіт, сіди 3–5 —
вхід опису (`ОПИС_V1`). ДО — промпт із запису: `case.goal_zones` є, правила поля нема; ПІСЛЯ — той самий обʼєкт через
`промпт_опису` цього коду: правило поля є. Кращим: ПІСЛЯ рядок «goal_zones» у task.input на кожному записі.
Запуск: cd джерела && python3 проби/опис_зона_5885.py (потрібна гілка `claude/zhyvi-1510-g`)."""
import json, re, subprocess, sys
sys.path.insert(0, "."); import розбір_відповідей as Р
git = lambda *а: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, text=True).stdout
git("fetch", "-q", "origin", "claude/zhyvi-1510-g:refs/remotes/origin/claude/zhyvi-1510-g")
ГІЛКА, ТЕКА = "origin/claude/zhyvi-1510-g", "аудит/живі_1510_Г/04_ж4_робота_живіт/VIDPOVIDI/"
файли = [l for l in git("ls-tree", "--full-tree", "--name-only", ГІЛКА, ТЕКА).split("\n") if "ОПИС_V1" in l]
правило = lambda вх: [x for x in вх["task"]["input"] if x.startswith('"goal_zones"')]
for ф in sorted(файли):
    текст = git("show", ГІЛКА + ":" + ф)
    вх = json.loads(re.search(r"^\{.*\}$", текст.partition("── ВІДПОВІДЬ")[0], re.M | re.S).group(0))
    ПІСЛЯ = (Р._ЗП.зібрати(Р.ОПИС, {к: v for к, v in вх.items() if к != "task"},
                                     мова_тексту=вх["task"].get("language")))
    print("%-50s case.goal_zones=%s | правило ДО: %d → ПІСЛЯ: %d" % (ф.rsplit("/", 1)[1][:50], вх.get("case", {}).get(
        "goal_zones", "—"), len(правило(вх)), len(правило(ПІСЛЯ))))
print("ПІСЛЯ, правило:", правило(ПІСЛЯ)[0][:160] if правило(ПІСЛЯ) else "—")
