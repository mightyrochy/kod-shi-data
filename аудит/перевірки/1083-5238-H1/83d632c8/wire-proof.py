import sys,pathlib,json,hashlib
sys.path.insert(0,sys.argv[1])
import формальність as Ф,вердикт_моделі as В,дріт_моделі as Д
речі=[dict(річ='кардиган',тип='кардиган',слот='верх',ошатність=5),dict(річ='човники',тип='човники',слот='взуття',ошатність=6)]
з, _=В.знахідки_вердикту(Ф.вимоги_коду(речі,'cocktail')+Ф.формальність_образу(речі,{'діапазон':(7,8)}),'о3')
в=[Д._знахідка(z) for z in з]
print(json.dumps(dict(wire=в,sha256=hashlib.sha256(json.dumps(в,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),контекст=[z['речі'] for z in з],заяв=[len(z.get('заяви') or []) for z in з]),ensure_ascii=False))
