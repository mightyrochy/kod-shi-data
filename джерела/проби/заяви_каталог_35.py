"""3.5/6945/8242: справжні свідки каталогу → заяви трауру, без моделі й нових порогів.
PROBE_SOURCE_DIR дозволяє виконати ту саму пробу на базовому дереві.
"""
import collections, json, os, pathlib, sys
sys.path.insert(0, os.environ.get('PROBE_SOURCE_DIR', str(pathlib.Path(__file__).resolve().parents[1])))
import feed, outfit, composer as К, формальність as Ф, траурний_регістр as Т
каталог = feed._прочитати_каталог(feed.каталог_на_диску(sys.argv[1]), 0)['каталог']
групи = collections.defaultdict(list)
for р in каталог:
    if р.get('назва') and р.get('id'): групи[р['назва']].append(р['id'])
однойменні = sum(len(set(і)) > 1 for і in групи.values())
свідки = [р for р in каталог if Т.біля_обличчя(р) and Т.свідки_блиску(р)['розходяться']]
заяви = [з for р in свідки for зн in Ф.нагода_палітра(outfit.елементи([К._у_річ(р, р["слот"], None)]),
         місце='похорон', нагода='траур', речі=[р]) for з in зн.get('заяви', [])
         if з['code'] == 'mourning_shine_unknown_one']
без = sum(not (з.get('item_ids') or з.get('values', {}).get('item_id')) for з in заяви)
коди_словами = sum('shine_class_' in json.dumps(з.get('values'), ensure_ascii=False) for з in заяви)
print('каталог', len(каталог), 'однойменних груп різних ID', однойменні, 'свідків блиску', len(свідки))
print('заяв', len(заяви), 'без ID', без, 'кодів шкали як слів', коди_словами,
      'з ключем', sum(bool(з.get('key')) for з in заяви))
if заяви:
    з = заяви[0]; print('приклад', json.dumps(з, ensure_ascii=False))
