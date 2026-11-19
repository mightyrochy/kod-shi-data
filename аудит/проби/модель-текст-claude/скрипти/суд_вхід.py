"""Сліпе порівняння «Build outfits»: на кожен вхід — відповіді трьох моделей під літерами A/B/C (перемішано сідом)."""
import json, random, sys, collections
Д = '/tmp/вимір/дані/'
сторінка = {json.loads(л)['id']: json.loads(л) for л in open(Д + 'сторінка.jsonl')}
ids = json.load(open(Д + 'збірка_ids.json'))
відп = {'sonnet_low': {}, 'haiku_low': {}}
for к in відп:
    for л in open(Д + к + '.jsonl'):
        з = json.loads(л); відп[к][з['id']] = з['текст']
for і, з in сторінка.items():
    pass
def вхід(і):
    т = json.loads(сторінка[і]['запит']); б = т['messages'][0]['content']
    txt = б[0]['text'] if isinstance(б, list) else б
    return json.JSONDecoder().raw_decode(txt[txt.index('{'):])[0]
def обʼєкт(т):
    try: return json.JSONDecoder().raw_decode(т[т.index('{'):])[0]
    except Exception: return None
за_с = collections.defaultdict(list)
for і in ids: за_с[і.split('#')[0]].append(і)
вибрані = [зз[к] for с, зз in sorted(за_с.items()) for к in (0, 2)]
rnd = random.Random(1911)
ключ, рядки, прилади = {}, [], collections.defaultdict(collections.Counter)
for і in ids:
    о = вхід(і); пул = {р[0]: р for р in о['pool']['rows']}; кол = о['pool']['cols']
    варіанти = {'sonnet_low': відп['sonnet_low'].get(і, ''), 'haiku_low': відп['haiku_low'].get(і, ''),
                'sonnet_13_11': json.loads(сторінка[і]['відповідь'])['content'][0]['text']}
    for м, т in варіанти.items():
        в = обʼєкт(т); п = прилади[м]; п['викликів'] += 1
        if not в or not isinstance(в.get('outfits'), list): п['JSON не розібрано'] += 1; continue
        ос = в['outfits']; п['образів'] += len(ос); п['образів замовлено'] += о.get('outfits_wanted') or 0
        вжито = collections.Counter()
        for x in ос:
            its = [str(n).split('/')[0] for n in x.get('items', [])]
            п['речей'] += len(its); п['вигаданих n'] += sum(1 for n in its if n not in пул)
            вжито.update(its)
            if not (4 <= len(its) <= 7): п['образів поза 4–7 речей'] += 1
        п['речей понад 2 образи'] += sum(1 for n, к in вжито.items() if к > 2)
    if і not in вибрані: continue
    м = list(варіанти); rnd.shuffle(м); ключ[і] = dict(zip('ABC', м))
    c = о['case']; ж = (c.get('field_quotes') or {})
    рядки.append(f"\n## {і.split('#')[0]} · виклик {і.split('#')[1]}\nЇї випадок: {c.get('event')}; її слова: {json.dumps(ж, ensure_ascii=False)}; "
                 f"відмови: {json.dumps(c.get('refusals'), ensure_ascii=False)}; день: {json.dumps(о.get('day'), ensure_ascii=False)[:300]}; "
                 f"її палітра: {json.dumps((о.get('person') or {}).get('palette'), ensure_ascii=False)[:450]}; образів замовлено: {о.get('outfits_wanted')}; ідеї (poles): {json.dumps(о.get('poles'), ensure_ascii=False)[:400]}")
    for літ, мод in ключ[і].items():
        в = обʼєкт(варіанти[мод]); рядки.append(f"\n### {літ}")
        if not в or not isinstance(в.get('outfits'), list): рядки.append('(відповідь не розібрано як JSON)'); continue
        for x in в['outfits']:
            речі = []
            for n in x.get('items', []):
                р = пул.get(str(n).split('/')[0])
                речі.append('ВИГАДАНО ' + str(n) if not р else
                            f"{р[кол.index('type')]} {р[кол.index('color')]}" + (f" {р[кол.index('fabric')]}" if р[кол.index('fabric')] else '')
                            + f" {р[кол.index('price')]}₴")
            рядки.append(f"- [{x.get('pole')}] «{x.get('caption')}»: " + '; '.join(речі) + f". День: {x.get('day')}"
                         + (f" Свідомо: {'; '.join(d.get('item','') + ' — ' + d.get('why','') for d in x.get('deliberate') or [])}" if x.get('deliberate') else ''))
        if в.get('needed'): рядки.append('Бракує: ' + '; '.join(d.get('description', '') for d in в['needed']))
open('/tmp/вимір/суд/образи_сліпо.md', 'w').write('# Сліпе порівняння: 16 запитів збірки образів, по три відповіді A/B/C\n' + '\n'.join(рядки))
json.dump(ключ, open('/tmp/вимір/суд/ключ.json', 'w'), ensure_ascii=False, indent=1)
json.dump({м: dict(п) for м, п in прилади.items()}, open('/tmp/вимір/суд/прилади.json', 'w'), ensure_ascii=False, indent=1)
print(json.dumps({м: dict(п) for м, п in прилади.items()}, ensure_ascii=False, indent=1))
