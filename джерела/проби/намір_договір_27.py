"""Ф2/2.7: шість чинних намірів на швах паспорта й моделі; тема уваги після її відповіді.
Проба друкує факт ДО/ПІСЛЯ, не тлумачить слів жінки й не підміняє живого приймання 5312."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import реєстр_правил as Р, внутрішня_мова as В, паспорт_нагоди as П
import протокол as Т, пакет_моделі as К, мовний_шар as М
for код in Р.INTENT:
    паспорт = П.паспорт_з_json(json.dumps(dict(подія="зустріч", намір=код)), {}, слова="зустріч")
    випадок = К.випадок_для_пакета(dict(подія="зустріч", намір=код), "")
    print(json.dumps(dict(intent=код, lexicon={к: Р.INTENT[код][к] for к in
        ("рахункові", "підлога", "стриманий", "сміливі_гілки", "каблук_стеля", "форм_допуск")},
        language=В.код("intent", код), passport=паспорт.get("намір"),
        conversation=М.паспорт_кодами(dict(намір=код)).get("intent"),
        case=випадок.get("намір"), schema=код in Т.ВИПАДОК["поля"]["намір"]["значення"]), ensure_ascii=False))
for назва, дані in (("unknown", {}), ("default", dict(намір="conventional")),
    ("intent", dict(намір="statement", намір_слова="хочу, щоб дивились")),
    ("strict", dict(мета_важливо=["строго"])), ("zone", dict(мета_зони=["живіт"])),
    ("attention", dict(мета="експресія"))):
    п = dict(нагода="свято", година=20, **дані)
    print(json.dumps(dict(scene=назва, allowed="мета" in П.теми_дозволені({}, п),
                         open="goal" in М.теми_відкриті(п)), ensure_ascii=False))
print(json.dumps(dict(attention=list(В.ТАБЛИЦЯ["goal"]), extra=list(В.ТАБЛИЦЯ["goal_extra"]),
                      veto_same=П.ЗОНИ_ВЕТО is Т.ЗОНИ_ВЕТО), ensure_ascii=False))
