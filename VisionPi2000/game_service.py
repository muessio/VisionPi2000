import pygame
import json
import os
import sys
import glob
import subprocess
import time

VERSION = "1.7.0"
GAMES = ["Service-Menü"]
OPTIONS = ["Einstellungen & Update", "Display & Lampen", "Matrix", "Sensoren", "Chip-Test"]

DEFAULT_SETTINGS = {"format": "4:3", "mapper": "display_mapper_Vision_Dart"}

def run_sudo(cmd):
    subprocess.run(f'sudo sh -c "{cmd}" >/dev/null 2>&1', shell=True)

def get_boot_dir():
    if os.path.exists("/boot/firmware"): return "/boot/firmware"
    if os.path.exists("/boot"): return "/boot"
    return "."

def get_local_settings_path():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

def get_boot_settings_path():
    return os.path.join(get_boot_dir(), "settings.json")

def load_settings():
    boot_path = get_boot_settings_path()
    local_path = get_local_settings_path()
    
    for path in [boot_path, local_path]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        for k, v in DEFAULT_SETTINGS.items():
                            if k not in data: data[k] = v
                        return data
            except:
                pass
    save_settings(DEFAULT_SETTINGS.copy())
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    boot_dir = get_boot_dir()
    boot_path = get_boot_settings_path()
    local_path = get_local_settings_path()
    tmp_path = "/tmp/visionpi_settings.json"

    try:
        with open(tmp_path, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print("TMP Write Error:", e)
        return

    if boot_dir != ".":
        try:
            run_sudo(f'mount -o remount,rw {boot_dir}')
            run_sudo(f'cp -f {tmp_path} {boot_path}')
        except: pass

    try:
        run_sudo(f'rm -f {local_path}')
        run_sudo(f'cp -f {tmp_path} {local_path}')
        run_sudo(f'chown visionpi2000:visionpi2000 {local_path}')
    except: pass

def get_available_mappers():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.basename(f) for f in glob.glob(os.path.join(base_dir, "display_mapper*.py"))]
    return sorted(files) if files else ["display_mapper_Vision_Dart.py"]

