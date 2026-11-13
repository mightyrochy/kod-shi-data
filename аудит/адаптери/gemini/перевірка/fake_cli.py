#!/usr/bin/env python3
"""Фальшивий `codex` (рушій М.9-В) для стенду обгортки: сценарій — FAKE_SCENARIO, вид — FAKE_KIND=codex.
Codex: `exec ... --json -o <файл> <промпт>` -> відповідь у файлі -o, події JSONL у stdout."""
import json, os, re, subprocess, sys, time

KIND = os.environ['FAKE_KIND']
SC = os.environ.get('FAKE_SCENARIO', 'abandon_then_done')
STATE = os.environ['FAKE_STATE']
args = sys.argv[1:]
with open(os.path.join(STATE, KIND + '.argv.log'), 'a') as f:
    f.write(json.dumps(args, ensure_ascii=False) + '\n')

def opt(name):
    return args[args.index(name) + 1] if name in args else ''

# Зусилля, які «приймає» фальшивий codex (FAKE_CODEX_EFFORTS=a,b,c): інше — помилка конфігурації, як у справжнього, без подій.
eff = [a.split('=', 1)[1] for a in args if a.startswith('model_reasoning_effort=')]
ok_eff = os.environ.get('FAKE_CODEX_EFFORTS')
if eff and ok_eff and eff[0] not in ok_eff.split(','):
    style = os.environ.get('FAKE_EFFORT_STYLE')
    if style == 'escaped':
        # те саме повідомлення в екрануванні Windows PowerShell 5.1 (ConvertTo-Json): апостроф як \u0027
        msg = ("Invalid response.create payload: Invalid value: '%s'. Supported values are: "
               "'none', 'minimal', 'low', 'medium', 'high', 'xhigh', and 'max'." % eff[0])
        print(json.dumps({'type': 'error', 'message': msg}).replace("'", '\\u0027'))
        sys.exit(1)
    if style == 'payload':
        # відмова сервера (codex 0.164): подія --json без назви параметра в тексті
        print(json.dumps({'type': 'error', 'message': "Invalid response.create payload: Invalid value: '%s'. Supported values are: "
                          "'none', 'minimal', 'low', 'medium', 'high', 'xhigh', and 'max'." % eff[0]}))
        sys.exit(1)
    sys.stderr.write('Error loading config.toml: unknown variant `%s`, expected one of %s in `model_reasoning_effort`\n'
                     % (eff[0], ', '.join('`%s`' % x for x in ok_eff.split(','))))
    sys.exit(1)

def git(*a):
    return subprocess.run(['git', *a], check=True, capture_output=True, text=True).stdout.strip()

def commit(path):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'a').write('x\n')
    git('add', path)
    git('-c', 'user.name=g', '-c', 'user.email=g@x', 'commit', '-q', '-m', 'крок: ' + path)

from fake_timeline import тримати as hold, замкнути

prompt_arg = args[-1]
path = re.search(r'файл (\S+) ', prompt_arg).group(1)
content = open(path, encoding='utf-8').read()
open(os.path.join(STATE, KIND + '.prompts.log'), 'a').write(content + '\n=====\n')
p = os.path.join(STATE, KIND + '.turns')
with замкнути(p):
    n = int(open(p).read()) + 1 if os.path.exists(p) else 1
    with open(p, 'w') as counter:
        counter.write(str(n))
m = re.search(r'ГОТОВО gemini/(\S+) <', content)
slug = m.group(1) if m else '?'
def done():
    # SHA беруть після коміту сценарію: звіт з попереднім SHA обгортка відхиляє як mismatch
    return 'Готово.\nНОУТБУК ГОТОВО gemini/%s %s' % (slug, git('rev-parse', 'HEAD'))
err = ''
if SC == 'commit_done':
    hold(slug); commit('робота/%s.txt' % slug); resp = done()
elif SC == 'abandon_then_done':
    if n == 1:
        commit('робота/а.txt'); resp = 'Запустив фонове завдання, чекаю результату.'
    else:
        resp = done()
