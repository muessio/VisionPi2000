import pygame
import os

VERSION = "1.0.0"
GAMES = ["Über das Projekt"]
OPTIONS = ["Projektziel & Infos"]

def run_game(screen, ser, display, players, game_name, option, mode):
    sw, sh = screen.get_width(), screen.get_height()
    clock = pygame.time.Clock()
    
    title_font = pygame.font.SysFont("arial", int(sh * 0.034), bold=True)
    sub_font = pygame.font.SysFont("arial", int(sh * 0.020), bold=True)
    heading_font = pygame.font.SysFont("arial", int(sh * 0.024), bold=True)
    text_font = pygame.font.SysFont("arial", int(sh * 0.021), bold=True)
    hint_font = pygame.font.SysFont("arial", int(sh * 0.025), bold=True)
    qr_label_font = pygame.font.SysFont("arial", int(sh * 0.018), bold=True)
    
    HIGHLIGHT, WHITE, GRAY = (255, 215, 0), (255, 255, 255), (180, 180, 180)

    # Hardware-Anzeige im Info-Modus sauber leeren/abschalten
    if display:
        try:
            display.clear_all()
            if hasattr(display, 'update'): display.update()
        except: pass

    # QR-Code Bild laden, falls vorhanden
    qr_img = None
    if os.path.exists("qrcode.png"):
        try:
            qr_size = int(sh * 0.26)
            raw_qr = pygame.image.load("qrcode.png").convert()
            qr_img = pygame.transform.smoothscale(raw_qr, (qr_size, qr_size))
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

        # Textinhalte strukturierter und ohne Grafik-Symbole
        lines = [
            ("VisionPi2000 / OpenRetroDart", HIGHLIGHT, title_font),
            ("Custom Dartsports Engine • Developed by Oliver Müssig", GRAY, sub_font),
            ("", WHITE, text_font),
            ("Ein alternatives Open-Source-System als hochmoderne", WHITE, text_font),
            ("Retrofit-Lösung für klassische Dartautomaten der 90er/", WHITE, text_font),
            ("2000er-Jahre (z.B. Turnierdart 2000 / Vision Dart Gehäuse).", WHITE, text_font),
            ("", WHITE, text_font),
            ("Projektziel & Zielsetzung:", HIGHLIGHT, heading_font),
            ("• Rettung alter, robuster Gehäuse vor dem Elektroschrott.", WHITE, text_font),
            ("• Weiternutzung von Matrix, Kaskaden-Anzeigen und Lampen.", WHITE, text_font),
            ("• Vollständige Bedienung über die originalen 5 Gehäusetasten.", WHITE, text_font),
            ("• Modernes Innenleben durch Raspberry Pi 4B & Arduino Mega.", WHITE, text_font),
            ("", WHITE, text_font),
            ("Highlights & Display-Mapper:", HIGHLIGHT, heading_font),
            ("• Präziser Display-Mapper (display_mapper_Vision_Dart.py)", WHITE, text_font),
            ("  exakt für das originale THT-Layout (keine SMD-Bestückung).", WHITE, text_font),
            ("• Ausfallsicheres Read-Only-System zum Schutz der", WHITE, text_font),
            ("  Speicherkarten vor Dateisystem-Korruption.", WHITE, text_font),
            ("• Integriertes Service-Menü und OTA-Online-Updates.", WHITE, text_font)
        ]

        # Kasten zeichnen
        box_w = int(sw * 0.88)
        box_h = int(sh * 0.85)
        box_x = (sw - box_w) // 2
        box_y = int(sh * 0.03)

        pygame.draw.rect(screen, (20, 20, 30), (box_x, box_y, box_w, box_h), border_radius=14)
        pygame.draw.rect(screen, HIGHLIGHT, (box_x, box_y, box_w, box_h), width=2, border_radius=14)

        # Zeilen links in den Kasten rendern mit angepassten Abständen
        curr_y = box_y + int(box_h * 0.04)
        for text, color, font_obj in lines:
            if text == "":
                curr_y += int(sh * 0.008)
                continue
            
            surf = font_obj.render(text, True, color)
            screen.blit(surf, (box_x + int(box_w * 0.04), curr_y))
            
            # Dynamischer Zeilenabstand je nach Schriftart
            if font_obj == title_font:
                curr_y += int(sh * 0.038)
            elif font_obj == heading_font:
                curr_y += int(sh * 0.035)
            else:
                curr_y += int(sh * 0.028)

        # QR-Code rechts im Kasten anzeigen, falls geladen
        if qr_img:
            qr_x = box_x + box_w - qr_img.get_width() - int(box_w * 0.04)
            qr_y = box_y + int(box_h * 0.20)
            screen.blit(qr_img, (qr_x, qr_y))
            
            # Label unter dem QR-Code
            lbl_surf = qr_label_font.render("GitHub / stable", True, HIGHLIGHT)
            screen.blit(lbl_surf, (qr_x + (qr_img.get_width() - lbl_surf.get_width()) // 2, qr_y + qr_img.get_height() + 8))

        # Schließen-Hinweis ganz unten
        hint_surf = hint_font.render("Zum Schließen: Spielerwechsel-Taste oder START drücken", True, HIGHLIGHT)
        screen.blit(hint_surf, hint_surf.get_rect(center=(sw // 2, box_y + box_h - int(box_h * 0.05))))

        pygame.display.flip()
        clock.tick(30)

    return "menu"
