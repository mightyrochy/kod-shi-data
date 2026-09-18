"""Experiment folder utilities.

Usage:
    from system.exp import create, log

    exp_path = create("sam3_mask_quality")   # → experiments/001_sam3_mask_quality/
    log(exp_path, "started")
"""

import re
from datetime import datetime
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).parent.parent / "experiments"

_PROTOCOL_TEMPLATE = """\
# {folder_name}

Created: {date}

## Question
(what this experiment is trying to answer)

## Method
(how it will be run)

## Setup
- engine:
- seeds:
- inputs:
- fixed config:

## Success criteria
(what result counts as an answer)

## Results
(fill in after running)

## Conclusion
(fill in after reviewing results)
"""


def create(name: str) -> Path:
    """Create experiments/NNN_<name>/ with protocol.md template and results/ subdir.

    Returns the experiment folder path.
    Raises FileExistsError if the folder already exists.
    """
    slug = re.sub(r"[^\w]+", "_", name.lower()).strip("_")
    idx = _next_index()
    folder_name = f"{idx:03d}_{slug}"
    folder = EXPERIMENTS_ROOT / folder_name

    folder.mkdir(parents=True)
    (folder / "results").mkdir()

    protocol = _PROTOCOL_TEMPLATE.format(
        folder_name=folder_name,
        date=datetime.now().strftime("%Y-%m-%d"),
    )
    (folder / "protocol.md").write_text(protocol, encoding="utf-8")

    log(folder, "experiment folder created")
    return folder


def log(exp_path: Path, message: str) -> None:
    """Append a timestamped line to <exp_path>/log.txt."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(exp_path / "log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


def _next_index() -> int:
    if not EXPERIMENTS_ROOT.exists():
        return 1
    existing = [
        p
        for p in EXPERIMENTS_ROOT.iterdir()
        if p.is_dir() and re.match(r"^\d{3}_", p.name)
    ]
    if not existing:
        return 1
    return max(int(p.name[:3]) for p in existing) + 1
