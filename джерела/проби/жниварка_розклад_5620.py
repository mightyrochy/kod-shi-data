"""5620: тільки виправний diff активного ланцюжка; жнив і мережі немає."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import yaml
def main():
    """Звіряє живі YAML-вузли й відмову для вимкнених та сторонніх кроків."""
    корінь = Path(__file__).resolve().parents[2]
    сп = importlib.util.spec_from_file_location("розклад", корінь / "zhnyvarka/розклад.py")
    м = importlib.util.module_from_spec(сп); сп.loader.exec_module(м)
    схема = yaml.load((корінь / ".github/workflows/zhnyva.yml").read_text(), Loader=yaml.BaseLoader)
    assert схема["on"]["schedule"] == [{"cron": "17 3 * * 1"}]
    assert м._ланцюжок(схема) is True
    базові = схема["jobs"]["harvest"]["steps"]
    в = next(і for і, к in enumerate(базові) if к.get("id") == "restore")
    з = next(і for і, к in enumerate(базові) if к.get("id") == "harvest")
    а = next(і for і, к in enumerate(базові) if к.get("with", {}).get("name") == "${{ steps.restore.outputs.artifact }}")
    вади = [("disabled", в, "if", "false"), ("continue", в, "continue-on-error", "true"),
            ("dead", з, "run", "if false; then\n" + базові[з]["run"] + "\nfi"),
            ("journal", з, "env", {"JOURNAL_ROOT": "/tmp/інший"}),
            ("pause", з, "run", базові[з]["run"].replace('--пауза "$HARVEST_PAUSE"', ""))]
    for назва, і, ключ, знач in вади:
        х = copy.deepcopy(схема); х["jobs"]["harvest"]["steps"][і][ключ] = знач
        assert м._ланцюжок(х) is False, назва
    х = copy.deepcopy(схема); х["jobs"]["other"] = {"steps": [х["jobs"]["harvest"]["steps"].pop(в)]}
    assert м._ланцюжок(х) is False
    х = copy.deepcopy(схема); х["jobs"]["harvest"]["steps"][а]["with"]["path"] = "/tmp/інший"
    assert м._ланцюжок(х) is False
    х = copy.deepcopy(схема); х["jobs"]["harvest"]["steps"][в], х["jobs"]["harvest"]["steps"][а] = х["jobs"]["harvest"]["steps"][а], х["jobs"]["harvest"]["steps"][в]
    assert м._ланцюжок(х) is False
    with tempfile.TemporaryDirectory() as т:
        assert м.готовність(Path(т))[0] is False
    print("5620 fixdiff: active ready; disabled/continue/dead/unrelated/journal/pause/upload/order/missing → skip; HTTP/MODEL/GPU 0")
if __name__ == "__main__": main()
