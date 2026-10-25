"""Replay записаних ходів розмови без моделі: відповідь → прийняти_розмову → сторож_мовного_шару.
Лише читання й лічба. argv: тека live, 'main' | 'pr'."""
import os, re, sys, json, glob, io, contextlib
S = os.path.dirname(os.path.abspath(__file__))
L, ВЕРСІЯ = sys.argv[1], sys.argv[2]
if ВЕРСІЯ == 'pr':
    sys.path.insert(0, os.path.join(S, 'pr1819'))
sys.path.insert(1 if ВЕРСІЯ == 'pr' else 0, '/home/user/kod-shi-data/джерела')
sys.path.insert(0, os.path.dirname(S))
from prompt_keys import load
with contextlib.redirect_stdout(io.StringIO()):
    import мовний_шар as МШ
ЧИСЛО_ГОДИНИ = re.compile(r"\d")
def сцена(f):
    s = re.sub(r'^zhyvi-[^/]+/аудит/', '', f[len(L)+1:])
    return s.split('/VIDPOVIDI/')[0] + ' #' + re.search(r'seed\d+_(\d+)', f).group(1)
рядки = []
for f in sorted(glob.glob(L + '/**/VIDPOVIDI/*хід_розмови*.txt', recursive=True)):
    ob, r = load(f)
    her = (ob or {}).get('her_new_message') or ''
    відп = r.split('──\n', 1)[1] if '──\n' in r else r
    р = МШ.прийняти_розмову(відп)
    вн = р.get('внутрішня') or {}
    try:
        стор = МШ.сторож_мовного_шару(вн, [her])
    except Exception as e:
        стор = {'помилка': repr(e)[:80]}
    рядки.append(dict(сцена=сцена(f), її=her, внутрішня=вн, сторож=стор, не_взято=р.get('не_взято'), незнайомі=р.get('незнайомі')))
json.dump(рядки, open(os.path.join(S, 'replay_%s.json' % ВЕРСІЯ), 'w', encoding='utf8'), ensure_ascii=False, indent=1, default=str)
print(ВЕРСІЯ, len(рядки), 'ходів')
x = рядки[0]
print(json.dumps({k: x[k] for k in ('сцена', 'її', 'внутрішня')}, ensure_ascii=False, default=str)[:1500])
print('СТОРОЖ:', json.dumps(x['сторож'], ensure_ascii=False, default=str)[:800])
