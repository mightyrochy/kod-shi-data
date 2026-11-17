"""#4162: пара руки 1 — назва, номер, рядок стилістки (останній ВЕРДИКТ_V1 сцени) і що каже суд руки 1 про каблук і підошву."""
import json, re, sys, glob
from pathlib import Path
КОДИ = re.compile(r'"code": ?"([^"]*(?:heel|sole|stiletto|platform|grip|ice|slip)[^"]*)"', re.I)
for сцена in sys.argv[1:]:
    d = json.loads(Path(сцена, 'вердикти.txt').read_text())
    for в in d['прогони'][0]['вердикти']:
        if str(в['рука']) != '1': continue
        е = в['етапи']; дов = е.get('довідник_речей') or {}
        for р in в['речі_образу']:
            if р.get('слот') != 'взуття': continue
            н = (дов.get(р['id']) or {}).get('номер')
            print(f"== {сцена} · рука 1 · {р['id']} · {н} · «{р['назва']}»")
            for f in sorted(glob.glob(f'{сцена}/VIDPOVIDI/*_V1*.txt')):
                ч = Path(f).read_text().split('── ВІДПОВІДЬ')[0]
                і = ч.find('["' + н + '",')
                if і >= 0:
                    к = ч.find('}]', і); print('   рядок стилістки', Path(f).name[:34], ':', ч[і:к+2][-260:])
            for з in (е.get('суд') or {}).get('знахідки', []):
                т = json.dumps(з, ensure_ascii=False)
                if р['id'] in т or р['назва'] in т or (н and н in т):
                    print('   суд (знахідка з цією річчю):', з['правило'], з['сила'], '·', [z['code'] for z in з.get('заяви') or []], '·', з['суть'][:140])
            т = json.dumps(в, ensure_ascii=False)
            print('   коди каблука/підошви/зчеплення в записі руки 1:', sorted(set(КОДИ.findall(т))))
