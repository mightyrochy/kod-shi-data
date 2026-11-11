"""Повторює записані входи траурного прогону через міст без звернень до моделей."""
import gzip, json, os, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import feed, міст_відповіді as М


def головна():
    """Надрукувати результат кожної записаної відповіді й заяви траурної картки."""
    корінь = pathlib.Path(__file__).resolve().parents[2]
    запис = корінь / "аудит/проби/знімок_входи/інше_траур.jsonl.gz"
    каталог = feed.каталог_на_диску("каталог_brief.xml")
    збоїв = 0
    with tempfile.TemporaryDirectory() as тека, gzip.open(запис, "rt", encoding="utf-8") as ф:
        for н, рядок in enumerate(ф):
            виклик = json.loads(рядок)
            if виклик["ім"] != "від_моделі":
                continue
            вхід = json.loads(виклик["вхід"])
            вхід.update(каталог=каталог, кеш_кольорів=os.path.join(тека, "кольори.json"), без_фото=True)
            вихід = json.loads(М.від_моделі(вхід))
            коди = [з["code"] for з in ((вихід.get("нагода_жінці") or {}).get("повідомлення") or {}).get("statements", [])]
            збій = bool(вихід.get("помилка"))
            збоїв += збій
            print("виклик", н, "перевірено", вихід.get("перевірено"), "збій", збій,
                  "чому", вихід.get("чому"), "заяви", коди, flush=True)
    print("збоїв", збоїв)
    return bool(збоїв)


if __name__ == "__main__":
    sys.exit(головна())
