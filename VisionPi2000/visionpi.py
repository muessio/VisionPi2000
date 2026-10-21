import pygame
import serial
import sys
import os
import glob

# Zwingt die Grafikkarte, beim Skalieren keine Weichzeichner zu nutzen (Pixel bleiben scharf!)
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

# =====================================================================
# ================= LAYOUT EINSTELLUNGEN ==============================
BOX_WIDTH = 290         
BOX_HEIGHT = 420        
BOX_SPACING = 30        
MENU_START_Y = 240    
FONT_SIZE_MENU = 16     
FONT_SIZE_TITLE = 20    
HEADER_START_Y = 5    
# =====================================================================

BAUD_RATE = 115200
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
BG_COLOR, RED_COL, BLUE_COL, GREY_COL = (0, 0, 0), (180, 30, 30), (30, 80, 180), (80, 80, 80)
HIGHLIGHT, WHITE, TOPBAR_BG = (255, 215, 0), (255, 255, 255), (50, 50, 55)

VERSION = "1.0.6"

def init_serial():
    ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
    for port in ports:
        try:
            ser = serial.Serial(port, BAUD_RATE, timeout=0.01)
            return ser
        except:
            continue
    return None

def send_to_display(ser, chip, digit, value):
    if ser:
        try: ser.write(f"DISP:{chip}:{digit}:{value}\n".encode('utf-8'))
        except: pass

def clear_all_displays(ser):
    if ser:
        for c in range(10):
            for d in range(8):
                send_to_display(ser, c, d, 15)

