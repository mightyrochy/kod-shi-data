"""Спільний міжпроцесний запис часової лінії заглушок трьох рушіїв."""
import os
import time
import errno
from contextlib import contextmanager

СТРОК_ЗАМКА_С = 30
КРОК_ЗАМКА_С = 0.001


@contextmanager
def замкнути(шлях):
    """Тримає міжпроцесний замок для цілої операції з файлом."""
    with open(шлях + '.lock', 'a+b') as замок:
        замок.seek(0, 2)
        if not замок.tell():
            замок.write(b'0')
            замок.flush()
        замок.seek(0)
        if os.name == 'nt':
            import msvcrt
            межа = time.monotonic() + СТРОК_ЗАМКА_С
            while True:
                try:
                    msvcrt.locking(замок.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except OSError as збій:
                    if збій.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK) or time.monotonic() >= межа:
                        raise
                    time.sleep(КРОК_ЗАМКА_С)
        else:
            import fcntl
            fcntl.flock(замок, fcntl.LOCK_EX)
        try:
            yield
        finally:
            if os.name == 'nt':
                замок.seek(0)
                msvcrt.locking(замок.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(замок, fcntl.LOCK_UN)

def позначити(шлях, подія, слаг):
    """Дописує цілий рядок під замком, відкриваючи журнал після взяття замка."""
    with замкнути(шлях):
        with open(шлях, 'a', encoding='utf-8') as журнал:
            журнал.write('%s %s %d\n' % (подія, слаг, int(time.time() * 1000)))



def почали(шлях):
    """Часи (мс) завершених рядків `start` у спільному журналі: недописаний рядок ще не рахується."""
    try:
        with open(шлях, encoding='utf-8') as журнал:
            рядки = журнал.read().split(chr(10))[:-1]
    except OSError:
        return []
    return [int(р.split()[2]) for р in рядки if р.startswith('start ')]


def чекати_кворуму(шлях, кворум):
    """Тримає заглушку, доки в журналі не стане `кворум` стартів, — подія, а не сон: скільки б не йшов старт процесів,
    наряди перетинаються всі. Власної межі нема: недобір кворуму обриває сама обгортка (TurnMinutes, CodexStallMinutes), і стенд бачить його як збій. Кінець ставиться не раніше за час останнього старту: рівний час `end`
    сортується перед `start`, і перетин урахувався б на один менше."""
    while True:
        часи = почали(шлях)
        if len(часи) >= кворум:
            break
        time.sleep(КРОК_ЗАМКА_С)
    while int(time.time() * 1000) <= max(часи):
        time.sleep(КРОК_ЗАМКА_С)


def тримати(слаг):
    """Позначає початок і кінець роботи заглушки. Без FAKE_QUORUM — тримає FAKE_HOLD с; з FAKE_QUORUM=N — до N стартів
    у журналі (FAKE_HOLD тоді не діє)."""
    шлях = os.environ.get('FAKE_TIMELINE')
    if шлях:
        позначити(шлях, 'start', слаг)
        кворум = int(os.environ.get('FAKE_QUORUM', '0'))
        if кворум:
            чекати_кворуму(шлях, кворум)
        else:
            time.sleep(float(os.environ.get('FAKE_HOLD', '0')))
        позначити(шлях, 'end', слаг)
