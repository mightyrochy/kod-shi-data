"""Відтворює джерела ручної звірки семи образів, не кличе моделей і не оцінює їх замість людей."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    """Збирає входи, відповіді, назви каталогу й таблицю тверджень з адресами оригіналів."""
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    run = here.parent / 'живий-як-людина-1'
    rows = json.loads((here / 'твердження.json').read_text(encoding='utf8'))
    selected = sorted({(r['с'], r['запит']) for r in rows})
    exchanges = {}
    photos = {}
    translated = {(2, 16): 23, (3, 16): 22, (4, 41): 45, (6, 20): 23,
                  (6, 38): 43, (7, 20): 27, (7, 46): 53}
    for s, n in selected:
        path = next((run / 'стенд/службове').glob(f'с{s}*/обміни.jsonl.gz'))
        records = [json.loads(line) for line in gzip.open(path, 'rt', encoding='utf8')]
        record = records[n - 1]
        content = json.loads(record['запит'])['messages'][-1]['content']
        text = '\n'.join(b.get('text', '') for b in content if b['type'] == 'text')
        data = json.loads(text[text.index('{'):])
        raw = json.loads(record['відповідь'])
        answer = json.loads(''.join(b.get('text', '') for b in raw['content']))
        urls = [b['source']['url'] for b in content if b['type'] == 'image']
        assert {r['н'] for r in rows if r['с'] == s and r['запит'] == n} == {
            i['n'] for i in data['outfit']['items']}
        entry = {'с': s, 'рядок': n, 'оригінал': str(path.relative_to(root)).replace('\\', '/'),
                 'час': record['час'], 'вхід': data, 'вихід': answer, 'фото': urls}
        translation = records[translated[s, n] - 1]
        translation_content = json.loads(translation['запит'])['messages'][-1]['content']
        translation_raw = json.loads(translation['відповідь'])
        entry['переклад'] = {'рядок': translated[s, n], 'вхід': translation_content,
            'вихід': json.loads(''.join(b.get('text', '') for b in translation_raw['content']))}
        exchanges[s, n] = entry
        for i, url in enumerate(urls, 1):
            photos[f'{s}-{n}-{i}'] = url
    catalog = {}
    with gzip.open(root / 'каталог_записи_v1.jsonl.gz', 'rt', encoding='utf8') as stream:
        for n, line in enumerate(stream, 1):
            record = json.loads(line)
            matches = [k for k, url in photos.items() if url in record.get('кадри', [])]
            for key in matches:
                catalog.setdefault(key, []).append({'рядок': n, 'ід': record['ід'],
                    'назва': record['назва'], 'адреса': record.get('адреса'),
                    'опис': record.get('опис'), 'параметри': record.get('параметри'),
                    'кадри': record['кадри']})
    output = {'образи': list(exchanges.values()), 'каталог': catalog,
              'каталог_sha256': hashlib.sha256((root / 'каталог_записи_v1.jsonl.gz').read_bytes()).hexdigest()}
    (here / 'джерела.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    fields = ['назва', 'коди', 'фото', 'а', 'б', 'в', 'невідомо']
    report = ['# Повний розклад тверджень', '',
        'Одиниця — окрема властивість однієї речі; повтор тієї самої властивості у назві, описі й пораді не множить число. '
        'Назви наведені окремо: це властивості запису крамниці, а не результат моделі опису. '
        'Коди й фото — підтверджена опора; а/б/в — класи відхилень наряду. '
        '«Невідомо» не зараховано ні до правильних, ні до помилкових. '
        'Естетичні судження та оптичні ефекти не є властивістю товару.', '',
        '| сцена · рядок обміну | назва | коди | фото | а | б | в | невідомо |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for key, exchange in exchanges.items():
        own = [r for r in rows if (r['с'], r['запит']) == key]
        counts = [sum(len(r.get(f, [])) for r in own) for f in fields]
        report.append('| с%d · %d | %s |' % (*key, ' | '.join(map(str, counts))))
    report += ['', '| річ · джерело | джерело твердження | властивості |', '|---|---|---|']
    for row in rows:
        entry = exchanges[row['с'], row['запит']]
        source = '../живий-як-людина-1/' + entry['оригінал'].split('живий-як-людина-1/')[1]
        label = f"с{row['с']} · {row['запит']} · {row['н']}"
        for field in fields:
            claims = row.get(field, [])
            if claims:
                report.append(f'| [{label}]({source}#L{row["запит"]}) | {field} | ' + '; '.join(claims) + ' |')
        for note in row.get('інше', []):
            report.append(f'| {label} | примітка | {note} |')
    (here / 'ТАБЛИЦЯ.md').write_text('\n'.join(report) + '\n', encoding='utf8')
    print('образів:', len(selected), 'речей:', len(rows))
    print({field: sum(len(r.get(field, [])) for r in rows) for field in fields})


if __name__ == '__main__':
    main()
