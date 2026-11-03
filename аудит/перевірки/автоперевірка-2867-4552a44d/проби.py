"""Відтворення зауважень Codex на дереві, переданому першим аргументом."""
import json
from pathlib import Path
import sys
import tempfile

голова = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(голова / 'джерела/прилади'))
from корінь_річ_примірка_та_сама_людина import лічба

випадки = [
    ('Codex-4452313108', {'а.html': '<img id="preview"><script>document.querySelector("#preview").src=generate_image()</script>'}, 1),
    ('Codex-4452313121', {'а.py': 'def choose(original, generated):\n    return generated\nresult=choose(original="original", generated=generate_image())\njudge(result)\n'}, 1),
    ('оригінал-CSS', {'а.html': '<img id="preview"><script>document.querySelector("#preview").src="original"</script>'}, 0),
    ('оригінал-Python', {'а.py': 'def choose(original, generated):\n    return original\nresult=choose(original="original", generated=generate_image())\njudge(result)\n'}, 0),
    ('два-покази', {'а.html': '<img id="preview"><canvas id="out"></canvas><script>const p=document.querySelector("#preview");\np.src=generate_image();\ndocument.querySelector("#out").getContext("2d").drawImage(p,0,0);</script>'}, 2),
    ('kwargs', {'а.py': 'def choose(**args):\n    return args["generated"]\njudge(choose(**{"original":"original", "generated":generate_image()}))\n'}, 1),
]
помилок = 0
for назва, файли, очікувано in випадки:
    with tempfile.TemporaryDirectory(prefix='проба2867_') as т:
        дж = Path(т) / 'джерела'
        дж.mkdir()
        for ім, код in файли.items():
            (дж / ім).write_text(код, encoding='utf-8')
        звіт = лічба(Path(т))
        фактично = звіт['місць']
        помилок += фактично != очікувано
        print(json.dumps(dict(випадок=назва, файли=файли, очікувано=очікувано,
                              фактично=фактично), ensure_ascii=False))
print(f'проб: {len(випадки)}; розбіжностей: {помилок}')
sys.exit(bool(помилок))
