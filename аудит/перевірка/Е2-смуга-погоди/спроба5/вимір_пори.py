"""Друкує результат чинного погодного читача без смуги дня, але з порою року."""
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'джерела'))
import суд_погода as погода

if __name__ == '__main__':
    річ = dict(річ='літній льон', слот='низ', сезон_тканини=('hot',), сезон_за_чим=('льон',))
    try:
        знахідки = погода.сезон_без_градусів([річ], [], 'зима')
        print('знахідок:', len(знахідки))
        for знахідка in знахідки:
            print(знахідка)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
