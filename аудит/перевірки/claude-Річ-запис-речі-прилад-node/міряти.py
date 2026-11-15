"""Міряє склад входу node приладу: розмір, глибину, частки полів. Аргумент — корінь дерева."""
import json, sys, os
from pathlib import Path
корінь = Path(sys.argv[1]); os.chdir(корінь)
sys.path.insert(0, str(корінь / 'джерела/прилади'))
import корінь_річ_запис_речі as к
стат = []
стара = к.Прогін.node
def глибина(в, г=1):
    if not isinstance(в, dict): return г - 1
    return max([г] + [глибина(ч, г + 1) for ч in в['діти']])
def частки(в, s):
    s['вузлів'] += 1
    s['шлях'] += len(json.dumps(в['шлях'], ensure_ascii=False))
    s['причина'] += len(json.dumps(в['причина'], ensure_ascii=False))
    s['атр'] += len(json.dumps(в['атр'], ensure_ascii=False))
    for ч in в['діти']:
        if isinstance(ч, dict): частки(ч, s)
        else: s['текст'] += len(json.dumps(ч, ensure_ascii=False)); s['текстів'] += 1
def node(self, вхід):
    if 'дерево' in вхід:
        s = dict(вхід_ascii=len(json.dumps(вхід)), вхід_utf8=len(json.dumps(вхід, ensure_ascii=False).encode()),
                 вузлів=0, шлях=0, причина=0, атр=0, текст=0, текстів=0,
                 селектори=len(json.dumps(вхід['селектори'])), код=len(вхід['код']))
        sys.setrecursionlimit(100000)
        s['глибина'] = глибина(вхід['дерево'])
        частки(вхід['дерево'], s)
        стат.append(s)
    else:
        стат.append(dict(вхід_ascii=len(json.dumps(вхід)), вхід_utf8=len(json.dumps(вхід, ensure_ascii=False).encode()), лише_селектори=1))
    return стара(self, вхід)
к.Прогін.node = node
try:
    к.main(sys.argv[2:])
finally:
    Path(os.environ.get('STAT', '/tmp/вимір/стат.json')).write_text(json.dumps(стат, ensure_ascii=False))
