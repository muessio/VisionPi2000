# Datei: game_about.py
# Version: 1.3.1
# Über das Projekt & Lizenzvereinbarung im VisionPi2000 Cyber-Circuit-Design

import pygame
import os

VERSION = "1.3.1"
GAMES = ["Über das Projekt"]
OPTIONS = ["Projektziel & Infos", "Lizenzvereinbarung"]

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


def draw_cyber_frame(surface, x, y, w, h, cut=22):
    """Zeichnet den gecachten VisionPi2000 Cyber-Tech-Rahmen ohne Rand-Clipping."""
    key = ("cyber_frame_v2", w, h, cut)
    if key not in _frame_cache:
        if len(_frame_cache) > 16:
            _frame_cache.clear()
        NEON_GREEN = (0, 255, 157)
        NEON_CYAN = (0, 216, 255)
        NEON_RED = (255, 56, 76)
        GOLD_TRACE = (180, 140, 40)
        PANEL_BG = (8, 20, 32, 225)

        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        r = w - 2
        b = h - 2
        pts_local = [
            (cut, 1), (r - cut, 1), (r, cut), (r, b - cut),
            (r - cut, b), (cut, b), (1, b - cut), (1, cut)
        ]
        pygame.draw.polygon(panel_surf, PANEL_BG, pts_local)

        traces = [
            [(cut + 20, 14), (cut + 90, 14), (cut + 110, 34)],
            [(r - cut - 20, 14), (r - cut - 90, 14), (r - cut - 110, 34)],
            [(cut + 20, b - 14), (cut + 90, b - 14), (cut + 110, b - 34)],
            [(r - cut - 20, b - 14), (r - cut - 90, b - 14), (r - cut - 110, b - 34)]
        ]
        for tr in traces:
            pygame.draw.lines(panel_surf, (20, 65, 60, 160), False, tr, 2)
            pygame.draw.circle(panel_surf, (0, 255, 157, 160), tr[-1], 4, 1)

        pygame.draw.polygon(panel_surf, (0, 110, 75), pts_local, 6)
        pygame.draw.polygon(panel_surf, NEON_GREEN, pts_local, 2)

        c_len = int(h * 0.22)
        pygame.draw.line(panel_surf, NEON_RED, (1, cut), (cut, 1), 4)
        pygame.draw.line(panel_surf, NEON_RED, (1, b - cut), (cut, b), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (2, cut + 12), (2, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (2, b - cut - 12), (2, b - cut - c_len), 4)

        pygame.draw.line(panel_surf, NEON_RED, (r - cut, 1), (r, cut), 4)
        pygame.draw.line(panel_surf, NEON_RED, (r - cut, b), (r, b - cut), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (r - 1, cut + 12), (r - 1, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (r - 1, b - cut - 12), (r - 1, b - cut - c_len), 4)

        for cx, cy in [(cut + 10, 8), (r - cut - 10, 8), (cut + 10, b - 8), (r - cut - 10, b - 8)]:
            pygame.draw.circle(panel_surf, GOLD_TRACE, (cx, cy), 4)

        _frame_cache[key] = panel_surf

    surface.blit(_frame_cache[key], (x, y))


def run_game(screen, ser, display, players, game_name, option, mode):
    sw, sh = screen.get_width(), screen.get_height()
    clock = pygame.time.Clock()
    
    role_font = pygame.font.SysFont("arial", int(sh * 0.028), bold=True)
    title_font = pygame.font.SysFont("arial", int(sh * 0.032), bold=True)
    sub_font = pygame.font.SysFont("arial", int(sh * 0.020), bold=True)
    heading_font = pygame.font.SysFont("arial", int(sh * 0.024), bold=True)
    text_font = pygame.font.SysFont("arial", int(sh * 0.019), bold=True)
    hint_font = pygame.font.SysFont("arial", int(sh * 0.023), bold=True)
    qr_label_font = pygame.font.SysFont("arial", int(sh * 0.018), bold=True)
    
    HIGHLIGHT, WHITE, GRAY = (255, 205, 45), (255, 255, 255), (180, 200, 215)
    NEON_GREEN, NEON_CYAN = (0, 255, 157), (0, 216, 255)

    if display:
        try:
            display.clear_all()
            if hasattr(display, 'update'): display.update()
        except Exception:
            pass

    is_16_9 = (sw / float(sh)) > 1.5
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
            header_h = int(sh * 0.16)
            header_w = int(raw_h.get_width() * (header_h / raw_h.get_height()))
            header_img = pygame.transform.smoothscale(raw_h, (header_w, header_h))
        except Exception:
            pass

    qr_img = None
    if os.path.exists("qrcode.png"):
        try:
            qr_size = int(sh * 0.25)
            raw_qr = pygame.image.load("qrcode.png").convert()
            qr_img = pygame.transform.smoothscale(raw_qr, (qr_size, qr_size))
        except Exception:
            pass

    is_license_view = (option == "Lizenzvereinbarung")

    running = True
    while running:
        raw_data = ser.readline().decode('utf-8', 'ignore').strip() if ser and ser.in_waiting > 0 else None
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_p, pygame.K_SPACE, pygame.K_RETURN]:
                    running = False

        if raw_data in ["BTN:PLAYER", "BTN:START", "BTN:COMBO"]:
            running = False

        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((6, 17, 28))

        if header_img:
            screen.blit(header_img, ((sw - header_img.get_width()) // 2, 6))
            box_y = int(sh * 0.15)
            box_h = int(sh * 0.81)
        else:
            box_y = int(sh * 0.04)
            box_h = int(sh * 0.92)

        box_w = int(sw * 0.90)
        box_x = (sw - box_w) // 2

        draw_cyber_frame(screen, box_x, box_y, box_w, box_h, cut=22)

        if is_license_view:
            head_surf = role_font.render("LIZENZVEREINBARUNG  •  VISIONPI2000", True, HIGHLIGHT)
        else:
            head_surf = role_font.render("PROJEKT-INFORMATIONEN  •  VISIONPI2000 / OPENRETRODART", True, HIGHLIGHT)
        screen.blit(head_surf, ((sw - head_surf.get_width()) // 2, box_y + int(box_h * 0.028)))

        line_y = box_y + int(box_h * 0.10)
        pygame.draw.line(screen, NEON_GREEN, (box_x + 35, line_y), (box_x + box_w - 35, line_y), 2)
        pygame.draw.circle(screen, HIGHLIGHT, (sw // 2, line_y), 5)

        if is_license_view:
            lines = [
                ("Quellcode-Lizenzbestimmungen / Source-Available License", NEON_GREEN, title_font),
                ("Urheberrecht © 2026 Oliver Müssig", NEON_CYAN, sub_font),
                ("", WHITE, text_font),
                ("Lizenzbestimmungen für VisionPi2000", NEON_GREEN, heading_font),
                ("1. Nutzungsrecht: Freie Nutzung für private, nicht-kommerzielle Zwecke.", WHITE, text_font),
                ("2. Einschränkungen: Jede unbefugte kommerzielle Vermarktung oder Modifikation ist untersagt.", WHITE, text_font),
                ("3. Ausnahmen: Kommerzielle Nutzung nur nach ausdrücklicher, schriftlicher Vereinbarung.", WHITE, text_font),
                ("4. Haftungsausschluss: Die Software wird ohne jegliche Gewährleistung bereitgestellt.", WHITE, text_font),
                ("", WHITE, text_font),
                ("----------------------------------------------------------------", GRAY, text_font),
                ("", WHITE, text_font),
                ("Source-Available License Terms for VisionPi2000", NEON_GREEN, heading_font),
                ("1. Scope of Use: Authorized for private, non-commercial use.", WHITE, text_font),
                ("2. Restrictions: Unauthorized commercial exploitation or modification is prohibited.", WHITE, text_font),
                ("3. Exceptions: Commercial deployment requires explicit written agreement.", WHITE, text_font),
                ("4. Disclaimer: PROVIDED WITHOUT WARRANTY OF ANY KIND.", WHITE, text_font)
            ]
        else:
            lines = [
                ("VisionPi2000 / OpenRetroDart", NEON_GREEN, title_font),
                ("Custom-Dartsports-Engine • Developed by Oliver Müssig", NEON_CYAN, sub_font),
                ("", WHITE, text_font),
                ("Ein alternatives Source-Available-System als hochmoderne", WHITE, text_font),
                ("Retrofit-Lösung für klassische Dartautomaten der 90er-/", WHITE, text_font),
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

        # Startet direkt oben unter dem Trenner und nutzt den Raum optimal aus
        content_top = line_y + int(sh * 0.025)
        curr_y = content_top

        for text, color, font_obj in lines:
            if text == "":
                curr_y += int(sh * 0.012)
                continue
            
            surf = font_obj.render(text, True, color)
            screen.blit(surf, (box_x + int(box_w * 0.04), curr_y))
            
            if font_obj == title_font:
                curr_y += int(sh * 0.038)
            elif font_obj == heading_font:
                curr_y += int(sh * 0.032)
            else:
                curr_y += int(sh * 0.025)

        if not is_license_view and qr_img:
            qr_w = qr_img.get_width()
            qr_h = qr_img.get_height()
            label_h = qr_label_font.get_height() + 8
            card_pad = 16
            qr_box_w = qr_w + card_pad * 2
            qr_box_h = qr_h + label_h + card_pad * 2
            
            qr_box_x = box_x + box_w - qr_box_w - int(box_w * 0.045)
            qr_box_y = content_top + int(sh * 0.02)

            pygame.draw.rect(screen, (12, 30, 46), (qr_box_x, qr_box_y, qr_box_w, qr_box_h), border_radius=12)
            pygame.draw.rect(screen, NEON_CYAN, (qr_box_x, qr_box_y, qr_box_w, qr_box_h), width=2, border_radius=12)
            
            screen.blit(qr_img, (qr_box_x + card_pad, qr_box_y + card_pad))
            
            lbl_surf = qr_label_font.render("GitHub / stable", True, HIGHLIGHT)
            screen.blit(lbl_surf, (qr_box_x + (qr_box_w - lbl_surf.get_width()) // 2, qr_box_y + card_pad + qr_h + 6))

        hint_surf = hint_font.render("▶  Zum Schließen: SPIELERWECHSEL oder START drücken  ◀", True, HIGHLIGHT)
        screen.blit(hint_surf, hint_surf.get_rect(center=(sw // 2, box_y + box_h - int(box_h * 0.045))))

        pygame.display.flip()
        clock.tick(30)

    return "menu"
    
