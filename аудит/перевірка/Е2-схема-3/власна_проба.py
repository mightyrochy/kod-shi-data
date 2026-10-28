"""Незалежні виміри форми на записах і справжнього моста; без генерації."""
import copy
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SOURCES = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / 'джерела'
sys.path.insert(0, str(SOURCES))
import протокол as P
import збирач_промптів as Z
import знання_дріт as K
import дріт_моделі as D
import вердикт_моделі as V
import повнота_образу as F


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def replay():
    prefix = 'аудит/проби/автоживий-bd628bb29a90637ae18833c92eceb8230bd9b995'
    records = []
    recording_sha = 'dd1327c9a809f03ffb7663089183950b623e976c'
    names = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'ls-tree', '-r', '--name-only',
                                     recording_sha, '--', prefix], cwd=ROOT).decode('utf8').splitlines()
    for name in names:
        path = ROOT / name
        if path.parent.name != 'відповіді' or 'ВЕРДИКТ_V1' not in path.name:
            continue
        text_record = subprocess.check_output(['git', 'show', recording_sha + ':' + name], cwd=ROOT).decode('utf8')
        prompt_text, reply = re.split(r'\n\n── ВІДПОВІДЬ [^\n]*\n', text_record, maxsplit=1)
        old = json.loads(prompt_text[prompt_text.index('{'):])
        full = K.відновити(old) if old.get('knowledge_legend') else copy.deepcopy(old)
        is_repair = 'ОБРАЗИ_V1' in path.name
        new = D.кандидати_вердикту(full)
        table = {r['n']: r for r in K.рядки_таблиці(new['candidates'])}
        old_items = [r for o in full['verdict'] for r in o['your_outfit']['items']] + full.get('showcase', [])
        assert all(table[r['n']] == r for r in old_items)
        rebuilt = copy.deepcopy(new)
        for o in rebuilt['verdict']:
            o['your_outfit']['items'] = [table[n] for n in o['your_outfit']['items']]
        if 'showcase' in rebuilt:
            rebuilt['showcase'] = [table[n] for n in rebuilt['showcase']]
        del rebuilt['candidates']
        assert rebuilt == full, 'Змінився факт поза формою довідника'
        declaration = V.оголошення_ремонту(new) if is_repair else F.ВИБІР
        wire = Z.зібрати(declaration, new)
        restored = K.відновити(wire) if wire.get('knowledge_legend') else wire
        assert {r['n']: r for r in K.рядки_таблиці(restored['candidates'])} == table
        if old.get('format_error'):
            wire['format_error'] = old['format_error']
        obj, error = P.розбір(reply)
        strict_error = None
        # Кінцева відповідь після роздумів мусить бути одним цілим JSON.
        final_reply = reply.rsplit('</think>', 1)[-1].strip()
        try:
            json.loads(final_reply)
        except ValueError as exc:
            strict_error = str(exc)
        recovered = False
        if error:
            # Беремо лише ціле поле, реально записане до обриву; хвіст не вигадуємо.
            start = re.search(r'"chosen"\s*:', reply).end()
            chosen, _ = json.JSONDecoder().raw_decode(reply[start:].lstrip())
            assert len(chosen) == old['outfits_wanted']
            obj = {'version': '1', 'outfits': chosen}
            start = re.search(r'"needed"\s*:', reply)
            if start:
                obj['needed'], _ = json.JSONDecoder().raw_decode(reply[start.end():].lstrip())
            recovered = True
        projected = copy.deepcopy(obj)
        if is_repair:
            why = {o['id']: o.get('why') for o in obj.get('chosen', [])}
            allowed = Z.скелет(declaration)['outfits'][0]
            outfits = []
            for outfit in obj['outfits']:
                item = {k: copy.deepcopy(v) for k, v in outfit.items() if k in allowed}
                item['items'] = [r['n'] if isinstance(r, dict) else r for r in outfit['items']]
                if why.get(item.get('id')):
                    item['why'] = why[item['id']]
                outfits.append(item)
            projected = dict(version='1', outfits=outfits)
            if 'needed' in obj:
                projected['needed'] = obj['needed']
            assert [o['items'] for o in projected['outfits']] == [
                [r['n'] if isinstance(r, dict) else r for r in o['items']] for o in obj['outfits']]
        text = dump(projected)
        schema = 'ОБРАЗИ_V1' if is_repair else 'ВИБІР_V1'
        parsed, err, notes = P.розбір_за_схемою(text, schema)
        violations = P.перевірити(P.СХЕМИ[schema], parsed)
        records.append(dict(файл=str(path.relative_to(ROOT)), вхід_до=len(dump(old)), вхід_після=len(dump(wire)),
                            вихід_до=len(reply.strip()), проєкція=len(text), фактів=len(table),
                            помилка_сирого_JSON=strict_error, відновлено_ціле_поле=recovered,
                            помилка_розбору=err, нотатки=notes, порушення_схеми=violations))
    assert len(records) == 9, len(records)
    (OUT / 'записи.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    for r in records:
        print(Path(r['файл']).name, r['вхід_до'], r['вхід_після'], r['вихід_до'], r['проєкція'],
              'сирий JSON:', r['помилка_сирого_JSON'], 'схема:', len(r['порушення_схеми']))


def bridge_probe():
    os.chdir(SOURCES)
    import bridge as B
    import схеми_розбору as S
    import feed
    feed.каталог_на_диску('каталог_повний.xml')
    brief = dict(json.loads(Path('стенд_вх.json').read_text(encoding='utf8')), сід=4242,
                 варіантів=10, ремонт_варіантів=5, бюджет_символів=120000, без_фото=1, пакети=1)
    requests = json.loads(B.виклик('запити', json.dumps(brief, ensure_ascii=False)))
    pool = requests['пакети']['1']['пул']
    outfits = [dict(ід='о%d' % (i + 1), речі=[pool[s][i % len(pool[s])]['н']
                   for s in ('верх', 'низ', 'взуття', 'сумка')]) for i in range(10)]
    brief['текст_моделі'] = json.dumps(dict(версія='1', образи=outfits), ensure_ascii=False)
    times, lengths = [], []
    for _ in range(3):
        t = time.perf_counter()
        answer = B.виклик('від_моделі', json.dumps(brief, ensure_ascii=False))
        times.append(time.perf_counter() - t)
        lengths.append(len(answer))
    decoded = json.loads(answer)
    assert not decoded.get('помилка'), decoded.get('помилка')
    tag = 'до' if SOURCES != ROOT / 'джерела' else 'після'
    scratch = Path('C:/Users/gemini/gemini-runs/20261028-171005-42cc673ca36e/e2-check')
    (scratch / ('відповідь-моста-' + tag + '.json')).write_text(answer, encoding='utf8')
    result = dict(джерела=str(SOURCES), секунд=times, медіана=statistics.median(times),
                  довжини=lengths, ключі_моста=list(decoded),
                  ремонт=len(decoded['промпт_ремонту']), вибір=len(decoded['промпт_лише_вибору']))
    result['випадки'] = parser_cases()
    (OUT / ('міст-' + tag + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: v for k, v in result.items() if k != 'випадки'}, ensure_ascii=False, indent=2))


