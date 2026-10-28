# -*- coding: utf-8 -*-
"""5.3-Б ДО: окремо доводить, що базова проба не могла дійти до перевірки зависання."""
import subprocess, sys, tempfile
from pathlib import Path

корінь = Path(__file__).resolve().parents[2]
код = subprocess.check_output(["git", "show", "8c26d728^:zhnyvarka/обхід.py"], cwd=корінь)
with tempfile.TemporaryDirectory(prefix="обхід-до-") as т:
    файл = Path(т) / "обхід.py"; файл.write_bytes(код)
    п = subprocess.run([sys.executable, файл, "--журнал", т, "--заглушка", "жнива"], capture_output=True, timeout=2)
    assert п.returncode and b"unrecognized arguments" in п.stderr
print("5.3-Б ДО: нема заглушки (--заглушка відхилена argparse)")
