"""5659: offline-контролі перенесення artifact; жодних GitHub API викликів."""
import io, json, sys, tempfile, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
from журнал_артефакт import розпакувати


def архів(ідентичність, ім):
    """Робить малий явний контрольний zip, не відповідь GitHub."""
    потік = io.BytesIO()
    with zipfile.ZipFile(потік, "w") as з:
        з.writestr("ідентичність.json", json.dumps(ідентичність))
        з.writestr(ім, "CONTROL")
    потік.seek(0)
    return потік


def main():
    """Розділяє валідний журнал, чуже походження, кадр і вихід за теку."""
    ід = {"schema": 1, "GITHUB_WORKFLOW_REF": "repo/workflow@refs/heads/main"}
    with tempfile.TemporaryDirectory(prefix="artifact5659-") as тека:
        корінь = Path(тека)
        розпакувати(архів(ід, "проходи/control.invalid/abc.body"), корінь, ід)
        assert (корінь / "проходи/control.invalid/abc.body").read_text() == "CONTROL"
        for інше, ім in [({}, "сирі/x.jsonl"), (ід, "../outside.txt"), (ід, "проходи/x.jpg")]:
            try: розпакувати(архів(інше, ім), корінь, ід)
            except ValueError: pass
            else: raise AssertionError((інше, ім))
        print("ARTIFACT CONTROL: valid body preserved; wrong identity/traversal/photo rejected; HTTP 0")


if __name__ == "__main__":
    main()
