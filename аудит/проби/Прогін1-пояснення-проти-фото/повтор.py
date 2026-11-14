"""Повторює збирання промпту й розбір записаних відповідей без нового виклику моделі."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request


def replay(here, calls):
    """Віддає записані відповіді через штатний сервер replay_сцени.py й завжди прибирає сервер."""
    with tempfile.TemporaryDirectory(prefix='пояснення-', dir=os.environ.get('TEMP') or os.environ.get('TMP')) as temp:
        folder = Path(temp)
        (folder / 'VIDPOVIDI').mkdir()
        (folder / 'лог.txt').write_text('', encoding='utf8')
        for number, (old, fresh, answer) in enumerate(calls, 1):
            path = folder / 'VIDPOVIDI' / f'seed0_{number}_опис.txt'
            path.write_text(f'── ПРОМПТ ({len(old)} симв.) ──\n{old}\n\n'
                f'── ВІДПОВІДЬ (HTTP 200) ──\n{json.dumps(answer, ensure_ascii=False)}\n', encoding='utf8')
        server = subprocess.Popen([sys.executable, str(here.parent / 'replay_сцени.py'), str(folder), '0',
            '--за-порядком'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding='utf8', env=dict(os.environ, PYTHONIOENCODING='utf-8'),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        prefix = []
        try:
            while True:
                line = server.stdout.readline()
                prefix.append(line)
                if line.startswith('REPLAY_READY '):
                    url = line.strip().split(' ', 1)[1]
                    break
                if not line:
                    raise RuntimeError(''.join(prefix))
            results = []
            for old, fresh, answer in calls:
                request = urllib.request.Request(url + '/chat/completions',
                    data=json.dumps({'messages': [{'role': 'user', 'content': fresh}]}).encode(),
                    headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(request, timeout=30) as response:
                    results.append(json.loads(json.loads(response.read())['choices'][0]['message']['content']))
            return results
        finally:
            server.terminate()
            tail, _ = server.communicate(timeout=15)
            (here / 'replay.log').write_text(''.join(prefix) + tail, encoding='utf8')


def main():
    """Звіряє збереження предметних входів та показує межу повтору для семантичного мірила."""
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here.parents[2] / 'джерела'))
    import pipeline
    import збирач_промптів as builder
    import розбір_відповідей as description
    import мовний_шар as language
    data = json.loads((here / 'джерела.json').read_text(encoding='utf8'))
    measurements = json.loads((here / 'твердження.json').read_text(encoding='utf8'))
    results = []
    calls = []
    for recorded in data['образи']:
        old = recorded['вхід']
        facts = {k: copy.deepcopy(v) for k, v in old.items() if k not in ('version', 'task')}
        fresh = builder.зібрати(description.ОПИС, facts, мова_тексту='English')
        assert {k: v for k, v in fresh.items() if k not in ('version', 'task')} == facts
        calls.append((json.dumps(old, ensure_ascii=False, separators=(',', ':')),
                      json.dumps(fresh, ensure_ascii=False, separators=(',', ':')), recorded['вихід']))
        translation = recorded['переклад']['вхід']
        text = translation if isinstance(translation, str) else '\n'.join(b.get('text', '') for b in translation)
        # Речі й таблиця текстів — незмінний вхід живого виклику; змінюється лише стала частина промпту прози.
        end = text.index('Речі образу —')
        prefix, _, _ = language.ПРОМПТ_ВИХОДУ.rpartition('ТЕКСТИ:\n')
        calls.append((text, prefix + text[end:], recorded['переклад']['вихід']))
        items = old['outfit']['items']
        candidates = [dict(id=i['n'], н=i['n'], назва=i['n']) for i in items]
        parsed = pipeline.опис_відповідь_з_json(json.dumps(recorded['вихід']),
            каталог=candidates, склад=[i['n'] for i in items])
        own = [r for r in measurements if (r['с'], r['запит']) == (recorded['с'], recorded['рядок'])]
        count = sum(len(r.get('в', [])) for r in own)
        results.append({'с': recorded['с'], 'рядок': recorded['рядок'], 'речей': len(items),
            'предметний_вхід_збережено': True, 'тверджень_без_опори_до': count,
            'тверджень_без_опори_повтор': count,
            'розбір': {k: parsed.get(k) for k in ('помилки', 'повторний_виклик', 'не_описано')},
            'промпт_після': fresh})
    responses = replay(here, calls)
    assert len(responses) == 14 and all(response == call[2] for response, call in zip(responses, calls))
    output = {'образи': results, 'промпт_перекладача_після': language.ПРОМПТ_ВИХОДУ,
        'підсумок': {'образів': len(results), 'речей': sum(r['речей'] for r in results), 'відповідей_через_replay_сцени': len(responses),
            'без_опори_до': sum(r['тверджень_без_опори_до'] for r in results),
            'без_опори_повтор': sum(r['тверджень_без_опори_повтор'] for r in results),
            'самосуперечностей_пояснення_до': 2, 'самосуперечностей_пояснення_повтор': 2,
            'назва_проти_пояснення_до': 1, 'назва_проти_пояснення_повтор': 1,
            'семантика_нової_відповіді': 'не виміряно: нових відповідей моделі немає'}}
    (here / 'повтор.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps(output['підсумок'], ensure_ascii=False))


if __name__ == '__main__':
    main()
