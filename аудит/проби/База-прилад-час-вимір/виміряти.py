# -*- coding: utf-8 -*-
"""Міряє прилад на копіях записів; відновлює лише створені ним нічні бази."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from datetime import datetime, timezone


КОРІНЬ = Path(__file__).resolve().parents[3]
ЗВІТ = Path(__file__).resolve().parent
ВХІД = КОРІНЬ / 'аудит/проби/автоживий-04911e686195fc47873b70a231d6b70876f83af2'
НІЧНІ = КОРІНЬ / 'аудит/проби/нічні'
ТИМЧАСОВА = Path(os.environ['TEMP']).resolve() / 'base-time-measure'
ДО = '5432127751b0abf7b7c0cef14fb15f482c80e1b8'
ПРИЛАД = КОРІНЬ / 'аудит/проби/нова_база.js'
ПЯТЬ = ['ж3_кафе_20', 'ж4_весілля_гостя', 'ж4_робота',
        'ж7_збій_правил_без_підборів', 'ж7_ювілей_свекрухи']


def utc():
    return datetime.now(timezone.utc).isoformat()


def відбитки(тека):
    return {str(ф.relative_to(тека)): hashlib.sha256(ф.read_bytes()).hexdigest()
            for ф in тека.rglob('*') if ф.is_file()}


def видалити(тека, межа):
    """Видаляє лише перевірену дочірню теку в межах робочої задачі."""
    тека, межа = тека.resolve(), межа.resolve()
    if тека == межа or not тека.is_relative_to(межа):
        raise ValueError(f'Поза межею видалення: {тека}')
    shutil.rmtree(тека)


def виконати():
    ТИМЧАСОВА.mkdir(exist_ok=True)
    джерело = ТИМЧАСОВА / 'before.js'
    джерело.write_bytes(subprocess.check_output(['git', 'show', ДО + ':аудит/проби/нова_база.js'], cwd=КОРІНЬ))
    обгортка = ТИМЧАСОВА / 'run.cjs'
    обгортка.write_text("""const fs = require('fs'), path = require('path'), Module = require('module'), zlib = require('zlib');
