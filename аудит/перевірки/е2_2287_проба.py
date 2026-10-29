"""Відтворити прицільні спостереження перевірки PR #2287 на заданому дереві."""
import ast
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace


def main():
    """Прочитати незмінений прилад і перевірити його детектори без запуску моделей."""
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    spec = importlib.util.spec_from_file_location(
        'е2_2287', root / 'джерела/прилади/корінь_е2_межі.py')
    instrument = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(instrument)
    instrument.ДЖЕРЕЛА = str(root / 'джерела')
    instrument.ПОКАЗ = str(root / 'джерела/показ')
    instrument.КОРІНЬ = str(root)
    modules = instrument.модулі_продукту()
    indexed = {name: instrument.Модуль(name, tree) for name, tree in modules.items()}
    notes = instrument.Структура(SimpleNamespace(м=indexed)).нотатки()
    for module, function, line, reason in sorted(notes):
        if module == 'міст_відповіді' and function == '_злити_частини':
            print(f'{module}.py:{line} · п.4 · {reason}')

    # Відомий приклад паспорта: детектор бачить читання години в її уривку.
    analysis = instrument.Аналіз(
        {'картка_запиту': modules['картка_запиту']}, set(), {'уривок'}, {}).виконати()
    hours = sorted((event['рядок'], event['дія']) for event in analysis.події.values()
                   if event['функція'] == '_число_години' and event['вид'] == 'слова')
    print('Година, події п.7:', hours)

    # Штучна проба можливості детектора; це не знайдене місце продукту.
    example = ast.parse('def вибір(уривок):\n    return "вечір" in уривок\n')
    analysis = instrument.Аналіз({'приклад': example}, set(), {'уривок'}, {}).виконати()
    print('Штучна проба порівняння, подій:', len(analysis.події))
    print('Модулів Python в області:', len(modules))
    return 0


if __name__ == '__main__':
    sys.exit(main())
