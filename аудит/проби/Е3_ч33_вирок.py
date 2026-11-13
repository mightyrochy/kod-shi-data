"""Фактична сила K-COL-01 на вході старої перевірки площ масок, без каталогу й API."""
import sys, pathlib, os, json
код = pathlib.Path(sys.argv[sys.argv.index('--код') + 1]).resolve() if '--код' in sys.argv else pathlib.Path(__file__).resolve().parents[2] / 'джерела'
os.chdir(код); sys.path.insert(0, str(код))
import колір_світлота as КС
записи = [dict(річ=с, слот=с, lab=(60.0, 0.0, 0.0), колір_тип='вимір',
               L=60.0, C=0.0, h=0.0, текстура=None, площа=п, джерело_площі='маски')
          for с, п in zip(('верх', 'низ', 'взуття', 'сумка'), (.45, .30, .10, .15))]
for з in КС.перевірка_value(записи):
    print(json.dumps({к: з.get(к) for к in ('правило', 'сила', 'сила_нп', 'регістр', 'заяви')}, ensure_ascii=False))
