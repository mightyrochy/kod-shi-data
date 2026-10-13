"""Lapa після невдачі Mamay; виправлений код #991, незмінний валідатор."""
import pathlib,importlib.util,json
source=pathlib.Path('C:/Users/Admin/kod-shi-wt/fix-991/джерела/прилади/рядки_кольору_5190.py')
spec=importlib.util.spec_from_file_location('pilot991_repeat',source)
pilot=importlib.util.module_from_spec(spec); spec.loader.exec_module(pilot)
pilot.МОДЕЛЬ='lapa-v0.1.3-instruct'
out=pathlib.Path(__file__).with_name('повтор_lapa_3')
try:
 result=pilot.виконати(pilot.походження(pilot.підготувати(),None),out,4,лише_переклад=True)
 print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
except Exception as error:
 print('ЗБІЙ LAPA: '+str(error),flush=True)
 raise SystemExit(1)
