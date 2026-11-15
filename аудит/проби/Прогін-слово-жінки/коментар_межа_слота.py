"""15271 повтором записаних коментарів с1/с8 (живий «як людина» 2): відповідь перекладача коментаря → прийняти_вхід
("comment") → паспорт_з_коментаря; які межі долито й чи є службовий ключ слота. argv: корінь_джерел обміни.jsonl.gz…"""
import sys, json, gzip, re
sys.path.insert(0, sys.argv[1])
import мовний_шар as М
СЛУЖБОВІ = {М._ВМ.ключ("slot", с) for с in М._ВМ.схема()["$defs"]["thing"]["properties"]["slot"]["enum"]} - {None}
ключів = записів = 0
for ф in sys.argv[2:]:
    for л in gzip.open(ф, 'rt', encoding='utf8'):
        з = json.loads(л)
        try:
            т = json.loads(з["відповідь"])["content"][0]["text"]
        except Exception:
            continue
        if '"vetoes"' not in т or '"about_items"' not in т:
            continue
        об = json.loads(т[т.index('{'):т.rindex('}') + 1])
        п = М.паспорт_з_коментаря(dict(vetoes=об.get("vetoes") or []), паспорт_досі={"вето": {}, "бажання": []})
        тв = (п["паспорт"] or {}).get("вето_тверде") or {}
        сл = [w for w in тв.get("типи") or [] if w in СЛУЖБОВІ]
        записів += 1; ключів += bool(сл)
        print(ф.split('/')[0], "межі:", json.dumps({к: в for к, в in тв.items() if в and к != "без_читача"}, ensure_ascii=False),
              "| слот цілим:", сл, "| не_межа:", п["додано"].get("не_межа"))
print("коментарів з межами: %d; із межею на весь слот: %d" % (записів, ключів))
