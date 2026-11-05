"""Відтворення зауважень Codex і відомих меж приладу на переданому дереві."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile

дерево = Path(sys.argv[1]).resolve()
буфер = io.StringIO()
with contextlib.redirect_stdout(буфер):
    runpy.run_path(str(дерево / 'аудит/перевірки/перевірка-2867/відтворення.py'))
м = sys.modules['прилад']
for рядок in буфер.getvalue().splitlines():
    print(рядок)
випадки = [
    ('Codex-CSS', {'а.html': '<img id="preview"><script>document.querySelector("#preview").src=generate_image()</script>'}, 1),
    ('Codex-CSS-негативний', {'а.html': '<div id="preview"></div><script>document.querySelector("#preview").src=generate_image()</script>'}, 0),
    ('Codex-іменовані', {'а.py': 'def choose(original, generated):\n    return generated\nresult = choose(original="original", generated=generate_image())\njudge(result)\n'}, 1),
    ('Codex-іменовані-негативний', {'а.py': 'def choose(original, generated):\n    return original\nresult = choose(original="original", generated=generate_image())\njudge(result)\n'}, 0),
]
for назва, файли, очікувано in випадки:
    with tempfile.TemporaryDirectory(prefix='перевірка2867_') as т:
        корінь = Path(т)
        (корінь / 'джерела').mkdir()
        for ім, код in файли.items():
            (корінь / 'джерела' / ім).write_text(код, encoding='utf-8')
        звіт = м.лічба(корінь)
        print(json.dumps(dict(випадок=назва, файли=файли, очікувано=очікувано,
                              фактично=звіт['місць'], входи=звіт['входи']), ensure_ascii=False))