def draw_column(screen, font, title_font, x, y, w, h, color, title, items, sel_idx):
    pygame.draw.rect(screen, color, (x, y, w, h), border_radius=12)
    t_surf = title_font.render(title, True, WHITE)
    screen.blit(t_surf, (x + (w - t_surf.get_width()) // 2, y + 15))
    pygame.draw.line(screen, WHITE, (x + 15, y + 50), (x + w - 15, y + 50), 2)
    y_off = y + 65
    for i, item in enumerate(items):
        item_color = HIGHLIGHT if i == sel_idx else WHITE
        prefix = "> " if i == sel_idx else "  " 
        screen.blit(font.render(prefix + item, True, item_color), (x + 15, y_off))
        y_off += (font.get_height() + 10) 

def main():
    pygame.init(); pygame.mixer.init()
    sound_click = pygame.mixer.Sound("sounds/click.wav") if os.path.exists("sounds/click.wav") else None
    sound_start = pygame.mixer.Sound("sounds/start.wav") if os.path.exists("sounds/start.wav") else None
        
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
    pygame.display.set_caption("VisionPi2000")
    
    ser = init_serial()

    if os.path.exists("Start.jpg"):
        try:
            screen.blit(pygame.transform.scale(pygame.image.load("Start.jpg").convert(), (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
            pygame.display.flip()
            pygame.event.clear()
            if ser:
                try: ser.reset_input_buffer()
                except: pass
            splash_start = pygame.time.get_ticks()
            waiting = True
            while waiting:
                if pygame.time.get_ticks() - splash_start > 7000: waiting = False
                if ser and ser.in_waiting > 0:
                    try:
                        s_in = ser.readline().decode('utf-8','ignore').strip()
                        if s_in == "BTN:START": waiting = False
                    except: pass
                for e in pygame.event.get():
                    if e.type == pygame.KEYDOWN and e.key in [pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN]: waiting = False 
        except: pass

    header_img = None
    if os.path.exists("header.png"):
        try:
            raw_h = pygame.image.load("header.png").convert_alpha()
            header_img = pygame.transform.scale(raw_h, (500, int(raw_h.get_height() * (500 / raw_h.get_width()))))
        except: pass

    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", FONT_SIZE_MENU, bold=True)
    title_font = pygame.font.SysFont("arial", FONT_SIZE_TITLE, bold=True)
    big_font = pygame.font.SysFont("arial", 32, bold=True)
    topbar_font = pygame.font.SysFont("arial", 16) 
    
    game_registry = []
    if game_x01:
        for g in game_x01.GAMES: game_registry.append({"name": g, "options": game_x01.OPTIONS, "module": game_x01})
    if game_cricket:
        for g in game_cricket.GAMES: game_registry.append({"name": g, "options": game_cricket.OPTIONS, "module": game_cricket})
    if game_elimination:
        for g in game_elimination.GAMES: game_registry.append({"name": g, "options": game_elimination.OPTIONS, "module": game_elimination})
    if game_splitscore:
        for g in game_splitscore.GAMES: game_registry.append({"name": g, "options": game_splitscore.OPTIONS, "module": game_splitscore})
    if game_shanghai:
        for g in game_shanghai.GAMES: game_registry.append({"name": g, "options": game_shanghai.OPTIONS, "module": game_shanghai})
    if game_aroundclock:
        for g in game_aroundclock.GAMES: game_registry.append({"name": g, "options": game_aroundclock.OPTIONS, "module": game_aroundclock})

    modes = ["Normales Spiel", "Bullseye-Berry (Leicht)", "Bullseye-Berry (Mittel)", "Bullseye-Berry (Schwer)", "Team-Modus"]
    sel_game, sel_option, sel_mode, players, running = 0, 0, 0, 1, True
    combo_press_start = 0

    clear_all_displays(ser)

    while running:
        g_list = [g["name"] for g in game_registry]
        c_opts = game_registry[sel_game]["options"]
        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
            
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE): running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r: raw_data = "BTN:RED"
                elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif e.key == pygame.K_g: raw_data = "BTN:GREY"
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_SPACE: raw_data = "BTN:START"

        keys = pygame.key.get_pressed()
        is_combo_keys = keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]
        is_combo_serial = raw_data == "BTN:COMBO"

        trigger_info = False
        
        if is_combo_serial: trigger_info = True
        elif is_combo_keys:
            if combo_press_start == 0: combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 3000: trigger_info = True
        else: combo_press_start = 0

        if trigger_info:
            showing_info = True
            if ser:
                try: ser.reset_input_buffer()
                except: pass
                
            while showing_info:
                screen.fill(BG_COLOR)
                
                screen.blit(title_font.render("SYSTEM-INFORMATIONEN (Revisionsindex)", True, HIGHLIGHT), (120, 80))
                screen.blit(font.render(f"Vision Pi 2000 (Hauptmenü): v{VERSION}", True, WHITE), (150, 150))
                y_pos = 200
                for mod_item in game_registry:
                    m_name = mod_item["name"]
                    m_ver = getattr(mod_item["module"], "VERSION", "1.0.0") if mod_item["module"] else "1.0.0"
                    screen.blit(font.render(f"- {m_name}: v{m_ver}", True, WHITE), (170, y_pos))
                    y_pos += 40
                
                screen.blit(font.render("Taste Spielerwechsel drücken, um das Menü zu verlassen.", True, HIGHLIGHT), (150, SCREEN_HEIGHT - 80))
                pygame.display.flip()
                
                for ev in pygame.event.get():
                    if ev.type == pygame.KEYDOWN and ev.key in [pygame.K_p, pygame.K_ESCAPE]: showing_info = False
                if ser and ser.in_waiting > 0:
                    s_in = ser.readline().decode('utf-8','ignore').strip()
                    if s_in == "BTN:PLAYER": showing_info = False
            
            combo_press_start = 0
            raw_data = None 

        if raw_data:
            if raw_data in ["BTN:RED", "BTN:BLUE", "BTN:GREY", "BTN:PLAYER"]:
                if sound_click: sound_click.play()
                if raw_data == "BTN:RED": sel_game, sel_option = (sel_game + 1) % len(g_list), 0
                elif raw_data == "BTN:BLUE": sel_option = (sel_option + 1) % len(c_opts)
                elif raw_data == "BTN:GREY": 
                    sel_mode = (sel_mode + 1) % len(modes)
                    while players == 8 and "Berry" in modes[sel_mode]:
                        sel_mode = (sel_mode + 1) % len(modes)
                elif raw_data == "BTN:PLAYER": 
                    players = players + 1 if players < 8 else 1
                    if players == 8 and "Berry" in modes[sel_mode]:
                        sel_mode = 0
                    send_to_display(ser, 0, 2, 15)
                    send_to_display(ser, 0, 1, 15)
                    send_to_display(ser, 0, 0, players)
            elif raw_data == "BTN:START":
                if sound_start: sound_start.play()
                mod = game_registry[sel_game]["module"]
                if mod: 
                    mod.run_game(screen, ser, players, g_list[sel_game], c_opts[sel_option], modes[sel_mode])
                    clear_all_displays(ser)

        screen.fill(BG_COLOR)
        
        pygame.draw.rect(screen, TOPBAR_BG, (0, 0, SCREEN_WIDTH, 30))
        screen.blit(topbar_font.render(f"Hauptmenü: Version {VERSION}", True, (50, 255, 50)), (15, 6))
        dev_text = "Custom Dartsports Engine • Developed by Oliver Müssig"
        dev_surf = topbar_font.render(dev_text, True, (200, 200, 200))
        screen.blit(dev_surf, ((SCREEN_WIDTH - dev_surf.get_width()) // 2, 6))
        
        if header_img: screen.blit(header_img, ((SCREEN_WIDTH - header_img.get_width()) // 2, HEADER_START_Y))
        else:
            hx = (SCREEN_WIDTH - big_font.render("VISION PI 2000", True, HIGHLIGHT).get_width()) // 2
            screen.blit(big_font.render("VISION PI 2000", True, HIGHLIGHT), (hx, HEADER_START_Y + 15))
        
        cw, ch, pad = BOX_WIDTH, BOX_HEIGHT, BOX_SPACING 
        sx, sy = (SCREEN_WIDTH - (3 * cw + 2 * pad)) // 2, MENU_START_Y 
        
        draw_column(screen, font, title_font, sx, sy, cw, ch, RED_COL, "SPIEL", g_list, sel_game)
        draw_column(screen, font, title_font, sx + cw + pad, sy, cw, ch, BLUE_COL, "OPTION", c_opts, sel_option)
        draw_column(screen, font, title_font, sx + 2 * (cw + pad), sy, cw, ch, GREY_COL, "MODUS", modes, sel_mode)

        screen.blit(big_font.render(f"Spieleranzahl: {players}", True, WHITE), (sx, sy + ch + 30))
        screen.blit(font.render("Tasten Rot, Blau, Grau zur Auswahl - START zum Beginnen", True, (150, 150, 150)), (sx, sy + ch + 75))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit(); sys.exit()

if __name__ == "__main__": main()
