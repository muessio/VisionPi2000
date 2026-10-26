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

VERSION = "1.4.1"

def load_settings():
    default_settings = {"format": "4:3", "mapper": "display_mapper_Vision_Dart"}
    if not os.path.exists("settings.json"): return default_settings
    try:
        with open("settings.json", "r") as f:
            data = json.load(f)
            for k, v in default_settings.items():
                if k not in data: data[k] = v
            data["mapper"] = data["mapper"].replace(".py", "")
            return data
    except: return default_settings

class ScreenSaver:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.timeout = 10 * 60 * 1000  
        self.last_activity = pygame.time.get_ticks()
        self.active = False
        self.avatars = []
        berry_files = ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]
        for file in berry_files:
            if os.path.exists(file):
                try:
                    img = pygame.transform.smoothscale(pygame.image.load(file).convert_alpha(), (100, 100))
                    self.avatars.append({"img": img, "x": random.randint(50, width-150), "y": random.randint(50, height-150), "vx": random.choice([-2, 2]), "vy": random.choice([-2, 2])})
                except: pass
        self.font = pygame.font.SysFont("arial", int(height * 0.026), bold=True)

    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active:
            self.active = False
            return True
        return False

    def check(self):
        if not self.active and pygame.time.get_ticks() - self.last_activity > self.timeout: self.active = True
        return self.active

    def update_and_draw(self, screen):
        if not self.active: return
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
        
    # --- SEITENVERHÄLTNIS ERZWINGEN (SCALED + Letterboxing) ---
    if is_16_9:
        TARGET_WIDTH, TARGET_HEIGHT = 1920, 1080
    else:
        TARGET_WIDTH, TARGET_HEIGHT = 1024, 768

    # SCALED sorgt nun dafür, dass Pygame die Zielauflösung auf den echten Monitor hoch/runterskaliert 
    # und automatisch schwarze Balken an den Rändern hinzufügt, wenn die Monitormaße abweichen!
    screen = pygame.display.set_mode((TARGET_WIDTH, TARGET_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    # ----------------------------------------------------------
    
    ser = init_serial()
    display = LoewenDisplay(ser) 
    display.set_light(True)     
    display.clear_all()

    screensaver = ScreenSaver(TARGET_WIDTH, TARGET_HEIGHT)

    bg_file = "background_16_9.png" if is_16_9 else "background.png"
    bg_img = None
    if os.path.exists(bg_file):
        try:
            raw_bg = pygame.image.load(bg_file).convert()
            bg_img = pygame.transform.scale(raw_bg, (TARGET_WIDTH, TARGET_HEIGHT))
            darker_overlay = pygame.Surface((TARGET_WIDTH, TARGET_HEIGHT))
            darker_overlay.set_alpha(120); darker_overlay.fill((0, 0, 0))
            bg_img.blit(darker_overlay, (0, 0))
        except: pass

    start_file = "Start_16_9.jpg" if is_16_9 else "Start.jpg"
    if os.path.exists(start_file):
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
    
    game_registry = []
    for m in [game_x01, game_cricket, game_elimination, game_splitscore, game_shanghai, game_aroundclock, game_spieleanleitung, game_service]:
        if m:
            for g in m.GAMES: game_registry.append({"name": g, "options": m.OPTIONS, "module": m})

    modes = ["Normales Spiel", "Bullseye-Berry (Leicht)", "Bullseye-Berry (Mittel)", "Bullseye-Berry (Schwer)", "Team-Modus"]
    sel_game, sel_option, sel_mode, players, running = 0, 0, 0, 1, True
    combo_press_start = 0

    def update_menu_hardware_display():
        g_name = game_registry[sel_game]["name"] if game_registry else "301"
        is_berry = "Bullseye-Berry" in modes[sel_mode]
        tot_pl = min(8, players + 1 if is_berry else players)
        preview_score = int(g_name) if g_name in ["301", "501", "701"] else (40 if g_name == "Split Score" else (1 if g_name == "Around the Clock" else 0))
        for i in range(8):
            if i < tot_pl: display.set_score(i, preview_score); display.set_pl_lamp(i + 1, True)
            else: display.set_score(i, None); display.set_pl_lamp(i + 1, False)
        display.set_temp_score(None); display.set_turn(tot_pl); display.set_dart_arrows(0)
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
        c_opts = game_registry[sel_game]["options"]
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
                screen.blit(title_font.render("SYSTEM-INFORMATIONEN", True, (255,215,0)), (TARGET_WIDTH*0.1, TARGET_HEIGHT*0.1))
                screen.blit(font.render(f"Vision Pi 2000: v{VERSION}", True, (255,255,255)), (TARGET_WIDTH*0.15, TARGET_HEIGHT*0.2))
                pygame.display.flip()
                for ev in pygame.event.get():
                    if ev.type == pygame.KEYDOWN and ev.key in [pygame.K_p, pygame.K_ESCAPE]: showing_info = False
                if ser and ser.in_waiting > 0:
                    if ser.readline().decode('utf-8','ignore').strip() == "BTN:PLAYER": showing_info = False
            trigger_info = False; raw_data = None 

        if raw_data:
            if raw_data in ["BTN:RED", "BTN:BLUE", "BTN:GREY", "BTN:PLAYER"]:
                if sound_click: sound_click.play()
                if raw_data == "BTN:RED": sel_game, sel_option = (sel_game + 1) % len(g_list), 0
                elif raw_data == "BTN:BLUE": sel_option = (sel_option + 1) % len(c_opts)
                elif raw_data == "BTN:GREY": 
                    sel_mode = (sel_mode + 1) % len(modes)
                    if players == 8:
                        while "Berry" in modes[sel_mode]: sel_mode = (sel_mode + 1) % len(modes)
                elif raw_data == "BTN:PLAYER": 
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
                    if g_list[sel_game] == "Service-Menü":
                        return main()
                    display.clear_all() 
                    update_menu_hardware_display()
                    screensaver.reset_timer()

        if screensaver.check():
            screensaver.update_and_draw(screen)
            pygame.display.flip(); clock.tick(30); continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0,0,0))
        
        # --- DER HEADER IST WIEDER DA ---
        hx = (TARGET_WIDTH - big_font.render("VISION PI 2000", True, (255,215,0)).get_width()) // 2
        screen.blit(big_font.render("VISION PI 2000", True, (255,215,0)), (hx, TARGET_HEIGHT * 0.05))
        # ---------------------------------
        
        cw = int(TARGET_WIDTH * 0.28)
        ch = int(TARGET_HEIGHT * 0.55)
        pad = int(TARGET_WIDTH * 0.03)
        sx = (TARGET_WIDTH - (3 * cw + 2 * pad)) // 2
        sy = int(TARGET_HEIGHT * 0.25)
        
        draw_column(screen, font, title_font, sx, sy, cw, ch, (180,30,30), "SPIEL", g_list, sel_game)
        draw_column(screen, font, title_font, sx + cw + pad, sy, cw, ch, (30,80,180), "OPTION", c_opts, sel_option)
        draw_column(screen, font, title_font, sx + 2 * (cw + pad), sy, cw, ch, (80,80,80), "MODUS", modes, sel_mode)

        screen.blit(big_font.render(f"Spieleranzahl: {players}", True, (255,255,255)), (sx, sy + ch + int(TARGET_HEIGHT*0.04)))
        pygame.display.flip(); clock.tick(30)

    display.set_light(False) 
    pygame.quit(); sys.exit()

if __name__ == "__main__": main()
