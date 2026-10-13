"""РЕМОНТ-МІРИЛО: які правила блокують образи ГГ-1 до ремонту, без моделі.

  cd джерела && python3 ../аудит/проби/ремонт_блокери_до.py
"""
import collections as K, gzip, json, os, sys


def main():
    sys.path.insert(0, "."); sys.path.insert(0, os.path.dirname(__file__))
    os.environ["ЗАМІНА_ПУЛУ"] = "0"
    import гг1_повтор_ремонту as Г
    Л = K.Counter()
    for рядок in gzip.open(Г.ВХОДИ, "rt", encoding="utf-8"):
        з = json.loads(рядок)
        р = Г.промпт_ремонту(з["вх"], з["текст"], True)
        for о in (р.get("вердикт") or {}).get("образи") or []:
            бл = (о.get("структура") or {}).get("блокери") or []
            гейти = [x for x in о.get("знахідки") or [] if x.get("регістр") == "гейт"]
            Л["образів"] += 1
            Л["образів з блокером"] += bool(бл or гейти)
            for б in бл:
                Л["правило · " + str(б.get("правило") or б.get("код") or "unknown")] += 1
            for г in гейти:
                Л["правило · " + str(г.get("правило") or "unknown")] += 1
                Л["гейтів"] += 1

    print("Блокери до ремонту: %d/%d образів (%.1f %%), з них гейтів %d" %
          (Л["образів з блокером"], Л["образів"], 100 * Л["образів з блокером"] / Л["образів"], Л["гейтів"]))
    for к in sorted(к for к in Л if к.startswith("правило · ")):
        print("  %s: %d" % (к[10:], Л[к]))


if __name__ == "__main__":
    main()
