# Datei: visionpi.py
# Version: 1.1.4
# Hauptprogramm für VisionPi2000 mit integriertem Web-Streamer & serieller Hardware-Steuerung

import sys
import os

# Sicherstellen, dass das lokale paho-Modul im Spielordner gefunden wird
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import time
import json
import pygame
import serial
import serial.tools.list_ports
import online_manager
import web_streamer

VERSION = "1.1.4"

SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
default_settings = {
    "format": "4:3",
    "mapper": "display_mapper_Vision_Dart",
    "branch": "stable",
    "mqtt_broker": "broker.emqx.io"
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default_settings.items():
                    data.setdefault(k, v)
                return data
        except Exception:
            pass
    return default_settings.copy()


settings = load_settings()


def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        if "Arduino" in p.description or "ACM" in p.device or "USB" in p.device:
            return p.device
    return "/dev/ttyACM0"


def init_display_mapper(ser):
    """Lädt den in settings.json konfigurierten 7-Segment Display-Mapper."""
    mapper_name = settings.get("mapper", "display_mapper_Vision_Dart")
    try:
        mapper_mod = __import__(mapper_name)
        if hasattr(mapper_mod, "DisplayMapper"):
            return mapper_mod.DisplayMapper(ser)
        elif hasattr(mapper_mod, "VisionDisplay"):
            return mapper_mod.VisionDisplay(ser)
    except Exception as e:
        print(f"Hinweis: Display-Mapper '{mapper_name}' nicht geladen ({e})")
    return None


def main():
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass

    if settings.get("format") == "16:9":
        sw, sh = 1280, 720
    else:
        sw, sh = 1024, 768

    screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN)
    pygame.display.set_caption("VisionPi2000 - Custom Dartsports Engine")
    pygame.mouse.set_visible(False)

    # Optionales Hintergrundbild (JPG bevorzugt)
    bg_image = None
    for bg_name in ["background.jpg", "bg.jpg", "hintergrund.jpg"]:
        bg_path = os.path.join(BASE_DIR, bg_name)
        if os.path.exists(bg_path):
            try:
                loaded_bg = pygame.image.load(bg_path).convert()
                bg_image = pygame.transform.scale(loaded_bg, (sw, sh))
                break
            except Exception:
                pass

    # 1. Web-Streamer im Hintergrund starten (Port 8080)
    web_streamer.start_streaming_thread()

    # 2. GLOBALER DISPLAY-HOOK: Leitet JEDEN Bildaufbau automatisch in den Stream!
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

    display = init_display_mapper(ser)

    font_title = pygame.font.SysFont("arial", int(sh * 0.050), bold=True)
    font_item = pygame.font.SysFont("arial", int(sh * 0.032), bold=True)
    font_hint = pygame.font.SysFont("arial", int(sh * 0.022), bold=True)

    # Saubere Zuordnung von Menü-Eintrag -> (game_name, default_option)
    menu_entries = [
        ("301 Single Out", "301", "Single Out"),
        ("501 Double Out", "501", "Double Out"),
        ("701 Master Out", "701", "Master Out"),
        ("Cricket", "Cricket", "Standard"),
        ("Elimination", "Elimination", "301 Double Out"),
        ("Split Score", "Split Score", "Standard"),
        ("Shanghai", "Shanghai", "Standard"),
        ("Around the Clock", "Around the Clock", "Standard"),
        ("Online Match: HOST (Lobby öffnen)", "ONLINE_HOST", "Double Out"),
        ("Online Match: GAST (Lobby beitreten)", "ONLINE_GUEST", "Double Out"),
        ("Beenden", "EXIT", "")
    ]

    selected_idx = 1  # Startet standardmäßig auf 501 Double Out
    local_players = 1
    vs_berry = False  # Computergegner BullsEye-Berry

    clock = pygame.time.Clock()
    running = True

    while running:
        # Regel: Bei 8 menschlichen Spielern ist BullsEye-Berry gesperrt (Max 8 Slots auf dem Display)
        if local_players >= 8 and vs_berry:
            vs_berry = False

        ser_cmd = None
        if ser and ser.in_waiting > 0:
            try:
                ser_cmd = ser.readline().decode("utf-8", "ignore").strip()
            except Exception:
                pass

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_w]:
                    selected_idx = (selected_idx - 1) % len(menu_entries)
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    selected_idx = (selected_idx + 1) % len(menu_entries)
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    local_players = max(1, local_players - 1)
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    local_players = min(8, local_players + 1)
                elif event.key == pygame.K_b:
                    if local_players < 8:
                        vs_berry = not vs_berry
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    ser_cmd = "BTN:START"
                elif event.key in [pygame.K_ESCAPE, pygame.K_p]:
                    ser_cmd = "BTN:PLAYER"

        if ser_cmd:
            if ser_cmd == "BTN:PLAYER":
                selected_idx = (selected_idx + 1) % len(menu_entries)
            elif ser_cmd == "BTN:BLUE":
                local_players = (local_players % 8) + 1
            elif ser_cmd == "BTN:RED":
                if local_players < 8:
                    vs_berry = not vs_berry
            elif ser_cmd in ["BTN:START", "HIT:ENTER"]:
                label, g_name, g_opt = menu_entries[selected_idx]

                if g_name == "EXIT":
                    running = False

                elif g_name in ["ONLINE_HOST", "ONLINE_GUEST"]:
                    is_host_mode = (g_name == "ONLINE_HOST")
                    try:
                        import game_x01
                        online_manager.run_online_lobby_and_match(
                            screen=screen,
                            ser=ser,
                            display=display,
                            local_players=local_players,
                            game_name="501",
                            option="Double Out",
                            is_host=is_host_mode,
                            game_mod=game_x01,
                            settings=settings
                        )
                    except Exception as e:
                        print(f"Fehler im Online-Modus: {e}")

                else:
                    # Korrekte Spielmodul-Datei über den vollen Spielnamen ermitteln
                    game_file = online_manager.GAME_TO_FILE.get(g_name, "game_x01.py")
                    game_mod_name = game_file.replace(".py", "")
                    mode_str = "BullsEye-Berry" if (vs_berry and local_players < 8) else "Normales Spiel"
                    try:
                        game_mod = __import__(game_mod_name)
                        game_mod.run_game(
                            screen,
                            ser,
                            display,
                            local_players,
                            g_name,
                            g_opt,
                            mode_str
                        )
                    except Exception as e:
                        print(f"Konnte Spielmodul {game_mod_name} nicht starten: {e}")

        # Hintergrund zeichnen
        if bg_image:
            screen.blit(bg_image, (0, 0))
        else:
            screen.fill((12, 14, 24))

        # Titel & Status-Header
        title_surf = font_title.render("VISION PI 2000  •  Dartsports Engine", True, (255, 215, 0))
        screen.blit(title_surf, ((sw - title_surf.get_width()) // 2, int(sh * 0.04)))

        berry_txt = "  |  + BullsEye-Berry (KI)" if vs_berry else "  |  Modus: Normales Spiel"
        if local_players >= 8:
            berry_txt = "  |  Max. 8 Spieler (BullsEye-Berry deaktiviert)"
        p_surf = font_hint.render(
            f"Spieler: {local_players}{berry_txt}   (BLAU: Spielerzahl | ROT/Taste B: KI)",
            True,
            (100, 230, 110)
        )
        screen.blit(p_surf, ((sw - p_surf.get_width()) // 2, int(sh * 0.11)))

        # Kompakte Menüliste
        start_y = int(sh * 0.16)
        item_h = int(sh * 0.068)
        for idx, (label, _, _) in enumerate(menu_entries):
            is_sel = (idx == selected_idx)
            box_w, box_h = int(sw * 0.72), int(sh * 0.056)
            box_x, box_y = (sw - box_w) // 2, start_y + idx * item_h

            bg_col = (40, 52, 85) if is_sel else (20, 24, 38)
            border_col = (255, 215, 0) if is_sel else (60, 70, 100)
            text_col = (255, 215, 0) if is_sel else (225, 225, 225)

            pygame.draw.rect(screen, bg_col, (box_x, box_y, box_w, box_h), border_radius=10)
            pygame.draw.rect(screen, border_col, (box_x, box_y, box_w, box_h), width=2, border_radius=10)

            txt_surf = font_item.render(label, True, text_col)
            screen.blit(txt_surf, (box_x + 28, box_y + (box_h - txt_surf.get_height()) // 2))

        # Footer mit Branding & Stream-Hinweis
        hint_surf = font_hint.render(
            "Custom Dartsports Engine • Developed by Oliver Müssig  |  Live-Stream: Port 8080",
            True,
            (150, 160, 190)
        )
        screen.blit(hint_surf, ((sw - hint_surf.get_width()) // 2, sh - int(sh * 0.045)))

        pygame.display.flip()
        clock.tick(30)

    if ser:
        try:
            ser.close()
        except Exception:
            pass
    pygame.quit()


if __name__ == "__main__":
    main()
