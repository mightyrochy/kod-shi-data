# Інструменти керування Claude

Довідка під конкретну дію менеджера, диспетчера, перевірки, сторожа або запускача; не стартовий пакет виконавця.
Хто має право виконати дію й коли — у договорі ролі. Відмова запобіжника — за `AGENTS.md`.

## Створення й продовження

- Хмара: `create_session(source_url="https://github.com/mightyrochy/kod-shi-data", model=<модель>, title=<назва>,
  prompt="/effort <рівень>", append_system_prompt=<роль, файл наряду й адресати>)`, потім `send_message("Почни")`.
  `/effort` діє першим ходом. Наряд, його розширення (дозвіл, зняття кроку) — в системному нової сесії:
  Sonnet не виконує нового наряду з листа, класифікатор відхиляє розширення. Листом — доповнення до того самого PR.
- Диспетчер: модель і `/effort` — рядок «диспетчер» `аудит/МОДЕЛІ.md` (ідентифікатори — там само), системне —
  `аудит/ДИСПЕТЧЕР.md` і гілка передачі; створює менеджер.
- Пульс диспетчера: `create_trigger(persistent_session_id=<id>, cron_expression="0 * * * *",
  prompt="ПУЛЬС: такт за аудит/ДИСПЕТЧЕР.md")`; старий — вимкнути, не `delete_trigger`: той видаляє й сесії своїх
  прогонів, а прогони пульсу записані на сесію диспетчера. Перевірка — `get_trigger`, `last_run`; вимкнути чи
  ввімкнути — `update_trigger(trigger_id=<id>, enabled=<false|true>)`.
- Глибина родоводу: на 8 `create_trigger` відмовляє (менеджер → диспетчер +1 → сесії +2). Наступника менеджера до
  глибини 4 включно створює менеджер; з 5 — власник вручну в claude.ai/code, середовище `lyusterko`, Opus 5.5:
  `/effort max`; `get_session` без id; старому менеджерові `send_message("Новий менеджер: <id>")`; чекати «Почни»
  з № PR передачі. Стиснення — `CLAUDE.md`, «Контекст».

## Події й стан

- Стан сесії: `get_session(<id>)` того самого ходу, час UTC.
  `list_*` — фільтри й `limit` ≤ 10, `list_events` — `kinds`; не тягти весь список у контекст.
- Недоставлені листи: `list_triggers(recurring=false, include_completed=true, limit=6)`, звірити `last_run`.
  Прямий патч між сесіями — `send_message`, доставка — `updated_at`; звичайний лист — `CLAUDE.md`, «Лист».
- Нагляд PR — `subscribe_pr_activity`; правки коментарів не сповіщають — їх бачить пульс. Останній коментар —
  `get_comments(perPage=1, page=<кількість>)`. Архів/повернення — `archive_session` / `unarchive_session`.
- Голова PR: `git fetch origin pull/N/head`; відмовлено — `pull_request_read(method="get_status")`.
  Чернетка перед дозволеним злиттям — `update_pull_request(draft=false)`, інакше 405; злиття — з `expectedHeadSha`.
  Застарілий прогін — `cancel_workflow_run`. Стан доступу, наприклад 403 пушу, — з фактичної відповіді GitHub.

## Ноутбук

- Міст DESKTOP-6N11SA4 шукається через `list_environments` лише вперше чи після відмови запуску. `create_session`
  з його `environment_id`, моделлю, `/effort` і дослівним нарядом; потім `send_message("Почни")`.
- `elevated_session_untrusted_device` — дозволений власником запасний шлях запускача на самому ноутбуці:
  `Agent(subagent_type="general-purpose", model=<haiku|sonnet|opus>, effort=<рівень>, run_in_background=true,
  description=<назва>, prompt=<наряд>)`. Цей виняток не надає хмарній сесії права відкривати віддалений доступ.
- Пробудження запускача — `send_later` за його договором (працює, 23.10). Інструмент листа для ноутбучної
  сесії — ToolSearch `send_message`.
- Картка довіри «комп'ютери й інші сесії» (`confirm_repository_trust`) відкриває хмарній сесії ноутбук, але глушить
  її саму: тригери (пульс, нагадування, листи) — `ROUTINE_RUN_FAILURE_REASON_ACCESS_DENIED`, `send_message` інших
  сесій — `elevated_session_untrusted_device`; доходять лише чат власника й події PR за підпискою (ДИСПЕТЧЕР-7,
  23.10). Менеджер і диспетчер її не просять; роботу ноутбукові — «Черга ноутбука» `аудит/СТАН.md`.
