#!/usr/bin/env python3
# Підробний `gh api <шлях>` для стенда спостерігача: відповіді — файли в $FAKE_GH_DIR (pulls.json, comments_<N>.json,
# checks_<SHA>.json); сторінки per_page/page і since розбирає сам. FAKE_GH_FAIL=1 — завжди помилка.
# `-X PATCH … --input <файл>` (стан ноутбука, claude_run.ps1): тіло — у patch_<N>.json, шлях — у calls.log.
# `-i` (спостерігач, умовні запити): як справжній gh 2.103 — `HTTP/2.0 200 OK`, `Etag: W/"<sha256 тіла>"`, порожній рядок,
# тіло; з `If-None-Match` того ж ETag — `HTTP/2.0 304 Not Modified` (ETag без `W/`), stderr `gh: HTTP 304`, код 1.
# Кожна така відповідь — рядок `<статус> <шлях>` у etag.log. FAKE_GH_STATUS=<код> — відповісти цим статусом
# (500 — код 1; 202 — код 0, як відповідь, що не є 200).
import hashlib, json, os, sys
from urllib.parse import urlparse, parse_qs
d = os.environ['FAKE_GH_DIR']
a = sys.argv[1:]
path = a[a.index('--input') - 1] if '--input' in a else a[-1]
with open(os.path.join(d, 'calls.log'), 'a') as f:
    f.write(('PATCH ' if 'PATCH' in a else '') + path + '\n')
if os.environ.get('FAKE_GH_FAIL') == '1':
    sys.stderr.write('HTTP 502\n'); sys.exit(1)
if 'PATCH' in a:
    n = len([x for x in os.listdir(d) if x.startswith('patch_')])
    body = open(a[a.index('--input') + 1], encoding='utf-8').read()
    open(os.path.join(d, 'patch_%d.json' % n), 'w', encoding='utf-8').write(body)
    sys.stdout.write('{}'); sys.exit(0)
u = urlparse(path); q = parse_qs(u.query); parts = u.path.strip('/').split('/')
def load(name, default):
    p = os.path.join(d, name)
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default
def page(items):
    n = int(q.get('per_page', ['30'])[0]); pg = int(q.get('page', ['1'])[0])
    return items[(pg - 1) * n:pg * n]
if parts[-1] == 'pulls':
    out = page(load('pulls.json', []))
elif len(parts) >= 6 and parts[3] == 'issues' and parts[5] == 'comments':
    items = load('comments_%s.json' % parts[4], [])
    if 'since' in q:
        items = [c for c in items if c['updated_at'] >= q['since'][0]]
    out = page(items)
elif parts[-1] == 'check-runs':
    runs = load('checks_%s.json' % parts[-2], [])
    out = {'total_count': len(runs), 'check_runs': runs}
else:
    sys.stderr.write('404 ' + path + '\n'); sys.exit(1)
body = json.dumps(out, ensure_ascii=False)
if '-i' not in a:
    sys.stdout.write(body); sys.exit(0)
def answer(code, reason, header, text, err=''):
    with open(os.path.join(d, 'etag.log'), 'a') as f:
        f.write('%d %s\n' % (code, path))
    sys.stdout.buffer.write(('HTTP/2.0 %d %s\r\n%s\r\n%s' % (code, reason, header, text)).encode('utf-8'))
    if err:
        sys.stderr.write(err + '\n')
    sys.exit(1 if code >= 300 else 0)
etag = hashlib.sha256(body.encode('utf-8')).hexdigest()
sent = [x.split(':', 1)[1].strip() for x in a if x.startswith('If-None-Match:')]
forced = os.environ.get('FAKE_GH_STATUS')
if forced and forced != '200':
    answer(int(forced), 'Odd', '', '{}', 'gh: HTTP ' + forced)
if sent and sent[0].replace('W/', '', 1) == '"%s"' % etag:
    answer(304, 'Not Modified', 'Etag: "%s"\r\n' % etag, '', 'gh: HTTP 304')
answer(200, 'OK', 'Etag: W/"%s"\r\n' % etag, body)
