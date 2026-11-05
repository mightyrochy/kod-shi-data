"""Збережене джерело керує воротами всього пакета, а не лише його контрастом."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import colorspace as С
import pipeline as К


def main():
    """Перевіряє межу моделі й фізичного виміру за старого аргументу викликача."""
    випадків = 0
    for дж in ("model_hex", "spectro"):
        F = С.features(С.hx("#d7b59c"), С.hx("#30251e"), С.hx("#493024"), джерело=дж)
        п = К.підготувати(F, source="uncontrolled", форма_повна=False)
        assert п["готово"], п.get("чому")
        г = п["особа"]["гейт_джерела"]
        assert г["джерело"] == дж
        if дж == "model_hex":
            assert not г["можна_стверджувати"] and not any(г["надійність"].values())
            assert п["особа"]["value_gap"] is None
        else:
            assert "contrast" in г["можна_стверджувати"] and п["особа"]["доступно"]
        випадків += 1
    print("джерело воріт та ознак:", випадків, "контрольні випадки пройдено")


if __name__ == "__main__":
    main()
