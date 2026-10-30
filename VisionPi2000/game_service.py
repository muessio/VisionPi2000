import pygame
import json
import os
import sys
import glob
import subprocess
import time
import re

VERSION = "1.8.10"
GAMES = ["Service-Menü"]
OPTIONS = ["Einstellungen & Update", "WLAN & WPS", "Display & Lampen", "Matrix", "Sensoren", "Chip-Test"]

DEFAULT_SETTINGS = {
    "format": "4:3", 
    "mapper": "display_mapper_Vision_Dart", 
    "branch": "stable",
    "wifi_ssid": "",
    "wifi_password": ""
}

def run_sudo(cmd):
    subprocess.run(f'sudo sh -c "{cmd}" >/dev/null 2>&1', shell=True)

def get_boot_dir():
    if os.path.exists("/boot/firmware"): return "/boot/firmware"
    if os.path.exists("/boot"): return "/boot"
    return "."

def get_boot_settings_path():
    return os.path.join(get_boot_dir(), "settings.json")

def load_settings():
    boot_path = get_boot_settings_path()
    if os.path.exists(boot_path):
        try:
            with open(boot_path, "r") as f:
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
            run_sudo('sync')
            run_sudo(f'mount -o remount,ro {boot_dir}')
        except: pass
    else:
        try:
            run_sudo(f'cp -f {tmp_path} {boot_path}')
        except: pass

def get_available_mappers():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.basename(f) for f in glob.glob(os.path.join(base_dir, "display_mapper*.py"))]
    return sorted(files) if files else ["display_mapper_Vision_Dart.py"]

def get_wifi_status():
    try:
        res = subprocess.run("nmcli -t -f active,ssid dev wifi | grep '^yes'", shell=True, capture_output=True, text=True)
        if res.stdout:
            ssid = res.stdout.split(":", 1)[1].strip()
            ip_res = subprocess.run("hostname -I", shell=True, capture_output=True, text=True)
            ip = ip_res.stdout.split()[0] if ip_res.stdout else "Keine IP"
            return f"Verbunden ({ssid}) [IP: {ip}]"
    except: pass
    return "Nicht verbunden"

