import json,sys
out,ref=sys.argv[1],sys.argv[2]   # тека виходу стенда, тека офлайн-проби
ет=json.load(open(out+'/етапи.json'))
суд=dict(ет['суд']); суд.pop('мс',None)
р=json.load(open(ref+'/суд.json'))
print('суд сторінки == суд CPython:', суд==р)
if суд!=р:
    for k in set(суд)|set(р):
        if суд.get(k)!=р.get(k): print('  різниця в ключі', k)
оц=open(ref+'/оцінка.json',encoding='utf-8').read()
в=ет['виклики']
print('виклики сторінки:', [(x['крок'], x['запит']['символів']) for x in в])
print('промпт оцінки == оцінка.json:', в[0]['запит']['текст']==оц)
т=json.load(open(out+'/обміни/01_запит.json'))
блоки=т['messages'][-1]['content']
print('блоків у запиті #1:', len(блоки), [b['type'] for b in блоки], '· текст == оцінка.json:', блоки[-1].get('text')==оц)
