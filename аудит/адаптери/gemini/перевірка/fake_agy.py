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
if args[:1] == ['--version']:
    print(os.environ.get('FAKE_VERSION_OUT') or ('agy ' + os.environ.get('FAKE_VERSION', '1.1.11'))); sys.exit(0)
if args[:2] == ['-p', '/usage']:
    # Квота як дані (0 ходів): FAKE_USAGE — tsv | tsv_nohdr | proclaude | ok | flash0 | claude0 | all0 | used | envelope | garbage | fail; FAKE_RESET — хв до скидання.
    import datetime
    mode = os.environ.get('FAKE_USAGE', 'ok')
    if mode == 'live':
        # Формат живого agy 1.4.7 (26.10): без заголовка, «група ⇥ вікно ⇥ NN% ⇥ скидання ISO», рядок на вікно.
        # Gemini 4 Argon — 0 % до FAKE_ZERO_UNTIL (unix), далі 100 %.
        now = datetime.datetime.now(datetime.timezone.utc); iso = lambda t: t.strftime('%Y-%m-%dT%H:%M:%SZ')
        until = datetime.datetime.fromtimestamp(int(os.environ.get('FAKE_ZERO_UNTIL', '0')), datetime.timezone.utc)
        week = iso(now + datetime.timedelta(days=6)); five = iso(now + datetime.timedelta(hours=4))
        argon = 0 if now < until else 100
        print('\n'.join(['Gemini Models\tWeekly Limit Remaining\t100%\t' + week, 'Gemini Models\tFive Hour Limit Remaining\t100%\t' + five,
                         'Claude and GPT models\tWeekly Limit Remaining\t100%\t' + week, 'Claude and GPT models\tFive Hour Limit Remaining\t100%\t' + five,
                         'Gemini 4 Argon\tGemini 4 Argon Weekly Limit\t%d%%\t%s' % (argon, iso(until if argon == 0 else now + datetime.timedelta(days=7)))]))
        sys.exit(0)
    reset = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=int(os.environ.get('FAKE_RESET', '137')))).strftime('%Y-%m-%dT%H:%M:%SZ')
    left = {'Gemini 3.5 Flash': 34, 'Gemini 3.1 Pro': 0, 'Claude & GPT': 0}
    if mode == 'proclaude':
        left['Claude & GPT'] = 50
    if mode in ('flash0', 'all0'):
        left['Gemini 3.5 Flash'] = 0
    if mode == 'claude0':
        left['Claude & GPT'] = 0
    if mode == 'fail':
        sys.exit(1)
    if mode == 'garbage':
        print('Model quotas: Flash 34% remaining'); sys.exit(0)
    if mode in ('tsv', 'tsv_nohdr'):
        # Формат з changelog agy 1.1.11: запис на рядок, поля розділені табами; колонки — припущення стенду.
        rows = [('Group', 'Remaining', 'Resets in')] if mode == 'tsv' else []
        rows += [(k, '%d%%' % v, '2h 17m') for k, v in left.items()]
        print('\n'.join('\t'.join(r) for r in rows)); sys.exit(0)
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

from fake_timeline import тримати as hold

def act(prompt):
    m = re.search(r'ГОТОВО gemini/(\S+) <', prompt)
    slug = m.group(1) if m else '?'
    n = turn_no()
    done = lambda: 'Готово.\nНОУТБУК ГОТОВО gemini/%s %s' % (slug, git('rev-parse', 'HEAD'))
    if model.startswith('gemini-4-argon') and os.environ.get('FAKE_USAGE') == 'live' and time.time() < int(os.environ.get('FAKE_ZERO_UNTIL', '0')):
        # Квота групи на нулі: як живий agy — 429 на першому ж ході.
        return 'ERROR', '', '429 RESOURCE_EXHAUSTED: quota exceeded'
    if model == 'bad-model':
        return 'ERROR', '', 'invalid model selection (--model "bad-model")'
    if SC == 'commit_done':
        hold(slug); commit('робота/%s.txt' % slug); return 'SUCCESS', done(), ''
    if SC == 'abandon_then_done':
        if n == 1:
            commit('робота/а.txt'); return 'SUCCESS', 'Запустив фонове завдання, чекаю результату.', ''
        return 'SUCCESS', done(), ''
    if SC == 'github':
        commit('.github/workflows/evil.yml'); return 'SUCCESS', done(), ''
    if SC == 'secret_path':
        commit('.codex/auth.json', '{}'); return 'SUCCESS', done(), ''
    if SC == 'secret_content':
        commit('робота/нотатки.md', 'token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'); return 'SUCCESS', done(), ''
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
