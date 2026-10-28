"""Оновлює й перевіряє захищені латки в тимчасовій копії, не торкаючись робочих правил."""
import difflib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

КОРІНЬ = Path(__file__).resolve().parents[3]
ЛАТКИ = КОРІНЬ / 'аудит/латки/Е1-приймання-наживо'
БАЗА = '509226902538880ae9a167247d91bd6032fe074e'


def git(*аргументи, cwd=КОРІНЬ):
    """Виконує read-only git або застосування латки лише до тимчасової копії."""
    return subprocess.check_output(['git', *map(str, аргументи)], cwd=cwd)


def перевірити():
    """Перевіряє порядок #1945 → Е1 на поточному main та створює доповнення храповика."""
    with tempfile.TemporaryDirectory(prefix='Е1-латки-') as tmp:
        тека = Path(tmp)
        with zipfile.ZipFile(io.BytesIO(git('archive', '--format=zip', БАЗА, '.github', 'аудит/адаптери/gemini'))) as архів:
            архів.extractall(тека)
        git('apply', '--check', ЛАТКИ / '00-1945-на-базі.patch', cwd=тека)
        git('apply', ЛАТКИ / '00-1945-на-базі.patch', cwd=тека)
        for ім in ('02-stendy.patch', '03-sposterihach.patch'):
            файл = тека / ім
            файл.write_bytes(git('show', '943ea4288604273494caec883597a33d07933ed6:аудит/латки/CI-шляхи-й-стенди-обгортки/' + ім))
            git('apply', '--check', файл, cwd=тека)
            git('apply', файл, cwd=тека)
        for ім in ('01-приймання.patch', '02-нічна-позначка.patch', '03-нічний-стенд-CI.patch'):
            git('apply', '--check', ЛАТКИ / ім, cwd=тека)
            git('apply', ЛАТКИ / ім, cwd=тека)
        шлях = '.github/workflows/zbirka.yml'
        файл = тека / шлях
        до = файл.read_text(encoding='utf-8')
        після = до.replace('        id: stend\n        env:', '        id: stend\n        continue-on-error: true\n        env:')
        після = після.replace('; крок блокує)', '; дим без приймання)')
        після = після.replace("          python-version: '3.11'\n      - uses: actions/setup-node", "          python-version: '3.12.1'\n      - uses: actions/setup-node")
        початок = після.index('      - name: усі звірки мають огляд')
        після = після[:початок] + '''      - name: код базового main й повна збірка
        env:
          BASE_REF: ${{ github.event.pull_request.base.sha || github.event.before }}
        run: |
          if [ -z "$BASE_REF" ] || ! git cat-file -e "${BASE_REF}^{commit}"; then
            echo "Нема коду бази для храповика" >&2
            exit 1
          fi
          git worktree add --detach "${RUNNER_TEMP}/main-replay" "$BASE_REF"
          mkdir -p "${RUNNER_TEMP}/main-pokaz"
          NODE_PATH="${GITHUB_WORKSPACE}/джерела/node_modules" LYUSTERKO_CATALOG=повний python "${RUNNER_TEMP}/main-replay/джерела/build_артефакт.py" \\
            "${RUNNER_TEMP}/main-replay/джерела" "${RUNNER_TEMP}/main-pokaz/index.html" показ-повний
      - name: усі звірки мають огляд''' + після[початок + len('      - name: усі звірки мають огляд'):]
        після = після.replace('      - name: записані сцени через продукт\n', '''      - name: храповик і відомі червоні звірки
        run: node аудит/проби/перевірити_храповик.js
      - name: записані сцени через продукт
''')
        після = після.replace('          NODE_PATH: джерела/node_modules\n        run: |\n          node аудит/проби/приймання_записів.js', '''          NODE_PATH: джерела/node_modules
          REPLAY_BASE_BUILD: ${{ runner.temp }}/main-pokaz
          REPLAY_BASE_ROOT: ${{ runner.temp }}/main-replay
        run: |
          node аудит/проби/приймання_записів.js''')
        файл.write_text(після, encoding='utf-8', newline='\n')
        латка = 'diff --git a/' + шлях + ' b/' + шлях + '\n' + ''.join(difflib.unified_diff(
            до.splitlines(True), після.splitlines(True), fromfile='a/' + шлях, tofile='b/' + шлях))
        доповнення = ЛАТКИ / '04-храповик.patch'
        доповнення.write_text(латка, encoding='utf-8', newline='\n')
        файл.write_text(до, encoding='utf-8', newline='\n')
        git('apply', '--check', доповнення, cwd=тека)
        git('apply', доповнення, cwd=тека)
        import yaml
        документи = {ім: yaml.safe_load((тека / '.github/workflows' / ім).read_text(encoding='utf-8'))
                     for ім in ('zbirka.yml', 'obhortka.yml')}
        job = документи['zbirka.yml']['jobs']['pryimannia']
        assert len(job['strategy']['matrix']['chastyna']) == 10
        assert any('REPLAY_BASE_BUILD' in к.get('env', {}) for к in job['steps'])
        assert 'pryimannia' in документи['zbirka.yml']['jobs']['zbirka']['needs']
        звіт = {'база': БАЗА,
                'порядок': ['00-1945-на-базі.patch', '02-stendy.patch', '03-sposterihach.patch',
                            '01-приймання.patch', '02-нічна-позначка.patch', '03-нічний-стенд-CI.patch', '04-храповик.patch'],
                'apply_check': True, 'yaml': list(документи), 'частин': 10}
        (Path(__file__).parent / 'латки-5.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(json.dumps(звіт, ensure_ascii=False))


if __name__ == '__main__':
    перевірити()
