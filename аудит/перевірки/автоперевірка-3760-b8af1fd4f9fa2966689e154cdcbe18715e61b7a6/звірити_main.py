"""Звіряє колонку ДО авторської таблиці з модулем surface зі свіжого main.

Аргументи: дерево PR з таблицею, перевимір.json.gz зафіксованих даних.
"""
import csv, gzip, json, pathlib, sys
sys.stdout.reconfigure(encoding="utf-8")
корінь = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(корінь / "джерела"))
import surface as П


def main():
    """Рахує поточним main усі записані Lab/U й порівнює кожен код, не лише суму."""
    таблиця = pathlib.Path(sys.argv[1]) / "аудит/проби/річ_колір_один_колір_1411/сукупність.tsv"
    дані = json.load(gzip.open(sys.argv[2]))
    рядки = list(csv.DictReader(таблиця.open(encoding="utf-8"), delimiter="\t"))
    з_кодом, розбіжності = 0, []
    for р in рядки:
        в = next(в for в in дані["записи"][р["id"]] if в["файл"] == р["файл"])
        з = дані["звірка"][р["id"] + "|" + р["файл"]]
        k = з["поправка"]
        код = П.код_розкиду(tuple(в["lab"]), з["хрома"][1], [k] * 3 if k else None)[0]
        з_кодом += код is not None
        if (код or "невідомо") != р["код_main"]:
            розбіжності.append((р["id"], р["файл"], р["код_main"], код))
    print("кадрів %d; кодів свіжого main %d; розбіжностей із колонкою ДО %d" % (len(рядки), з_кодом, len(розбіжності)))
    for р in розбіжності:
        print(р)
    return bool(розбіжності)


if __name__ == "__main__":
    sys.exit(main())
