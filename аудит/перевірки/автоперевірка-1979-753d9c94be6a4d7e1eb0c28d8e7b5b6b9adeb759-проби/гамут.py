import sys, pathlib
sys.path.insert(0, str(pathlib.Path(sys.argv[1]) / "джерела"))
import bridge as М, palettes as П, colorspace as cs
зап = []
ориг = П.палітра_практична
П.палітра_практична = lambda *а, **к: (зап.append(ориг(*а, **к)) or зап[-1])
М.палітри(dict(шкіра=["#f1d0b5"], очі="#765336", волосся=["#16110e"], обхвати={}, зріст=168, самозвіт=dict(метал="срібло")))
for к in зап[0]["кольори"]:
    if к["hex"] in ("#b15c7c", "#f8ba87", "#003928"):
        вн = cs.lch(tuple(к["lab"])); hx = cs.lch(cs.hx(к["hex"]))
        print(к["hex"], к["назва"], "внутр LCh", [round(x, 1) for x in вн], "hex LCh", [round(x, 1) for x in hx])
