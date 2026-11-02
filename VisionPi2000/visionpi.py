# Datei: visionpi.py
# Version: 1.1.4
# Hauptprogramm für VisionPi2000 mit integriertem Web-Streamer & serieller Hardware-Steuerung

import sys
import os

# Sicherstellen, dass das lokale paho-Modul im Spielordner gefunden wird
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import json
import pygame
import serial
import serial.tools.list_ports
import online_manager
import web_streamer  # Web-Streamer Import

VERSION = "1.1.2"

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
default_settings = {
    "format": "4:3",
    "mapper": "display_mapper_Vision_Dart",
    "branch": "stable",
    "mqtt_broker": "broker.emqx.io"
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return default_settings

settings = load_settings()

def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "ACM" in p.device or "USB" in p.device:
            return p.device
    return "/dev/ttyACM0"

def main():
    pygame.init()
    pygame.mixer.init()

    if settings.get("format") == "16:9":
        sw, sh = 1280, 720
    else:
        sw, sh = 1024, 768

    screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN)
    pygame.display.set_caption("VisionPi2000 - Custom Dartsports Engine")
    pygame.mouse.set_visible(False)

    # 1. Web-Streamer im Hintergrund starten (Port 8080)
    web_streamer.start_streaming_thread()

    # 2. GLOBALER DISPLAY-HOOK: Leitet JEDEN Bildaufbau automatisch in den Stream!
    # Funktioniert systemweit, auch wenn ein Unterspiel (z.B. game_x01.py) die Anzeige übernimmt.
    orig_flip = pygame.display.flip
    def hooked_flip():
        web_streamer.update_stream_frame(pygame.display.get_surface())
        orig_flip()
    pygame.display.flip = hooked_flip

    port = find_arduino_port()
    ser = None
    try:
        ser = serial.Serial(port, 9600, timeout=0.1)
        time.sleep(2.0)
    except Exception as e:
        print(f"Warnung: Konnte Arduino nicht unter {port} öffnen: {e}")

    font_title = pygame.font.SysFont("arial", int(sh * 0.055), bold=True)
    font_item = pygame.font.SysFont("arial", int(sh * 0.035), bold=True)
    font_hint = pygame.font.SysFont("arial", int(sh * 0.024), bold=True)

    menu_items = [
        "301 / 501 / 701 (X01)",
        "Cricket",
        "Elimination",
        "Split Score",
        "Shanghai",
        "Around the Clock",
        "Online Match (P2P MQTT)",
        "Beenden"
    ]
    selected_idx = 0
    local_players = 1

    clock = pygame.time.Clock()
    running = True

    while running:
        ser_cmd = None
        if ser and ser.in_waiting > 0:
            try:
                ser_cmd = ser.readline().decode("utf-8", "ignore").strip()
            except:
                pass

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_w]:
                    selected_idx = (selected_idx - 1) % len(menu_items)
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    selected_idx = (selected_idx + 1) % len(menu_items)
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    local_players = max(1, local_players - 1)
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    local_players = min(8, local_players + 1)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    ser_cmd = "BTN:START"
                elif event.key in [pygame.K_ESCAPE, pygame.K_p]:
                    ser_cmd = "BTN:PLAYER"

        if ser_cmd:
            if ser_cmd == "BTN:PLAYER":
                selected_idx = (selected_idx + 1) % len(menu_items)
            elif ser_cmd == "BTN:BLUE":
                local_players = (local_players % 8) + 1
            elif ser_cmd in ["BTN:START", "HIT:ENTER"]:
                choice = menu_items[selected_idx]

                if "Beenden" in choice:
                    running = False
                elif "Online Match" in choice:
                    try:
                        import game_x01
                        online_manager.run_online_lobby_and_match(
                            screen=screen,
                            ser=ser,
                            display=None,
                            local_players=local_players,
                            game_name="501",
                            option="Double Out",
                            is_host=True,
                            game_mod=game_x01,
                            settings=settings
                        )
                    except Exception as e:
                        print(f"Fehler im Online-Modus: {e}")
                else:
                    game_mod_name = online_manager.GAME_TO_FILE.get(choice.split()[0], "game_x01.py")
                    game_mod_name_base = game_mod_name.replace(".py", "")
                    try:
                        game_mod = __import__(game_mod_name_base)
                        game_mod.run_game(
                            screen=screen,
                            ser=ser,
                            display=None,
                            total_players=local_players,
                            game_name=choice.split()[0],
                            option="Standard",
                            mode_desc=choice
                        )
                    except Exception as e:
                        print(f"Konnte Spielmodul {game_mod_name_base} nicht laden: {e}")

        screen.fill((12, 14, 24))

        title_surf = font_title.render("VISION PI 2000  •  Dartsports Engine", True, (255, 215, 0))
        screen.blit(title_surf, ((sw - title_surf.get_width()) // 2, int(sh * 0.08)))

        p_surf = font_hint.render(f"Lokale Spieler: {local_players} (Tasten: Links/Rechts oder B-Taster)", True, (100, 220, 100))
        screen.blit(p_surf, ((sw - p_surf.get_width()) // 2, int(sh * 0.17)))

        start_y = int(sh * 0.25)
        item_h = int(sh * 0.075)
        for idx, item in enumerate(menu_items):
            is_sel = (idx == selected_idx)
            box_w, box_h = int(sw * 0.65), int(sh * 0.06)
            box_x, box_y = (sw - box_w) // 2, start_y + idx * item_h

            bg_col = (40, 50, 80) if is_sel else (20, 24, 38)
            border_col = (255, 215, 0) if is_sel else (60, 70, 100)
            text_col = (255, 215, 0) if is_sel else (220, 220, 220)

            pygame.draw.rect(screen, bg_col, (box_x, box_y, box_w, box_h), border_radius=10)
            pygame.draw.rect(screen, border_col, (box_x, box_y, box_w, box_h), width=2, border_radius=10)

            txt_surf = font_item.render(item, True, text_col)
            screen.blit(txt_surf, (box_x + 30, box_y + (box_h - txt_surf.get_height()) // 2))

        hint_surf = font_hint.render("Entwickelt von Oliver Müssig • Web-Stream aktiv auf Port 8080", True, (140, 150, 180))
        screen.blit(hint_surf, ((sw - hint_surf.get_width()) // 2, sh - int(sh * 0.06)))

        pygame.display.flip()
        clock.tick(30)

    if ser:
        try:
            ser.close()
        except:
            pass
    pygame.quit()

if __name__ == "__main__":
    main()
