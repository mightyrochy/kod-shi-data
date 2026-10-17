"""5620: offline-фікстура готовності; не виконує жнив і не доводить свіжості."""
import importlib.util
from pathlib import Path
import tempfile
import yaml
def main():
    """Перевіряє розклад на синтетичних контрактах без запуску виконавця."""
    корінь = Path(__file__).resolve().parents[2]
    сп = importlib.util.spec_from_file_location("розклад", корінь / "zhnyvarka/розклад.py")
    м = importlib.util.module_from_spec(сп); сп.loader.exec_module(м)
    workflow = (корінь / ".github/workflows/zhnyva.yml").read_text()
    схема = yaml.load(workflow, Loader=yaml.BaseLoader)
    assert схема["on"]["schedule"] == [{"cron": "17 3 * * 1"}]
    assert схема["jobs"]["harvest"]["needs"] == "schedule-readiness"
    assert "needs.schedule-readiness.outputs.ready == 'true'" in схема["jobs"]["harvest"]["if"]
    assert схема["jobs"]["harvest"]["timeout-minutes"] == "${{ github.event_name == 'schedule' && 10 || 340 }}"
    with tempfile.TemporaryDirectory() as т:
        р = Path(т); (р / "zhnyvarka").mkdir(); (р / ".github/workflows").mkdir(parents=True)
        assert м.готовність(р)[0] is False
        # Синтетичні ознаки контракту, не перенесення runtime незлитої #1366.
        for ім in ("журнал_артефакт.py", "журнал_проходу.py"):
            (р / "zhnyvarka" / ім).write_text("")
        (р / "zhnyvarka/виконавець.py").write_text('from журнал_проходу import ЖурналПроходу\nпрапорці = ["--журнал", "--без-огляду"]\n')
        ш = р / ".github/workflows/zhnyva.yml"; ш.write_text(workflow)
        assert м.готовність(р)[0] is False  # Старий force/push не стає готовим від самих файлів.
        # Додаємо тільки декларативні токени майбутнього контракту.
        ознаки = '\n'.join(['python3 zhnyvarka/журнал_артефакт.py', '--журнал "$JOURNAL_ROOT" --без-огляду',
            'actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02', "always() && steps.restore.outcome == 'success'",
            'steps.restore.outputs.artifact', '${{ runner.temp }}/жнива-журнал/ідентичність.json',
            '${{ runner.temp }}/жнива-журнал/проходи/', '${{ runner.temp }}/жнива-журнал/сирі/',
            'if-no-files-found: error', 'retention-days: 30', 'actions: read'])
        безпечний = '\n'.join(л for л in workflow.splitlines() if 'git push' not in л) + '\n' + ознаки
        ш.write_text(безпечний); assert м.готовність(р)[0] is True
        ш.write_text(безпечний + '\n      HARVEST_SHOPS: ${{ inputs.shops }}')
        assert м.готовність(р)[0] is False
        ш.write_text(безпечний.replace('--пауза "$HARVEST_PAUSE"', ''))
        assert м.готовність(р)[0] is False
    print('5620: cron/ліміти перевірені; missing/unsafe/override/pause → skip; фікстура контракту → ready; HTTP/MODEL/GPU 0')

if __name__ == "__main__": main()
