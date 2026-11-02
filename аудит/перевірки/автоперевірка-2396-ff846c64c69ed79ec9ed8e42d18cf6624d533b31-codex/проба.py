"""Відтворює охоплення правил на незміненій голові PR; аргумент — її робоче дерево."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

репо = Path(sys.argv[1]).resolve()
assert subprocess.check_output(["git", "-C", str(репо), "rev-parse", "HEAD"], text=True).strip() == "ff846c64c69ed79ec9ed8e42d18cf6624d533b31"


def модуль(імя, файл):
    опис = importlib.util.spec_from_file_location(імя, репо / "джерела/прилади" / файл)
    м = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(м)
    return м


п = модуль("прилад", "корінь_пк_дотримання.py")
х = модуль("храповик", "храповик_кореня.py")


def подія(н, вид, дані):
    return {"created_at": f"2026-10-30T07:00:{н:02d}Z", вид: {
        "uuid": f"подія-{н}", "internal_anthropic_catchall": дані}}


def виклик(н, імя, вхід):
    return подія(н, "assistant", {"message": {"content": [{
        "type": "tool_use", "id": f"виклик-{н}", "name": імя, "input": вхід}]}})


def аналіз(роль, події):
    return п.аналіз(роль, події, "диспетчер-id", "менеджер-id", "", "")


паспорт = (репо / "аудит/корені/ПК-дотримання-правил.md").read_text(encoding="utf-8")
шлях, арг, бази, помилки = х.розібрати_паспорт(паспорт)
print(f"1. Паспорт: прилад={шлях}; бази={бази}; помилки={помилки}")
print(f"   лічити={х.лічити(репо, шлях, арг)}")
дії, _ = аналіз("диспетчер", [виклик(1, "mcp__claude-code-remote__create_trigger", {
    "persistent_session_id": "диспетчер-id", "cron_expression": "0 * * * *", "prompt": "ПУЛЬС", "name": "Пульс"})])
print("2. Дозволений пульс: " + str([(д.правило, д.порушення) for д in дії]))
дії, _ = аналіз("менеджер", [
    виклик(1, "mcp__claude-code-remote__list_events", {"session_id": "сесія", "limit": 100}),
    виклик(2, "mcp__claude-code-remote__send_message", {"session_id": "диспетчер-id", "message": "ЗЛИТИ #1"})])
print("3. list_events без kinds, limit=100; ЗЛИТИ без SHA: " + str([(д.правило, д.порушення) for д in дії]))
дії, _ = аналіз("виконавець", [виклик(1, "mcp__github__create_pull_request", {"head": "гілка", "draft": False})])
print("   PR виконавця з draft=false: " + str([(д.правило, д.порушення) for д in дії]))
рез = {"result": "звіт", "origin": {"kind": "task-notification"}, "num_turns": 1}
дії, стиснення = аналіз("диспетчер", [подія(1, "result", рез),
    подія(2, "system", {"subtype": "compact_boundary"}), подія(3, "result", рез),
    подія(4, "system", {"subtype": "compact_boundary"}), подія(5, "result", рез)])
print(f"4. Стиснень={len(стиснення)}; К1=" + str(п.зведення([д for д in дії if д.правило == "К1"])[0]))

for роль in ("диспетчер", "менеджер"):
    for інструмент, вхід in (("Edit", {"file_path": "/repo/джерела/pipeline.py", "old_string": "x", "new_string": "y"}),
                              ("Write", {"file_path": "/repo/джерела/pipeline.py", "content": "x = 1"})):
        дії, _ = аналіз(роль, [виклик(1, інструмент, вхід)])
        print(f"5. {роль}, {інструмент} джерела/pipeline.py: дій={len(дії)}, порушень={sum(д.порушення for д in дії)}")

with tempfile.TemporaryDirectory(prefix="проба2396_") as т:
    Path(т, "сторінка.json").write_bytes((репо / "аудит/корені/ПК-дотримання-правил-зразок.json").read_bytes())
    команда = [sys.executable, "-X", "utf8", "-I", str(репо / шлях),
               "--диспетчер", "session_ДИСПЕТЧЕР", "--менеджер", "session_МЕНЕДЖЕР", "--сесія", f"перевірка={т}"]
    перший = subprocess.check_output(команда, encoding="utf-8")
    другий = subprocess.check_output(команда, encoding="utf-8")
    print(f"6. Умовний зразок: повтор ідентичний={перший == другий}; {перший.splitlines()[-1]}")
