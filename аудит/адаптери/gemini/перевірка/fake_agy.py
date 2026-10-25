#!/usr/bin/env python3
"""Фальшивий agy для перевірки обгортки: stream-json і print, сценарій — змінна FAKE_SCENARIO."""
import json, os, re, subprocess, sys, time, uuid

SC = os.environ.get('FAKE_SCENARIO', 'abandon_then_done')
STATE = os.environ['FAKE_STATE']          # тека стану між процесами
args = sys.argv[1:]
with open(os.path.join(STATE, 'argv.log'), 'a') as f:
    f.write(json.dumps(args, ensure_ascii=False) + '\n')

def opt(name):
    return args[args.index(name) + 1] if name in args else ''

if args[:1] == ['models']:
    print('gemini-3.8-flash-high Gemini 3.8 Flash (High)\nclaude-opus-5-5-high Claude Opus 5.5 (High)\nBad Line')
    sys.exit(0)
if args[:2] == ['-p', '/usage']:
    # Квота як дані (0 ходів): FAKE_USAGE — ok | flash0 | claude0 | all0 | used | envelope | garbage | fail; FAKE_RESET — хв до скидання.
    import datetime
    mode = os.environ.get('FAKE_USAGE', 'ok')
    reset = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=int(os.environ.get('FAKE_RESET', '137')))).strftime('%Y-%m-%dT%H:%M:%SZ')
    left = {'Gemini 3.5 Flash': 34, 'Gemini 3.1 Pro': 0, 'Claude & GPT': 0}
    if mode in ('flash0', 'all0'):
        left['Gemini 3.5 Flash'] = 0
    if mode == 'claude0':
        left['Claude & GPT'] = 0
    if mode == 'fail':
        sys.exit(1)
    if mode == 'garbage':
        print('Model quotas: Flash 34% remaining'); sys.exit(0)
    if mode == 'used':
        doc = {'quotas': [{'model_group': k, 'usedPercent': 100 - v, 'resetsAt': reset} for k, v in left.items()]}
    else:
        doc = {'model_quotas': [{'name': k, 'remaining_percent': v, 'reset_time': reset} for k, v in left.items()]}
    if mode == 'envelope':
        doc = {'conversation_id': 'u', 'status': 'SUCCESS', 'response': json.dumps(doc)}
    print(json.dumps(doc)); sys.exit(0)
conv = opt('--conversation') or str(uuid.uuid4())
model = opt('--model')
stream = opt('--input-format') == 'stream-json'

def git(*a):
    return subprocess.run(['git', *a], check=True, capture_output=True, text=True).stdout.strip()

def commit(path, text='x'):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'a') as f:
        f.write(text + '\n')
    git('add', path)
    git('-c', 'user.name=g', '-c', 'user.email=g@x', 'commit', '-q', '-m', 'крок: ' + path)
    return git('rev-parse', 'HEAD')

def turn_no():
    p = os.path.join(STATE, 'turns_' + conv)
    n = int(open(p).read()) + 1 if os.path.exists(p) else 1
    open(p, 'w').write(str(n))
    return n

def act(prompt):
    m = re.search(r'ГОТОВО gemini/(\S+) <', prompt)
    slug = m.group(1) if m else '?'
    n = turn_no()
    done = lambda: 'Готово.\nНОУТБУК ГОТОВО gemini/%s %s' % (slug, git('rev-parse', 'HEAD'))
    if model == 'bad-model':
        return 'ERROR', '', 'invalid model selection (--model "bad-model")'
    if SC == 'abandon_then_done':
        if n == 1:
            commit('робота/а.txt'); return 'SUCCESS', 'Запустив фонове завдання, чекаю результату.', ''
        return 'SUCCESS', done(), ''
    if SC == 'github':
        commit('.github/workflows/evil.yml'); return 'SUCCESS', done(), ''
    if SC == 'github_renamed':
        commit('.github/workflows/z.yml'); git('mv', '.github/workflows/z.yml', 'z.yml')
        git('-c', 'user.name=g', '-c', 'user.email=g@x', 'commit', '-q', '-m', 'mv'); return 'SUCCESS', done(), ''
    if SC == 'wrapper':
        commit('аудит/адаптери/gemini/gemini_publish.ps1'); return 'SUCCESS', done(), ''
    if SC == 'blocked':
        commit('робота/б.txt'); return 'SUCCESS', 'ЗАБЛОКОВАНО: чекаю рішення', ''
    if SC == 'wrong_sha':
        if n == 1:
            commit('робота/в.txt'); return 'SUCCESS', 'НОУТБУК ГОТОВО gemini/%s %s' % (slug, '0' * 40), ''
        return 'SUCCESS', done(), ''
    if SC == 'dirty':
        if n == 1:
            commit('робота/г.txt'); open('сміття.tmp', 'w').write('x'); return 'SUCCESS', done(), ''
        os.remove('сміття.tmp'); return 'SUCCESS', done(), ''
    if SC == 'never':
        return 'SUCCESS', 'Працюю далі.', ''
    if SC == 'hang':
        if n == 1:
            commit('робота/д.txt'); time.sleep(60); return 'SUCCESS', 'пізно', ''
        return 'SUCCESS', done(), ''
    if SC == 'die':
        if n == 1:
            commit('робота/е.txt'); sys.exit(3)
        return 'SUCCESS', done(), ''
    if SC == 'quota429':
        return 'ERROR', '', '429 RESOURCE_EXHAUSTED: quota exceeded'
    if SC == 'nothing':
        return 'SUCCESS', 'ЗАБЛОКОВАНО: нема доступу', ''
    raise SystemExit('невідомий сценарій ' + SC)

def result(status, resp, err, n):
    r = {'conversation_id': conv, 'status': status, 'response': resp, 'duration_seconds': 1, 'num_turns': n,
         'usage': {}}
    if err:
        r['error'] = err
    return r

if stream:
    print(json.dumps({'event': 'init', 'conversation_id': conv, 'init': {}}), flush=True)
    for line in sys.stdin:
        msg = json.loads(line)
        content = msg['message']['content']
        with open(os.path.join(STATE, 'prompts.log'), 'a') as f:
            f.write(content + '\n=====\n')
        st, resp, err = act(content)
        print(json.dumps({'event': 'step_update', 'step_update': {'conversation_id': conv}}), flush=True)
        print(json.dumps({'event': 'result', 'result': result(st, resp, err, 1)}, ensure_ascii=False), flush=True)
        if st == 'ERROR':
            sys.exit(1)
else:
    p = opt('-p')
    path = re.search(r'файл (\S+) ', p).group(1)
    content = open(path, encoding='utf-8').read()
    with open(os.path.join(STATE, 'prompts.log'), 'a') as f:
        f.write(content + '\n=====\n')
    st, resp, err = act(content)
    print(json.dumps(result(st, resp, err, 1), ensure_ascii=False))
    sys.exit(1 if st == 'ERROR' else 0)
