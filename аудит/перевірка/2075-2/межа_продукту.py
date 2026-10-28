"""Відтворює продуктовий обхід на незміненій функції з основи перевірки."""
import ast
import json
from pathlib import Path
import subprocess
import sys

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import приміряння as П


def головна():
    """Той самий вхід і залежності; ДО — точне тіло історичної функції."""
    база = "dd10cf82cd0dad262e39e87b30bc3e7c41f0dc39"
    текст = subprocess.check_output(["git", "show", база + ":джерела/приміряння.py"], cwd=КОРІНЬ).decode("utf-8-sig")
    вузол = next(в for в in ast.parse(текст).body if isinstance(в, ast.FunctionDef) and в.name == "опис_речі")
    простір = dict(vars(П))
    exec(compile(ast.Module(body=[вузол], type_ignores=[]), "приміряння.py@" + база, "exec"), простір)
    входи = [dict(слот="верх", назва="Річ", hex="#112233", lab=(20, 1, 2),
                  колір_тип=т, колір_не_вимір=dict(свідок="shop_word", вікно=(10, 50, 0, 30, (240, 310))))
             for т in ("інтервал", "невідомо", "вимір")]
    факти = [dict(тип=р["колір_тип"], ДО=простір["опис_речі"](р), ПІСЛЯ=П.опис_речі(р)) for р in входи]
    assert all("color_hex" in ф["ДО"] and "color_hex" not in ф["ПІСЛЯ"] for ф in факти[:2])
    assert факти[2]["ДО"] == факти[2]["ПІСЛЯ"]
    вихід = dict(база=база, метод="Історичне тіло функції, поточні незмінені залежності опису",
                 обхід_типу_ДО=2, обхід_типу_ПІСЛЯ=0, вимір_тотожний=True, факти=факти)
    (Path(__file__).parent / "межа-продукту.json").write_text(json.dumps(вихід, ensure_ascii=False, indent=2), "utf-8")
    print(json.dumps(вихід, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    головна()
