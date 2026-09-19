# -*- coding: utf-8 -*-
"""П.2: фактичне співвідношення чутливостей бала (контраст/хрома/тон) до
однакового кроку ΔE00, проти заявленого 2.45:1:1.09 (bases.py:180-195)."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import colorspace as cs, bases as ОС, outfit as _O, palette as П, face_contrast as KC
вх = json.load(open("стенд_вх.json", encoding="utf-8"))
F = cs.features(cs.hx(вх["шкіра"]), cs.hx(вх["волосся"][0]), cs.hx(вх["очі"]))
к = _O.контраст_особи(F, "uncontrolled")
КОНТР = dict(щілина=к.get("value_gap"), value_gap=к.get("value_gap"), рівень=к.get("рівень"))
НАДІЙ = П.reliability("uncontrolled")
L_обл = KC.value_обличчя(F)
# база на межі чутливості контрасту (факт=ліміт) і хроми (C0 біля цілі 12)
L0, C0, h0 = L_обл - 12.3, 17.0, math.radians(40)
a0, b0 = C0 * math.cos(h0), C0 * math.sin(h0)
ЦІЛЬ_ΔE = 5.0
def лаб(L, C, h): return (L, C * math.cos(h), C * math.sin(h))
def знайти(f_lab, лоу=0.01, хай=45.0):
    for _ in range(40):
        сер = (лоу + хай) / 2
        if cs.de00((L0, a0, b0), f_lab(сер)) < ЦІЛЬ_ΔE: лоу = сер
        else: хай = сер
    return f_lab((лоу + хай) / 2)
_L = знайти(lambda d: лаб(L0 + d, C0, h0))
_C = знайти(lambda d: лаб(L0, C0 + d, h0))
_H = знайти(lambda d: лаб(L0, C0, h0 + math.radians(d)))
def бал(lab, ключ="х"):
    out, _ = ОС.ранг(F, {ключ: (cs.hex_з_lab(lab), ключ)}, [ключ],
                     контраст=КОНТР, надійність=НАДІЙ, intent="conventional")
    return out[0]["бал"]
б0 = бал((L0, a0, b0)); б_L = бал(_L); б_C = бал(_C); б_H = бал(_H)
d = dict(контраст=abs(б_L - б0), chroma=abs(б_C - б0), hue=abs(б_H - б0))
print("ΔE00 кроку ≈%.2f, бал база=%.3f" % (cs.de00((L0, a0, b0), _L), б0))
print("Δбал: контраст(L)=%.4f  chroma(C)=%.4f  hue(H)=%.4f" % (d["контраст"], d["chroma"], d["hue"]))
база_c = d["chroma"] or 1e-9
факт = tuple(round(d[k] / база_c, 2) for k in ("контраст", "chroma", "hue"))
print("фактичне K:C:H = %.2f : %.2f : %.2f (заявлено 2.45 : 1 : 1.09)" % факт)
for н, р, з in (("K", факт[0], 2.45), ("H", факт[2], 1.09)):
    print("  %s: розходження %.0f%%" % (н, 100 * abs(р - з) / з))
