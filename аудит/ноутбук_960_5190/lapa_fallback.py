"""Дозволений у #960/6150404798 fallback після зафіксованої невдачі Mamay.

Протокол, raw, промпт і валідатор #991 незмінні. Лише ідентифікатор моделі
для запиту/перевірки/ключа кешу замінено у завантаженому модулі приладу.
Жодних змін продукту, ручного ремонту чи повтору кешу Mamay.
"""
import sys, pathlib, importlib.util, json
root=pathlib.Path(__file__).resolve().parents[2]
source=root/'джерела/прилади/рядки_кольору_5190.py'
spec=importlib.util.spec_from_file_location('pilot5190',source)
pilot=importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
pilot.МОДЕЛЬ='lapa-v0.1.3-instruct'
out=pathlib.Path(__file__).with_name('пілот_lapa')
try:
    result=pilot.виконати(pilot.походження(pilot.підготувати(),None),out,4,лише_переклад=True)
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
except Exception as error:
    print('ЗБІЙ LAPA: '+str(error),flush=True)
    raise SystemExit(1)
