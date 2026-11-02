"""Відтворює число місць із невдалими пробами та підміну ролі в рядках переліку."""
import contextlib
import io
import os
from pathlib import Path
import runpy
import sys
from unittest.mock import patch


def головна():
    """Викликає незмінений прилад із заданого дерева на контрольованому вході."""
    корінь = Path(sys.argv[1]).resolve()
    os.chdir(корінь)
    прилад = runpy.run_path(str(корінь / "джерела/прилади/корінь_пк_дотримання.py"))
    простір = прилад["головна"].__globals__
    перелік = "аудит/корені/ПК-дотримання-правил-перелік.md"
    print("ДО: усі проби успішні; ПІСЛЯ: усі проби невдалі (підмінено лише результат запуску).")
    for успіх in (True, False):
        вивід = io.StringIO()
        with patch.dict(простір, {"запустити_проби": lambda проби, _: dict.fromkeys(проби, успіх)}):
            with contextlib.redirect_stdout(вивід):
                код = прилад["головна"](["--перелік", перелік, "--проби"])
        print(f"успіх={успіх}; код={код}; " + "; ".join(вивід.getvalue().splitlines()[-2:]))
    час = "2026-10-30T01:00:00Z"
    подія = {"created_at": час, "assistant": {"uuid": "подія-1", "internal_anthropic_catchall": {
        "message": {"content": [{"type": "tool_use", "id": "дія-1",
        "name": "mcp__claude-code-remote__list_events", "input": {"limit": 100}}]}}}}
    вивід = io.StringIO()
    with patch.dict(простір, {"події": lambda _: [подія], "відбиток": lambda _: []}):
        with contextlib.redirect_stdout(вивід):
            прилад["головна"](["--перелік", перелік, "--сесія", "виконавець=умовна",
                                "--диспетчер", "диспетчер", "--менеджер", "менеджер"])
    print("Вхід: лише виконавець, один list_events(limit=100), подій диспетчера немає.")
    for рядок in вивід.getvalue().splitlines():
        if рядок.startswith(("К21 ·", "ЧЕРГА.md:32–33 ·")):
            print(рядок)


if __name__ == "__main__":
    головна()
