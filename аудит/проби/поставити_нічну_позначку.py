"""Створює один датований дозвіл нічного прогону з довіреного розкладу GitHub."""
from datetime import datetime, timezone
import json
import os
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def поставити():
    """Створює відсутню гілку; наявну не пересуває, навіть коли main уже змінився."""
    if (os.environ.get('GITHUB_EVENT_NAME') != 'schedule' or
            os.environ.get('GITHUB_REPOSITORY') != 'mightyrochy/kod-shi-data'):
        raise RuntimeError('Дозвіл створює лише розклад основного репозиторію')
    def виклик(шлях, дані=None):
        запит = Request('https://api.github.com/repos/mightyrochy/kod-shi-data/' + quote(шлях, safe='/'),
                        data=None if дані is None else json.dumps(дані).encode('utf-8'),
                        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                                 'Accept': 'application/vnd.github+json', 'User-Agent': 'kod-shi-nightly',
                                 'Content-Type': 'application/json'})
        with urlopen(запит, timeout=30) as відповідь:
            return json.load(відповідь)
    дата = datetime.now(timezone.utc).strftime('%Y%m%d')
    гілка = 'heads/gemini-queue/Е1-нічний-живий-' + дата + '/gpt-6.1-sol-high/1/gpu-p8'
    try:
        виклик('git/ref/' + гілка)
    except HTTPError as помилка:
        if помилка.code != 404:
            raise
    else:
        print('Нічний дозвіл уже існує: ' + гілка)
        return
    голова = виклик('git/ref/heads/main')['object']['sha']
    виклик('git/refs', {'ref': 'refs/' + гілка, 'sha': голова})
    print('Створено нічний дозвіл: ' + гілка + ' ' + голова)


if __name__ == '__main__':
    поставити()
