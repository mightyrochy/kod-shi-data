"""Перелічує прямі читання hex поза модулями продукту без запуску їхнього коду."""
import ast
import json
from pathlib import Path


def main():
    """Зберігає вирази й контексти, щоб відділити типізовані входи від фіксованих точок."""
    корінь = Path(__file__).resolve().parents[3]
    джерела = корінь / "джерела"
    модулі = set()
    for вузол in ast.parse((джерела / "status.py").read_text("utf-8-sig")).body:
        if isinstance(вузол, ast.Assign) and any(
                isinstance(ціль, ast.Name) and ціль.id == "МОДУЛІ_ПРОДУКТУ" for ціль in вузол.targets):
            модулі = set(ast.literal_eval(вузол.value))
    шляхи = list(джерела.glob("*.py"))
    for тека in (джерела / "прилади", джерела / "проби", джерела / "лабораторія", корінь / "аудит/проби"):
        шляхи.extend(тека.rglob("*.py"))
    вихід = []
    for шлях in sorted(шляхи):
        if шлях.parent == джерела and шлях.stem in модулі:
            continue
        текст = шлях.read_text("utf-8-sig")
        рядки = текст.splitlines()
        дерево = ast.parse(текст)
        читання = [dict(рядок=в.lineno, вираз=ast.get_source_segment(текст, в),
                       контекст=рядки[max(0, в.lineno - 5):min(len(рядки), в.lineno + 2)])
                   for в in ast.walk(дерево) if isinstance(в, ast.Subscript)
                   and isinstance(в.slice, ast.Constant) and в.slice.value == "hex" and isinstance(в.ctx, ast.Load)]
        if читання:
            вихід.append(dict(файл=шлях.relative_to(корінь).as_posix(), читання=читання))
    (Path(__file__).parent / "читачі-hex.json").write_text(
        json.dumps(вихід, ensure_ascii=False, indent=2), "utf-8")
    print("Файлів:", len(вихід), "прямих читань hex:", sum(len(в["читання"]) for в in вихід))


if __name__ == "__main__":
    main()
