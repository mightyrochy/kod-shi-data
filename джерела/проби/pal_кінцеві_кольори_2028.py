"""Друкує силу кінцевої тріади через міст і звіряє координати з hex."""
import itertools
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import bridge as М
import colorspace as КС
import колір_річ as КР
import колір_відношення as КВ
import palettes as П


def головна():
    """Повторює доведений випадок в усіх трьох режимах насиченості."""
    факти = []
    for гама in ("середні", "приглушені", "насичені"):
        вхід = dict(шкіра=["#bb8561"], очі="#765336", волосся=["#70503b"],
                    обхвати={}, зріст=168, самозвіт=dict(метал="срібло"), вибір_кольору=dict(насиченість=гама))
        екран = json.loads(М.палітри(вхід))
        г = next(г for г in екран["гілки"] if г["схема"] == "тріада")
        кольори = [dict(lab=КС.hx(h)) for h in г["зразки"]]
        сили = [КВ.сила(КР.запис_кольору(а), КР.запис_кольору(б), "triadic")[0]
                for а, б in itertools.combinations(кольори, 2)]
        факти.append(dict(гама=гама, hex=г["зразки"], сили=сили))
    # Невірні внутрішні координати не мають впливати на оцінку кінцевих фішок.
    к = П.кінцевий_колір(dict(hex="#00422b", lab=(90, 70, 70), L=90, C=99, h=45))
    немає = П.поєднання_схеми(dict(кольори=[], вікна=dict(L=(20, 21))), "тріада") is None
    print(json.dumps(dict(тріади=факти, координати_з_hex=к["lab"] == КС.hx(к["hex"]), нема_незаконної=немає), ensure_ascii=False))
    return немає and к["lab"] == КС.hx(к["hex"]) and all(len(з["сили"]) == 3 and min(з["сили"]) >= 0.5 for з in факти)


if __name__ == "__main__":
    sys.exit(0 if головна() else 1)
