#!/usr/bin/env python3
"""Проба наряду Річ-ознаки-обличчя-очі-називає-модель (не код продукту): що модель зору продукту каже про очі
шести портретів набору `аудит/проби/набір-фото-жінок/`.

Промпт — той, що на дереві (`міст_вхід.промпт_кольору()`, як збирач кладе в показ), фото — перед промптом, як
`модельРукиП`. Модель — `claude -p` за підпискою сесії (стенд хмари, `ZHYVA=sonnet`: claude-sonnet-5-5), без ключів
API. Сирі відповіді — `<тека>/<прохід>/<ж>.txt`, журнал — `<тека>/журнал.jsonl`.
Запуск (з кореня репозиторію): python3 аудит/проби/очі-називає-модель/виклик.py <тека> <прохід> [<прохід>…]"""
import base64, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
import міст_вхід  # noqa: E402

НАБІР = КОРІНЬ / "аудит/проби/набір-фото-жінок"
ЖІНКИ = ("ж1", "ж2", "ж3", "ж4", "ж7", "ж8")
МОДЕЛЬ = os.environ.get("CLAUDE_MODEL") or "claude-sonnet-5-5"
БІН = os.environ.get("ZHYVA_BIN") or "/opt/node22/bin/claude"
СИСТЕМНИЙ = ("You are the model behind a mobile styling app. The user message is the application prompt, "
             "verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code "
             "fence when it asks for JSON, plain prose when it asks for prose. No preamble, no commentary, "
             "no tools, no questions back.")   # той самий, що `живий-як-людина-3/стенд/міст_claude.py`


def виклик(тека, прохід, ж):
    дані = base64.b64encode((НАБІР / f"{ж}-портрет.jpg").read_bytes()).decode()
    блоки = [{"type": "text", "text": "photo_of_her:"},
             {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": дані}},
             {"type": "text", "text": міст_вхід.промпт_кольору()}]
    рядок = json.dumps({"type": "user", "message": {"role": "user", "content": блоки}}) + "\n"
    т0 = time.time()
    р = subprocess.run([БІН, "-p", "--model", МОДЕЛЬ, "--tools", "", "--strict-mcp-config",
                        "--no-session-persistence", "--input-format", "stream-json", "--output-format",
                        "stream-json", "--verbose", "--system-prompt", СИСТЕМНИЙ],
                       input=рядок, capture_output=True, text=True, timeout=600, cwd="/tmp",
                       env=dict(os.environ, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"))
    ітог = None
    for л in р.stdout.splitlines():
        try:
            о = json.loads(л)
        except ValueError:
            continue
        if о.get("type") == "result":
            ітог = о
    текст = (ітог or {}).get("result") or ""
    шлях = Path(тека) / прохід / f"{ж}.txt"
    шлях.parent.mkdir(parents=True, exist_ok=True)
    шлях.write_text(текст, encoding="utf-8")
    return dict(прохід=прохід, ж=ж, с=round(time.time() - т0, 1), модель=list((ітог or {}).get("modelUsage") or {}),
                помилка=None if ітог and not ітог.get("is_error") else (р.stderr or р.stdout)[-300:],
                симв=len(текст))


if __name__ == "__main__":
    тека, проходи = sys.argv[1], sys.argv[2:]
    with ThreadPoolExecutor(12) as пул:
        записи = list(пул.map(lambda а: виклик(тека, *а), [(п, ж) for п in проходи for ж in ЖІНКИ]))
    with open(Path(тека) / "журнал.jsonl", "a", encoding="utf-8") as ф:
        for з in записи:
            ф.write(json.dumps(з, ensure_ascii=False) + "\n")
            print(json.dumps(з, ensure_ascii=False))
