"""Вибрати відповідь, яка загубилася між руками, зі справжніх журналів стенда."""
import json
from pathlib import Path
import sys


def main():
    """Зберегти джерельні заяви й повтори до та після виправлення."""
    вихід = {}
    for назва, файл in zip(('до', 'після'), sys.argv[1:]):
        дані = json.loads(Path(файл).read_text(encoding='utf-8'))
        руки = []
        for вердикт in дані['прогони'][0]['вердикти']:
            записи = []
            for запис in вердикт.get('мова_шару', []):
                заяви = [р for р in запис.get('заяви', [])
                          if any(з.get('code') == 'items_register_unknown' for з in р.get('заяви', []))]
                if заяви:
                    записи.append(dict(де=запис['де'], спільний=запис.get('спільний_виклик', False),
                                       заяви=заяви))
            руки.append(dict(рука=вердикт['рука'], записи=записи))
        вихід[назва] = руки
    (Path(__file__).resolve().parent / 'доставка.json').write_text(
        json.dumps(вихід, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
