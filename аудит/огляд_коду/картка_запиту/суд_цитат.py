"""Офлайн: суддя «репліка цитує запис» на записаних репліках. Лише лічба."""
import json, os, re, glob, sys
S = os.path.dirname(os.path.abspath(__file__)); L = sys.argv[1]
sys.path.insert(0, os.path.dirname(S))
from prompt_keys import load
д = {x['сцена'].split(' #')[0]: x for x in json.load(open(os.path.join(S, 'replay_main.json'), encoding='utf8'))}
def н(т): return ' '.join(str(т).lower().replace('’', "'").replace('ʼ', "'").split())
рядки = []
# 1) репліки перекладачки
for f in sorted(glob.glob(L + '/**/VIDPOVIDI/*репліка*.txt', recursive=True)):
    с = re.sub(r'^zhyvi-[^/]+/аудит/', '', f[len(L)+1:]).split('/VIDPOVIDI/')[0]
    т = open(f, encoding='utf8').read()
    m = re.search(r'"text":\s*"([^"]*)', т.split('── ВІДПОВІДЬ')[1]); відп = m.group(1) if m else ''
    рядки.append(('перекладачка', с, відп))
# 2) власний текст моделі ходу з фактами (лог: СТИЛІСТКА без виклику репліки)
for lg in sorted(glob.glob(L + '/**/лог.txt', recursive=True)):
    с = re.sub(r'^zhyvi-[^/]+/аудит/', '', lg[len(L)+1:]).rsplit('/лог.txt', 1)[0]
    if glob.glob(os.path.dirname(lg) + '/VIDPOVIDI/*репліка*'): continue
    for line in open(lg, encoding='utf8', errors='replace'):
        m = re.match(r'\s+СТИЛІСТКА:\s*(.*)', line)
        if m: рядки.append(('модель_ходу', с, m.group(1).strip()))
for вид, с, відп in рядки:
    x = д.get(с); q = {}
    if x:
        ст = x['сторож'][0] if isinstance(x['сторож'], list) and x['сторож'] and isinstance(x['сторож'][0], dict) else x['внутрішня']
        q = ст.get('quotes') or {}
    цит = [v for v in q.values() if isinstance(v, str) and v.strip()]
    є = [v for v in цит if н(v) in н(відп)]
    цифри = re.findall(r'\d+', відп); чужі = [ц for ц in цифри if not any(ц in v for v in цит)]
    J = bool(є) and not чужі
    print('%-12s J=%-5s цитат_у_відп=%d/%d чужі_цифри=%s | %s | %s' % (вид, J, len(є), len(цит), чужі, с[-34:], відп[:110]))
