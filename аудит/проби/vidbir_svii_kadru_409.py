# -*- coding: utf-8 -*-
"""ВІДБІР 40 речей зі станом «свій_кадр» (клас_обов'язковий=True, злита голова #409) для очного
огляду: ≥15 із group_id, що має ≥2 кольорових варіанти в каталозі (ризик Н-6 — тон=null).
Друкує JSON-список (id, магазин, group_id, колір_назва, назва, стан, кадр-файл, клас, lab, чи_мульти)."""
import sys, os, json, random, collections
Д = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "джерела")
sys.path.insert(0, Д)
os.chdir(Д)
import feed as F
import фід_кадр_колір as ФКК
from фід_фото import _спільні_фото, _файл_фото, чужий_кадр
from фід_збагачення import _збагачення_придатне

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
за_ід = {o['id']: o for o in offers}

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
    ключ_групи = (o.get('магазин'), o.get('group_id'))
    мульти = ключ_групи in multi_groups
    кадр_файл = _файл_фото(р['кадр'])
    свій_кадр.append(dict(
        id=o['id'], магазин=o.get('магазин'), group_id=o.get('group_id'),
        колір_назва=o.get('колір_назва'), назва=o.get('назва'), мульти=мульти,
        кадр_файл=кадр_файл, кадр_url=р['кадр'],
        одногрупники=[(x['id'], x.get('колір_назва')) for x in gid.get(ключ_групи, []) if x['id'] != o['id']][:6] if мульти else [],
    ))

print('усього свій_кадр:', len(свій_кадр), 'з них мульти:', sum(1 for x in свій_кадр if x['мульти']))
rnd = random.Random(409)
мульти_пул = [x for x in свій_кадр if x['мульти']]
решта_пул = [x for x in свій_кадр if not x['мульти']]
rnd.shuffle(мульти_пул); rnd.shuffle(решта_пул)
вибір = мульти_пул[:20] + решта_пул[:20]
вибір = вибір[:40]
print('відібрано:', len(вибір), 'мульти серед відібраних:', sum(1 for x in вибір if x['мульти']))
with open(sys.argv[1] if len(sys.argv) > 1 else 'vidbir_409.json', 'w', encoding='utf-8') as f:
    json.dump(вибір, f, ensure_ascii=False, indent=1)
