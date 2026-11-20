"""с5 і с8: клік «Зібрати образи» → перша картка; виклики перекладачки (модель, с); латинські слова на екрані карток."""
import json, re, sys, os, glob, datetime as D, statistics as S, collections
корінь = sys.argv[1]
def t(s): return D.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()
for с in ('с5_весілля_сестри', 'с8_мінус_десять_сніг'):
    хід = open(os.path.join(корінь, с, 'хід.md'), encoding='utf-8').read()
    кроки = re.findall(r'### (\d+) · (\S+) · прохід (\d+)[^\n]*\n([\s\S]*?)(?=\n### |$)', хід)
    служб = os.path.join(корінь, 'стенд', 'службове', с)
    обм = [json.loads(л) for л in open(os.path.join(служб, 'обміни.jsonl'), encoding='utf-8')]
    екр = [json.loads(л) for л in open(os.path.join(служб, 'екрани.jsonl'), encoding='utf-8')]
    for п in ('1', '2'):
        клік = next((t(ч) for н, ч, пр, тіло in кроки if пр == п and 'Зібрати образи' in тіло and 'натиснула' in тіло), None)
        картка = next((t(ч) for н, ч, пр, тіло in кроки if пр == п and клік and t(ч) > клік and 'Твої образи.' in тіло), None)
        пер = [x for x in обм if str(x['прохід']) == п and json.loads(x['запит'])['messages'][0]['content'][0]['text'].startswith('Ти — перекладачка')]
        моделі = collections.Counter(json.loads(x['запит'])['model'] for x in пер)
        лат = collections.Counter()
        for е in екр:
            if str(е.get('прохід')) == п and 'Твої образи.' in (е.get('текст') or ''):
                for w in re.findall(r'\b[A-Za-z][A-Za-z\'-]{2,}\b', е['текст'].split('Твої образи.', 1)[1]):
                    лат[w] += 1
        print(f"{с[:2]} прохід {п}: клік→картка {картка - клік:.0f} с" if клік and картка else f"{с[:2]} прохід {п}: картки нема",
              f"· перекладачка {len(пер)} викл {dict(моделі)} с p50 {S.median([x['с'] for x in пер]) if пер else 0:.1f}",
              f"· не-200 {sum(1 for x in пер if x.get('статус') != 200)}",
              f"· латинка на екрані карток: {', '.join(sorted(лат)) or '—'}")

print('--- текст карток (руки.jsonl): латинські слова поза назвами речей і крамниць; урізане «…»')
for с in ('с5_весілля_сестри', 'с8_мінус_десять_сніг'):
    ф = os.path.join(корінь, 'стенд', 'службове', с, 'руки.jsonl')
    if not os.path.exists(ф): continue
    for л in open(ф, encoding='utf-8'):
        x = json.loads(л); лат = collections.Counter(); знаків = 0; карток = 0
        for п in x.get('позиції', []):
            т = п.get('текст_картки') or ''; знаків += len(т); карток += 1
            свої = json.dumps([п.get('речі'), п.get('ф')], ensure_ascii=False).lower()
            for w in re.findall(r'\b[A-Za-z][A-Za-z\'-]{2,}\b', т):
                if w.lower() not in свої: лат[w] += 1
        print(f"{с[:2]} прохід {x['прохід']} крок {x['крок']}: карток {карток}, знаків {знаків}, латинка: {dict(лат) or '—'}")
