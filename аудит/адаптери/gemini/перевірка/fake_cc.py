#!/usr/bin/env python3
# Підробний `claude -p … --output-format stream-json` для стенда claude_run.ps1: сценарій — FAKE_CC_SCENARIO,
# argv і промпт — рядком JSON у FAKE_CC_LOG, свій pid — у FAKE_CC_LOG.pid (pid нащадка — .child). Гілку
# `claude/<наряд>` пушить у origin клону (поточна тека), як сесія.
import json, os, re, subprocess, sys, time
sc = os.environ.get('FAKE_CC_SCENARIO', 'done')
open(os.environ['FAKE_CC_LOG'] + '.pid', 'w').write(str(os.getpid()))
prompt = sys.stdin.read()
with open(os.environ['FAKE_CC_LOG'], 'a', encoding='utf-8') as f:
    f.write(json.dumps({'argv': sys.argv[1:], 'stdin': prompt}, ensure_ascii=False) + '\n')
slug = re.search(r'аудит/наряди/(.+?)\.md', prompt).group(1)
branch = 'claude/' + slug
def hold(slug):
    # Стенд смуг: FAKE_HOLD с роботи й рядки start/end у FAKE_TIMELINE — щоб виміряти, що йде водночас.
    tl = os.environ.get('FAKE_TIMELINE')
    if not tl:
        return
    def mark(k):
        with open(tl, 'a') as f:
            f.write('%s %s %d\n' % (k, slug, int(time.time() * 1000)))
    mark('start'); time.sleep(float(os.environ.get('FAKE_HOLD', '0'))); mark('end')

def emit(o):
    sys.stdout.write(json.dumps(o, ensure_ascii=False) + '\n'); sys.stdout.flush()
def git(*a):
    return subprocess.run(['git', *a], check=True, capture_output=True, text=True).stdout.strip()
def push():
    tree = git('rev-parse', 'origin/main^{tree}')
    sha = git('commit-tree', tree, '-p', 'origin/main', '-m', 'звіт ' + sc)
    git('push', '-q', 'origin', '+' + sha + ':refs/heads/' + branch)
    return sha
def result(text, err=False, code=0):
    emit({'type': 'result', 'subtype': 'error_during_execution' if err else 'success', 'is_error': err, 'result': text})
    sys.exit(code)
emit({'type': 'system', 'subtype': 'init', 'model': sys.argv[sys.argv.index('--model') + 1]})
emit({'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'працюю'}]}})
if os.environ.get('FAKE_CC_RL'):
    # Подія ліміту, як у живого claude 2.1.300 (26.10): status, resetsAt, unifiedWindows з utilization і resetsAt.
    t = int(time.time()); u = int(os.environ.get('FAKE_CC_QUOTA_UNTIL', '0'))
    rej = sc == 'quota_until' and t < u
    emit({'type': 'rate_limit_event', 'rate_limit_info': {'status': 'rejected' if rej else 'allowed', 'resetsAt': u if rej else t + 14400,
          'rateLimitType': 'five_hour', 'unifiedWindows': {'five_hour': {'utilization': 1.0 if rej else 0.32, 'resetsAt': u if rej else t + 14400},
                                                           'seven_day': {'utilization': 0.82, 'resetsAt': t + 400000}}}})
if sc == 'quota_until':
    if time.time() < int(os.environ.get('FAKE_CC_QUOTA_UNTIL', '0')):
        result("You've hit your limit · resets soon", True, 1)
    sc = 'done'
if sc == 'done':
    hold(slug)
    result('Готово.\n\n**НОУТБУК ГОТОВО `%s` %s**' % (branch, push()))
if sc == 'wrong_sha':
    push(); result('НОУТБУК ГОТОВО %s %s' % (branch, 'a' * 40))
if sc == 'bad_branch':
    result('НОУТБУК ГОТОВО main %s' % push())
if sc == 'blocked':
    push(); result('НОУТБУК ЗАБЛОКОВАНО: LM Studio не відповідає, гілка %s.' % branch)
if sc == 'no_report':
    result('Зроблено, усе гаразд.')
if sc == 'die':
    sys.exit(3)
if sc == 'hang':
    time.sleep(600)
if sc == 'effort':
    sys.stderr.write("Unknown --effort value 'ultra' — ignoring it and using the default effort. Valid values: low, medium, high\n")
    sys.stderr.flush(); time.sleep(600)
if sc == 'auth':
    result('Not logged in · Please run /login', True, 1)
if sc == 'quota':
    # ліміт зі скиданням через 10 хв (формат «…|<unix>» давніх claude; новіші — подія rate_limit_event)
    result('Claude AI usage limit reached|%d' % (int(time.time()) + 600), True, 1)
if sc == 'bad_model':
    result("There's an issue with the selected model (x). It may not exist or you may not have access to it.", True, 1)
if sc == 'child_holds_stdout':
    # Сервер, піднятий сесією, лишається з успадкованим stdout після кінця claude.
    c = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)'], stdout=sys.stdout,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    open(os.environ['FAKE_CC_LOG'] + '.child', 'w').write(str(c.pid))
    result('НОУТБУК ГОТОВО %s %s' % (branch, push()))
if sc == 'closed':
    # Закрив stdout і stderr, а процес живий і мовчить: завислість, хоч потоків уже нема.
    os.close(1); os.close(2); time.sleep(600)
if sc == 'noise':
    # Лише не-JSON рядки після подій: таймер завислості вони не скидають.
    for i in range(40):
        sys.stdout.write('шум %d\n' % i); sys.stdout.flush(); time.sleep(0.5)
    result('НОУТБУК ГОТОВО %s %s' % (branch, push()))
if sc == 'pause':
    # Справжні події частіше за поріг, хоч усього довше: не завислість.
    for i in range(10):
        emit({'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': 'крок %d' % i}]}}); time.sleep(0.5)
    result('НОУТБУК ГОТОВО %s %s' % (branch, push()))
sys.exit(9)
