"""Записує залежності збережених бандлів та verify у клоні виконавця."""
import json
from pathlib import Path
import subprocess
import sys


def main():
    """Пише заголовки й повний verify без доступу до профілю власника."""
    source, output = map(Path, sys.argv[1:3])
    report = []
    for ident in ('20261027-235118-7e4a2f8828ea', '20261028-044724-2afb786802c4',
                  '20261028-044724-1ae2bf44a4a3'):
        status = json.loads((source / (ident + '.json')).read_text(encoding='utf-8'))
        bundle = source / (ident + '.bundle')
        header = bundle.read_bytes().split(b'\n\n', 1)[0].decode('utf-8')
        result = subprocess.run(['git', 'bundle', 'verify', str(bundle)],
                                capture_output=True, encoding='utf-8')
        assert result.returncode == 0 and ('-' + status['start']) in header
        report.append(f"{status['slug']} / {ident}\nпозначка: {status['marker']}\n"
                      f"start: {status['start']}\nhead: {status['head']}\n{header}\n"
                      f"git bundle verify У КЛОНІ ВИКОНАВЦЯ: код {result.returncode}\n{result.stdout}{result.stderr}")
    output.write_text('\n'.join(report), encoding='utf-8')
    print('Три бандли вимагають локальний start; у клоні виконавця verify успішний. Профіль публікатора недоступний.')


if __name__ == '__main__':
    sys.exit(main())
