"""Додати до корпусу replay записи гілки claude/zhyvi-3.2e: ходи розмови й власні репліки з логів (§7 розбору)."""
import json
import re
import subprocess
import sys
from pathlib import Path

ГІЛКА = 'origin/claude/zhyvi-3.2e'
КОРІНЬ = 'аудит/живі_3.2е'
ДОБРА = 'ДО/ж3_кафе_20'  # старий суддя J (цитата без чужих цифр) пропускає її на main — одна з 8 добрих §7
СЦЕНИ = ('ДО/ж3_кафе_20', 'ПІСЛЯ/ж3_кафе_20', 'ПІСЛЯ/ж7_вечеря_сьомій', 'ПІСЛЯ/ж7_театр_дата')


def git(*арг):
    """Прочитати об'єкт гілки; шляхи без екранування."""
    return subprocess.run(('git', '-c', 'core.quotepath=off') + арг, check=True,
                          capture_output=True, text=True).stdout


def хід(текст):
    """Розібрати файл VIDPOVIDI: запит із першого JSON, відповідь із блоку ```json."""
    запит = json.loads(текст.split('\n', 1)[1].split('\n\n── ВІДПОВІДЬ', 1)[0])
    відп = re.search(r'```json\s*(.*?)```', текст.split('── ВІДПОВІДЬ', 1)[1], re.S)
    return запит, json.loads(відп.group(1))


def записи(sha):
    """Усі записи 3.2-Е, що входять у вибірку §7: хід розмови й показаний текст сцени."""
    р = []
    for с in СЦЕНИ:
        каталог = f'{КОРІНЬ}/{с}'
        файли = [ф for ф in git('ls-tree', '-r', '--name-only', ГІЛКА, '--', каталог + '/VIDPOVIDI').split('\n')
                 if ф.endswith('хід_розмови.txt')]
        for ф in sorted(файли):
            запит, відп = хід(git('show', f'{ГІЛКА}:{ф}'))
            р.append(dict(джерело=f'{sha}:{ф}', група='живі_3.2е', вид='розмова',
                          запит={'her_new_message': запит.get('her_new_message', '')}, відповідь=відп))
        лог = git('show', f'{ГІЛКА}:{каталог}/лог.txt')
        текст = re.search(r'^\s+СТИЛІСТКА:\s*(.*)$', лог, re.M).group(1).strip()
        запис = dict(джерело=f'{sha}:{каталог}/лог.txt', група='живі_3.2е', вид='показ',
                     запит={}, відповідь={'text': текст})
        if с == ДОБРА:
            запис['очікування_J'] = 'good'
        р.append(запис)
    return р


def main():
    """Дописати записи, яких ще нема, у корпус argv[1]; повторний запуск нічого не змінює."""
    шлях = Path(sys.argv[1])
    корпус = json.loads(шлях.read_text(encoding='utf8'))
    є = {з['джерело'] for з in корпус}
    нові = [з for з in записи(git('rev-parse', ГІЛКА).strip()) if з['джерело'] not in є]
    шлях.write_text(json.dumps(корпус + нові, ensure_ascii=False, indent=1), encoding='utf8')
    print(len(нові), 'нових записів; всього', len(корпус) + len(нові))


if __name__ == '__main__':
    main()
