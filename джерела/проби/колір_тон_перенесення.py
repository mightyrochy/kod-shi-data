"""Звіряє перенесення тону з вхідною головою, фасадами й швом кола."""
import ast, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import colorspace as КП
import колір_простір_риси as РИСИ
import колір_тон as ТОН
def головна():
    """Звіряє AST, фасади, шов та власника опор кола."""
    БАЗА = "5fc912a01fe93e5c180422131ce6a6798c2b3c27"
    до = subprocess.check_output(["git", "show", БАЗА + ":джерела/колір_простір_риси.py"]).decode("utf-8")
    після = Path(ТОН.__file__).read_text(encoding="utf-8")
    вузли = lambda с: {getattr(в, "name", в.targets[0].id if isinstance(в, ast.Assign) else ""): в
                       for в in ast.parse(с).body if isinstance(в, (ast.FunctionDef, ast.Assign))}
    старі, нові = вузли(до), вузли(після)
    перенесені = [і for і in нові if і in старі]
    assert len(перенесені) == 12, перенесені
    for ім in перенесені:
        assert ast.dump(старі[ім]) == ast.dump(нові[ім]), ім
        assert getattr(РИСИ, ім) is getattr(ТОН, ім), ім
        if not ім.startswith("_"):
            assert getattr(КП, "_in_arc" if ім == "in_arc" else ім) is getattr(ТОН, ім), ім
    точки = [x / 10 for x in range(-7200, 7201)]
    точки += [h + d for h, _ in ТОН._КОЛО for d in (-1e-9, 0, 1e-9)]
    for h in точки:
        назад = ТОН.з_кола_художника(ТОН.у_коло_художника(h))
        assert abs((назад - h + 180) % 360 - 180) <= 0.050000001, h
    assert ТОН.тепло(None) is None
    опори = ТОН._КОЛО
    try:
        ТОН._КОЛО = ((0.0, 0.0), (180.0, 90.0))
        assert КП.у_коло_художника(180) == 90
        assert РИСИ.у_коло_художника(180) == 90
    finally:
        ТОН._КОЛО = опори
    print(f"AST: {len(перенесені)}/12; фасади: ті самі об'єкти; шов і обернення: {len(точки)} точок")

if __name__ == "__main__":
    головна()
