"""Відтворює додаткові випадки п.6 на приладі з переданого дерева голови."""
import importlib.util
import pathlib
import sys
import tempfile

корінь = pathlib.Path(sys.argv[1]).resolve()
опис = importlib.util.spec_from_file_location(
    'прилад_перевірки', корінь / 'джерела/прилади/корінь_е2_опора_пояснення.py')
прилад = importlib.util.module_from_spec(опис)
опис.loader.exec_module(прилад)

міст = "async function model(x){ return await fetch('/v1/messages', {body:x}); }\n"
випадки = [
    ('кадри через дві змінні', 1,
     "async function run(фото){ const a=фото.slice(); const b=блокиЗапиту(a); return model(b); }"),
    ('лічба дійшлих', 0,
     "async function run(фото){ const a=фото.slice(); const b=блокиЗапиту(a); const t=await model(b); return [t, headers['x-images-dropped']]; }"),
    ('результат чужого виміру', 0,
     "async function run(фото){ const a=measure(фото); return model(a); }"),
    ('лише довжина', 0,
     "async function run(фото){ const a=фото.length; return model(a); }"),
    ('кадри у дужках', 1,
     "async function run(фото){ const a=(фото); return model(a); }"),
    ('кадри у другій гілці трійки', 1,
     "async function run(фото, flag){ const a=flag ? [] : фото; return model(a); }"),
    ('кадр як поле запису', 1,
     "async function run(фото){ const a={messages:[{role:'user',content:[{type:'image',source:фото}]}]}; return model(a); }"),
    ('та сама назва у сусідній функції', 1,
     "async function outer(фото){ async function first(){const a=фото.slice(); return model(a);} async function second(){const a='text'; return model(a);} return second(); }"),
    ('властивість length у прямому аргументі', 0,
     "async function run(фото){ return model(фото.length); }"),
    ('модель без кадрів', 0,
     "async function run(){ return model('plain text'); }"),
]
пройдено = 0
for назва, очікувано, тіло in випадки:
    with tempfile.TemporaryDirectory() as тека:
        шлях = pathlib.Path(тека)
        (шлях / 'джерела/показ').mkdir(parents=True)
        текст = (міст + тіло).replace('; ', ';\n').replace('{const', '{\nconst')
        (шлях / 'джерела/показ/scene.js').write_text(текст, encoding='utf8')
        прилад.КОРІНЬ = str(шлях)
        місця, _ = прилад.п6(str(шлях))
        отримано = len(місця)
        пройдено += отримано == очікувано
        print(f'{назва}: очікую {очікувано}, отримано {отримано}')
print(f'пройдено: {пройдено}/{len(випадки)}')
