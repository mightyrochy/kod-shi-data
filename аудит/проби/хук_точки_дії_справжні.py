#!/usr/bin/env python3
"""Мірило наряду ПК-дотримання-правил: три хуки на справжніх транскриптах менеджера й диспетчера 26.10–06.11.

Даних у репозиторії нема: це чати сесій. Сторінки бере `list_events` (claude-code-remote) з `kinds` user, assistant,
other — кожна відповідь як є (`{"data": [...], ...}`) у файл `<тека>/<сесія>/<номер>.json`; вікна — у таблицях нижче.
Подію перетворює `записи()` у транскрипт CLI: слово власника — подія з `client_platform` (`origin.kind = "human"`),
лист і сповіщення — подія `notification` (`task-notification`); кінець ходу — текст асистента, після якого перший запис
— не дія й не результат інструмента. Посеред ходу вхід лягає вкладенням `queued_command`, як у CLI. `stop_reason` у
подіях нема, а ходу, який почало сповіщення, нема й початку — тож межі ходів відновлено, а не прочитано.

Запуск: `python3 аудит/проби/хук_точки_дії_справжні.py --сторінки <тека> [--хуки <тека хуків>]`; ДО — `--хуки` з
`git show origin/main:.claude/хуки/<файл>`. Код виходу 1 — є розбіжність з «чекано».
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")
КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

МЕНЕДЖЕР = {"26.10": "session_01TctSEcetUWE1jcJWUpJjRY", "29.10": "session_01FPQuiaz2yECem4rbVqPg1G",
            "01.11": "session_01FPQuiYEiCWmgRLiwt5d9tJ", "04.11": "session_01FPQuiZyd9M1gnM6g7n3Gkn",
            "05.11": "session_01FPQuia6nzmnfVEqMEDhwMx", "06.11": "session_01FPQuia6nzmnfVEqMEDhwMx"}
# (назва, сесія-відправник, час листа UTC, чекано) — вікна: 26.10 18:37–19:06 і 20:37–21:38, 29.10 03:20–05:47,
# 01.11 20:32–20:55, 04.11 05:40–06:21, 05.11 20:32–20:57, 06.11 05:38–06:01
ЛИСТИ = [
    ("26.10 21:30 — слова 18:52, 18:56 (докір), 19:15, 19:21 під «ДИСПЕТЧЕР: …»", "session_01L7qFqsTWSTWavDgtTNEgy7",
     "2026-10-26T21:30:51", True),
    ("29.10 05:25 — слово 05:24 (питання диспетчерові)", "session_01FPQuiashigctm8vV4JXxd7", "2026-10-29T05:25:44", True),
    ("29.10 05:40 — слово 05:39 (вказівка диспетчерові)", "session_01FPQuiashigctm8vV4JXxd7", "2026-10-29T05:40:10",
     True),
    ("29.10 05:42 — слово 05:41 (докір: «технічне питання до тебе»)", "session_01FPQuiashigctm8vV4JXxd7",
     "2026-10-29T05:42:37", True),
    ("01.11 20:46 — слово 20:45 (докір: «я задав ці питання тобі»)", "session_01FPQuiY6a3ufUCxKG2Naof8",
     "2026-11-01T20:46:31", True),
    ("04.11 06:04 — слово 06:04 (продукт: змінило правила)", "session_01FPQuiY6a3ufUCxKG2Naof8", "2026-11-04T06:04:38",
     False),
    ("05.11 20:52 — слово 20:51 (питання диспетчерові)", "session_01FPQuiXXt31teF6ZdBUPTfA", "2026-11-05T20:52:25", True),
    ("06.11 05:47 — слово 05:46 (відповідь на рядок диспетчера)", "session_01FPQuiXoe5Djj6NLiq4NfqU",
     "2026-11-06T05:47:05", True),
]
ПОВТОР = ("05.11 20:52", "06.11 05:47")  # другий той самий лист — уже не повертається
МЕНЕДЖЕР_0511 = "session_01FPQuia6nzmnfVEqMEDhwMx"
# (назва, початок ходу менеджера UTC, чекано): 05.11 18:49–21:56, 06.11 02:18–06:57
ХОДИ = [
    ("05.11 18:52 лист диспетчера → рядок власникові 18:56", "2026-11-05T18:52", True),
    ("05.11 20:52 лист диспетчера → рядок власникові 20:57", "2026-11-05T20:52", True),
    ("05.11 21:52 лист диспетчера → хід кінчається «—»", "2026-11-05T21:52", False),
    ("06.11 05:28 хід власника → відповіді 05:35 і 05:40", "2026-11-06T05:28", False),
    ("06.11 05:43 хід власника → відповідь 05:45", "2026-11-06T05:43", False),
    ("06.11 05:47 лист диспетчера → рядки 05:59 і 06:00", "2026-11-06T05:47", True),
    ("06.11 06:39 лист диспетчера → рядок 06:40", "2026-11-06T06:39", True),
    ("06.11 06:42 хід власника «Що робиш?» → відповідь 06:44", "2026-11-06T06:42", False),
]


def події(тека):
    вихід, бачені = [], set()
    for ф in sorted(glob.glob(os.path.join(тека, "*.json"))):
        with open(ф, encoding="utf-8") as д:
            сторінка = json.load(д)
        for е in сторінка.get("data", []):
            ключ = next(к for к in е if к != "created_at")
            з = е[ключ]
            всередині = з.get("internal_anthropic_catchall") or з
            ід = з.get("uuid") or всередині.get("uuid")
            if ід in бачені:
                continue
            бачені.add(ід)
            вихід.append((е["created_at"], ключ, з, всередині))
    return sorted(вихід, key=lambda п: п[0])


def текст(вміст):
    if isinstance(вміст, str):
        return вміст
    return "\n".join(б.get("text", "") for б in вміст or [] if isinstance(б, dict) and б.get("type") == "text")


def записи(тека, до=None):
    сирі = []
    for коли, ключ, з, в in події(тека):
        if до and коли[:len(до)] > до:
            break
        п = з.get("message") or в.get("message") or {}
        вміст = п.get("content") if isinstance(п, dict) else None
        if "client_platform" in в or "notification" in в:
            людина = "client_platform" in в
            сирі.append(("вхід", коли, "human" if людина else "task-notification",
                         текст(вміст) if людина else в["notification"].get("content", "")))
        elif в.get("isSynthetic"):
            сирі.append(("стиснення", коли, None, текст(вміст)[:200]))
        elif ключ == "assistant" and isinstance(вміст, list):
            for б in вміст:
                if isinstance(б, dict) and б.get("type") == "text" and б["text"].strip():
                    сирі.append(("текст", коли, None, б["text"]))
                elif isinstance(б, dict) and б.get("type") == "tool_use":
                    сирі.append(("дія", коли, None, {к: б.get(к) for к in ("type", "id", "name", "input")}))
        elif ключ == "user" and isinstance(вміст, list) and any(
                isinstance(б, dict) and б.get("type") == "tool_result" for б in вміст):
            сирі.append(("результат", коли, None, [
                {"type": "tool_result", "tool_use_id": б.get("tool_use_id"),
                 "content": б["content"] if isinstance(б.get("content"), str)
                 else json.dumps(б.get("content"), ensure_ascii=False)}
                for б in вміст if isinstance(б, dict) and б.get("type") == "tool_result"]))
    вихід, у_ході = [], False
    for н, (вид, коли, джерело, дані) in enumerate(сирі):
        if вид == "вхід" and у_ході:
            вихід.append({"type": "attachment", "timestamp": коли,
                          "attachment": {"type": "queued_command", "prompt": дані, "origin": {"kind": джерело}}})
        elif вид == "вхід":
            вихід.append({"type": "user", "timestamp": коли, "origin": {"kind": джерело},
                          "message": {"role": "user", "content": дані}})
            у_ході = True
        elif вид == "стиснення":
            вихід.append({"type": "user", "timestamp": коли, "isCompactSummary": True,
                          "message": {"role": "user", "content": дані}})
        elif вид == "результат":
            вихід.append({"type": "user", "timestamp": коли, "message": {"role": "user", "content": дані}})
        elif вид == "дія":
            вихід.append({"type": "assistant", "timestamp": коли, "message": {"role": "assistant", "content": [дані]}})
        else:
            наступний = next((с[0] for с in сирі[н + 1:] if с[0] != "стиснення"), None)
            запис = {"type": "assistant", "timestamp": коли,
                     "message": {"role": "assistant", "content": [{"type": "text", "text": дані}]}}
            if у_ході and наступний in (None, "вхід"):
                запис["message"]["stop_reason"] = "end_turn"
                у_ході = False
            вихід.append(запис)
    return вихід


def записати(записи_, тека, назва):
    шлях = os.path.join(тека, назва)
    with open(шлях, "w", encoding="utf-8") as ф:
        for з in записи_:
            ф.write(json.dumps(з, ensure_ascii=False) + "\n")
    return шлях


def запустити(хук, вхід, env):
    п = subprocess.run([sys.executable, хук], input=json.dumps(вхід, ensure_ascii=False), capture_output=True,
                       text=True, encoding="utf-8", env=env, timeout=60)
    return п.stdout.strip(), п.stderr.strip()


def середовище(тека, менеджер, диспетчер, я):
    os.makedirs(os.path.join(тека, "аудит"), exist_ok=True)
    with open(os.path.join(тека, "аудит", "СТАН.md"), "w", encoding="utf-8") as ф:
        ф.write(f"| роль | адреса |\n|---|---|\n| менеджер | {менеджер} |\n| диспетчер | {диспетчер} |\n")
    env = dict(os.environ, CLAUDE_PROJECT_DIR=тека, PYTHONIOENCODING="utf-8",
               CLAUDE_CODE_REMOTE_SDK_URL=f"https://x/v1/sessions/cse_{я.removeprefix('session_')}",
               ЛИСТИ_ПОВТОР_ФАЙЛ=os.path.join(тека, "повтор"), ЛИСТИ_СТАН_ФАЙЛ=os.path.join(тека, "зведення"),
               ЛИСТИ_ЗАРАЗ="2026-11-06T12:00:00Z")
    return env


def main():
    а = argparse.ArgumentParser()
    а.add_argument("--сторінки", required=True)
    а.add_argument("--хуки", default=os.path.join(КОРІНЬ, ".claude", "хуки"))
    а = а.parse_args()
    хук_листа = os.path.join(а.хуки, "листи_менеджерові.py")
    хук_кінця = os.path.join(а.хуки, "обіцянка_без_дії.py")
    хук_прийому = os.path.join(а.хуки, "прийом_менеджера.py")
    розбіжностей, рядки = 0, []

    def звіт(група, назва, повернув, чекано, чим=""):
        nonlocal розбіжностей
        розбіжностей += повернув != чекано
        рядки.append(f"{'ок ' if повернув == чекано else 'ХИБА'} {група}: {назва} → "
                     f"{'повертає' if повернув else 'пропускає'}{f' [{чим}]' if чим else ''} (чекано "
                     f"{'повертає' if чекано else 'пропускає'})")

    for назва, сесія, коли, чекано in ЛИСТИ:
        записи_ = записи(os.path.join(а.сторінки, сесія), коли)
        лист = next(б["input"] for з in reversed(записи_) if з["type"] == "assistant"
                    for б in з["message"]["content"] if б.get("type") == "tool_use" and "send_message" in б["name"])
        слова = [з for з in записи_ if з["type"] in ("user", "attachment") and
                 (з.get("origin") or з.get("attachment", {}).get("origin") or {}).get("kind") == "human"]
        менеджер = МЕНЕДЖЕР[f"{коли[8:10]}.{коли[5:7]}"]
        with tempfile.TemporaryDirectory() as т:
            env = середовище(т, менеджер, сесія, сесія)
            шлях = записати(слова, т, "транскрипт.jsonl")
            разів = 2 if назва[:11] in ПОВТОР else 1
            for раз in range(разів):
                вихід, _ = запустити(хук_листа, {"tool_name": "mcp__claude-code-remote__send_message",
                                                  "tool_input": лист, "transcript_path": шлях}, env)
                причина = json.loads(вихід)["hookSpecificOutput"]["permissionDecisionReason"] if вихід else ""
                слово = "звернене до тебе" in причина
                чим = "слово до відправника" if слово else ("інша причина: " + причина[:50]) if причина else ""
                звіт("лист", назва + (" — другий той самий" if раз else ""), слово, чекано and not раз, чим)
    тека_менеджера = os.path.join(а.сторінки, МЕНЕДЖЕР_0511)
    усі = записи(тека_менеджера)
    for назва, початок, чекано in ХОДИ:
        і = next(н for н, з in enumerate(усі) if з["type"] == "user" and "origin" in з
                 and з["timestamp"].startswith(початок))
        к = next(н for н in range(і, len(усі)) if усі[н]["type"] == "assistant"
                 and усі[н]["message"].get("stop_reason") == "end_turn")
        with tempfile.TemporaryDirectory() as т:
            шлях = записати(усі[і:к + 1], т, "транскрипт.jsonl")
            вихід, _ = запустити(хук_кінця, {"transcript_path": шлях, "stop_hook_active": False},
                                 dict(os.environ, PYTHONIOENCODING="utf-8"))
            причина = json.loads(вихід).get("reason", "") if вихід else ""
            к1 = "Текст у чаті читає власник" in причина
            звіт("кінець ходу", назва, к1, чекано, "К1" if к1 else ("інша причина" if причина else ""))
        старт = усі[і]
        with tempfile.TemporaryDirectory() as т:
            env = середовище(т, МЕНЕДЖЕР_0511, "session_01FPQuiXoe5Djj6NLiq4NfqU", МЕНЕДЖЕР_0511)
            if старт["origin"]["kind"] == "human":
                вхід = {"hook_event_name": "UserPromptSubmit", "prompt": старт["message"]["content"]}
            else:
                вхід = {"hook_event_name": "PostToolUse", "tool_name": "ReadNotifications",
                        "tool_response": {"notifications": [{"content": старт["message"]["content"]}]}}
            if not os.path.exists(хук_прийому):
                нагадав = False
            else:
                вихід, _ = запустити(хук_прийому, вхід, env)
                нагадав = "Що доходить" in вихід
            звіт("прийом", назва, нагадав, старт["origin"]["kind"] != "human")
    print("\n".join(рядки))
    print(f"розбіжностей: {розбіжностей}")
    sys.exit(1 if розбіжностей else 0)


if __name__ == "__main__":
    main()
