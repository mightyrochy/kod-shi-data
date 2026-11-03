"""Незалежні проби приладу #2867; аргумент — дерево перевіреної голови."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

голова = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(голова / 'джерела/прилади'))
spec = importlib.util.spec_from_file_location('прилад', голова / 'джерела/прилади/корінь_річ_примірка_та_сама_людина.py')
м = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = м
spec.loader.exec_module(м)

випадки = [
    ('контроль-суд', {'а.py': 'judge(generate_image())\n'}, 1),
    ('python-показ', {'а.py': 'import streamlit as st\nst.image(generate_image())\n'}, 1),
    ('python-показ-display', {'а.py': 'from IPython.display import display\ndisplay(generate_image())\n'}, 1),
    ('python-аліас-джерела', {'а.py': 'from vendor import generate_image as draw\njudge(draw())\n'}, 1),
    ('python-аліас-контроль', {'а.py': 'from vendor import generate_image\njudge(generate_image())\n'}, 1),
    ('js-фон', {'а.html': '<div id="preview"></div><script>document.getElementById("preview").style.backgroundImage="url("+generate_image()+")";</script>'}, 1),
    ('js-суд-аліас', {'а.js': 'const rate=measure_skin;\nrate(generate_image());\n'}, 1),
    ('js-суд-контроль', {'а.js': 'measure_skin(generate_image());\n'}, 1),
    ('js-зовнішній-canvas', {'а.html': '<canvas id="preview"></canvas><script>const c=document.getElementById("preview");c.getContext("2d").drawImage(generate_image(),0,0);</script>'}, 1),
]
for назва, файли, очікувано in випадки:
    with tempfile.TemporaryDirectory(prefix='перевірка2867_') as т:
        дерево = Path(т)
        (дерево / 'джерела').mkdir()
        for ім, код in файли.items():
            (дерево / 'джерела' / ім).write_text(код, encoding='utf-8')
        звіт = м.лічба(дерево)
        print(json.dumps(dict(випадок=назва, файли=файли, очікувано=очікувано,
                              фактично=звіт['місць'], входи=звіт['входи']), ensure_ascii=False))
