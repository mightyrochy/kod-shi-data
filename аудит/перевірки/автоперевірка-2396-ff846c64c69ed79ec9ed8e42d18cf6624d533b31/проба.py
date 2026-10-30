"""Проба приладу ПК-дотримання-правил на голові PR: умовні події для пунктів переліку, які видно з події синтаксично."""
import json, os, subprocess, sys, tempfile
дерево = sys.argv[1]
print("голова:", subprocess.run(["git", "-C", дерево, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip())
sys.path.insert(0, os.path.join(дерево, "джерела", "прилади"))
import корінь_пк_дотримання as п
Д, М = "session_D", "session_M"
def ас(і, ім, вх):
    return {"created_at": f"2026-01-01T00:00:{і:02d}.0Z", "assistant": {"uuid": f"u{і}", "internal_anthropic_catchall":
            {"message": {"content": [{"type": "tool_use", "id": f"t{і}", "name": ім, "input": вх}]}}}}
def кін(і):
    return {"created_at": f"2026-01-01T00:00:{і:02d}.0Z", "result": {"uuid": f"r{і}", "internal_anthropic_catchall":
            {"result": "—", "origin": {"kind": "task-notification"}, "num_turns": 2}}}
випадки = [
  ("ДИСПЕТЧЕР.md:3–8 Edit у джерела/ диспетчером", "диспетчер", [ас(1, "Edit", {"file_path": "/home/user/kod-shi-data/джерела/х.py", "old_string": "a", "new_string": "b"}), кін(2)]),
  ("МЕНЕДЖЕР.md:3–9 Write у джерела/ менеджером", "менеджер", [ас(1, "Write", {"file_path": "джерела/у.js", "content": "x"}), кін(2)]),
  ("ДИСПЕТЧЕР.md:116–118 archive_session у основному ході", "диспетчер", [ас(1, "mcp__claude-code-remote__archive_session", {"session_id": "session_X"}), кін(2)]),
  ("ПЕРЕВІРКА.md:68–74 цикл чекання CI на передньому плані", "перевірка", [ас(1, "Bash", {"command": "until gh pr checks 1; do sleep 60; done"}), кін(2)]),
  ("ВИКОНАВЕЦЬ.md:14–15 гілка від незлитого PR", "виконавець", [ас(1, "Bash", {"command": "git checkout -b claude/x origin/claude/inshyi"}), кін(2)]),
]
for назва, роль, події in випадки:
    дії, _ = п.аналіз(роль, події, Д, М, "", "")
    правила = sorted({д.правило for д in дії if д.правило != "К1"})
    print(f"{назва}: порушень={sum(д.порушення for д in дії)}; правила крім К1={правила}")
