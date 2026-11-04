# Datei: game_service.py
# Version: 1.2.0
# Service-, WLAN- & Update-Menü im VisionPi2000 Cyber-Circuit-Design (4:3 & 16:9 Support)

import pygame
import json
import os
import sys
import glob
import subprocess
import time
import re

VERSION = "1.2.0"
GAMES = ["Service-Menü"]
OPTIONS = ["Einstellungen & Update", "WLAN & WPS", "Display & Lampen", "Matrix", "Sensoren", "Chip-Test"]

DEFAULT_SETTINGS = {
    "format": "4:3", 
    "mapper": "display_mapper_Vision_Dart", 
    "branch": "stable",
    "wifi_ssid": "",
    "wifi_password": "",
    "mqtt_broker": "broker.emqx.io",
    "mqtt_room": "VP2000-Raum-1"
}

_frame_cache = {}


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


def draw_cyber_frame(surface, x, y, w, h, cut=24):
    """Zeichnet den gecachten VisionPi2000 Cyber-Tech-Rahmen wie im Online-Manager."""
    key = (w, h, cut)
    if key not in _frame_cache:
        if len(_frame_cache) > 8:
            _frame_cache.clear()
        NEON_GREEN = (0, 255, 157)
        NEON_CYAN = (0, 216, 255)
        NEON_RED = (255, 56, 76)
        GOLD_TRACE = (180, 140, 40)
        PANEL_BG = (8, 20, 32, 225)

        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pts_local = [
            (cut, 0), (w - cut, 0), (w, cut), (w, h - cut),
            (w - cut, h), (cut, h), (0, h - cut), (0, cut)
        ]
        pygame.draw.polygon(panel_surf, PANEL_BG, pts_local)

        traces = [
            [(cut + 20, 14), (cut + 90, 14), (cut + 110, 34)],
            [(w - cut - 20, 14), (w - cut - 90, 14), (w - cut - 110, 34)],
            [(cut + 20, h - 14), (cut + 90, h - 14), (cut + 110, h - 34)],
            [(w - cut - 20, h - 14), (w - cut - 90, h - 14), (w - cut - 110, h - 34)]
        ]
        for tr in traces:
            pygame.draw.lines(panel_surf, (20, 65, 60, 160), False, tr, 2)
            pygame.draw.circle(panel_surf, (0, 255, 157, 160), tr[-1], 4, 1)

        pygame.draw.polygon(panel_surf, (0, 110, 75), pts_local, 6)
        pygame.draw.polygon(panel_surf, NEON_GREEN, pts_local, 2)

        c_len = int(h * 0.22)
        pygame.draw.line(panel_surf, NEON_RED, (0, cut), (cut, 0), 4)
        pygame.draw.line(panel_surf, NEON_RED, (0, h - cut), (cut, h), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (0, cut + 12), (0, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (0, h - cut - 12), (0, h - cut - c_len), 4)

        pygame.draw.line(panel_surf, NEON_RED, (w - cut, 0), (w, cut), 4)
        pygame.draw.line(panel_surf, NEON_RED, (w - cut, h), (w, h - cut), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (w - 1, cut + 12), (w - 1, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (w - 1, h - cut - 12), (w - 1, h - cut - c_len), 4)

        for cx, cy in [(cut + 10, 8), (w - cut - 10, 8), (cut + 10, h - 8), (w - cut - 10, h - 8)]:
            pygame.draw.circle(panel_surf, GOLD_TRACE, (cx, cy), 4)

        _frame_cache[key] = panel_surf

    surface.blit(_frame_cache[key], (x, y))


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
        except Exception:
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
        except Exception:
            pass
    else:
        try:
            run_sudo(f'cp -f {tmp_path} {boot_path}')
        except Exception:
            pass


def get_available_mappers():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = [os.path.basename(f) for f in glob.glob(os.path.join(base_dir, "display_mapper*.py"))]
    return sorted(files) if files else ["display_mapper_Vision_Dart.py"]


def get_wifi_status():
    try:
        res = subprocess.run("nmcli -t -f active,ssid dev wifi | grep '^yes'", shell=True, capture_output=True, text=True, timeout=4)
        if res.stdout:
            ssid = res.stdout.split(":", 1)[1].strip()
            ip_res = subprocess.run("hostname -I", shell=True, capture_output=True, text=True, timeout=3)
            ip = ip_res.stdout.split()[0] if ip_res.stdout else "Keine IP"
            return f"Verbunden ({ssid})  •  IP: {ip}"
    except Exception:
        pass
    return "Nicht verbunden"


def render_cyber_shell(screen, bg_img, header_img, role_font, title_text):
    """Zeichnet Hintergrund, oberes Logo und den Cyber-Rahmen und gibt (box_x, box_y, box_w, box_h) zurück."""
    sw, sh = screen.get_width(), screen.get_height()
    GOLD = (255, 205, 45)
    NEON_GREEN = (0, 255, 157)

    if bg_img:
        screen.blit(bg_img, (0, 0))
    else:
        screen.fill((6, 17, 28))

    if header_img:
        screen.blit(header_img, ((sw - header_img.get_width()) // 2, 8))
        box_y = int(sh * 0.17)
        box_h = int(sh * 0.78)
    else:
        fallback_surf = role_font.render("VisionPi2000", True, GOLD)
        screen.blit(fallback_surf, ((sw - fallback_surf.get_width()) // 2, 10))
        box_y = int(sh * 0.08)
        box_h = int(sh * 0.86)

    box_w = int(sw * 0.90)
    box_x = (sw - box_w) // 2

    draw_cyber_frame(screen, box_x, box_y, box_w, box_h, cut=22)

    head_surf = role_font.render(title_text, True, GOLD)
    screen.blit(head_surf, ((sw - head_surf.get_width()) // 2, box_y + int(box_h * 0.03)))

    line_y = box_y + int(box_h * 0.115)
    pygame.draw.line(screen, NEON_GREEN, (box_x + 35, line_y), (box_x + box_w - 35, line_y), 2)
    pygame.draw.circle(screen, GOLD, (sw // 2, line_y), 5)

    return box_x, box_y, box_w, box_h


def do_wps_connect(screen, bg_img, header_img, role_font, font, sub_font, sw, sh):
    GOLD = (255, 205, 45)
    NEON_CYAN = (0, 216, 255)
    WHITE = (255, 255, 255)

    tmp_wpa = "/tmp/wps_temp.conf"
    try:
        with open(tmp_wpa, "w") as f:
            f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\nupdate_config=1\n")
    except Exception:
        return False

    box_x, box_y, box_w, box_h = render_cyber_shell(
        screen, bg_img, header_img, role_font, "SERVICE-MODUS  •  WPS-ROUTER-KOPPLUNG AKTIV"
    )
    info1 = font.render("WPS-Suche wird initialisiert...", True, GOLD)
    screen.blit(info1, ((sw - info1.get_width()) // 2, box_y + int(box_h * 0.42)))
    pygame.display.flip()

    run_sudo("systemctl stop NetworkManager")
    run_sudo("systemctl stop wpa_supplicant")
    run_sudo("killall wpa_supplicant")
    run_sudo("rm -rf /var/run/wpa_supplicant/wlan0")
    time.sleep(0.5)
    
    run_sudo(f"wpa_supplicant -B -i wlan0 -c {tmp_wpa}")
    time.sleep(1.5)
    run_sudo("wpa_cli -i wlan0 wps_pbc")
    
    wps_ok = False
    ssid_found = ""
    psk_found = ""
    
    start_t = time.time()
    while time.time() - start_t < 60:
        pygame.event.pump()
        remaining = max(0, 60 - int(time.time() - start_t))

        box_x, box_y, box_w, box_h = render_cyber_shell(
            screen, bg_img, header_img, role_font, "SERVICE-MODUS  •  WPS-ROUTER-KOPPLUNG AKTIV"
        )
        msg1 = font.render("Bitte drücke JETZT die WPS-Taste an deinem WLAN-Router!", True, GOLD)
        msg2 = sub_font.render(f"Warte auf Router-Antwort... (Restzeit: {remaining} Sekunden)", True, NEON_CYAN)
        screen.blit(msg1, ((sw - msg1.get_width()) // 2, box_y + int(box_h * 0.38)))
        screen.blit(msg2, ((sw - msg2.get_width()) // 2, box_y + int(box_h * 0.50)))
        pygame.display.flip()

        res = subprocess.run("sudo wpa_cli -i wlan0 status", shell=True, capture_output=True, text=True)
        if "wpa_state=COMPLETED" in res.stdout:
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
            except Exception:
                pass
            break
        time.sleep(1)

    box_x, box_y, box_w, box_h = render_cyber_shell(
        screen, bg_img, header_img, role_font, "SERVICE-MODUS  •  NETZWERK WIRD KONFIGURIERT"
    )
    wait_surf = font.render("Aktiviere WLAN-Verbindung und speichere Zugangsdaten...", True, WHITE)
    screen.blit(wait_surf, ((sw - wait_surf.get_width()) // 2, box_y + int(box_h * 0.44)))
    pygame.display.flip()

    run_sudo("killall wpa_supplicant")
    run_sudo(f"rm -f {tmp_wpa}")
    run_sudo("systemctl start wpa_supplicant")
    run_sudo("systemctl start NetworkManager")
    time.sleep(4)
    
    if wps_ok and ssid_found and psk_found:
        settings = load_settings()
        settings["wifi_ssid"] = ssid_found
        settings["wifi_password"] = psk_found
        save_settings(settings)
        
        run_sudo("nmcli device disconnect wlan0")
        run_sudo("nmcli device wifi rescan")
        time.sleep(2)
        
        connect_res = subprocess.run(f'sudo nmcli device wifi connect "{ssid_found}" password "{psk_found}"', shell=True, capture_output=True)
        if connect_res.returncode != 0:
            run_sudo(f'nmcli connection up "{ssid_found}"')
            
        time.sleep(2)
        return True
        
    return False


def do_online_update(screen, bg_img, header_img, role_font, font, sub_font, sw, sh, ser, branch):
    GOLD = (255, 205, 45)
    NEON_GREEN = (0, 255, 157)
    boot_dir = get_boot_dir()
    log_file = os.path.join(boot_dir, "update_log.txt")
    
    box_x, box_y, box_w, box_h = render_cyber_shell(
        screen, bg_img, header_img, role_font, f"SYSTEM-UPDATE  •  BRANCH: {branch.upper()}"
    )
    info1 = font.render(f"Online-Update von Branch '{branch}' wird gestartet...", True, NEON_GREEN)
    info2 = sub_font.render("Bitte den Automaten NICHT ausschalten! Neustart erfolgt automatisch.", True, GOLD)
    screen.blit(info1, ((sw - info1.get_width()) // 2, box_y + int(box_h * 0.38)))
    screen.blit(info2, ((sw - info2.get_width()) // 2, box_y + int(box_h * 0.50)))
    pygame.display.flip()
    time.sleep(1.5)

    if ser:
        try:
            ser.write(b"LAMP:START:2\n")
            ser.write(b"LAMP:PLAYER:2\n")
            ser.flush()
        except Exception:
            pass

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
    
    role_font = pygame.font.SysFont("arial", int(sh * 0.028), bold=True)
    font = pygame.font.SysFont("arial", int(sh * 0.026), bold=True)
    sub_font = pygame.font.SysFont("arial", int(sh * 0.022), bold=True)
    small_font = pygame.font.SysFont("arial", int(sh * 0.019), bold=True)
    big_font = pygame.font.SysFont("arial", int(sh * 0.042), bold=True)
    giant_font = pygame.font.SysFont("arial", int(sh * 0.095), bold=True)
    
    GOLD = (255, 205, 45)
    WHITE = (255, 255, 255)
    NEON_GREEN = (0, 255, 157)
    NEON_CYAN = (0, 216, 255)
    NEON_RED = (255, 56, 76)
    
    current_settings = load_settings()
    is_16_9 = (current_settings.get("format", "4:3") == "16:9") or ((sw / float(sh)) > 1.5)
    bg_candidates = ["background_16_9.jpg", "background_16_9.png", "background_16_9.PNG"] if is_16_9 else ["background.jpg", "background.png", "Background.png", "background.PNG"]
    bg_file = find_image_file(bg_candidates)
    bg_img = None
    if bg_file:
        try:
            raw_bg = pygame.image.load(bg_file).convert()
            bg_img = pygame.transform.scale(raw_bg, (sw, sh))
            darker = pygame.Surface((sw, sh))
            darker.set_alpha(165)
            darker.fill((4, 12, 20))
            bg_img.blit(darker, (0, 0))
        except Exception:
            pass

    header_file = find_image_file(["header.png", "Header.png", "HEADER.png"])
    header_img = None
    if header_file:
        try:
            raw_h = pygame.image.load(header_file).convert_alpha()
            header_h = int(sh * 0.18)
            header_w = int(raw_h.get_width() * (header_h / raw_h.get_height()))
            header_img = pygame.transform.smoothscale(raw_h, (header_w, header_h))
        except Exception:
            pass

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
            
        menu_items = [
            ("Bildschirmformat (Auflösung)", "format"),
            ("Hardware Display-Mapper", "mapper"),
            ("GitHub Update-Kanal (Branch)", "branch"),
            ("System-Update (Online via GitHub)", "update")
        ]
        sel_item = 0
        if display:
            try: display.clear_all()
            except Exception: pass
        
        if ser:
            try: 
                ser.write(b"LAMP:START:1\n")
                ser.write(b"LAMP:PLAYER:1\n")
                ser.flush()
            except Exception:
                pass

        while running:
            raw_data = None
            if ser and ser.in_waiting > 0:
                try: raw_data = ser.readline().decode('utf-8', 'ignore').strip()
                except Exception: pass
                    
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_r: raw_data = "BTN:RED"
                    elif ev.key == pygame.K_b: raw_data = "BTN:BLUE"
                    elif ev.key == pygame.K_p: raw_data = "BTN:PLAYER"

            if raw_data:
                if raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
                    running = False
                elif raw_data == "BTN:RED":
                    sel_item = (sel_item + 1) % len(menu_items)
                elif raw_data == "BTN:BLUE":
                    if sel_item == 0:
                        settings["format"] = available_formats[(available_formats.index(settings["format"]) + 1) % len(available_formats)]
                    elif sel_item == 1:
                        settings["mapper"] = available_mappers[(available_mappers.index(settings["mapper"]) + 1) % len(available_mappers)]
                    elif sel_item == 2:
                        settings["branch"] = available_branches[(available_branches.index(settings["branch"]) + 1) % len(available_branches)]
                    elif sel_item == 3:
                        save_settings(settings)
                        do_online_update(screen, bg_img, header_img, role_font, font, sub_font, sw, sh, ser, settings["branch"])
            
            box_x, box_y, box_w, box_h = render_cyber_shell(
                screen, bg_img, header_img, role_font, "SERVICE-MENÜ  •  SYSTEM-EINSTELLUNGEN & ONLINE-UPDATE"
            )
            
            card_w = int(box_w * 0.86)
            card_x = box_x + (box_w - card_w) // 2
            start_y = box_y + int(box_h * 0.16)
            slot_h = int(box_h * 0.155)

            for i, (label_txt, key_id) in enumerate(menu_items):
                is_sel = (i == sel_item)
                cy = start_y + i * slot_h
                ch = slot_h - 12

                if key_id == "format":
                    val_str = f"{settings['format']}  ({'1920x1080 Full-HD' if settings['format'] == '16:9' else '1024x768 Klassik'})"
                elif key_id == "mapper":
                    val_str = settings["mapper"].replace(".py", "")
                elif key_id == "branch":
                    val_str = f"{settings['branch'].upper()}  ({'Empfohlene Release-Version' if settings['branch'] == 'stable' else 'Entwickler-Testversion'})"
                else:
                    val_str = "[ BLAUE TASTE DRÜCKEN ZUM STARTEN ]"

                bg_c = (14, 52, 44) if is_sel else (10, 24, 38)
                border_c = NEON_GREEN if is_sel else (40, 75, 95)
                if key_id == "update" and is_sel:
                    border_c = GOLD
                    bg_c = (48, 38, 12)

                pygame.draw.rect(screen, bg_c, (card_x, cy, card_w, ch), border_radius=10)
                pygame.draw.rect(screen, border_c, (card_x, cy, card_w, ch), width=3 if is_sel else 2, border_radius=10)

                prefix = "▶  " if is_sel else "    "
                lbl_surf = font.render(f"{prefix}{label_txt}", True, GOLD if is_sel else (190, 205, 215))
                val_col = NEON_GREEN if (is_sel and key_id != "update") else (GOLD if key_id == "update" else NEON_CYAN)
                val_surf = font.render(val_str, True, val_col)

                screen.blit(lbl_surf, (card_x + 22, cy + (ch - lbl_surf.get_height()) // 2))
                screen.blit(val_surf, (card_x + card_w - val_surf.get_width() - 24, cy + (ch - val_surf.get_height()) // 2))
                
            hint_str = "ROT: Punkt wählen   |   BLAU: Wert ändern / Update starten   |   SPIELERWECHSEL: Speichern & Zurück"
            h_surf = sub_font.render(hint_str, True, GOLD)
            draw_centered(h_surf, box_y + box_h - int(box_h * 0.075))

            pygame.display.flip()
            clock.tick(30)
            
        settings["mapper"] = settings["mapper"].replace(".py", "")
        
        if settings["format"] != old_format or settings["mapper"] != old_mapper or settings.get("branch") != old_branch:
            save_settings(settings)
            pygame.quit()
            os.execv(sys.executable, ['python3'] + sys.argv)

    elif option_name == "WLAN & WPS":
        wifi_msg = get_wifi_status()
        saved_ssid = load_settings().get("wifi_ssid", "") or "Keine SSID in settings.json hinterlegt"
        if display:
            try: display.clear_all()
            except Exception: pass
        
        if ser:
            try: 
                ser.write(b"LAMP:START:1\n")
                ser.write(b"LAMP:PLAYER:1\n")
                ser.flush()
            except Exception:
                pass

        while running:
            raw_data = None
            if ser and ser.in_waiting > 0:
                try: raw_data = ser.readline().decode('utf-8', 'ignore').strip()
                except Exception: pass
                    
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_b: raw_data = "BTN:BLUE"
                    elif ev.key == pygame.K_r: raw_data = "BTN:RED"
                    elif ev.key == pygame.K_p: raw_data = "BTN:PLAYER"

            if raw_data:
                if raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
                    running = False
                elif raw_data == "BTN:RED":
                    wifi_msg = get_wifi_status()
                    saved_ssid = load_settings().get("wifi_ssid", "") or "Keine SSID in settings.json hinterlegt"
                elif raw_data == "BTN:BLUE":
                    success = do_wps_connect(screen, bg_img, header_img, role_font, font, sub_font, sw, sh)
                    wifi_msg = get_wifi_status() if success else "WPS-Zeitüberschreitung / Kopplung fehlgeschlagen"
                    saved_ssid = load_settings().get("wifi_ssid", "") or "Keine SSID in settings.json hinterlegt"

            box_x, box_y, box_w, box_h = render_cyber_shell(
                screen, bg_img, header_img, role_font, "SERVICE-MENÜ  •  WLAN-STATUS & WPS-SCHNELLKOPPLUNG"
            )

            card_w = int(box_w * 0.84)
            card_x = box_x + (box_w - card_w) // 2
            is_connected = "Verbunden" in wifi_msg

            # Karte 1: Aktueller Verbindungsstatus
            c1_y = box_y + int(box_h * 0.18)
            c1_h = int(box_h * 0.20)
            pygame.draw.rect(screen, (12, 46, 38) if is_connected else (42, 16, 22), (card_x, c1_y, card_w, c1_h), border_radius=10)
            pygame.draw.rect(screen, NEON_GREEN if is_connected else NEON_RED, (card_x, c1_y, card_w, c1_h), width=2, border_radius=10)
            s_lbl = sub_font.render("AKTUELLER NETZWERK- & STREAM-STATUS (PORT 8080):", True, GOLD)
            s_val = font.render(wifi_msg, True, NEON_GREEN if is_connected else NEON_RED)
            screen.blit(s_lbl, ((sw - s_lbl.get_width()) // 2, c1_y + int(c1_h * 0.20)))
            screen.blit(s_val, ((sw - s_val.get_width()) // 2, c1_y + int(c1_h * 0.55)))

            # Karte 2: Gespeicherte Konfiguration auf Boot-Partition
            c2_y = box_y + int(box_h * 0.42)
            c2_h = int(box_h * 0.18)
            pygame.draw.rect(screen, (10, 24, 38), (card_x, c2_y, card_w, c2_h), border_radius=10)
            pygame.draw.rect(screen, NEON_CYAN, (card_x, c2_y, card_w, c2_h), width=2, border_radius=10)
            c_lbl = sub_font.render("DAUERHAFT GESPEICHERTES WLAN (BOOT/SETTINGS.JSON):", True, (180, 200, 215))
            c_val = font.render(f"SSID:  {saved_ssid}", True, WHITE)
            screen.blit(c_lbl, ((sw - c_lbl.get_width()) // 2, c2_y + int(c2_h * 0.20)))
            screen.blit(c_val, ((sw - c_val.get_width()) // 2, c2_y + int(c2_h * 0.55)))

            # Karte 3: WPS Button
            c3_y = box_y + int(box_h * 0.64)
            c3_h = int(box_h * 0.18)
            pygame.draw.rect(screen, (45, 36, 12), (card_x, c3_y, card_w, c3_h), border_radius=10)
            pygame.draw.rect(screen, GOLD, (card_x, c3_y, card_w, c3_h), width=3, border_radius=10)
            btn_surf = font.render("▶  [ BLAUE TASTE DRÜCKEN: WPS-KOPPLUNG MIT ROUTER STARTEN ]  ◀", True, GOLD)
            sub_wps = small_font.render("Verbindet den Automaten automatisch per Knopfdruck und speichert das Passwort.", True, WHITE)
            screen.blit(btn_surf, ((sw - btn_surf.get_width()) // 2, c3_y + int(c3_h * 0.22)))
            screen.blit(sub_wps, ((sw - sub_wps.get_width()) // 2, c3_y + int(c3_h * 0.62)))

            h_surf = sub_font.render("BLAU: WPS-Kopplung starten   |   ROT: Status aktualisieren   |   SPIELERWECHSEL: Zurück", True, GOLD)
            draw_centered(h_surf, box_y + box_h - int(box_h * 0.075))

            pygame.display.flip()
            clock.tick(30)

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
                except Exception:
                    pass
        elif option_name == "Chip-Test":
            if display:
                display.clear_all()
                display.test_single_chip(test_chip, test_digit, 0xFF)

        while running:
            raw_data = None
            if ser and ser.in_waiting > 0:
                try: raw_data = ser.readline().decode('utf-8', 'ignore').strip()
                except Exception: pass

            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE: running = False
                    elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                    elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                    elif e.key == pygame.K_g: raw_data = "BTN:GREY"
                    elif e.key == pygame.K_r: raw_data = "BTN:RED"

            if raw_data:
                if option_name == "Matrix" and raw_data.startswith("HIT:"):
                    last_hit = raw_data.split(":")[1]
                    if last_hit == "-": last_hit = "LEERES FELD (-)"
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
                    if raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
                        running = False
                else:
                    if raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
                        running = False

            box_x, box_y, box_w, box_h = render_cyber_shell(
                screen, bg_img, header_img, role_font, f"SERVICE-DIAGNOSE  •  {option_name.upper()}"
            )

            if option_name == "Display & Lampen":
                draw_centered(big_font.render("Alle 7-Segment-Anzeigen & LEDs leuchten auf.", True, NEON_GREEN), box_y + int(box_h * 0.30))
                draw_centered(font.render("Scheiben-Beleuchtung (Relais) ist EINGESCHALTET.", True, WHITE), box_y + int(box_h * 0.45))
                draw_centered(sub_font.render("SPIELERWECHSEL drücken: Test beenden & zurück ins Hauptmenü", True, GOLD), box_y + box_h - int(box_h * 0.075))

            elif option_name == "Chip-Test":
                draw_centered(big_font.render(f"MAX7219 / Shift-Register Chip: U{test_chip+1} (Index {test_chip})", True, NEON_GREEN), box_y + int(box_h * 0.28))
                draw_centered(big_font.render(f"Aktive Spalte / Digit: {test_digit} (0–7)", True, NEON_CYAN), box_y + int(box_h * 0.42))
                draw_centered(sub_font.render("BLAU: Chip wechseln   |   GRAU: Spalte wechseln   |   SPIELERWECHSEL: Zurück", True, GOLD), box_y + box_h - int(box_h * 0.075))

            elif option_name == "Matrix":
                draw_centered(font.render("Drücke Segmente auf der Dartscheibe mit dem Finger.", True, WHITE), box_y + int(box_h * 0.22))
                draw_centered(sub_font.render("Prüfung auf tote Felder oder vertauschte Matrix-Leitungen:", True, (170, 190, 205)), box_y + int(box_h * 0.32))
                c = WHITE if last_hit == "Warte auf Eingabe..." else NEON_GREEN
                draw_centered(giant_font.render(last_hit, True, c), box_y + int(box_h * 0.48))
                draw_centered(sub_font.render("SPIELERWECHSEL drücken: Matrix-Test beenden", True, GOLD), box_y + box_h - int(box_h * 0.075))

            elif option_name == "Sensoren":
                card_w = int(box_w * 0.78)
                card_x = box_x + (box_w - card_w) // 2
                y_sens = box_y + int(box_h * 0.16)
                slot_h = int(box_h * 0.098)
                for key, name in sensor_names.items():
                    is_active = pygame.time.get_ticks() < sensor_timers[key]
                    bg_c = (12, 52, 40) if is_active else (10, 22, 34)
                    bd_c = NEON_GREEN if is_active else (35, 65, 80)
                    state_text = "AUSGELÖST / AKTIV" if is_active else "Bereit (Inaktiv)"
                    pygame.draw.rect(screen, bg_c, (card_x, y_sens, card_w, slot_h - 6), border_radius=8)
                    pygame.draw.rect(screen, bd_c, (card_x, y_sens, card_w, slot_h - 6), width=2, border_radius=8)
                    s_lbl = font.render(f"{name} ({key})  •  {state_text}", True, NEON_GREEN if is_active else (150, 165, 175))
                    screen.blit(s_lbl, ((sw - s_lbl.get_width()) // 2, y_sens + (slot_h - 6 - s_lbl.get_height()) // 2))
                    y_sens += slot_h
                draw_centered(sub_font.render("SPIELERWECHSEL drücken: Sensor-Diagnose beenden", True, GOLD), box_y + box_h - int(box_h * 0.075))

            pygame.display.flip()
            clock.tick(30)

        if display:
            try:
                display.clear_all()
            except Exception:
                pass

    return "menu"
