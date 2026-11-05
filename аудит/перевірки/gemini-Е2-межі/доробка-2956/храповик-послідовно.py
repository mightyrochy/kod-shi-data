"""Запустити незмінений храповик з одним працівником за браку пам'яті."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "джерела/прилади"))
import храповик_кореня as х

if __name__ == "__main__":
    # Міняється лише число одночасних запусків, не прилади, дані, таймаути чи умова приймання.
    with patch.object(х.os, "cpu_count", return_value=1):
        sys.exit(х.main())
