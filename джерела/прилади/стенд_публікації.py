# -*- coding: utf-8 -*-
"""СТЕНД ПУБЛІКАЦІЇ: голод `build.txt` за частих злиттів — ДО і ПІСЛЯ на справжніх кроках `zbirka.yml`.

ЧОМУ. Concurrency збірки тримає одну запущену й одну очікувану збірку push, новіша очікувана витісняє старшу.
Коли публікація пропускає збірку, яка до кінця застала новіший main, а злиття частіші за CI, кожна наступна
збірка застає ще новіший main — і штамп стоїть, скільки тривають злиття. Стенд відтворює це без GitHub.

ЩО РОБИТЬ. Локальний bare-«origin» без силового push (`receive.denyNonFastForwards`), злиття гілок PR за
розкладом, черга concurrency GitHub (одна запущена, одна очікувана, новіша очікувана витісняє старшу; збірку
запускає лише push, що зачепив `on.push.paths`). Кожна збірка виконує справжні bash-кроки з даного `zbirka.yml`:
«які шляхи змінено» (job zminy) у клоні глибини 2 і «згорнути дошку» + «закомітити артефакт» (job publish) у
клоні глибини 1 — як actions/checkout. Збірку показу імітує вантаж: штамп SHA + відбиток джерел цього SHA, тож
розсинхрон index.html ↔ build.txt ↔ джерела видно побайтово. Згортання дошки — заглушка з тим самим контрактом:
файли `аудит/дошка/**.md` → рядки `аудит/БЕКЛОГ.md`, файли видаляє.

СЦЕНАРІЇ. «29.10» — злиття main 29.10 10:43–15:01 UTC з тривалостями прогонів із журналів Actions (ДО має
відтворити п'ять пропусків реального дня); «часті» — злиття джерел кожні 12 хв шість годин, CI 35 хв.
`--гонка` — перед першим push публікації в origin зливається ще одне злиття джерел (push відбито → повтор).

ЗАПУСК (з кореня репозиторію):
    git show origin/main:.github/workflows/zbirka.yml > /tmp/до.yml
    python3 джерела/прилади/стенд_публікації.py --yml /tmp/до.yml --сценарій 29.10           # ДО
    python3 джерела/прилади/стенд_публікації.py --сценарій 29.10 [--гонка]                   # ПІСЛЯ (робоче дерево)

Друкує кожну публікацію й підсумок: збірки, що не опублікували новіші за штамп джерела; найдовша затримка від
злиття джерел до їхньої публікації; неопубліковане наприкінці. Код виходу 1 — порушено інваріант (розсинхрон,
штамп назад, рядок дошки втрачено чи подвоєно); лічба голоду — факт, не гейт.
"""
import argparse
import hashlib
import os
import subprocess
import sys
import tempfile

import yaml

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# (хвилина UTC 29.10, мітка = короткий SHA злиття в main, вид): Д — джерела й дошка, Б — лише дошка,
# Н — поза paths. Вид — з `git diff --name-only <злиття>^1 <злиття>`.
ЗЛИТТЯ_2910 = [
    (10 * 60 + 43.0, '05d8516e', 'Н'),
    (11 * 60 + 0.1, 'b6aab24b', 'Д'), (11 * 60 + 0.75, '49756342', 'Н'), (11 * 60 + 0.8, '003a4ee5', 'Н'),
    (11 * 60 + 7.0, 'c060080d', 'Д'), (11 * 60 + 33.7, 'fdcd7756', 'Д'), (11 * 60 + 51.2, 'c6111d28', 'Д'),
    (12 * 60 + 17.7, '82f60e2f', 'Д'), (12 * 60 + 38.1, 'd6618610', 'Н'), (12 * 60 + 54.7, '8e0659c3', 'Д'),
    (13 * 60 + 4.6, 'ea0dc0cb', 'Н'), (13 * 60 + 9.7, '256b1d07', 'Д'), (13 * 60 + 13.2, '4bc77d79', 'Б'),
    (14 * 60 + 9.9, '780a8603', 'Н'), (14 * 60 + 16.4, '560fa388', 'Д'), (14 * 60 + 53.2, 'b6152c0b', 'Д'),
    (15 * 60 + 1.4, 'ae7aa01c', 'Б'),
]
# Від старту прогону до кроку публікації, хв (журнали Actions 29.10, job «опублікувати…»).
ТРИВАЛІСТЬ_2910 = {'b6aab24b': 31.6, 'c060080d': 28.1, 'c6111d28': 31.7, '82f60e2f': 32.4, '8e0659c3': 23.3,
                   '560fa388': 32.1}
