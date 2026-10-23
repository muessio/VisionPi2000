import pygame
import time
import os

VERSION = "1.0.0"
GAMES = ["Service Menu"]
OPTIONS = ["Display & Lampen", "Matrix", "Sensoren"]

class ScreenSaver:
    # Dummy, damit das Service-Menü nicht vom Screensaver unterbrochen wird
    def __init__(self, w, h): self.active = False
    def reset_timer(self): return False
    def check(self): return False
    def update_and_draw(self, screen, font): pass

def run_game(screen, ser, players, game_name, option, mode):
    screensaver = ScreenSaver(screen.get_width(), screen.get_height())
    title_font = pygame.font.SysFont("arial", 28, bold=True)
    big_font = pygame.font.SysFont("arial", 38, bold=True)
    giant_font = pygame.font.SysFont("arial", 90, bold=True)
    WHITE, HIGHLIGHT, RED_COL, GREEN = (255, 255, 255), (255, 215, 0), (180, 30, 30), (50, 255, 50)

    running = True
    clock = pygame.time.Clock()

    last_hit = "Warte auf Eingabe..."
    
    # Speicher für die Sensoren-Zustände (leuchten für 1 Sekunde grün auf, wenn getriggert)
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

    # STARTAKTION: Alles einschalten für Display-Test
    if option == "Display & Lampen":
        if ser:
            try:
                ser.write(b"LIGHT:ON\n")
                ser.flush()
                # Schicke auf alle Displays die Zahl 8 (aktiviert alle 7 Leuchtsegmente)
                for c in range(10):
                    for d in range(8):
                        ser.write(f"DISP:{c}:{d}:8\n".encode('utf-8'))
                        ser.flush()
                        time.sleep(0.005)
            except: pass

    while running:
        raw_data = None
        if ser and ser.in_waiting > 0:
            try: raw_data = ser.readline().decode('utf-8', 'ignore').strip()
            except: pass

        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                # Tastatur-Simulation für Tests ohne Arduino
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_s: raw_data = "BTN:START"
                elif e.key == pygame.K_1: raw_data = "HIT:t20"
                elif e.key == pygame.K_2: raw_data = "HIT:-"

        if raw_data:
            # MATRIX-LOGIK
            if option == "Matrix" and raw_data.startswith("HIT:"):
                last_hit = raw_data.split(":")[1]
                if last_hit == "-": 
                    last_hit = "LEERES FELD (-)"

            # SENSOREN-LOGIK
            if option == "Sensoren":
                if raw_data in sensor_timers:
                    sensor_timers[raw_data] = pygame.time.get_ticks() + 1000

            # BEENDEN LOGIK
            if option == "Sensoren":
                # Da wir den Spielerwechsel-Taster testen wollen, beenden wir hier über die Tasten-Kombi
                if raw_data == "BTN:COMBO": running = False
            else:
                # In den anderen Menüs normal mit Spielerwechsel beenden
                if raw_data == "BTN:PLAYER" or raw_data == "BTN:COMBO": running = False

        # --- ZEICHNEN ---
        screen.fill((0, 0, 0))
        screen.blit(title_font.render(f"SERVICE-MODUS: {option}", True, HIGHLIGHT), (40, 40))

        if option == "Display & Lampen":
            screen.blit(big_font.render("Alle Segmente zeigen '8'.", True, WHITE), (200, 200))
            screen.blit(big_font.render("Beleuchtung (Relais) ist EINGESCHALTET.", True, WHITE), (200, 280))
            screen.blit(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), (200, 500))

        elif option == "Matrix":
            screen.blit(big_font.render("Drücke Segmente auf der Dartscheibe mit dem Finger.", True, WHITE), (100, 150))
            screen.blit(title_font.render("So findest du tote Felder oder falsche Belegungen im Code.", True, (150,150,150)), (100, 200))
            
            c = WHITE if last_hit == "Warte auf Eingabe..." else GREEN
            screen.blit(giant_font.render(last_hit, True, c), (100, 350))
            screen.blit(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), (100, 600))

        elif option == "Sensoren":
            screen.blit(big_font.render("Drücke Tasten oder löse Sensoren aus:", True, WHITE), (150, 120))
            y = 220
            for key, name in sensor_names.items():
                is_active = pygame.time.get_ticks() < sensor_timers[key]
                c = GREEN if is_active else (100, 100, 100)
                state_text = "AKTIV" if is_active else "Inaktiv"
                screen.blit(big_font.render(f"{name}: {state_text}", True, c), (200, y))
                y += 45
            screen.blit(title_font.render("Zum Beenden: ROTE, BLAUE und GRAUE Taste gedrückt halten (COMBO)", True, RED_COL), (100, y + 40))

        pygame.display.flip()
        clock.tick(30)

    # Cleanup beim Beenden
    if option == "Display & Lampen" and ser:
        try:
            ser.write(b"LIGHT:OFF\n")
            ser.flush()
        except: pass
