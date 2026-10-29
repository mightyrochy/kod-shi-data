# -*- coding: utf-8 -*-
"""Рядки 6217, 6218: ПИТАННЯ стилістки — replay записів ж15 кодом БАЗИ (ДО) і робочого дерева (ПІСЛЯ).
Друкує: скільки записаних відповідей прочитав `прийняти`; чи `міст_помічниця.ДОВІДКА` байт у байт та сама;
розмір промпту на виклик — ДО (записи), ПІСЛЯ кодом (ті самі питання, речі й «case» записів через новий
`ПИТАННЯ`: речі — як їх дає `_річ`, без означень, ід латинкою; паспорта в записах нема, тож «case» — рядок
запису) і ПІСЛЯ сцени (записи replay сцени, коли тека дана); кирилицю коду в «case» (поза її словами) й в ідах.
Запуск: cd джерела && python3 проби/промпти3_стилістка.py <тека ДО> [<тека replay сцени>] [БАЗА=origin/main]"""
import glob, json, os, re, subprocess, sys, tarfile, io, tempfile; sys.path.insert(0, os.getcwd())
import міст_стилістка as МС, збирач_промптів as ЗП, оцінка_образу as ОО
ДО, СЦЕНА, БАЗА = (sys.argv[1:] + [None, "origin/main"][len(sys.argv) - 2:])[:3]
кир = lambda s: len(re.findall(r"[А-Яа-яІіЇїЄєҐґ]", json.dumps(s, ensure_ascii=False)))
ЇЇ = ("event", "her_words", "goal_quote", "intent_quote", "her_other_words", "beliefs", "mood")  # її слова
def записи(тека):
    for ф in sorted(glob.glob(os.path.join(тека, "**", "*стилістка_питання_про_образ.txt"), recursive=True)):
        г = re.match(r"── ПРОМПТ \(\d+ симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ \([^\n]*\) ──\n(.*)\n$", open(ф, encoding="utf8").read(), re.S)
        yield json.loads(г.group(1).strip()), г.group(2).strip()
def лічба(дані, назва):
    case = sum(кир(д["case"]) if isinstance(д.get("case"), str) else
               sum(кир(v) for к, v in (д.get("case") or {}).items() if к not in ЇЇ) for д in дані)
    іди = sum(кир([[р.get("id"), р.get("photo")] for р in д.get("items", [])] + [д.get("photos")]) for д in дані)
    print("%-12s %2d викл. · %d симв. на виклик · кирилиця коду в «case» %d · в ідах %d" % (назва, len(дані),
          round(sum(len(json.dumps(д, ensure_ascii=False)) for д in дані) / max(len(дані), 1)), case, іди))
def новий(д):
    р_ = lambda р: dict(р, id=ОО.ід_на_дріт(р["id"]), **({"photo": ОО.ід_на_дріт(р["photo"])} if р.get("photo") else {}),
                        **({"verdict": {"statements": р["verdict"]["statements"]}} if р.get("verdict") else {}))
    return ЗП.зібрати(МС.ПИТАННЯ, dict(question=д["question"], items=[р_(р) for р in д.get("items", [])], case=д.get("case"),
                      photos=[{к: ОО.ід_на_дріт(v) for к, v in ф.items()} for ф in д.get("photos", [])]), д["task"]["language"])
тмп = tempfile.mkdtemp()  # БАЗА — архівом у тимчасову теку: її `прийняти` і її ДОВІДКА
tarfile.open(fileobj=io.BytesIO(subprocess.run(["git", "archive", БАЗА, "."], capture_output=True, check=True).stdout)).extractall(тмп, filter="data")
ДОВІДКА = ("import json,міст_помічниця as М,міст_стилістка as С;print(json.dumps([М.промпт('як зберегти?','APP',"
           "{'екран':'профіль'},[{'хто':'людина','текст':'привіт'}],'English')]+[С.прийняти(в)['відповідь'] for в in json.load(open(%r))]))")
з = list(записи(ДО)); json.dump([в for _, в in з], open(os.path.join(тмп, "в.json"), "w"))
база, тут = (json.loads(subprocess.run([sys.executable, "-c", ДОВІДКА % os.path.join(тмп, "в.json")], cwd=к,
                                       capture_output=True, text=True, check=True).stdout) for к in (тмп, "."))
print("відповідей ж15: %d · прочитано ДО (%s) %d → ПІСЛЯ %d" % (len(з), БАЗА, sum(map(bool, база[1:])), sum(map(bool, тут[1:]))))
print("ДОВІДКА (міст_помічниця) байт у байт та сама: %s (%d симв.)" % (база[0] == тут[0], len(тут[0])))
лічба([д for д, _ in з], "ДО"); лічба([новий(д) for д, _ in з], "ПІСЛЯ кодом")
if СЦЕНА:
    лічба([д for д, _ in записи(СЦЕНА)], "ПІСЛЯ сцени")