def do_wps_connect(screen, font, sw, sh):
    screen.fill((15, 15, 30))
    info_surf = font.render("WPS aktiv! Bitte drücke jetzt die WPS-Taste am Router...", True, (255, 215, 0))
    screen.blit(info_surf, ((sw - info_surf.get_width()) // 2, sh // 2 - 30))
    pygame.display.flip()
    
    # 1. Temporäre, beschreibbare wpa_supplicant Konfiguration in /tmp (RAM) anlegen
    tmp_wpa = "/tmp/wps_temp.conf"
    try:
        with open(tmp_wpa, "w") as f:
            f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\n")
    except:
        return False

    # 2. NetworkManager und alte wpa_supplicant Prozesse kurz stoppen, Interface freimachen
    run_sudo("systemctl stop NetworkManager")
    run_sudo("systemctl stop wpa_supplicant")
    run_sudo("killall wpa_supplicant")
    run_sudo("rm -rf /var/run/wpa_supplicant/wlan0")
    time.sleep(0.5)
    
    # 3. Eigenen wpa_supplicant mit unserer /tmp-Config starten und WPS auslösen
    run_sudo(f"wpa_supplicant -B -i wlan0 -c {tmp_wpa}")
    time.sleep(1.5)
    run_sudo("wpa_cli -i wlan0 wps_pbc")
    
    wps_ok = False
    ssid_found = ""
    psk_found = ""
    
    start_t = time.time()
    while time.time() - start_t < 60:
        pygame.event.pump()
        res = subprocess.run("sudo wpa_cli -i wlan0 status", shell=True, capture_output=True, text=True)
        if "wpa_state=COMPLETED" in res.stdout:
            # Verbindung steht! Jetzt Config in /tmp/wps_temp.conf herausschreiben lassen
            run_sudo("wpa_cli -i wlan0 save_config")
            time.sleep(0.5)
            run_sudo(f"chmod 644 {tmp_wpa}")
            try:
                with open(tmp_wpa, "r") as f:
                    content = f.read()
                m_ssid = re.search(r'ssid="([^"]+)"', content)
                m_psk = re.search(r'psk=(?:"([^"]+)"|([0-9a-fA-F]{64}))', content)
                if m_ssid and m_psk:
                    ssid_found = m_ssid.group(1)
                    psk_found = m_psk.group(1) if m_psk.group(1) else m_psk.group(2)
                    wps_ok = True
            except:
                pass
            break
        time.sleep(1)

    # 4. Temporären wpa_supplicant beenden und NetworkManager wieder sauber starten
    run_sudo("killall wpa_supplicant")
    run_sudo(f"rm -f {tmp_wpa}")
    run_sudo("systemctl start wpa_supplicant")
    run_sudo("systemctl start NetworkManager")
    
    # Warten bis NetworkManager wieder bereit ist
    time.sleep(4)
    
    if wps_ok and ssid_found and psk_found:
        # 5. SSID und extrahierten PSK dauerhaft auf der Boot-Partition in settings.json speichern
        settings = load_settings()
        settings["wifi_ssid"] = ssid_found
        settings["wifi_password"] = psk_found
        save_settings(settings)
        
        # 6. Sofort über NetworkManager mit robustem Fallback verbinden
        run_sudo("nmcli device disconnect wlan0")
        run_sudo("nmcli device wifi rescan")
        time.sleep(2)
        
        connect_res = subprocess.run(f'sudo nmcli device wifi connect "{ssid_found}" password "{psk_found}"', shell=True, capture_output=True)
        if connect_res.returncode != 0:
            run_sudo(f'nmcli connection up "{ssid_found}"')
            
        time.sleep(2)
        return True
        
    return False

def do_online_update(screen, font, sw, sh, ser, branch):
    boot_dir = get_boot_dir()
    log_file = os.path.join(boot_dir, "update_log.txt")
    
    screen.fill((15, 15, 30))
    info_surf = font.render(f"Update von Branch '{branch}' startet...", True, (255, 255, 255))
    screen.blit(info_surf, ((sw - info_surf.get_width()) // 2, sh // 2 - 30))
    pygame.display.flip()
    time.sleep(1.5)

    if ser:
        try:
            ser.write(b"LAMP:START:2\n")
            ser.write(b"LAMP:PLAYER:2\n")
            ser.flush()
        except: pass

    pygame.quit()

    cmd = (
        f'curl -s https://raw.githubusercontent.com/muessio/VisionPi2000/{branch}/Pi_Setup/Update.sh -o /tmp/Update.sh '
        f'&& sudo bash /tmp/Update.sh | tee {log_file}'
    )

    os.system(cmd)
    sys.exit(0)

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
            darker_overlay.set_alpha(160)
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
        old_branch = settings.get("branch", "stable")
        
        available_formats = ["4:3", "16:9"]
        available_mappers = get_available_mappers()
        available_branches = ["stable", "main"]
        
        if not settings.get("branch") or settings["branch"] not in available_branches:
            settings["branch"] = "stable"
            
        if not settings["mapper"].endswith(".py"): settings["mapper"] += ".py"
        
        if settings["format"] not in available_formats: settings["format"] = available_formats[0]
        if settings["mapper"] not in available_mappers: settings["mapper"] = available_mappers[0] if available_mappers else "display_mapper_Vision_Dart.py"
            
        menu_items = ["Bildschirmformat", "Hardware-Mapper", "Update-Quelle", "System-Update (Online)"]
        sel_item = 0
        if display: display.clear_all()
        
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
                    elif sel_item == 2: settings["branch"] = available_branches[(available_branches.index(settings["branch"]) + 1) % len(available_branches)]
                    elif sel_item == 3: do_online_update(screen, font, sw, sh, ser, settings["branch"])
            
            screen.fill((15, 15, 30))
            t_surf = title_font.render("EINSTELLUNGEN & UPDATE", True, HIGHLIGHT)
            draw_centered(t_surf, int(sh * 0.1))
            
            y_pos = int(sh * 0.26)
            for i, item in enumerate(menu_items):
                color = HIGHLIGHT if i == sel_item else WHITE
                prefix = "> " if i == sel_item else "  "
                if i == 0: value = settings["format"]
                elif i == 1: value = settings["mapper"]
                elif i == 2: value = settings["branch"]
                else: value = "[ BLAU drücken zum Starten ]"
                screen.blit(font.render(f"{prefix}{item}: {value}", True, color), (int(sw * 0.15), y_pos))
                y_pos += int(sh * 0.08)
                
            h_surf = small_font.render("ROT: Auswählen | BLAU: Wert ändern/Aktion | START: Speichern & Zurück", True, (150, 150, 150))
            draw_centered(h_surf, int(sh * 0.82))
            pygame.display.flip(); clock.tick(30)
            
        settings["mapper"] = settings["mapper"].replace(".py", "")
        
        if settings["format"] != old_format or settings["mapper"] != old_mapper or settings.get("branch") != old_branch:
            save_settings(settings)
            pygame.quit()
            os.execv(sys.executable, ['python3'] + sys.argv)

    elif option_name == "WLAN & WPS":
        wifi_msg = get_wifi_status()
        saved_ssid = load_settings().get("wifi_ssid", "") or "Keine hinterlegt"
        if display: display.clear_all()
        
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
                    if ev.key == pygame.K_b: raw_data = "BTN:BLUE"
                    elif ev.key == pygame.K_SPACE: raw_data = "BTN:START"

            if raw_data:
                if raw_data == "BTN:START": running = False
                elif raw_data == "BTN:BLUE":
                    success = do_wps_connect(screen, font, sw, sh)
                    wifi_msg = get_wifi_status() if success else "WPS Zeitüberschreitung / Fehler"
                    saved_ssid = load_settings().get("wifi_ssid", "") or "Keine hinterlegt"

            screen.fill((15, 15, 30))
            t_surf = title_font.render("WLAN & WPS EINSTELLUNGEN", True, HIGHLIGHT)
            draw_centered(t_surf, int(sh * 0.15))
            
            stat_surf = font.render(f"Status: {wifi_msg}", True, GREEN if "Verbunden" in wifi_msg else WHITE)
            draw_centered(stat_surf, int(sh * 0.32))
            
            cfg_surf = small_font.render(f"Gespeichert in settings.json: {saved_ssid}", True, (180, 180, 180))
            draw_centered(cfg_surf, int(sh * 0.40))
            
            btn_surf = font.render("[ BLAU drücken: WPS-Kopplung starten ]", True, HIGHLIGHT)
            draw_centered(btn_surf, int(sh * 0.54))
            
            h_surf = small_font.render("BLAU: WPS starten | START: Zurück ins Menü", True, (150, 150, 150))
            draw_centered(h_surf, int(sh * 0.82))
            pygame.display.flip(); clock.tick(30)

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
                    elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                    elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                    elif e.key == pygame.K_g: raw_data = "BTN:GREY"
                    elif e.key == pygame.K_r: raw_data = "BTN:RED"
                    elif e.key == pygame.K_SPACE: raw_data = "BTN:START"

            if raw_data:
                if option_name == "Matrix" and raw_data.startswith("HIT:"):
                    last_hit = raw_data.split(":")[1]
                    if last_hit == "-": last_hit = "LEERES FELD (-)"
                    if raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
                        running = False
                elif option_name == "Matrix" and raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
                    running = False

                elif option_name == "Chip-Test":
                    if raw_data == "BTN:BLUE":
                        test_chip = (test_chip + 1) % 9
                        if display: display.test_single_chip(test_chip, test_digit, 0xFF)
                    elif raw_data == "BTN:GREY":
                        test_digit = (test_digit + 1) % 8
                        if display: display.test_single_chip(test_chip, test_digit, 0xFF)
                    elif raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
                        running = False

                elif option_name == "Sensoren":
                    if raw_data in sensor_timers:
                        sensor_timers[raw_data] = pygame.time.get_ticks() + 1000
                    if raw_data == "BTN:COMBO": running = False
                else:
                    if raw_data in ["BTN:PLAYER", "BTN:COMBO"]: running = False

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

        if display:
            try:
                display.clear_all()
            except: pass

    return "menu"
