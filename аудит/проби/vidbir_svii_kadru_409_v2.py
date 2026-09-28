# -*- coding: utf-8 -*-
"""Друга, незалежна випадкова вибірка 20 речей зі станом «свій_кадр» (злита голова #409),
не перетинається з першою вибіркою (сід 409), для очного огляду перевірки."""
import sys, os, json, random, collections
Д = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "джерела")
sys.path.insert(0, Д)
os.chdir(Д)
import feed as F
import фід_кадр_колір as ФКК
from фід_фото import _спільні_фото, _файл_фото, чужий_кадр
from фід_збагачення import _збагачення_придатне

вже = set(json.load(open(sys.argv[2], encoding='utf-8')).__iter__()) if False else None
вже_ід = set(x['id'] for x in json.load(open(sys.argv[2], encoding='utf-8'))) if len(sys.argv) > 2 else set()

offers = F.читати_yml(F.каталог_на_диску())[0]
зб = F.читати_збагачення()
сп = _спільні_фото(offers)
к = ФКК.контекст(offers, зб, сп)
ФКК.КЛАС_ПОТРІБЕН = True

gid = collections.defaultdict(list)
for o in offers:
    g = o.get('group_id')
    if g:
        gid[(o.get('магазин'), g)].append(o)
multi_groups = {g for g, os_ in gid.items() if len(os_) > 1}

свій_кадр = []
for o in offers:
    з = зб.get(o.get('id'))
    if not (з and _збагачення_придатне(з)):
        continue
    if чужий_кадр(з.get('фото'), сп.get(o.get('магазин')) or {}):
        continue
    р = ФКК.рішення(o, з, к)
    if р['стан'] != 'свій_кадр':
        continue
    if o['id'] in вже_ід:
        continue
    ключ_групи = (o.get('магазин'), o.get('group_id'))
    мульти = ключ_групи in multi_groups
    свій_кадр.append(dict(
        id=o['id'], магазин=o.get('магазин'), group_id=o.get('group_id'),
        колір_назва=o.get('колір_назва'), назва=o.get('назва'), мульти=мульти,
        кадр_url=р['кадр'],
        одногрупники=[(x['id'], x.get('колір_назва')) for x in gid.get(ключ_групи, []) if x['id'] != o['id']][:6] if мульти else [],
    ))

print('доступно поза першою вибіркою:', len(свій_кадр))
rnd = random.Random(9092)
rnd.shuffle(свій_кадр)
вибір = свій_кадр[:20]
print('відібрано:', len(вибір))
with open(sys.argv[1] if len(sys.argv) > 1 else 'vidbir_409_v2b.json', 'w', encoding='utf-8') as f:
    json.dump(вибір, f, ensure_ascii=False, indent=1)