ПОВНИЙ_2910, ЛЕГКИЙ = 30.0, 1.8

ЗАГЛУШКА_ЗГОРТАННЯ = '''import os
рядки = []
for тека, _, файли in sorted(os.walk('аудит/дошка')):
    for ф in sorted(файли):
        if ф.endswith('.md'):
            шлях = os.path.join(тека, ф)
            рядки += [р for р in open(шлях, encoding='utf-8').read().splitlines() if р.strip()]
            os.remove(шлях)
if рядки:
    open('аудит/БЕКЛОГ.md', 'a', encoding='utf-8').write('\\n'.join(рядки) + '\\n')
print('згорнуто рядків:', len(рядки))
'''


def запустити(аргументи, тека, env=None, перевірити=True):
    """Виконує команду в теці; за `перевірити` зупиняє стенд на ненульовому коді."""
    р = subprocess.run(аргументи, cwd=тека, env=env, capture_output=True, text=True)
    if перевірити and р.returncode:
        raise SystemExit(f'{" ".join(аргументи)} у {тека}: {р.returncode}\n{р.stdout}\n{р.stderr}')
    return р


def git(тека, *а, перевірити=True):
    """Виконує git із некодованими кириличними шляхами й повертає stdout без крайніх пробілів."""
    return запустити(['git', '-c', 'core.quotepath=off', *а], тека, перевірити=перевірити).stdout.strip()


def кроки(yml):
    """Дістає з zbirka.yml bash трьох кроків (zminy, згортання, публікація) і `on.push.paths`."""
    д = yaml.safe_load(open(yml, encoding='utf-8'))
    def крок(job, назва):
        """Повертає `run` кроку за назвою; нема — стенд зупиняється."""
        for к in д['jobs'][job]['steps']:
            if к.get('name') == назва:
                return к['run']
        raise SystemExit(f'{yml}: нема кроку {job} / {назва}')
    paths = (д.get('on') or д.get(True))['push']['paths']
    return (крок('zminy', 'які шляхи змінено'), крок('publish', 'згорнути дошку'),
            крок('publish', 'закомітити артефакт'), paths)


def вантаж(тека, sha):
    """Імітація збірки: штамп + відбиток джерел (без звіту досяжності й приладів, як справжній вантаж)."""
    h = hashlib.sha256()
    for шлях in git(тека, 'ls-tree', '-r', '--name-only', sha, '--', 'джерела').splitlines():
        if шлях.startswith('джерела/код'):
            h.update(шлях.encode() + git(тека, 'show', f'{sha}:{шлях}').encode())
    return f'const ЗБІРКА_ПОКАЗУ = "{sha}";\n// джерела {h.hexdigest()}\n'


