"""Повтор Б.1 до старту збирання без моделей: python проби/палітра_старт_10209.py <збірка> <кеш Pyodide> <вивід>."""
import os, re, subprocess, sys, time, socket
from pathlib import Path


def головна():
    """Повторює чотири проблемні й три контрольні сцени на записаних відповідях."""
    корінь = Path(__file__).resolve().parents[2]
    збірка, кеш, вихід = map(lambda п: Path(п).resolve(), sys.argv[1:4])
    вихід.mkdir(parents=True, exist_ok=True)
    сцени = (корінь / 'аудит/проби/б1_доречність.md').read_text(encoding='utf8')
    рядки = [р.split('|') for р in сцени.splitlines() if р.startswith('б1_')]
    for номер in (7, 9, 11, 14, 1, 20, 29):
        назва, жінка, слова, *_ = рядки[номер - 1]
        запис = корінь / 'аудит/проби/б1/ДО-2710' / ('%02d_' % номер + назва)
        with socket.socket() as порт:
            порт.bind(('127.0.0.1', 0)); адреса = str(порт.getsockname()[1])
        середовище = dict(os.environ, PYTHONIOENCODING='utf-8', NODE_PATH=str(корінь / 'джерела/node_modules'),
                         MODEL_URL='http://127.0.0.1:' + адреса + '/v1', MODEL='qwen/qwen3.5-9b',
                         MODEL_MOVA='mamaylm-gemma-3-12b-it-v2.0', ZHINKA=str(корінь / 'аудит/проби/жінки' / (жінка + '.json')),
                         CHAT_TEXT=слова, OTSINKA='0', ZNIMKY=str(вихід / запис.name))
        with (вихід / (запис.name + '.replay.txt')).open('w', encoding='utf8') as лог:
            сервер = subprocess.Popen([sys.executable, str(корінь / 'аудит/проби/replay_сцени.py'), str(запис), адреса],
                                       stdout=лог, stderr=лог, env=середовище)
            try:
                time.sleep(0.3)
                subprocess.run(['node', str(Path(__file__).with_suffix('.js')), str(збірка), str(кеш), str(запис)],
                               env=середовище, check=True, timeout=300)
            finally:
                сервер.terminate(); сервер.wait()
        схожості = re.findall(r'схожість ([0-9.]+)', (вихід / (запис.name + '.replay.txt')).read_text(encoding='utf8'))
        if not схожості or min(map(float, схожості)) < 0.9:
            raise RuntimeError('схожість промптів не доведена: ' + запис.name)
        print('ПОВТОР', запис.name, '· мінімальна схожість', min(map(float, схожості)), flush=True)


if __name__ == '__main__':
    головна()
