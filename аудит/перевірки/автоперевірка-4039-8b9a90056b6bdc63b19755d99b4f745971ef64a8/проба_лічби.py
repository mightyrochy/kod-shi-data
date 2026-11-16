"""Зіставляє число проби з фактичним видимим текстом карток екскурсії."""
import json
from pathlib import Path
import sys

тека = Path(sys.argv[1])
рядки = (тека / "повтор-після.jsonl").read_text(encoding="utf-8-sig").splitlines()
лічба = next(р for р in map(json.loads, рядки) if р["сцена"] == "ж1_екскурсія_бруківка")
видимий = (тека / "ж1_екскурсія_бруківка-картки.txt").read_text(encoding="utf-8")
print(json.dumps(dict(проба=лічба["градусів_у_картці"],
                     фраз_плюс_12_градусів_у_видимому_тексті=видимий.count("+12 градусів")), ensure_ascii=False))
