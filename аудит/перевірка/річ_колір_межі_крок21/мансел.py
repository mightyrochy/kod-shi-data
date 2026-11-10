"""Munsell (colour-science 0.4.6, Lab D65 → C Bradford) точок-аргументів «L,C,h» чи «#hex»: специфікація [H, V, C, код тону]
(6 YR, 7 R, 5 Y); помилка colour тут — лише відмова назви при C < 2, числа в ній і є точкою. Запуск з джерела/."""
import sys, warnings, math
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
import numpy as np, colour
from колір_простір_перетворення import lab_з_lch, hx
D65 = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["D65"]
C_ = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]["C"]
def мансел(lab):
    XYZ = colour.Lab_to_XYZ(np.array(lab), D65)
    XYZc = colour.adaptation.chromatic_adaptation_VonKries(XYZ, colour.xy_to_XYZ(D65), colour.xy_to_XYZ(C_), "Bradford")
    try:
        return colour.notation.munsell.xyY_to_munsell_colour(colour.XYZ_to_xyY(XYZc))
    except Exception as e:
        return "помилка: %s" % e
for арг in sys.argv[1:]:
    lab = hx(арг) if арг.startswith("#") else lab_з_lch(*map(float, арг.split(",")))
    print(арг, [round(x, 2) for x in lab], мансел(lab))
