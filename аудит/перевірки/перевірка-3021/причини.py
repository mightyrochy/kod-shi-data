import json, pathlib, sys
src = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(src))
import вибір_палітри as В, міст_вхід as М, міст_основи as О
cases = [('why_her_contrast', 'contrast', {'level':'unknown'}, False), ('why_her_contrast','contrast',{'level':'low'},True), ('why_her_undertone','undertone',{'class':'not_asserted'},False), ('why_her_undertone','undertone',{'class':'cool'},True), ('why_her_hair','hair',{'family':'unknown'},False), ('why_her_hair','hair',{'family':'neutral'},True)]
for reason, key, value, expected in cases:
    actual = В.ЗВІРКА_ПРИЧИН[reason]('base', {}, {'особа':{key:value}})[0]
    print(reason, json.dumps(value), 'прийнято:', actual, 'очікувано:', expected)
base = json.loads((src / 'стенд_вх.json').read_text('utf8'))
woman = json.loads((src.parent / 'аудит/проби/жінки/ж4.json').read_text('utf8'))
input = dict(base, шкіра=woman['skin'], волосся=woman['hair'], очі=woman['eyes'], source='model_hex')
features = М.features(input)[0]
person = В.перелік(input)['особа']
print('ж4 model_hex person:', json.dumps(person, ensure_ascii=False))
features_empty = {k:v for k,v in features.items() if k not in ('шкіра', 'волосся', 'очі') and not k.startswith('волосся_')}
palette = {'особа': {'рівень':'невідомо','value_gap':None}}
print('невідома щілина:', В._особа(features_empty, palette)['contrast']['light_dark_gap'])
