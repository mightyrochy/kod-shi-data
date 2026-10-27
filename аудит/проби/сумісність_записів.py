"""Готує старі відповіді до чинної нумерації заяв функціями самого продукту."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "джерела"))
import мовний_шар as шар


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
    print(json.dumps(підготувати(sys.argv[1]), ensure_ascii=False))
