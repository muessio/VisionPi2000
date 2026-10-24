import pygame
import time
import os

VERSION = "1.0.2"
GAMES = ["Service Menu"]
OPTIONS = ["Display & Lampen", "Matrix", "Sensoren"]

class ScreenSaver:
    def __init__(self, w, h): self.active = False
    def reset_timer(self): return False
    def check(self): return False
    def update_and_draw(self, screen, font): pass

# NEUE SIGNATUR MIT 'display'
def run_game(screen, ser, display, players, game_name, option, mode):
    screensaver = ScreenSaver(screen.get_width(), screen.get_height())
    title_font = pygame.font.SysFont("arial", 28, bold=True)
    big_font = pygame.font.SysFont("arial", 38, bold=True)
    giant_font = pygame.font.SysFont("arial", 90, bold=True)
    WHITE, HIGHLIGHT, RED_COL, GREEN = (255, 255, 255), (255, 215, 0), (180, 30, 30), (50, 255, 50)

    running = True
    clock = pygame.time.Clock()
    last_hit = "Warte auf Eingabe..."
    
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

    if option == "Display & Lampen":
        if ser:
            try:
                display.set_light(True)
                # Rohes Ansteuern ALLER Bits auf ALLER Chips (255 = alle 8 LEDs pro Spalte an)
                for c in range(10):
                    for d in range(8):
                        ser.write(f"RAW:{c}:{d}:255\n".encode('utf-8'))
                        ser.flush()
                        time.sleep(0.005)
            except: pass

    def draw_centered(surf, y):
        screen.blit(surf, ((screen.get_width() - surf.get_width()) // 2, y))

    while running:
        raw_data = None
        if ser and ser.in_waiting > 0:
            try: raw_data = ser.readline().decode('utf-8', 'ignore').strip()
            except: pass

        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: running = False
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_s: raw_data = "BTN:START"
                elif e.key == pygame.K_1: raw_data = "HIT:t20"
                elif e.key == pygame.K_2: raw_data = "HIT:-"

        if raw_data:
            if option == "Matrix" and raw_data.startswith("HIT:"):
                last_hit = raw_data.split(":")[1]
                if last_hit == "-": last_hit = "LEERES FELD (-)"

            if option == "Sensoren":
                if raw_data in sensor_timers:
                    sensor_timers[raw_data] = pygame.time.get_ticks() + 1000
                if raw_data == "BTN:COMBO": running = False
            else:
                if raw_data == "BTN:PLAYER" or raw_data == "BTN:COMBO": running = False

        screen.fill((0, 0, 0))
        draw_centered(title_font.render(f"SERVICE-MODUS: {option}", True, HIGHLIGHT), 40)

        if option == "Display & Lampen":
            draw_centered(big_font.render("Alle Segmente des Boards leuchten auf.", True, WHITE), 200)
            draw_centered(big_font.render("Beleuchtung (Relais) ist EINGESCHALTET.", True, WHITE), 280)
            draw_centered(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), 500)

        elif option == "Matrix":
            draw_centered(big_font.render("Drücke Segmente auf der Scheibe mit dem Finger.", True, WHITE), 150)
            draw_centered(title_font.render("So findest du tote Felder oder falsche Belegungen.", True, (150,150,150)), 200)
            
            c = WHITE if last_hit == "Warte auf Eingabe..." else GREEN
            draw_centered(giant_font.render(last_hit, True, c), 350)
            draw_centered(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), 600)

        elif option == "Sensoren":
            draw_centered(big_font.render("Drücke Tasten oder löse Sensoren aus:", True, WHITE), 120)
            y = 220
            for key, name in sensor_names.items():
                is_active = pygame.time.get_ticks() < sensor_timers[key]
                c = GREEN if is_active else (100, 100, 100)
                state_text = "AKTIV" if is_active else "Inaktiv"
                draw_centered(big_font.render(f"{name}: {state_text}", True, c), y)
                y += 45
            draw_centered(title_font.render("Zum Beenden: COMBO (Rot+Blau+Grau) halten", True, RED_COL), y + 40)

        pygame.display.flip()
        clock.tick(30)

    # Cleanup beim Beenden
    if option == "Display & Lampen" and ser:
        try:
            display.set_light(False)
            display.clear_all() # Stellt sicher, dass das Display im Menü wieder aus ist
        except: pass
