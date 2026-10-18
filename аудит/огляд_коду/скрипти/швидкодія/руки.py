"""Ланцюги рук у збиранні: сума обслуговування моделі й коду по руках (часи_*.json стенда). python3 руки.py файл..."""
import json, sys, collections
for ф in sys.argv[1:]:
    д = json.load(open(ф)); т0 = д['т0']; ключ = д['ключ']
    рука = lambda п: '?' if п is None or п < 0 or п >= len(ключ) else ключ[п]
    м = collections.defaultdict(float); к = collections.defaultdict(float); n = collections.Counter()
    for з in д['події']:
        if з['к'] == 'модель':
            м[рука(з['поз'])] += (з.get('т1', д['кінець']) - з.get('старт', з['т0'])) / 1000; n[рука(з['поз'])] += 1
        if з['к'] == 'код':
            к[рука(з['поз'])] += (з['т1'] - з['т0']) / 1000
    py = collections.defaultdict(float)
    for ім, a, b in д['python']: py[ім] += (b - a) / 1000
    кінець_рук = {}
    for з in д['події']:
        if з['к'] == 'стадія' and з['текст'] == '': кінець_рук[рука(з['поз'])] = (з['т'] - т0) / 1000
    print(ф.split('/')[-1], 'збір %.1f с · Python %.1f с (%s) · по руках: модель с/викликів, код (інтервали містП) с: %s · кінець рук %s' % (
        (д['кінець'] - т0) / 1000, sum(py.values()), ', '.join('%s %.1f' % kv for kv in sorted(py.items(), key=lambda kv: -kv[1])),
        {р: ('%.1f/%d' % (м[р], n[р]), round(к[р], 1)) for р in sorted(set(м) | set(к))}, кінець_рук))
