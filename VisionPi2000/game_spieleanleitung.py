# Datei: game_spieleanleitung.py
# Version: 1.2.6
# Spieleanleitung im VisionPi2000 Cyber-Circuit-Design (Detaillierte Profi-Edition, 4:3 & 16:9)

import pygame
import os
import random
import json

VERSION = "1.2.6"
GAMES = ["Spieleanleitung"]
OPTIONS = [
    "301 / 501 / 701 (X01)", 
    "Cricket", 
    "Split Score", 
    "Around the Clock", 
    "Shanghai",
    "Elimination",
    "Fruit Splasher",
    "Bedienung, Modi & Bot"
]

EXPLANATIONS = {
    "301 / 501 / 701 (X01)": [
        "ZIEL: Von 301, 501 oder 701 Punkten rückwärts exakt auf 0 Punkte werfen (3 Pfeile pro Aufnahme).",
        "• Open In / Open Out: Spielbeginn und Checkout über jedes beliebige Feld (Single, Double, Triple, Bull).",
        "• Double In: Punkte zählen erst, sobald der erste Pfeil ein Doppelfeld oder das rote Bullseye (50) trifft.",
        "• Double Out: Zum Sieg muss der letzte Pfeil exakt mit einem Doppelfeld oder dem roten Bullseye (50) auf 0",
        "  checken. Bei Master Out ist das Beenden über Double, Triple oder Bullseye erlaubt.",
        "• Überwerfen (Bust): Wirft man mehr Punkte als nötig, fällt bei Double/Master Out auf 1 Punkt Rest oder",
        "  erreicht 0 ohne gültiges Checkout-Feld, verfällt die Aufnahme und der Rundenstart-Score wird wiederhergestellt.",
        "• Team-Modus (4 / 6 / 8 Spieler): Je 2 Spieler bilden ein Team mit gemeinsamem Punktestand und",
        "  werfen im Wechsel (z. B. bei 4 Spielern: Team 1 [P1] -> Team 2 [P2] -> Team 1 [P3] -> Team 2 [P4])."
    ],
    "Cricket": [
        "ZIEL: Alle 7 Zielfelder durch je 3 Treffer schließen ('öffnen') und die beste Punktzahl erzielen.",
        "• Trefferwertung: Single = 1 Mark (/), Double = 2 Marks (X), Triple = 3 Marks (Kreis = geschlossen).",
        "  Auf das Bullseye zählt der äußere Ring (25) als 1 Mark und das innere Bull (50) als 2 Marks.",
        "• Standard (15–20 & Bull): Sobald du ein Feld mit 3 Marks geöffnet hast, bringt dir jeder weitere Treffer",
        "  auf dieses Feld die entsprechende Punktzahl – bis alle Mitspieler das Feld ebenfalls geschlossen haben.",
        "• Cut Throat (Strafpunkte): Treffer auf eigene geöffnete Felder werden allen Gegnern als Strafpunkte",
        "  aufaddiert, die dieses Feld noch nicht geschlossen haben! Hier gewinnt am Ende der niedrigste Score.",
        "• You Pick It: Vor Runde 1 werden die 6 Zahlen (1–20) durch Drücken/Abwerfen an der Scheibe frei gewählt.",
        "• Crazy (Zufall): Die 6 Zielfelder (plus Bullseye) werden beim Spielstart automatisch zufällig ausgelost."
    ],
    "Split Score": [
        "ZIEL: Über 9 fest vorgegebene Runden so viele Punkte wie möglich sammeln (Startkapital: 40 Punkte).",
        "• Rundenablauf (9 Runden): Runde 1 = Zahl 15  |  Runde 2 = Zahl 16  |  Runde 3 = Jedes Double",
        "  Runde 4 = Zahl 17  |  Runde 5 = Zahl 18  |  Runde 6 = Jedes Triple  |  Runde 7 = Zahl 19",
        "  Runde 8 = Zahl 20  |  Runde 9 = Bullseye (Single Bull = 25 Punkte, Double Bull = 50 Punkte).",
        "• Punkte-Addition: Trifft mindestens 1 Pfeil deiner Aufnahme (3 Pfeile) die geforderte Rundenvorgabe,",
        "  werden alle gültigen Treffer dieser Runde voll auf deinen Gesamtpunktestand addiert.",
        "• In den Runden 'Double' und 'Triple' zählt jedes beliebige Doppel- bzw. Dreifachfeld auf der Scheibe.",
        "• HALBIERUNG (Split): Verfehlst du mit allen 3 Pfeilen das Vorgabeziel der aktuellen Runde komplett,",
        "  wird dein gesamter bisheriger Punktestand gnadenlos halbiert (abgerundet)!"
    ],
    "Around the Clock": [
        "ZIEL: Alle Zahlen von 1 bis 20 nacheinander in exakt aufsteigender Reihenfolge treffen.",
        "• Spielablauf: Jeder Spieler startet auf dem Ziel '1'. Sobald die aktuelle Zielzahl getroffen wird,",
        "  schaltet das persönliche Ziel noch während derselben Aufnahme sofort auf die nächste Zahl weiter",
        "  (z. B. Pfeil 1 trifft die 1 -> Pfeil 2 zielt direkt auf die 2 -> Pfeil 3 auf die 3).",
        "• Das Hardware-Display sowie der Bildschirm zeigen stets die aktuell benötigte Zielzahl des Spielers an.",
        "• Variante 'Standard': Jeder Treffer im richtigen Zahlensegment (Single, Double oder Triple) zählt.",
        "• Variante 'Double Only': Für Profis! Eine Zahl gilt nur dann als getroffen, wenn exakt das Doppelfeld",
        "  (äußerer Ring) der jeweiligen Zielzahl getroffen wird.",
        "• Siegbedingung: Wer als Erster nach der 19 auch die 20 erfolgreich trifft, gewinnt sofort."
    ],
    "Shanghai": [
        "ZIEL: Über 7 Runden auf die Zahlen 1 bis 7 die meisten Punkte sammeln oder einen 'Shanghai' werfen.",
        "• Runden-Vorgabe: Die Rundennummer bestimmt das einzige gültige Zielfeld! In Runde 1 zählt nur die 1,",
        "  in Runde 2 nur die 2, in Runde 3 nur die 3 ... bis zur 7. Runde, in der ausschließlich die 7 zählt.",
        "• Punktwertung: Treffer außerhalb der aktuellen Rundenzahl bringen 0 Punkte. Gültige Treffer zählen",
        "  ihren regulären Wert (Rundenzahl × 1 für Single, × 2 für Double, × 3 für Triple).",
        "• SOFORTSIEG ('SHANGHAI'): Gelingt es einem Spieler innerhalb einer einzigen Aufnahme (mit seinen",
        "  3 Pfeilen), jeweils genau 1× Single, 1× Double und 1× Triple der aktuellen Rundenzahl zu treffen",
        "  (Reihenfolge egal), endet das Match auf der Stelle und dieser Spieler gewinnt durch Shanghai!",
        "• Reguläres Spielende: Fällt kein Shanghai, gewinnt nach Ende von Runde 7 der höchste Punktestand."
    ],
    "Elimination": [
        "ZIEL: Von 0 Punkten aufwärts exakt die Zielpunktzahl (Standard: 301 Punkte) erreichen.",
        "• Punkteaufbau: Jeder geworfene Pfeil (Single, Double, Triple, Bull) wird direkt zum eigenen",
        "  Punktestand addiert. Die Varianten erlauben auch schnelles Spiel bis 501 oder Double Out.",
        "• ELIMINIERUNG (Rauswurf): Landet dein Punktestand nach einem Pfeilwurf exakt auf derselben",
        "  Punktzahl, auf der sich gerade ein oder mehrere Mitspieler befinden, werden diese Gegner",
        "  sofort 'eliminiert' und fallen gnadenlos auf 0 Punkte zurück!",
        "• Überwerfen (Bust): Überschreitest du mit einem Wurf das Spielziel (z. B. mehr als 301 Punkte),",
        "  ist die gesamte Aufnahme ungültig und dein Punktestand wird auf den Wert vor der Runde zurückgesetzt.",
        "• Siegbedingung: Wer zuerst mit einem gültigen Pfeil exakt die 301 erreicht, gewinnt das Spiel."
    ],
    "Fruit Splasher": [
        "ZIEL: Das exklusive VisionPi2000 Action-Game – wahlweise als 'Juice Press' oder 'Berry Hunt'!",
        "• Juice Press (3 / 5 Beeren): Jeder Spieler bekommt eine eigene Zielzahl (1–20). Treffer auf die eigene",
        "  Zahl oder das Bullseye pumpen deine Frucht auf (Single = +1, Double/Bull = +2, Triple/D-Bull = +3 Juice).",
        "  Bei 7/7 Juice platzt die Beere ('SPLASH! +1'), du erhältst 1 Punkt und eine neue Zufallszahl.",
        "• Juice Press (Battle - Bull klaut): Wie Standard, aber jeder Treffer auf das Bullseye pumpt nicht nur",
        "  die eigene Beere auf, sondern stiehlt dem aktuell führenden Mitspieler zusätzlich 1 bis 2 Juice-Stufen!",
        "• Berry Hunt (10 / 15 Runden): 6 Früchte mit Zahlen (1–20) sowie die Golden-Berry (Bullseye) liegen offen",
        "  aus (auch auf den 6 Cricket-Displays sichtbar). Jeder Treffer zerquetscht die Frucht für Direktpunkte",
        "  (Zahl × Multiplikator; Bull = 50 / 100 Pkt.) und spawnt sofort eine neue Frucht auf einer freien Zahl."
    ],
    "Bedienung, Modi & Bot": [
        "STEUERUNG AM AUTOMATEN, SONDERFUNKTIONEN & SPIELMODI:",
        "• Menü-Auswahl: Taste ROT = Spiel wählen  |  Taste BLAU = Spiel-Option  |  Taste GRAU = Modus wählen",
        "  Taste SPIELERWECHSEL = Spieleranzahl (1–8)  |  Taste START = Ausgewähltes Spiel starten.",
        "• Spielerwechsel im Spiel: Nach 3 geworfenen Pfeilen blinkt die Spielerwechsel-Taste. Ziehe die Pfeile",
        "  aus der Scheibe: Der Infrarot-Sensor (IR) erkennt dich und schaltet nach kurzer Verzögerung automatisch",
        "  auf den nächsten Spieler weiter. Alternativ schaltet die Taste SPIELERWECHSEL jederzeit sofort weiter.",
        "• Spiel abbrechen / System-Info: Halte alle 3 Auswahltasten (ROT + BLAU + GRAU) gleichzeitig gedrückt,",
        "  um im Spiel das Abbruch-Menü zu öffnen (oder im Hauptmenü die System- & Versionsübersicht anzuzeigen).",
        "• Bullseye-Berry (Bot Stufe 1–3) & Online: Spiele allein oder mit bis zu 7 Freunden gegen den animierten",
        "  Computergegner (Stufe 1 = Einsteiger, 2 = Fortgeschritten, 3 = Profi) oder über WLAN im Online-Modus!"
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
    text_font = pygame.font.SysFont("arial", int(sh * 0.0185), bold=True)
    hint_font = pygame.font.SysFont("arial", int(sh * 0.020), bold=True)
    
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
            screen, bg_img, header_img, role_font, "SPIELEANLEITUNG & REGELWERK"
        )

        # Ausgewähltes Thema als Untertitel in der Box (inkl. Seitenanzeige)
        page_str = f"Thema ({current_opt_idx + 1}/{len(OPTIONS)}): {option}"
        opt_surf = sub_font.render(page_str, True, NEON_GREEN)
        screen.blit(opt_surf, ((sw - opt_surf.get_width()) // 2, box_y + int(box_h * 0.145)))

        # Trennlinie unter dem Titel
        pygame.draw.line(screen, (40, 75, 95), (box_x + 35, box_y + int(box_h * 0.205)), (box_x + box_w - 35, box_y + int(box_h * 0.205)), 2)

        # Regeltextzeilen dynamisch innerhalb der Cyber-Box verteilen
        # Jeder Aufzählungspunkt wechselt zwischen NEON_CYAN und WHITE, Fortsetzungszeilen behalten die Farbe
        lines = EXPLANATIONS.get(option, ["Keine Beschreibung verfügbar."])
        y_text = box_y + int(box_h * 0.235)
        avail_text_h = int(box_h * 0.65)
        line_step = min(int(box_h * 0.068), avail_text_h // max(1, len(lines)))

        current_bullet_col = WHITE
        is_cyan_turn = True

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if idx == 0 and (stripped.startswith("ZIEL:") or stripped.startswith("STEUERUNG")):
                col = GOLD
            elif stripped.startswith("•"):
                col = NEON_CYAN if is_cyan_turn else WHITE
                is_cyan_turn = not is_cyan_turn
                current_bullet_col = col
            else:
                col = current_bullet_col
            line_surf = text_font.render(line, True, col)
            screen.blit(line_surf, (box_x + int(box_w * 0.045), y_text))
            y_text += line_step

        # Steuerungs- und Schließen-Hinweis ganz unten in der Box
        back_hint = hint_font.render("BLAU / ROT = Vor / Zurück blättern   |   START oder SPIELERWECHSEL = Hauptmenü", True, GOLD)
        screen.blit(back_hint, back_hint.get_rect(center=(sw // 2, box_y + box_h - int(box_h * 0.05))))

        pygame.display.flip()
        clock.tick(30)
        
    if ser:
        try: 
            ser.write(b"LAMP:PLAYER:2\n")
            ser.write(b"LAMP:START:2\n")
            ser.flush()
        except Exception:
            pass
