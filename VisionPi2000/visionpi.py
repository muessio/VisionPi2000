import pygame
import json
import os
import sys
import subprocess
import time

import game_service

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
    DEFAULT_SETTINGS = {
        "format": "4:3", 
        "mapper": "display_mapper_Vision_Dart", 
        "branch": "stable",
        "wifi_ssid": "",
        "wifi_password": ""
    }
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
    return DEFAULT_SETTINGS.copy()

def ensure_wifi_connection(settings):
    ssid = settings.get("wifi_ssid", "")
    if not ssid:
        return
    
    try:
        # Prüfen, ob NetworkManager bereits mit der korrekten SSID verbunden ist
        res = subprocess.run("nmcli -t -f active,ssid dev wifi | grep '^yes'", shell=True, capture_output=True, text=True)
        if ssid not in res.stdout:
            print(f"Erzwinge Verbindung mit WLAN aus settings.json: {ssid}...")
            # NetworkManager anweisen, sich mit der in der JSON hinterlegten SSID zu verbinden
            subprocess.run(f"nmcli device wifi connect '{ssid}'", shell=True)
    except Exception as e:
        print(f"WLAN Auto-Connect Fehler: {e}")

def main():
    pygame.init()
    settings = load_settings()
    
    # WLAN-Verbindung beim Start automatisch erzwingen falls in settings.json hinterlegt
    ensure_wifi_connection(settings)

    is_16_9 = settings.get("format", "4:3") == "16:9"
    if is_16_9:
        screen = pygame.display.set_mode((1280, 720), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((1024, 768), pygame.FULLSCREEN)
        
    pygame.mouse.set_visible(False)
    
    # Hardware-Mapper laden
    display = None
    mapper_name = settings.get("mapper", "display_mapper_Vision_Dart")
    try:
        mapper_mod = __import__(mapper_name)
        display = mapper_mod.DisplayMapper()
    except Exception as e:
        print(f"Konnte Mapper {mapper_name} nicht laden: {e}")

    # Serielle Schnittstelle für Arduino Mega / Matrix / Taster initialisieren
    ser = None
    for port in ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/serial0']:
        try:
            import serial
            ser = serial.Serial(port, 115200, timeout=0.01)
            print(f"Serielle Verbindung auf {port} hergestellt.")
            break
        except:
            pass
    if not ser:
        print("Keine serielle Schnittstelle gefunden (Simulationsmodus aktiv).")

    current_game = "Service-Menü"
    current_option = "Einstellungen & Update"
    current_mode = "Standard"

    running = True
    while running:
        # Übergabe an den Game- bzw. Service-Menü-Service
        result = game_service.run_game(screen, ser, display, 1, current_game, current_option, current_mode)
        if not result:
            running = False
            
    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
