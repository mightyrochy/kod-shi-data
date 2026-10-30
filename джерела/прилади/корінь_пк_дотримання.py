#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""прилади/корінь_пк_дотримання.py — прилад кореня ПК-дотримання-правил: частка дій сесій із порушенням правила.

Паспорт — `аудит/корені/ПК-дотримання-правил.md`. Місце — правило ядра, файлу ролі чи адаптера, що велить або забороняє
дію сесії, коли в мить цієї дії його перевіряє лише пам'ять сесії. Прилад лічить на збережених сторінках `list_events`
(claude-code-remote; `kinds`: assistant, user, result, system) правила з переліку `аудит/корені/ПК-дотримання-правил-перелік.md`,
порушення яких видно з самої події. Кожне правило — функція над подіями: точка дії → дія → порушення так чи ні.

Вхід: теки зі сторінками `*.json` (кожна сторінка — об'єкт `ccr` відповіді `list_events`: `data`, `first_id`, `last_id`),
по одній теці на сесію (у теці лише сторінки). Формат — умовний зразок `аудит/корені/ПК-дотримання-правил-зразок.json`. Події зі сторінок зливаються за `uuid`,
сортуються за `created_at`. Сторінки у репозиторій не кладуться (обсяг): їх збирає той, хто лічить.

Рядок підсумку — `правило · роль · дій · порушень · до/після стиснення` («до/після» — дії до першого `compact_boundary` у
даних сесії і після нього, у кожному: порушень/дій). Вид правила: «місце» — тримає лише пам'ять; «контроль» — уже тримає
хук (рядок — перевірка механізму, у підсумок не входить); «кандидат» — порушення залежить від змісту, який подія не
розрізняє, тому число — верхня межа, і в підсумок воно не входить. Останній рядок — `порушень: <N> з <дій>` за «місцями».

Не лічить (подія не показує): зміст листа, лише його початок; стан CI на мить злиття; дії через `Bash` (редагування
файлів `sed`, коміт чи пуш у скрипті — лише рядки `git commit`/`git push` у тексті команди); правила про файли й дані
в PR (їх дивиться CI); блокер «ЗАБЛОКОВАНО» і мова листа — зміст.

Запуск (з кореня репозиторію):
  python3 -I джерела/прилади/корінь_пк_дотримання.py \\
      --диспетчер session_… --менеджер session_… \\
      --сесія диспетчер=<тека> --сесія менеджер=<тека> --сесія перевірка=<тека> [--до 2026-10-30T05:17]
      [--від …] [--зразок N] [--json]
`--зразок N` додає N дій із порушенням і N без (рівномірно за часом) для ручного звіряння.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import OrderedDict

ЛЮДИНА_ВІДСУТНЯ = {None, "claude_code_sdk", "claude_code_mcp", "claude_code_mcp_seed"}
ПЕРЕЛІК_ЛИСТА_МЕНЕДЖЕРОВІ = ("СЛОВО ВЛАСНИКА", "РІШЕННЯ ПОТРІБНЕ:", "КОЛО", "ЛІМІТ", "ДИСПЕТЧЕР ПЕРЕДАЧА", "ЗВЕДЕННЯ")
ПОЧАТКИ_ЛИСТА_ДИСПЕТЧЕРОВІ = ("ГОТОВО", "ЗНАХІДКА", "ЗАБЛОКОВАНО", "ПЕРЕВІРЕНО", "ДОРОБИТИ", "КОЛО", "РІШЕННЯ", "ПРОБЛЕМА",
                              "НОВИЙ МЕНЕДЖЕР", "ЖИВИЙ ПІСЛЯ")
З_ПОВНИМ_SHA = ("ГОТОВО", "ПЕРЕВІРЕНО")
ФАЙЛИ_ПРАВИЛ = re.compile(r"(?:^|/)(?:AGENTS\.md|CLAUDE\.md|аудит/(?:ДИСПЕТЧЕР|МЕНЕДЖЕР|ВИКОНАВЕЦЬ|ПЕРЕВІРКА|ПЛАН|КАРТИНА|"
                          r"МОДЕЛІ|ПРОДУКТ|СТАН)\.md|аудит/адаптери/CLAUDE_КЕРУВАННЯ\.md)")
ФАЙЛ_РОЛІ = {"диспетчер": "ДИСПЕТЧЕР.md", "менеджер": "МЕНЕДЖЕР.md", "перевірка": "ПЕРЕВІРКА.md",
             "виконавець": "ВИКОНАВЕЦЬ.md"}
SHA = re.compile(r"\b[0-9a-f]{40}\b")
ТАЙМЕР = {"mcp__claude-code-remote__send_later", "CronCreate"}

ПРАВИЛА = OrderedDict([
    ("К1", ("місце", "кінець ходу без «—», крім відповіді на слово власника (ядро:89–91; CLAUDE.md:17)")),
    ("К2", ("місце", "текст у чаті посеред ходу, крім відповіді на слово власника (ядро:89–91)")),
    ("К3", ("місце", "лист іншій сесії через send_message, а не create_trigger+fire_trigger (CLAUDE.md:30–35)")),
    ("К4", ("контроль", "лист диспетчера менеджерові поза переліком (ДИСПЕТЧЕР.md:101–107; хук листи_менеджерові)")),
    ("К5", ("місце", "лист виконавця/перевірки диспетчерові: початок із переліку, повний SHA в ГОТОВО/ПЕРЕВІРЕНО "
                     "(ВИКОНАВЕЦЬ.md:31; ПЕРЕВІРКА.md:78)")),
    ("К6", ("місце", "коміт без пушу до кінця ходу (ядро:59)")),
    ("К7", ("місце", "злиття без expectedHeadSha з повним SHA (ДИСПЕТЧЕР.md:69; CLAUDE_КЕРУВАННЯ.md:33)")),
    ("К8", ("місце", "злиття не диспетчером (ядро:86)")),
    ("К9", ("місце", "auto-merge чи workflow_dispatch (ядро:95)")),
    ("К10", ("місце", "пуш у main (ядро:95)")),
    ("К11", ("місце", "згадка @codex поза «@codex review» (ядро:96–98)")),
    ("К12", ("місце", "create_session без /effort, моделі, source_url чи append_system_prompt (CLAUDE_КЕРУВАННЯ.md:8–10)")),
    ("К13", ("місце", "create_trigger листа зі create_new_session_on_fire чи розкладом; fire_trigger з text (CLAUDE.md:32–35)")),
    ("К14", ("місце", "таймер, не передбачений роллю; delete_trigger диспетчера (МЕНЕДЖЕР.md:61; ДИСПЕТЧЕР.md:60; "
                      "ВИКОНАВЕЦЬ.md:40; CLAUDE_КЕРУВАННЯ.md:15)")),
    ("К15", ("місце", "субагент без явної моделі (ВИКОНАВЕЦЬ.md:42; МЕНЕДЖЕР.md:70)")),
    ("К16", ("місце", "правка файлів правил не менеджером (ядро:105–108)")),
    ("К17", ("місце", "після стиснення файл ролі не перечитано до кінця ходу зі стисненням і наступного (ядро:42)")),
    ("К18", ("кандидат", "слово власника з чату не передано менеджерові / не записано в журнал (ядро:39–41)")),
    ("К19", ("кандидат", "питання власникові через AskUserQuestion не менеджером (ядро:87; ДИСПЕТЧЕР.md:72)")),
    ("К20", ("контроль", "фонове завдання Bash з циклом чекання (CLAUDE.md:15; хук фонові_завдання)")),
    ("К21", ("місце", "list_* без limit ≤ 10; list_events без kinds (CLAUDE_КЕРУВАННЯ.md:26)")),
    ("К22", ("місце", "лист менеджера «ЗЛИТИ» (з префіксом «МЕНЕДЖЕР:» чи без) без повного SHA (МЕНЕДЖЕР.md:47)")),
    ("К23", ("місце", "PR виконавця не чернетка; PR пачки перевірки — чернетка (ВИКОНАВЕЦЬ.md:3,20; ПЕРЕВІРКА.md:12–14)")),
    ("К24", ("місце", "картка довіри confirm_repository_trust у диспетчера чи менеджера (CLAUDE_КЕРУВАННЯ.md:40–46)")),
    ("К25", ("місце", "повтор виклику, який відхилив хук, дозвіл чи запобіжник (ядро:92–94)")),
    ("К26", ("місце", "Edit/Write у `джерела/` диспетчером чи менеджером (ДИСПЕТЧЕР.md:3; МЕНЕДЖЕР.md:5–9)")),
    ("К27", ("місце", "archive_session диспетчера в основному ході; події субагентів у list_events нема (ДИСПЕТЧЕР.md:116)")),
    ("К28", ("місце", "перевірка: цикл чекання (sleep/until/while) у Bash на передньому плані (ПЕРЕВІРКА.md:68–71)")),
    ("К29", ("місце", "виклик інструмента з `permissions.deny`, що виконався без відмови (CLAUDE_КЕРУВАННЯ.md:29–31)")),
])
ЗАБОРОНЕНІ = re.compile(r"^(?:Workflow|ScheduleWakeup|ShowOnboardingRolePicker|SearchPlugins|SuggestPluginInstall|SuggestSkills|"
                        r"mcp__ccd_session__.*|mcp__claude-code-remote__subscribe_pr_activity)$")
ШЛЯХ_КОДУ = re.compile(r"(?:^|/)джерела/")
РУШІЙ = "Claude"
ЗАБОРОНА_З = "2026-10-29T16:05"  # коміт 936e60c7: `subscribe_pr_activity` у deny; раніше заборони не було
ВІДМОВА = re.compile(r"hook error|elevated_session_untrusted_device|requires approval|permission to use|was denied|"
                     r"not allowed|ACCESS_DENIED", re.IGNORECASE)


def події(тека):
    бачені, дані = set(), []
    for файл in sorted(glob.glob(os.path.join(тека, "*.json"))):
        for е in json.load(open(файл, encoding="utf-8"))["data"]:
            ключ = next((v.get("uuid") for k, v in е.items() if k != "created_at" and isinstance(v, dict)), None)
            if ключ in бачені:
                continue
            бачені.add(ключ)
            дані.append(е)
    дані.sort(key=lambda е: е["created_at"])
    return дані


def розібрати(е):
    """(вид, тіло, внутрішнє) події: тіло — під ключем виду, внутрішнє — `internal_anthropic_catchall`."""
    for к, в in е.items():
        if к != "created_at" and isinstance(в, dict):
            return к, в, в.get("internal_anthropic_catchall") or {}
    return None, {}, {}


class Дія:
    __slots__ = ("правило", "роль", "час", "порушення", "зміст", "інтервал")

    def __init__(с, правило, роль, час, порушення, зміст):
        с.правило, с.роль, с.час, с.порушення, с.зміст = правило, роль, час, порушення, зміст
        с.інтервал = 0


def блоки(вн):
    повідомлення = вн.get("message")
    зміст = повідомлення.get("content") if isinstance(повідомлення, dict) else None
    return [б for б in зміст if isinstance(б, dict)] if isinstance(зміст, list) else []


def git_команди(команда, дія):
    """Уривки команди (за `&&`, `||`, `;`, рядком) з викликом `git <дія>` (перед ним можуть стояти `timeout N`, `do`,
    `-c …`); тіла `<<EOF … EOF` не беруться — у них git лише згадано."""
    без_вставок = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?\n.*?\n\1\b", "", команда, flags=re.S)
    шаблон = r"(?:^|\s|\()git\s+(?:-c\s+\S+\s+|-q\s+)*" + дія + r"\b"
    return [у for у in re.split(r"&&|\|\||;|\n", без_вставок) if re.search(шаблон, у)]


def читано_повністю(команда, файл):
    """`cat <файл>` чи `git show <гілка>:<файл>` у команді без обрізання файлу до вибірки (`grep`, `sed -n`, `head`)."""
    for у in re.split(r"&&|\|\||;|\n", команда):
        if файл in у and re.search(r"\bcat\b|\bgit\s+show\b", у) and not re.search(r"\b(?:grep|sed|awk|head)\b[^|]*" + re.escape(файл), у):
            return True
    return False


def пуш_у_main(уривок):
    """`git push` ставить у `main`, якщо призначення будь-якого refspec — `main` чи `refs/heads/main`."""
    слова = [с.strip("'\"") for с in уривок.split() if not с.startswith("-")]
    після = слова[слова.index("push") + 1:] if "push" in слова else []
    return any(с.split(":")[-1] in ("main", "refs/heads/main") for с in після[1:] if с)


def відмови_хука(список):
    """Ідентифікатори викликів, яких не пропустив хук: `tool_result` з `is_error` і «hook error» у тексті."""
    ід = set()
    for е in список:
        вид, _, вн = розібрати(е)
        if вид != "user":
            continue
        for б in блоки(вн):
            if б.get("type") == "tool_result" and б.get("is_error") and "hook error" in json.dumps(
                    б.get("content"), ensure_ascii=False):
                ід.add(б.get("tool_use_id"))
    return ід


def відхилені(список):
    """Виклики, яких не пропустив хук, дозвіл чи запобіжник: ідентифікатор → (час, інструмент, вхід)."""
    виклики, відхилено = {}, {}
    for е in список:
        вид, _, вн = розібрати(е)
        for б in блоки(вн):
            if вид == "assistant" and б.get("type") == "tool_use":
                виклики[б["id"]] = (е["created_at"], б["name"], json.dumps(б.get("input") or {}, ensure_ascii=False, sort_keys=True))
            elif вид == "user" and б.get("type") == "tool_result" and б.get("is_error") and б.get("tool_use_id") in виклики \
                    and ВІДМОВА.search(json.dumps(б.get("content"), ensure_ascii=False)):
                відхилено[б["tool_use_id"]] = виклики[б["tool_use_id"]]
    return відхилено, виклики


def коротко(текст, н=110):
    return re.sub(r"\s+", " ", str(текст))[:н]


def аналіз(роль, список, диспетчер, менеджер, від, до):
    """Дії сесії за правилами: список `Дія`; `стиснення` — часи `compact_boundary`."""
    дії, стиснення, бачені_вики = [], [], set()
    відмови = відмови_хука(список)
    відхилено, виклики = відхилені(список)
    for ід, (час, ім, вх) in відхилено.items():
        if (від and час[:len(від)] < від) or (до and час[:len(до)] >= до):
            continue
        повтор = any(ч > час and н == ім and в == вх for ч, н, в in виклики.values())
        дії.append(Дія("К25", роль, час, повтор, ім))
    ходи, хід = [], []
    диспетчери = set(диспетчер.split(","))
    ід_ролей = диспетчери | {менеджер, "@parent"}
    помилки = {б.get("tool_use_id"): bool(б.get("is_error")) for е in список for б in блоки(розібрати(е)[2])
               if б.get("type") == "tool_result"}
    for е in список:
        час = е["created_at"]
        if (від and час[:len(від)] < від) or (до and час[:len(до)] >= до):
            continue
        вид, тіло, вн = розібрати(е)
        if вид == "system" and вн.get("subtype") == "compact_boundary":
            стиснення.append(час)
        хід.append((час, вид, вн))
        if вид == "result":
            ходи.append((хід, вн))
            хід = []
    # подієві правила: інструмент → дія
    for час, вид, вн in [(х[0], х[1], х[2]) for х in sum((х for х, _ in ходи), []) + хід]:
        if вид != "assistant":
            continue
        for б in блоки(вн):
            if б.get("type") != "tool_use" or б.get("id") in бачені_вики:
                continue
            бачені_вики.add(б.get("id"))
            ім, вх = б["name"], б.get("input") or {}
            рядок = json.dumps(вх, ensure_ascii=False)
            кому, текст = вх.get("session_id", ""), (вх.get("message") or "").lstrip()
            if ім == "mcp__claude-code-remote__send_message":
                if текст.startswith("Почни"):
                    continue
                дії.append(Дія("К3", роль, час, кому not in ід_ролей, f"{кому[-8:]}: {коротко(текст, 70)}"))
                if роль == "диспетчер" and кому == менеджер:
                    дії.append(Дія("К4", роль, час, not текст.startswith(ПЕРЕЛІК_ЛИСТА_МЕНЕДЖЕРОВІ) and б["id"] not in відмови,
                                   коротко(текст, 70)))
                if роль in ("перевірка", "виконавець") and кому in диспетчери:
                    початок = next((п for п in ПОЧАТКИ_ЛИСТА_ДИСПЕТЧЕРОВІ if текст.startswith(п)), None)
                    порушення = початок is None or (початок in З_ПОВНИМ_SHA and not SHA.search(текст))
                    дії.append(Дія("К5", роль, час, порушення, коротко(текст, 90)))
            elif ім == "mcp__github__merge_pull_request":
                дії.append(Дія("К7", роль, час, not SHA.fullmatch(вх.get("expectedHeadSha") or ""), f"#{вх.get('pullNumber')}"))
                дії.append(Дія("К8", роль, час, роль != "диспетчер", f"#{вх.get('pullNumber')}"))
            elif ім in ("mcp__github__enable_pr_auto_merge", "mcp__github__actions_run_trigger"):
                дії.append(Дія("К9", роль, час, True, ім))
            elif ім == "Bash":
                команда = вх.get("command") or ""
                for уривок in git_команди(команда, "push"):
                    дії.append(Дія("К10", роль, час, пуш_у_main(уривок), коротко(уривок, 90)))
                if вх.get("run_in_background"):
                    дії.append(Дія("К20", роль, час, bool(re.search(r"\bsleep\b|\buntil\b|\bwhile\b", команда))
                                   and б["id"] not in відмови, коротко(команда, 80)))
            if ім in ("mcp__github__add_issue_comment", "mcp__github__create_pull_request", "mcp__github__update_pull_request",
                      "mcp__github__add_reply_to_pull_request_comment", "mcp__github__pull_request_review_write",
                      "mcp__github__issue_write"):
                згадки = re.findall(r"@codex\b(?!\s+review)", рядок, re.IGNORECASE)
                дії.append(Дія("К11", роль, час, bool(згадки), ім.split("__")[-1]))
            if ім == "mcp__claude-code-remote__create_session":
                проп = ("/effort" in (вх.get("prompt") or "")) and вх.get("model") and вх.get("source_url") \
                    and (вх.get("append_system_prompt") or "").strip()
                дії.append(Дія("К12", роль, час, not проп, коротко(вх.get("title") or "", 60)))
            if ім == "mcp__claude-code-remote__create_trigger":
                розклад = bool(вх.get("cron_expression") or вх.get("run_once_at"))
                пульс = "ПУЛЬС" in (вх.get("prompt") or "")[:20]
                лист = bool(вх.get("persistent_session_id")) and not (роль == "диспетчер" and пульс)
                порушення = bool(вх.get("create_new_session_on_fire")) or (лист and розклад)
                дії.append(Дія("К13", роль, час, порушення, коротко(вх.get("name") or "", 60)))
                if розклад:
                    дозволено = роль == "диспетчер" and пульс
                    дії.append(Дія("К14", роль, час, not дозволено, "розклад: " + коротко(вх.get("name") or "", 50)))
            if ім == "mcp__claude-code-remote__fire_trigger":
                дії.append(Дія("К13", роль, час, bool(вх.get("text")), "fire_trigger"))
            if ім in ТАЙМЕР:
                дії.append(Дія("К14", роль, час, True, ім))
            if ім == "mcp__claude-code-remote__delete_trigger" and роль == "диспетчер":
                дії.append(Дія("К14", роль, час, True, "delete_trigger"))
            if ім.startswith("mcp__claude-code-remote__list_"):
                ліміт = вх.get("limit")
                без_kinds = ім.endswith("list_events") and not вх.get("kinds")
                дії.append(Дія("К21", роль, час, not (isinstance(ліміт, int) and ліміт <= 10) or без_kinds,
                               ім.split("__")[-1] + f" limit={ліміт} kinds={'є' if вх.get('kinds') else 'нема'}"))
            if ім == "mcp__claude-code-remote__send_message" and роль == "менеджер" and кому in диспетчери \
                    and re.match(r"(?:МЕНЕДЖЕР:\s*)?ЗЛИТИ", текст):
                дії.append(Дія("К22", роль, час, not SHA.search(текст), коротко(текст, 90)))
            if ім == "mcp__github__create_pull_request" and (роль == "виконавець" or (роль == "перевірка" and "pachka" in (вх.get("head") or ""))):
                чернетка = вх.get("draft") is True
                дії.append(Дія("К23", роль, час, чернетка != (роль == "виконавець"), коротко(вх.get("title") or "", 70)))
            if ім == "mcp__claude-code-remote__confirm_repository_trust" and роль in ("диспетчер", "менеджер"):
                дії.append(Дія("К24", роль, час, True, ім))
            if ім == "Agent":
                дії.append(Дія("К15", роль, час, not вх.get("model"), коротко(вх.get("description") or "", 60)))
            шляхи = [вх.get("file_path") or "", вх.get("path") or ""] + [
                ф.get("path", "") for ф in (вх.get("files") or []) if isinstance(ф, dict)]
            if ім in ("Edit", "Write", "NotebookEdit", "mcp__github__create_or_update_file", "mcp__github__push_files",
                      "mcp__github__delete_file"):
                торкнуто = [ш for ш in шляхи if ФАЙЛИ_ПРАВИЛ.search(ш)]
                if торкнуто:
                    дії.append(Дія("К16", роль, час, роль != "менеджер", коротко(торкнуто[0], 80)))
            if ЗАБОРОНЕНІ.match(ім) and час >= ЗАБОРОНА_З:
                дії.append(Дія("К29", роль, час, not помилки.get(б["id"], True), ім))
            if ім in ("Edit", "Write", "NotebookEdit", "mcp__github__create_or_update_file", "mcp__github__push_files",
                      "mcp__github__delete_file") and роль in ("диспетчер", "менеджер"):
                код = [ш for ш in шляхи if ШЛЯХ_КОДУ.search(ш)]
                if код:
                    дії.append(Дія("К26", роль, час, True, коротко(код[0], 80)))
            if ім == "mcp__claude-code-remote__archive_session" and роль == "диспетчер":
                дії.append(Дія("К27", роль, час, True, кому[-8:]))
            if ім == "Bash" and роль == "перевірка" and not вх.get("run_in_background"):
                дії.append(Дія("К28", роль, час, bool(re.search(r"\bsleep\b|\buntil\b|\bwhile\b", вх.get("command") or "")),
                               коротко(вх.get("command") or "", 80)))
            if ім == "AskUserQuestion":
                дії.append(Дія("К19", роль, час, роль != "менеджер", коротко(рядок, 80)))
    # ходові правила
    for подіїх, результат in ходи:
        час_кінця = подіїх[-1][0]
        походження = ((результат.get("origin") or {}).get("kind"))
        від_людини = походження == "human"
        текст = (результат.get("result") or "").strip()
        if результат.get("num_turns") != 0:
            дії.append(Дія("К1", роль, час_кінця, not від_людини and текст != "—" and текст != "", f"[{походження}] " + коротко(текст, 70)))
        помічники = [(ч, в) for ч, в, вн in подіїх if в == "assistant"]
        останній_ас = помічники[-1][0] if помічники else None
        for час, вид, вн in подіїх:
            if вид != "assistant" or час == останній_ас:
                continue
            for б in блоки(вн):
                if б.get("type") == "text" and (б.get("text") or "").strip() not in ("", "—"):
                    дії.append(Дія("К2", роль, час, not від_людини, f"[{походження}] " + коротко(б["text"], 70)))
        ві = [(ч, вн) for ч, в, вн in подіїх if в == "user" and isinstance(((вн.get("message") or {}).get("content")), str)
              and вн.get("client_platform") not in ЛЮДИНА_ВІДСУТНЯ
              and not ((вн.get("message") or {}).get("content") or "").startswith("/")]
        сліди = [json.dumps((б.get("input") or {}), ensure_ascii=False) + б["name"] for ч, в, вн in подіїх if в == "assistant"
                 for б in блоки(вн) if б.get("type") == "tool_use"]
        for час, вн in ві:
            слово = коротко(вн["message"]["content"], 70)
            if роль == "менеджер":
                передано = any("РІШЕННЯ_ВЛАСНИКА" in с for с in сліди)
            else:
                передано = any("СЛОВО ВЛАСНИКА" in с and менеджер in с for с in сліди)
            дії.append(Дія("К18", роль, час, not передано, слово))
        коміти = [(ч, б["input"].get("command") or "") for ч, в, вн in подіїх if в == "assistant" for б in блоки(вн)
                  if б.get("type") == "tool_use" and б["name"] == "Bash"]
        for ч, к in коміти:
            for коміт in git_команди(к, "commit"):
                пушено = any(git_команди(к2, "push") for ч2, к2 in коміти if ч2 >= ч)
                дії.append(Дія("К6", роль, ч, not пушено, коротко(коміт, 80)))
    # після стиснення — файл ролі
    файл = ФАЙЛ_РОЛІ.get(роль)
    for ч0 in стиснення:
        після, кінців = [], 0
        for е in список:
            if е["created_at"] <= ч0:
                continue
            вид, _, вн = розібрати(е)
            після.append((е["created_at"], вид, вн))
            кінців += вид == "result"
            if кінців == 2:
                break
        читано = False
        for ч, в, вн in після:
            if в != "assistant" or not файл:
                continue
            for б in блоки(вн):
                if б.get("type") != "tool_use":
                    continue
                вх = б.get("input") or {}
                if б["name"] == "Read" and файл in (вх.get("file_path") or "") and not (вх.get("limit") or вх.get("offset")):
                    читано = True
                if б["name"] == "Bash" and читано_повністю(вх.get("command") or "", файл):
                    читано = True
        дії.append(Дія("К17", роль, ч0, not читано, "compact_boundary"))
    for д in дії:
        д.інтервал = int(any(д.час >= ч0 for ч0 in стиснення))
    return дії, стиснення


def зведення(усі):
    рядки, всього_д, всього_п = [], 0, 0
    ключі = sorted({(д.правило, д.роль) for д in усі}, key=lambda к: (int(к[0][1:]), к[1]))
    for правило, роль in ключі:
        групa = [д for д in усі if д.правило == правило and д.роль == роль]
        п = sum(д.порушення for д in групa)
        найбільший = max(д.інтервал for д in групa)
        інтервали = " ".join(
            f"{к}:{sum(д.порушення for д in групa if д.інтервал == к)}/{sum(д.інтервал == к for д in групa)}"
            for к in range(найбільший + 1))
        вид = ПРАВИЛА[правило][0]
        if вид == "місце":
            всього_д += len(групa)
            всього_п += п
        рядки.append((правило, вид, роль, len(групa), п,
                      інтервали))
    return рядки, всього_д, всього_п


def зразок(усі, н):
    вивід = []
    for назва, умова in (("з порушенням", True), ("без порушення", False)):
        відібрані = sorted((д for д in усі if ПРАВИЛА[д.правило][0] == "місце" and д.порушення is умова),
                           key=lambda д: д.час)
        крок = max(1, len(відібрані) // max(1, н))
        вивід.append(f"-- зразок {назва}: {min(н, len(відібрані))} з {len(відібрані)}")
        for д in відібрані[::крок][:н]:
            вивід.append(f"{д.час[:19]} {д.правило} {д.роль} · {д.зміст}")
    return вивід


ФАЙЛИ_ПЕРЕЛІКУ = {"AGENTS.md": "AGENTS.md", "CLAUDE.md": "CLAUDE.md", "CLAUDE_КЕРУВАННЯ.md": "аудит/адаптери/CLAUDE_КЕРУВАННЯ.md",
                  "ДИСПЕТЧЕР.md": "аудит/ДИСПЕТЧЕР.md", "МЕНЕДЖЕР.md": "аудит/МЕНЕДЖЕР.md",
                  "ВИКОНАВЕЦЬ.md": "аудит/ВИКОНАВЕЦЬ.md", "ПЕРЕВІРКА.md": "аудит/ПЕРЕВІРКА.md",
                  "НОУТБУК.md": "аудит/НОУТБУК.md", "CHATGPT.md": "аудит/CHATGPT.md", "GEMINI.md": "GEMINI.md",
                  "ЧЕРГА.md": "аудит/адаптери/gemini/ЧЕРГА.md"}
АДРЕСА = re.compile(r"^([\w.]+\.md):(\d+)(?:[–-](\d+))?$")


def таблиці_переліку(шлях):
    """(правила, не_правила, проби): правила — списки з 7 клітинок; не_правила — (адреса, причина); проби — код → команда."""
    правила, не_правила, проби, розділ = [], [], {}, ""
    for рядок in open(шлях, encoding="utf-8"):
        if рядок.startswith("## "):
            розділ = рядок.strip()
        клітинки = [к.strip() for к in рядок.strip().strip("|").replace("\\|", "\u0001").split("|")]
        клітинки = [к.replace("\u0001", "|") for к in клітинки]
        if not рядок.startswith("|") or not клітинки:
            continue
        if розділ == "## Правила" and len(клітинки) == 7 and АДРЕСА.match(клітинки[0]):
            правила.append(клітинки)
        elif розділ == "## Не правило" and len(клітинки) == 2 and АДРЕСА.match(клітинки[0]):
            не_правила.append(tuple(клітинки))
        elif розділ == "## Проби механізмів" and len(клітинки) == 3 and re.match(r"П\d+$", клітинки[0]):
            проби[клітинки[0]] = клітинки[1].strip("`")
    return правила, не_правила, проби


def місце_рядка(к):
    """Правило — місце, коли в мить дії його тримає (хоч частково) пам'ять або механізм без проби."""
    return "пам'ять" in к[4] or к[5].strip() == "нема"


def проби_рядка(к):
    return re.findall(r"П\d+", к[5])


def місць_у_переліку(шлях, незбіг=()):
    """Місця переліку; рядок з пробою, що не тримає (`незбіг` — коди проб), теж місце: механізм без підтвердження."""
    правила, _, _ = таблиці_переліку(шлях)
    return sum(місце_рядка(к) or any(п in незбіг for п in проби_рядка(к)) for к in правила), len(правила)


def ролі_рядка(к):
    """Ролі, чиї дії стосуються рядка переліку (стовпець «роль · рушій»): `усі`, `усі, крім X`, чи перелік."""
    ролі = ("диспетчер", "менеджер", "перевірка", "виконавець", "ноутбук")
    назви = к[3].split(" · ")[0]
    if назви.startswith("усі"):
        крім = назви.split("крім", 1)[1] if "крім" in назви else ""
        return {р for р in ролі if р not in крім}
    return {р for р in ролі if р in назви}


def покриття(шлях, корінь):
    """Речення файлів правил: (усього, покрито, [непокриті адреси]). Речення покрите, коли його рядок у діапазоні рядка
    таблиці «Правила» чи «Не правило»."""
    правила, не_правила, _ = таблиці_переліку(шлях)
    діапазони = {}
    for адреса in [к[0] for к in правила] + [к[0] for к in не_правила]:
        м = АДРЕСА.match(адреса)
        діапазони.setdefault(м.group(1), set()).update(range(int(м.group(2)), int(м.group(3) or м.group(2)) + 1))
    усього = покрито = 0
    нема = []
    for коротко_ім, відносний in ФАЙЛИ_ПЕРЕЛІКУ.items():
        for н, рядок in enumerate(open(os.path.join(корінь, відносний), encoding="utf-8"), 1):
            for речення in re.split(r"(?<=[.!?])\s+", рядок.strip()):
                if not re.search(r"\w", речення):
                    continue
                усього += 1
                if н in діапазони.get(коротко_ім, ()):
                    покрито += 1
                else:
                    нема.append(f"{коротко_ім}:{н}")
    return усього, покрито, sorted(set(нема), key=lambda а: (а.split(":")[0], int(а.split(":")[1])))


def проби_конфігу(корінь):
    """Проба П6: `.claude/settings.json` забороняє всі інструменти з ЗАБОРОНЕНІ й підключає хуки з наявними файлами."""
    налаштування = json.load(open(os.path.join(корінь, ".claude/settings.json"), encoding="utf-8"))
    заборони = налаштування.get("permissions", {}).get("deny", [])
    нема = [н for н in ("Workflow", "ScheduleWakeup", "ShowOnboardingRolePicker", "SearchPlugins", "SuggestPluginInstall",
                        "SuggestSkills", "mcp__ccd_session__x", "mcp__claude-code-remote__subscribe_pr_activity")
            if not any(ЗАБОРОНЕНІ.match(н) and (з == н or (з.endswith("*") and н.startswith(з[:-1]))) for з in заборони)]
    хуки = re.findall(r"\.claude/хуки/[\w.]+", json.dumps(налаштування, ensure_ascii=False))
    без_файлу = [х for х in хуки if not os.path.exists(os.path.join(корінь, х))]
    for н in нема:
        print(f"П6: не заборонено: {н}")
    for х in без_файлу:
        print(f"П6: хука нема: {х}")
    print(f"П6: заборон {len(заборони)}, хуків {len(хуки)}")
    return not нема and not без_файлу and bool(хуки)


def запустити_проби(проби, корінь):
    """Кожна проба — окремий процес з кореня репозиторію; тримає, коли код виходу 0."""
    результат = {}
    for код, команда in проби.items():
        if "запустити_стенд.sh" in команда and not shutil.which("pwsh"):
            результат[код] = True
            print(f"проба {код}: тут не ганяється (нема pwsh); тримає CI `obhortka` (Windows) · {команда}")
            continue
        п = subprocess.run(команда, shell=True, cwd=корінь, capture_output=True, text=True, timeout=900)
        результат[код] = п.returncode == 0
        print(f"проба {код}: {'тримає' if п.returncode == 0 else 'НЕ ТРИМАЄ'} · {команда}")
    return результат


def відбиток(усі_теки):
    """Короткий відбиток входу: сесія → подій і sha256 їхніх `uuid` (для звірки повторного запуску)."""
    рядки = []
    for роль, тека in усі_теки:
        ід = sorted(next((v.get("uuid") for k, v in е.items() if k != "created_at" and isinstance(v, dict)), "")
                    for е in події(тека))
        рядки.append(f"# вхід {роль} {os.path.basename(тека.rstrip('/'))[-8:]}: подій {len(ід)}, "
                     f"{hashlib.sha256(chr(10).join(ід).encode()).hexdigest()[:12]}")
    return рядки


def головна(арг=None):
    п = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    п.add_argument("--перелік", help="перелік правил (без --сесія — режим храповика: покриття й число місць)")
    п.add_argument("--сесія", action="append", default=[], help="роль=тека (диспетчер|менеджер|перевірка|виконавець)")
    п.add_argument("--диспетчер", default="")
    п.add_argument("--менеджер", default="")
    п.add_argument("--дії", default="", help="друкує всі дії правил через кому, напр. К1,К21")
    п.add_argument("--від", default="")
    п.add_argument("--до", default="")
    п.add_argument("--зразок", type=int, default=0)
    п.add_argument("--json", action="store_true")
    п.add_argument("--проби", action="store_true", help="запускає проби механізмів із переліку")
    п.add_argument("--проби-конфігу", action="store_true", help="проба П6: заборони й хуки в .claude/settings.json")
    а = п.parse_args(арг)
    корінь = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    if а.проби_конфігу:
        return 0 if проби_конфігу(корінь) else 1
    if а.перелік and not а.сесія:
        правила, не_правила, проби = таблиці_переліку(а.перелік)
        незбіг = set()
        if а.проби:
            незбіг = {к for к, добре in запустити_проби(проби, корінь).items() if not добре}
        if not проби_конфігу(корінь):
            незбіг.add("П6")
        місць, усього = місць_у_переліку(а.перелік, незбіг)
        речень, покрито, нема = покриття(а.перелік, корінь)
        print(f"правил у переліку: {усього}; не правил (рядків): {len(не_правила)}; проб механізмів: {len(проби)}")
        print(f"місць у переліку (пам'ять або механізм без проби): {місць}")
        print(f"речень {речень}, покрито {покрито}, непокрито {len(нема)}")
        for адреса in нема[:40]:
            print(f"вада приладу: непокрите речення {адреса}")
        print(f"проб, що не тримають: {len(незбіг)} {sorted(незбіг)}")
        print(f"місць: {місць + len(нема)}")
        return 0
    if not (а.сесія and а.диспетчер and а.менеджер):
        п.error("потрібні --сесія, --диспетчер, --менеджер (чи --перелік)")
    усі, по_сесіях = [], []
    for запис in а.сесія:
        роль, тека = запис.split("=", 1)
        список = події(тека)
        дії, стиснення = аналіз(роль, список, а.диспетчер, а.менеджер, а.від, а.до)
        усі += дії
        вікно = [е["created_at"] for е in список if (not а.від or е["created_at"][:len(а.від)] >= а.від)
                 and (not а.до or е["created_at"][:len(а.до)] < а.до)]
        по_сесіях.append((роль, os.path.basename(тека.rstrip("/"))[-8:], len(вікно), стиснення))
    рядки, всього_д, всього_п = зведення(усі)
    if а.json:
        print(json.dumps([list(р) for р in рядки] + [["підсумок", всього_п, всього_д]], ensure_ascii=False))
        return 0
    for рядок in відбиток([з.split("=", 1) for з in а.сесія]):
        print(рядок)
    print("-- сесії: роль · сесія · подій у вікні · стиснення (час UTC)")
    for роль, ід, н, ст in по_сесіях:
        print(f"{роль} · {ід} · {н} · " + (", ".join(ч[5:16] for ч in ст) or "нема"))
    print(f"-- правило · вид · роль · рушій · дій · порушень · до/після першого стиснення своєї сесії (порушень/дій)")
    for р in рядки:
        print(" · ".join(str(х) for х in (р[0], р[1], р[2], РУШІЙ) + р[3:]))
    if а.перелік:
        підсумок = {}
        for д in усі:
            д_, п_ = підсумок.get((д.правило, д.роль), (0, 0))
            підсумок[(д.правило, д.роль)] = (д_ + 1, п_ + д.порушення)
        print("-- за правилами переліку: адреса · слід · порушень/дій (код ділять кілька рядків — не складати)")
        for к in таблиці_переліку(а.перелік)[0]:
            коди = re.findall(r"К\d+", к[6])
            if коди:
                ролі = ролі_рядка(к)
                def за(c):
                    дп = [підсумок.get((c, р), (0, 0)) for р in ролі]
                    return f"{c} {sum(х[1] for х in дп)}/{sum(х[0] for х in дп)}"
                print(f"{к[0]} · {к[6]} · ролі {','.join(sorted(ролі)) or '-'} · " + "; ".join(за(c) for c in коди))
            else:
                print(f"{к[0]} · {к[6]} · не виміряно: слід не події сесій Claude ({к[6]})")
    for код in filter(None, а.дії.split(",")):
        print(f"-- дії {код}")
        for д in sorted((д for д in усі if д.правило == код), key=lambda д: д.час):
            print(f"{д.час[:19]} {д.роль} {'ПОРУШЕННЯ' if д.порушення else 'ні'} · {д.зміст}")
    if а.зразок:
        print("\n".join(зразок(усі, а.зразок)))
    print(f"порушень: {всього_п} з {всього_д}")
    return 0


if __name__ == "__main__":
    sys.exit(головна())
