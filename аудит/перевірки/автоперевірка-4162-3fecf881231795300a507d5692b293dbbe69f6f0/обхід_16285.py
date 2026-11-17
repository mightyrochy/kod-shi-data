import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve() / 'джерела'))
import дріт_моделі as Д
import пара_взуття as П

р = dict(id='проба', слот='взуття', осі={'heel': 'unknown'},
         розбір={'heel': {'present': 'yes', 'shape': 'thin', 'height': 'high'}})
print(json.dumps(dict(вхід=р, одне_визначення=П.каблук(р),
    рядок=Д.річ(р, короткий=True), вето=П.під_межею_підборів(р)), ensure_ascii=False, indent=2))
