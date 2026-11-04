"""Повторює незмінений розділ 117 батареї з його власними межами часу й перевіркою побічних файлів."""
import ast, importlib.util, json, sys
from pathlib import Path

def main():
    """Завантажує батарею без запуску main і виконує її розділ 117 без зміни тверджень."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    шлях = корінь / "джерела/прилади/розділи_гейтів.py"
    схема = importlib.util.spec_from_file_location("_повтор_гейтів", шлях)
    модуль = importlib.util.module_from_spec(схема)
    схема.loader.exec_module(модуль)
    вузли = next(в for в in ast.parse(шлях.read_text(encoding="utf-8")).body
                 if isinstance(в, ast.FunctionDef) and в.name == "main").body
    def початок(номер):
        """Знаходить межу розділу за його друкованим заголовком."""
        return next(і for і, в in enumerate(вузли) if isinstance(в, ast.Expr)
                    and isinstance(в.value, ast.Call) and isinstance(в.value.func, ast.Name)
                    and в.value.func.id == "print" and в.value.args
                    and isinstance(в.value.args[0], ast.Constant)
                    and str(в.value.args[0].value).startswith(str(номер) + "."))
    тіло = ast.Module(body=вузли[початок(117):початок(118)], type_ignores=[])
    exec(compile(тіло, str(шлях), "exec"), модуль.__dict__)
    звіт = dict(імпорти=модуль._звіт117, пройдено=модуль.ok, впало=модуль.збої,
                без_входу=модуль.пропущено)
    (тека / "гейти_117_повтор.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(звіт, ensure_ascii=False))
    return bool(модуль.збої or модуль.пропущено)

if __name__ == "__main__":
    sys.exit(main())
