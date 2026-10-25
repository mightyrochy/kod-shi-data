#!/usr/bin/env python3
"""Фальшивий `codex` (рушій М.9-В) для стенду обгортки: сценарій — FAKE_SCENARIO, вид — FAKE_KIND=codex.
Codex: `exec ... --json -o <файл> <промпт>` -> відповідь у файлі -o, події JSONL у stdout."""
import json, os, re, subprocess, sys

KIND = os.environ['FAKE_KIND']
SC = os.environ.get('FAKE_SCENARIO', 'abandon_then_done')
STATE = os.environ['FAKE_STATE']
args = sys.argv[1:]
with open(os.path.join(STATE, KIND + '.argv.log'), 'a') as f:
    f.write(json.dumps(args, ensure_ascii=False) + '\n')

def opt(name):
    return args[args.index(name) + 1] if name in args else ''

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
else:
    raise SystemExit('невідомий сценарій ' + SC)

print(json.dumps({'type': 'turn.started'}))
if err:
    print(json.dumps({'type': 'error', 'message': err})); sys.exit(1)
open(opt('-o'), 'w', encoding='utf-8').write(resp)
print(json.dumps({'type': 'turn.completed'}))
