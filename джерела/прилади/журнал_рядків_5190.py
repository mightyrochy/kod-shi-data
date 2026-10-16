"""Сталий журнал спроб raw-рядка: версія промпту й тека не дають нового дозволу."""
from contextlib import contextmanager
import datetime
import hashlib
import json
import os
from pathlib import Path
import tempfile


def тека_журналу():
    """Повертає спільну теку користувача для всіх checkout і тек результатів."""
    return Path.home() / '.lyusterko' / '5190'


def відбиток(дані):
    """Рахує сталий відбиток JSON-ідентичності дозволеного повтору."""
    return hashlib.sha256((json.dumps(дані, ensure_ascii=False, indent=2) + '\n').encode('utf-8')).hexdigest()


def _записати(шлях, дані):
    """Зберігає журнал до транспорту атомарно з fsync."""
    with tempfile.NamedTemporaryFile(dir=шлях.parent, delete=False) as файл:
        тимчасовий = Path(файл.name)
        файл.write((json.dumps(дані, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
        файл.flush()
        os.fsync(файл.fileno())
    тимчасовий.replace(шлях)


@contextmanager
def відкрити(історія):
    """Блокує конкурентні прогони й додає відомі історичні спроби без мережі."""
    тека = тека_журналу()
    тека.mkdir(parents=True, exist_ok=True)
    замок = тека / '.lock'
    with замок.open('x', encoding='utf-8') as файл:
        файл.write(datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        шлях = тека / 'спроби.json'
        дані = json.loads(шлях.read_text(encoding='utf-8')) if шлях.exists() else {'version': '5190-once-v1', 'rows': {}}
        if дані.get('version') != '5190-once-v1':
            raise ValueError('Невідома версія журналу спроб')
        for запис in історія:
            ряд = дані['rows'].setdefault(запис['row_id'], {'raw': запис['raw'], 'attempts': []})
            if ряд['raw'] != запис['raw']:
                raise ValueError('Колізія row_id історичного рядка')
            відомі = {с['request_sha256'] for с in ряд['attempts']}
            for спроба in запис['attempts']:
                if спроба['request_sha256'] not in відомі:
                    ряд['attempts'].insert(0, dict(спроба, state='historical'))
        _записати(шлях, дані)
        yield Журнал(шлях, дані)
    finally:
        замок.unlink()


class Журнал:
    """Тримає історію, резервує спробу до POST і допускає лише явний повтор."""

    def __init__(self, шлях, дані):
        """Прив'язує об'єкт до вже заблокованого журналу."""
        self.шлях, self.дані = шлях, дані

    def зберегти(self):
        """Фіксує весь журнал до наступної зовнішньої дії."""
        _записати(self.шлях, self.дані)

    def попередні(self, рядок):
        """Знаходить усі спроби за raw SHA, незалежно від версій."""
        ряд = self.дані['rows'].get(рядок['row_id'])
        if ряд is not None and ряд['raw'] != рядок['raw']:
            raise ValueError('Колізія row_id журналу')
        return ряд['attempts'] if ряд else []

    def перевірити_повтор(self, рядок, версія, дозвіл):
        """Вимагає окремий дозвіл саме на цю історію та нову ідентичність."""
        попередні = self.попередні(рядок)
        if not попередні:
            return
        if not дозвіл or дозвіл.get('version') != '5190-repeat-v1' or дозвіл.get('target_identity_sha256') != відбиток(версія):
            raise ValueError('Рядок уже мав спробу; зміна версії або теки не дозволяє повтор: ' + рядок['row_id'])
        if not дозвіл.get('decision_ref') or not дозвіл.get('reason') or not дозвіл.get('authorization_id'):
            raise ValueError('Повтор не має рішення, причини або id дозволу')
        дозволені = дозвіл.get('rows', {}).get(рядок['row_id'])
        фактичні = sorted(с['request_sha256'] for с in попередні)
        if not дозволені or sorted(дозволені) != фактичні or any(с.get('authorization_id') == дозвіл['authorization_id'] for с in попередні):
            raise ValueError('Дозвіл не охоплює точну історію або вже використаний: ' + рядок['row_id'])

    def почати(self, рядки, версія, запит, файл_запиту, тека, дозвіл):
        """Резервує кожний рядок атомарно перед єдиною транспортною спробою."""
        for рядок in рядки:
            self.перевірити_повтор(рядок, версія, дозвіл)
        for рядок in рядки:
            спроби = self.дані['rows'].setdefault(рядок['row_id'], {'raw': рядок['raw'], 'attempts': []})['attempts']
            спроби.append({'identity': версія, 'request_sha256': запит, 'request_file': файл_запиту, 'output_dir': str(Path(тека).resolve()),
                'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'state': 'inflight',
                'authorization_id': дозвіл['authorization_id'] if спроби and дозвіл else None,
                'authorization': дозвіл if спроби and дозвіл else None})
        self.зберегти()

    def завершити(self, рядки, стани):
        """Зберігає валідні, відхилені й неоднозначні спроби, не стираючи історію."""
        for рядок in рядки:
            self.попередні(рядок)[-1]['state'] = стани[рядок['row_id']]
        self.зберегти()
