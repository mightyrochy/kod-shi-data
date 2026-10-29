"""Відтворює відомі З1–З3 і контрольні форми на незміненому приладі заданого дерева."""
import importlib.util
import pathlib
import sys
import tempfile


def головна():
    root = pathlib.Path(sys.argv[1]).resolve()
    spec = importlib.util.spec_from_file_location('meter', root / 'джерела/прилади/корінь_річ_колір_межі.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    cases = [
        ('З1-підтон', 'колір_простір_риси.py', 'def підтон_риси(a, b, h):\n    return "холодний" if h < 35 else "теплий"\n'),
        ('З2-межі', 'колір_річ.py', 'ДУГИ: dict = {"red": (330, 30), "blue": (200, 270)}\n'),
        ('З2-вікна', 'колір_річ.py', 'ВІКНА: dict = {"red": (0, 90, 10, 80, (330, 30)), "blue": (0, 90, 10, 80, (200, 270)), "green": (0, 90, 10, 80, (100, 180))}\n'),
        ('З3-LCh', 'показ/колір.js', 'function lchToLab(L, C, h) { return [L, C * Math.cos(h * Math.PI / 180), C * Math.sin(h * Math.PI / 180)]; }\n'),
        ('З3-RGB', 'показ/колір.js', 'function family(r, g, b) { return r > g && r > b ? "red" : "other"; }\n'),
        ('П1-контроль', 'колір_річ.py', 'def тон(h):\n    return h % 360\n'),
        ('П2-контроль', 'колір_річ.py', 'def сім_я(h, lab):\n    L = lab[0]\n    return h // 30\n'),
        ('П3-контроль', 'колір_річ.py', 'def той_самий(h1, h2):\n    return abs(h1-h2) < 15\n'),
        ('П3-невідомо', 'колір_річ.py', 'def той_самий(h1, h2):\n    if h1 is None or h2 is None:\n        return False\n    return h1 == h2\n'),
        ('П4-контроль', 'колір_річ.py', 'def сім_я_слова(слово):\n    return "red"\n'),
        ('модуль-П1', 'колір_тон.py', 'def тон(h):\n    return h % 360\n'),
        ('модуль-П2', 'колір_тон.py', 'def сім_я(h, lab):\n    L = lab[0]\n    return h // 30\n'),
        ('модуль-П3', 'колір_тон.py', 'def той_самий(h1, h2):\n    return abs(h1-h2) < 15\n'),
        ('модуль-П4', 'колір_тон.py', 'def сім_я_слова(слово):\n    return "red"\n'),
    ]
    with tempfile.TemporaryDirectory(dir=root.parent) as temporary:
        for label, relative, source in cases:
            file = pathlib.Path(temporary) / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(source, encoding='utf-8')
            found = m.Збір()
            if relative.endswith('.py'):
                m.обхід_python(str(file), 'джерела/' + relative, found, set(), set())
            else:
                m.обхід_js(str(file), 'джерела/' + relative, found)
            points = sorted({point for place in found.м.values() for point in place['пункти']})
            print(f'{label}: місць {len(found.м)}; пункти {points}')


if __name__ == "__main__":
    головна()
