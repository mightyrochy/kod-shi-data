# -*- coding: utf-8 -*-
# Аркуш очима до рядка 411: на кожну річ — кадри картки ДО правила 7 `кадри_речі`; знятий кадр у червоній рамці з
# написом «ЗНЯТО», лишений — у зеленій. Вибірка: id з аргументів, а потім N випадкових змінених (зерно 411).
# Запуск: python3 аудит/проби/аркуш_411.py <тека> <N випадкових> [id…]   (PIL, curl; кеш /tmp/фото_огляд)
import sys, os, random, hashlib, subprocess
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'джерела'))
from PIL import Image, ImageDraw, ImageFont
import feed as Ф, фід_фото as ФФ, фід_кадр_колір as ФКК
from фід_збагачення import _збагачення_придатне
ТЕКА, N, ІД = os.path.abspath(sys.argv[1]), int(sys.argv[2]), sys.argv[3:]
os.makedirs(ТЕКА, exist_ok=True); os.makedirs('/tmp/фото_огляд', exist_ok=True)
оф = Ф.читати_yml(Ф.каталог_на_диску('каталог_повний.xml'))[0]
зб, сп, хо = Ф.читати_збагачення(), ФФ._спільні_фото(оф), ФФ._хости_крамниць(оф); к = ФКК.контекст(оф, зб, сп)
шр = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12)
def кадр_картки(o):
    з = зб.get(o['id']); ок = _збагачення_придатне(з) and not ФФ.чужий_кадр(з.get('фото'), сп.get(o.get('магазин')) or {})
    return ФКК.рішення(o, з if ок else None, к).get('кадр') or (з.get('фото') if isinstance(з, dict) else None)
def ряд(o, правило):
    справжнє = ФФ.чужий_підпис
    ФФ.чужий_підпис = справжнє if правило else (lambda u, я: None)
    try: return ФФ.кадри_речі(o, сп.get(o.get('магазин')) or {}, хо, кадр_картки(o))
    finally: ФФ.чужий_підпис = справжнє
def кадр(u):
    p = '/tmp/фото_огляд/' + hashlib.md5(u.encode()).hexdigest() + '.img'
    if not os.path.exists(p) or os.path.getsize(p) == 0: subprocess.run(['curl', '-sS', '-L', '-m', '40', '-o', p, u], capture_output=True)
    try: im = Image.open(p).convert('RGB'); im.thumbnail((150, 210)); return im
    except Exception: return None
зміни = [o for o in оф if ряд(o, False) != ряд(o, True)]
вибір = [o for i in ІД for o in оф if o['id'] == i] + random.Random(411).sample([o for o in зміни if o['id'] not in ІД], N)
РІД = 3
for а in range(0, len(вибір), РІД):
    арк = Image.new('RGB', (1500, 270 * РІД), 'white'); д = ImageDraw.Draw(арк)
    for i, o in enumerate(вибір[а:а + РІД]):
        до, після = ряд(o, False), ряд(o, True); Y = i * 270
        д.text((6, Y + 2), '%s · %s · кадрів ДО %d → ПІСЛЯ %d' % (o['id'], o.get('назва', '')[:60], len(до), len(після)), fill='black', font=шр)
        for j, u in enumerate(до[:9]):
            зняти = u not in після; X = 6 + j * 164
            im = кадр(u)
            if im: арк.paste(im, (X + 2, Y + 24))
            д.rectangle([X, Y + 22, X + 158, Y + 236], outline=(210, 0, 0) if зняти else (0, 150, 0), width=3)
            д.text((X + 4, Y + 240), ('ЗНЯТО' if зняти else 'лишено') + (' · перший' if j == 0 else ''), fill=(210, 0, 0) if зняти else (0, 120, 0), font=шр)
    арк.save(os.path.join(ТЕКА, 'аркуш_%02d.png' % (а // РІД + 1)))
print(len(зміни), 'змінених;', len(вибір), 'на аркушах у', ТЕКА)
