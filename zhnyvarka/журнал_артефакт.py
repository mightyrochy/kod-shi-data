"""Відновлює журнал цього workflow/ref з GitHub artifact, поза git і без нових секретів."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile


def розпакувати(архів, корінь, ідентичність):
    """Перевіряє походження й межі шляхів до запису файлів журналу."""
    with zipfile.ZipFile(архів) as запис:
        if json.loads(запис.read("ідентичність.json")) != ідентичність:
            raise ValueError("ARTIFACT_IDENTITY_MISMATCH")
        for ім in запис.namelist():
            шлях = (корінь / ім).resolve()
            if not шлях.is_relative_to(корінь.resolve()) or ім.split('/')[0] not in {
                    "ідентичність.json", "сирі", "проходи", "зведення_жнив.tsv", "жнива_лог.txt"}:
                raise ValueError("ARTIFACT_INVALID_PATH")
            if not ім.endswith('/') and Path(ім).suffix not in {".json", ".jsonl", ".sqlite3", ".body", ".tsv", ".txt"}:
                raise ValueError("ARTIFACT_INVALID_TYPE")
        запис.extractall(корінь)


def main():
    """Обирає останній не прострочений artifact тільки цього workflow/ref."""
    ідентичність = {к: os.environ[к] for к in ("GITHUB_REPOSITORY", "GITHUB_WORKFLOW_REF", "GITHUB_REF")}
    ідентичність["schema"] = 1
    відбиток = hashlib.sha256(json.dumps(ідентичність, sort_keys=True).encode()).hexdigest()[:24]
    назва = "zhnyva-journal-" + відбиток
    корінь = Path(os.environ["RUNNER_TEMP"]) / "жнива-журнал"
    корінь.mkdir(parents=True, exist_ok=True)
    команда = ["gh", "api", f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/artifacts"]
    дані = json.loads(subprocess.check_output(команда + ["--method", "GET", "-f", "name=" + назва, "-f", "per_page=100"]))
    кандидати = [р for р in дані["artifacts"] if р["name"] == назва and not р["expired"]]
    if кандидати:
        останній = max(кандидати, key=lambda р: р["id"])
        with tempfile.TemporaryFile() as архів:
            subprocess.run(["gh", "api", f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/artifacts/{останній['id']}/zip"],
                           stdout=архів, check=True)
            архів.seek(0); розпакувати(архів, корінь, ідентичність)
        print("RESTORED", останній["id"])
    else:
        print("NO_CURRENT_JOURNAL: missing/expired; source UNKNOWN, fresh discovery required")
    (корінь / "ідентичність.json").write_text(json.dumps(ідентичність, ensure_ascii=False), encoding="utf-8")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as вихід:
        вихід.write("artifact=" + назва + "\n")


if __name__ == "__main__":
    main()
