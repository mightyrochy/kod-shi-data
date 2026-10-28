"""Незалежне відтворення обриву JSONL на точній голові PR #2042, без мережі."""
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "zhnyvarka"))
sys.path.insert(0, str(root / "джерела" / "проби"))
import обхід
from каталог_зависла_крамниця_json_проба import прогін, порція, РІЧ

with tempfile.TemporaryDirectory(prefix="review-2042-utf8-") as tmp:
    raw = Path(tmp) / "сирі"
    raw.mkdir()
    (raw / "hang.com.jsonl").write_bytes(b'{"url":"https://hang.com/p1","note":"\xd0')
    launches = []
    def launch(*args):
        launches.extend(args[1])
        raise AssertionError("неочікуваний запуск")
    try:
        with patch.object(обхід, "запустити_крамниці", launch):
            обхід.main(["--журнал", tmp, "--магазини", "hang.com,ok.com", "--циклів", "1"])
    except UnicodeDecodeError as exc:
        print(f"UTF8: {type(exc).__name__}; запуски={launches}; стан_записано={(Path(tmp)/'обхід_стан.tsv').exists()}")
    else:
        raise AssertionError("падіння на UTF-8 не відтворено")

for family in ("woo", "shopify"):
    with tempfile.TemporaryDirectory(prefix="review-2042-jsonl-") as tmp:
        raw = Path(tmp) / "сирі"
        raw.mkdir()
        file = raw / "json.test.jsonl"
        file.write_text('{"url":', encoding="utf-8")
        state, requests = прогін(tmp, family, [порція(family, [РІЧ]), порція(family, [])])
        cards = []
        bad = 0
        for line in file.read_text(encoding="utf-8").splitlines():
            try:
                cards.append(json.loads(line))
            except json.JSONDecodeError:
                bad += 1
        _, retry = прогін(tmp, family, [порція(family, [РІЧ]), порція(family, [])])
        print(f"JSONL/{family}: запити={requests}; стан={state['стан_код']}; готово={state['готово']}; лишилось={state['лишилось']}; читабельних_карток={len(cards)}; хибних_рядків={bad}; повторних_запитів={retry}")
        assert requests == 2 and state["стан_код"] == "CATALOG" and state["лишилось"] == "0"
        assert len(cards) == 0 and bad == 1 and retry == 0
