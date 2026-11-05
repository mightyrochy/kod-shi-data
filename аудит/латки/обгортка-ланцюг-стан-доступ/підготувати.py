"""Будує латку лише на тимчасовому git-дереві та оновлює штатні хеші."""
import hashlib
from pathlib import Path
import re
import subprocess
import sys


ТЕКА = Path(__file__).resolve().parent
АДАПТЕР = 'аудит/адаптери/gemini'


def замінити(текст, старе, нове):
    """Відмовляє, якщо база вже не відповідає оглянутому коду."""
    if текст.count(старе) != 1:
        raise ValueError(f'Неоднозначна база: {старе[:100]!r}')
    return текст.replace(старе, нове)


def main():
    """Править копію, а diff зберігає поряд із цим скриптом."""
    дерево = Path(sys.argv[1]).resolve()
    if дерево == ТЕКА.parents[2] or дерево.parent != ТЕКА.parents[3] / 'tmp':
        raise ValueError('Потрібне тимчасове дерево в tmp цієї задачі')
    база = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=дерево, text=True).strip()
    корінь = дерево / АДАПТЕР
    chain = (корінь / 'wrapper_chain.ps1').read_text(encoding='utf-8-sig')
    # Усі прямі читання цього модуля отримують шлях при винятку; обробка й рішення не змінюються.
    chain = re.sub(r'\[IO\.File\]::ReadAllText\((.+), \$script:Utf8\)', r'(Read-ChainStateText \1)', chain)
    chain = замінити(chain, 'function Write-ChainFailure($Failure) {',
                     (ТЕКА / 'діагностика.ps1').read_text(encoding='utf-8-sig') + '\nfunction Write-ChainFailure($Failure) {')
    chain = замінити(chain,
        '    <# Пише причину збою й безпечне місце: файл:рядок або функція першого кадру створеного блоку.\n\n'
        '    Повідомлення та шляхи лишаються в журналі; назовні виходять лише перевірені тип та місце. #>',
        '    <# Пише тип, місце й JSON-шлях об’єкта в рядок; повний виняток і метадані — у журнали. #>')
    chain = замінити(chain, "    $code = [string]$Failure.Exception.Message",
        "    $code = [string]$Failure.Exception.Message\n"
        "    $diagnosticCode = $(if ($code -cmatch '^CHAIN_[A-Z_]+$') { $code } else { 'CHAIN_FAILED' })\n"
        "    $path = Write-StateFailureDiagnostic $diagnosticCode $Failure")
    chain = замінити(chain,
        ' { $detail = " $kind $where" }',
        ' { $detail = " $kind $where" }\n'
        '        if ($path -and $detail) { $detail += \' ШЛЯХ \' + (ConvertTo-Json -InputObject $path -Compress) }')
    chain = замінити(chain, '    Get-MarkerState $marker $dir',
        '    try { Get-MarkerState $marker $dir }\n'
        '    catch {\n'
        '        if (-not (Get-StateFailurePath $_)) { $_.Exception.Data[\'StatePath\'] = [IO.Path]::GetFullPath((Get-StatePath (Get-MarkerKey $marker) $dir)) }\n'
        '        throw\n'
        '    }')
    (корінь / 'wrapper_chain.ps1').write_text(chain, encoding='utf-8-sig', newline='\n')

    pub = (корінь / 'gemini_publish.ps1').read_text(encoding='utf-8-sig')
    pub = замінити(pub, 'function Get-BadLine([string]$Id, [string]$Why) {',
        'function Get-BadLine([string]$Id, [string]$Why, $Failure = $null) {')
    pub = замінити(pub, '    Write-WrapperLog "стан $Id $Why — не опубліковано"',
        '    if ($null -eq $Failure) {\n'
        '        try { throw [IO.InvalidDataException]::new($Why) } catch { $Failure = $_ }\n'
        '    }\n'
        '    [void](Write-StateFailureDiagnostic \'STATE_INVALID\' $Failure (Join-Path $OutDir ($Id + \'.json\')) $Why)\n'
        '    Write-WrapperLog "стан $Id $Why — не опубліковано"')
    pub = замінити(pub,
        "    if ((Get-Item -LiteralPath $path).Length -gt 65536) { return Get-BadLine $Id 'завеликий' }\n"
        '    try { $s = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json }\n'
        "    catch { return Get-BadLine $Id 'не читається як JSON' }",
        '    try {\n'
        "        if ((Get-Item -LiteralPath $path).Length -gt 65536) { return Get-BadLine $Id 'завеликий' }\n"
        '        $s = [System.IO.File]::ReadAllText($path, $script:Utf8) | ConvertFrom-Json\n'
        "    } catch { return Get-BadLine $Id 'не читається як JSON' $_ }")
    pub = замінити(pub, "$line = Get-BadLine $id 'не обробився'", "$line = Get-BadLine $id 'не обробився' $_")
    старий_шаблон = "    '^GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_[A-Z_]{1,32}(?: [A-Za-z0-9]{1,40} (?:[a-z_]{1,40}\\.ps1:[0-9]{1,5}|[A-Za-z][A-Za-z0-9-]{0,79}))?\\z',"
    новий_шаблон = старий_шаблон + '\n' + r'''    '^GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED [A-Za-z0-9]{1,40} (?:[a-z_]{1,40}\.ps1:[0-9]{1,5}|[A-Za-z][A-Za-z0-9-]{0,79}) ШЛЯХ "(?:[A-Za-z]:\\\\|/)(?:[^"\\\x00-\x1f]|\\["\\]|\\u[0-9a-fA-F]{4}){1,4096}"\z','''
    pub = замінити(pub, старий_шаблон, новий_шаблон)
    pub = замінити(pub, "    if ($Line.Contains('..')) { return 'NO_TEMPLATE' }",
        "    if ($Line.Contains('..')) { return 'NO_TEMPLATE' }\n"
        "    if ($Line -cmatch ' ШЛЯХ (\".*\")\\z') {\n"
        "        try { $path = ConvertFrom-Json $Matches[1] } catch { return 'NO_TEMPLATE' }\n"
        "        if ($path -cmatch '[\\x00-\\x1f\\x7f]' -or -not [IO.Path]::IsPathRooted($path)) { return 'NO_TEMPLATE' }\n"
        "    }")
    (корінь / 'gemini_publish.ps1').write_text(pub, encoding='utf-8-sig', newline='\n')

    повтор = корінь / 'перевірка/повтор_позначок.ps1'
    текст = повтор.read_text(encoding='utf-8-sig')
    текст = замінити(текст,
        "    $script:ChainStateReaders = @([scriptblock]::Create(@'",
        "    $script:ChainStateReaders = @($script:ChainStateReaders | Where-Object { $_.ToString() -cnotmatch '^function Get-MarkerState\\(' }) + @([scriptblock]::Create(@'")
    текст = замінити(текст,
        "$_ -ceq 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED UnauthorizedAccessException Get-MarkerState'",
        "$_ -clike 'GEMINI ОБГОРТКА: ЛАНЦЮГ CHAIN_FAILED UnauthorizedAccessException Get-MarkerState ШЛЯХ *'")
    повтор.write_text(текст, encoding='utf-8-sig', newline='\n')
    gpu = корінь / 'перевірка/сценарії_gpu_моделі.py'
    текст = gpu.read_text(encoding='utf-8')
    текст = замінити(текст, '$script:SlotDir = $TestDir', '$script:StateDir = $TestDir\n$script:SlotDir = $TestDir')
    gpu.write_text(текст, encoding='utf-8', newline='\n')
    (корінь / 'перевірка/сценарії_діагностики_стану.ps1').write_text(
        (ТЕКА / 'сценарії_діагностики_стану.ps1').read_text(encoding='utf-8-sig'), encoding='utf-8-sig', newline='\n')

    опис = корінь / 'НАЛАШТУВАННЯ.md'
    текст = опис.read_text(encoding='utf-8')
    текст = замінити(текст, 'винятку й стек — у `publish.log`.',
        'винятку й стек — у `publish.log`. Крім нього, кожен `CHAIN_*` і `STATE_INVALID` (до приглушення\n'
        'повторних сповіщень) дописується одним JSON-рядком у `C:\\Users\\Public\\gemini\\out\\state-failures.jsonl`\n'
        '(за іншого `-OutDir` — `<OutDir>\\state-failures.jsonl`). Це наявна тека обміну, доступна `gemini`;\n'
        'нові дозволи й зміни ACL не потрібні. Поля: `utc`, `code`, `reason`, `path` (повний шлях),\n'
        '`object_type` (`file`/`directory`/`unavailable`), `owner`, `acl` (SDDL одним рядком), `last_write_utc`,\n'
        '`exception` (повний .NET-виняток), `script_stack`, `position`, `metadata_errors`. Якщо метадані\n'
        'недоступні, їхні поля порожні, а причина — у `metadata_errors`; це не доказ відсутності об’єкта.\n'
        'Для відмови перевірки формату без винятку записується `InvalidDataException` з причиною.\n'
        'Коли читач знає шлях об’єкта, рядок `CHAIN_FAILED` має суфікс `ШЛЯХ "<шлях у JSON>"` без стеку;\n'
        'лапки й зворотні скісні риски екрануються як JSON. Сам журнал є даними з теки обміну, не командами.\n'
        'Збій запису діагностики лишається в `publish.log`, не змінюючи рішення про позначку чи публікацію.')
    # Стан спільний для записувача gemini та читача з обмеженим токеном власника.
    run_path = корінь / 'gemini_run.ps1'
    run = run_path.read_text(encoding='utf-8-sig')
    run = замінити(run, 'function Main {', (ТЕКА / 'спільний_стан.ps1').read_text(encoding='utf-8-sig') + '\nfunction Main {')
    run = замінити(run, '    if ($WorkerFile) { return (Invoke-Worker) }',
        "    if ($WorkerFile) {\n"
        "        $script:StateDir = Join-Path $OutDir 'marker-state'\n"
        "        if (-not (Test-Path -LiteralPath (Join-Path $script:StateDir 'ready'))) { throw 'STATE_NOT_READY' }\n"
        "        return (Invoke-Worker)\n    }")
    run = замінити(run, '        $workers = New-Object System.Collections.ArrayList',
        '        $shared = Initialize-SharedMarkerState\n'
        "        if (-not $shared) { return 0 }\n"
        '        $script:StateDir = $shared\n'
        '        $workers = New-Object System.Collections.ArrayList')
    run_path.write_text(run, encoding='utf-8-sig', newline='\n')
    chain = (корінь / 'wrapper_chain.ps1').read_text(encoding='utf-8-sig')
    chain = замінити(chain, "    $detail = ''", "    $detail = ''\n    $where = ''")
    start = chain.index('        $at = $Failure.InvocationInfo')
    end = chain.index('        Write-WrapperLog', start)
    location = '\n'.join(line[4:] for line in chain[start:end].rstrip().splitlines())
    chain = chain[:start] + chain[end:]
    chain = замінити(chain, "    $where = ''", location)
    chain = замінити(chain, '("chain-failed $code$detail " +', '("chain-failed $code $where " +')
    chain = замінити(chain, '"chain $code$detail"', '"chain $code $where"')
    chain = замінити(chain, "             else { Join-Path $GeminiRunsDir 'state' })",
        "             else { Join-Path $OutDir 'marker-state' })\n"
        "    if ($Model -cnotmatch '^cc-' -and -not (Test-Path -LiteralPath (Join-Path $dir 'ready'))) {\n"
        "        return [pscustomobject]@{ Kind = 'UNKNOWN'; Wait = $null }\n    }")
    (корінь / 'wrapper_chain.ps1').write_text(chain, encoding='utf-8-sig', newline='\n')
    cc_path = корінь / 'claude_run.ps1'
    cc = cc_path.read_text(encoding='utf-8-sig')
    cc = замінити(cc, "[string]$GeminiStateDir = (Join-Path $env:USERPROFILE 'gemini-runs\\state')",
        "[string]$GeminiStateDir = (Join-Path $GeminiOutDir 'marker-state')")
    cc_path.write_text(cc, encoding='utf-8-sig', newline='\n')
    # Фікстура читає той самий стан, що публікатор і планувальник.
    повтор = корінь / 'перевірка/повтор_позначок.ps1'
    проба = повтор.read_text(encoding='utf-8-sig').replace('$GeminiRunsDir/state', '$OutDir/marker-state')
    проба = замінити(проба, '    $seed = "$tmp/seed";', '    Write-FileAtomic "$OutDir/marker-state/ready" \'1\'\n    $seed = "$tmp/seed";')
    повтор.write_text(проба, encoding='utf-8-sig', newline='\n')
    diag = корінь / 'перевірка/сценарії_діагностики_стану.ps1'
    diag.write_text((ТЕКА / diag.name).read_text(encoding='utf-8-sig'), encoding='utf-8-sig', newline='\n')
    (корінь / 'перевірка/сценарії_спільного_стану.ps1').write_text(
        (ТЕКА / 'сценарії_спільного_стану.ps1').read_text(encoding='utf-8-sig'), encoding='utf-8-sig', newline='\n')
    for name in ('сценарії_ланцюга.ps1', 'сценарії_менше_прогонів.ps1', 'сценарії_кінець_роботи.ps1', 'сценарії_живих_pr.ps1'):
        fixture = корінь / 'перевірка' / name
        lines = fixture.read_text(encoding='utf-8-sig').splitlines(keepends=True)
        output = []
        for line in lines:
            output.append(line)
            if ". (Join-Path $SourceDir 'gemini_publish.ps1')" in line:
                output.extend(['    [void][IO.Directory]::CreateDirectory("$OutDir/marker-state")\n',
                               '    Write-FileAtomic "$OutDir/marker-state/ready" \'1\'\n'])
        fixture.write_text(''.join(output), encoding='utf-8-sig', newline='\n')
    for name, old, new in (
        ('сценарії_смуг.sh', '"$W"/gr/state/*.txt', '"$W"/gout/marker-state/*.txt'),
        ('сценарії_доставки.sh', '"$W"/runs/state/*.txt', '"$W"/out/marker-state/*.txt'),
        ('сценарії_claude.sh', 'grep -vE "heartbeat|pools|skipped"', 'grep -vE "heartbeat|pools|skipped|marker-state"'),
    ):
        fixture = корінь / 'перевірка' / name
        value = fixture.read_text(encoding='utf-8-sig')
        fixture.write_text(замінити(value, old, new), encoding='utf-8', newline='\n')
    текст += '\nСтан позначок gemini-run зберігається в `<OutDir>\\marker-state` (типово\n' \
        '`C:\\Users\\Public\\gemini\\out\\marker-state`), де обидва облікові записи вже мають доступ.\n' \
        'Під замком планувальника перехід чекає старих слотів і claims, переписує завершені файли\n' \
        'з приватного `gemini-runs/state` (без перенесення ACL), і лише тоді пише `ready`. До `ready`\n' \
        'ланцюг бачить UNKNOWN; стара історія лишається. Нові процеси нарядів використовують цю ж теку.\n' \
        'Сповіщення CHAIN_FAILED приглушуються за кодом і місцем на UTC-годину, незалежно від шляху\n' \
        'та типу винятку; кожний шлях і повний виняток лишаються у `state-failures.jsonl`.\n'
    маніфест = корінь / 'm9v/хеші.psd1'
    хеші = маніфест.read_text(encoding='utf-8-sig')
    for імʼя in ('wrapper_chain.ps1', 'gemini_publish.ps1', 'gemini_run.ps1', 'claude_run.ps1'):
        хеш = hashlib.sha256((корінь / імʼя).read_bytes()).hexdigest().upper()
        хеші = re.sub(r"('" + re.escape(імʼя) + r"'\s*=\s*')[A-F0-9]{64}'", lambda m: m[1] + хеш + "'", хеші)
        текст = re.sub(r'(\| `' + re.escape(імʼя) + r'` \| `)[A-F0-9]{64}`', lambda m: m[1] + хеш + '`', текст)
    маніфест.write_text(хеші, encoding='utf-8', newline='\n')
    опис.write_text(текст, encoding='utf-8', newline='\n')
    subprocess.run(['git', 'add', '--', АДАПТЕР], cwd=дерево, check=True)
    латка = subprocess.check_output(['git', 'diff', '--cached', '--binary', '--', АДАПТЕР], cwd=дерево)
    (ТЕКА / 'зміна.patch').write_bytes(латка)
    print(f'База {база}; латка {len(латка)} байтів')


if __name__ == '__main__':
    main()
