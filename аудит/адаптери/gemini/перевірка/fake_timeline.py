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



def тримати(слаг):
    """Позначає початок і кінець заданого часу роботи заглушки."""
    шлях = os.environ.get('FAKE_TIMELINE')
    if шлях:
        позначити(шлях, 'start', слаг)
        time.sleep(float(os.environ.get('FAKE_HOLD', '0')))
        позначити(шлях, 'end', слаг)
