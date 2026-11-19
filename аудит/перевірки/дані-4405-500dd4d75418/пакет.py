"""Вхід руки 1 з контрольним виміром, невизначеним контрастом і каталогом голови; моделі не викликає."""
import os, json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
os.chdir(root)
import bridge, стенд_знімок as СЗ
snapshot = next(x for x in json.loads(pathlib.Path(__file__).with_name('браузер.json').read_text('utf8')) if x['режим'] == 'після')
data = json.loads((root / 'стенд_вх.json').read_text('utf8'))
data.update(snapshot['стилістка'])
data.update(сценарій=СЗ.СЦЕНАРІЇ['офіс·18°C'], випадок='офіс', каталог='каталог_brief.xml', без_фото=1,
            зріст=168, обхвати=dict(плечі=100, груди=92, талія=74, стегна=100))
result = json.loads(bridge.виклик('запити', json.dumps(data)))
print(json.dumps(dict(пул_речей=result.get('пул_речей'), помилка=result.get('помилка'), пул_чому=result.get('пул_чому'),
                     colouring=json.loads(result['B'])['person']['colouring']), ensure_ascii=False, indent=2))
