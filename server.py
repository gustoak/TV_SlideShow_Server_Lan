#!/usr/bin/env python3
"""
TV Slideshow Server
-------------------
Servidor local para uso em rede. Permite que o painel de controle
seja acessado de qualquer dispositivo na mesma rede Wi-Fi/LAN.

Uso:
    python server.py

Acesse no navegador:
    TV Display  → http://<IP-DO-PC>:8765/tv
    Controle    → http://<IP-DO-PC>:8765/control
    (ou use localhost:8765 no próprio PC)

Requisitos: Python 3.7+ (sem dependências externas)
"""

import json
import os
import sys
import socket
import mimetypes
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# ── Estado compartilhado (em memória) ──────────────────────────────────────
state = {
    "images": [],          # lista de base64 das imagens
    "delay": 5000,         # ms entre slides
    "alert": {"msg": "", "ts": "", "duration": 0, "pinned": False, "id": 0},
    "command": "",         # next / prev / pause / play
    "cmd_id": 0,
    "paused": False,
}
state_lock = threading.Lock()

# SSE clients: lista de (response_object, event)
sse_clients = []
sse_lock = threading.Lock()

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def broadcast(event_name: str, data: dict):
    """Envia evento SSE para todos os clientes conectados."""
    msg = f"event: {event_name}\ndata: {json.dumps(data)}\n\n".encode()
    with sse_lock:
        dead = []
        for (wfile, alive_event) in sse_clients:
            try:
                wfile.write(msg)
                wfile.flush()
            except Exception:
                dead.append((wfile, alive_event))
        for d in dead:
            sse_clients.remove(d)


# ── Handler HTTP ────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] {fmt % args}")

    # ── GET ──────────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        # Redirecionar raiz
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/control")
            self.end_headers()
            return

        # Servir páginas HTML embutidas
        if path == "/control":
            self._serve_file("tv-control.html")
            return
        if path == "/tv":
            self._serve_file("tv-display.html")
            return

        # SSE — stream de eventos para a TV
        if path == "/events":
            self._sse_stream()
            return

        # API: estado atual (polling fallback)
        if path == "/api/state":
            with state_lock:
                s = dict(state)
                s["images_count"] = len(s["images"])
                s_send = {k: v for k, v in s.items() if k != "images"}
            self._json(200, s_send)
            return

        # API: imagens (para a TV carregar)
        if path == "/api/images":
            with state_lock:
                imgs = list(state["images"])
            self._json(200, {"images": imgs})
            return

        # Fallback 404
        self._json(404, {"error": "not found"})

    # ── POST ─────────────────────────────────────────────────────────────
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except Exception:
            data = {}

        # Salvar imagens
        if path == "/api/images":
            imgs = data.get("images", [])
            with state_lock:
                state["images"] = imgs
            broadcast("images", {"count": len(imgs)})
            self._json(200, {"ok": True, "count": len(imgs)})
            return

        # Delay
        if path == "/api/delay":
            d = int(data.get("delay", 5000))
            with state_lock:
                state["delay"] = d
            broadcast("delay", {"delay": d})
            self._json(200, {"ok": True})
            return

        # Alerta
        if path == "/api/alert":
            with state_lock:
                state["alert"] = {
                    "msg":      data.get("msg", ""),
                    "ts":       data.get("ts", ""),
                    "duration": data.get("duration", 0),   # 0 = sem auto-fechar
                    "pinned":   data.get("pinned", False),
                    "id":       state["alert"]["id"] + 1,
                }
                alert_copy = dict(state["alert"])
            broadcast("alert", alert_copy)
            self._json(200, {"ok": True})
            return

        # Cancelar alerta
        if path == "/api/alert/clear":
            with state_lock:
                state["alert"] = {"msg": "", "ts": "", "duration": 0, "pinned": False, "id": state["alert"]["id"] + 1}
                alert_copy = dict(state["alert"])
            broadcast("alert", alert_copy)
            self._json(200, {"ok": True})
            return

        # Comando de reprodução
        if path == "/api/command":
            cmd = data.get("cmd", "")
            with state_lock:
                state["command"] = cmd
                state["cmd_id"] += 1
                cid = state["cmd_id"]
                if cmd == "pause":
                    state["paused"] = True
                elif cmd == "play":
                    state["paused"] = False
            broadcast("command", {"cmd": cmd, "id": cid})
            self._json(200, {"ok": True})
            return

        self._json(404, {"error": "not found"})

    # ── OPTIONS (CORS) ───────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    # ── SSE stream ──────────────────────────────────────────────────────
    def _sse_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()

        # Enviar estado atual imediatamente
        with state_lock:
            cur_alert = dict(state["alert"])
            cur_delay = state["delay"]
            cur_cmd   = state["command"]
            cur_paused= state["paused"]
            img_count = len(state["images"])

        def send_init():
            try:
                self.wfile.write(f"event: delay\ndata: {json.dumps({'delay': cur_delay})}\n\n".encode())
                self.wfile.write(f"event: alert\ndata: {json.dumps(cur_alert)}\n\n".encode())
                self.wfile.write(f"event: images\ndata: {json.dumps({'count': img_count})}\n\n".encode())
                self.wfile.flush()
            except Exception:
                pass

        send_init()

        # Registrar cliente
        with sse_lock:
            sse_clients.append((self.wfile, True))

        # Manter conexão aberta (heartbeat)
        try:
            import time
            while True:
                time.sleep(15)
                self.wfile.write(b": heartbeat\n\n")
                self.wfile.flush()
        except Exception:
            pass

    # ── Helpers ─────────────────────────────────────────────────────────
    def _serve_file(self, filename):
        filepath = os.path.join(SCRIPT_DIR, filename)
        if not os.path.exists(filepath):
            self._json(404, {"error": f"{filename} não encontrado na pasta do servidor"})
            return
        mime, _ = mimetypes.guess_type(filepath)
        mime = mime or "text/html"
        with open(filepath, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", len(content))
        self._cors()
        self.end_headers()
        self.wfile.write(content)

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


# ── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    PORT = 8765
    local_ip = get_local_ip()

    server = HTTPServer(("0.0.0.0", PORT), Handler)

    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║           📺  TV SLIDESHOW SERVER               ║")
    print("  ╠══════════════════════════════════════════════════╣")
    print(f"  ║  Painel de Controle → http://{local_ip}:{PORT}/control")
    print(f"  ║  Tela da TV         → http://{local_ip}:{PORT}/tv")
    print(f"  ║  (no próprio PC)    → http://localhost:{PORT}/control")
    print("  ╠══════════════════════════════════════════════════╣")
    print("  ║  Pressione Ctrl+C para encerrar                 ║")
    print("  ╚══════════════════════════════════════════════════╝")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado.")
        server.shutdown()
