# Datei: web_streamer.py
# Version: 1.1.2
# Ultra-leichter HTTP-Streamer (0% CPU ohne Zuschauer, Asynchroner Encoder, RAM-gepiniet, TCP_NODELAY)

import http.server
import socketserver
import socket
import threading
import time
import io
import os
import pygame

VERSION = "1.1.2"
PORT = 8080

# Leicht erhöhte Bildfrequenz (~11 FPS / 0.09s) – dank Hintergrund-Thread ohne Ruckeln im Hauptprogramm
FRAME_INTERVAL = 0.09
MAX_CLIENTS = 4

latest_jpeg = None
frame_id = 0
frame_condition = threading.Condition()

active_clients = 0
clients_lock = threading.Lock()

# Asynchroner Übergabe-Puffer zwischen Pygame-Mainloop und Encoder-Thread
_raw_frame = None
_raw_event = threading.Event()
_raw_lock = threading.Lock()
_last_capture_time = 0.0

_cached_header_bytes = None


def get_header_bytes():
    global _cached_header_bytes
    if _cached_header_bytes is not None:
        return _cached_header_bytes
    for name in ["header.png", "Header.png", "HEADER.png"]:
        if os.path.exists(name):
            try:
                with open(name, "rb") as f:
                    _cached_header_bytes = f.read()
                return _cached_header_bytes
            except Exception:
                pass
    try:
        for f in os.listdir("."):
            if f.lower() == "header.png":
                with open(f, "rb") as fp:
                    _cached_header_bytes = fp.read()
                return _cached_header_bytes
    except Exception:
        pass
    return None


def _encoder_worker():
    """Hintergrund-Thread: Skaliert und komprimiert Bilder, ohne Pygame auszubremsen."""
    global latest_jpeg, frame_id
    scaled_surface = None
    scaled_size = (0, 0)
    # Einmalig allokierter RAM-Puffer verhindert Speicher-Fragmentierung auf dem 1GB Pi
    jpeg_buffer = io.BytesIO()

    while True:
        _raw_event.wait()
        _raw_event.clear()

        if active_clients <= 0:
            continue

        with _raw_lock:
            src = _raw_frame

        if src is None:
            continue

        try:
            sw, sh = src.get_width(), src.get_height()
            target_size = (800, 450) if (sw / float(sh)) > 1.5 else (768, 576)

            # 24-Bit Surface (ohne Alpha-Kanal) spart 25% RAM und beschleunigt den JPEG-Export
            if scaled_surface is None or scaled_size != target_size:
                scaled_surface = pygame.Surface(target_size, 0, 24)
                scaled_size = target_size

            pygame.transform.smoothscale(src, target_size, scaled_surface)

            jpeg_buffer.seek(0)
            jpeg_buffer.truncate(0)
            pygame.image.save(scaled_surface, jpeg_buffer, "frame.jpg")
            jpg_bytes = jpeg_buffer.getvalue()

            with frame_condition:
                latest_jpeg = jpg_bytes
                frame_id += 1
                frame_condition.notify_all()
        except Exception:
            pass


