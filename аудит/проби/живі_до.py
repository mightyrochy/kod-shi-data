"""ДО живої сцени = останній результат її на коді-предку (CLAUDE.md п.18): ДО не ганяють, коли він уже є.
python3 аудит/проби/живі_до.py <id з живі_сцени.txt> [<код правки>, типово HEAD]   (історія: git fetch --unshallow)
Результати: `живі_прогони.txt` (давні) і `код.txt` у теках гілок origin/claude/zhyv* — рядок «<SHA> <id> <етап> <моделі>»."""
import pathlib, subprocess as sp, sys
Т = pathlib.Path(__file__).resolve().parent; КОР = str(Т.parents[1])
def г(*а):
    р = sp.run(['git', '-c', 'core.quotepath=false', '-C', КОР, *а], capture_output=True, text=True)
    return р.stdout.strip() if р.returncode == 0 else None
def рядки(ім): return [р.split('|') for р in (Т / ім).read_text(encoding='utf-8').splitlines() if р and р[0] != '#']
сц, код = sys.argv[1], г('rev-parse', sys.argv[2] if len(sys.argv) > 2 else 'HEAD')
с = next((р for р in рядки('живі_сцени.txt') if р[0] == сц), None)
if not с: sys.exit(f'сцени {сц} нема в живі_сцени.txt')
print('СЦЕНА ' + '|'.join(с[:4]) + f'\n  режим {с[4]} · руки {с[5]} · {с[6]}\n  питання: {с[7]}\n  краще: {с[8]}')
рез = [(р[1], р[2], 'origin/' + р[3], р[4], р[5]) for р in рядки('живі_прогони.txt') if р[0] == сц]
for реф in (г('for-each-ref', '--format=%(refname:short)', 'refs/remotes/origin/claude/zhyv*') or '').split():
    for ф in (г('ls-tree', '-r', '--name-only', реф) or '').splitlines():
        if ф.endswith('/код.txt'):
            п = (г('show', f'{реф}:{ф}') or '').split() + ['?'] * 4
            if п[1] == сц: рез.append((п[2], п[0], реф, ф.rsplit('/', 1)[0], п[3]))
предки, чужі = [], 0
for ет, sha, реф, тека, мод in рез:
    if sha != '?' and г('cat-file', '-e', sha + '^{commit}') is None: print(f'  {sha[:12]} нема в клоні — git fetch --unshallow'); continue
    if sha != '?' and sp.run(['git', '-C', КОР, 'merge-base', '--is-ancestor', sha, код]).returncode == 0:
        предки.append((int(г('rev-list', '--count', sha)), ет, sha, реф, тека, мод))
    else: чужі += 1
if not предки:
    sys.exit(f'ДО на коді-предку {код[:12]} нема (поза предками чи без SHA: {чужі}) → ДО лише для порівняльного питання, раз, найменшим режимом')
_, ет, sha, реф, тека, мод = max(предки)
змін = len((г('diff', '--name-only', sha, код, '--', 'джерела/') or '').split())
print(f'ДО = {ет} {реф}:{тека}\n  код {sha} · до {код[:12]} комітів {г("rev-list", "--count", sha + ".." + код)}, '
      f'файлів джерела/ змінено {змін} · моделі {мод}\n  файли: {" ".join((г("ls-tree", "--name-only", реф + ":" + тека) or "").split())}'
      f'\n  інших результатів на предках {len(предки) - 1}, поза предками чи без SHA {чужі}')
