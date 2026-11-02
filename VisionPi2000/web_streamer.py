# Datei: web_streamer.py
# Version: 1.0.3
# Leichter HTTP-Streamer für VisionPi2000 im Cyber-Circuit-Design

import http.server
import socketserver
import threading
import time
import io
import pygame

VERSION = "1.0.3"
PORT = 8080

latest_jpeg = None
lock = threading.Lock()
last_capture_time = 0.0


class StreamHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Unterdrückt die Konsolen-Ausgaben bei jedem HTTP-Aufruf."""
        pass

    def do_GET(self):
        if self.path == '/' or self.path == '/stream.html':
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
            --gold-mid: #f5a623;
        }
        * {
            box-sizing: border-box;
        }
        body {
            background-color: var(--bg-deep);
            background-image:
                radial-gradient(circle at 50% 45%, rgba(0, 180, 120, 0.16) 0%, rgba(6, 17, 28, 0.96) 70%),
                repeating-linear-gradient(0deg, rgba(0, 255, 157, 0.03) 0px, rgba(0, 255, 157, 0.03) 1px, transparent 1px, transparent 40px),
                repeating-linear-gradient(90deg, rgba(0, 216, 255, 0.03) 0px, rgba(0, 216, 255, 0.03) 1px, transparent 1px, transparent 40px);
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 16px 24px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            align-items: center;
        }
        .topbar {
            width: 100%;
            max-width: 1280px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 10px;
        }
        .brand-wrap {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .logo-badge {
            width: 54px;
            height: 54px;
            border-radius: 50%;
            background: radial-gradient(circle, #0e6b45 0%, #073824 75%);
            border: 2.5px solid #ffffff;
            box-shadow: 0 0 14px rgba(0, 255, 157, 0.65);
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        .logo-badge::after {
            content: "🎯";
            font-size: 28px;
        }
        .brand-text {
            text-align: left;
        }
        .brand-title {
            font-size: 1.9rem;
            font-weight: 900;
            letter-spacing: 1.5px;
            color: #ffffff;
            text-shadow: 0 2px 10px rgba(0, 216, 255, 0.45);
            line-height: 1.05;
        }
        .brand-sub {
            font-size: 0.95rem;
            font-weight: 700;
            color: #e0f2f1;
            letter-spacing: 0.6px;
        }
        .live-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 16px;
            border-radius: 999px;
            background: rgba(8, 28, 44, 0.85);
            border: 2px solid var(--neon-green);
            box-shadow: 0 0 14px rgba(0, 255, 157, 0.35);
            font-weight: 800;
            font-size: 0.9rem;
            letter-spacing: 1px;
            color: var(--gold-bright);
        }
        .live-dot {
            width: 11px;
            height: 11px;
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
            max-height: 74vh;
            width: auto;
            height: auto;
            border-radius: 6px;
        }
        .footer-credit {
            margin-top: 12px;
            font-size: 1.0rem;
            font-weight: 700;
            color: #ffffff;
            letter-spacing: 0.5px;
            text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9);
        }
    </style>
</head>
<body>
    <header class="topbar">
        <div class="brand-wrap">
            <div class="logo-badge"></div>
            <div class="brand-text">
                <div class="brand-title">VisionPi2000</div>
                <div class="brand-sub">Open-Source-Dartsports</div>
            </div>
        </div>
        <div class="live-pill">
            <span class="live-dot"></span>
            <span>LIVE-STREAM • PORT 8080</span>
        </div>
    </header>

    <main class="cyber-frame">
        <div class="cyber-inner">
            <img class="stream-view" src="/stream.mjpg" alt="VisionPi2000 Live Stream" />
        </div>
    </main>

    <footer class="footer-credit">
        :Grundprogramm &amp; Design entwickelt von Oliver Müssig:
    </footer>
</body>
</html>"""
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))

        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with lock:
                        frame = latest_jpeg
                    if frame:
                        self.wfile.write(b'--FRAME\r\n')
                        self.wfile.write(b'Content-Type: image/jpeg\r\n')
                        self.wfile.write(f'Content-Length: {len(frame)}\r\n\r\n'.encode('utf-8'))
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')
                    time.sleep(0.1)  # ~10 FPS im Browser
            except Exception:
                pass
        else:
            self.send_response(404)
            self.end_headers()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def background_server():
    try:
        server = ThreadedHTTPServer(('0.0.0.0', PORT), StreamHandler)
        server.serve_forever()
    except Exception as e:
        print(f"Web-Streamer Fehler auf Port {PORT}: {e}")


def start_streaming_thread():
    """Startet den Webserver als Hintergrund-Thread."""
    t = threading.Thread(target=background_server, daemon=True)
    t.start()


def update_stream_frame(screen):
    """
    Wird durch den globalen Hook bei jedem pygame.display.flip() aufgerufen.
    Begrenzt die Bildaufnahme auf max. 10 FPS (alle 0.1s), damit die Spiel-Engine
    zu 100 % flüssig bleibt, und kodiert nativ über Pygame als JPEG im RAM.
    """
    global latest_jpeg, last_capture_time
    if screen is None:
        return

    now = time.time()
    if now - last_capture_time < 0.1:
        return
    last_capture_time = now

    try:
        surface = pygame.transform.scale(screen, (800, 600))
        buf = io.BytesIO()
        pygame.image.save(surface, buf, "frame.jpg")
        with lock:
            latest_jpeg = buf.getvalue()
    except Exception:
        pass
