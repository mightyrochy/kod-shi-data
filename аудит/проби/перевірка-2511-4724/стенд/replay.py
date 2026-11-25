# Офлайн-повтор 21.11 (обміни 5→6) справжнім читачем: python3 replay.py <тека джерела>
import sys, json
sys.path.insert(0, sys.argv[1])
import мовний_шар as М
t = open('/tmp/r3w/persha5_prompt.txt').read()
р = json.loads(t[t.index('РЕПЛІКА:\n') + 9:])
з = р['advice']
п = М.прийняти_репліку(open('/tmp/r3w/persha5.txt').read(), р, з)
print('СПРОБА 1 · причина:', п.get('причина')); print('  текст:', repr(п.get('текст')))
kw = {'після_повтору': True} if 'після_повтору' in М.прийняти_репліку.__code__.co_varnames else {}
д = М.прийняти_репліку(open('/tmp/r3w/druha6.txt').read(), р, з, **kw)
print('СПРОБА 2', kw, '· причина:', д.get('причина'))
print('  текст:', д.get('текст'))
print('  частини:', json.dumps(д.get('частини_репліки'), ensure_ascii=False))
print('  відкинуто:', len(д.get('відкинуто') or []), sorted({в.get('чому') for в in д.get('відкинуто') or []}))
