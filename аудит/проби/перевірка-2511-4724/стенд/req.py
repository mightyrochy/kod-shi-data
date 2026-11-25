import sys, json
sys.path.insert(0, sys.argv[1]); import мовний_шар as М
р = {"recorded": {"wants": {"label": "оцю свою синю сукню", "quote": "оцю свою синю сукню", "source": "reading"}}, "required": ["occasion"], "advice": "Якщо хочеш, розкажи про прикраси."}
w = {"about": ["wants"], "recorded": ["wants"], "her_words": ["оцю свою синю сукню"], "says": "Я записала, що ти хочеш «оцю свою синю сукню»."}
bad = {"about": ["wants"], "recorded": ["wants"], "her_words": ["wants"], "says": "Я записала сукню."}
q = {"about": ["required"], "says": "Куди ти збираєшся?"}
qo = {"about": ["occasion"], "recorded": [], "says": "Розкажи, куди ти збираєшся?"}
extra = {"about": ["wants"], "recorded": ["wants"], "her_words": [], "says": "Вона синя й довга."}
kw = lambda r: {"після_повтору": True} if r and 'після_повтору' in М.прийняти_репліку.__code__.co_varnames else {}
def п(ім, т, р_, з, повтор):
    д = М.прийняти_репліку(json.dumps({"text": т}, ensure_ascii=False), р_, з, **kw(повтор))
    print(ім, '|', repr(д.get('текст')), '| причина', д.get('причина'), '| відкинуто', [в.get('чому') for в in д.get('відкинуто') or []])
for повтор in (False, True):
    print('--- повтор' if повтор else '--- перша')
    п('A повна+питання', [w, q], р, "", повтор)
    п('B без питання', [w], р, "", повтор)
    п('C питання не останнє', [q, w], р, "", повтор)
    п('D погане+питання', [bad, q], р, "", повтор)
    п('E без required, з частковим', [w, extra], dict(р, required=[]), р["advice"], повтор)
    п('F дубль запрошення', [w, {"says": "Якщо хочеш, розкажи про прикраси."}], dict(р, required=[]), р["advice"], повтор)
    п('G повна валідна без required', [w], dict(р, required=[]), р["advice"], повтор)
