"""5659: явні контролі відмов, inflight, втраченого тіла та зміни джерела; не фактичні HTTP."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
from журнал_проходу import ЖурналПроходу


def main():
    """Перевіряє стани черги на малих штучних відповідях."""
    with tempfile.TemporaryDirectory(prefix="стани5659-") as корінь:
        url = "https://control.invalid/product"
        п = ЖурналПроходу(корінь, "control.invalid", "recipe-1"); п.перелік([url, url])
        for стан, код in [("заслон", 200), ("збій", 500), ("невідомо", 200), ("неповна_розбірка", 200)]:
            ід = п.відповідь(url, код, b"CONTROL"); п.почати(url)
            п.завершити({"url": url, "стан": стан, "відповідь": ід})
            assert п.звіт()["pending"] == 1 and not п.звіт()["queue_complete"]
        п.почати(url); п.закрити(); п = ЖурналПроходу(корінь, "control.invalid", "recipe-1")
        assert п.продовження() and п.очікують() == [url]
        ід = п.відповідь(url, 200, b"CONTROL"); п.завершити({"url": url, "стан": "картка", "відповідь": ід})
        assert п.звіт()["queue_complete"]
        файл = next(п.тека.glob("*.body")); файл.unlink(); п.закрити()
        п = ЖурналПроходу(корінь, "control.invalid", "recipe-1"); assert п.очікують() == [url]
        ід = п.відповідь(url, 200, b"CONTROL_NEW"); п.завершити({"url": url, "стан": "картка", "відповідь": ід}); п.закрити()
        п = ЖурналПроходу(корінь, "control.invalid", "recipe-2")
        assert п.очікують() == [url] and not п.продовження()
        assert п.база.execute("SELECT count(*) FROM відповіді").fetchone()[0] == 6
        п.перелік([]); assert not п.звіт()["queue_complete"]; п.закрити()
        print("КОНТРОЛІ: заслон/збій/невідомо/неповний — pending; inflight відновлено; raw missing — pending; новий рецепт — pending; порожнє джерело не complete; історія 6")


if __name__ == "__main__":
    main()
