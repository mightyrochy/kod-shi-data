"""Run-folder I/O.

Each pipeline execution gets /runs/NNNNNN with stage subfolders.
Every stage writes its inputs/outputs there so any step is inspectable
and re-runnable in isolation (design principle P6).
"""

import datetime
import json
import re
from pathlib import Path

RUN_ID_PATTERN = re.compile(r"^\d{6}$")


class RunFolder:
    def __init__(self, path: Path):
        self.path = Path(path)

    @property
    def run_id(self) -> str:
        return self.path.name

    def stage_dir(self, name: str) -> Path:
        d = self.path / name
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_json(self, rel_path: str, obj) -> Path:
        p = self.path / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
        return p

    def load_json(self, rel_path: str):
        return json.loads((self.path / rel_path).read_text(encoding="utf-8"))

    def save_text(self, rel_path: str, text: str) -> Path:
        p = self.path / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def log(self, message: str) -> None:
        """Append a timestamped line to the run log. Never overwrites."""
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.path / "run.log", "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] {message}\n")


def next_run_id(runs_dir: Path) -> str:
    runs_dir = Path(runs_dir)
    existing = [
        int(p.name) for p in runs_dir.iterdir()
        if p.is_dir() and RUN_ID_PATTERN.match(p.name)
    ] if runs_dir.exists() else []
    return f"{max(existing, default=0) + 1:06d}"


def create_run(runs_dir: Path) -> RunFolder:
    runs_dir = Path(runs_dir)
    run = RunFolder(runs_dir / next_run_id(runs_dir))
    run.path.mkdir(parents=True)
    run.log(f"run {run.run_id} created")
    return run


def open_run(runs_dir: Path, run_id: str) -> RunFolder:
    path = Path(runs_dir) / run_id
    if not path.is_dir():
        raise FileNotFoundError(f"run {run_id} not found in {runs_dir}")
    return RunFolder(path)
