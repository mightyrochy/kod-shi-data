"""Фіксує завершені кроки прогону, не втручаючись у моделі чи стенд."""
import json
import os
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
plan = json.loads((OUT / 'ПЛАН.json').read_text(encoding='utf-8'))
done_file = OUT / 'done.txt'
done = [json.loads(s) for s in done_file.read_text(encoding='utf-8').splitlines() if s.strip()] if done_file.exists() else []
completed = []
for entry in done:
    args = entry.get('команда', [])
    if '--сцена' not in args:
        continue
    scene = args[args.index('--сцена') + 1]
    if scene not in plan['scenes']:
        raise RuntimeError('Невідома сцена в done.txt')
    folder = OUT / scene
    result = folder / 'результат.json'
    if not result.exists():
        continue
    relative = result.relative_to(ROOT).as_posix()
    tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', '--', relative], cwd=ROOT, capture_output=True)
    if tracked.returncode:
        subprocess.run(['git', 'add', '--', folder.relative_to(ROOT).as_posix(), done_file.relative_to(ROOT).as_posix()], cwd=ROOT, check=True)
        message = f"Е1 15.11: записано спробу {scene}, rc={entry['rc']}"
        subprocess.run(['git', 'commit', '-m', message], cwd=ROOT, check=True, capture_output=True)
        completed.append({'сцена': scene, 'rc': entry['rc']})
active = []
for scene in plan['scenes']:
    folder = OUT / scene
    if folder.is_dir() and not (folder / 'результат.json').exists():
        log = folder / 'лог.txt'
        text = log.read_text(encoding='utf-8').splitlines() if log.exists() else []
        active.append({'сцена': scene, 'останній_рядок': next((s.strip()[:240] for s in reversed(text) if s.strip()), 'старт')})
print(json.dumps({'завершених_спроб': sum('команда' in e for e in done), 'нові_коміти': completed, 'активні': active}, ensure_ascii=False))
