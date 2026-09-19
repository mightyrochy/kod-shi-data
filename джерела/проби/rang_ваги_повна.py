# -*- coding: utf-8 -*-
"""A: чутливість бала на крок ΔE00≈5 по осях при повній надійності (spectro + три
картки + слово про барви) проти заявленої bases.ЦІНА_КРОКУ; контраст — обидва напрямки K-CLR-02."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import colorspace as cs, bases as ОС, outfit as _O, face_contrast as KC
вх = json.load(open("стенд_вх.json", encoding="utf-8"))
F = cs.features(cs.hx(вх["шкіра"]), cs.hx(вх["волосся"][0]), cs.hx(вх["очі"]))
к = _O.контраст_особи(F, "uncontrolled")
КОНТР = dict(щілина=к.get("value_gap"), value_gap=к.get("value_gap"), рівень=к.get("рівень"))
НАДІЙ = cs.reliability("spectro")
КАРТКИ = dict(метал="золото", нейтраль="теплі", білий="теплий")   # тепла людина
L_обл, ліміт = KC.value_обличчя(F), abs(float(КОНТР["value_gap"]))
def бал(lab):
    out, п = ОС.ранг(F, {"х": (cs.hex_з_lab(lab), "х")}, ["х"], самозвіт=КАРТКИ, барви="яскраві",
                      контраст=КОНТР, надійність=НАДІЙ, intent="conventional")
    return out[0]["бал"], п
def крок(lab0, f, ціль=5.0, lo=0.01, hi=60.0):
    for _ in range(40):
        m = (lo + hi) / 2; lo, hi = (m, hi) if cs.de00(lab0, f(m)) < ціль else (lo, m)
    return f((lo + hi) / 2)
C0, h0 = 28.0, math.radians(350.0)              # хрома над ціллю 22; тон трохи на холодному боці
def лаб(L, C, h): return (L, C * math.cos(h), C * math.sin(h))
L_пер, L_нед = L_обл - ліміт - 3.0, L_обл - ліміт + 3.0
проби = {
    "контраст_перевищення": (лаб(L_пер, C0, h0), lambda d: лаб(L_пер - d, C0, h0)),
    "контраст_недобір":     (лаб(L_нед, C0, h0), lambda d: лаб(L_нед + d, C0, h0)),
    "хрома":                (лаб(L_пер, C0, h0), lambda d: лаб(L_пер, C0 + d, h0)),
    "тон":                  (лаб(L_пер, C0, h0), lambda d: лаб(L_пер, C0, h0 - math.radians(d))),
}
Δ, п = {}, None
for ім, (lab0, f) in проби.items():
    б0, п = бал(lab0); б1, _ = бал(крок(lab0, f)); Δ[ім] = abs(б1 - б0)
оч = п["чутливість_ΔE00"]; впевн = п["стиснення"]["H"]
print("картки: %s; стиснення тону %.2f; крок ΔE00 = %.2f" % (п["температура"]["джерело"], впевн, оч["крок_ΔE00"]))
for ім in проби:
    print("  %-22s Δбал=%.4f  очікувано з рампи %.4f  розходження %3.0f%%"
          % (ім, Δ[ім], оч[ім] * 5, 100 * abs(Δ[ім] - оч[ім] * 5) / (оч[ім] * 5)))
ф = (Δ["контраст_перевищення"] / Δ["хрома"], Δ["контраст_недобір"] / Δ["хрома"], Δ["тон"] / Δ["хрома"] / впевн)
print("K(перевищ):C:H(без стиснення) = %.2f : 1 : %.2f  (заявлено 2.45 : 1 : 1.09); K(недобір) = %.2f (×%.2f, K-CLR-02)"
      % (ф[0], ф[2], ф[1], KC.ШТРАФ_НЕДОБОРУ / KC.ШТРАФ_ПЕРЕВИЩЕННЯ))
