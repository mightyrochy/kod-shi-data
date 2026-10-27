# -*- coding: utf-8 -*-
"""5.3-Б: таймаут без нового зведення не понижує CATALOG і не губить невідому чергу."""
import csv, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід  # noqa: E402

with tempfile.TemporaryDirectory(prefix="обхід-стан-") as ж:
    шлях = Path(ж) / "обхід_стан.tsv"
    with open(шлях, "w", encoding="utf-8", newline="") as ф:
        п = csv.DictWriter(ф, обхід.ШАПКА, delimiter="\t"); п.writeheader()
        п.writerow(dict(домен="hang.com", стан_код="CATALOG", причина_код="", адрес=4,
                        готово=2, лишилось=2, цикл=1, підстава="картки збережено"))
    обхід.main(["--журнал", ж, "--магазини", "hang.com", "--секунд-на-магазин", "9",
                "--секунд-на-цикл", "1", "--циклів", "1", "--заглушка", "синхронний_блок"])
    р = next(csv.DictReader(open(шлях, encoding="utf-8"), delimiter="\t"))
    assert р["стан_код"] == "CATALOG" and р["лишилось"] == "2"
    print("5.3-Б ПІСЛЯ: CATALOG з картками не понижено; без черги лишилось=2")
