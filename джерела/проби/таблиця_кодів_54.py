"""Коди з наявних відповідей 404 → живий фід → стовпці → та сама база; без моделі."""
import gzip, json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feed, каталог_коди as КК, фід_каталог as ФК, фід_розбір as ФР
import таблиця_збирання as З, таблиця_каталогу as Т
кодів = json.load(gzip.open(sys.argv[1], 'rt'))
старий = КК.читати
КК.читати = lambda тека=None: кодів
try:
    шлях = str(Path(__file__).resolve().parents[1] / 'каталог_повний.xml')
    with tempfile.TemporaryDirectory() as tmp:
        кеш = str(Path(tmp)/'кеш.json'); Path(кеш).write_text('{}')
        база = ФК.прочитати_каталог(шлях, 0, кеш, feed.читати_збагачення())
        таблиця = З.зібрати(шлях)
        відновлена = Т.відновити(таблиця, ФР.офери_фіду(шлях))
        assert база['каталог'] and Т.однакові(відновлена, база)
        assert 'код_item_type' in таблиця['поля'] and 'код_fabric' in таблиця['поля']
        assert 'каталог_розбір_коди.json.gz' in таблиця['ключ']['дані']
        assert 'каталог_фото_тип_приймання.json' in таблиця['ключ']['дані']
        assert all(r['розбір']['evidence'] == кодів[r['id']]['evidence'] for r in база['каталог'])
        print('404: кодів',len(кодів),'→ записів продукту',len(база['каталог']), '→ стовпців',len(таблиця['поля']),'; база тотожна, цитати й ключі даних збережено')
finally:
    КК.читати = старий