class Стенд:
    def __init__(self, yml, гонка):
        """Читає кроки з yml і заводить тимчасову теку стенда та лічильники."""
        self.zminy, self.згортання, self.публікація, self.paths = кроки(yml)
        self.yml_текст = open(yml, encoding='utf-8').read()
        self.тимчас = tempfile.mkdtemp(prefix='стенд_публікації_')
        self.origin = os.path.join(self.тимчас, 'origin.git')
        self.url = 'file://' + self.origin
        self.dev = os.path.join(self.тимчас, 'dev')
        self.мітки, self.n, self.гонка = {}, 0, гонка
        self.злиття_джерел = []   # (час, sha, мітка)
        self.публікації = []       # (час, мітка штампу, мітка збірки)
        self.пропуски = []         # (мітка збірки, мітка штампу після неї)
        self.рядки_дошки = []
        self.порушення = []
        self.збірок = {'повна': 0, 'легка': 0, 'витіснено': 0}
        self.повторів = 0

    # --- репозиторій -------------------------------------------------------------------------------------
    def підготувати(self, мітка0):
        """Створює bare-origin без силового push і перший опублікований стан (джерела + збірка мітки0)."""
        запустити(['git', 'init', '-q', '--bare', '-b', 'main', self.origin], self.тимчас)
        for к, з in (('receive.denyNonFastForwards', 'true'), ('uploadpack.allowAnySHA1InWant', 'true')):
            git(self.origin, 'config', к, з)
        запустити(['git', 'clone', '-q', self.url, self.dev], self.тимчас)
        git(self.dev, 'config', 'user.name', 'стенд'); git(self.dev, 'config', 'user.email', 'стенд@локально')
        файли = {'джерела/код.txt': 'початок\n', 'джерела/аудит/ДОСЯЖНІСТЬ.md': 'досяжність —\n',
                 'джерела/прилади/згорнути_дошку.py': ЗАГЛУШКА_ЗГОРТАННЯ, 'аудит/БЕКЛОГ.md': '| № | рядок |\n',
                 'аудит/інше.md': 'поза paths\n', '.github/workflows/zbirka.yml': self.yml_текст,
                 'index.html': '—\n', 'build.txt': ''}
        for шлях, текст in файли.items():
            os.makedirs(os.path.dirname(os.path.join(self.dev, шлях)) or self.dev, exist_ok=True)
            open(os.path.join(self.dev, шлях), 'w', encoding='utf-8').write(текст)
        git(self.dev, 'add', '-A'); git(self.dev, 'commit', '-qm', f'джерела {мітка0}')
        sha0 = git(self.dev, 'rev-parse', 'HEAD'); self.мітки[sha0] = мітка0
        # початковий стан — опубліковано sha0 (як cd8e5ea7 о 02:47 29.10)
        open(os.path.join(self.dev, 'index.html'), 'w', encoding='utf-8').write(вантаж(self.dev, sha0))
        open(os.path.join(self.dev, 'build.txt'), 'w', encoding='utf-8').write(sha0)
        open(os.path.join(self.dev, 'джерела/аудит/ДОСЯЖНІСТЬ.md'), 'w', encoding='utf-8').write(f'досяжність {sha0}\n')
        git(self.dev, 'add', '-A'); git(self.dev, 'commit', '-qm', f'збірка: {sha0}')
        git(self.dev, 'push', '-q', 'origin', 'HEAD:main')
        self.звірити_main()

    def злити(self, мітка, вид, тека=None):
        """Злиття PR: гілка від main~2, коміт, --no-ff merge у свіжий main. Повертає (before, sha, чи запускає)."""
        тека = тека or self.dev
        git(тека, 'fetch', '-q', 'origin', 'main'); git(тека, 'checkout', '-q', '-B', 'main', 'FETCH_HEAD')
        база = git(тека, 'rev-parse', '-q', '--verify', 'HEAD~2', перевірити=False) or 'HEAD'
        git(тека, 'checkout', '-q', '-B', f'pr/{мітка}', база)
        if вид == 'Д':
            open(os.path.join(тека, f'джерела/код-{мітка}.txt'), 'w', encoding='utf-8').write(f'{мітка}\n')
        if вид in 'ДБ':
            os.makedirs(os.path.join(тека, 'аудит/дошка'), exist_ok=True)
            рядок = f'| {мітка} | рядок дошки |'
            open(os.path.join(тека, f'аудит/дошка/{мітка}.md'), 'w', encoding='utf-8').write(рядок + '\n')
            self.рядки_дошки.append(рядок)
        if вид == 'Н':
            open(os.path.join(тека, f'аудит/інше-{мітка}.md'), 'w', encoding='utf-8').write(f'{мітка}\n')
        git(тека, 'add', '-A'); git(тека, 'commit', '-qm', f'PR {мітка}')
        git(тека, 'checkout', '-q', 'main'); git(тека, 'merge', '-q', '--no-ff', f'pr/{мітка}', '-m', f'Merge {мітка}')
        before, sha = git(тека, 'rev-parse', 'HEAD^1'), git(тека, 'rev-parse', 'HEAD')
        git(тека, 'push', '-q', 'origin', 'HEAD:main')
        self.мітки[sha] = мітка
        шляхи = [f':(exclude,glob){п[1:]}' if п.startswith('!') else f':(glob){п}' for п in self.paths]
        запускає = bool(git(тека, 'diff', '--name-only', before, sha, '--', *шляхи))
        return before, sha, запускає

    def клон(self, sha, глибина, назва):
        """Клон SHA заданої глибини, як actions/checkout для push у main."""
        тека = os.path.join(self.тимчас, f'{назва}-{self.n}'); self.n += 1
        os.makedirs(тека)
        git(тека, 'init', '-q'); git(тека, 'remote', 'add', 'origin', self.url)
        git(тека, 'fetch', '-q', '--no-tags', f'--depth={глибина}', 'origin', f'+{sha}:refs/remotes/origin/main')
        git(тека, 'checkout', '-q', '--force', '-B', 'main', 'refs/remotes/origin/main')
        return тека

    def крок(self, тека, скрипт, env):
        """Виконує bash кроку з тими самими прапорцями, що runner GitHub (`-eo pipefail`)."""
        шлях = os.path.join(тека, '..', f'крок-{self.n}.sh'); self.n += 1
        open(шлях, 'w', encoding='utf-8').write(скрипт)
        return запустити(['bash', '--noprofile', '--norc', '-eo', 'pipefail', шлях], тека,
                         env={**os.environ, **env}, перевірити=False)

    # --- кроки збірки ------------------------------------------------------------------------------------
    def продукт(self, збірка):
        """Крок «які шляхи змінено» на старті прогону: чи йде збірка повним шляхом."""
        тека = self.клон(збірка['sha'], 2, 'zminy')
        вихід = os.path.join(тека, '..', f'output-{self.n}'); self.n += 1
        open(вихід, 'w').close()
        р = self.крок(тека, self.zminy, {'GITHUB_EVENT_NAME': 'push', 'BEFORE': збірка['before'],
                                         'GITHUB_SHA': збірка['sha'], 'GITHUB_OUTPUT': вихід,
                                         'GITHUB_STEP_SUMMARY': os.devnull})
        if р.returncode:
            raise SystemExit(f'zminy {збірка["мітка"]}: {р.returncode}\n{р.stdout}{р.stderr}')
        return 'produkt=true' in open(вихід).read()

    def опублікувати(self, збірка, час):
        """Job publish наприкінці прогону: вантаж збірки, згортання дошки, коміт і push; повертає вивід."""
        sha, тека = збірка['sha'], self.клон(збірка['sha'], 1, 'publish')
        if збірка['produkt']:   # download-artifact кладе перевірені файли в робоче дерево
            open(os.path.join(тека, 'index.html'), 'w', encoding='utf-8').write(вантаж(self.dev, sha))
            open(os.path.join(тека, 'джерела/аудит/ДОСЯЖНІСТЬ.md'), 'w', encoding='utf-8').write(f'досяжність {sha}\n')
        if self.гонка and not os.path.exists(os.path.join(self.тимчас, 'гонка.було')):
            гак = os.path.join(тека, '.git', 'hooks', 'pre-push')
            гонщик = os.path.join(self.тимчас, 'гонщик')
            if not os.path.exists(гонщик):
                запустити(['git', 'clone', '-q', self.url, гонщик], self.тимчас)
                git(гонщик, 'config', 'user.name', 'стенд'); git(гонщик, 'config', 'user.email', 'стенд@локально')
            open(гак, 'w').write(f'#!/bin/sh\nunset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE\n'
                                 f'[ -e "{self.тимчас}/гонка.було" ] && exit 0\ntouch "{self.тимчас}/гонка.було"\n'
                                 f'"{sys.executable}" "{os.path.abspath(__file__)}" --злити-гонку "{гонщик}" '
                                 f'"{self.тимчас}/гонка.txt"\n')
            os.chmod(гак, 0o755)
        підсумок = os.path.join(тека, '..', f'summary-{self.n}'); self.n += 1
        env = {'PRODUKT': 'true' if збірка['produkt'] else 'false', 'GITHUB_STEP_SUMMARY': підсумок,
               'RUNNER_TEMP': os.path.join(тека, '..', f'runner-temp-{self.n}')}
        os.makedirs(env['RUNNER_TEMP'])
        self.крок(тека, self.згортання, env)
        р = self.крок(тека, self.публікація, env)
        текст = (р.stdout + р.stderr + (open(підсумок).read() if os.path.exists(підсумок) else ''))
        if р.returncode:
            self.порушення.append(f'{збірка["мітка"]}: крок публікації впав ({р.returncode}): {текст[-400:]}')
        return текст

    def звірити_main(self):
        """Інваріанти голови origin: index.html ↔ build.txt ↔ джерела штампу, звіт того самого штампу."""
        git(self.dev, 'fetch', '-q', 'origin', 'main')
        штамп = git(self.dev, 'show', 'FETCH_HEAD:build.txt')
        if git(self.dev, 'show', 'FETCH_HEAD:index.html') + '\n' != вантаж(self.dev, штамп):
            self.порушення.append(f'розсинхрон: index.html main не є збіркою штампу {self.мітки.get(штамп, штамп)}')
        if git(self.dev, 'show', 'FETCH_HEAD:джерела/аудит/ДОСЯЖНІСТЬ.md') != f'досяжність {штамп}':
            self.порушення.append(f'розсинхрон: звіт досяжності не від штампу {self.мітки.get(штамп, штамп)}')
        return штамп

    # --- черга concurrency -------------------------------------------------------------------------------
    def прогнати(self, злиття, тривалість, повний):
        """Подієвий прогін: злиття за розкладом і черга concurrency до спорожнення."""
        мітка0 = 'cd8e5ea7' if злиття is ЗЛИТТЯ_2910 else 'початок'
        self.підготувати(мітка0)
        штамп = self.штамп0 = self.звірити_main()
        запущена, очікувана, черга = None, None, list(злиття)

        def поставити(збірка, час):
            """Push у групу concurrency: вільно — старт, інакше очікувана (новіша витісняє старшу)."""
            nonlocal очікувана
            if запущена is None:
                почати(збірка, час)
            else:
                if очікувана is not None:
                    self.збірок['витіснено'] += 1
                очікувана = збірка

        def почати(збірка, час):
            """Старт прогону: шлях із кроку zminy, кінець — за тривалістю повного чи легкого шляху."""
            nonlocal запущена
            збірка['produkt'] = self.продукт(збірка)
            self.збірок['повна' if збірка['produkt'] else 'легка'] += 1
            трив = (тривалість.get(збірка['мітка'], повний) if збірка['produkt'] else ЛЕГКИЙ)
            запущена = (збірка, час + трив)

        while черга or запущена:
            if черга and (запущена is None or черга[0][0] <= запущена[1]):
                час, мітка, вид = черга.pop(0)
                before, sha, запускає = self.злити(мітка, вид)
                if вид == 'Д':
                    self.злиття_джерел.append((час, sha, мітка))
                if запускає:
                    поставити({'sha': sha, 'before': before, 'мітка': мітка}, час)
                continue
            збірка, час = запущена
            текст = self.опублікувати(збірка, час)
            self.повторів += текст.count('push відбито')
            if os.path.exists(f'{self.тимчас}/гонка.txt'):   # злиття, що влізло перед push публікації
                before, sha = open(f'{self.тимчас}/гонка.txt').read().split()
                os.remove(f'{self.тимчас}/гонка.txt')
                self.мітки[sha] = 'гонка'
                self.злиття_джерел.append((час, sha, 'гонка'))
                поставити({'sha': sha, 'before': before, 'мітка': 'гонка'}, час)   # слот ще зайнятий
            запущена = None
            новий = self.звірити_main()
            if новий != штамп:
                if not self.предок(штамп, новий):
                    self.порушення.append(f'штамп назад: {self.мітки.get(штамп)} → {self.мітки.get(новий)}')
                self.публікації.append((час, новий, збірка['мітка']))
                штамп = новий
            if збірка['produkt'] and not self.предок(збірка['sha'], штамп):
                рядок = next((р.strip() for р in текст.splitlines() if 'пропущено' in р), '')
                for s, м in self.мітки.items():
                    рядок = рядок.replace(s, м)
                self.пропуски.append((збірка['мітка'], self.мітки.get(штамп, штамп), рядок))
            if очікувана is not None:
                наступна, очікувана = очікувана, None
                почати(наступна, час)
            self.кінець = час
        self.підсумок(штамп)

    def предок(self, старший, новіший):
        """Чи містить `новіший` коміт `старший` (рівність — теж так)."""
        return запустити(['git', 'merge-base', '--is-ancestor', старший, новіший], self.dev,
                         перевірити=False).returncode == 0

    def підсумок(self, штамп):
        """Друкує публікації, пропуски, затримки, вікно без публікації й порушення інваріантів."""
        def хв(т):
            """Хвилини стенда → «ГГ:ХХ»."""
            return f'{int(т // 60):02d}:{int(т % 60):02d}'
        print('публікації (час UTC стенда — штамп ← збірка):')
        for час, шт, збірка in self.публікації:
            print(f'  {хв(час)}  {self.мітки.get(шт, шт)} ← {збірка}')
        print(f'збірки: повних {self.збірок["повна"]}, легких {self.збірок["легка"]}, '
              f'витіснено з черги {self.збірок["витіснено"]}; push публікації відбито й повторено: {self.повторів}')
        print(f'зелених повних збірок, що не опублікували новіші за штамп джерела: {len(self.пропуски)}')
        for мітка, шт, рядок in self.пропуски:
            print(f'  {мітка}: штамп лишився {шт}' + (f' — «{рядок[:110]}»' if рядок else ''))
        затримки, неопубліковано = [], []
        for час, sha, мітка in self.злиття_джерел:
            коли = next((т for т, шт, _ in self.публікації if self.предок(sha, шт)), None)
            (затримки.append((коли - час, мітка)) if коли is not None else неопубліковано.append(мітка))
        if затримки:
            з, м = max(затримки)
            print(f'найдовша затримка злиття джерел → публікації: {з:.0f} хв ({м})')
        # вікно без публікації: від публікації (чи першого не покритого нею злиття джерел) до наступної
        вікно, межі, попередній = 0.0, '', (None, self.штамп0)
        for час, шт, _ in self.публікації + [(self.кінець, None, None)]:
            старт = min((т for т, sha, _ in self.злиття_джерел
                         if т < час and not self.предок(sha, попередній[1])), default=None)
            if старт is not None:
                початок = старт if попередній[0] is None else max(старт, попередній[0])
                if час - початок > вікно:
                    вікно, межі = час - початок, f'{хв(початок)}–{хв(час)}' + ('' if шт else ' (кінець стенда)')
            попередній = (час, шт)
        print(f'найдовше вікно без публікації за неопублікованих джерел: {вікно:.0f} хв ({межі})')
        print(f'злиття джерел без публікації наприкінці: {len(неопубліковано)}'
              + (f' ({", ".join(неопубліковано)})' if неопубліковано else ''))
        print(f'штамп наприкінці: {self.мітки.get(штамп, штамп)}')
        беклог = git(self.dev, 'show', 'FETCH_HEAD:аудит/БЕКЛОГ.md').splitlines()
        for рядок in self.рядки_дошки:
            if беклог.count(рядок) > 1:
                self.порушення.append(f'рядок дошки подвоєно: {рядок}')
        лишилось = git(self.dev, 'ls-tree', '-r', '--name-only', 'FETCH_HEAD', '--', 'аудит/дошка').splitlines()
        загублено = [р for р in self.рядки_дошки if р not in беклог and not any(р.split()[1] in л for л in лишилось)]
        for р in загублено:
            self.порушення.append(f'рядок дошки загублено: {р}')
        print(f'файлів дошки незгорнуто наприкінці: {len(лишилось)}')
        print('інваріанти: ' + ('цілі' if not self.порушення else 'ПОРУШЕНО'))
        for п in self.порушення:
            print('  ' + п)


