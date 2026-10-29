"""Вимикає історичне доповнення аналогової та звіряє всі початкові короткі брифи."""
import ast
import gzip
import importlib.util
import json
import pathlib
import sys
import tempfile

КОРІНЬ = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'аудит/проби'))
from кольори_2028_3_причини import дослід, байти
import bridge as М


def головна():
    """Окремо доводить причину 35 доповнених персон перемикачем у тимчасовій копії."""
    читати = lambda п: json.loads(gzip.decompress(п.read_bytes()))
    історія = читати(КОРІНЬ / 'аудит/перевірка/кольори_9858/доробка/персони.json.gz')
    причинні = читати(pathlib.Path(__file__).with_name('причини.json.gz'))
    текст = дослід((КОРІНЬ / 'джерела/palettes.py').read_text(encoding='utf-8'), 0, 0, 0)
    дерево = ast.parse(текст)
    функція = next(ф for ф in дерево.body if isinstance(ф, ast.FunctionDef) and ф.name == 'поєднання')
    цикли = [в for в in ast.walk(функція) if isinstance(в, ast.For) and isinstance(в.target, ast.Name)
             and в.target.id == 'схема']
    assert len(цикли) == 1
    цикли[0].body.insert(0, ast.parse('if схема == "аналогова":\n    continue').body[0])
    записи = []
    with tempfile.TemporaryDirectory(prefix='kolory-2028-3-completion-') as тека:
        файл = pathlib.Path(тека) / 'palettes.py'
        файл.write_text(ast.unparse(дерево), encoding='utf-8')
        спец = importlib.util.spec_from_file_location('без_доповнення', файл)
        П = importlib.util.module_from_spec(спец)
        спец.loader.exec_module(П)
        for і, р in enumerate(історія):
            вхід = р['вхід']
            F = М._features(вхід)[0]
            контраст = П.контраст_особи(F).get('рівень')
            пал = П.палітра_практична(F, самозвіт=вхід.get('самозвіт'), контраст_рівень=контраст)
            бриф = П.для_пакета(пал)
            виходи = причинні[і]['брифи']['без_усіх']
            # Незмінений короткий конструктор має однакове джерело у всіх гілках.
            assert all(байти(в) == байти(виходи[0]) for в in виходи), і
            старий = [г.get('поєднання') for г in р['бриф_ДО']]
            після = [бриф.get('поєднання')] * len(старий)
            assert байти(після) == байти(старий), (і, 'доповнення не пояснило початковий бриф')
            змінено = байти(після) != байти([г.get('поєднання') for г in виходи])
            assert змінено == р['раніше_без_аналогової'], (і, 'неочікуваний вплив доповнення')
            записи.append(dict(персона=і, зміна_від_г=змінено, короткий_без_г=після))
            if (і + 1) % 35 == 0:
                print(f'Доповнення: {і + 1}/315', flush=True)
    результат = dict(персон=315, зміна_від_г=sum(р['зміна_від_г'] for р in записи),
                     без_абвг_побайтно_першої_спроби=315, непояснених=0, записи=записи)
    pathlib.Path(__file__).with_name('доповнення.json.gz').write_bytes(gzip.compress(байти(результат), mtime=0))
    print('Доповнення аналогової: 35; решта 280 без впливу; без а/б/в/г = перша спроба 315/315')
    return 0


if __name__ == '__main__':
    sys.exit(головна())
