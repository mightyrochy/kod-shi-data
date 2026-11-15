import json, sys, os
from pathlib import Path
from collections import Counter
корінь = Path(sys.argv[1]); os.chdir(корінь)
sys.path.insert(0, str(корінь / 'джерела/прилади'))
import корінь_річ_запис_речі as к
стара = к.Прогін.node
підсумок = []
def node(self, вхід):
    if 'дерево' in вхід and len(json.dumps(вхід)) > 1_000_000:
        за_ім, текст_за_тегом, усі = Counter(), Counter(), Counter()
        def обійти(в):
            for а, з in в['атр'].items():
                з = str(з); за_ім[а] += len(з.encode()); усі[з] += 1
            for ч in в['діти']:
                if isinstance(ч, dict): обійти(ч)
                else: текст_за_тегом[в['тег']] += len(ч.encode()); усі[ч] += 1
        обійти(вхід['дерево'])
        унікальне = sum(len(s.encode()) for s in усі)
        загальне = sum(len(s.encode()) * n for s, n in усі.items())
        підсумок.append(dict(url=self._url, атр=за_ім.most_common(8), текст=текст_за_тегом.most_common(5), рядки_всього=загальне, рядки_унікальні=унікальне))
    return стара(self, вхід)
стара_dom = к.Прогін.dom
def dom(self, тіло, url, сел):
    self._url = url; return стара_dom(self, тіло, url, сел)
к.Прогін.dom = dom
к.Прогін.node = node
try: к.main(['--стеля', sys.argv[2]] if len(sys.argv) > 2 else [])
finally: Path('/tmp/вимір/атр.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=1))