def do_online_update(screen, font, sw, sh, ser):
    boot_dir = get_boot_dir()
    log_file = os.path.join(boot_dir, "update_log.txt")
    
    screen.fill((15, 15, 30))
    info_surf = font.render("Online-Update wird vorbereitet...", True, (255, 255, 255))
    screen.blit(info_surf, ((sw - info_surf.get_width()) // 2, sh // 2 - 30))
    pygame.display.flip()

    if ser:
        try:
            ser.write(b"LAMP:START:2\n")
            ser.write(b"LAMP:PLAYER:2\n")
            ser.flush()
        except: pass

    # Arbeitsverzeichnis erzwingen, damit curl & private_Update.sh im korrekten Pfad arbeiten
    target_cwd = "/home/visionpi2000/VisionPi2000"
    if not os.path.exists(target_cwd):
        target_cwd = "."

    inner_cmd = (
        'curl -H "Authorization: token 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" '
        'https://raw.githubusercontent.com/muessio/VisionPi2000/main/Pi_Setup/private_Update.sh -o private_Update.sh '
        '&& chmod +x private_Update.sh '
        '&& sudo ./private_Update.sh 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'
    )
    cmd = f'cd {target_cwd} && sudo sh -c "{inner_cmd}" > {log_file} 2>&1'

    screen.fill((15, 15, 30))
    result_surf = font.render("Update läuft! System startet gleich automatisch neu...", True, (255, 215, 0))
    screen.blit(result_surf, ((sw - result_surf.get_width()) // 2, sh // 2))
    pygame.display.flip()

    try:
        subprocess.Popen(cmd, shell=True, stdin=None, stdout=None, stderr=None)
    except Exception as e:
        print("Update Error:", e)

    start_wait = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start_wait < 120000:
        pygame.time.Clock().tick(10)
        pygame.event.pump() 
        if ser:
            try:
                ser.write(b"LAMP:START:2\n")
            except: pass

def run_game(screen, ser, display, players, game_name, option_name, mode_name):
    clock = pygame.time.Clock()
    sw, sh = screen.get_width(), screen.get_height()
    
    font = pygame.font.SysFont("arial", int(sh * 0.03), bold=True)
    title_font = pygame.font.SysFont("arial", int(sh * 0.04), bold=True)
    small_font = pygame.font.SysFont("arial", int(sh * 0.02), bold=True)
    big_font = pygame.font.SysFont("arial", int(sh * 0.05), bold=True)
    giant_font = pygame.font.SysFont("arial", int(sh * 0.1), bold=True)
    
    WHITE, HIGHLIGHT, RED_COL, GREEN = (255, 255, 255), (255, 215, 0), (180, 30, 30), (50, 255, 50)
    
    current_settings = load_settings()
    is_16_9 = current_settings.get("format", "4:3") == "16:9"
    bg_file = "background_16_9.png" if is_16_9 else "background.png"
    bg_img = None
    if os.path.exists(bg_file):
        try:
            raw_bg = pygame.image.load(bg_file).convert()
            bg_img = pygame.transform.scale(raw_bg, (sw, sh))
            darker_overlay = pygame.Surface((sw, sh))
            darker_overlay.set_alpha(120)
            darker_overlay.fill((0, 0, 0))
            bg_img.blit(darker_overlay, (0, 0))
        except: pass

    def draw_centered(surf, y):
        screen.blit(surf, ((sw - surf.get_width()) // 2, y))

    running = True

    if option_name == "Einstellungen & Update":
        settings = load_settings()
        old_format = settings.get("format", "4:3")
        old_mapper = settings.get("mapper", "display_mapper_Vision_Dart").replace(".py", "")
        
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
            t_surf = title_font.render("EINSTELLUNGEN & UPDATE", True, HIGHLIGHT)
            draw_centered(t_surf, int(sh * 0.1))
            
            y_pos = int(sh * 0.3)
            for i, item in enumerate(menu_items):
                color = HIGHLIGHT if i == sel_item else WHITE
                prefix = "> " if i == sel_item else "  "
                if i == 0: value = settings["format"]
                elif i == 1: value = settings["mapper"]
                else: value = "[ BLAU drücken zum Starten ]"
                screen.blit(font.render(f"{prefix}{item}: {value}", True, color), (int(sw * 0.15), y_pos))
                y_pos += int(sh * 0.08)
                
            h_surf = small_font.render("ROT: Auswählen | BLAU: Wert ändern/Aktion | START: Speichern & Zurück", True, (150, 150, 150))
            draw_centered(h_surf, int(sh * 0.8))
            pygame.display.flip(); clock.tick(30)
            
        settings["mapper"] = settings["mapper"].replace(".py", "")
        save_settings(settings)

        if settings["format"] != old_format or settings["mapper"] != old_mapper:
            pygame.quit()
            os.execv(sys.executable, ['python3'] + sys.argv)

    else:
        last_hit = "Warte auf Eingabe..."
        test_chip = 0
        test_digit = 0
        
        sensor_timers = {"BTN:RED": 0, "BTN:BLUE": 0, "BTN:GREY": 0, "BTN:START": 0, "BTN:PLAYER": 0, "MISS:1": 0, "IR:DETECT": 0}
        sensor_names = {
            "BTN:RED": "Roter Taster", 
            "BTN:BLUE": "Blauer Taster", 
            "BTN:GREY": "Grauer Taster", 
            "BTN:START": "Start Taster", 
            "BTN:PLAYER": "Spielerwechsel", 
            "MISS:1": "Fehlwurf (Piezo)", 
            "IR:DETECT": "Infrarot-Sensor"
        }

        if option_name == "Display & Lampen":
            if display:
                try:
                    display.set_light(True)
                    for c in range(9):
                        for d in range(8):
                            display.buffer[c][d] = 255
                    display.update()
                except: pass
        elif option_name == "Chip-Test":
            if display:
                display.clear_all()
                display.test_single_chip(test_chip, test_digit, 0xFF)

        while running:
            raw_data = None
            if ser and ser.in_waiting > 0:
                try: raw_data = ser.readline().decode('utf-8', 'ignore').strip()
                except: pass

            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: running = False

            if raw_data:
                if option_name == "Matrix" and raw_data.startswith("HIT:"):
                    last_hit = raw_data.split(":")[1]
                    if last_hit == "-": last_hit = "LEERES FELD (-)"

                elif option_name == "Chip-Test":
                    if raw_data == "BTN:BLUE":
                        test_chip = (test_chip + 1) % 9
                        if display: display.test_single_chip(test_chip, test_digit, 0xFF)
                    elif raw_data == "BTN:GREY":
                        test_digit = (test_digit + 1) % 8
                        if display: display.test_single_chip(test_chip, test_digit, 0xFF)
                    elif raw_data == "BTN:PLAYER":
                        running = False

                elif option_name == "Sensoren":
                    if raw_data in sensor_timers:
                        sensor_timers[raw_data] = pygame.time.get_ticks() + 1000
                    if raw_data == "BTN:COMBO": running = False
                else:
                    if raw_data == "BTN:PLAYER" or raw_data == "BTN:COMBO": running = False

            if bg_img: screen.blit(bg_img, (0, 0))
            else: screen.fill((0, 0, 0))
            
            draw_centered(title_font.render(f"SERVICE-MODUS: {option_name}", True, HIGHLIGHT), int(sh*0.05))

            if option_name == "Display & Lampen":
                draw_centered(big_font.render("Alle Segmente des Boards leuchten auf.", True, WHITE), int(sh*0.25))
                draw_centered(big_font.render("Beleuchtung (Relais) ist EINGESCHALTET.", True, WHITE), int(sh*0.35))
                draw_centered(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), int(sh*0.7))

            elif option_name == "Chip-Test":
                draw_centered(big_font.render(f"Teste MAX7219 Chip: U{test_chip+1} (Index {test_chip})", True, GREEN), int(sh*0.25))
                draw_centered(big_font.render(f"Spalte / Digit: {test_digit} (0-7)", True, WHITE), int(sh*0.35))
                draw_centered(small_font.render("Blauer Taster: Chip wechseln | Grauer Taster: Spalte wechseln", True, HIGHLIGHT), int(sh*0.5))
                draw_centered(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), int(sh*0.7))

            elif option_name == "Matrix":
                draw_centered(big_font.render("Drücke Segmente auf der Scheibe mit dem Finger.", True, WHITE), int(sh*0.2))
                draw_centered(title_font.render("So findest du tote Felder oder falsche Belegungen.", True, (150,150,150)), int(sh*0.3))
                c = WHITE if last_hit == "Warte auf Eingabe..." else GREEN
                draw_centered(giant_font.render(last_hit, True, c), int(sh*0.5))
                draw_centered(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), int(sh*0.8))

            elif option_name == "Sensoren":
                draw_centered(big_font.render("Drücke Taster oder löse Sensoren aus:", True, WHITE), int(sh*0.15))
                y_sens = int(sh*0.28)
                for key, name in sensor_names.items():
                    is_active = pygame.time.get_ticks() < sensor_timers[key]
                    c = GREEN if is_active else (100, 100, 100)
                    state_text = "AKTIV" if is_active else "Inaktiv"
                    draw_centered(big_font.render(f"{name}: {state_text}", True, c), y_sens)
                    y_sens += int(sh*0.07)
                draw_centered(title_font.render("Zum Beenden: COMBO (Rot+Blau+Grau) halten", True, RED_COL), y_sens + int(sh*0.05))

            pygame.display.flip()
            clock.tick(30)

        if ser:
            try:
                display.set_light(False)
                display.clear_all()
            except: pass
        
