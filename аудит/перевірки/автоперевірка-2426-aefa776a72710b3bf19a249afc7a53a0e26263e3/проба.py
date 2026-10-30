"""Відтворює доробку приладу й розподіл подій за рушієм рядка переліку."""
import contextlib
import io
import os
from pathlib import Path
import runpy
import sys
from unittest.mock import patch


def головна():
    """Викликає незмінений прилад голови на контрольованих входах."""
    корінь = Path(sys.argv[1]).resolve()
    os.chdir(корінь)
    прилад = runpy.run_path(str(корінь / "джерела/прилади/корінь_пк_дотримання.py"))
    простір = прилад["головна"].__globals__
    перелік = "аудит/корені/ПК-дотримання-правил-перелік.md"
    for успіх in (True, False):
        вивід = io.StringIO()
        with patch.dict(простір, {"запустити_проби": lambda проби, _: dict.fromkeys(проби, успіх)}):
            with contextlib.redirect_stdout(вивід):
                код = прилад["головна"](["--перелік", перелік, "--проби"])
        print(f"успіх усіх проб={успіх}; код={код}; {вивід.getvalue().splitlines()[-1]}")
    випадки = [
        ("роль", "mcp__claude-code-remote__list_events", {"limit": 100},
         ("К21 ·", "ЧЕРГА.md:32–33 ·")),
        ("рушій", "mcp__github__add_issue_comment", {"body": "@codex fix"},
         ("К11 ·", "CHATGPT.md:16–17 ·")),
    ]
    for назва, інструмент, вхід, початки in випадки:
        подія = {"created_at": "2026-10-30T01:00:00Z", "assistant": {
            "uuid": "умовна-подія", "internal_anthropic_catchall": {"message": {"content": [
                {"type": "tool_use", "id": "умовна-дія", "name": інструмент, "input": вхід}
            ]}}}}
        вивід = io.StringIO()
        with patch.dict(простір, {"події": lambda _: [подія], "відбиток": lambda _: []}):
            with contextlib.redirect_stdout(вивід):
                код = прилад["головна"](["--перелік", перелік, "--сесія", "виконавець=умовна",
                                         "--диспетчер", "диспетчер", "--менеджер", "менеджер"])
        print(f"{назва}: лише одна дія виконавця Claude; код={код}")
        for рядок in вивід.getvalue().splitlines():
            if рядок.startswith(початки):
                print(рядок)


if __name__ == "__main__":
    головна()
