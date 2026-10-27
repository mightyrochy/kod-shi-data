"""Друкує завершення здорових крамниць після синхронного зависання першої, також при повторі."""
import csv, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import обхід


def main():
    """Міряє чергу довшу за паралельність, з завислою крамницею на початку й у кінці."""
    помилки = []
    for паралельно, порядок in ((1, "hang.com,ok.com,ok2.com"), (2, "hang.com,ok.com,ok2.com"),
                                (1, "ok.com,ok2.com,hang.com,ok.com,,")):
        with tempfile.TemporaryDirectory(prefix="обхід-черговість-") as ж:
            for повтор in (1, 2):
                початок = time.monotonic()
                обхід.main(["--журнал", ж, "--магазини", порядок, "--секунд-на-магазин", "1",
                            "--секунд-на-цикл", "3", "--циклів", "2", "--паралельно", str(паралельно),
                            "--заглушка", "синхронний_блок"])
                with open(Path(ж) / "обхід_стан.tsv", encoding="utf-8") as ф:
                    стани = {р["домен"]: р for р in csv.DictReader(ф, delimiter="\t")}
                здорові = sum(стани[д]["стан_код"] == "CATALOG" for д in ("ok.com", "ok2.com"))
                зависла = стани["hang.com"]
                print(f"паралельно={паралельно}, {порядок}, повтор={повтор}: CATALOG={здорові}/2, "
                      f"hang={зависла['стан_код']}/{зависла['причина_код']}, секунд={time.monotonic() - початок:.2f}")
                помилки.append(здорові != 2 or зависла["стан_код"] != "WAIT" or зависла["причина_код"] != "TIMEOUT")
    return int(any(помилки))


if __name__ == "__main__":
    sys.exit(main())
