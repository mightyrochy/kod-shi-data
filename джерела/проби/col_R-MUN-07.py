# -*- coding: utf-8 -*-
"""R-MUN-07: стеля гамуту під СВОЇМ освітлювачем. Pointer 1980 заданий під C, модуль
рахує під D65. Друкує: (1) 8 вузлів корпусу — C* як опубліковано, після діагоналі XYZ
(форма `адаптувати`: тотожність) і після Bradford; (2) скільки кольорів каталогу міняють
вердикт `palette.здійсненність` проти стану ДО (8 сирих вузлів + sRGB на решті)."""
import sys, pathlib, json, math
_К = pathlib.Path(__file__).resolve().parent.parent; sys.path.insert(0, str(_К))
import colorspace as cs, palette as P, feed as Ф, bridge as B
ВІСІМ = [(90,130),(85,140),(60,330),(90,90),(20,50),(20,60),(20,90),(20,120)]
print("вузол        C*(під C)  XYZ-діаг  Bradford(D65)  клітинка")
for L, h in ВІСІМ:
    C = cs._POINTER_ВУЗЛИ_C[L][h // 10]
    lab = (L, C*math.cos(math.radians(h)), C*math.sin(math.radians(h)))
    x = cs.lch(cs.адаптувати_освітлювач(lab, метод="XYZ"))[1]
    b = cs.lch(cs.адаптувати_освітлювач(lab))
    print(f"L{L:2d} h{h:3d}      {C:5.1f}     {x:6.2f}    {b[1]:6.2f} (h{b[2]:5.1f})   {cs._POINTER_ВУЗЛИ[(L,h)]:6.2f}")
assert all(abs(cs.lch(cs.адаптувати_освітлювач((L, cs._POINTER_ВУЗЛИ_C[L][h//10], 0), метод="XYZ"))[1]
               - cs._POINTER_ВУЗЛИ_C[L][h//10]) < 0.01 for L, h in ВІСІМ), "діагональ XYZ мала б бути тотожністю"
СИРІ = {(L, h): float(cs._POINTER_ВУЗЛИ_C[L][h // 10]) for L, h in ВІСІМ}
def _до(L, h):                                   # стан до правки: 8 сирих вузлів, решта sRGB
    ключ = (int(round(L/5.0))*5, int(round((h % 360)/10.0))*10)
    return (СИРІ[ключ], "Pointer 1980 (виміряний вузол)") if ключ in СИРІ else (cs.c_max(L, h % 360), "sRGB — не витягнута")
вх = json.load(open(_К / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml"); вх["гілка"] = 0
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кольори = [cs.lch(c["lab"]) for c in B.каталог_останнього_пакета() if c.get("lab")]
def _вердикти(стеля):
    cs.c_max_поверхня, _ст = стеля, cs.c_max_поверхня
    try: return [P.здійсненність([L, L], (h - 1, h + 1), [C, C])["ok"] for L, C, h in кольори if C >= 2.0]
    finally: cs.c_max_поверхня = _ст
до, після = _вердикти(_до), _вердикти(cs.c_max_поверхня)
зм = sum(a != b for a, b in zip(до, після))
print(f"кольорів каталогу (C*≥2): {len(до)}; ok до: {sum(до)}, ok після: {sum(після)}; "
      f"вердикт змінили: {зм} ({100*зм/len(до):.1f} %) — з них ok→ні {sum(a and not b for a,b in zip(до,після))}, "
      f"ні→ok {sum(b and not a for a,b in zip(до,після))}")
джерела = {}
for L, C, h in кольори: джерела[cs.c_max_поверхня(L, h)[1][:12]] = джерела.get(cs.c_max_поверхня(L, h)[1][:12], 0) + 1
print("джерело стелі по кольорах каталогу:", джерела)
