"""Копія c71cc075 для контрольованого повтору: лише модулі правки й дві функції показу."""
import argparse
import base64
import io
from pathlib import Path
import re
import subprocess
import sys
import zipfile


def скласти(сторінка, вихід, компілятор):
    """Зберігає каталог і решту коду запису; оновлює checked-hash байткод офіційним збирачем."""
    джерела = Path(__file__).resolve().parents[3] / 'джерела'
    sys.path.insert(0, str(джерела))
    import build_артефакт as Б
    from build_байткод import скомпілювати
    html = сторінка.read_text(encoding='utf-8')
    вираз = r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"'
    м = re.search(вираз, html)
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(м[1]))) as z:
        файли = {ім: z.read(ім) for ім in z.namelist()}
    for ім in ('міст_пакет.py', 'міст_запити.py', 'міст_відповіді.py'):
        файли[ім] = Б._стрип(str(джерела / ім))
    файли.update(скомпілювати({ім: в for ім, в in файли.items() if ім.endswith('.py')}, str(компілятор)))
    новий = io.BytesIO()
    with zipfile.ZipFile(новий, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for ім, в in файли.items():
            z.writestr(ім, в)
    html = html[:м.start(1)] + base64.b64encode(новий.getvalue()).decode('ascii') + html[м.end(1):]
    for файл, ім in [('картки.js', 'замінитиРічП'), ('звіти.js', 'знімокПрогонуП')]:
        код = (джерела / 'показ' / файл).read_text(encoding='utf-8')
        початок = re.search(r'^(?:async )?function '+ім+r'\(', код, re.M).start()
        наступна = re.search(r'^(?:async )?function (\w+)\(', код[початок+1:], re.M)
        кінець = початок + 1 + наступна.start()
        # Межа — наступна функція, а не перша закривна дужка вкладеного блока.
        поч = re.search(r'(?:async )?function '+ім+r'\(', html).start()
        кін = re.search(r'(?:async )?function '+наступна[1]+r'\(', html[поч:]).start()+поч
        чистий = Б._чистка_показу('<script>\n'+код[початок:кінець]+'\n</script>')
        чистий = чистий.removeprefix('<script>').removesuffix('</script>')
        html = html[:поч]+чистий+'\n'+html[кін:]
    вихід.parent.mkdir(parents=True, exist_ok=True)
    вихід.write_text(html, encoding='utf-8')
    js = вихід.with_suffix('.js')
    js.write_text('\n'.join(re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>', html)), encoding='utf-8')
    subprocess.run(['node', '--check', str(js)], check=True)
    print('Контрольна копія:', вихід)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('сторінка', type=Path)
    p.add_argument('вихід', type=Path)
    p.add_argument('компілятор', type=Path)
    a = p.parse_args()
    скласти(a.сторінка, a.вихід, a.компілятор.resolve())
