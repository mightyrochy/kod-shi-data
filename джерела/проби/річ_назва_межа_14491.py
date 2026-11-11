"""Від сирої відповіді до паспорта: назва з поля речі; сама цитата назви не створює."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import мовний_шар as М
import річ_з_фото as РФ


def main():
    """Перевіряє канонічну назву й вкладені форми на всьому шляху запису її речі."""
    уривок = "моєї спідниці"
    випадки = [
        ("спідниця", ["спідниця"]),
        ({"quote": уривок, "value": "спідниця"}, ["спідниця"]),
        ({"free_text": "спідниця", "lang": "uk"}, ["спідниця"]),
        ({"quote": уривок}, []),
        ({"quote": уривок, "status": "has"}, []),
        ({"quote": уривок, "status": "has", "value": "спідниця"}, ["спідниця"]),
    ]
    збоїв = 0
    for назва, очікувані in випадки:
        річ = dict(name=назва, quote=уривок, slot="bottom", item_type="skirt")
        if not isinstance(назва, dict) or "status" not in назва:
            річ["status"] = "has"
        р = М.прийняти_розмову(json.dumps({"update": {"own_items": [річ]}, "need": "look"}))
        п = М.паспорт_з_шару(р.get("внутрішня") or {}, {}, слова_ходу=уривок)["паспорт"]
        фактичні = [р["назва"] for р in п.get("речі_з_фото") or []]
        фото = РФ.речі_з_відповіді_фото(json.dumps({"items": [dict(photo="ф1", name="skirt", slot="bottom", owner="mine")]}),
            [dict(ід="ф1", ширина=1000, висота=1600)], власні=(р.get("внутрішня") or {}).get("own_items"))
        чия = [р["чия"] for р in фото["речі_з_фото"]]
        print(json.dumps(dict(назва=назва, фактичні=фактичні, очікувані=очікувані, чия=чия), ensure_ascii=False))
        збоїв += фактичні != очікувані or чия != ["моя"]
    print(f"випадків: {len(випадки)}; збоїв: {збоїв}")
    return int(bool(збоїв))


if __name__ == "__main__":
    raise SystemExit(main())