class StreamHandler(http.server.BaseHTTPRequestHandler):
    timeout = 5.0

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        global active_clients
        try:
            if self.path == "/" or self.path.startswith("/stream.html"):
                html = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>VisionPi2000 • Open-Source-Dartsports Live</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg-deep: #06111c;
            --neon-green: #00ff9d;
            --neon-cyan: #00d8ff;
            --neon-red: #ff384c;
            --gold-bright: #ffe066;
        }
        * { box-sizing: border-box; }
        body {
            background-color: var(--bg-deep);
            background-image:
                radial-gradient(circle at 50% 45%, rgba(0, 180, 120, 0.16) 0%, rgba(6, 17, 28, 0.96) 70%),
                repeating-linear-gradient(0deg, rgba(0, 255, 157, 0.03) 0px, rgba(0, 255, 157, 0.03) 1px, transparent 1px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(0, 216, 255, 0.03) 0px, rgba(0, 216, 255, 0.03) 1px, transparent 1px, transparent 40px);
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 10px 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .header-wrap {
            width: 100%;
            max-width: 1280px;
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 8px;
        }
        .header-logo {
            max-height: 110px;
            max-width: 85vw;
            width: auto;
            height: auto;
            filter: drop-shadow(0 4px 14px rgba(0, 255, 157, 0.35));
        }
        .header-fallback {
            display: none;
            font-size: 1.8rem;
            font-weight: 900;
            letter-spacing: 1.5px;
            color: #ffffff;
            text-shadow: 0 2px 10px rgba(0, 216, 255, 0.45);
        }
        .live-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 6px;
            padding: 5px 15px;
            border-radius: 999px;
            background: rgba(8, 28, 44, 0.85);
            border: 2px solid var(--neon-green);
            box-shadow: 0 0 14px rgba(0, 255, 157, 0.35);
            font-weight: 800;
            font-size: 0.85rem;
            letter-spacing: 1px;
            color: var(--gold-bright);
        }
        .live-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--neon-red);
            box-shadow: 0 0 10px var(--neon-red);
            animation: pulse 1.2s infinite ease-in-out;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.35); opacity: 0.55; }
        }
        .cyber-frame {
            position: relative;
            padding: 10px;
            background: linear-gradient(135deg, var(--neon-red) 0%, var(--neon-green) 28%, var(--neon-cyan) 72%, var(--neon-red) 100%);
            clip-path: polygon(
                22px 0, calc(100% - 22px) 0,
                100% 22px, 100% calc(100% - 22px),
                calc(100% - 22px) 100%, 22px 100%,
                0 calc(100% - 22px), 0 22px
            );
            box-shadow: 0 0 35px rgba(0, 255, 157, 0.35);
            max-width: 95vw;
        }
        .cyber-inner {
            background: #050c14;
            padding: 8px;
            clip-path: polygon(
                18px 0, calc(100% - 18px) 0,
                100% 18px, 100% calc(100% - 18px),
                calc(100% - 18px) 100%, 18px 100%,
                0 calc(100% - 18px), 0 18px
            );
        }
        img.stream-view {
            display: block;
            max-width: 92vw;
            max-height: 72vh;
            width: auto;
            height: auto;
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <header class="header-wrap">
        <img class="header-logo" src="/header.png" alt="VisionPi2000"
             onerror="this.style.display='none'; document.getElementById('fb-title').style.display='block';" />
        <div id="fb-title" class="header-fallback">VisionPi2000 • Open-Source-Dartsports</div>
        <div class="live-pill">
            <span class="live-dot"></span>
            <span>VisionPi2000 LIVE-STREAM</span>
        </div>
    </header>

    <main class="cyber-frame">
        <div class="cyber-inner">
            <img class="stream-view" src="/stream.mjpg" alt="VisionPi2000 Live Stream" />
        </div>
    </main>
</body>
</html>"""
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))

            elif self.path == "/header.png":
                data = get_header_bytes()
                if data:
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "public, max-age=3600")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                self.send_response(404)
                self.end_headers()

            elif self.path == "/stream.mjpg":
                with clients_lock:
                    if active_clients >= MAX_CLIENTS:
                        self.send_response(503)
                        self.end_headers()
                        return
                    active_clients += 1

                try:
                    self.connection.settimeout(5.0)
                    # TCP_NODELAY schickt MJPEG-Frames sofort ohne Puffer-Verzögerung auf die Reise
                    self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

                    self.send_response(200)
                    self.send_header("Age", "0")
                    self.send_header("Cache-Control", "no-cache, private")
                    self.send_header("Pragma", "no-cache")
                    self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=FRAME")
                    self.end_headers()

                    my_last_id = -1
                    while True:
                        with frame_condition:
                            if frame_id == my_last_id:
                                frame_condition.wait(timeout=1.0)
                            if frame_id == my_last_id or latest_jpeg is None:
                                continue
                            frame = latest_jpeg
                            my_last_id = frame_id

                        # Kompakter Write-Aufruf in einem Stück spart Syscalls
                        header = (
                            f"--FRAME\r\n"
                            f"Content-Type: image/jpeg\r\n"
                            f"Content-Length: {len(frame)}\r\n\r\n"
                        ).encode("ascii")
                        self.wfile.write(header + frame + b"\r\n")
                        self.wfile.flush()
                except Exception:
                    pass
                finally:
                    with clients_lock:
                        active_clients = max(0, active_clients - 1)
            else:
                self.send_response(404)
                self.end_headers()
        except Exception:
            pass


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def background_server():
    try:
        server = ThreadedHTTPServer(("0.0.0.0", PORT), StreamHandler)
        server.serve_forever()
    except Exception as e:
        print(f"Web-Streamer Fehler auf Port {PORT}: {e}")


def start_streaming_thread():
    t_enc = threading.Thread(target=_encoder_worker, daemon=True)
    t_enc.start()
    t_srv = threading.Thread(target=background_server, daemon=True)
    t_srv.start()


def update_stream_frame(screen):
    global _raw_frame, _last_capture_time
    # 0% CPU & 0 RAM wenn kein Zuschauer verbunden ist
    if active_clients <= 0 or screen is None:
        return

    now = time.time()
    if now - _last_capture_time < FRAME_INTERVAL:
        return
    _last_capture_time = now

    try:
        sw, sh = screen.get_width(), screen.get_height()
        # Schneller Blit in den Übergabe-Puffer (< 1ms), die teure Skalierung macht der Hintergrund-Thread!
        with _raw_lock:
            if _raw_frame is None or _raw_frame.get_size() != (sw, sh):
                _raw_frame = pygame.Surface((sw, sh), 0, 24)
            _raw_frame.blit(screen, (0, 0))
        _raw_event.set()
    except Exception:
        pass
 
