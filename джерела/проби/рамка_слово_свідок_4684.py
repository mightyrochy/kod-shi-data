"""Рядок 4684: слово стилістки — свідок вибору тла (`річ_з_фото.виміряти`) — ДО (ref, типово 4ec81bf6) і ПІСЛЯ (тут), на фото крамниць.
Вхід: тека фото (`аудит/проби/огляд_крамниць.py` кладе їх у /tmp/фото_огляд). Сцени й правда — як `рамка_край_фото_проба.py`, плюс «рамка
зсунута на тло» (ЖИВІ-24 №06: рамка на 60 % ширини правіше речі, на річ лягає 40 %). Слово стилістки — слово правди («слово вірне») чи
слово іншої сім'ї («слово хибне»: чорний для світлої речі, білий для решти). Друкує по сцені: правильних (ΔE00 ≤ 10), хибних, без виміру.
Запуск: cd джерела && python3 проби/рамка_слово_свідок_4684.py /tmp/фото_огляд [ref]"""
import base64, collections, glob, os, subprocess, sys, types
from PIL import Image
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, Д)
import річ_з_фото as НОВ, colorspace as cs, verify as V
СТ = types.ModuleType("стара"); СТ.__file__ = os.path.join(Д, "річ_з_фото.py")
exec(subprocess.check_output(["git", "show", (sys.argv[2] if len(sys.argv) > 2 else "4ec81bf6") + ":джерела/річ_з_фото.py"]).decode(), СТ.__dict__)
def пікс(im, б, поле=.12):
    W, H = im.size; л, в, п, н = б; dx, dy = (п - л) * поле, (н - в) * поле; л2, в2, п2, н2 = max(0, л - dx), max(0, в - dy), min(1000, п + dx), min(1000, н + dy)
    c = im.crop([round(л2 / 1000 * W), round(в2 / 1000 * H), round(п2 / 1000 * W), round(н2 / 1000 * H)]); к = min(1, 128 / max(c.size))
    c = c.resize((max(1, round(c.width * к)), max(1, round(c.height * к))))
    return {"дані": base64.urlsafe_b64encode(c.tobytes()).decode(), "ширина": c.width, "висота": c.height, "ядро": {"ліво": round((л - л2) / (п2 - л2) * 1000),
            "верх": round((в - в2) / (н2 - в2) * 1000), "право": round((п - л2) / (п2 - л2) * 1000), "низ": round((н - в2) / (н2 - в2) * 1000)}}
рез = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*"))):
    try: im = Image.open(f).convert("RGB")
    except Exception: continue
    im.thumbnail((128, 128)); W, H = im.size
    w, h, rgb = НОВ.розпакувати({"дані": base64.urlsafe_b64encode(im.tobytes()).decode(), "ширина": W, "висота": H})
    m, ч, _ = НОВ.маска(rgb, w, h); смуга = [rgb[i] for i in НОВ._рамка_кадру(w, h)]; мед = tuple(НОВ._медіана([p[c] for p in смуга]) for c in range(3))
    if not (.03 < ч < .6 and sum(1 for p in смуга if sum((p[c] - мед[c]) ** 2 for c in range(3)) ** .5 < 28) / len(смуга) > .9): continue
    xs, ys = [i % w for i, v in enumerate(m) if v], [i // w for i, v in enumerate(m) if v]
    L, T, R, B = min(xs) / w * 1000, min(ys) / h * 1000, (max(xs) + 1) / w * 1000, (max(ys) + 1) / h * 1000
    правда = НОВ.виміряти(пікс(im, (L, T, R, B)))
    if not правда.get("lab"): continue
    хибне = "чорний" if правда["lab"][0] > 50 else "білий"
    for н, б in (("4 краї, щільна рамка", (L, T, R, B)), ("рамка в речі (3690)", (L + .05 * (R - L), T + .25 * (B - T), R - .25 * (R - L), B - .25 * (B - T))),
                 ("рамка в речі, низ до краю (4285)", (L + .25 * (R - L), T + .4 * (B - T), R - .25 * (R - L), 1000)), ("рамка зсунута на тло (4684)", (L + .6 * (R - L), T, R + .6 * (R - L), B))):
        if б[2] > 1000: continue
        for сл, слово in (("слово вірне", правда["слово"]), ("слово хибне", хибне)):
            for ім, мод in (("до", СТ), ("після", НОВ)):
                лаб = мод.виміряти(пікс(im, б), слово_моделі=слово).get("lab"); рез[(н, сл, ім)].append(None if not лаб else cs.de00(tuple(лаб), tuple(правда["lab"])))
for (н, сл, ім), v in sorted(рез.items()):
    ок = [x for x in v if x is not None]; print("%-34s %-11s %-5s n=%3d правильно %3d · хибно %3d · без виміру %3d" % (н, сл, ім, len(v), sum(x <= 10 for x in ок), sum(x > 10 for x in ок), len(v) - len(ок)))