def злити_гонку(тека, файл):
    """Виклик із pre-push публікації: ще одне злиття джерел у origin, поки публікація не запушена."""
    for змінна in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'):
        os.environ.pop(змінна, None)
    git(тека, 'fetch', '-q', 'origin', 'main'); git(тека, 'checkout', '-q', '-B', 'main', 'FETCH_HEAD')
    before = git(тека, 'rev-parse', 'HEAD')
    open(os.path.join(тека, 'джерела/код-гонка.txt'), 'w', encoding='utf-8').write('гонка\n')
    git(тека, 'add', '-A'); git(тека, 'commit', '-qm', 'PR гонка')
    git(тека, 'push', '-q', 'origin', 'HEAD:main')
    open(файл, 'w').write(f'{before} {git(тека, "rev-parse", "HEAD")}')


def main():
    """Розбирає аргументи й проганяє сценарій; код 1 — порушено інваріант."""
    п = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    п.add_argument('--yml', default=os.path.join(КОРІНЬ, '.github/workflows/zbirka.yml'))
    п.add_argument('--сценарій', choices=['29.10', 'часті'], default='29.10')
    п.add_argument('--гонка', action='store_true')
    п.add_argument('--злити-гонку', nargs=2, help=argparse.SUPPRESS)
    а = п.parse_args()
    if а.злити_гонку:
        return злити_гонку(*а.злити_гонку)
    стенд = Стенд(а.yml, а.гонка)
    if а.сценарій == '29.10':
        стенд.прогнати(ЗЛИТТЯ_2910, ТРИВАЛІСТЬ_2910, ПОВНИЙ_2910)
    else:
        злиття = [(т, f'д{т:03d}', 'Д') for т in range(0, 361, 12)]
        злиття += [(т + 5.0, f'б{т:03d}', 'Б') for т in range(0, 361, 30)]
        злиття += [(т + 3.0, f'н{т:03d}', 'Н') for т in range(0, 361, 20)]
        стенд.прогнати(sorted((float(т), м, в) for т, м, в in злиття), {}, 35.0)
    print(f'стенд: {стенд.тимчас}')
    sys.exit(1 if стенд.порушення else 0)


if __name__ == '__main__':
    main()
