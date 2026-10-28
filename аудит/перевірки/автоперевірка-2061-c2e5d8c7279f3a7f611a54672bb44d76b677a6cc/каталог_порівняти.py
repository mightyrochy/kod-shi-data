"""Зіставити id, типи та збережені фото власних знімків двох дерев."""
import collections
import json
from pathlib import Path
import sys


def головна():
    """Надрукувати лише числа, отримані з фактично перечитаних каталогів."""
    тека = Path(__file__).resolve().parent
    sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "джерела"))
    import колір_річ as К
    каталоги = {ім: json.loads((тека / ім).read_text(encoding="utf-8"))["каталог"]
               for ім in sys.argv[2:]}
    після = каталоги[sys.argv[2]]
    ід_після = {р["id"]: р for р in після}
    підсумок = {}
    for ім, записи in каталоги.items():
        за_ід = {р["id"]: р for р in записи}
        підсумок[ім] = dict(записів=len(записи), типи=dict(collections.Counter(К.тип_кольору(р) for р in записи)),
            втрачено_id=len(set(за_ід) - set(ід_після)),
            змінених_записів=sum(р != ід_після.get(ід) for ід, р in за_ід.items()),
            невимірів_з_lab=sum(bool(р.get("lab")) for р in записи if К.тип_кольору(р) != "вимір"))
    корінь = Path(sys.argv[1]).resolve()
    група = json.loads((корінь / "аудит/перевірка/2.13_тип_кольору/каталог.json").read_text(encoding="utf-8"))["група_59"]
    підсумок["група_59"] = dict(розмір=len(група), знайдено=sum(ід in ід_після for ід in група),
        зі_збереженим_фото=sum(bool(ід_після[ід].get("колір_вимір")) for ід in група),
        з_типом_вимір=sum(К.тип_кольору(ід_після[ід]) == "вимір" for ід in група))
    текст = json.dumps(підсумок, ensure_ascii=False, indent=2)
    (тека / "каталог-підсумок.json").write_text(текст, encoding="utf-8")
    print(текст)


if __name__ == "__main__":
    головна()
