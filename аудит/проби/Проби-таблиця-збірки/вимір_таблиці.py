"""Наряд Проби-таблиця-збірки, крок 1 (15018): вихід `запити` на записаних входах трьох сцен — зі свіжою таблицею збірки
і повільним шляхом без таблиці, на тих самих модулях тієї самої сторінки `показ-повний` (повний каталог).

  python3 аудит/проби/Проби-таблиця-збірки/вимір_таблиці.py <index.html> [<сцена> …]   (CPython 3.12.1, як у збірці)

Кожен запуск — окремий процес (кеші модулів не ділять стану). Друкує «<сцена> <з таблицею|без таблиці> sha <16>
sha_без_мета <16> таблиця <стан>»; `sha_без_мета` — той самий вихід без `мета.таблиця_каталогу` (стан таблиці — власне
те, що відрізняє два шляхи, тож цілий SHA відрізнятиметься завжди).
"""
import base64, gzip, hashlib, io, json, os, re, subprocess, sys, tempfile, zipfile

ТУТ = os.path.dirname(os.path.abspath(__file__))
КОРІНЬ = os.path.abspath(os.path.join(ТУТ, '..', '..', '..'))
ВХОДИ = os.path.join(ТУТ, '..', 'Збирання-запити-час', 'входи')
ТАБЛИЦЯ = 'каталог_таблиця.json.gz'


def дитина(сторінка, сцена, режим):
    sys.path.insert(0, os.path.join(КОРІНЬ, 'джерела', 'прилади'))
    import asyncio, знімок_мосту as З
    тека = tempfile.mkdtemp(prefix='табл_')
    t = open(сторінка, encoding='utf-8').read()
    zipfile.ZipFile(io.BytesIO(base64.b64decode(re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"', t).group(1)))).extractall(тека)
    if режим == 'без таблиці':
        os.remove(os.path.join(тека, ТАБЛИЦЯ))
    З.підготувати(тека)
    входи = З.прочитати(os.path.join(ВХОДИ, сцена + '.jsonl.gz'))
    знімок, час = asyncio.run(З.прогнати(входи))
    for р in знімок.splitlines()[1:]:
        з = json.loads(р)
        if з['ім'] == 'запити':
            рез = з.get('результат')
            мета = (рез or {}).get('мета') or {}
            стан = (мета.get('таблиця_каталогу') or {}).get('стан')
            if isinstance(рез, dict) and isinstance(рез.get('мета'), dict):
                рез['мета'].pop('таблиця_каталогу', None)
            print(json.dumps(dict(sha=hashlib.sha256(р.encode()).hexdigest()[:16], стан=стан, помилка=з.get('помилка'),
                                  sha_без_мета=hashlib.sha256(З.канон(з).encode()).hexdigest()[:16])))
            return
    print(json.dumps(dict(помилка='виклику запити нема')))


def головна():
    if sys.argv[1] == '--дитина':
        return дитина(*sys.argv[2:5])
    сторінка = os.path.abspath(sys.argv[1])
    сцени = sys.argv[2:] or sorted(ф[:-len('.jsonl.gz')] for ф in os.listdir(ВХОДИ) if ф.endswith('.jsonl.gz'))
    ч = [(с, р, subprocess.Popen([sys.executable, '-I', __file__, '--дитина', сторінка, с, р], stdout=subprocess.PIPE, text=True))
         for с in сцени for р in ('з таблицею', 'без таблиці')]
    for с, р, п in ч:
        в = json.loads(п.communicate()[0].strip().splitlines()[-1])
        print('%s | %s | sha %s | sha_без_мета %s | таблиця %s%s' % (с, р, в.get('sha'), в.get('sha_без_мета'), в.get('стан'),
              ' | помилка ' + str(в['помилка']) if в.get('помилка') else ''), flush=True)


if __name__ == '__main__':
    головна()
