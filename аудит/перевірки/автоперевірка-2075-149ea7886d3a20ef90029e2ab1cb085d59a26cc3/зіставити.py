"""Ті самі проби доробки на коді ДО; ненульові коди фіксуються без зупинки."""
import json
import os
from pathlib import Path
import subprocess
import sys

голова, до = map(Path, sys.argv[1:3])
тека = Path(__file__).resolve().parent
оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
результати = (json.loads((тека / "ДО-результати.json").read_text(encoding="utf-8"))
              if len(sys.argv) > 3 else [])
for п in sorted((голова / "джерела/проби").glob(sys.argv[3] if len(sys.argv) > 3 else "колір_тип_213_*.py")):
    команда = [sys.executable, "-X", "utf8", str(п)]
    р = subprocess.run(команда, cwd=до / "джерела", env=оточення, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, encoding="utf-8")
    (тека / ("ДО-" + п.stem + ".txt")).write_text(р.stdout, encoding="utf-8")
    результати = [з for з in результати if з["команда"][-1] != str(п)]
    результати.append(dict(команда=команда, код=р.returncode))
    (тека / "ДО-результати.json").write_text(
        json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    print(п.stem, р.returncode, flush=True)
