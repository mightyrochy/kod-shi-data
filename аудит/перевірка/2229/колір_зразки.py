import sys, json; sys.path.insert(0, '.')
import міст_відповіді as МВ
З = {
 "чистий": '{"photo":"usable","skin":["#f2d6c4","#eac9b5","#e8c2ad"],"hair":["#3b2a20"],"eyes":"#6b8cae","limbal_ring":null,"light_cast":"none","light_correction":"none"}',
 "огорожа+слова": 'Ось:\n```json\n{"photo":"usable","skin":["#f2d6c4"],"hair":["#3b2a20"],"eyes":"#6b8cae"}\n```\nСподіваюсь, допомогла!',
 "відмова-підпис": '{"photo":"portrait_eyes_hidden — usable, or why it is not"}',
 "photo true": '{"photo":true,"skin":["f2d6c4"],"hair":"#3B2A20","eyes":"#6b8cae"}',
 "рядки": 'Шкіра: #f2d6c4, #eac9b5\nВолосся — #3b2a20\nОчі: #6b8cae',
 "обірвано": '{"photo":"usable","skin":["#f2d6c4","#eac9',
 "два об'єкти": '{"photo":"usable"} {"photo":"usable","skin":["#f2d6c4"],"hair":["#3b2a20"],"eyes":"#6b8cae"}',
 "без очей": '{"photo":"usable","skin":["#f2d6c4"],"hair":["#3b2a20"],"eyes":null}',
 "порожньо": '',
 "answer-обгортка": '{"answer":{"photo":"usable","skin":["#f2d6c4"],"hair":["#3b2a20"],"eyes":"#6b8cae"}}',
}
for к, т in З.items():
    р = json.loads(МВ.колір(json.dumps({"відповідь_моделі": т})))
    print("%-16s стан=%s шк=%d вол=%d очі=%s від=%s дж=%s повтор=%s пом=%s" % (к, р.get("стан"), len(р.get("шкіра") or []), len(р.get("волосся") or []), р.get("очі"), р.get("відмова"), р.get("джерело"), bool(р.get("повтор")), [п.get("що") for п in р.get("помилки") or []][:3]))
print(МВ.колір(json.dumps({"відповідь_моделі": None})))
р = json.loads(МВ.колір(json.dumps({"відповідь_моделі": З["без очей"]}))); print(р["повтор"][:300])
