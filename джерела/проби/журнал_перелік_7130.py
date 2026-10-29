"""7130: новий непорожній перелік замінює чергу, не історію; явний offline контроль."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
from журнал_проходу import ЖурналПроходу


def main():
    """Показує old+keep → keep, зі збереженою історією двох контрольних відповідей."""
    with tempfile.TemporaryDirectory(prefix="перелік7130-") as корінь:
        old, keep = "https://control.invalid/old", "https://control.invalid/keep"
        п = ЖурналПроходу(корінь, "control.invalid", "recipe-1"); п.перелік([old, keep])
        for url in [old, keep]:
            ід = п.відповідь(url, 200, b"CONTROL"); п.завершити({"url": url, "стан": "картка", "відповідь": ід})
        п.закрити(); п = ЖурналПроходу(корінь, "control.invalid", "recipe-2")
        п.перелік([keep, keep]); assert п.очікують() == [keep]
        assert п.звіт()["total"] == 1 and п.звіт()["pending"] == 1
        assert п.база.execute("SELECT count(*) FROM відповіді").fetchone()[0] == 2
        п.перелік([]); assert п.очікують() == [keep] and п.звіт()["source_complete"] is None
        assert not п.звіт()["queue_complete"]; п.закрити()
        print("7130: активна черга 2→1; old вилучено з черги, відповіді 2 збережено; порожнє джерело UNKNOWN; HTTP 0")


if __name__ == "__main__":
    main()
