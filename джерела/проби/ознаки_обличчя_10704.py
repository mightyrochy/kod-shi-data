"""Профілі записаних сцен: узгодженість довіри рангу, суду й пулу; зміна шуму фото."""
import copy, json, os, pathlib, sys
К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, os.environ.get("ОЗНАКИ_КОД", str(К)))
import bases, colorspace as cs, outfit, palette, personal_palette as PP, міст_вхід as МВ


def main():
    """Друкує ДО/ПІСЛЯ на тих самих профілях та повертає ненульовий код при розбіжності."""
    без = set(); розбіжності = рук = 0
    база = json.loads((К / "стенд_вх.json").read_text("utf8"))
    for шлях in sorted((К.parent / "аудит/проби/жінки").glob("*.json")):
        ж = json.loads(шлях.read_text("utf8"))
        for режим in ("uncontrolled", "protocolized", "spectro", "hex", "шум"):
            дж = режим if режим in cs.AXIS_RELIABILITY else "uncontrolled"
            вх = dict(база, шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source=дж)
            F = МВ.features(вх)[0] if режим != "hex" else cs.features(*map(cs.hx, (ж["skin"][0], ж["hair"][0], ж["eyes"])))
            if режим == "шум": F["шкіра"]["se_L"] = 4.0
            к = outfit.контраст_особи(F, дж); н = cs.reliability(дж)
            _, ранг = bases.ранг(F, {"чорний": ("#111111", "чорний")}, ["чорний"], контраст=к, надійність=н)
            пул = palette.специфікація(F, "тональна", ["верх", "низ", "взуття"], source=дж)
            палітра = PP.палітра(F, source=дж)
            for назва, вих in (("ранг", ранг), ("пул", пул), ("палітра", палітра)):
                if "ознаки_обличчя" not in вих: без.add(назва)
            вимір = ранг.get("ознаки_обличчя")
            над = вимір["надійність"]["contrast"] if вимір else н["contrast"]
            поз, дов, _ = bases.температура_людини(F, {}, н)
            розбіжності += abs(над - к["надійність_контрасту"]["надійність"]) > 1e-8
            розбіжності += bool(поз) and abs(дов / abs(поз) - палітра["родини"]["надійність_тону"]) > 1e-8
            if вимір:
                assert вимір is пул["ознаки_обличчя"] is палітра["ознаки_обличчя"]
                зм = copy.deepcopy(F); зм["шкіра"]["L"] -= 1
                assert outfit.контраст_особи(зм, дж) is not к
            рук += 1
    print("рук", рук, "· читачів без довіри", len(без), "· розбіжностей довіри", розбіжності)
    return int(bool(без or розбіжності))


if __name__ == "__main__":
    sys.exit(main())
