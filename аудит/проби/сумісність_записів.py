"""Готує старі відповіді до чинної нумерації заяв функціями самого продукту."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
import мовний_шар as шар


def заяви_з_запису(текст):
    """Читає вкладені масиви JSON, не відтворюючи заголовків чи шаблону промпту."""
    декодер = json.JSONDecoder()
    for індекс, символ in enumerate(текст):
        if символ != "[":
            continue
        try:
            значення, _ = декодер.raw_decode(текст, індекс)
        except ValueError:
            continue
        if isinstance(значення, list) and значення and all(
                isinstance(з, dict) and "key" in з and "code" in з for з in значення):
            return значення
    return []


def відповідь_на_виклик(старий, новий, відповідь):
    """Переносить дослівну відповідь між іменами тієї самої заяви двох викликів."""
    було, тепер = заяви_з_запису(старий), заяви_з_запису(новий)
    дані, _ = шар._обʼєкт(відповідь, [])
    if not було or not тепер or not isinstance(дані, dict):
        return відповідь
    if not set(дані) & {str(з["key"]) for з in було}:
        return відповідь
    if шар._повторені_ключі_повідомлень(відповідь):
        return відповідь

    def зміст(заява):
        return json.dumps({к: з for к, з in заява.items() if к != "key"}, ensure_ascii=False, sort_keys=True)

    поточні = {зміст(з): str(з["key"]) for з in тепер}
    перейменування = {str(з["key"]): поточні[зміст(з)] for з in було if зміст(з) in поточні}
    результат = {перейменування.get(ключ, ключ): текст for ключ, текст in дані.items()}
    if len(результат) != len(дані):
        raise ValueError("Перенумерація об'єднала різні відповіді")
    assert list(результат.values()) == list(дані.values())
    return json.dumps(результат, ensure_ascii=False)


def підготувати(архів):
    """Перенумеровує ключі з архівної розмітки; тексти моделі лишає дослівними."""
    if not Path(архів).is_file():
        return {}
    вихід = {}

    def обійти(вузол):
        if isinstance(вузол, list):
            for значення in вузол:
                обійти(значення)
        elif isinstance(вузол, dict):
            розмітка = вузол.get("розмітка")
            відповідь = вузол.get("відповідь_моделі")
            if вузол.get("напрям") == "out_messages" and розмітка and isinstance(відповідь, str):
                дані, _ = шар._обʼєкт(відповідь, [])
                ключі = шар._ключі_повідомлень(розмітка)
                if isinstance(дані, dict) and set(дані) & set(ключі):
                    нова = {ключі.get(ключ, ключ): текст for ключ, текст in дані.items()}
                    assert list(нова.values()) == list(дані.values())
                    ід = hashlib.sha256(відповідь.encode("utf8")).hexdigest()
                    запис = dict(промпт=шар.промпт_повідомлень(розмітка),
                                 відповідь=json.dumps(нова, ensure_ascii=False))
                    if запис not in вихід.setdefault(ід, []):
                        вихід[ід].append(запис)
            for значення in вузол.values():
                обійти(значення)

    обійти(json.loads(Path(архів).read_text(encoding="utf-8-sig")))
    return вихід


if __name__ == "__main__":
    if sys.argv[1] == "--виклик":
        дані = json.load(sys.stdin)
        print(json.dumps(відповідь_на_виклик(дані["було"], дані["тепер"], дані["відповідь"]), ensure_ascii=False))
    else:
        print(json.dumps(підготувати(sys.argv[1]), ensure_ascii=False))
