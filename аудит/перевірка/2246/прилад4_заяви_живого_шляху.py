# Прилад перевірки 4 (не виконавця): усі заяви, створені на 6 живих прогонах (`внутрішня_мова.заява`),
# і скільки з них несуть у значеннях назву з каталогу (будь-яку, не лише речей образу) чи ключі name/shop.
import json, os, re, sys, tempfile, collections
sys.path.insert(0, os.getcwd())
import внутрішня_мова as ВМ
записані = []
_з = ВМ.заява
def заява(код, *a, **k):
    р = _з(код, *a, **k); записані.append(р); return р
ВМ.заява = заява
import statements as З
_с = З.створити
def створити(код, значення=None, **k):
    р = _с(код, значення, **k); записані.append(р); return р
З.створити = створити
import тест_живого_шляху as Т, feed as Ф
вх = json.load(open("стенд_вх.json", encoding="utf-8")); вх["каталог"] = Ф.каталог_на_диску(Т.КАТАЛОГ)
вх["кеш_кольорів"] = os.path.join(tempfile.gettempdir(), "кеш_живого_шляху.json")
if not os.path.exists(вх["кеш_кольорів"]): json.dump({}, open(вх["кеш_кольорів"], "w"))
назви = {re.sub(r"\s+", " ", str(з.get("назва") or "")).strip() for з in Ф.база_прогону(вх["каталог"], 0, вх["кеш_кольорів"])["каталог"]}
назви = {н for н in назви if len(н) > 6}
for г in Т.ГІЛКИ:
    for н in Т.НАМІРИ:
        Т.прогін(вх, г, н)
def рядки(в):
    if isinstance(в, dict):
        for k, x in в.items():
            yield from рядки(x)
    elif isinstance(в, (list, tuple)):
        for x in в: yield from рядки(x)
    elif isinstance(в, str): yield в
з_назвою = collections.Counter(); з_name = collections.Counter()
for р in записані:
    s = json.dumps(р.get("values"), ensure_ascii=False)
    if any(н in t for t in рядки(р.get("values")) for н in назви): з_назвою[р["code"]] += 1
    if '"name"' in s or '"shop' in s: з_name[р["code"]] += 1
print("заяв створено на 6 прогонах:", len(записані), "| різних кодів:", len({р['code'] for р in записані}))
print("заяв із назвою каталогу у values:", sum(з_назвою.values()), dict(з_назвою))
print("заяв із ключем name/shop у values:", sum(з_name.values()), dict(з_name))
