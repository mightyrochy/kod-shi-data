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

prompt_arg = args[-1]
path = re.search(r'файл (\S+) ', prompt_arg).group(1)
content = open(path, encoding='utf-8').read()
open(os.path.join(STATE, KIND + '.prompts.log'), 'a').write(content + '\n=====\n')
p = os.path.join(STATE, KIND + '.turns')
n = int(open(p).read()) + 1 if os.path.exists(p) else 1
open(p, 'w').write(str(n))
m = re.search(r'ГОТОВО gemini/(\S+) <', content)
slug = m.group(1) if m else '?'
done = 'Готово.\nНОУТБУК ГОТОВО gemini/%s %s' % (slug, git('rev-parse', 'HEAD'))
err = ''
if SC == 'abandon_then_done':
    if n == 1:
        commit('робота/а.txt'); resp = 'Запустив фонове завдання, чекаю результату.'
    else:
        resp = done
elif SC == 'github':
    commit('.github/workflows/evil.yml'); resp = done
elif SC == 'quota429':
    resp, err = '', '429 RESOURCE_EXHAUSTED: quota exceeded'
elif SC == 'auth':
    resp, err = '', 'Not logged in. Please log in'
elif SC == 'blocked':
    commit('робота/б.txt'); resp = 'ЗАБЛОКОВАНО: чекаю рішення'
elif SC == 'slow_done':
    # довгий прогін із подіями щосекунди: довший за TotalMinutes обгортки, але без завислості
    commit('робота/а.txt'); resp = done
    print(json.dumps({'type': 'turn.started'}), flush=True)
    for i in range(int(os.environ.get('FAKE_SLOW_SECONDS', '40'))):
        time.sleep(1); print(json.dumps({'type': 'item.completed', 'n': i}), flush=True)
elif SC == 'hang':
    # одна подія й тиша: завислість
    print(json.dumps({'type': 'turn.started'}), flush=True)
    time.sleep(300); raise SystemExit(0)
else:
    raise SystemExit('невідомий сценарій ' + SC)

if SC != 'slow_done':
    print(json.dumps({'type': 'turn.started'}))
if err:
    print(json.dumps({'type': 'error', 'message': err})); sys.exit(1)
open(opt('-o'), 'w', encoding='utf-8').write(resp)
print(json.dumps({'type': 'turn.completed'}))
