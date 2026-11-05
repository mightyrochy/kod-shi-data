"""Запустити незмінений храповик із заданим числом одночасних вимірів."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "джерела/прилади"))
import храповик_кореня as х

if __name__ == "__main__":
    працівників = int(sys.argv.pop(1))
    # Обмежено лише планувальник; прилади, порівняння й таймаут не змінені.
    with patch.object(х.os, "cpu_count", return_value=працівників):
        sys.exit(х.main())
