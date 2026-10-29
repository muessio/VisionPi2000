import pygame
import os

VERSION = "1.0.0"
GAMES = ["Über das Projekt"]  # Hier kannst du den Namen jederzeit anpassen
OPTIONS = ["Projektziel & Infos"]

def run_game(screen, ser, display, players, game_name, option, mode):
    sw, sh = screen.get_width(), screen.get_height()
    clock = pygame.time.Clock()
    
    title_font = pygame.font.SysFont("arial", int(sh * 0.038), bold=True)
    text_font = pygame.font.SysFont("arial", int(sh * 0.024), bold=True)
    hint_font = pygame.font.SysFont("arial", int(sh * 0.028), bold=True)
    
    HIGHLIGHT, WHITE, GRAY = (255, 215, 0), (255, 255, 255), (180, 180, 180)

    # Hardware-Anzeige im Info-Modus sauber leeren/abschalten
    if display:
        try:
            display.clear_all()
            if hasattr(display, 'update'): display.update()
        except: pass

    running = True
    while running:
        raw_data = ser.readline().decode('utf-8', 'ignore').strip() if ser and ser.in_waiting > 0 else None
        
        for event in pygame.event.get():
            if event.type in [pygame.KEYDOWN, pygame.MOUSEQUIT]:
                if event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_p, pygame.K_SPACE, pygame.K_RETURN]:
                    running = False

        if raw_data in ["BTN:PLAYER", "BTN:START", "BTN:COMBO"]:
            running = False

        screen.fill((10, 10, 20))

        # Textinhalte (Gekürzte Projektziele aus der Readme)
        lines = [
            ("VisionPi2000 / OpenRetroDart", HIGHLIGHT),
            ("", WHITE),
            ("Ein alternatives Open-Source-System zur Restauration und", WHITE),
            ("Modernisierung klassischer Dartautomaten der 90er/2000er", WHITE),
            ("(z.B. Turnierdart 2000 / Vision Dart Gehäuse).", WHITE),
            ("", WHITE),
            ("🎯 Zielsetzung:", HIGHLIGHT),
            ("• Rettung alter, robuster Gehäuse vor dem Elektroschrott.", WHITE),
            ("• Weiternutzung der originalen Matrix, Kaskaden-Anzeigen und Lampen.", WHITE),
            ("• Vollständige Bedienung über die originalen 5 Gehäusetasten.", WHITE),
            ("• Modernes Innenleben durch Raspberry Pi 4B & Arduino Mega.", WHITE),
            ("", WHITE),
            ("⚙️ Highlights:", HIGHLIGHT),
            ("• Präziser Display-Mapper für bedrahtete THT-LEDs.", WHITE),
            ("• Ausfallsicheres Read-Only-System gegen zerschossene SD-Karten.", WHITE),
            ("• Integriertes Service-Menü und OTA-Online-Updates.", WHITE)
        ]

        # Kasten für die Readme-Ausgabe zeichnen
        box_w = int(sw * 0.85)
        box_h = int(sh * 0.80)
        box_x = (sw - box_w) // 2
        box_y = int(sh * 0.05)

        pygame.draw.rect(screen, (20, 20, 30), (box_x, box_y, box_w, box_h), border_radius=14)
        pygame.draw.rect(screen, HIGHLIGHT, (box_x, box_y, box_w, box_h), width=2, border_radius=14)

        # Zeilen in den Kasten rendern
        curr_y = box_y + int(box_h * 0.05)
        for text, color in lines:
            if text == "":
                curr_y += int(sh * 0.015)
                continue
            # Überschriften etwas größer/fetter hervorheben
            f = title_font if color == HIGHLIGHT and "VisionPi" in text else text_font
            surf = f.render(text, True, color)
            screen.blit(surf, (box_x + int(box_w * 0.06), curr_y))
            curr_y += int(sh * 0.038)

        # Schließen-Hinweis ganz unten
        hint_surf = hint_font.render("Zum Schließen: Spielerwechsel-Taste oder START drücken", True, HIGHLIGHT)
        screen.blit(hint_surf, hint_surf.get_rect(center=(sw // 2, box_y + box_h - int(box_h * 0.06))))

        pygame.display.flip()
        clock.tick(30)

    return "menu"
