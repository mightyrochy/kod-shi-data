"""3.5: один стан вибору, явний адресат і кімоно в слоті пояса; без моделі."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import statements as С, внутрішня_мова as В, вибір_палітри as П, palettes as Л, мовний_шар as М
from міст_відповіді import _для_всіх
гілки = [dict(і=і, схема=сх, вага='ядро', рідший=False,
             нота_кодами=В.повідомлення('palette_scheme_note', В.заява(код)))
         for і, (сх, код) in enumerate([('тональна', 'scheme_tonal'), ('аналогова', 'scheme_analogous')])]
стил = dict(вибір=dict(схема='тональна', гама='насичені', вибір_кольору={'база': 'бузковий'},
                       обрала=dict(base='stylist', scheme='stylist', saturation='stylist')))
до = П.стан_для_показу(dict(її={}, гілки=гілки))
після = П.стан_для_показу(dict(її={}, стилістка=стил, гілки=гілки))
assert {з['choice'] for з in до['пал-стан']['statements']} == {'pending'}
assert {з['choice'] for з in після['пал-стан']['statements']} == {'stylist'}
assert після['рідша.0']['statements'][0]['choice'] == 'stylist'
assert після['рідша.1']['statements'][0]['choice'] == 'unselected'
assert not після['рідша.0']['statements'][0]['rank']['rare']
її = П.стан_для_показу(dict(її={'гілка': 1}, стилістка=стил, гілки=гілки))
assert її['рідша.1']['statements'][0]['choice'] == 'her'
assert її['пал-стан']['statements'][1]['values']['value'] == 'аналогова'
assert С.автор('рука') == С.автор('she_chose') == С.автор(True) == 'her'
assert С.автор('вона обрала сама') == 'her'
репліка = {'not_recorded': ['occasion_part', 'place']}
промпт = М.промпт_репліки(репліка)
assert 'occasion_part' not in промпт and 'place' in промпт
assert репліка['not_recorded'] == ['occasion_part', 'place']
assert _для_всіх(В.повідомлення('card_unchecked', В.заява('areas_not_measured', count=3))) == 1
assert _для_всіх(В.повідомлення('card_unchecked', В.заява('cut_not_declared_assumed_regular'))) == 0
речі = [dict(id='kimono', слот='пояс', тип='кімоно', назва='Кімоно довге')]
т = Л.тон_тональної(речі, {'_схема': 'тональна'})
р = т['предмети']['не_виміряно'][0]
assert р['item_id'] == 'kimono' and р['slot'] == 'belt' and 'Кімоно' in р['name']['free_text']
print('поточний стан: pending → stylist → her; альтернатива unselected; ранг чипа збережено')
print('адресат незалежний від values; кімоно: id=kimono, slot=belt, власна назва')
print('перелік авторів один:', ','.join(sorted(С.АВТОРИ)))
