"""Відтворює виправлення й похибки приладу на незміненій голові PR #2396."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile


def модуль(репо, імя, файл):
    """Завантажує модуль саме з перевірюваного дерева."""
    опис = importlib.util.spec_from_file_location(імя, репо / "джерела/прилади" / файл)
    м = importlib.util.module_from_spec(опис)
    опис.loader.exec_module(м)
    return м


def подія(н, вид, дані):
    """Створює умовну подію у форматі зразка автора."""
    return {"created_at": f"2026-10-30T07:00:{н:02d}Z", вид: {
        "uuid": f"подія-{н}", "internal_anthropic_catchall": дані}}


def виклик(н, імя, вхід):
    """Створює умовний виклик інструмента, нічого не виконує."""
    return подія(н, "assistant", {"message": {"content": [{
        "type": "tool_use", "id": f"виклик-{н}", "name": імя, "input": вхід}]}})


def головна():
    """Друкує факти контрольних і граничних проб, перевіряючи SHA дерева."""
    репо = Path(sys.argv[1]).resolve()
    assert subprocess.check_output(["git", "-C", str(репо), "rev-parse", "HEAD"], text=True).strip() == "f44e174e5c7a428afc3ced1974af7cda44ed148d"
    п = модуль(репо, "прилад", "корінь_пк_дотримання.py")
    х = модуль(репо, "храповик", "храповик_кореня.py")

    def аналіз(роль, події):
        """Лічить умовні події за механізмом автора."""
        return п.аналіз(роль, події, "session_dispatcher", "session_manager", "", "")

    паспорт = (репо / "аудит/корені/ПК-дотримання-правил.md").read_text(encoding="utf-8")
    шлях, арг, бази, помилки = х.розібрати_паспорт(паспорт)
    print(f"1. Паспорт: помилки={помилки}; бази={бази}")
    print("   лічити=" + str(х.лічити(str(репо), шлях, арг)))

    дії, _ = аналіз("диспетчер", [виклик(1, "mcp__claude-code-remote__create_trigger", {
        "persistent_session_id": "session_dispatcher", "cron_expression": "0 * * * *",
        "prompt": "ПУЛЬС: такт за аудит/ДИСПЕТЧЕР.md"})])
    print("2. Дозволений пульс: " + "; ".join(f"{д.правило} порушення={д.порушення}" for д in дії))

    дії, _ = аналіз("менеджер", [
        виклик(1, "mcp__claude-code-remote__list_events", {"session_id": "x", "limit": 100}),
        виклик(2, "mcp__claude-code-remote__send_message", {"session_id": "session_dispatcher", "message": "ЗЛИТИ #1"})])
    print("3. list_events без kinds, limit=100; ЗЛИТИ без SHA: " +
          str([(д.правило, д.порушення) for д in дії]))
    дії, _ = аналіз("виконавець", [виклик(1, "mcp__github__create_pull_request", {"title": "Правка", "draft": False})])
    print("   PR виконавця draft=false: " + str([(д.правило, д.порушення) for д in дії]))

    результат = {"result": "звіт", "origin": {"kind": "task-notification"}, "num_turns": 1}
    дії, стиснення = аналіз("диспетчер", [подія(1, "result", результат),
        подія(2, "system", {"subtype": "compact_boundary"}), подія(3, "result", результат),
        подія(4, "system", {"subtype": "compact_boundary"}), подія(5, "result", результат)])
    к1 = [д for д in дії if д.правило == "К1"]
    print(f"4. Стиснень={len(стиснення)}; інтервали К1={[д.інтервал for д in к1]}")
    print("   " + str(п.зведення(к1)[0]))

    with tempfile.TemporaryDirectory(prefix="проба2396_") as т:
        Path(т, "сторінка.json").write_bytes((репо / "аудит/корені/ПК-дотримання-правил-зразок.json").read_bytes())
        команда = [sys.executable, "-X", "utf8", "-I", str(репо / "джерела/прилади/корінь_пк_дотримання.py"),
            "--диспетчер", "session_ДИСПЕТЧЕР", "--менеджер", "session_МЕНЕДЖЕР", "--сесія", f"перевірка={т}"]
        перший = subprocess.check_output(команда, encoding="utf-8")
        другий = subprocess.check_output(команда, encoding="utf-8")
        print(f"5. Умовний зразок: повтор ідентичний={перший == другий}; {перший.splitlines()[-1]}")

    for команда in ("cat аудит/ДИСПЕТЧЕР.md", "cat аудит/ДИСПЕТЧЕР.md | head -n 1"):
        дії, _ = аналіз("диспетчер", [подія(1, "system", {"subtype": "compact_boundary"}),
            виклик(2, "Bash", {"command": команда}), подія(3, "result", результат)])
        print(f"6. К17 {команда!r}: порушення=" + str(next(д.порушення for д in дії if д.правило == "К17")))

    дії, _ = аналіз("диспетчер", [виклик(1, "Edit", {"file_path": "/repo/аудит/СТАН.md",
        "old_string": "попередник", "new_string": "наступник"})])
    print("7. Дозволене ведення СТАН.md диспетчером: " + str([(д.правило, д.порушення) for д in дії]))

    таблиця = паспорт.split("правило · вид · роль · дій · порушень", 1)[1].split("```", 1)[0]
    рядки = [[ч.strip() for ч in р.split("·")] for р in таблиця.splitlines() if р.startswith("К")]
    дія, порушення = (sum(int(р[і]) for р in рядки if р[1] == "місце") for і in (3, 4))
    print(f"8. Сума таблиці паспорта: {порушення} з {дія}")
    дошка = (репо / "аудит/дошка/claude/pk-dotrymannia-pravyl-prylad.md").read_text(encoding="utf-8")
    print("   11501 у фрагменті досі містить 93 з 529: " + str("93 з 529" in дошка.splitlines()[1]))


if __name__ == "__main__":
    головна()
