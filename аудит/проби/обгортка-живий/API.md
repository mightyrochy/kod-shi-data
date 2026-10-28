# Перевірка HTTP перед зміною проксі

2026-10-27 UTC, користувач `desktop-6n11sa4\gemini`, сервер `127.0.0.1:1234`, API **v1**.
`GET /lmstudio-greeting` повернув `{"lmstudio":true}`; номера версії застосунку відповідь не містить.
Процес сервера — `LM Studio`, PID 14132; ОС не повернула його шлях та командний рядок цьому користувачеві.

ДО: `GET /api/v1/models` — HTTP 200, усі `loaded_instances` порожні.
Проба `POST /api/v1/models/load`:

```json
{"model":"qwen/qwen3.5-9b","context_length":57344,"parallel":1,"echo_load_config":true}
```

ПІСЛЯ: HTTP 200, `status=loaded`, `instance_id=qwen/qwen3.5-9b`,
`load_config.context_length=57344`, `load_config.parallel=1`, час 10.673 с.
Окремий `GET /api/v1/models` підтвердив ті самі параметри екземпляра.
`POST /api/v1/models/unload` з `{"instance_id":"qwen/qwen3.5-9b"}` — HTTP 200.
Сирі запити та відповіді збережено у файлах `завантаження-qwen.json`,
`моделі-після-завантаження.json`, `вивантаження-qwen.json`.

Первинні довідки: [завантаження](https://lmstudio.ai/docs/developer/rest/load),
[перелік](https://lmstudio.ai/docs/developer/rest/list),
[вивантаження](https://lmstudio.ai/docs/developer/rest/unload).
Поле `parallel` установлено та перевірено на живому сервері.

Проксі вмикає цей шлях через `LMS_MODE=http`. `CTX` лишається джерелом контексту;
перед передаванням запиту проксі перевіряє фактичний контекст і `parallel=1`.
Чужий екземпляр спричиняє 503 без завантаження або вивантаження моделей.
Вивантажуються лише instance_id, які повернув власний POST load.
Без `LMS_MODE=http` збережено виклики `lms` з попередніми аргументами.

Встановлення: переносний Node v24.22.1 (LTS), Playwright 1.64.1,
Chromium 156.0.8078.4 — шляхи в `середовище.json`. Для npm використано
`NODE_USE_SYSTEM_CA=1`; перевірка TLS ввімкнена. Системних змінних не змінено.
Для збірки додатково потрібен CPython 3.12.1:
`C:\Users\gemini\tools\python-3.12.1\python.exe`, офіційний embeddable zip,
чинний Authenticode-підпис Python Software Foundation.

Команда збірки з кореня: `python джерела/build_артефакт.py джерела C:\Users\gemini\kod-shi-stand-live\index.html показ-повний`.
Змінні лише процесу: `LYUSTERKO_PYC_PYTHON=C:\Users\gemini\tools\python-3.12.1\python.exe`,
`LYUSTERKO_CATALOG=повний`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`;
на початку `PATH` — тека переносного Node.
Ізольований CPython ігнорує ці змінні. Тому лише у власній переносній інсталяції
`python312._pth` увімкнено `import site`, а `sitecustomize.py` містить:

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
```

`python.exe -I -c "import sys; print(sys.stdout.encoding); print('Україна')"`
повертає `utf-8` і `Україна`. Системний Python не змінено.
Спроба `PYTHONUTF8=0` дала збірку з пошкодженими кириличними ключами довідника:
цей артефакт відкинуто; журнал `збірка-3.txt`, `тест-показу.txt`.
Причина несумісності стандартного запуску — рядок 10229 дошки.
