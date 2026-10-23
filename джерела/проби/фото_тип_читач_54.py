"""Фото-тип → читач: три файли, поточна SKU/URL, невідомий текст і явна суперечність."""
from фото_тип_синтетика import *
import catalog_fields as К
import feed
r, manifest, receipt = fixture()
overlay = dict(version=Ф.ВЕРСІЯ_ФАЙЛА, records=[r])
with tempfile.TemporaryDirectory() as tmp:
    for ім, дані in zip(Ф.ФАЙЛИ, (overlay, manifest, receipt)):
        Path(tmp, ім).write_text(json.dumps(дані))
    старий = Ф.читати
    Ф.читати = lambda: старий(tmp)
    try:
        о = dict(id='synthetic', фото=[r['image']['url']], назва='Пояс', розбір={'item_type':'unknown'})
        assert feed.слот(о) == 'верх' and feed.тип_речі(о) == 'сорочка'
        assert feed.слот(dict(о, фото=['https://example.invalid/other.jpg'])) is None
        текст = dict(о, розбір={'item_type':'belt'})
        assert feed.слот(текст) == 'пояс' and К.проєкція(текст)['фото_тип']['item_type'] == 'shirt'
        Path(tmp, Ф.ПРИЙМАННЯ_ФАЙЛ).unlink()
        assert feed.слот(о) is None
    finally:
        Ф.читати = старий
print('Фото-тип: прийнятий → читач; інший URL/без приймання → unknown; суперечність з текстом видима')
