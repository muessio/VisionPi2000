# Datei: visionpi.py
# Version: 1.1.15-stable
# VisionPi2000 - Hauptmenü im Cyber-Circuit-Design mit farbigen Spalten-Hintergründen

import pygame
import serial
import sys
import os
import gc
import glob
import random
import time
import json
import importlib
import subprocess

os.environ['SDL_RENDER_SCALE_QUALITY'] = '0'

try: import game_x01
except ImportError: game_x01 = None
try: import game_cricket
except ImportError: game_cricket = None
try: import game_elimination
except ImportError: game_elimination = None
try: import game_splitscore
except ImportError: game_splitscore = None
try: import game_shanghai
except ImportError: game_shanghai = None
try: import game_aroundclock
except ImportError: game_aroundclock = None
try: import game_fruit_splasher
except ImportError: game_fruit_splasher = None
try: import game_spieleanleitung
except ImportError: game_spieleanleitung = None
try: import game_service
except ImportError: game_service = None
try: import game_about
except ImportError: game_about = None
try: import online_manager
except ImportError: online_manager = None
try: import web_streamer
except ImportError: web_streamer = None

VERSION = "1.1.15-stable"

# Globaler RAM-schonender Asset-Cache für 0ms Spielstart auf dem Pi 4B (1GB RAM)
GLOBAL_FONT_CACHE = {}
GLOBAL_SOUND_CACHE = {}
GLOBAL_IMAGE_CACHE = {}
SHARED_GAME_ASSETS = {}
_frame_cache = {}

_orig_sysfont = pygame.font.SysFont
_orig_sound = None


def draw_cyber_frame_colored(surface, x, y, w, h, bg_color, cut=18):
    """Zeichnet den Cyber-Tech-Rahmen mit einer spezifischen Hintergrundfarbe für die Spalten."""
    key = ("cyber_frame_col", w, h, bg_color, cut)
    if key not in _frame_cache:
        if len(_frame_cache) > 24:
            _frame_cache.clear()
        NEON_GREEN = (0, 255, 157)
        NEON_CYAN = (0, 216, 255)
        NEON_RED = (255, 56, 76)
        GOLD_TRACE = (180, 140, 40)

        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        r = w - 2
        b = h - 2
        pts_local = [
            (cut, 1), (r - cut, 1), (r, cut), (r, b - cut),
            (r - cut, b), (cut, b), (1, b - cut), (1, cut)
        ]
        
        # Hintergrundfarbe mit leichter Transparenz (210 von 255) einfüllen, damit das Design erhalten bleibt
        col_with_alpha = (bg_color[0], bg_color[1], bg_color[2], 210)
        pygame.draw.polygon(panel_surf, col_with_alpha, pts_local)

        traces = [
            [(cut + 15, 12), (cut + 60, 12), (cut + 75, 26)],
            [(r - cut - 15, 12), (r - cut - 60, 12), (r - cut - 75, 26)],
            [(cut + 15, b - 12), (cut + 60, b - 12), (cut + 75, b - 26)]
        ]
        for tr in traces:
            pygame.draw.lines(panel_surf, (255, 255, 255, 70), False, tr, 1)
            pygame.draw.circle(panel_surf, (0, 255, 157, 120), tr[-1], 3, 1)

        pygame.draw.polygon(panel_surf, (0, 110, 75), pts_local, 5)
        pygame.draw.polygon(panel_surf, NEON_GREEN, pts_local, 2)

        c_len = int(h * 0.20)
        pygame.draw.line(panel_surf, NEON_RED, (1, cut), (cut, 1), 3)
        pygame.draw.line(panel_surf, NEON_RED, (1, b - cut), (cut, b), 3)
        pygame.draw.line(panel_surf, NEON_CYAN, (2, cut + 10), (2, cut + c_len), 3)
        pygame.draw.line(panel_surf, NEON_CYAN, (2, b - cut - 10), (2, b - cut - c_len), 3)

        pygame.draw.line(panel_surf, NEON_RED, (r - cut, 1), (r, cut), 3)
        pygame.draw.line(panel_surf, NEON_RED, (r - cut, b), (r, b - cut), 3)
        pygame.draw.line(panel_surf, NEON_CYAN, (r - 1, cut + 10), (r - 1, cut + c_len), 3)
        pygame.draw.line(panel_surf, NEON_CYAN, (r - 1, b - cut - 10), (r - 1, b - cut - c_len), 3)

        for cx, cy in [(cut + 8, 6), (r - cut - 8, 6), (cut + 8, b - 6), (r - cut - 8, b - 6)]:
            pygame.draw.circle(panel_surf, GOLD_TRACE, (cx, cy), 3)

        _frame_cache[key] = panel_surf

    surface.blit(_frame_cache[key], (x, y))


