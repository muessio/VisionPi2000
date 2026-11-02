# Datei: game_spieleanleitung.py
# Version: 1.2.0
# Spieleanleitung im edlen VisionPi2000 Cyber-Box-Design (4:3 & 16:9 Support)

import pygame
import os
import random
import json

VERSION = "1.2.0"
GAMES = ["Spieleanleitung"]
OPTIONS = [
    "301 / 501 / 701 (X01)", 
    "Cricket", 
    "Split Score", 
    "Around the Clock", 
    "Shanghai",
    "Elimination"
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
        "• Überwerfen (Bust): Wirst du mehr Punkte als Rest oder bleibst auf 1,",
        "zählt die Runde nicht und der Punktestand des Teams wird zurückgesetzt."
    ],
    "Cricket": [
        "Ein Taktikspiel. Gespielt wird standardmäßig",
        "auf die Zahlen 15 bis 20 sowie das Bullseye (jeweils 3 Treffer zum Schließen).",
        "• Standard / Cut Throat: Feste Zahlenvorgabe mit Punktewertung.",
        "• You Pick It: Die ersten Felder sind frei wählbar durch eigene Treffer!",
        "• Crazy (Zufall): Die 6 Zielfelder werden zu Beginn per Zufall bestimmt.",
        "Wer als Erster alles schließt und die meisten Punkte hat, gewinnt."
    ],
    "Split Score": [
        "Ein Disziplin-Test über 9 Runden (15, 16, Double, 17, 18,",
        "Triple, 19, 20, Bull). Man startet mit 40 Punkten. Trifft man das",
        "Vorgabeziel der Runde nicht, halbiert sich der aktuelle Punktestand!",
        "Wer am Ende die meisten Punkte hat, gewinnt."
    ],
    "Around the Clock": [
        "Der Klassiker für Einsteiger und Präzisionstraining. Die Zahlen",
        "müssen nacheinander von 1 bis 20 (und optional mit Bull) in der",
        "korrekten Reihenfolge getroffen werden. Wer als Erster die 20",
        "(bzw. das Bull) trifft, gewinnt das Spiel."
    ],
    "Shanghai": [
        "Ein schnelles 7-Runden-Spiel (Zahlen 1 bis 7). In jeder Runde",
        "zählt nur die aktuelle Zielzahl (Runde 1 = Einsen, Runde 2 = Zweien usw.).",
        "Wer in einer Aufnahme Single, Double und Triple derselben Zahl",
        "trifft, gewinnt das Spiel sofort ('Shanghai'). Ansonsten entscheidet der Punktestand."
    ],
    "Elimination": [
        "Jeder Spieler startet bei 0 Punkten. Ziel ist es, exakt 301 Punkte",
        "zu erreichen. Wirft ein Spieler genau die Punktzahl eines Gegners,",
        "wird dieser Gegner gnadenlos auf 0 Punkte zurück ‚eliminiert‘!"
    ]
}

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
                    self.avatars.append({"img": img, "x": random.randint(50, width-150), "y": random.randint(50, height-150), "vx": random.choice([-2, 2]), "vy": random.choice([-2, 2])})
                except: pass
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
    try: display.clear_all()
    except: pass
    
    is_16_9 = False
    try:
        with open("settings.json", "r") as f: is_16_9 = json.load(f).get("format", "4:3") == "16:9"
    except: pass
    
    bg_file = "background_16_9.png" if is_16_9 else "background.png"
    bg_img = None
    if os.path.exists(bg_file):
        try:
            raw_bg = pygame.image.load(bg_file).convert()
            bg_img = pygame.transform.scale(raw_bg, (sw, sh))
            darker_overlay = pygame.Surface((sw, sh))
            darker_overlay.set_alpha(160)
            darker_overlay.fill((0, 0, 0))
            bg_img.blit(darker_overlay, (0, 0))
        except: pass

    title_font = pygame.font.SysFont("arial", int(sh * 0.036), bold=True)
    sub_font = pygame.font.SysFont("arial", int(sh * 0.024), bold=True)
    text_font = pygame.font.SysFont("arial", int(sh * 0.022), bold=True)
    hint_font = pygame.font.SysFont("arial", int(sh * 0.022), bold=True)
    
    WHITE, HIGHLIGHT, GREEN_COL = (255, 255, 255), (255, 215, 0), (100, 220, 100)

    if ser:
        try: 
            ser.write(b"LAMP:PLAYER:1\n")
            ser.write(b"LAMP:START:0\n")
            ser.flush()
        except: pass

    running = True
    clock = pygame.time.Clock()

    while running:
        raw_data = None
        if ser and ser.in_waiting > 0:
            try: raw_data = ser.readline().decode('utf-8','ignore').strip()
            except: pass
            
        for e in pygame.event.get():
            # MOUSEMOTION entfernt, damit Vibrationen den Screensaver nicht stören
            if e.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer(): raw_data = None; continue
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_p, pygame.K_ESCAPE]: running = False
                elif e.key == pygame.K_SPACE: running = False

        if raw_data and screensaver.reset_timer(): raw_data = None; continue

        if raw_data in ["BTN:PLAYER", "BTN:START", "BTN:COMBO"]:
            running = False

        if screensaver.check():
            screensaver.update_and_draw(screen, hint_font)
            pygame.display.flip()
            clock.tick(30)
            continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        # Kasten-Dimensionen (wie im Service-Menü)
        box_w = int(sw * 0.88)
        box_h = int(sh * 0.88)
        box_x = (sw - box_w) // 2
        box_y = (sh - box_h) // 2 - int(sh * 0.02)

        # 1. Schatten unter dem Kasten
        shadow_rect = pygame.Rect(box_x + 6, box_y + 6, box_w, box_h)
        pygame.draw.rect(screen, (0, 0, 0), shadow_rect, border_radius=14)

        # 2. Satter, dunkler Hintergrund für den Kasten
        pygame.draw.rect(screen, (10, 10, 18), (box_x, box_y, box_w, box_h), border_radius=14)
        
        # 3. Edler goldener Rahmen
        pygame.draw.rect(screen, HIGHLIGHT, (box_x, box_y, box_w, box_h), width=2, border_radius=14)

        # Titel & Spiel-Option innerhalb der Box rendern
        t_surf = title_font.render("SPIELEANLEITUNG & REGELN", True, HIGHLIGHT)
        screen.blit(t_surf, (box_x + (box_w - t_surf.get_width()) // 2, box_y + int(box_h * 0.04)))
        
        opt_surf = sub_font.render(f"Ausgewähltes Spiel: {option}", True, GREEN_COL)
        screen.blit(opt_surf, (box_x + (box_w - opt_surf.get_width()) // 2, box_y + int(box_h * 0.11)))

        # Trennlinie
        pygame.draw.line(screen, (60, 70, 90), (box_x + 30, box_y + int(box_h * 0.17)), (box_x + box_w - 30, box_y + int(box_h * 0.17)), 2)

        # Regeltextzeilen zentriert in der Box ausgeben
        lines = EXPLANATIONS.get(option, ["Keine Beschreibung verfügbar."])
        y_text = box_y + int(box_h * 0.21)
        for line in lines:
            line_surf = text_font.render(line, True, WHITE)
            screen.blit(line_surf, (box_x + (box_w - line_surf.get_width()) // 2, y_text))
            y_text += int(sh * 0.038)

        # Schließen-Hinweis ganz unten in der Box
        back_hint = hint_font.render("Zum Schließen: Spielerwechsel-Taste oder START drücken", True, HIGHLIGHT)
        screen.blit(back_hint, back_hint.get_rect(center=(sw // 2, box_y + box_h - int(box_h * 0.05))))

        pygame.display.flip()
        clock.tick(30)
        
    if ser:
        try: 
            ser.write(b"LAMP:PLAYER:2\n")
            ser.write(b"LAMP:START:2\n")
            ser.flush()
        except: pass
