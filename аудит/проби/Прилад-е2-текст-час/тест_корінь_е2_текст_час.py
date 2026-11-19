"""Запускає зразки часу, які є частиною самоперевірки приладу."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'джерела' / 'прилади'))
import корінь_е2_текст_жінці as К

if __name__ == '__main__':
    sys.exit(bool(К.самоперевірка_часу()[1]))
