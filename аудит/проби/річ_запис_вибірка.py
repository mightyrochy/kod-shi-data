"""Готує 20 нових різних місць із кодом і повними ланцюгами; оцінює їх людина або сесія очима."""
import json
from pathlib import Path
import random
import sys


def головна():
    """Вибирає нові координати проти збереженого ДО, зерно 2424."""
    до = json.loads(Path('аудит/проби/річ_запис_ланцюг_докази/доробка1/до.json').read_text(encoding='utf8'))
    після = json.loads(Path(sys.argv[1]).read_text(encoding='utf8'))
    старі = {(м['файл'], м['рядок']) for м in до['місця']}
    нові = {}
    for м in після['місця']:
        к = м['файл'], м['рядок']
        if к not in старі:
            нові.setdefault(к, []).append(м)
    вибірка = []
    for ф, р in sorted(random.Random(2424).sample(sorted(нові), min(20, len(нові)))):
        код = Path(ф).read_text(encoding='utf8').splitlines()
        вибірка.append(dict(файл=ф, рядок=р, місця=нові[ф, р], код=[f'{i + 1}: {код[i]}' for i in range(max(0, р - 4), min(len(код), р + 3))]))
    print(json.dumps(dict(нових_координат=len(нові), зерно=2424, вибірка=вибірка), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    головна()
