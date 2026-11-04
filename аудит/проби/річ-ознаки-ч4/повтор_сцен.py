"""Повтор записаних викликів мосту: python аудит/проби/річ-ознаки-ч4/повтор_сцен.py до|після."""
import asyncio, gzip, json, pathlib, sys, tempfile


def main():
    """Відтворює два записи на поточному коді, відокремлюючи лише шлях кеша кольорів."""
    К = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).resolve().parents[3]
    Д = pathlib.Path(__file__).resolve().parent
    sys.path.insert(0, str(К / 'джерела/прилади'))
    import знімок_мосту as З
    З.підготувати(str(К / 'джерела'))
    import feed
    feed.каталог_на_диску('каталог_brief.xml')
    кеш = pathlib.Path(tempfile.gettempdir()) / 'повтор_кеш.json'
    кеш.write_text('{}', encoding='utf8')
    підсумок = []
    for сцена in ('палітра_її', 'плитка_робота'):
        запис = З.прочитати(str(К / 'аудит/проби/знімок_входи' / (сцена + '.jsonl.gz')))
        рядки = [json.loads(р) for р in запис.splitlines() if р.strip()]
        for рядок in рядки:
            вхід = json.loads(рядок['вхід'])
            if 'кеш_кольорів' in вхід: вхід['кеш_кольорів'] = str(кеш)
            рядок['вхід'] = json.dumps(вхід, ensure_ascii=False)
        запис = '\n'.join(json.dumps(р, ensure_ascii=False) for р in рядки)
        знімок, час = asyncio.run(З.прогнати(запис))
        записи = [json.loads(р) for р in знімок.splitlines()][1:]
        (Д / (сцена + '-' + sys.argv[1] + '.jsonl.gz')).write_bytes(gzip.compress(знімок.encode('utf8'), mtime=0))
        помилки = [dict(н=з['н'], ім=з['ім'], помилка=з['помилка']) for з in записи if 'помилка' in з]
        підсумок.append(dict(сцена=сцена, викликів=len(записи), помилки=помилки, час=час))
        print(сцена, 'викликів', len(записи), 'винятків', len(помилки), flush=True)
    (Д / ('повтор-сцен-' + sys.argv[1] + '.json')).write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding='utf8')
    return any(с['помилки'] for с in підсумок)


if __name__ == '__main__':
    sys.exit(main())
