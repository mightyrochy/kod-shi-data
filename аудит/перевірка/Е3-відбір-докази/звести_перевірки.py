"""Зводить останні коди команд, зберігаючи початкові падіння окремо."""
import json, pathlib, re, sys


def головна():
    """Підсумувати батарею, виправлену пробу та явно запущені архівні команди."""
    тека = pathlib.Path(__file__).resolve().parent
    останні, початкові = {}, []
    for файл in ('батарея.json', 'доробка.json', 'архівні-проби.json', 'додаткові.json', 'стеля-повтор.json'):
        дані = json.loads((тека / файл).read_text(encoding='utf-8'))
        for запис in дані if isinstance(дані, list) else [дані]:
            команда = запис['команда']
            текст = ' '.join(команда) if isinstance(команда, list) else команда
            ім = re.search(r'([^ /\\]+\.(?:py|js))', текст).group(1)
            факт = dict(перевірка=ім, код=запис['код'], джерело=файл)
            if файл == 'батарея.json' and запис['код']: початкові.append(факт)
            останні[ім] = факт
    if not останні:
        raise ValueError('Нема результатів перевірок')
    підсумок = dict(перевірок=len(останні), невдалих=sum(bool(v['код']) for v in останні.values()),
                    початкові_падіння=початкові, останні=list(останні.values()))
    (тека / 'підсумок_перевірок.json').write_text(
        json.dumps(підсумок, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in підсумок.items() if k != 'останні'}, ensure_ascii=False))
    return int(bool(підсумок['невдалих']))


if __name__ == '__main__':
    sys.exit(головна())
