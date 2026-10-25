import pygame
import time
import os

VERSION = "1.0.5"
GAMES = ["Service Menu"]
OPTIONS = ["Display & Lampen", "Matrix", "Sensoren", "Chip-Test"]  # NEU: "Chip-Test" hinzugefügt!

class ScreenSaver:
    def __init__(self, w, h): self.active = False
    def reset_timer(self): return False
    def check(self): return False
    def update_and_draw(self, screen, font): pass

def run_game(screen, ser, display, players, game_name, option, mode):
    screensaver = ScreenSaver(screen.get_width(), screen.get_height())
    title_font = pygame.font.SysFont("arial", 28, bold=True)
    big_font = pygame.font.SysFont("arial", 38, bold=True)
    small_font = pygame.font.SysFont("arial", 22, bold=True)
    giant_font = pygame.font.SysFont("arial", 90, bold=True)
    WHITE, HIGHLIGHT, RED_COL, GREEN = (255, 255, 255), (255, 215, 0), (180, 30, 30), (50, 255, 50)

    running = True
    clock = pygame.time.Clock()
    last_hit = "Warte auf Eingabe..."
    
    # Variablen für den neuen Chip-Einzeltest
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

    if option == "Display & Lampen":
        if display:
            try:
                display.set_light(True)
                # Sauberes, fehlerfreies Füllen über den Mapper (Chips 0 bis 8)
                for c in range(9):
                    for d in range(8):
                        display.buffer[c][d] = 255
                display.update()
            except: pass
    elif option == "Chip-Test":
        if display:
            display.clear_all()
            display.test_single_chip(test_chip, test_digit, 0xFF)

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
                elif option == "Chip-Test":
                    if e.key == pygame.K_UP:
                        test_chip = (test_chip + 1) % 9
                        display.test_single_chip(test_chip, test_digit, 0xFF)
                    elif e.key == pygame.K_DOWN:
                        test_chip = (test_chip - 1) % 9
                        display.test_single_chip(test_chip, test_digit, 0xFF)
                    elif e.key == pygame.K_RIGHT:
                        test_digit = (test_digit + 1) % 8
                        display.test_single_chip(test_chip, test_digit, 0xFF)
                    elif e.key == pygame.K_LEFT:
                        test_digit = (test_digit - 1) % 8
                        display.test_single_chip(test_chip, test_digit, 0xFF)

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

        elif option == "Chip-Test":
            draw_centered(big_font.render(f"Teste MAX7219 Chip: U{test_chip+1} (Index {test_chip})", True, GREEN), 150)
            draw_centered(big_font.render(f"Spalte / Digit: {test_digit} (0-7)", True, WHITE), 220)
            draw_centered(small_font.render("Nutze PFEIL HOCH/RUNTER für Chip, RECHTS/LINKS für Spalte", True, HIGHLIGHT), 320)
            draw_centered(title_font.render("Zum Beenden: Spielerwechsel-Taste drücken", True, RED_COL), 550)

        elif option == "Matrix":
            draw_centered(big_font.render("Drücke Segmente auf der Scheibe mit dem Finger.", True, WHITE), 150)
            draw_centered(title_font.render("So findest du tote Felder oder falsche Belegungen.", True, (150,150,150)), 200)
            
            c = WHITE if last_hit == "Warte auf Eingabe..." else GREEN
            draw_centered(giant_font.giant_font.render(last_hit, True, c) if hasattr(giant_font, 'giant_font') else giant_font.render(last_hit, True, c), 350)
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

    # Sauberes Cleanup beim Verlassen des Service-Menüs
    if ser:
        try:
            display.set_light(False)
            display.clear_all()
        except: pass
