import pygame
import serial
import sys
import os
import glob
import random
import time
import json
import importlib

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
try: import game_spieleanleitung
except ImportError: game_spieleanleitung = None
try: import game_service
except ImportError: game_service = None
try: import game_about
except ImportError: game_about = None

VERSION = "1.7.0"

def get_settings_path():
    if os.path.exists("/boot/firmware/settings.json"): return "/boot/firmware/settings.json"
    if os.path.exists("/boot/settings.json"): return "/boot/settings.json"
    return "settings.json"

def load_settings():
    default_settings = {"format": "4:3", "mapper": "display_mapper_Vision_Dart"}
    path = get_settings_path()
    if not os.path.exists(path): return default_settings
    try:
        with open(path, "r") as f:
            data = json.load(f)
            for k, v in default_settings.items():
                if k not in data: data[k] = v
            data["mapper"] = data["mapper"].replace(".py", "")
            return data
    except: return default_settings

# Hilfsfunktion für robustes, case-insensitives Laden von Bilddateien
def find_image_file(preferred_names):
    if isinstance(preferred_names, str):
        preferred_names = [preferred_names]
    
    # 1. Exakte Suche prüfen
    for name in preferred_names:
        if os.path.exists(name):
            return name
            
    # 2. Groß-/Kleinschreibung im Verzeichnis ignorieren (Linux/Pi Fix)
    try:
        files = os.listdir('.')
        files_lower = {f.lower(): f for f in files}
        for name in preferred_names:
            if name.lower() in files_lower:
                return files_lower[name.lower()]
    except:
        pass
    return None

