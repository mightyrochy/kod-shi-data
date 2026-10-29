"""Ф2/2.7: чинний намір після шву паспорта на ≤200 діагностичних трійках справжнього каталогу.
Запуск: проба <джерела ДО/ПІСЛЯ> <каталог_таблиця.json.gz> <повний.xml>; це не оцінка краси образів."""
import collections, gzip, hashlib, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve()))
import feed as Ф, таблиця_каталогу as Т, паспорт_нагоди as П
import outfit as О, суд_образу as С, реєстр_правил as Р
таблиця = pathlib.Path(sys.argv[2]); фід = sys.argv[3]
т = json.load(gzip.open(таблиця, "rt")); офери = Ф.читати_yml(фід)[0]
каталог = Т.відновити(т, офери)["каталог"]
import колір_річ as _КОЛІР
слоти = {с: sorted((x for x in каталог if x.get("слот") == с and (_КОЛІР.hex_кольору(x) or x.get("colors"))), key=lambda x: x["id"])
         for с in ("верх", "низ", "взуття")}
образи = [О.елементи([слоти[с][i] for с in слоти]) for i in range(min(200, *(len(x) for x in слоти.values())))]
print(json.dumps(dict(items=len(каталог), triples=len(образи), slots={с: len(x) for с, x in слоти.items()},
                      table_sha256=hashlib.sha256(таблиця.read_bytes()).hexdigest()), ensure_ascii=False))
for намір in Р.INTENT:
    п = П.паспорт_з_json(json.dumps(dict(подія="зустріч", намір=намір)), {}, слова="зустріч")
    факти = [С.підлога_інтересу_проактивно(E, п["намір"]) for E in образи]
    правильні = [С.підлога_інтересу_проактивно(E, намір) for E in образи]
    print(json.dumps(dict(intent=намір, passport=п["намір"], floor=Р.намір(п["намір"])["підлога"],
        changed_from_direct=sum(a != b for a, b in zip(факти, правильні)),
        with_findings=sum(bool(x) for x in факти),
        repair_keys=dict(collections.Counter(к for x in факти for z in x
                         for к in z.get("запит_у_каталог", {}) if к not in ("слот", "чому"))),
        registers=dict(collections.Counter(z.get("регістр") for x in факти for z in x))), ensure_ascii=False))
