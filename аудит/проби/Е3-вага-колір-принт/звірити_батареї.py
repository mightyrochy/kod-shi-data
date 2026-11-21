"""Звірити коди виходу проб і кожну записану вагу емітерів частини ДО/ПІСЛЯ."""
import collections
import itertools
import json
import pathlib
import sys


def main():
    """Перевірити тотожність трас та відокремити давні провали від нових."""
    тека = pathlib.Path(__file__).resolve().parent
    до = json.loads((тека / 'до-батарея.json').read_text(encoding='utf-8'))
    після = json.loads((тека / 'після-батарея.json').read_text(encoding='utf-8'))
    if not (до.get('завершено') and після.get('завершено')):
        факт = dict(стан='НЕ ВИМІРЯНО', чому='хоча б один прогін батареї не завершено',
                    до_завершено=до.get('завершено'), після_завершено=після.get('завершено'))
        (тека / 'звірка-батарей.json').write_text(json.dumps(факт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(факт, ensure_ascii=False))
        return 2
    коди_до, коди_після = dict(до['результати']), dict(після['результати'])
    спільні = коди_до.keys() & коди_після.keys()
    рядки_до = [з for з in до['записи'] if з[0] in спільні]
    рядки_після = [з for з in після['записи'] if з[0] in спільні]
    зміни = [[і, д, п] for і, (д, п) in enumerate(itertools.zip_longest(рядки_до, рядки_після)) if д != п]
    зміни_кодів = [[к, коди_до.get(к), коди_після.get(к)] for к in sorted(спільні)
                  if коди_до.get(к) != коди_після.get(к)]
    лічба = collections.Counter(з[2] for з in після['записи'])
    факт = dict(скриптів=len(коди_після), знахідок_до=len(до['записи']), знахідок_після=len(після['записи']),
                порівняно_до=len(рядки_до), порівняно_після=len(рядки_після),
                відсутні_після=sorted(коди_до.keys() - коди_після.keys()),
                змін_ваг=len(зміни), перші_відмінності=зміни[:5], зміни_кодів=зміни_кодів,
                правила=dict(лічба), провали_до=[з for з in до['результати'] if з[1]],
                провали_після=[з for з in після['результати'] if з[1]])
    (тека / 'звірка-батарей.json').write_text(json.dumps(факт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(факт, ensure_ascii=False))
    return 1 if зміни or зміни_кодів or факт['відсутні_після'] or факт['провали_після'] else 0


if __name__ == '__main__':
    sys.exit(main())
