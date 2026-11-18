import sys, os, pickle, time
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
os.chdir("/tmp/скрипти_звірки/run")
import фід_каталог as ФК
t=time.time()
шлях = ФК.каталог_на_диску(тека="/tmp/скрипти_звірки/дані")
print("шлях", шлях, time.time()-t, flush=True)
б = ФК.база_прогону(шлях, ліміт_фото=0, кеш="/tmp/скрипти_звірки/run/кеш_кольорів.json", кешувати=False)
print({k:(len(v) if hasattr(v,'__len__') else v) for k,v in б.items()}, time.time()-t)
pickle.dump(б["каталог"], open("/tmp/скрипти_звірки/дані/каталог.pkl","wb"))
