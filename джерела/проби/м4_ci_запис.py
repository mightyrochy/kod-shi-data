"""Вимірює відмову git push із read-токеном CI без збережених credentials."""
import os
import subprocess
import sys


def main():
    """Пробує створити лише тимчасову гілку та вимагає явної HTTP 403 відмови."""
    saved = subprocess.run(['git', 'config', '--local', '--get-regexp',
                            r'http\..*\.extraheader'], capture_output=True)
    if saved.returncode != 1:
        sys.exit('ПОМИЛКА: checkout залишив credentials або config не прочитано')
    branch = f"refs/heads/codex/m4-probe-{os.environ['GITHUB_RUN_ID']}"
    helper = '!f() { printf "%s\\n" "username=x-access-token" "password=${GH_TOKEN}"; }; f'
    probe = subprocess.run(['git', '-c', 'credential.helper=', '-c',
                            f'credential.helper={helper}', 'push', 'origin',
                            f'HEAD:{branch}'], capture_output=True, text=True)
    print(f'checkout credentials: відсутні; probe ref: {branch}; git rc: {probe.returncode}')
    print(probe.stdout + probe.stderr)
    if probe.returncode == 0:
        sys.exit('НЕБЕЗПЕКА: гілку створено; це НЕ PASS, потрібне повідомлення координатору')
    if '403' not in probe.stderr or 'denied' not in probe.stderr.lower():
        sys.exit('НЕ ВИМІРЯНО: push не дійшов до явної відмови прав GitHub')
    print('PASS: read-токен дістав явну відмову GitHub; гілку не створено')


if __name__ == '__main__':
    main()
