"""Лічба ділянки паспорта; аргумент — корінь версії, яку вимірюємо."""
import ast
import json
import re
import sys
from pathlib import Path

корінь = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
дж = корінь / 'джерела'
sys.path.insert(0, str(дж))
import паспорт_поля as поля
import паспорт_нагоди as п
import картка_запиту as к
import внутрішня_мова as м
import сценарій as с

обходи = []
текст = (дж / 'паспорт_нагоди.py').read_text(encoding='utf8')
функція = next(в for в in ast.parse(текст).body if isinstance(в, ast.FunctionDef) and в.name == 'паспорт_з_json')
for в in ast.walk(функція):
    if isinstance(в, ast.Return) and isinstance(в.value, ast.Name) and в.value.id == 'п':
        обходи.append(f'джерела/паспорт_нагоди.py:{в.lineno}')
for файл in sorted((дж / 'показ').glob('*.js')):
    for н, рядок in enumerate(файл.read_text(encoding='utf8').splitlines(), 1):
        if re.search(r'(?:КАРТКА_ЗАПИТУ_П|картка)\[поле\]\s*=\s*\{значення', рядок):
            обходи.append(f'джерела/показ/{файл.name}:{н}')

опис = поля.ПОЛЯ_ПАСПОРТА
проєкції = [п.СХЕМА_ПАСПОРТА == {к: в['схема'](п._КОНТЕКСТ_СХЕМИ) for к, в in опис.items() if 'схема' in в},
             с.ПОЛЯ == {к: в['сценарій'] for к, в in опис.items() if 'сценарій' in в},
             м.СЦЕНАРІЙ == {в['поле']: в['мова'](м._КОНТЕКСТ_ПОЛІВ) for в in опис.values() if 'мова' in в},
             json.loads((дж / 'внутрішня_мова.schema.json').read_text(encoding='utf8')) == м.схема(),
             п.довідник()['поля_паспорта'] == поля.поля_показу()]
паспорт = {}
к.записати(паспорт, 'місце', 'парк', 'her', 'у парку')
к.записати(паспорт, 'місце', 'офіс', 'hand')
старий_уривок = bool(к.факт(паспорт, 'місце').get('уривок'))
після_помилки = п.паспорт_з_json('', {}, '', паспорт_досі=паспорт)
втрата = к.факт(після_помилки, 'місце') != к.факт(паспорт, 'місце')
print(json.dumps(dict(описів=1, проєкцій=len(проєкції), розбіжностей_проєкцій=проєкції.count(False),
                     обходів=len(обходи), місця=обходи, чужий_уривок=int(старий_уривок),
                     втрата_при_помилці=int(втрата)), ensure_ascii=False, indent=1))