const [source, original, input, root] = process.argv.slice(2);
const m = new Module(original, module);
m.filename = original; m.paths = Module._nodeModulePaths(path.dirname(original));
m._compile(fs.readFileSync(source, 'utf8'), original);
const results = {}, capture = path.join(path.dirname(original), 'База-прилад-час-вимір', path.basename(input) + '-стенд.json.gz');
process.exitCode = m.exports.виконати([input, '--main', 'origin/main'], root, {відтворити: (...args) => {
  const result = m.exports.відтворитиЗапис(...args);
  results[path.basename(args[0])] = result;
  fs.writeFileSync(capture, zlib.gzipSync(JSON.stringify(results)));
  return result;
}});
""", encoding='utf-8')
    середовище = dict(os.environ, NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')
    записи = sorted(ф.parent for ф in ВХІД.rglob('повтор.json') if (ф.parent / 'результат.json').is_file())
    збережено = ЗВІТ / 'вимір.json'
    перед = json.loads(збережено.read_text(encoding='utf-8'))['вхідні_файли'] if збережено.exists() else відбитки(ВХІД)
    дані = json.loads(збережено.read_text(encoding='utf-8')) if збережено.exists() else {'початок': utc(), 'base': ДО, 'main': subprocess.check_output(
        ['git', 'rev-parse', 'origin/main'], cwd=КОРІНЬ, text=True).strip(),
        'записів': len(записи), 'вхідні_файли': перед, 'запуски': []}

    def запуск(назва, джерела, код, ліміт):
        готовий = next((р for р in дані['запуски'] if р['назва'] == назва), None)
        if готовий:
            return готовий
        тека = ТИМЧАСОВА / назва
        if тека.exists():
            # Незавершений попередній хід: його докази зберігаємо, копію входу відновлюємо.
            for суфікс in ('.log', '-НОВА_БАЗА.md', '-стенд.json.gz'):
                файл = ЗВІТ / (назва + суфікс)
                if файл.exists():
                    файл.rename(ЗВІТ / (назва + '-попередній-хід' + суфікс))
            видалити(тека, ТИМЧАСОВА)
        тека.mkdir()
        for сцена in джерела:
            shutil.copytree(сцена, тека / сцена.name)
        було = {ф.resolve() for ф in НІЧНІ.rglob('*')}
        батьки = {ф.parent for ф in було} | {НІЧНІ.resolve()}
        команда = ['node', str(обгортка), str(код), str(ПРИЛАД), str(тека), str(КОРІНЬ)]
        запис = {'назва': назва, 'команда': команда, 'сцени': [str(с.relative_to(ВХІД)) for с in джерела],
                 'початок': utc()}
        початок = time.perf_counter()
        try:
            with (ЗВІТ / (назва + '.log')).open('wb') as лог:
                процес = subprocess.Popen(команда, cwd=КОРІНЬ, env=середовище,
                                          stdout=лог, stderr=subprocess.STDOUT)
                try:
                    запис['rc'] = процес.wait(timeout=ліміт)
                except subprocess.TimeoutExpired:
                    запис['таймаут'] = ліміт
                    subprocess.run(['taskkill', '/PID', str(процес.pid), '/T', '/F'],
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    процес.wait()
                    raise
        finally:
            запис['секунд'] = time.perf_counter() - початок
            запис['кінець'] = utc()
            підсумок = тека / 'НОВА_БАЗА.md'
            if підсумок.exists():
                текст = підсумок.read_text(encoding='utf-8').replace(os.path.relpath(тека, КОРІНЬ), '<вхід>')
                запис['рішення'] = текст
                (ЗВІТ / (назва + '-НОВА_БАЗА.md')).write_text(текст, encoding='utf-8')
            створено = {ф.resolve() for ф in НІЧНІ.rglob('*')} - було
            запис['створено_нічних_файлів'] = [str(ф.relative_to(КОРІНЬ)) for ф in sorted(створено) if ф.is_file()]
            # Прилад не перезаписує наявних баз: прибираємо тільки нові піддерева.
            верхні = [ф for ф in створено if ф.is_dir() and (ф.parent in батьки or ф.parent in було)]
            for ф in sorted(верхні, key=lambda ф: len(ф.parts)):
                if ф.exists():
                    видалити(ф, НІЧНІ)
            дані['запуски'].append(запис)
            (ЗВІТ / 'вимір.json').write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print(назва, запис.get('rc', 'таймаут'), round(запис['секунд'], 3), flush=True)
        return запис

    for назва in ПЯТЬ:
        сцена = ВХІД / назва
        до = запуск('ДО-' + назва, [сцена], джерело, 900)
        після = запуск('ПІСЛЯ-' + назва, [сцена], ПРИЛАД, 900)
        дані.setdefault('порівняння_фактичних_рішень', {})[назва] = до.get('рішення') == після.get('рішення')
    # Та сама множина без зміни глибини обходу приладу: верхній рівень, потім вкладені батьки.
    дані.setdefault('початок_повного_проходу', utc())
    (ЗВІТ / 'вимір.json').write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    початок = datetime.fromisoformat(дані['початок_повного_проходу'])
    for і, батько in enumerate(sorted({с.parent for с in записи})):
        залишок = 10800 - (datetime.now(timezone.utc) - початок).total_seconds()
        if залишок <= 0:
            raise TimeoutError('Повний прохід перевищив 3 години')
        try:
            запуск('повний-' + str(і + 1), [с for с in записи if с.parent == батько], ПРИЛАД, залишок)
        except subprocess.TimeoutExpired:
            дані['межа_трьох_годин'] = True
            break
    дані['вхід_незмінний'] = перед == відбитки(ВХІД)
    дані['кінець'] = utc()
    (ЗВІТ / 'вимір.json').write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not дані['вхід_незмінний']:
        raise AssertionError('Вхідні записи змінилися')


if __name__ == '__main__':
    виконати()
