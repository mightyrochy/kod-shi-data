"""ОЦІНКА-1000 (рядок 1111): колір речі з рамки, що торкається краю фото — ДО (голова пачки) і ПІСЛЯ (тут), на реальних фото.
Вхід: тека з фото крамниць (`аудит/проби/огляд_крамниць.py` кладе їх у /tmp/фото_огляд; будь-які jpg/png/webp).
Правда — колір речі на цілому фото з рівним тлом; сцени: рамка впирається в 1–4 краї або вирізана всередині речі (з полем на самій речі — рядок 3690; з трьох боків у речі, а
низом — за річ до краю фото, рядок 4285).
Друкує: з усіх фото сцени — скільки правильних (ΔE00 ≤ 10), хибних і без виміру."""
import base64, collections, glob, os, subprocess, sys, types
from PIL import Image
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, Д)
import річ_з_фото as НОВ, colorspace as cs
СТАРЕ = types.ModuleType("стара")
СТАРЕ.__dict__["__file__"] = os.path.join(Д, "річ_з_фото.py")
exec(subprocess.check_output(["git", "show", sys.argv[2] if len(sys.argv) > 2 else "origin/claude/pachka-1009-9:джерела/річ_з_фото.py"]).decode(), СТАРЕ.__dict__)
def пікс(im, б, поле=.12):
    W, H = im.size; л, в, п, н = б; dx, dy = (п - л) * поле, (н - в) * поле
    л2, в2, п2, н2 = max(0, л - dx), max(0, в - dy), min(1000, п + dx), min(1000, н + dy)
    c = im.crop([round(л2 / 1000 * W), round(в2 / 1000 * H), round(п2 / 1000 * W), round(н2 / 1000 * H)])
    к = min(1, 128 / max(c.size)); c = c.resize((max(1, round(c.width * к)), max(1, round(c.height * к))))
    return {"дані": base64.urlsafe_b64encode(c.tobytes()).decode(), "ширина": c.width, "висота": c.height,
            "ядро": {"ліво": round((л - л2) / (п2 - л2) * 1000), "верх": round((в - в2) / (н2 - в2) * 1000),
                     "право": round((п - л2) / (п2 - л2) * 1000), "низ": round((н - в2) / (н2 - в2) * 1000)}}
рез = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(sys.argv[1], "*"))):
    try: im = Image.open(f).convert("RGB")
    except Exception: continue
    im.thumbnail((128, 128)); W, H = im.size
    w, h, rgb = НОВ.розпакувати({"дані": base64.urlsafe_b64encode(im.tobytes()).decode(), "ширина": W, "висота": H})
    m, ч, _ = НОВ.маска(rgb, w, h); смуга = [rgb[i] for i in НОВ._рамка_кадру(w, h)]
    мед = tuple(НОВ._медіана([p[c] for p in смуга]) for c in range(3))
    if not (.03 < ч < .6 and sum(1 for p in смуга if sum((p[c] - мед[c]) ** 2 for c in range(3)) ** .5 < 28) / len(смуга) > .9): continue
    xs, ys = [i % w for i, v in enumerate(m) if v], [i // w for i, v in enumerate(m) if v]
    L, T, R, B = min(xs) / w * 1000, min(ys) / h * 1000, (max(xs) + 1) / w * 1000, (max(ys) + 1) / h * 1000
    правда = НОВ.виміряти(пікс(im, (L, T, R, B))).get("lab")
    if not правда: continue
    bw, bh = (R - L) / 1000 * W, (B - T) / 1000 * H; x0, y0, x1, y1 = L / 1000 * W, T / 1000 * H, R / 1000 * W + 1, B / 1000 * H + 1
    for н, (a, b, c_, d) in (("1 край (ліво)", (x0, 0, W, H)), ("2 краї (ліво, верх)", (x0, y0, W, H)), ("3 краї (ліво, верх, право)", (x0, y0, x1, H)),
                             ("4 краї, щільна рамка", (x0, y0, x1, y1)), ("зум у річ, низ — тло", (x0 + .12 * bw, y0 + .12 * bh, x1 - .12 * bw, y1 + .2 * bh)),
                             ("зум у річ, тла нема", (x0 + .12 * bw, y0 + .12 * bh, x1 - .12 * bw, y1 - .12 * bh)),
                             ("рамка в речі, тло лише зліва", (0, 0, W, H)), ("рамка в речі, за низом тло до краю фото", (0, 0, W, y1 + .1 * bh))):
        a, b, c_, d = int(a), int(b), min(W, int(c_)), min(H, int(d))
        if c_ - a < 8 or d - b < 8 or ("за низом" in н and y1 + .1 * bh > H): continue
        c = im.crop((a, b, c_, d)); cw, ch = c.size
        рамка = tuple(min(1000, max(0, v)) for v in ((L / 1000 * W - a) / cw * 1000, (T / 1000 * H - b) / ch * 1000, (R / 1000 * W - a) / cw * 1000, (B / 1000 * H - b) / ch * 1000))
        if "за низом" in н: рамка = (L + .25 * (R - L), (T + .4 * (B - T)) / 1000 * H / ch * 1000, R - .25 * (R - L), 1000)  # рядок 4285
        elif н.startswith("рамка в"): рамка = (L + .05 * (R - L), T + .25 * (B - T), R - .25 * (R - L), B - .25 * (B - T))  # рядок 3690
        if н.startswith("зум"): рамка = (0, 0, 1000, 1000 if "тла нема" in н else min(1000, (B / 1000 * H - b) / ch * 1000))
        for ім, мод in (("до", СТАРЕ), ("після", НОВ)):
            лаб = мод.виміряти(пікс(c, рамка)).get("lab"); рез[(н, ім)].append(None if not лаб else cs.de00(tuple(лаб), tuple(правда)))
for (н, ім), v in sorted(рез.items()):
    ок = [x for x in v if x is not None]; print("%-28s %-5s n=%3d правильно %3d · хибно %3d · без виміру %3d" % (н, ім, len(v), sum(x <= 10 for x in ок), sum(x > 10 for x in ок), len(v) - len(ок)))
