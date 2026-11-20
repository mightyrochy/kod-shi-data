"""Виклики моделі за видом: скільки на ситуацію, знаків, токенів входу й виходу, найдовший виклик.

Запуск з кореня: python3 -I аудит/звіти/ядро-образу-наново/скрипти/виклики_моделі.py \
    аудит/проби/Живий-через-міст/стенд/службове/с*/обміни.jsonl
Вид — роль із перших 3 000 знаків запиту («role»), перекладачка й опис речі з фото — за початком тексту. Токени входу —
input + cache_read + cache_creation з usage відповіді. Ділиться на кількість файлів (ситуацій).
"""
import json,sys,re,collections
лч=collections.OrderedDict()
for f in sys.argv[1:]:
  for i,l in enumerate(open(f,encoding='utf-8')):
    d=json.loads(l); q=json.loads(d['запит']) if isinstance(d['запит'],str) else d['запит']
    t=q['messages'][0]['content']; t=t if isinstance(t,str) else ' '.join(c.get('text','') for c in t if c.get('type')=='text')
    if t.startswith('Ти — перекладачка'): v='перекладачка (укр.)'
    elif t.startswith('Photo 1'): v='опис речі з фото'
    else:
        m=re.search(r'"role":\s*"([^"]+)"',t[:3000]); v=(m.group(1) if m else t[:60])
        v=re.sub(r'(Lyusterko styling app|styling app in a live chat with a woman)\.? ?','',v)[:95]
    r=d.get('відповідь'); 
    try:
        u=json.loads(r)['usage'] if isinstance(r,str) else r['usage']; ti=u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0); to=u.get('output_tokens',0)
    except Exception: ti=to=0
    e=лч.setdefault(v,[0,0,0,0,0.0]); e[0]+=1;e[1]+=len(t);e[2]+=ti;e[3]+=to;e[4]=max(e[4],d.get('с') or 0)
n=len(sys.argv)-1
print('вид | викликів на сцену | симв на сцену | вх.ток | вих.ток | макс с')
for v,e in sorted(лч.items(),key=lambda x:-x[1][2]):
    print(f'{v} | {e[0]/n:.1f} | {e[1]/n:.0f} | {e[2]/n:.0f} | {e[3]/n:.0f} | {e[4]:.0f}')
