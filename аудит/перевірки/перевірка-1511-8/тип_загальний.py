"""Загальна відмова від типу в коментарі до образу (#3881): чи лягає межею. argv: корінь_джерел"""
import sys, json; sys.path.insert(0, sys.argv[1]); import мовний_шар as М
for в in ([{"quote": "спідниць я взагалі не ношу", "item_type": "skirt"}],
          [{"quote": "спідниць я взагалі не ношу", "slot": "bottom", "item_type": "skirt"}],
          [{"quote": "пальто нижче коліна", "slot": "outerwear", "length": "midi"}]):
    п = М.паспорт_з_коментаря(dict(vetoes=в), паспорт_досі={"вето": {}, "бажання": []})
    print(json.dumps({к: в for к, в in ((п["паспорт"] or {}).get("вето_тверде") or {}).items() if в}, ensure_ascii=False), "| додано:", json.dumps(п["додано"], ensure_ascii=False))
