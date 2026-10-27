import pygame
import json
import os
import sys

VERSION = "1.5.4"

# =====================================================================
# UI-ANPASSUNGEN (Hier direkt im Quellcode auf GitHub anpassbar!)
# =====================================================================
UI_SCALE = 1.0              # Allgemeine Skalierung
HEADER_OFFSET_X = 0         # Header nach links (-) oder rechts (+) verschieben
HEADER_OFFSET_Y = 0         # Header nach oben (-) oder unten (+) verschieben
HEADER_WIDTH = 480          # Breite des Header-Fensters
HEADER_HEIGHT = 160         # Höhe des Header-Fensters

# Anpassungen für die Button-/Aktions-Gruppe (z.B. Spieler/Aktionen)
BTN_GROUP_WIDTH = 550       # Breite der Gruppen-Box
BTN_GROUP_HEIGHT = 220      # Höhe der Gruppen-Box (länger nach oben/unten)
BTN_GROUP_OFFSET_Y = 30     # Abstand der Gruppen-Box unter dem Header
# =====================================================================

def load_settings():
    paths = ["/boot/firmware/settings.json", "/boot/settings.json", "settings.json"]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except: pass
    return {"format": "4:3", "mapper": "display_mapper_Vision_Dart"}

def main():
    pygame.init()
    pygame.font.init()

    settings = load_settings()
    
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    if sw < 800: sw = 1024
    if sh < 600: sh = 768

    screen = pygame.display.set_mode((sw, sh), pygame.FULLSCREEN)
    pygame.display.set_caption("VisionPi2000 Kiosk")

    clock = pygame.time.Clock()
    
    # Dynamische Schriftgrößen skaliert mit UI_SCALE
    font = pygame.font.SysFont("arial", int(sh * 0.03 * UI_SCALE), bold=True)
    title_font = pygame.font.SysFont("arial", int(sh * 0.04 * UI_SCALE), bold=True)
    small_font = pygame.font.SysFont("arial", int(sh * 0.02 * UI_SCALE), bold=True)

    ser = None
    try:
        import serial
        for port in ["/dev/ttyUSB0", "/dev/ttyACM0", "/dev/ttyS0"]:
            if os.path.exists(port):
                ser = serial.Serial(port, 115200, timeout=0.05)
                break
    except: pass

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((15, 15, 30))

        # --- 1. HEADER (Position und Größe über Variablen steuerbar) ---
        overlay_x = (sw - HEADER_WIDTH) // 2 + HEADER_OFFSET_X
        overlay_y = int(sh * 0.05) + HEADER_OFFSET_Y
        overlay_rect = pygame.Rect(overlay_x, overlay_y, HEADER_WIDTH, HEADER_HEIGHT)
        
        pygame.draw.rect(screen, (0, 0, 0), overlay_rect)
        pygame.draw.rect(screen, (255, 215, 0), overlay_rect, 2)

        # Versionsnummer im Header
        ver_surf = title_font.render(f"VisionPi2000 - v{VERSION}", True, (255, 215, 0))
        screen.blit(ver_surf, (overlay_x + (overlay_rect.width - ver_surf.get_width()) // 2, overlay_rect.y + 12))

        # Status / Info im Header
        info_surf = small_font.render(f"Skalierung: {UI_SCALE:.1f} | Offset X/Y: {HEADER_OFFSET_X}/{HEADER_OFFSET_Y}", True, (200, 200, 200))
        screen.blit(info_surf, (overlay_x + (overlay_rect.width - info_surf.get_width()) // 2, overlay_rect.y + 60))

        # Exit-Hinweis unter dem Header
        exit_surf = small_font.render("Drücke ESC zum Beenden", True, (180, 180, 180))
        screen.blit(exit_surf, (overlay_x + (overlay_rect.width - exit_surf.get_width()) // 2, overlay_rect.bottom + 10))

        # --- 2. BUTTON- / SPIELER-GRUPPE (Breite, Höhe & Position steuerbar) ---
        group_x = (sw - BTN_GROUP_WIDTH) // 2
        group_y = overlay_rect.bottom + BTN_GROUP_OFFSET_Y
        group_rect = pygame.Rect(group_x, group_y, BTN_GROUP_WIDTH, BTN_GROUP_HEIGHT)

        # Zeichne den Gruppen-Hintergrund (z.B. für die Rot/Blau/Grau- oder Spieler-Boxen)
        pygame.draw.rect(screen, (25, 25, 45), group_rect, border_radius=8)
        pygame.draw.rect(screen, (100, 100, 150), group_rect, 2, border_radius=8)

        # Inhalt in der Gruppe
        menu_title = font.render("Aktions- & Spieler-Gruppe", True, (255, 255, 255))
        screen.blit(menu_title, (group_x + (group_rect.width - menu_title.get_width()) // 2, group_y + 20))

        sub_text = small_font.render("(Passe BTN_GROUP_WIDTH / HEIGHT oben im Code an)", True, (150, 150, 150))
        screen.blit(sub_text, (group_x + (group_rect.width - sub_text.get_width()) // 2, group_y + 65))

        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
    
