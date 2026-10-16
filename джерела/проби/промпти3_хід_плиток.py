"""ПРОМПТИ-3 (рядок 6185): хід плиток — своє оголошення (`мовний_шар.ХІД_ПЛИТОК`) замість повного промпту розмови.
(1) Розмір промпту ходу «плитка Робота, порожній паспорт»: ДО — `мовний_шар` з `origin/main`, ПІСЛЯ — цей.
(2) Replay 15 записаних ходів плиток живої пачки 15 (`claude/zhyvi-pachka-15`, `her_new_message: unknown`): що модель
написала в `update` (ДО) і що бере код — ДО `прийняти_розмову`, ПІСЛЯ `прийняти_хід_плиток` (лише 4 поля норми).
Кращим: ПІСЛЯ промпт менший, event/place_words/occasion/invite взято 0, formality — стільки ж, скільки ДО.
Запуск: cd джерела && python3 проби/промпти3_хід_плиток.py"""
import importlib.util, json, os, re, subprocess, sys, tempfile
sys.path.insert(0, "."); import мовний_шар as Н
Г = "origin/claude/zhyvi-pachka-15"
git = lambda *а, **к: subprocess.run(["git", "-c", "core.quotepath=false", *а], capture_output=True, **к).stdout
git("fetch", "-q", "origin", "claude/zhyvi-pachka-15:refs/remotes/" + Г)
ш = os.path.join(tempfile.mkdtemp(), "мш_main.py"); open(ш, "wb").write(git("show", "origin/main:джерела/мовний_шар.py"))
сп = importlib.util.spec_from_file_location("мш_main", ш); С = importlib.util.module_from_spec(сп); сп.loader.exec_module(С)
d = {"розмова": {"нове": "", "історія": []}, "сценарій": {"нагода": "робота"}}
до, після = len(С.промпт_розмови(d)), len(Н.промпт_розмови(d))
print("хід «плитка Робота», порожній паспорт: %d → %d симв. (%+.0f %%)" % (до, після, 100.0 * (після - до) / до))
імена = [і for і in git("ls-tree", "-r", "--name-only", Г, "../аудит/живі_пачка_15").decode().split("\n")
         if і.endswith("_хід_розмови.txt")]
записи = re.split(rb"(?m)^[0-9a-f]{40} blob \d+\n", git("cat-file", "--batch", input="".join(
    "%s:%s\n" % (Г, і) for і in імена).encode()))[1:]
ПОЛЯ = ("event", "place_words", "occasion", "invite", "formality")
лік = {к: [0, 0, 0] for к in ПОЛЯ}; ходів = однакова = поза = 0
for з in записи:
    т = з.decode("utf-8", "replace")
    if '"her_new_message": "unknown"' not in т.split("── ВІДПОВІДЬ")[0]:
        continue
    відп = т.split("── ВІДПОВІДЬ", 1)[1].split("──\n", 1)[1]
    об, _ = Н._обʼєкт(відп); об = об if isinstance(об, dict) else {}
    сире = dict(об.get("update") or {}, **({"invite": 1} if (об.get("invite") or "").strip() else {}))
    було, стало = С.прийняти_розмову(відп)["внутрішня"], Н.прийняти_хід_плиток(відп)["внутрішня"]
    ходів += 1; однакова += було.get("formality") == стало.get("formality")
    поза += len(set(стало) - set(Н.ПОЛЯ_ХОДУ_ПЛИТОК))
    for к in ПОЛЯ:
        лік[к] = [лік[к][0] + (к in сире), лік[к][1] + (к in було), лік[к][2] + (к in стало)]
print("ходів плиток: %d · поле: у відповіді моделі / взято ДО / взято ПІСЛЯ" % ходів)
for к, (а, б, в) in лік.items():
    print("  %-11s %2d/%d · %2d · %2d" % (к, а, ходів, б, в))
print("formality ПІСЛЯ = ДО: %d з %d · полів ПІСЛЯ поза нормою: %d" % (однакова, ходів, поза))
