"""HTTP chat: static Gemini-like UI + một lượt voice pipeline.

Chữ trả về trước. TTS chạy ngay sau đó, cùng nội dung.
Một lock: không ghi mic trong lúc đang nói.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.chat_env import DEEPSEEK_MODEL, LLM_PROVIDER, OLLAMA_MODEL
from voice.pipeline import run_voice_turn
from voice.tts import TTS_VOICE, speak

STATIC = Path(__file__).resolve().parent / "static"
FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/styles.css": "styles.css",
    "/app.js": "app.js",
}
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
}
MAX_BODY = 32_000

_TURN_LOCK = threading.Lock()


def health() -> dict:
    model = DEEPSEEK_MODEL if LLM_PROVIDER == "deepseek" else OLLAMA_MODEL
    return {
        "ok": True,
        "provider": LLM_PROVIDER,
        "model": model,
        "voice": TTS_VOICE,
        "ai_backend": os.getenv("AI_BACKEND", "mock"),
        "otto_act": os.getenv("OTTO_ACT", "1"),
        "tts_mode": os.getenv("TTS_MODE", "full"),
    }


def execute_turn(user_text: str | None) -> dict:
    t = run_voice_turn(user_text=user_text, speak_out=False)
    return {
        "ok": bool(t.assistant_text),
        "user_text": t.user_text,
        "assistant_text": t.assistant_text,
        "summary": t.summary(),
    }


def speak_text(text: str) -> None:
    speak(text)


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        print(f"frontend {self.address_string()} {fmt % args}", flush=True)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, health())
            return
        if path == "/favicon.ico":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        name = FILES.get(path)
        if name is None:
            self._send_json(404, {"error": "Không thấy trang."})
            return
        data = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", TYPES[Path(name).suffix])
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        body = self._read_json()
        if body is None:
            return
        if path == "/api/chat":
            text = str(body.get("text") or "").strip()
            if not text:
                self._send_json(400, {"error": "Nhập một câu."})
                return
            self._handle_turn(text)
            return
        if path == "/api/listen":
            self._handle_turn(None)
            return
        if path == "/api/replay":
            text = str(body.get("text") or "").strip()
            if not text:
                self._send_json(400, {"error": "Không có câu để đọc."})
                return
            self._speak_only(text)
            return
        self._send_json(404, {"error": "Không thấy API."})

    def _handle_turn(self, user_text: str | None) -> None:
        _TURN_LOCK.acquire()
        try:
            payload = execute_turn(user_text)
        except Exception as exc:
            _TURN_LOCK.release()
            msg = str(exc).strip() or type(exc).__name__
            # json.loads("") → "Expecting value…" — đổi thành câu rõ
            if "Expecting value" in msg or isinstance(exc, json.JSONDecodeError):
                msg = (
                    "Uno trả dòng không phải JSON (cảm biến/Serial). "
                    "Đóng Serial Monitor, rút cắm USB Uno, rồi hỏi lại."
                )
            print(f"chat lỗi: {type(exc).__name__}: {exc}", flush=True)
            self._send_json(502, {"error": msg})
            return
        who = payload.get("user_text") or "(mic trống)"
        print(f"you: {who}", flush=True)
        print(f"jarvis: {payload.get('assistant_text') or '(trống)'}", flush=True)
        self._send_then_speak(payload, str(payload.get("assistant_text") or ""))

    def _speak_only(self, text: str) -> None:
        _TURN_LOCK.acquire()
        self._send_then_speak({"ok": True}, text)

    def _send_then_speak(self, payload: dict, say: str) -> None:
        """Giữ lock tới khi TTS xong. Response đi trước để UI kịp vẽ chữ."""
        say = (say or "").strip()
        try:
            self._send_json(200, payload)
        except Exception:
            _TURN_LOCK.release()
            raise
        if not say:
            _TURN_LOCK.release()
            return

        def _run() -> None:
            try:
                speak_text(say)
            except Exception as exc:
                print(f"TTS lỗi: {exc}", flush=True)
            finally:
                _TURN_LOCK.release()

        threading.Thread(target=_run, daemon=True).start()

    def _read_json(self) -> dict | None:
        raw_len = self.headers.get("Content-Length", "0")
        try:
            n = int(raw_len)
        except ValueError:
            n = 0
        if n < 0 or n > MAX_BODY:
            self._send_json(413, {"error": "Câu quá dài."})
            return None
        raw = self.rfile.read(n) if n else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "JSON không đọc được."})
            return None
        if not isinstance(data, dict):
            self._send_json(400, {"error": "JSON phải là object."})
            return None
        return data

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()


def main() -> int:
    host = os.getenv("FRONTEND_HOST", "127.0.0.1")
    port = int(os.getenv("FRONTEND_PORT", "8787"))
    try:
        httpd = Server((host, port), Handler)
    except OSError as exc:
        print(f"Không mở được {host}:{port}: {exc}", file=sys.stderr)
        return 1
    print(f"Jarvis chat http://{host}:{port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDừng.", flush=True)
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
