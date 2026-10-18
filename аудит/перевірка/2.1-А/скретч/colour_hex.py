import math
def lab(L, C, h):
    r = math.radians(h); return (L, C * math.cos(r), C * math.sin(r))
def з_lab(lab_):
    L, a, b = lab_
    fy = (L + 16) / 116; fx = fy + a / 500; fz = fy - b / 200
    f = lambda t: t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    X, Y, Z = 0.95047 * f(fx), 1.0 * f(fy), 1.08883 * f(fz)
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z; g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z; b_ = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    g_ = lambda c: 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(255 * g_(c)))) for c in (r, g, b_))