def draw_cyber_frame(surface, x, y, w, h, cut=22):
    """Standard Cyber-Rahmen für Popups und Infos."""
    key = ("cyber_frame_v2", w, h, cut)
    if key not in _frame_cache:
        if len(_frame_cache) > 16:
            _frame_cache.clear()
        NEON_GREEN = (0, 255, 157)
        NEON_CYAN = (0, 216, 255)
        NEON_RED = (255, 56, 76)
        GOLD_TRACE = (180, 140, 40)
        PANEL_BG = (8, 20, 32, 225)

        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        r = w - 2
        b = h - 2
        pts_local = [
            (cut, 1), (r - cut, 1), (r, cut), (r, b - cut),
            (r - cut, b), (cut, b), (1, b - cut), (1, cut)
        ]
        pygame.draw.polygon(panel_surf, PANEL_BG, pts_local)

        traces = [
            [(cut + 20, 14), (cut + 90, 14), (cut + 110, 34)],
            [(r - cut - 20, 14), (r - cut - 90, 14), (r - cut - 110, 34)],
            [(cut + 20, b - 14), (cut + 90, b - 14), (cut + 110, b - 34)],
            [(r - cut - 20, b - 14), (r - cut - 90, b - 14), (r - cut - 110, b - 34)]
        ]
        for tr in traces:
            pygame.draw.lines(panel_surf, (20, 65, 60, 160), False, tr, 2)
            pygame.draw.circle(panel_surf, (0, 255, 157, 160), tr[-1], 4, 1)

        pygame.draw.polygon(panel_surf, (0, 110, 75), pts_local, 6)
        pygame.draw.polygon(panel_surf, NEON_GREEN, pts_local, 2)

        c_len = int(h * 0.22)
        pygame.draw.line(panel_surf, NEON_RED, (1, cut), (cut, 1), 4)
        pygame.draw.line(panel_surf, NEON_RED, (1, b - cut), (cut, b), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (2, cut + 12), (2, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (2, b - cut - 12), (2, b - cut - c_len), 4)

        pygame.draw.line(panel_surf, NEON_RED, (r - cut, 1), (r, cut), 4)
        pygame.draw.line(panel_surf, NEON_RED, (r - cut, b), (r, b - cut), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (r - 1, cut + 12), (r - 1, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (r - 1, b - cut - 12), (r - 1, b - cut - c_len), 4)

        for cx, cy in [(cut + 10, 8), (r - cut - 10, 8), (cut + 10, b - 8), (r - cut - 10, b - 8)]:
            pygame.draw.circle(panel_surf, GOLD_TRACE, (cx, cy), 4)

        _frame_cache[key] = panel_surf

    surface.blit(_frame_cache[key], (x, y))


def _cached_sysfont(name, size, bold=False, italic=False):
    key = (str(name).lower(), int(size), bool(bold), bool(italic))
    if key not in GLOBAL_FONT_CACHE:
        GLOBAL_FONT_CACHE[key] = _orig_sysfont(name, int(size), bold=bold, italic=italic)
    return GLOBAL_FONT_CACHE[key]


def _cached_sound(file_path):
    if isinstance(file_path, str):
        if file_path not in GLOBAL_SOUND_CACHE:
            GLOBAL_SOUND_CACHE[file_path] = _orig_sound(file_path)
        return GLOBAL_SOUND_CACHE[file_path]
    return _orig_sound(file_path)


def get_settings_path():
    if os.path.exists("/boot/firmware"): return "/boot/firmware/settings.json"
    if os.path.exists("/boot"): return "/boot/settings.json"
    return "settings.json"

def load_settings():
    default_settings = {
        "format": "4:3", 
        "mapper": "display_mapper_Vision_Dart", 
        "branch": "stable",
        "wifi_ssid": "", 
        "wifi_password": "",
        "mqtt_broker": "broker.emqx.io",
        "mqtt_room": "VP2000-Raum-1"
    }
    path = get_settings_path()
    if not os.path.exists(path): return default_settings
    try:
        with open(path, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                for k, v in default_settings.items():
                    if k not in data: data[k] = v
                data["mapper"] = data["mapper"].replace(".py", "")
                return data
    except Exception:
        pass
    return default_settings

def ensure_wifi_connection(settings):
    ssid = settings.get("wifi_ssid", "").strip()
    password = settings.get("wifi_password", "").strip()
    if not ssid:
        return
    
    try:
        res = subprocess.run("nmcli -t -f active,ssid dev wifi | grep '^yes'", shell=True, capture_output=True, text=True, timeout=5)
        current_ssid = res.stdout.split(":", 1)[1].strip() if res.stdout and ":" in res.stdout else ""
        
        if current_ssid != ssid:
            print(f"Erzwinge Verbindung mit WLAN aus settings.json: {ssid}...")
            if current_ssid:
                subprocess.run(f'sudo nmcli connection modify id "{current_ssid}" connection.autoconnect no >/dev/null 2>&1', shell=True, timeout=5)
                subprocess.run("sudo nmcli device disconnect wlan0 >/dev/null 2>&1", shell=True, timeout=5)
            
            subprocess.run("sudo nmcli device wifi rescan >/dev/null 2>&1", shell=True, timeout=5)
            time.sleep(2)
            
            if password:
                subprocess.run(f'sudo nmcli device wifi connect "{ssid}" password "{password}" >/dev/null 2>&1', shell=True, timeout=12)
            else:
                subprocess.run(f'sudo nmcli device wifi connect "{ssid}" >/dev/null 2>&1', shell=True, timeout=12)
    except Exception as e:
        print(f"WLAN Auto-Connect Fehler: {e}")

def find_image_file(preferred_names):
    if isinstance(preferred_names, str):
        preferred_names = [preferred_names]
    
    for name in preferred_names:
        if os.path.exists(name):
            return name
            
    try:
        files = os.listdir('.')
        files_lower = {f.lower(): f for f in files}
        for name in preferred_names:
            if name.lower() in files_lower:
                return files_lower[name.lower()]
    except Exception:
        pass
    return None


def preload_all_game_assets(sw, sh, is_16_9, raw_bg_surface):
    """Lädt und skaliert alle Spiel-Ressourcen einmalig während des Boot-Splashscreens."""
    if raw_bg_surface is not None:
        game_bg = raw_bg_surface.copy()
        darker_overlay = pygame.Surface((sw, sh))
        darker_overlay.set_alpha(160)
        darker_overlay.fill((0, 0, 0))
        game_bg.blit(darker_overlay, (0, 0))
        SHARED_GAME_ASSETS[f"bg_{sw}_{sh}_{is_16_9}"] = game_bg

    sound_files = [
        "sounds/click.wav", "sounds/start.wav", "sounds/victory.wav",
        "sounds/champ.wav", "sounds/hit_single.wav", "sounds/hit_double.wav",
        "sounds/hit_triple.wav", "sounds/switch_player.wav",
        "sounds/miss.wav", "sounds/bust.wav"
    ]
    for snd_path in sound_files:
        if os.path.exists(snd_path):
            try:
                snd_obj = pygame.mixer.Sound(snd_path)
                SHARED_GAME_ASSETS[f"snd_{snd_path}"] = snd_obj
            except Exception:
                SHARED_GAME_ASSETS[f"snd_{snd_path}"] = None

    ss_imgs = []
    berry_files = [
        "Bullseye-Berry_Original.png",
        "Bullseye-Berry_Cyber.png",
        "Bullseye-Berry_Ninja.png",
        "Bullseye-Berry_Champ.png"
    ]
    for b_file in berry_files:
        f_found = find_image_file(b_file)
        if f_found:
            try:
                raw_av = pygame.image.load(f_found).convert_alpha()
                GLOBAL_IMAGE_CACHE[b_file] = raw_av
                ss_imgs.append(pygame.transform.smoothscale(raw_av, (100, 100)))

                if b_file != "Bullseye-Berry_Champ.png":
                    base_28 = int(sh * 0.28)
                    SHARED_GAME_ASSETS[f"av28_{b_file}_{sh}"] = [
                        pygame.transform.smoothscale(raw_av, (base_28 + off, base_28 + off))
                        for off in [-10, -5, 0, 5, 10]
                    ]
                    base_25 = int(sh * 0.25)
                    SHARED_GAME_ASSETS[f"av_{b_file}_{sh}"] = [
                        pygame.transform.smoothscale(raw_av, (base_25 + off, base_25 + off))
                        for off in [-8, -4, 0, 4, 8]
                    ]
                else:
                    SHARED_GAME_ASSETS[f"champ45_{sh}"] = pygame.transform.smoothscale(
                        raw_av, (int(sh * 0.45), int(sh * 0.45))
                    )
                    SHARED_GAME_ASSETS[f"champ_{sh}"] = pygame.transform.smoothscale(
                        raw_av, (int(sh * 0.42), int(sh * 0.42))
                    )
            except Exception:
                pass
    SHARED_GAME_ASSETS["ss_avatars"] = ss_imgs

    font_ratios = [0.018, 0.020, 0.021, 0.022, 0.024, 0.025, 0.026, 0.028, 0.030, 0.032, 0.033, 0.034, 0.040, 0.044, 0.045, 0.12, 0.20]
    for r in font_ratios:
        sz = int(sh * r)
        pygame.font.SysFont("arial", sz, bold=True)
        SHARED_GAME_ASSETS[f"font_{sz}"] = pygame.font.SysFont("arial", sz, bold=True)

    for mod in [game_x01, game_cricket, game_elimination, game_splitscore, game_shanghai, game_aroundclock, game_fruit_splasher]:
        if mod is not None:
            if hasattr(mod, "_ASSET_CACHE") and isinstance(mod._ASSET_CACHE, dict):
                mod._ASSET_CACHE.update(SHARED_GAME_ASSETS)
            else:
                setattr(mod, "_ASSET_CACHE", SHARED_GAME_ASSETS)


class ScreenSaver:
    def __init__(self, width, height, is_16_9=False):
        self.width, self.height = width, height
        self.timeout = 10 * 60 * 1000  
        self.last_activity = pygame.time.get_ticks()
        self.active = False
        
        self.state = "ANIMATION"
        self.state_timer = pygame.time.get_ticks()
        
        self.avatars = []
        av_size = int(min(width, height) * 0.13)
        berry_files = ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]
        for file in berry_files:
            raw_av = GLOBAL_IMAGE_CACHE.get(file)
            if raw_av is None:
                f_found = find_image_file(file)
                if f_found:
                    try:
                        raw_av = pygame.image.load(f_found).convert_alpha()
                    except Exception:
                        raw_av = None
            if raw_av is not None:
                try:
                    img = pygame.transform.smoothscale(raw_av, (av_size, av_size))
                    self.avatars.append({
                        "img": img,
                        "size": av_size,
                        "x": random.randint(50, max(60, width - av_size - 50)),
                        "y": random.randint(50, max(60, height - av_size - 50)),
                        "vx": random.choice([-3, 3]),
                        "vy": random.choice([-3, 3])
                    })
                except Exception:
                    pass
        self.font = pygame.font.SysFont("arial", int(height * 0.026), bold=True)
        self.hint_surf = self.font.render("STANDBY – Beliebige Taste drücken zum Fortfahren", True, (140, 140, 140))
        self.hint_rect = self.hint_surf.get_rect(center=(self.width // 2, self.height - int(self.height * 0.05)))

        if is_16_9:
            candidates = [
                "screensaver_16_9.jpg", "Screensaver_16_9.jpg",
                "screensaver_16_9.png", "Screensaver_16_9.png",
                "screensaver.jpg", "Screensaver.jpg",
                "screensaver.png", "Screensaver.png"
            ]
        else:
            candidates = [
                "screensaver.jpg", "Screensaver.jpg",
                "screensaver.png", "Screensaver.png",
                "screensaver_16_9.jpg", "Screensaver_16_9.jpg"
            ]

        self.static_img = None
        img_found = find_image_file(candidates)
        if img_found:
            try:
                raw_img = pygame.image.load(img_found).convert()
                self.static_img = pygame.transform.scale(raw_img, (width, height))
            except Exception:
                pass

    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active:
            self.active = False
            self.state = "ANIMATION"
            self.state_timer = pygame.time.get_ticks()
            return True
        return False

    def check(self):
        now = pygame.time.get_ticks()
        if not self.active and (now - self.last_activity > self.timeout):
            self.active = True
            self.state = "IMAGE" if (self.static_img is not None and not self.avatars) else "ANIMATION"
            self.state_timer = now
        return self.active

    def update_and_draw(self, screen):
        if not self.active:
            return
        
        current_time = pygame.time.get_ticks()
        
        if self.state == "ANIMATION":
            if self.static_img is not None and (current_time - self.state_timer > 60000):
                self.state = "IMAGE"
                self.state_timer = current_time
        elif self.state == "IMAGE":
            if self.avatars and (current_time - self.state_timer > 30000):
                self.state = "ANIMATION"
                self.state_timer = current_time

        if self.state == "IMAGE" and self.static_img is not None:
            screen.blit(self.static_img, (0, 0))
        else:
            screen.fill((0, 0, 0))
            for av in self.avatars:
                sz = av["size"]
                av["x"] += av["vx"]
                av["y"] += av["vy"]
                if av["x"] <= 0 or av["x"] >= self.width - sz:
                    av["vx"] *= -1
                if av["y"] <= 0 or av["y"] >= self.height - sz:
                    av["vy"] *= -1
                screen.blit(av["img"], (av["x"], av["y"]))
            screen.blit(self.hint_surf, self.hint_rect)

def init_serial():
    for port in glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'):
        try:
            ser = serial.Serial(port, 115200, timeout=0.01)
            time.sleep(2.5) 
            return ser
        except Exception:
            continue
    return None

def draw_column(screen, font, title_font, x, y, w, h, color, title, items, sel_idx):
    NEON_GREEN = (0, 255, 157)
    
    # Hier wird nun die übergebene Farbe (Rot, Blau, Grau) als dezenter Hintergrund-Ton eingesetzt
    draw_cyber_frame_colored(screen, x, y, w, h, color, cut=18)
    
    t_surf = title_font.render(title, True, (255, 205, 45))
    screen.blit(t_surf, (x + (w - t_surf.get_width()) // 2, y + 14))
    pygame.draw.line(screen, NEON_GREEN, (x + 15, y + 46), (x + w - 15, y + 46), 2)
    
    y_off = y + 58
    for i, item in enumerate(items):
        is_sel = (i == sel_idx)
        item_color = (0, 255, 157) if is_sel else (255, 255, 255)
        prefix = "▶  " if is_sel else "    " 
        screen.blit(font.render(prefix + item, True, item_color), (x + 15, y_off))
        y_off += (font.get_height() + 10) 

def main():
    global _orig_sound
    pygame.init(); pygame.mixer.init()
    pygame.mouse.set_visible(False)

    # Globale Cache-Hooks für Schriften und Sounds aktivieren
    _orig_sound = pygame.mixer.Sound
    pygame.font.SysFont = _cached_sysfont
    pygame.mixer.Sound = _cached_sound
    
    settings = load_settings()
    ensure_wifi_connection(settings) 
    
    is_16_9 = (settings.get("format", "4:3") == "16:9")
    mapper_name = settings.get("mapper", "display_mapper_Vision_Dart")
    
    try:
        mapper_mod = importlib.import_module(mapper_name)
        LoewenDisplay = mapper_mod.LoewenDisplay
    except Exception as e:
        print(f"Fehler beim Laden des Mappers {mapper_name}: {e}. Nutze Fallback.")
        import display_mapper_Vision_Dart
        LoewenDisplay = display_mapper_Vision_Dart.LoewenDisplay
        
    if is_16_9:
        TARGET_WIDTH, TARGET_HEIGHT = 1920, 1080
    else:
        TARGET_WIDTH, TARGET_HEIGHT = 1024, 768

    screen = pygame.display.set_mode((TARGET_WIDTH, TARGET_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)

    if web_streamer:
        web_streamer.start_streaming_thread()
        orig_flip = pygame.display.flip
        def hooked_flip():
            web_streamer.update_stream_frame(pygame.display.get_surface())
            orig_flip()
        pygame.display.flip = hooked_flip

    # Startbild SOFORT auf den Bildschirm bringen, damit das Laden dahinter unsichtbar passiert
    splash_start = pygame.time.get_ticks()
    start_candidates = ["Start_16_9.jpg", "start_16_9.jpg", "Start_16_9.JPG", "Start16_9.jpg"] if is_16_9 else ["Start.jpg", "start.jpg", "Start.JPG"]
    start_file = find_image_file(start_candidates)
    has_splash = False
    if start_file:
        try:
            screen.blit(pygame.transform.scale(pygame.image.load(start_file).convert(), (TARGET_WIDTH, TARGET_HEIGHT)), (0, 0))
            pygame.display.flip()
            has_splash = True
        except Exception:
            pass
    
    ser = init_serial()
    display = LoewenDisplay(ser) 
    display.set_light(True)      
    display.clear_all()

    bg_candidates = ["background_16_9.jpg", "background_16_9.png", "background_16_9.PNG"] if is_16_9 else ["background.jpg", "background.png", "Background.png", "background.PNG"]
    bg_file = find_image_file(bg_candidates)
    bg_img = None
    raw_scaled_bg = None
    if bg_file:
        try:
            raw_bg = pygame.image.load(bg_file).convert()
            raw_scaled_bg = pygame.transform.scale(raw_bg, (TARGET_WIDTH, TARGET_HEIGHT))
            bg_img = raw_scaled_bg.copy()
            darker_overlay = pygame.Surface((TARGET_WIDTH, TARGET_HEIGHT))
            darker_overlay.set_alpha(165); darker_overlay.fill((4, 12, 20))
            bg_img.blit(darker_overlay, (0, 0))
        except Exception:
            pass

    # Alle Spiel-Assets (Hintergrund, Sounds, Avatare, Fonts) während des Startbilds vorladen
    preload_all_game_assets(TARGET_WIDTH, TARGET_HEIGHT, is_16_9, raw_scaled_bg)

    sound_click = pygame.mixer.Sound("sounds/click.wav") if os.path.exists("sounds/click.wav") else None
    sound_start = pygame.mixer.Sound("sounds/start.wav") if os.path.exists("sounds/start.wav") else None

    screensaver = ScreenSaver(TARGET_WIDTH, TARGET_HEIGHT, is_16_9)

    header_file = find_image_file(["header.png", "Header.png", "HEADER.png"])
    header_img = None
    if header_file:
        try:
            raw_h = pygame.image.load(header_file).convert_alpha()
            header_h = int(TARGET_HEIGHT * 0.36 * 1.15)
            header_w = int(raw_h.get_width() * (header_h / raw_h.get_height()))
            header_img = pygame.transform.smoothscale(raw_h, (header_w, header_h))
        except Exception:
            pass

    if has_splash:
        try:
            if ser:
                try: ser.reset_input_buffer()
                except Exception: pass
            waiting = True
            while waiting:
                if pygame.time.get_ticks() - splash_start > 7000: waiting = False
                if ser and ser.in_waiting > 0:
                    try:
                        if ser.readline().decode('utf-8','ignore').strip() == "BTN:START": waiting = False
                    except Exception: pass
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN and e.key in [pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN]: waiting = False 
                time.sleep(0.02)
        except Exception:
            pass

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.02), bold=True)
    title_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.026), bold=True)
    big_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.04), bold=True)
    
    info_title_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.034), bold=True)
    info_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.032), bold=True)
    info_hint_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.033), bold=True)

    game_registry = []
    for m in [game_x01, game_cricket, game_elimination, game_splitscore, game_shanghai, game_aroundclock, game_fruit_splasher, game_spieleanleitung, game_service, game_about]:
        if m and hasattr(m, 'GAMES') and hasattr(m, 'OPTIONS'):
            for g in m.GAMES: 
                game_registry.append({"name": g, "options": m.OPTIONS, "module": m})
        elif m:
            print(f"Warnung: Modul {m.__name__} übersprungen (GAMES oder OPTIONS fehlt)")

    # Standard-Modi ohne Team für alle Nicht-X01 Spiele (wie Cricket etc.)
    standard_modes_no_team = [
        "Normales Spiel",
        "Bullseye-Berry (Stufe 1)",
        "Bullseye-Berry (Stufe 2)",
        "Bullseye-Berry (Stufe 3)",
        "Online: Host (Lobby)",
        "Online: Gast (Beitreten)"
    ]

    # Modi mit Team exklusiv für X01 Spiele (301, 501, 701)
    standard_modes_with_team = [
        "Normales Spiel",
        "Bullseye-Berry (Stufe 1)",
        "Bullseye-Berry (Stufe 2)",
        "Bullseye-Berry (Stufe 3)",
        "Team-Modus",
        "Online: Host (Lobby)",
        "Online: Gast (Beitreten)"
    ]

    sel_game, sel_option, sel_mode, players, running = 0, 0, 0, 1, True
    combo_press_start = 0
    last_gc_collect = time.time()

    def update_menu_hardware_display():
        g_name = game_registry[sel_game]["name"] if game_registry else "301"
        is_system_menu = g_name in ["Service-Menü", "Spieleanleitung", "Über das Projekt"]
        
        is_x01_game = (g_name in ["301", "501", "701"])
        active_modes = standard_modes_with_team if is_x01_game else standard_modes_no_team
        mode_str = active_modes[sel_mode] if sel_mode < len(active_modes) else ""

        tot_pl = 1 if is_system_menu else min(8, players + 1 if "Bullseye-Berry" in mode_str else players)
        preview_score = int(g_name) if g_name in ["301", "501", "701"] else (40 if g_name == "Split Score" else (1 if g_name == "Around the Clock" else 0))
        display.clear_buffer()
        for i in range(8):
            if not is_system_menu and i < tot_pl: display.set_score(i, preview_score); display.set_pl_lamp(i + 1, True)
            else: display.set_score(i, None); display.set_pl_lamp(i + 1, False)
        display.set_temp_score(None); display.set_turn(tot_pl if not is_system_menu else 0); display.set_dart_arrows(0)
        display.update()
        if ser:
            try:
                ser.write(b"LAMP:START:2\n")
                ser.write(b"LAMP:PLAYER:2\n")
                ser.flush()
            except Exception:
                pass

    display.clear_all()
    update_menu_hardware_display()
    screensaver.reset_timer()

    while running:
        if time.time() - last_gc_collect > 60.0:
            last_gc_collect = time.time()
            gc.collect()

        g_list = [g["name"] for g in game_registry]
        current_game_name = g_list[sel_game] if g_list else ""
        
        # Exakte Zuweisung der Modi je nach Spieltyp
        if current_game_name == "Service-Menü":
            c_opts = game_service.OPTIONS if game_service else ["Einstellungen"]
            modes = ["Konfiguration & Tests"]
        elif current_game_name == "Spieleanleitung":
            c_opts = game_spieleanleitung.OPTIONS if game_spieleanleitung else ["Anleitung"]
            modes = ["Regeln & Hilfe"]
        elif current_game_name == "Über das Projekt":
            c_opts = game_about.OPTIONS if game_about else ["Infos"]
            modes = ["Projekt & Ziel"]
        else:
            c_opts = game_registry[sel_game]["options"]
            if current_game_name in ["301", "501", "701"]:
                modes = standard_modes_with_team
            else:
                modes = standard_modes_no_team

        if sel_option >= len(c_opts): sel_option = 0
        if sel_mode >= len(modes): sel_mode = 0

        raw_data = None
        if ser and ser.in_waiting > 0:
            try:
                while ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', 'ignore').strip()
                    if line.startswith(("BTN:", "HIT:")):
                        raw_data = line
                        break
            except Exception:
                raw_data = None
            
        for e in pygame.event.get():
            if e.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer():
                    raw_data = None
                    continue
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: raw_data = "BTN:RED"
                elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif e.key == pygame.K_g: raw_data = "BTN:GREY"
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_SPACE: raw_data = "BTN:START"

        if raw_data:
            if screensaver.reset_timer():
                raw_data = None
                continue

        keys = pygame.key.get_pressed()
        if raw_data == "BTN:COMBO":
            trigger_info = True
            raw_data = None
        elif keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
            if combo_press_start == 0:
                combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 2000:
                trigger_info = True
                combo_press_start = 0
        else:
            combo_press_start = 0
            trigger_info = False

        if trigger_info:
            screensaver.reset_timer()
            showing_info = True
            if ser:
                try: ser.reset_input_buffer()
                except Exception: pass
            while showing_info:
                if bg_img: screen.blit(bg_img, (0, 0))
                else: screen.fill((0,0,0))
                
                box_w = int(TARGET_WIDTH * 0.75)
                box_h = int(TARGET_HEIGHT * 0.85)
                box_x = (TARGET_WIDTH - box_w) // 2
                box_y = (TARGET_HEIGHT - box_h) // 2
                
                draw_cyber_frame(screen, box_x, box_y, box_w, box_h, cut=22)

                cur_y = box_y + int(box_h * 0.04)
                
                t_surf = info_title_font.render("SYSTEM-INFORMATIONEN & SOFTWARE-STÄNDE", True, (255,205,45))
                screen.blit(t_surf, (box_x + (box_w - t_surf.get_width()) // 2, cur_y))
                cur_y += int(box_h * 0.08)

                main_surf = info_font.render(f"Hauptmenü (visionpi.py): v{VERSION}", True, (255,255,255))
                screen.blit(main_surf, (box_x + int(box_w * 0.08), cur_y))
                cur_y += int(box_h * 0.055)

                modules_to_check = [
                    ("X01", game_x01),
                    ("Cricket", game_cricket),
                    ("Elimination", game_elimination),
                    ("Split Score", game_splitscore),
                    ("Shanghai", game_shanghai),
                    ("Around the Clock", game_aroundclock),
                    ("Fruit Splasher", game_fruit_splasher),
                    ("Online-Engine", online_manager),
                    ("Web-Streamer", web_streamer),
                    ("Spieleanleitung", game_spieleanleitung),
                    ("Service-Menü", game_service),
                    ("Über das Projekt", game_about)
                ]

                for mod_name, mod_obj in modules_to_check:
                    mod_ver = getattr(mod_obj, 'VERSION', 'Unbekannt') if mod_obj else 'Nicht geladen'
                    color = (0, 255, 157) if mod_obj else (255, 56, 76)
                    text_str = f"• {mod_name}: v{mod_ver}" if mod_obj else f"• {mod_name}: Modul fehlt"
                    mod_surf = info_font.render(text_str, True, color)
                    screen.blit(mod_surf, (box_x + int(box_w * 0.12), cur_y))
                    cur_y += int(box_h * 0.048)

                hint_surf = info_hint_font.render("Zum Schließen: Spielerwechsel-Taste drücken", True, (255, 205, 45))
                screen.blit(hint_surf, (box_x + (box_w - hint_surf.get_width()) // 2, box_y + box_h - int(box_h * 0.08)))

                pygame.display.flip()
                clock.tick(20)
                for ev in pygame.event.get():
                    if ev.type == pygame.KEYDOWN and ev.key in [pygame.K_p, pygame.K_ESCAPE]:
                        showing_info = False
                if ser and ser.in_waiting > 0:
                    try:
                        if ser.readline().decode('utf-8','ignore').strip() == "BTN:PLAYER":
                            showing_info = False
                    except Exception:
                        pass
            trigger_info = False
            raw_data = None
            screensaver.reset_timer()

        if raw_data:
            if raw_data in ["BTN:RED", "BTN:BLUE", "BTN:GREY", "BTN:PLAYER"]:
                if sound_click: sound_click.play()
                if raw_data == "BTN:RED": 
                    sel_game, sel_option, sel_mode = (sel_game + 1) % len(g_list), 0, 0
                elif raw_data == "BTN:BLUE": 
                    sel_option = (sel_option + 1) % len(c_opts)
                elif raw_data == "BTN:GREY": 
                    if current_game_name not in ["Service-Menü", "Spieleanleitung", "Über das Projekt"]:
                        sel_mode = (sel_mode + 1) % len(modes)
                        if players == 8:
                            while "Berry" in modes[sel_mode]: sel_mode = (sel_mode + 1) % len(modes)
                elif raw_data == "BTN:PLAYER": 
                    if current_game_name not in ["Service-Menü", "Spieleanleitung", "Über das Projekt"]:
                        players = players + 1 if players < 8 else 1
                        if players == 8 and "Berry" in modes[sel_mode]: sel_mode = 0
                update_menu_hardware_display()
            elif raw_data == "BTN:START":
                if sound_start: sound_start.play()
                if ser:
                    try:
                        ser.write(b"LAMP:START:0\n")
                        ser.write(b"LAMP:PLAYER:0\n")
                        ser.flush()
                    except Exception:
                        pass
                mod = game_registry[sel_game]["module"]
                chosen_mode = modes[sel_mode]
                if mod:
                    if chosen_mode.startswith("Online:") and online_manager:
                        is_host_mode = ("Host" in chosen_mode)
                        online_manager.run_online_lobby_and_match(
                            screen, ser, display, players,
                            g_list[sel_game], c_opts[sel_option],
                            is_host_mode, mod, settings
                        )
                    else:
                        mod.run_game(screen, ser, display, players, g_list[sel_game], c_opts[sel_option], chosen_mode)
                    display.set_light(True)
                    display.clear_all() 
                    update_menu_hardware_display()
                    if ser:
                        try: ser.reset_input_buffer()
                        except Exception: pass
                    pygame.event.clear()
                    gc.collect()
                    screensaver.reset_timer()

        if screensaver.check():
            screensaver.update_and_draw(screen)
            pygame.display.flip()
            clock.tick(30)
            continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0,0,0))
        
        header_y_pos = 0 
        if header_img: 
            screen.blit(header_img, ((TARGET_WIDTH - header_img.get_width()) // 2, header_y_pos))
        else:
            hx = (TARGET_WIDTH - big_font.render("VisionPi2000", True, (255,205,45)).get_width()) // 2
            screen.blit(big_font.render("VisionPi2000", True, (255,205,45)), (hx, header_y_pos + 10))
        
        cw = int(TARGET_WIDTH * 0.28)
        ch = int(TARGET_HEIGHT * 0.48)  
        pad = int(TARGET_WIDTH * 0.03)
        sx = (TARGET_WIDTH - (3 * cw + 2 * pad)) // 2
        
        sy = int(TARGET_HEIGHT * 0.38)  
        
        # Hier werden die klassischen Farben (Rot, Blau, Grau) als dezent getönter Hintergrund in die Spalten übergeben
        draw_column(screen, font, title_font, sx, sy, cw, ch, (180, 30, 30), "SPIEL", g_list, sel_game)
        draw_column(screen, font, title_font, sx + cw + pad, sy, cw, ch, (30, 80, 180), "OPTION", c_opts, sel_option)
        draw_column(screen, font, title_font, sx + 2 * (cw + pad), sy, cw, ch, (80, 80, 80), "MODUS", modes, sel_mode)

        if current_game_name in ["Service-Menü", "Spieleanleitung", "Über das Projekt"]:
            screen.blit(big_font.render("System-Funktion", True, (255,255,255)), (sx, sy + ch + int(TARGET_HEIGHT * 0.015)))
            screen.blit(font.render("Wähle eine Option mit Rot/Blau und starte mit START", True, (150, 150, 150)), (sx, sy + ch + int(TARGET_HEIGHT * 0.055)))
        else:
            screen.blit(big_font.render(f"Spieleranzahl: {players}", True, (255,255,255)), (sx, sy + ch + int(TARGET_HEIGHT * 0.015)))
            screen.blit(font.render("Tasten Rot, Blau, Grau zur Auswahl - START zum Beginnen", True, (150, 150, 150)), (sx, sy + ch + int(TARGET_HEIGHT * 0.055)))

        pygame.display.flip()
        clock.tick(30)

    display.set_light(False) 
    pygame.quit(); sys.exit()

if __name__ == "__main__": main()
