import sys, json, time; sys.path.insert(0,'.')
import bridge as B
вх=json.load(open('стенд_вх.json')); вх['каталог']=sys.argv[1]; вх.pop('пакети',None); вх['бюджет_токенів']=43400; вх['без_фото']=1
t=time.time(); r=json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False))); print('запити с',round(time.time()-t,1))
for спроба,текст in (('порожня відповідь','{}'),('образ з двох id', json.dumps({"версія":"1","образи":[{"ід":"1","речі":[str(r['кандидати']['сукня'][0]['id']), str(r['кандидати']['взуття'][0]['id'])]}]},ensure_ascii=False))):
  for донор in (False,):
    t=time.time(); s=B.виклик("від_моделі", json.dumps(dict(вх, донор=донор, текст_моделі=текст), ensure_ascii=False)); dt=time.time()-t
    o=json.loads(s); print(спроба,'с',round(dt,2),'вихід байтів',len(s.encode()),'ключів',len(o), 'помилка' , str(o.get('помилка'))[:120])
    print('  ключі:',sorted(o)[:80])
