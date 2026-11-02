# Datei: web_streamer.py
# Version: 1.0.2
# Leichter HTTP-Streamer für VisionPi2000 (Spiegelt Pygame nativ auf den Webbrowser)

import http.server
import socketserver
import threading
import time
import io
import pygame

VERSION = "1.0.2"
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
    <title>VisionPi2000 Live-Stream</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            background: #0c0e18;
            color: #ffffff;
            text-align: center;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 15px;
        }
        h2 {
            color: #ffd700;
            margin: 5px 0 12px 0;
            letter-spacing: 1px;
        }
        .stream-box {
            display: inline-block;
            max-width: 96vw;
            max-height: 85vh;
        }
        img {
            max-width: 100%;
            max-height: 85vh;
            height: auto;
            border: 3px solid #ffd700;
            border-radius: 12px;
            box-shadow: 0 0 25px rgba(0, 0, 0, 0.85);
        }
    </style>
</head>
<body>
    <h2>VISION PI 2000 • LIVE</h2>
    <div class="stream-box">
        <img src="/stream.mjpg" alt="VisionPi2000 Live Stream" />
    </div>
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
        # Schnelles Herunterskalieren auf 800x600 für minimale Netzwerk- und CPU-Last
        surface = pygame.transform.scale(screen, (800, 600))
        buf = io.BytesIO()

        # Der Dateiname "frame.jpg" weist Pygame (SDL_image) an, nativ als JPEG in den RAM-Buffer zu schreiben
        pygame.image.save(surface, buf, "frame.jpg")

        with lock:
            latest_jpeg = buf.getvalue()
    except Exception:
        pass
