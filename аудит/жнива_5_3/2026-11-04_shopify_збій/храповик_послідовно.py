"""Запускає весь незмінений храповик одним працівником після таймаутів паралельних вимірів."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
import sys

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела/прилади"))
import храповик_кореня as х

def main():
    """Змінює лише число працівників: усі паспорти, команди, порівняння й таймаути лишаються штатними."""
    with patch.object(х, "ThreadPoolExecutor", lambda **_: ThreadPoolExecutor(max_workers=1)):
        return х.main()

if __name__ == "__main__":
    sys.exit(main())
