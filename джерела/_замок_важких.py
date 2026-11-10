# -*- coding: utf-8 -*-
"""_замок_важких.py — спільний на ноутбук замок важких кроків батареї: водночас іде не більше N.

ЧОМУ. Пам'ять ноутбука забирає не слот сесії (codex, shell і git слота разом ≈ 0,7 ГіБ), а важкий крок у ньому —
python-батарея й Pyodide, до 3,2 ГіБ на крок. Межа одночасних важких кроків тримає пам'ять, хоч би скільки сесій
ішло. Крок бере замок сам, на вході, — тож замок діє, хоч би хто його запустив (сесія codex, смуга claude, виконавець).

ДЕ ДІЄ. Лише коли задано змінну `KODSHI_HEAVY_DIR` — тека замків, спільна для всіх користувачів ноутбука (обгортка
задає її прогонам обох смуг). На CI, у хмарі й в інших клонах змінної нема: крок іде одразу, без замка й чекання.
N — `аудит/адаптери/gemini/важкі.json` (вимір, формула й шлях до даних там).

МЕХАНІЗМ. Слот i — файл `heavy-<i>.lock` у теці, відкритий без спільного доступу (лише читання, тож вистачає прав
INTERACTIVE/BATCH на спільну теку). Тримає його відкритий дескриптор процесу кроку; ОС закриває дескриптор зі смертю
процесу — старих PID і ручного прибирання нема. Дескриптор не успадковується: дитина кроку слота не тримає.
Черга — так само: чекач тримає квиток `heavy-q-<мс>-<pid>.lock`, і слот бере лише той, перед ким живих квитків нема.
Без черги опитування не FIFO: при 8 чекачах на 2 слоти кожне звільнення дістається одному з восьми навмання, і
окремий чекач міг би програвати годину — довше за поріг завислості codex. Той самий механізм у Node —
`_замок_важких.js`. Дитина, що сама є важким кроком, бачить `KODSHI_HEAVY_HELD` і замка вдруге не бере: інакше
N батьків, що чекають на своїх дітей, стояли б вічно.
"""
import datetime
import json
import os
import sys
import time

ЗМІННА_ТЕКИ = "KODSHI_HEAVY_DIR"
ЗМІННА_ТРИМАЮ = "KODSHI_HEAVY_HELD"
ФАЙЛ_N = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "аудит", "адаптери", "gemini", "важкі.json")
# Частота опитування, коли всі слоти зайняті: механізм, не межа роботи — крок чекає, скільки треба.
ОПИТУВАННЯ_С = 2

_ТРИМАЮ = []  # дескриптор взятого слота живе до кінця процесу


def межа(шлях=ФАЙЛ_N):
    """N з `важкі.json`; None — файла нема чи N не ціле додатне (тоді без замка, з рядком у stderr)."""
    try:
        with open(шлях, encoding="utf-8") as ф:
            n = json.load(ф)["n"]
    except (OSError, ValueError, KeyError, TypeError) as е:
        print("замок важкого кроку: N не прочитано (%s) — без замка" % е, file=sys.stderr, flush=True)
        return None
    return n if isinstance(n, int) and not isinstance(n, bool) and n > 0 else None


def _відкрити(шлях):
    """Дескриптор файла без спільного доступу або None — його тримає інший процес. Інша помилка ОС — OSError."""
    import ctypes
    from ctypes import wintypes
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateFileW.restype = wintypes.HANDLE
    k.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
                              wintypes.DWORD, wintypes.HANDLE]
    GENERIC_READ, БЕЗ_СПІЛЬНОГО, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL = 0x80000000, 0, 4, 0x80
    h = k.CreateFileW(шлях, GENERIC_READ, БЕЗ_СПІЛЬНОГО, None, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, None)
    if h is None or h == wintypes.HANDLE(-1).value:
        код = ctypes.get_last_error()
        if код == 32:  # ERROR_SHARING_VIOLATION
            return None
        raise ctypes.WinError(код)
    return h


def _закрити(h):
    """Закриває дескриптор файла замка (місце звільняється)."""
    import ctypes
    ctypes.WinDLL("kernel32").CloseHandle(ctypes.c_void_p(h))


def _попереду(тека, мій):
    """Скільки живих квитків черги старші за `мій` (None — у черзі мене нема); мертві квитки прибирає."""
    живі = 0
    for ім in sorted(os.listdir(тека)):
        if not ім.startswith("heavy-q-") or (мій is not None and ім >= мій):
            continue
        h = _відкрити(os.path.join(тека, ім))
        if h is None:
            живі += 1
            continue
        _закрити(h)
        try:
            os.remove(os.path.join(тека, ім))
        except OSError:
            pass  # прибере наступний; квиток без власника вже не рахується
    return живі


def _слот(тека, n):
    """Номер узятого вільного слота (дескриптор — у _ТРИМАЮ) або None."""
    for i in range(1, n + 1):
        h = _відкрити(os.path.join(тека, "heavy-%d.lock" % i))
        if h is not None:
            _ТРИМАЮ.append(h)
            return i
    return None


def взяти(крок):
    """Чекає своєї черги й вільного слота з N і тримає слот до кінця процесу; без `KODSHI_HEAVY_DIR` — одразу.

    Повертає номер слота або None (замка нема). Помилка ОС (тека недоступна) — рядок у stderr і крок без замка:
    батарея не має стояти через замок, якого не можна взяти."""
    тека = os.environ.get(ЗМІННА_ТЕКИ, "")
    if not тека or os.environ.get(ЗМІННА_ТРИМАЮ):
        return None
    if os.name != "nt":
        print("замок важкого кроку: лише Windows — без замка", file=sys.stderr, flush=True)
        return None
    n = межа()
    if n is None:
        return None
    квиток, дескриптор, почато = None, None, None
    try:
        while True:
            if _попереду(тека, квиток) == 0:
                i = _слот(тека, n)
                if i is not None:
                    break
            if квиток is None:
                почато = time.time()
                квиток = "heavy-q-%015d-%d.lock" % (int(почато * 1000), os.getpid())
                дескриптор = _відкрити(os.path.join(тека, квиток))
                print("чекаю замок важкого кроку %s: зайнято %d з %d, у черзі %d-й, з %s" % (
                    крок, n, n, _попереду(тека, квиток) + 1, datetime.datetime.now().strftime("%H:%M:%S")),
                    file=sys.stderr, flush=True)
            time.sleep(ОПИТУВАННЯ_С)
    except OSError as е:
        print("замок важкого кроку недоступний (%s) — без замка" % е, file=sys.stderr, flush=True)
        return None
    if дескриптор is not None:
        _закрити(дескриптор)
        try:
            os.remove(os.path.join(тека, квиток))
        except OSError:
            pass
    os.environ[ЗМІННА_ТРИМАЮ] = "%s:%d" % (крок, i)
    if почато is not None:
        print("замок важкого кроку взято: слот %d з %d, чекав %d с" % (i, n, time.time() - почато),
              file=sys.stderr, flush=True)
    return i


if __name__ == "__main__":
    # Ручна проба: `python _замок_важких.py <секунд>` бере слот і тримає його задану кількість секунд.
    print("слот", взяти("проба"), flush=True)
    time.sleep(float(sys.argv[1]) if len(sys.argv) > 1 else 0)