def parser_cases():
    import схеми_розбору as S
    from пакет_моделі import номери_речей
    candidates = {s: [dict(id='probe-' + str(i) + '@shop', слот=s)]
                  for i, s in enumerate(('верх', 'низ', 'взуття', 'сумка'), 1)}
    numbers, _ = номери_речей(candidates)
    items = ['#%s·%s' % pair for pair in numbers.values()]
    one = dict(version='1', outfits=[dict(id='o1', why='Її день', caption='Світлий задум',
                                        day='Зручний день.', items=items)])
    samples = {'звичайна': dump(one), 'обрізана': dump(one)[:-18],
               'невідомий_номер': dump(dict(version='1', outfits=[dict(id='o1', items=['#999999·99'])])),
               'повтор_номера': dump(dict(version='1', outfits=[dict(id='o1', items=[items[0]] * 2)])),
               'порожня': dump(dict(version='1', outfits=[])),
               'стара': dump(dict(one, chosen=[dict(id='o1', why='Її день')]))}
    six = dict(version='1', outfits=[dict(one['outfits'][0], id='o' + str(i)) for i in range(1, 7)])
    samples['понад_просили'] = dump(six)
    samples['старий_вибір_понад'] = dump(dict(six, chosen=[dict(id='o' + str(i), why='Її день')
                                                        for i in (6, 4, 2, 5, 1)]))
    result = {}
    for name, text in samples.items():
        obj, err, notes = P.розбір_за_схемою(text, 'ОБРАЗИ_V1')
        parsed = S._розбір_образи_v1(text, кандидати=candidates, просили=5)
        result[name] = dict(причина=err, нотатки=notes, розбір=parsed,
                                      помилки_схеми=P.перевірити(P.ОБРАЗИ_V1, obj) if obj is not None else [])
    assert len(result['звичайна']['розбір'][0]['ід']) == 4
    assert result['стара']['розбір'][0]['ід'] == result['звичайна']['розбір'][0]['ід']
    assert result['обрізана']['нотатки']['обрізано']
    assert not result['обрізана']['розбір'][0]['готово']
    assert not result['невідомий_номер']['розбір'][0]['готово']
    assert len(result['повтор_номера']['розбір'][0]['ід']) == 1
    assert result['повтор_номера']['розбір'][0]['двічі']
    assert not result['порожня']['розбір'][0]['готово']
    assert len(result['понад_просили']['розбір']) == 5
    # Історичний договір зберігає порядок відповіді серед членів chosen.
    assert [r['ід_відповіді'] for r in result['старий_вибір_понад']['розбір']] == ['о1', 'о2', 'о4', 'о5', 'о6']
    return result


if __name__ == '__main__':
    if sys.argv[1] == 'записи':
        replay()
    elif sys.argv[1] == 'випадки':
        tag = 'до' if SOURCES != ROOT / 'джерела' else 'після'
        result = parser_cases()
        (OUT / ('випадки-' + tag + '.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        old_path = OUT / ('міст-' + tag + '.json')
        if old_path.exists():
            old = json.loads(old_path.read_text(encoding='utf8'))
            old['випадки'] = result
            old_path.write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print('8/8 власних випадків:', tag)
    else:
        bridge_probe()
