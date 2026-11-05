"""Зіставити промпти й повтор записів на початковій голові доробки та після неї."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def main():
    """Виконати вимір лише під час запуску скрипту."""
    ТЕКА = Path(__file__).resolve().parent
    КОРІНЬ = ТЕКА.parents[3]
    КОД = КОРІНЬ / "джерела"
    sys.path[:0] = [str(КОД), str(КОД / "прилади")]
    if sys.argv[1] == "до":
        БАЗА = КОРІНЬ.parent / "tmp" / "модулі-2956-до"
        БАЗА.mkdir(parents=True, exist_ok=True)
        for ім in ("паспорт_поля.py", "внутрішня_мова.py"):
            (БАЗА / ім).write_bytes(subprocess.check_output(
                ["git", "show", "872c289771bb21ea4ec753ccb6eea538f0d3a8f3:джерела/" + ім], cwd=КОРІНЬ))
        sys.path.insert(0, str(БАЗА))
    else:
        БАЗА = КОД
    import мовний_шар as М
    import внутрішня_мова as В
    import паспорт_поля as П
    from е2_збирання import повне_оголошення
    from replay_картки import виміряти

    розмова = json.dumps(повне_оголошення(М.РОЗМОВА), ensure_ascii=False)
    print(json.dumps({
        "розмова": {"довжина": len(розмова), "sha256": hashlib.sha256(розмова.encode()).hexdigest(),
                    "правил_підвидів": sum(розмова.count(о) for о in П.описи_підвидів("place"))},
        "репліка": М.промпт_репліки({"not_recorded": ["place"]}),
        "схема_місця": В.СЦЕНАРІЙ["place"],
        "повтор": виміряти(КОД / "проби/дані/картка_запиту.json", БАЗА),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
