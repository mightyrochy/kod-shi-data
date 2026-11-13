"""Лічба пунктів картки з виміру мосту: рядків жінці, заяв жінці, повторів, кодів."""
import json, sys, collections
д = json.load(open(sys.argv[1]))
РЕЧ = ("колір", )
def заяви_жінці(п):
    return [з for з in (п.get("повідомлення") or {}).get("statements") or [] if з.get("recipient") != "journal"]
разом = collections.Counter(); коди = collections.Counter()
for ім, вм in д.items():
    картки = [вм] + [о for о in (вм.get("образи") or []) if isinstance(о, dict) and "пункти" in о]
    for н, в in enumerate(картки[:1] if len(картки) == 1 else картки):
        пп = [п for п in в.get("пункти") or [] if not п.get("для_всіх") and п.get("повідомлення")]
        зз = [з for п in пп for з in заяви_жінці(п)]
        ключі = [json.dumps(з, sort_keys=True, ensure_ascii=False) for з in зз]
        повт = len(ключі) - len(set(ключі))
        кв = collections.Counter(з["code"] for з in зз)
        повт_коду = sum(н - 1 for н in кв.values() if н > 1)
        print("%-22s картка %d: рядків %2d, заяв жінці %3d, однакових заяв %2d, той самий код удруге %2d"
              % (ім, н, len(пп), len(зз), повт, повт_коду))
        разом.update(рядків=len(пп), заяв=len(зз), однакових=повт, код_удруге=повт_коду, карток=1); коди.update(кв)
print("РАЗОМ", dict(разом))
print("КОДИ", коди.most_common())
