"""Відтворення незалежної перевірки #3707; перший аргумент — тека з base3707, pr3707, до.html та після.html."""

def головна():
    import sys
    if len(sys.argv)<2:
        raise SystemExit("Потрібна тека робочих дерев")
    from pathlib import Path
    import re,zipfile,io,base64,gzip,json
    root=Path(sys.argv[1]).resolve()
    tables=[]
    for name in ('до','після'):
        html=(root/f'{name}.html').read_text('utf8')
        binary=base64.b64decode(re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"',html).group(1))
        z=zipfile.ZipFile(io.BytesIO(binary))
        table=json.loads(gzip.decompress(z.read('каталог_таблиця.json.gz')))
        print(name,table.keys(),flush=True)
        tables.append(table)
    print('Різні верхні поля:',[k for k in tables[0] if tables[0][k]!=tables[1][k]],flush=True)


if __name__=="__main__":
    головна()
