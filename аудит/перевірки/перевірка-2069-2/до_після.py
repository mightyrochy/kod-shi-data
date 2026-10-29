"""Запускає власну пробу на a136a841 (ДО) і на голові злиття (ПІСЛЯ); вивід — файли поруч."""
import io, os, subprocess, sys, tarfile, tempfile
from pathlib import Path

тека = Path(__file__).resolve().parent
корінь = тека.parents[2]
середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
архів = subprocess.check_output(["git", "archive", "a136a841db8fed6703c17866166514729f2875eb", "zhnyvarka"], cwd=корінь)
with tempfile.TemporaryDirectory(prefix="перевірка-2069-2-до-") as т:
    tarfile.open(fileobj=io.BytesIO(архів)).extractall(т, filter="data")
    for назва, дерево in (("ДО", т), ("ПІСЛЯ", str(корінь))):
        р = subprocess.run([sys.executable, str(тека / "власна_проба.py"), дерево], cwd=корінь, env=середовище, capture_output=True)
        текст = р.stdout.decode("utf-8") + р.stderr.decode("utf-8")
        рядки = [л for л in текст.splitlines() if not (л[:2].isdigit() and л[2] == ":")]
        (тека / (назва + ".txt")).write_text("\n".join(рядки) + f"\nКод завершення: {р.returncode}\n", encoding="utf-8", newline="\n")
        print(назва, "код", р.returncode, [л for л in рядки if л.startswith("ПІДСУМОК")])
