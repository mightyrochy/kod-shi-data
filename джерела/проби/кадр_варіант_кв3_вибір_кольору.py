"""Перевіряє розмітку кольору та відмову від власника без доказу кадрів."""
from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parents[2] / "джерела/лабораторія/кадр_варіант_розмітка.py"),
                   run_name="__main__")
