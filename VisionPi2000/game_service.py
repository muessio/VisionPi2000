import pygame
import json
import os
import glob
import subprocess

VERSION = "1.3.0"
GAMES = ["Service-Menü"]
OPTIONS = ["Starten"]

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {"format": "4:3", "mapper": "display_mapper_Vision_Dart"}

def load_settings():
    if not os.path.exists(SETTINGS_FILE): return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                if k not in data: data[k] = v
            return data
    except: return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_FILE, "w") as f: json.dump(settings, f, indent=4)
    except: pass

def get_available_mappers():
    files = glob.glob("display_mapper*.py")
    return sorted(files) if files else ["display_mapper_Vision_Dart.py"]

def do_online_update(screen, font, sw, sh, ser):
    USER_PASSWORD = "VisionPi2000"
    screen.fill((15, 15, 30))
    info_surf = font.render("Online-Update läuft... Bitte warten.", True, (255, 255, 255))
    screen.blit(info_surf, ((sw - info_surf.get_width()) // 2, sh // 2))
    pygame.display.flip()

    if ser:
        try:
            ser.write(b"LAMP:START:2\n")
            ser.write(b"LAMP:PLAYER:2\n")
            ser.flush()
        except: pass

    cmd = (
        'curl -H "Authorization: token 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" '
        'https://raw.githubusercontent.com/muessio/VisionPi2000/main/Pi_Setup/private_Update.sh -o update.sh '
        '&& chmod +x update.sh '
        f'&& echo "{USER_PASSWORD}" | sudo -S ./update.sh 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'
    )

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        msg = "Update erfolgreich! Neustart wird empfohlen."
    except subprocess.CalledProcessError as e:
        msg = "Fehler beim Update! Keine Internetverbindung?"
        print("Update Error:", e.stderr)

    screen.fill((15, 15, 30))
    result_surf = font.render(msg, True, (255, 215, 0))
    screen.blit(result_surf, ((sw - result_surf.get_width()) // 2, sh // 2))
    hint_surf = font.render("Beliebige Taste drücken...", True, (150, 150, 150))
    screen.blit(hint_surf, ((sw - hint_surf.get_width()) // 2, (sh // 2) + 60))
    pygame.display.flip()

    waiting = True
    while waiting:
        raw_data = ser.readline().decode('utf-8', 'ignore').strip() if ser and ser.in_waiting > 0 else None
        for ev in pygame.event.get():
            if ev.type == pygame.KEYDOWN: waiting = False
        if raw_data and raw_data.startswith("BTN:"): waiting = False
        pygame.time.Clock().tick(10)

    if ser:
        try: 
            ser.write(b"LAMP:START:1\n")
            ser.write(b"LAMP:PLAYER:0\n")
            ser.flush()
        except: pass

def run_game(screen, ser, display, players, game_name, option_name, mode_name):
    clock = pygame.time.Clock()
    sw, sh = screen.get_width(), screen.get_height()
    font = pygame.font.SysFont("arial", int(sh * 0.03), bold=True)
    title_font = pygame.font.SysFont("arial", int(sh * 0.04), bold=True)
    small_font = pygame.font.SysFont("arial", int(sh * 0.02), bold=True)
    
    settings = load_settings()
    available_formats = ["4:3", "16:9"]
    available_mappers = get_available_mappers()
    if not settings["mapper"].endswith(".py"): settings["mapper"] += ".py"
    
    if settings["format"] not in available_formats: settings["format"] = available_formats[0]
    if settings["mapper"] not in available_mappers: settings["mapper"] = available_mappers[0] if available_mappers else "display_mapper_Vision_Dart.py"
        
    menu_items = ["Bildschirmformat", "Hardware-Mapper", "System-Update (Online)"]
    sel_item = 0
    display.clear_all()
    
    if ser:
        try: 
            ser.write(b"LAMP:START:1\n")
            ser.write(b"LAMP:PLAYER:0\n")
            ser.flush()
        except: pass

    running = True
    while running:
        raw_data = ser.readline().decode('utf-8', 'ignore').strip() if ser and ser.in_waiting > 0 else None
                
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE): running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_r: raw_data = "BTN:RED"
                elif ev.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif ev.key == pygame.K_SPACE: raw_data = "BTN:START"

        if raw_data:
            if raw_data == "BTN:START": running = False
            elif raw_data == "BTN:RED": sel_item = (sel_item + 1) % len(menu_items)
            elif raw_data == "BTN:BLUE":
                if sel_item == 0: settings["format"] = available_formats[(available_formats.index(settings["format"]) + 1) % len(available_formats)]
                elif sel_item == 1: settings["mapper"] = available_mappers[(available_mappers.index(settings["mapper"]) + 1) % len(available_mappers)]
                elif sel_item == 2: do_online_update(screen, font, sw, sh, ser)
        
        screen.fill((15, 15, 30))
        t_surf = title_font.render("SERVICE-MENÜ & EINSTELLUNGEN", True, (255, 215, 0))
        screen.blit(t_surf, ((sw - t_surf.get_width()) // 2, int(sh * 0.1)))
        
        y_pos = int(sh * 0.3)
        for i, item in enumerate(menu_items):
            color = (255, 215, 0) if i == sel_item else (255, 255, 255)
            prefix = "> " if i == sel_item else "  "
            if i == 0: value = settings["format"]
            elif i == 1: value = settings["mapper"]
            else: value = "[ BLAU drücken zum Starten ]"
            screen.blit(font.render(f"{prefix}{item}: {value}", True, color), (int(sw * 0.15), y_pos))
            y_pos += int(sh * 0.08)
            
        h_surf = small_font.render("ROT: Auswählen | BLAU: Wert ändern/Aktion | START: Speichern & Zurück", True, (150, 150, 150))
        screen.blit(h_surf, ((sw - h_surf.get_width()) // 2, int(sh * 0.8)))
        pygame.display.flip(); clock.tick(30)
        
    settings["mapper"] = settings["mapper"].replace(".py", "")
    save_settings(settings)
    