class ScreenSaver:
    def __init__(self, width, height, is_16_9):
        self.width, self.height = width, height
        self.timeout = 10 * 60 * 1000  # 10 Minuten Inaktivität bis Start
        self.last_activity = pygame.time.get_ticks()
        self.active = False
        
        # Zustandssteuerung für den Wechsel-Modus (Animation vs. Statisches Bild)
        self.state = "ANIMATION"
        self.state_timer = pygame.time.get_ticks()
        
        # Bullseye Berries Animation laden
        self.avatars = []
        berry_files = ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]
        for file in berry_files:
            f_found = find_image_file(file)
            if f_found:
                try:
                    img = pygame.transform.smoothscale(pygame.image.load(f_found).convert_alpha(), (100, 100))
                    self.avatars.append({"img": img, "x": random.randint(50, width-150), "y": random.randint(50, height-150), "vx": random.choice([-2, 2]), "vy": random.choice([-2, 2])})
                except: pass
        self.font = pygame.font.SysFont("arial", int(height * 0.026), bold=True)

        # Standby-Bild formatabhängig laden (mit intelligentem Fallback)
        if is_16_9:
            candidates = ["Screensaver_16_9.jpg", "screensaver_16_9.jpg", "Screensaver_16_9.png", "screensaver_16_9.png", "Screensaver.jpg", "Screensaver.png"]
        else:
            candidates = ["Screensaver.jpg", "screensaver.jpg", "Screensaver.png", "screensaver.png", "Screensaver_16_9.jpg"]

        self.static_img = None
        img_found = find_image_file(candidates)
        if img_found:
            try:
                raw_img = pygame.image.load(img_found).convert()
                self.static_img = pygame.transform.scale(raw_img, (width, height))
            except: pass

    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active:
            self.active = False
            self.state = "ANIMATION"
            self.state_timer = pygame.time.get_ticks()
            return True
        return False

    def check(self):
        if not self.active and pygame.time.get_ticks() - self.last_activity > self.timeout:
            self.active = True
            self.state = "ANIMATION"
            self.state_timer = pygame.time.get_ticks()
        return self.active

    def update_and_draw(self, screen):
        if not self.active: return
        
        current_time = pygame.time.get_ticks()
        
        # Zeitgesteuerter Wechsel: 60 Sekunden Animation, danach 30 Sekunden statisches Bild
        if self.state == "ANIMATION":
            if current_time - self.state_timer > 60000:
                self.state = "IMAGE"
                self.state_timer = current_time
        elif self.state == "IMAGE":
            if current_time - self.state_timer > 30000:
                self.state = "ANIMATION"
                self.state_timer = current_time

        if self.state == "IMAGE" and self.static_img is not None:
            screen.blit(self.static_img, (0, 0))
        else:
            screen.fill((0, 0, 0))
            for av in self.avatars:
                av["x"] += av["vx"]; av["y"] += av["vy"]
                if av["x"] <= 0 or av["x"] >= self.width - 100: av["vx"] *= -1
                if av["y"] <= 0 or av["y"] >= self.height - 100: av["vy"] *= -1
                screen.blit(av["img"], (av["x"], av["y"]))
            hint_surf = self.font.render("STANDBY – Beliebige Taste drücken zum Fortfahren", True, (120, 120, 120))
            screen.blit(hint_surf, hint_surf.get_rect(center=(self.width // 2, self.height - 40)))

def init_serial():
    for port in glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*'):
        try:
            ser = serial.Serial(port, 115200, timeout=0.01)
            time.sleep(2.5) 
            return ser
        except: continue
    return None

def draw_column(screen, font, title_font, x, y, w, h, color, title, items, sel_idx):
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=12)
    t_surf = title_font.render(title, True, (255, 255, 255))
    screen.blit(t_surf, (x + (w - t_surf.get_width()) // 2, y + 15))
    pygame.draw.line(screen, (255, 255, 255), (x + 15, y + 50), (x + w - 15, y + 50), 2)
    y_off = y + 65
    for i, item in enumerate(items):
        item_color = (255, 215, 0) if i == sel_idx else (255, 255, 255)
        prefix = "> " if i == sel_idx else "  " 
        screen.blit(font.render(prefix + item, True, item_color), (x + 15, y_off))
        y_off += (font.get_height() + 10) 

def main():
    pygame.init(); pygame.mixer.init()
    pygame.mouse.set_visible(False) 
    
    settings = load_settings()
    is_16_9 = (settings.get("format", "4:3") == "16:9")
    mapper_name = settings.get("mapper", "display_mapper_Vision_Dart")
    
    try:
        mapper_mod = importlib.import_module(mapper_name)
        LoewenDisplay = mapper_mod.LoewenDisplay
    except Exception as e:
        print(f"Fehler beim Laden des Mappers {mapper_name}: {e}. Nutze Fallback.")
        import display_mapper_Vision_Dart
        LoewenDisplay = display_mapper_Vision_Dart.LoewenDisplay

    sound_click = pygame.mixer.Sound("sounds/click.wav") if os.path.exists("sounds/click.wav") else None
    sound_start = pygame.mixer.Sound("sounds/start.wav") if os.path.exists("sounds/start.wav") else None
        
    # --- SEITENVERHÄLTNIS ERZWINGEN ---
    if is_16_9:
        TARGET_WIDTH, TARGET_HEIGHT = 1920, 1080
    else:
        TARGET_WIDTH, TARGET_HEIGHT = 1024, 768

    screen = pygame.display.set_mode((TARGET_WIDTH, TARGET_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    # ----------------------------------
    
    ser = init_serial()
    display = LoewenDisplay(ser) 
    display.set_light(True)     
    display.clear_all()

    screensaver = ScreenSaver(TARGET_WIDTH, TARGET_HEIGHT, is_16_9)

    # --- HINTERGRUND LÄDT (Kugelsicher) ---
    bg_candidates = ["background_16_9.png", "background_16_9.PNG"] if is_16_9 else ["background.png", "Background.png", "background.PNG"]
    bg_file = find_image_file(bg_candidates)
    bg_img = None
    if bg_file:
        try:
            raw_bg = pygame.image.load(bg_file).convert()
            bg_img = pygame.transform.scale(raw_bg, (TARGET_WIDTH, TARGET_HEIGHT))
            darker_overlay = pygame.Surface((TARGET_WIDTH, TARGET_HEIGHT))
            darker_overlay.set_alpha(120); darker_overlay.fill((0, 0, 0))
            bg_img.blit(darker_overlay, (0, 0))
        except: pass

    # --- HEADER BILD LÄDT (Kugelsicher, 15% vergrößert) ---
    header_file = find_image_file(["header.png", "Header.png", "HEADER.png"])
    header_img = None
    if header_file:
        try:
            raw_h = pygame.image.load(header_file).convert_alpha()
            header_h = int(TARGET_HEIGHT * 0.36 * 1.15)
            header_w = int(raw_h.get_width() * (header_h / raw_h.get_height()))
            header_img = pygame.transform.smoothscale(raw_h, (header_w, header_h))
        except: pass

    # --- START BILD LÄDT (Kugelsicher für 16:9 und 4:3) ---
    start_candidates = ["Start_16_9.jpg", "start_16_9.jpg", "Start_16_9.JPG", "Start16_9.jpg"] if is_16_9 else ["Start.jpg", "start.jpg", "Start.JPG"]
    start_file = find_image_file(start_candidates)
    if start_file:
        try:
            screen.blit(pygame.transform.scale(pygame.image.load(start_file).convert(), (TARGET_WIDTH, TARGET_HEIGHT)), (0, 0))
            pygame.display.flip()
            if ser:
                try: ser.reset_input_buffer()
                except: pass
            splash_start = pygame.time.get_ticks()
            waiting = True
            while waiting:
                if pygame.time.get_ticks() - splash_start > 7000: waiting = False
                if ser and ser.in_waiting > 0:
                    try:
                        if ser.readline().decode('utf-8','ignore').strip() == "BTN:START": waiting = False
                    except: pass
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN and e.key in [pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN]: waiting = False 
        except: pass

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.02), bold=True)
    title_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.026), bold=True)
    big_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.04), bold=True)
    
    # Großes Info-Schrift (doppelt so groß)
    info_title_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.042), bold=True)
    info_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.032), bold=True)
    info_hint_font = pygame.font.SysFont("arial", int(TARGET_HEIGHT * 0.035), bold=True)

    # --- KUGELSICHERES LADEN DER SPIELE ---
    game_registry = []
    for m in [game_x01, game_cricket, game_elimination, game_splitscore, game_shanghai, game_aroundclock, game_spieleanleitung, game_service, game_about]:
        if m and hasattr(m, 'GAMES') and hasattr(m, 'OPTIONS'):
            for g in m.GAMES: 
                game_registry.append({"name": g, "options": m.OPTIONS, "module": m})
        elif m:
            print(f"Warnung: Modul {m.__name__} übersprungen (GAMES oder OPTIONS fehlt)")
    # --------------------------------------

    standard_modes = ["Normales Spiel", "Bullseye-Berry (Stufe 1)", "Bullseye-Berry (Stufe 2)", "Bullseye-Berry (Stufe 3)", "Team-Modus"]
    sel_game, sel_option, sel_mode, players, running = 0, 0, 0, 1, True
    combo_press_start = 0

    def update_menu_hardware_display():
        g_name = game_registry[sel_game]["name"] if game_registry else "301"
        is_system_menu = g_name in ["Service-Menü", "Spieleanleitung", "Über das Projekt"]
        tot_pl = 1 if is_system_menu else min(8, players + 1 if "Bullseye-Berry" in standard_modes[sel_mode] else players)
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
            except: pass

    display.clear_all()
    update_menu_hardware_display()

    while running:
        g_list = [g["name"] for g in game_registry]
        current_game_name = g_list[sel_game] if g_list else ""
        
        # Dynamische Optionen & Modi je nach ausgewähltem Spiel
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
            modes = standard_modes

        # Begrenze die Indizes, falls sie durch den Wechsel über den Rand laufen
        if sel_option >= len(c_opts): sel_option = 0
        if sel_mode >= len(modes): sel_mode = 0

        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
            
        for e in pygame.event.get():
            if e.type in [pygame.KEYDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer(): raw_data = None; continue
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: raw_data = "BTN:RED"
                elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif e.key == pygame.K_g: raw_data = "BTN:GREY"
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_SPACE: raw_data = "BTN:START"

        if raw_data and screensaver.reset_timer(): raw_data = None; continue

        keys = pygame.key.get_pressed()
        if raw_data == "BTN:COMBO": trigger_info = True; raw_data = None
        elif keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
            if combo_press_start == 0: combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 2000: trigger_info = True; combo_press_start = 0
        else: combo_press_start = 0; trigger_info = False

        if trigger_info:
            screensaver.reset_timer(); showing_info = True
            if ser:
                try: ser.reset_input_buffer()
                except: pass
            while showing_info:
                if bg_img: screen.blit(bg_img, (0, 0))
                else: screen.fill((0,0,0))
                
                box_w = int(TARGET_WIDTH * 0.75)
                box_h = int(TARGET_HEIGHT * 0.82)
                box_x = (TARGET_WIDTH - box_w) // 2
                box_y = (TARGET_HEIGHT - box_h) // 2
                
                pygame.draw.rect(screen, (10, 10, 10), (box_x, box_y, box_w, box_h), border_radius=16)
                pygame.draw.rect(screen, (255, 215, 0), (box_x, box_y, box_w, box_h), width=3, border_radius=16)

                cur_y = box_y + int(box_h * 0.04)
                
                t_surf = info_title_font.render("SYSTEM-INFORMATIONEN & SOFTWARE-STÄNDE", True, (255,215,0))
                screen.blit(t_surf, (box_x + (box_w - t_surf.get_width()) // 2, cur_y))
                cur_y += int(box_h * 0.11)

                main_surf = info_font.render(f"Hauptmenü (visionpi.py): v{VERSION}", True, (255,255,255))
                screen.blit(main_surf, (box_x + int(box_w * 0.08), cur_y))
                cur_y += int(box_h * 0.07)

                modules_to_check = [
                    ("X01", game_x01),
                    ("Cricket", game_cricket),
                    ("Elimination", game_elimination),
                    ("Split Score", game_splitscore),
                    ("Shanghai", game_shanghai),
                    ("Around the Clock", game_aroundclock),
                    ("Spieleanleitung", game_spieleanleitung),
                    ("Service-Menü", game_service),
                    ("Über das Projekt", game_about)
                ]

                for mod_name, mod_obj in modules_to_check:
                    mod_ver = getattr(mod_obj, 'VERSION', 'Unbekannt') if mod_obj else 'Nicht geladen'
                    color = (100, 255, 100) if mod_obj else (255, 100, 100)
                    text_str = f"• {mod_name}: v{mod_ver}" if mod_obj else f"• {mod_name}: Modul fehlt"
                    mod_surf = info_font.render(text_str, True, color)
                    screen.blit(mod_surf, (box_x + int(box_w * 0.12), cur_y))
                    cur_y += int(box_h * 0.06)

                hint_surf = info_hint_font.render("Zum Schließen: Spielerwechsel-Taste drücken (oder ESC)", True, (255, 215, 0))
                screen.blit(hint_surf, (box_x + (box_w - hint_surf.get_width()) // 2, box_y + box_h - int(box_h * 0.09)))

                pygame.display.flip()
                for ev in pygame.event.get():
                    if ev.type == pygame.KEYDOWN and ev.key in [pygame.K_p, pygame.K_ESCAPE]: showing_info = False
                if ser and ser.in_waiting > 0:
                    if ser.readline().decode('utf-8','ignore').strip() == "BTN:PLAYER": showing_info = False
            trigger_info = False; raw_data = None 

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
                    except: pass
                mod = game_registry[sel_game]["module"]
                if mod: 
                    mod.run_game(screen, ser, display, players, g_list[sel_game], c_opts[sel_option], modes[sel_mode])
                    display.set_light(True)
                    display.clear_all() 
                    update_menu_hardware_display()
                    screensaver.reset_timer()
                    if ser:
                        try: ser.reset_input_buffer()
                        except: pass
                    pygame.event.clear()

        if screensaver.check():
            screensaver.update_and_draw(screen)
            pygame.display.flip(); clock.tick(30); continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0,0,0))
        
        # --- HEADER GANZ NACH OBEN GESCHOBEN ---
        header_y_pos = 0 
        if header_img: 
            screen.blit(header_img, ((TARGET_WIDTH - header_img.get_width()) // 2, header_y_pos))
        else:
            hx = (TARGET_WIDTH - big_font.render("VISION PI 2000", True, (255,215,0)).get_width()) // 2
            screen.blit(big_font.render("VISION PI 2000", True, (255,215,0)), (hx, header_y_pos + 10))
        
        # --- MENÜBOXEN (ROT, BLAU, GRAU) ---
        cw = int(TARGET_WIDTH * 0.28)
        ch = int(TARGET_HEIGHT * 0.48)  
        pad = int(TARGET_WIDTH * 0.03)
        sx = (TARGET_WIDTH - (3 * cw + 2 * pad)) // 2
        
        sy = int(TARGET_HEIGHT * 0.38)  
        
        draw_column(screen, font, title_font, sx, sy, cw, ch, (180,30,30), "SPIEL", g_list, sel_game)
        draw_column(screen, font, title_font, sx + cw + pad, sy, cw, ch, (30,80,180), "OPTION", c_opts, sel_option)
        draw_column(screen, font, title_font, sx + 2 * (cw + pad), sy, cw, ch, (80,80,80), "MODUS", modes, sel_mode)

        # --- FOOTER TEXT POSITIONS-LOGIK ---
        if current_game_name in ["Service-Menü", "Spieleanleitung", "Über das Projekt"]:
            screen.blit(big_font.render("System-Funktion", True, (255,255,255)), (sx, sy + ch + int(TARGET_HEIGHT * 0.015)))
            screen.blit(font.render("Wähle eine Option mit Rot/Blau und starte mit START", True, (150, 150, 150)), (sx, sy + ch + int(TARGET_HEIGHT * 0.055)))
        else:
            screen.blit(big_font.render(f"Spieleranzahl: {players}", True, (255,255,255)), (sx, sy + ch + int(TARGET_HEIGHT * 0.015)))
            screen.blit(font.render("Tasten Rot, Blau, Grau zur Auswahl - START zum Beginnen", True, (150, 150, 150)), (sx, sy + ch + int(TARGET_HEIGHT * 0.055)))

        pygame.display.flip(); clock.tick(30)

    display.set_light(False) 
    pygame.quit(); sys.exit()

if __name__ == "__main__": main()
