# 동선 SK충전기 서비스 — 정적 호스팅 + 카카오 길찾기 프록시 로컬 서버
import json
import os
import urllib.request
import urllib.parse
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)
PORT = 8000


def load_env():
    """상위 폴더 .env를 직접 파싱(라이브러리 불필요)."""
    keys = {}
    path = os.path.join(PARENT, ".env")
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            keys[k.strip()] = v.strip()
    return keys


ENV = load_env()
JS_KEY = ENV.get("KAKAO_JS_KEY", "")
REST_KEY = ENV.get("KAKAO_REST_KEY", "")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path

        if route == "/" or route == "/index.html":
            return self.serve_index()
        if route == "/sk_chargers.json":
            return self.serve_json(os.path.join(HERE, "sk_chargers.json"))
        if route == "/food.json":
            fp = os.path.join(HERE, "food.json")
            return self.serve_json(fp) if os.path.exists(fp) else self._send(200, "{}")
        if route == "/data.json":
            return self.serve_json(os.path.join(PARENT, "data.json"))
        if route == "/route":
            return self.serve_route(urllib.parse.parse_qs(parsed.query))

        self._send(404, "Not Found", "text/plain; charset=utf-8")

    def serve_index(self):
        with open(os.path.join(HERE, "index.html"), encoding="utf-8") as f:
            html = f.read()
        html = html.replace("__JSKEY__", JS_KEY)
        self._send(200, html, "text/html; charset=utf-8")

    def serve_json(self, path):
        with open(path, encoding="utf-8") as f:
            self._send(200, f.read())

    def serve_route(self, qs):
        origin = qs.get("origin", [""])[0]
        dest = qs.get("destination", [""])[0]
        if not origin or not dest:
            return self._send(400, json.dumps({"error": "origin/destination 필요"}))

        url = "https://apis-navi.kakaomobility.com/v1/directions?" + urllib.parse.urlencode(
            {"origin": origin, "destination": dest, "priority": "RECOMMEND"}
        )
        req = urllib.request.Request(url, headers={"Authorization": f"KakaoAK {REST_KEY}"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                self._send(200, resp.read())
        except urllib.error.HTTPError as e:
            self._send(e.code, json.dumps({"error": "길찾기 API 오류", "status": e.code,
                                           "detail": e.read().decode("utf-8", "ignore")}))
        except Exception as e:
            self._send(502, json.dumps({"error": "프록시 실패", "detail": str(e)}))

    def log_message(self, fmt, *args):
        pass  # 콘솔 깔끔하게


if __name__ == "__main__":
    print(f"[OK] JS_KEY {'로드됨' if JS_KEY else '없음!'} / REST_KEY {'로드됨' if REST_KEY else '없음!'}")
    print(f"[OK] 서버 시작 → http://localhost:{PORT}/")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
