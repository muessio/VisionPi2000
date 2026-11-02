# Datei: web_streamer.py
# Version: 1.0.1
# Leichter HTTP-Streamer für VisionPi2000 (Spiegelt Pygame auf den Webbrowser)

import http.server
import socketserver
import threading
import time
import pygame
import io

PORT = 8080
latest_jpeg = None
lock = threading.Lock()

class StreamHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/stream.html':
            html = """
            <html>
                <head>
                    <title>VisionPi2000 Live-Stream</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { background: #0c0e18; color: #fff; text-align: center; font-family: sans-serif; margin: 0; padding: 20px; }
                        h2 { color: #ffd700; margin-bottom: 10px; }
                        img { max-width: 100%; height: auto; border: 3px solid #ffd700; border-radius: 12px; box-shadow: 0 0 20px rgba(0,0,0,0.8); }
                    </style>
                </head>
                <body>
                    <h2>VisionPi2000 Live</h2>
                    <img src="/stream.mjpg" />
                </body>
            </html>
            """
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=FRAME')
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
                    time.sleep(0.1) # 10 FPS – schont die Pi-CPU
            except Exception:
                pass
        else:
            self.send_response(404)
            self.end_headers()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True

def background_server():
    try:
        server = ThreadedHTTPServer(('0.0.0.0', PORT), StreamHandler)
        server.serve_forever()
    except Exception:
        pass

def start_streaming_thread():
    t = threading.Thread(target=background_server, daemon=True)
    t.start()

def update_stream_frame(screen):
    """Wird durch den globalen Hook bei jedem pygame.display.flip() aufgerufen."""
    global latest_jpeg
    if screen is None:
        return
    try:
        surface = pygame.transform.smoothscale(screen, (800, 600))
        buf = io.BytesIO()
        
        try:
            # Versuch 1: Natives Pygame 2 JPEG-Save (sehr CPU-schonend)
            pygame.image.save(surface, buf, "JPEG")
        except Exception:
            # Versuch 2: Fallback über PIL (falls Pygame ohne libjpeg gebaut wurde)
            try:
                from PIL import Image
                str_data = pygame.image.tostring(surface, "RGB")
                img = Image.frombytes("RGB", surface.get_size(), str_data)
                img.save(buf, format="JPEG", quality=75)
            except Exception:
                return # Still abbrechen, falls PIL ebenfalls fehlt

        with lock:
            latest_jpeg = buf.getvalue()
    except Exception:
        pass
