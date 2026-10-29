"""Рядок 5840: вимір кольору покроково (`річ_з_фото.виміряти_кроками`) дає ТЕ САМЕ, що й `виміряти` ДО правки (ref, типово HEAD).
Фото — `аудит/фото_v2` (кожне в п'яти рамках: щільна, всередині речі, до краю фото, зсунута на тло, без рамки; слово вірне, хибне й без слова;
зі шкірою й без). Друкує: скільки вимірів збіглося побайтно (JSON усього виміру), скільки поступок і найдовший відрізок між ними (мс, CPython),
середній час виміру ДО і ПІСЛЯ. Запуск із `джерела`: python3 проби/вимір_кроками_5840.py [ref] [скільки фото]"""
import base64, glob, json, os, subprocess, sys, time, types
from PIL import Image
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, Д)
import річ_з_фото as НОВ
СТ = types.ModuleType("стара"); СТ.__file__ = os.path.join(Д, "річ_з_фото.py")
exec(subprocess.check_output(["git", "show", (sys.argv[1] if len(sys.argv) > 1 else "HEAD") + ":джерела/річ_з_фото.py"]).decode(), СТ.__dict__)
def пікс(im, б, поле=.12):
    W, H = im.size; л, в, п, н = б; dx, dy = (п - л) * поле, (н - в) * поле; л2, в2, п2, н2 = max(0, л - dx), max(0, в - dy), min(1000, п + dx), min(1000, н + dy)
    c = im.crop([round(л2 / 1000 * W), round(в2 / 1000 * H), round(п2 / 1000 * W), round(н2 / 1000 * H)]); к = min(1, 128 / max(c.size))
    c = c.resize((max(1, round(c.width * к)), max(1, round(c.height * к))))
    return {"дані": base64.urlsafe_b64encode(c.tobytes()).decode(), "ширина": c.width, "висота": c.height, "ядро": {"ліво": round((л - л2) / (п2 - л2) * 1000),
            "верх": round((в - в2) / (н2 - в2) * 1000), "право": round((п - л2) / (п2 - л2) * 1000), "низ": round((н - в2) / (н2 - в2) * 1000)}}
РАМКИ = ((150, 100, 850, 900), (300, 300, 650, 700), (250, 450, 750, 1000), (500, 100, 1000, 900))
збіг = разом = 0; відрізки = []; мс = [0.0, 0.0]; гілки = {}
for f in sorted(glob.glob(os.path.join(Д, "аудит", "фото_v2", "*")))[:int(sys.argv[2]) if len(sys.argv) > 2 else 60]:
    im = Image.open(f).convert("RGB")
    for б in РАМКИ + (None,):
        п = пікс(im, б) if б else dict(пікс(im, (0, 0, 1000, 1000)), ядро=None)
        for слово, шкіра, рамка in ((None, None, б), ("чорний", "#deb295", б), ("білий", None, None)):
            t = time.perf_counter(); до = json.dumps(СТ.виміряти(п, слово, шкіра, рамка), sort_keys=True, ensure_ascii=False); мс[0] += time.perf_counter() - t
            г = НОВ.виміряти_кроками(п, слово, шкіра, рамка); t0 = time.perf_counter(); t = t0; після = None
            while після is None:
                try: next(г)
                except StopIteration as к: після = json.dumps(к.value, sort_keys=True, ensure_ascii=False)
                відрізки.append((time.perf_counter() - t) * 1000); t = time.perf_counter()
            мс[1] += t - t0 + 0; разом += 1; збіг += до == після; гілки[json.loads(після).get("гілка")] = гілки.get(json.loads(після).get("гілка"), 0) + 1
print("вимірів %d · побайтно однакових %d · гілки %s" % (разом, збіг, гілки))
print("поступок %d · найдовший відрізок %.0f мс · p99 %.0f мс · середній вимір ДО %.0f мс, ПІСЛЯ %.0f мс (CPython)" % (
    len(відрізки), max(відрізки), sorted(відрізки)[int(len(відрізки) * .99)], 1000 * мс[0] / разом, 1000 * мс[1] / разом))
