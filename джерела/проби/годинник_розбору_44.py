# -*- coding: utf-8 -*-
"""Наряд 4.4 (Р21): дорога й годинник прогонів розбору (`каталог_розбір_прогін.надіслати`, `Годинник`) — без ноутбука.
Сервер форми OpenAI на 127.0.0.1 рве ПЕРШЕ з'єднання без відповіді (як ECONNRESET LM Studio, рядок 2900), решту
обслуговує за 0.2 с; чотири виклики двома потоками. Друкує: спроби, обриви ДО повтору, причину повтору, стінний час
і прогноз на 12 426 записів каталогу тим самим темпом. Запуск: python3 проби/годинник_розбору_44.py"""
import concurrent.futures, http.server, json, os, sys, threading, time
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д)
лічба = {"запитів": 0}
class Сервер(http.server.BaseHTTPRequestHandler):
    """POST /v1/chat/completions: перший — обрив з'єднання, далі — відповідь із usage."""
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"])); лічба["запитів"] += 1
        if лічба["запитів"] == 1:
            self.close_connection = True; self.connection.shutdown(2); return
        time.sleep(0.2); тіло = json.dumps({"choices": [{"message": {"content": "{}"}}],
                                            "usage": {"prompt_tokens": 900, "completion_tokens": 40}}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(тіло))); self.end_headers(); self.wfile.write(тіло)
    def log_message(self, *а): pass
с = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Сервер); threading.Thread(target=с.serve_forever, daemon=True).start()
os.environ["MODEL_URL"] = "http://127.0.0.1:%d/v1" % с.server_address[1]
import каталог_розбір_прогін as П
г = П.Годинник(2)
with concurrent.futures.ThreadPoolExecutor(2) as пул:
    відп = list(пул.map(lambda і: П.надіслати({"model": "m", "messages": []}, г, "річ"), range(4)))
з, п = г.зведення()["дія"], г.прогноз({"річ": (4, 12426)})
print("відповідей %d з 4 · запитів до сервера %d · спроб %d · викликів %d · обривів до повтору %d · повторів %s"
      % (sum(1 for т, _ in відп if т == "{}"), лічба["запитів"], з["спроб"], з["викликів"], з["обривів"], з["повторів"]))
print("стінний %.1f с · токени %d/%d · прогноз: %.2f с/річ стіною → %.1f год на 12 426"
      % (з["стінний_с"], з["вхід_т"], з["вихід_т"], п["стадії"]["річ"]["с_на_одиницю"], п["годин"]))
