"""Прицільні відтворення на незміненому дереві PR #2396; аргумент — шлях дерева."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile

репо = Path(sys.argv[1]).resolve()
assert subprocess.check_output(["git", "-C", str(репо), "rev-parse", "HEAD"], text=True).strip() == "78d326fec21984a3f6a75d4564e889095f4a1586"


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
    return п.аналіз(роль, події, "session_dispatcher", "session_manager", "", "")


паспорт = (репо / "аудит/корені/ПК-дотримання-правил.md").read_text(encoding="utf-8")
шлях, арг, бази, помилки = х.розібрати_паспорт(паспорт)
print(f"1. Храповик: шлях={шлях!r}; файл існує={(репо / шлях).is_file()}; бази={бази}; помилки розбору={помилки}")
print("   лічити=" + str(х.лічити(str(репо), шлях, арг)))

пульс = виклик(1, "mcp__claude-code-remote__create_trigger", {
    "persistent_session_id": "session_dispatcher", "cron_expression": "0 * * * *",
    "prompt": "ПУЛЬС: такт за аудит/ДИСПЕТЧЕР.md"})
дії, _ = аналіз("диспетчер", [пульс])
print("2. Дозволений пульс: " + "; ".join(f"{д.правило} порушення={д.порушення}" for д in дії))

пропуски = [виклик(1, "mcp__claude-code-remote__list_events", {"session_id": "x", "limit": 100}),
    виклик(2, "mcp__claude-code-remote__send_message", {"session_id": "session_dispatcher", "message": "ЗЛИТИ #1"})]
дії, _ = аналіз("менеджер", пропуски)
print("3. list_events без kinds, limit=100; ЗЛИТИ без SHA: " +
      f"порушень={sum(д.порушення for д in дії)}; правила={[д.правило for д in дії]}")
дії, _ = аналіз("виконавець", [виклик(1, "mcp__github__create_pull_request", {"title": "Правка", "body": "Текст", "draft": False})])
print("   PR виконавця з draft=false: " + f"порушень={sum(д.порушення for д in дії)}; правила={[д.правило for д in дії]}")

результат = {"result": "звіт", "origin": {"kind": "task-notification"}, "num_turns": 1}
дії, стиснення = аналіз("диспетчер", [подія(1, "result", результат),
    подія(2, "system", {"subtype": "compact_boundary"}), подія(3, "result", результат),
    подія(4, "system", {"subtype": "compact_boundary"}), подія(5, "result", результат)])
к1 = [д for д in дії if д.правило == "К1"]
print(f"4. Стиснень={len(стиснення)}; групи дій К1={[д.після for д in к1]}")
print("   " + str(п.зведення(к1)[0]))

with tempfile.TemporaryDirectory(prefix="проба2396_") as т:
    зразок = репо / "джерела/прилади/корінь_пк_дотримання_зразок.json"
    Path(т, "сторінка.json").write_bytes(зразок.read_bytes())
    команда = [sys.executable, "-X", "utf8", "-I", str(репо / "джерела/прилади/корінь_пк_дотримання.py"),
        "--диспетчер", "session_ДИСПЕТЧЕР", "--менеджер", "session_МЕНЕДЖЕР", "--сесія", f"перевірка={т}"]
    перший = subprocess.check_output(команда, encoding="utf-8")
    другий = subprocess.check_output(команда, encoding="utf-8")
    print(f"5. Умовний зразок: повтор ідентичний={перший == другий}; {перший.splitlines()[-1]}")
