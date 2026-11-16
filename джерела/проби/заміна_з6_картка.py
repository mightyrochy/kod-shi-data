"""Е3 з6: той самий рядок ціни каблука ДО → ПІСЛЯ, без неперевіреної пари.

Виконує справжню гілку складання картки; кандидат добору — фікстура без суду образу.
"""
import ast, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import внутрішня_мова as М
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "0a57c69152e7dea68f951cb2bd61bf04152e4395"

def картка(текст):
    """Зібрати рядок картки з тією самою ціною й неперевіреним кандидатом."""
    гілка = next(в for в in ast.walk(ast.parse(текст)) if isinstance(в, ast.If)
                 and ast.unparse(в.test) == "_ціна and _чому")
    в = dict(в={}, _ціна=[dict(сила_нп=0.2)], _чому=М.заява("heel_cost_long_day"), _ВМ_в=М,
             сцен=dict(поверхня="бруківка", тривалість_год=9), пак={}, _вз=[], d={}, T={}, _рука_2=False,
             прогін_руки=None, змінна_пара=lambda *а, **к: (dict(id="кандидат_без_суду"), dict(кандидатів=1)))
    exec(compile(ast.Module(body=[гілка], type_ignores=[]), "картка", "exec"), в)
    return в["в"]["носіння_жінці"]

if __name__ == "__main__":
    шлях = pathlib.Path(__file__).resolve().parent.parent / "міст_відповіді.py"
    до = картка(subprocess.check_output(["git", "show", БАЗА + ":джерела/міст_відповіді.py"]).decode("utf-8"))
    після = картка(шлях.read_text(encoding="utf-8"))
    assert до["пара"]["id"] == "кандидат_без_суду" and "пара" not in після
    assert до["повідомлення"]["statements"][:2] == після["повідомлення"]["statements"]
    assert {к: до[к] for к in ("сила_нп", "поверхня", "тривалість_год")} == {
        к: після[к] for к in ("сила_нп", "поверхня", "тривалість_год")}
    print("ДО: неперевірена пара + flat_pair_removes_cost; ПІСЛЯ: 0 пар, ціна каблука та її вибір ті самі")
