import sys, json, http.server; sys.path.insert(0, '.')
import bridge as B
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0); тіло = json.loads(self.rfile.read(n).decode('utf-8'))
        try: вих = B.виклик(тіло['ім'], json.dumps(тіло['дані'], ensure_ascii=False))
        except Exception as e:
            import traceback; traceback.print_exc(file=sys.stderr); sys.stderr.flush()
            вих = json.dumps(dict(помилка="%s: %s" % (type(e).__name__, e)), ensure_ascii=False)
        б = (вих if isinstance(вих, str) else json.dumps(вих, ensure_ascii=False, default=str)).encode('utf-8')
        self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(б))); self.end_headers(); self.wfile.write(б)
http.server.ThreadingHTTPServer(('127.0.0.1', 8765), H).serve_forever()
