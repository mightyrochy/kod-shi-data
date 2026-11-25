import sys, json
sys.path.insert(0, sys.argv[1]); import мовний_шар as М
iv = [{"verdict": {"kind": "her_item_verdict", "statements": [{"code": "found_in_catalogue", "values": {"count": 2}}]}, "slot": "top", "item": {"free_text": "светр", "lang": "uk"}}]
р = {"recorded": {"wants": {"label": "светр 61.5 см", "quote": "светр 61.5 см", "source": "reading"}}, "item_verdicts": iv, "advice": ""}
kw = {"після_повтору": True} if 'після_повтору' in М.прийняти_репліку.__code__.co_varnames else {}
for ім, т in [("лічильник як довжина", [{"about": ["item_verdicts"], "says": "Довжина другого светра — 2 см."}]),
              ("Знайдено 2 светри", [{"about": ["item_verdicts"], "says": "Знайдено 2 светри."}]),
              ("Знайдено два светри", [{"about": ["item_verdicts"], "says": "Знайдено два светри."}]),
              ("цитата з числом", [{"about": ["wants"], "recorded": ["wants"], "her_words": ["светр 61.5 см"], "says": "Я записала «светр 61.5 см»."}]),
              ("число поза цитатою", [{"about": ["wants"], "recorded": ["wants"], "her_words": ["светр 61.5 см"], "says": "Я записала «светр 61.5 см», це 61.5 см."}])]:
    д = М.прийняти_репліку(json.dumps({"text": т}, ensure_ascii=False), р, "", **kw)
    print(ім, '|', repr(д.get('текст')), '|', д.get('причина'))
