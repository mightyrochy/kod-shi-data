"""Перевіряє походження повернень та незалежний зворотний пошук без продукту."""
import ast
import json
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела/прилади'))
from корінь_річ_кадр_маршрути import Граф
from корінь_річ_кадр_варіант import розібрати_python


def перевірити(назва, тексти, очікується=True):
    """Порівнює досяжність споживача з двох протилежних напрямків."""
    граф = Граф(тексти)
    споживачі = {к for к, в in граф.точки.items() if isinstance(в, ast.Assign)
                  and any(isinstance(ц, ast.Name) and ц.id == 'запис' for ц in в.targets)}
    assert споживачі, назва
    прямий = граф.від_джерел()
    зворотний = граф.від_споживачів(споживачі)
    а = bool(споживачі & прямий.keys())
    б = bool(граф.входи & зворотний.keys())
    assert а == б == очікується, (назва, а, б, очікується)
    # Кожне ребро доказу існує в графі, початок прямого доказу — справжній вхід.
    докази = []
    for к in sorted(споживачі & прямий.keys()):
        шлях = граф.маршрут(прямий, к)
        assert шлях[-1] in граф.входи
        assert all(до in граф.ребра[від] for до, від in zip(шлях, шлях[1:]))
        докази.append(шлях)
    return dict(проба=назва, пройдено=True, звязаних_викликів=len(граф.звязані_виклики),
                джерел=len(граф.входи), є_маршрут=а, докази=докази)


def main():
    """Друкує відтворюваний JSON проб механізму та реального пропуску галереї."""
    випадки = [
        ('повернення списку після append', {'a.py': '''
def узяти(ел):
    вих = []
    v = ел.get("data-hex")
    вих.append(v)
    return вих
запис = dict(колір=узяти(ел))
'''}),
        ('вхід у тілі без повернення даних', {'a.py': '''
def узяти(ел):
    v = ел.get("data-hex")
    return "стала"
запис = dict(колір=узяти(ел))
'''}, False),
        ('аргумент не впливає на повернення', {'a.py': '''
def стала(x):
    return "стала"
запис = dict(колір=стала(ел.get("data-hex")))
'''}, False),
        ('параметр впливає на повернення', {'a.py': '''
def передати(x):
    return x
запис = dict(колір=передати(ел.get("data-hex")))
'''}),
        ('ключовий аргумент', {'a.py': '''
def передати(*, x):
    return x
запис = dict(колір=передати(x=ел.get("data-hex")))
'''}),
        ('імпорт із псевдонімом', {'src.py': '''
def узяти(ел):
    return ел.get("data-hex")
''', 'sink.py': '''
from src import узяти as зняти
запис = dict(колір=зняти(ел))
'''}),
        ('реекспорт фасадом', {'src.py': '''
def узяти(ел):
    return ел.get("src")
''', 'facade.py': 'from src import узяти as кадр',
         'sink.py': 'import facade as ф\nзапис = dict(фото=ф.кадр(ел))'}),
        ('однойменні функції різних модулів', {'src.py': '''
def узяти(ел):
    return ел.get("data-hex")
''', 'sink.py': '''
def узяти(ел):
    return "стала"
запис = dict(колір=узяти(ел))
'''}, False),
        ('вкладена область не змішується із сусідньою', {'a.py': '''
def перша():
    x = ел.get("data-hex")
    return x
def друга():
    x = "стала"
    return x
запис = dict(колір=друга())
'''}, False),
        ('замикання читає зовнішню змінну', {'a.py': '''
def зовнішня():
    x = ел.get("data-hex")
    def внутрішня():
        return x
    return внутрішня()
запис = dict(колір=зовнішня())
'''}),
        ('глобальна змінна', {'a.py': '''
x = ел.get("data-hex")
def узяти():
    return x
запис = dict(колір=узяти())
'''}),
        ('типовий параметр', {'a.py': '''
def узяти(x=ел.get("data-hex")):
    return x
запис = dict(колір=узяти())
'''}),
        ('цикл викликів завершується', {'a.py': '''
def а(x):
    return б(x)
def б(x):
    return а(x) or ел.get("src")
запис = dict(фото=а(None))
'''}),
    ]
    результати = [перевірити(*в) for в in випадки]
    текст = (КОРІНЬ / 'zhnyvarka/жниварка.py').read_text(encoding='utf-8-sig')
    дерево = ast.parse(текст)
    виклик = next(в for в in ast.walk(дерево) if isinstance(в, ast.Assign)
                   and isinstance(в.value, ast.Call) and isinstance(в.value.func, ast.Name)
                   and в.value.func.id == '_адреси_картинок')
    а, б = розібрати_python(текст)
    assert any(т[1] == виклик.lineno for т in а)
    результати.append(dict(проба='реальний виклик галереї', пройдено=True,
                            файл='zhnyvarka/жниварка.py', рядок=виклик.lineno))
    print(json.dumps(результати, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