elif SC == 'github':
    commit('.github/workflows/evil.yml'); resp = done()
elif SC == 'quota429':
    resp, err = '', '429 RESOURCE_EXHAUSTED: quota exceeded'
elif SC == 'quota_reset_at':
    # відмова Codex 0.167 з часом скидання: місцевий час тієї ж машини, дата — з порядковим суфіксом дня
    t = time.localtime(time.time() + 2 * 86400)
    suf = 'th' if t.tm_mday in (11, 12, 13) else {1: 'st', 2: 'nd', 3: 'rd'}.get(t.tm_mday % 10, 'th')
    when = '%s %d%s, %d %d:%02d %s' % (time.strftime('%b', t), t.tm_mday, suf, t.tm_year, t.tm_hour % 12 or 12, t.tm_min, 'AM' if t.tm_hour < 12 else 'PM')
    resp, err = '', "You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/settings/usage to purchase more credits or try again at %s." % when
elif SC == 'auth':
    resp, err = '', 'Not logged in. Please log in'
elif SC == 'engine_fail':
    # збій рушія без класу (не квота, не вхід, не зусилля) з текстом, який має дійти до результату: шлях профілю й ключ — приватне
    sys.stderr.write('panic: stream disconnected before completion\n')
    resp, err = '', 'Internal error at C:\\Users\\Alice\\codex\\x.rs api_key=abcdefghijklmnop12345 rushij-error-end'
elif SC == 'blocked':
    commit('робота/б.txt'); resp = 'ЗАБЛОКОВАНО: чекаю рішення'
elif SC == 'slow_done':
    # довгий прогін із подіями щосекунди: довший за TotalMinutes обгортки, але без завислості
    commit('робота/а.txt'); resp = done()
    print(json.dumps({'type': 'turn.started'}), flush=True)
    for i in range(int(os.environ.get('FAKE_SLOW_SECONDS', '40'))):
        time.sleep(1); print(json.dumps({'type': 'item.completed', 'n': i}), flush=True)
elif SC == 'hang':
    # одна подія й тиша: завислість
    print(json.dumps({'type': 'turn.started'}), flush=True)
    time.sleep(300); raise SystemExit(0)
else:
    raise SystemExit('невідомий сценарій ' + SC)

if os.environ.get('FAKE_CODEX_RATE'):
    # журнал сесії Codex <CODEX_HOME>/sessions/Р/М/Д/rollout-*.jsonl: подія token_count із rate_limits (форма — codex-rs protocol.rs);
    # FAKE_CODEX_RATE="<використано 5 год>,<використано тижня>"
    u5, u7 = os.environ['FAKE_CODEX_RATE'].split(',')
    now = time.time(); g = time.gmtime(now)
    d = os.path.join(os.environ['CODEX_HOME'], 'sessions', time.strftime('%Y/%m/%d', g))
    os.makedirs(d, exist_ok=True)
    rl = {'limit_id': 'codex', 'limit_name': None, 'plan_type': 'plus',
          'primary': {'used_percent': float(u5), 'window_minutes': 300, 'resets_at': int(now) + 3600},
          'secondary': {'used_percent': float(u7), 'window_minutes': 10080, 'resets_at': int(now) + 3 * 86400}}
    line = {'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', g), 'type': 'event_msg',
            'payload': {'type': 'token_count', 'info': None, 'rate_limits': rl}}
    with open(os.path.join(d, 'rollout-%d-%d.jsonl' % (time.time_ns(), n)), 'w', encoding='utf-8') as rf:
        meta = {'timestamp': line['timestamp'], 'type': 'session_meta', 'payload': {}}
        rf.write(json.dumps(meta) + '\n' + json.dumps(line) + '\n')

if SC != 'slow_done':
    print(json.dumps({'type': 'turn.started'}))
if err:
    print(json.dumps({'type': 'error', 'message': err})); sys.exit(1)
open(opt('-o'), 'w', encoding='utf-8').write(resp)
print(json.dumps({'type': 'turn.completed'}))
