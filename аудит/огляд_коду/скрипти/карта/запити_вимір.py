import sys, json, time; sys.path.insert(0,'.')
import bridge as B
вх=json.load(open('стенд_вх.json')); вх['каталог']=sys.argv[1]; вх.pop('пакети',None)
вх['бюджет_токенів']=43400; вх['без_фото']=1
t=time.time(); s=B.виклик("запити", json.dumps(вх, ensure_ascii=False)); dt=time.time()-t
r=json.loads(s)
print('вхід байтів',len(json.dumps(вх,ensure_ascii=False).encode()),'вихід байтів',len(s.encode()),'с',round(dt,1))
print('ключів верхнього рівня',len(r)); print(sorted(r)[:200])
print('помилка',r.get('помилка'))
big=sorted(((len(json.dumps(v,ensure_ascii=False).encode()),k) for k,v in r.items()),reverse=True)[:12]; print(big)
json.dump(r,open(sys.argv[2],'w'),ensure_ascii=False)
