"""Повторити лише два прилади з таймаутом послідовно, з тією самою межею 900 с."""
import io, json, os, subprocess, sys, tarfile, time
from pathlib import Path

тека = Path(__file__).resolve().parent
репо = тека.parents[3]
база = репо.parent / 'tmp/межі-таймаути-база'
база.mkdir(parents=True, exist_ok=True)
архів = subprocess.check_output(['git', 'archive', '48252dea6b263e8c654299179e0b324dc18364f9',
                                'джерела', 'zhnyvarka', 'аудит/проби', 'каталог_повний.xml.gz'], cwd=репо)
with tarfile.open(fileobj=io.BytesIO(архів)) as т:
    т.extractall(база, filter='data')
os.environ.update(PYTHONIOENCODING='utf-8', PYTHONUTF8='1', PYTHONUNBUFFERED='1')
рядки = []
for прилад in ['корінь_річ_запис_речі.py', 'корінь_річ_ознаки_обличчя.py']:
    for версія, корінь in [('голова', репо), ('база', база)]:
        команда = [sys.executable, 'джерела/прилади/' + прилад]
        почато = time.monotonic()
        try:
            р = subprocess.run(команда, cwd=корінь, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
            код, вивід = р.returncode, р.stdout
        except subprocess.TimeoutExpired as е:
            код, вивід = 124, е.stdout or b''
        (тека / (прилад[:-3] + '-' + версія + '.txt')).write_bytes(вивід)
        рядки.append(dict(прилад=прилад, дерево=версія, команда=команда, код=код,
                           секунди=round(time.monotonic()-почато, 2)))
        (тека / 'таймаути-підсумок.json').write_text(json.dumps(рядки, ensure_ascii=False, indent=1), encoding='utf-8')
        print(json.dumps(рядки[-1], ensure_ascii=False), flush=True)
sys.exit(int(any(р['код'] for р in рядки)))
