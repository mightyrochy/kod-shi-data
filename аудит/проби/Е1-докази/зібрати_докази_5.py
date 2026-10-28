"""Збирає закінчені браузерні докази й звіряє свіжу збірку із записаною."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys


def зібрати():
    """Копіює журнали завершених проб, зберігаючи також перший провал закриття браузера."""
    запуск, стара_збірка = map(lambda п: Path(п).resolve(), sys.argv[1:])
    тут = Path(__file__).parent
    перші = запуск / 'браузерні-докази'
    повтор = запуск / 'застарілий-після'
    звіт = json.loads((перші / 'браузерні-5.json').read_text(encoding='utf-8'))
    звіт += json.loads((повтор / 'браузерні-5.json').read_text(encoding='utf-8'))
    assert [(р['проба'], р['rc_приймання']) for р in звіт] == [('база', 0), ('регрес', 1), ('застарілий', 0)]
    (тут / 'браузерні-5.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for назва, корінь in [('база', перші), ('регрес', перші), ('застарілий', повтор), ('застарілий-ДО', перші)]:
        джерело = корінь / ('застарілий' if назва == 'застарілий-ДО' else назва)
        сцена = next((джерело / 'результат').glob('аудит_*'))
        shutil.copyfile(сцена / 'лог.txt', тут / (назва + '-5.log'))
        for ім in ('доказ.json', 'помилка_відтворення.json'):
            файл = сцена / 'знімки' / ім
            if файл.exists():
                shutil.copyfile(файл, тут / (назва + '-5-' + ім))
        if назва != 'застарілий-ДО':
            shutil.copyfile(сцена / 'звірки.json', тут / (назва + '-5-звірки.json'))
        if назва == 'база':
            shutil.copyfile(сцена / 'main/лог.txt', тут / 'база-main-5.log')
    файли = [стара_збірка / 'index.html', запуск / 'збірка/index.html']
    нормалізовані = []
    збірки = []
    for файл in файли:
        html = файл.read_text(encoding='utf-8')
        м = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)
        assert м
        збірки.append(м[1])
        нормалізовані.append(html[:м.start(1)] + '<SHA збірки>' + html[м.end(1):])
    assert нормалізовані[0] == нормалізовані[1], 'Відрізняється код чи каталог збірок'
    тотожність = {'збірки': збірки, 'відрізняється': 'лише штамп SHA checkout',
                 'sha256_нормалізованої_сторінки': hashlib.sha256(нормалізовані[0].encode()).hexdigest()}
    (тут / 'тотожність-збірок-5.json').write_text(json.dumps(тотожність, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({'браузерні': звіт, 'тотожність': тотожність}, ensure_ascii=False))


if __name__ == '__main__':
    зібрати()
