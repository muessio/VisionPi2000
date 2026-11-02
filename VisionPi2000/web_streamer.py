# Datei: web_streamer.py
# Version: 1.2.1
# High-Compatibility MJPEG-Streamer für alle Browser (Chrome, Safari, Firefox, Edge)

import http.server
import socketserver
import threading
import time
import io
import os
import pygame

VERSION = "1.2.1"
PORT = 8080

latest_jpeg = None
lock = threading.Lock()
last_capture_time = 0.0

active_clients = 0
clients_lock = threading.Lock()

_scaled_surface = None
_scaled_size = (0, 0)

_server_thread = None
_server_lock = threading.Lock()
_server_instance = None

JPEG_INTERVAL = 0.08


def get_header_bytes():
    for name in ["header.png", "Header.png", "HEADER.png"]:
        if os.path.exists(name):
            try:
                with open(name, "rb") as f:
                    return f.read()
            except Exception:
                pass
    return None


class StreamHandler(http.server.BaseHTTPRequestHandler):
    timeout = 10.0

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
                return

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
                return

            elif self.path.startswith("/stream.mjpg"):
                self.send_response(200)
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()

                with clients_lock:
                    active_clients += 1

                try:
                    last_sent_frame = None
                    while True:
                        with lock:
                            frame = latest_jpeg

                        if frame is not None and frame is not last_sent_frame:
                            last_sent_frame = frame
                            self.wfile.write(b"--frame\r\n")
                            self.wfile.write(b"Content-Type: image/jpeg\r\n")
                            self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("utf-8"))
                            self.wfile.write(frame)
                            self.wfile.write(b"\r\n")
                            self.wfile.flush()

                        time.sleep(0.08)
                except (ConnectionResetError, BrokenPipeError, OSError):
                    pass
                finally:
                    with clients_lock:
                        active_clients = max(0, active_clients - 1)
                return
            else:
                self.send_response(404)
                self.end_headers()
        except Exception:
            pass


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def background_server():
    global _server_instance
    try:
        server = ThreadedHTTPServer(("0.0.0.0", PORT), StreamHandler)
        _server_instance = server
        server.serve_forever()
    except Exception as e:
        print(f"Web-Streamer Fehler auf Port {PORT}: {e}")
    finally:
        _server_instance = None


def start_streaming_thread():
    global _server_thread
    with _server_lock:
        if _server_thread is not None and _server_thread.is_alive():
            return
        _server_thread = threading.Thread(
            target=background_server,
            daemon=True,
            name="VisionPi2000-WebStreamer"
        )
        _server_thread.start()


def update_stream_frame(screen):
    global latest_jpeg, last_capture_time, _scaled_surface, _scaled_size
    if screen is None:
        return

    now = time.time()
    if now - last_capture_time < JPEG_INTERVAL:
        return
    last_capture_time = now

    try:
        sw, sh = screen.get_width(), screen.get_height()
        target_size = (640, 360) if (sw / float(sh)) > 1.5 else (640, 480)

        if _scaled_surface is None or _scaled_size != target_size:
            _scaled_surface = pygame.Surface(target_size)
            _scaled_size = target_size

        pygame.transform.smoothscale(screen, target_size, _scaled_surface)

        buf = io.BytesIO()
        pygame.image.save(_scaled_surface, buf, "frame.jpg", quality=85)
        jpeg_data = buf.getvalue()
        buf.close()

        if jpeg_data and jpeg_data.startswith(b"\xff\xd8"):
            with lock:
                latest_jpeg = jpeg_data
    except Exception:
        pass


def get_stream_status():
    with lock:
        has_frame = latest_jpeg is not None
    with clients_lock:
        clients = active_clients
    return {
        "version": VERSION,
        "running": (_server_thread is not None and _server_thread.is_alive()),
        "has_frame": has_frame,
        "active_clients": clients,
        "port": PORT
    }
