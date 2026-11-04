# Datei: game_spieleanleitung.py
# Version: 1.2.2
# Spieleanleitung im VisionPi2000 Cyber-Circuit-Design (4:3 & 16:9 Support)

import pygame
import os
import random
import json

VERSION = "1.2.2"
GAMES = ["Spieleanleitung"]
OPTIONS = [
    "301 / 501 / 701 (X01)", 
    "Cricket", 
    "Split Score", 
    "Around the Clock", 
    "Shanghai",
    "Elimination",
    "Fruit Splasher"
]

EXPLANATIONS = {
    "301 / 501 / 701 (X01)": [
        "Das Standard-Dartspiel. Ziel: Exakt 0 Punkte von 301/501/701 abziehen.",
        "Optionen für den Ein- und Auswurf:",
        "• Open In/Out: Beliebiger Treffer zum Start und Ende (auch Single).",
        "• Double In: Das Spiel beginnt erst mit einem Treffer im Doppelring/Bull.",
        "• Double Out: Das Spiel muss mit einem Doppel- oder Bullseye-Treffer beendet werden.",
        "• Master Out: Beenden mit Double, Triple oder Bullseye möglich.",
        "• Team-Modus: 2er-Teams spielen mit gemeinsamem Punktestand.",
        "  Die Spieler werfen abwechselnd (z.B. P1 -> P3 -> P2 -> P4).",
        "• Überwerfen (Bust): Wirfst du mehr Punkte als Rest oder bleibst auf 1,",
        "  zählt die Runde nicht und der Punktestand wird zurückgesetzt."
    ],
    "Cricket": [
        "Ein Taktikspiel. Gespielt wird standardmäßig auf die Zahlen",
        "15 bis 20 sowie das Bullseye (jeweils 3 Treffer zum Öffnen/Schließen).",
        "• Standard: Punkte zählen für dich, solange Gegner die Zahl noch offen haben.",
        "• Cut Throat: Strafpunkte! Treffer auf deine bereits geöffneten Zahlen",
        "  werden allen Gegnern aufaddiert, die diese Zahl noch nicht zu haben.",
        "• You Pick It: Vor Spielbeginn werden die 6 Zielfelder (1–20) durch",
        "  Drücken/Abwerfen an der Scheibe frei festgelegt, danach startet Runde 1.",
        "• Crazy (Zufall): Die 6 Zielfelder werden zu Beginn per Zufall bestimmt.",
        "Wer alle 7 Felder geschlossen und die beste Punktzahl hat, gewinnt."
    ],
    "Split Score": [
        "Ein Disziplin-Test über 9 Runden (15, 16, Double, 17, 18,",
        "Triple, 19, 20, Bull). Man startet mit 40 Punkten.",
        "• Trifft man das Vorgabeziel der aktuellen Runde mindestens einmal,",
        "  werden die geworfenen Punkte zum Punktestand addiert.",
        "• Verfehlt man das Rundenziel mit allen 3 Pfeilen komplett,",
        "  halbiert sich der aktuelle Gesamtpunktestand!",
        "Wer nach Runde 9 die meisten Punkte hat, gewinnt."
    ],
    "Around the Clock": [
        "Der Klassiker für Einsteiger und Präzisionstraining. Die Zahlen",
        "müssen nacheinander von 1 bis 20 in der korrekten Reihenfolge",
        "getroffen werden.",
        "• Standard: Jeder Treffer im Zielsegment (Single, Double, Triple) zählt.",
        "• Double Only: Es zählen ausschließlich Treffer im Doppelring der Zielzahl!",
        "Wer als Erster die 20 trifft, gewinnt das Spiel."
    ],
    "Shanghai": [
        "Ein schnelles 7-Runden-Spiel auf die Zahlen 1 bis 7.",
        "• In jeder Runde zählt ausschließlich die aktuelle Rundenzahl",
        "  (Runde 1 = Einsen, Runde 2 = Zweien ... bis Runde 7 = Siebenen).",
        "• SHANGHAI-SIEG: Wer innerhalb einer Aufnahme (3 Pfeile) je einmal",
        "  Single, Double und Triple der aktuellen Zielzahl trifft, gewinnt sofort!",
        "• Ansonsten gewinnt nach 7 Runden der Spieler mit den meisten Punkten."
    ],
    "Elimination": [
        "Jeder Spieler startet bei 0 Punkten. Ziel ist es, exakt 301 Punkte",
        "(bzw. die gewählte Zielpunktzahl) zu erreichen.",
        "• Alle geworfenen Punkte werden zum eigenen Stand addiert.",
        "• ELIMINATION: Erreicht ein Spieler nach seinem Wurf exakt denselben",
        "  Punktestand wie ein oder mehrere Mitspieler, werden diese Gegner",
        "  gnadenlos auf 0 Punkte zurückgesetzt!",
        "• Überwirft man das Ziel (über 301), verfällt die aktuelle Aufnahme."
    ],
    "Fruit Splasher": [
        "Das rasante VisionPi2000 Action-Spiel in zwei Spielvarianten:",
        "• Juice Press (3 oder 5 Beeren): Jeder Spieler erhält eine eigene Zielzahl.",
        "  Treffer auf die eigene Zahl oder Bullseye pumpen die Frucht auf (Single +1,",
        "  Double +2, Triple +3). Bei 7/7 Juice platzt die Beere ('SPLASH! +1') und",
        "  eine neue Zahl wird vergeben. Im 'Battle'-Modus klaut Bullseye zudem",
        "  Juice-Punkte vom führenden Gegner!",
        "• Berry Hunt (10 / 15 Runden): 6 Früchte mit wechselnden Zahlen plus die",
        "  Golden-Berry (Bullseye = 50/100 Pkt.) liegen offen aus. Jede getroffene",
        "  Frucht bringt sofort Punkte (Zahl × Multiplikator) und wechselt das Feld."
    ]
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
    """Zeichnet den gecachten VisionPi2000 Cyber-Tech-Rahmen."""
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


def render_cyber_shell(screen, bg_img, header_img, role_font, title_text):
    """Zeichnet Hintergrund, oberes Logo und den Cyber-Rahmen."""
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


class ScreenSaver:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.timeout = 10 * 60 * 1000
        self.last_activity = pygame.time.get_ticks()
        self.active = False
        self.avatars = []
        for file in ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]:
            if os.path.exists(file):
                try:
                    img = pygame.transform.smoothscale(pygame.image.load(file).convert_alpha(), (100, 100))
                    self.avatars.append({"img": img, "x": random.randint(50, max(60, width-150)), "y": random.randint(50, max(60, height-150)), "vx": random.choice([-2, 2]), "vy": random.choice([-2, 2])})
                except Exception:
                    pass
    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active: self.active = False; return True
        return False
    def check(self):
        if not self.active and pygame.time.get_ticks() - self.last_activity > self.timeout: self.active = True
        return self.active
    def update_and_draw(self, screen, font):
        if not self.active: return
        screen.fill((0, 0, 0))
        for av in self.avatars:
            av["x"] += av["vx"]; av["y"] += av["vy"]
            if av["x"] <= 0 or av["x"] >= self.width - 100: av["vx"] *= -1
            if av["y"] <= 0 or av["y"] >= self.height - 100: av["vy"] *= -1
            screen.blit(av["img"], (av["x"], av["y"]))
        hint_surf = font.render("STANDBY – Beliebige Taste drücken zum Fortfahren", True, (120, 120, 120))
        screen.blit(hint_surf, hint_surf.get_rect(center=(self.width // 2, self.height - 40)))


def run_game(screen, ser, display, players, game_name, option, mode):
    sw, sh = screen.get_width(), screen.get_height()
    screensaver = ScreenSaver(sw, sh)
    try:
        display.clear_all()
    except Exception:
        pass
    
    is_16_9 = (sw / float(sh)) > 1.5
    try:
        with open("settings.json", "r") as f:
            is_16_9 = json.load(f).get("format", "4:3") == "16:9"
    except Exception:
        pass
    
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

    sound_click = pygame.mixer.Sound("sounds/click.wav") if os.path.exists("sounds/click.wav") else None

    role_font = pygame.font.SysFont("arial", int(sh * 0.028), bold=True)
    sub_font = pygame.font.SysFont("arial", int(sh * 0.023), bold=True)
    text_font = pygame.font.SysFont("arial", int(sh * 0.020), bold=True)
    hint_font = pygame.font.SysFont("arial", int(sh * 0.021), bold=True)
    
    GOLD = (255, 205, 45)
    WHITE = (255, 255, 255)
    NEON_GREEN = (0, 255, 157)
    NEON_CYAN = (0, 216, 255)

    current_opt_idx = OPTIONS.index(option) if option in OPTIONS else 0

    if ser:
        try: 
            ser.write(b"LAMP:PLAYER:1\n")
            ser.write(b"LAMP:START:1\n")
            ser.flush()
        except Exception:
            pass

    running = True
    clock = pygame.time.Clock()

    while running:
        raw_data = None
        if ser and ser.in_waiting > 0:
            try:
                while ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', 'ignore').strip()
                    if line.startswith(("BTN:", "HIT:")):
                        raw_data = line
                        break
            except Exception:
                raw_data = None
            
        for e in pygame.event.get():
            if e.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer():
                    raw_data = None
                    continue
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_p, pygame.K_ESCAPE, pygame.K_SPACE]:
                    running = False
                elif e.key in [pygame.K_b, pygame.K_RIGHT, pygame.K_DOWN]:
                    raw_data = "BTN:BLUE"
                elif e.key in [pygame.K_r, pygame.K_LEFT, pygame.K_UP]:
                    raw_data = "BTN:RED"

        if raw_data and screensaver.reset_timer():
            raw_data = None
            continue

        if raw_data == "BTN:BLUE":
            if sound_click:
                sound_click.play()
            current_opt_idx = (current_opt_idx + 1) % len(OPTIONS)
            option = OPTIONS[current_opt_idx]
        elif raw_data == "BTN:RED":
            if sound_click:
                sound_click.play()
            current_opt_idx = (current_opt_idx - 1) % len(OPTIONS)
            option = OPTIONS[current_opt_idx]
        elif raw_data in ["BTN:PLAYER", "BTN:START", "BTN:COMBO"]:
            running = False

        if screensaver.check():
            screensaver.update_and_draw(screen, hint_font)
            pygame.display.flip()
            clock.tick(30)
            continue

        # Cyber-Shell als Rahmen und Hintergrund zeichnen
        box_x, box_y, box_w, box_h = render_cyber_shell(
            screen, bg_img, header_img, role_font, "SPIELEANLEITUNG & REGELN"
        )

        # Ausgewähltes Spiel als Untertitel in der Box (inkl. Seitenanzeige)
        page_str = f"Ausgewähltes Spiel ({current_opt_idx + 1}/{len(OPTIONS)}): {option}"
        opt_surf = sub_font.render(page_str, True, NEON_GREEN)
        screen.blit(opt_surf, ((sw - opt_surf.get_width()) // 2, box_y + int(box_h * 0.155)))

        # Trennlinie unter dem Titel
        pygame.draw.line(screen, (40, 75, 95), (box_x + 40, box_y + int(box_h * 0.22)), (box_x + box_w - 40, box_y + int(box_h * 0.22)), 2)

        # Regeltextzeilen innerhalb der Cyber-Box ausgeben
        lines = EXPLANATIONS.get(option, ["Keine Beschreibung verfügbar."])
        y_text = box_y + int(box_h * 0.26)
        line_step = int(box_h * 0.058)
        for line in lines:
            col = NEON_CYAN if line.strip().startswith("•") else WHITE
            line_surf = text_font.render(line, True, col)
            screen.blit(line_surf, (box_x + int(box_w * 0.05), y_text))
            y_text += line_step

        # Steuerungs- und Schließen-Hinweis ganz unten in der Box
        back_hint = hint_font.render("Taste BLAU = Nächstes Spiel  |  START oder SPIELERWECHSEL = Zurück zum Menü", True, GOLD)
        screen.blit(back_hint, back_hint.get_rect(center=(sw // 2, box_y + box_h - int(box_h * 0.055))))

        pygame.display.flip()
        clock.tick(30)
        
    if ser:
        try: 
            ser.write(b"LAMP:PLAYER:2\n")
            ser.write(b"LAMP:START:2\n")
            ser.flush()
        except Exception:
            pass
