"""7533: файлові входи мають локальну декларацію, не whitelist сканера."""
from фото_тип_синтетика import *
import ast
from unittest.mock import patch
import audit_contracts as А


if __name__ == "__main__":
    module = "фото_тип_контракт"
    source = Path(Ф.__file__).read_text(encoding="utf-8")
    declared, blocks = А._декларація(ast.parse(source))
    expected = {"bytes_sha256", "contract_record", "dataset_revision", "dataset_sha256", "evidence_commit", "reviewer", "source_image_sha256", "source_kind", "verification", "verified_capture_ids"}
    assert declared == expected and set(Ф.ЗОВНІШНІ_ВХОДИ) == expected
    lines = source.splitlines(keepends=True)
    for first, last in blocks:
        lines[first - 1:last] = ["\n"] * (last - first + 1)
    bare, loader = "".join(lines), А._джерело
    counts, remaining = [], []
    for text in (bare, source):
        А._ОГОЛОШЕНІ.clear()
        with patch.object(А, "_джерело", lambda name: text if name == module else loader(name)):
            orphan, _, _, _, _ = А.поля()
        actual = {key for key, readers in orphan.items() if module in readers}
        counts.append(len(actual & expected))
        remaining.append(actual - expected)
        assert actual & expected == (expected if text == bare else set())
    assert remaining[0] == remaining[1]
    print("SYNTHETIC_ONLY boundary:", counts, "(10→0); other fields unchanged:", sorted(remaining[1]), "; PASS")
