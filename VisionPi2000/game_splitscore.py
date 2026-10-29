import pygame
import math
import os
import random
import time
import json

VERSION = "1.7.6"
GAMES = ["Split Score"]
OPTIONS = ["Standard"]

def trigger_victory(ser):
    if os.path.exists("sounds/victory.wav"):
        try: pygame.mixer.Sound("sounds/victory.wav").play()
        except: pass
    if ser:
        try:
            for _ in range(6):
                ser.write(b"TEST:ON\n"); ser.flush(); time.sleep(0.25)
                ser.write(b"TEST:OFF\n"); ser.flush(); time.sleep(0.25)
            ser.write(b"LAMP:PLAYER:2\n")
            ser.write(b"LAMP:START:0\n")
            ser.flush()
        except: pass

def get_bot_hit(target, mode):
    diff = 1 if "Leicht" in mode else (2 if "Mittel" in mode else 3)
    if target == "D": return f"d{random.randint(1,20)}" if random.random() < (0.2*diff) else "20"
    if target == "T": return f"t{random.randint(1,20)}" if random.random() < (0.2*diff) else "20"
    if target == "B": return "b" if random.random() < (0.3*diff) else "20"
    return str(target) if random.random() < (0.3*diff) else str(random.randint(1,20))

class ScreenSaver:
    def __init__(self, width, height):
        self.width, self.height, self.active, self.last_activity = width, height, False, pygame.time.get_ticks()
        self.avatars = []
        for file in ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]:
            if os.path.exists(file):
                try: self.avatars.append({"img": pygame.transform.smoothscale(pygame.image.load(file).convert_alpha(), (100, 100)), "x": random.randint(50, width-150), "y": random.randint(50, height-150), "vx": random.choice([-2, 2]), "vy": random.choice([-2, 2])})
                except: pass
    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active: self.active = False; return True
        return False
    def check(self):
        if not self.active and pygame.time.get_ticks() - self.last_activity > 600000: self.active = True
        return self.active
    def update_and_draw(self, screen, font):
        if not self.active: return
        screen.fill((0, 0, 0))
        for av in self.avatars:
            av["x"] += av["vx"]; av["y"] += av["vy"]
            if av["x"] <= 0 or av["x"] >= self.width - 100: av["vx"] *= -1
            if av["y"] <= 0 or av["y"] >= self.height - 100: av["vy"] *= -1
            screen.blit(av["img"], (av["x"], av["y"]))
        hint = font.render("STANDBY – Beliebige Taste drücken", True, (120, 120, 120))
        screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 40)))

def run_game(screen, ser, display, players, game_name, option, mode):
    is_berry_game = "Bullseye-Berry" in mode
    total_players = players + 1 if is_berry_game else players
    sw, sh = screen.get_width(), screen.get_height()
    screensaver = ScreenSaver(sw, sh)
    display.clear_all()

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
            darker_overlay = pygame.Surface((sw, sh)); darker_overlay.set_alpha(120); darker_overlay.fill((0, 0, 0))
            bg_img.blit(darker_overlay, (0, 0))
        except: pass

    avatar_path = {"Bullseye-Berry (Leicht)": "Bullseye-Berry_Original.png", "Bullseye-Berry (Mittel)": "Bullseye-Berry_Cyber.png", "Bullseye-Berry (Schwer)": "Bullseye-Berry_Ninja.png"}.get(mode, "")
    avatar_img = pygame.image.load(avatar_path).convert_alpha() if avatar_path and os.path.exists(avatar_path) else None
    champ_img = pygame.transform.smoothscale(pygame.image.load("Bullseye-Berry_Champ.png").convert_alpha(), (int(sh*0.45), int(sh*0.45))) if os.path.exists("Bullseye-Berry_Champ.png") else None

    sound_champ = pygame.mixer.Sound("sounds/champ.wav") if os.path.exists("sounds/champ.wav") else None
    sound_single = pygame.mixer.Sound("sounds/hit_single.wav") if os.path.exists("sounds/hit_single.wav") else None
    sound_double = pygame.mixer.Sound("sounds/hit_double.wav") if os.path.exists("sounds/hit_double.wav") else None
    sound_triple = pygame.mixer.Sound("sounds/hit_triple.wav") if os.path.exists("sounds/hit_triple.wav") else None
    sound_switch = pygame.mixer.Sound("sounds/switch_player.wav") if os.path.exists("sounds/switch_player.wav") else None
    sound_miss = pygame.mixer.Sound("sounds/miss.wav") if os.path.exists("sounds/miss.wav") else None

    title_font = pygame.font.SysFont("arial", int(sh * 0.035), bold=True)
    big_font = pygame.font.SysFont("arial", int(sh * 0.05), bold=True)
    giant_font = pygame.font.SysFont("arial", int(sh * 0.23), bold=True)
    HIGHLIGHT, WHITE, RED_COL = (255, 215, 0), (255, 255, 255), (180, 30, 30)

    scores = [40] * total_players
    targets = [15, 16, "D", 17, 18, "T", 19, 20, "B"]
    darts_thrown, active_player, round_points, switch_delay_timer, current_round = 0, 1, 0, 0, 0

    if ser:
        try: ser.write(b"LAMP:PLAYER:1\n"); ser.write(b"LAMP:START:0\n"); ser.flush()
        except: pass

    def sync_hw_display():
        display.clear_buffer()
        display.set_active_player(active_player - 1)
        for i in range(8): display.set_score(i, scores[i] if i < total_players else None)
        tgt = targets[current_round] if current_round < len(targets) else 0
        if isinstance(tgt, int): display.set_temp_score(tgt)
        else: display.set_temp_score(0)
        display.set_dart_arrows(3 - darts_thrown)
        display.update()
    sync_hw_display()

    running, clock, current_state = True, pygame.time.Clock(), "GAME"
    champ_display_until, bot_timer, combo_press_start = 0, 0, 0

    while running:
        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
        is_berrys_turn = (is_berry_game and active_player == total_players)
        
        for event in pygame.event.get():
            if event.type in [pygame.KEYDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer(): raw_data = None; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif event.key == pygame.K_SPACE: raw_data = "BTN:START"
                elif event.key == pygame.K_i: raw_data = "IR:DETECT"
                elif event.key == pygame.K_ESCAPE: running = False

        if raw_data and screensaver.reset_timer(): raw_data = None; continue

        keys = pygame.key.get_pressed()
        if raw_data == "BTN:COMBO": 
            current_state = "ABORT_MENU"
            raw_data = None
        elif keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
            if combo_press_start == 0: 
                combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 3000: 
                current_state = "ABORT_MENU"
                combo_press_start = 0
                raw_data = None
        else: 
            combo_press_start = 0

        if current_state == "ABORT_MENU":
            if raw_data == "BTN:START":
                current_state = "GAME"
                raw_data = None
            elif raw_data == "BTN:PLAYER":
                if sound_switch: sound_switch.play()
                display.clear_all()
                return "menu"

        elif current_state == "GAME":
            if raw_data == "BTN:PLAYER":
                switch_delay_timer = pygame.time.get_ticks(); raw_data = None
            elif raw_data == "IR:DETECT":
                if darts_thrown >= 3 and not is_berrys_turn and switch_delay_timer == 0: switch_delay_timer = pygame.time.get_ticks() + 1000
                raw_data = None
            
            if is_berrys_turn and darts_thrown >= 3 and switch_delay_timer == 0:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + 1000
                elif pygame.time.get_ticks() > bot_timer: switch_delay_timer = pygame.time.get_ticks() + 1000; bot_timer = 0

            if switch_delay_timer > 0 and pygame.time.get_ticks() >= switch_delay_timer:
                switch_delay_timer, darts_thrown, round_points = 0, 0, 0
                active_player = (active_player % total_players) + 1
                if active_player == 1: current_round += 1
                
                if current_round >= len(targets):
                    current_round = len(targets) - 1
                    current_state = "WIN"
                    trigger_victory(ser)
                    display.clear_all()
                    sync_hw_display()
                else:
                    if sound_switch: sound_switch.play()
                    if ser:
                        try: ser.write(b"LAMP:PLAYER:1\n"); ser.flush()
                        except: pass
                    sync_hw_display(); bot_timer = 0; is_berrys_turn = (is_berry_game and active_player == total_players)

            if is_berrys_turn and switch_delay_timer == 0 and darts_thrown < 3:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800) 
                elif pygame.time.get_ticks() > bot_timer:
                    raw_data = f"HIT:{get_bot_hit(targets[current_round], mode)}"; bot_timer = 0 

        if raw_data:
            if current_state == "GAME" and (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
                hit_segment = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                p_idx = active_player - 1
                
                if hit_segment == "MISS":
                    if sound_miss: sound_miss.play()
                elif hit_segment != "-":
                    seg = int(hit_segment.replace("t","").replace("d","").replace("b","25")) if hit_segment != "db" else 25
                    mult = 3 if "t" in hit_segment else (2 if "d" in hit_segment else 1)
                    tgt = targets[current_round]
                    
                    hit_was_useful = False
                    if (isinstance(tgt, int) and seg == tgt) or (tgt == "D" and mult == 2) or (tgt == "T" and mult == 3) or (tgt == "B" and seg == 25):
                        points = seg * mult
                        scores[p_idx] += points
                        round_points += points
                        hit_was_useful = True
                        
                    if hit_was_useful:
                        if hit_segment in ["t18", "t19", "t20", "b", "db"]:
                            champ_display_until = pygame.time.get_ticks() + 2000
                            if sound_champ: sound_champ.play()
                        elif mult == 3 and sound_triple: sound_triple.play()
                        elif mult == 2 and sound_double: sound_double.play()
                        elif sound_single: sound_single.play()
                    else:
                        if sound_single: sound_single.play()

                darts_thrown += 1
                if darts_thrown == 3 and ser:
                    try: ser.write(b"LAMP:PLAYER:2\n"); ser.flush()
                    except: pass
                    if round_points == 0: scores[p_idx] //= 2
                
                sync_hw_display()

            elif current_state == "WIN" and (raw_data in ["BTN:PLAYER", "BTN:START"]):
                if raw_data == "BTN:PLAYER":
                    if sound_switch: sound_switch.play()
                    display.clear_all()
                    return "menu"
                elif raw_data == "BTN:START":
                    if sound_switch: sound_switch.play()
                    scores = [40] * total_players
                    darts_thrown, active_player, round_points, switch_delay_timer, current_round = 0, 1, 0, 0, 0
                    current_state = "GAME"
                    if ser:
                        try: ser.write(b"LAMP:PLAYER:1\n"); ser.write(b"LAMP:START:0\n"); ser.flush()
                        except: pass
                    display.clear_all()
                    sync_hw_display()
                    raw_data = None

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font); pygame.display.flip(); clock.tick(30); continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        if current_state in ["GAME", "ABORT_MENU", "WIN"]:
            target_str = str(targets[current_round]) if current_round < len(targets) else "Ende"
            screen.blit(title_font.render(f"SPIEL: Split Score | Ziel: {target_str}", True, HIGHLIGHT), (int(sw*0.04), int(sh*0.08)))
            name_surf = big_font.render(mode if is_berrys_turn else f"Spieler {active_player}", True, RED_COL if is_berrys_turn else WHITE)
            screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, int(sh*0.14)))
            temp_score_surf = title_font.render(f"(Temp Score: {round_points})", True, (200, 200, 200))
            screen.blit(temp_score_surf, ((sw - temp_score_surf.get_width()) // 2, int(sh*0.20)))
            score_surf = giant_font.render(str(scores[active_player-1]), True, WHITE)
            screen.blit(score_surf, ((sw - score_surf.get_width()) // 2, int(sh*0.27)))
            
            if darts_thrown >= 3 and not is_berrys_turn and current_state == "GAME":
                block_hint = title_font.render("Bitte Pfeile ziehen und Spielerwechsel drücken!", True, RED_COL)
                screen.blit(block_hint, ((sw - block_hint.get_width())//2, int(sh*0.70)))

            darts_surf = big_font.render(f"Pfeile geworfen: {darts_thrown} / 3", True, (150, 150, 150))
            screen.blit(darts_surf, ((sw - darts_surf.get_width()) // 2, int(sh*0.78)))

            y_base = int(sh * 0.86)
            for i in range(total_players):
                p_n = "Berry" if (is_berry_game and i == total_players - 1) else f"P{i+1}"
                surf = title_font.render(f"{p_n}: {scores[i]}", True, HIGHLIGHT if i == (active_player - 1) else WHITE)
                row, col = i % 2, i // 2
                screen.blit(surf, ((col + 1) * (sw // ((total_players + 1) // 2 + 1 if row == 0 else total_players // 2 + 1)) - surf.get_width() // 2, y_base + (row * int(sh*0.05))))

            if is_berrys_turn and avatar_img:
                anim_size = int((sh*0.28) + math.sin(pygame.time.get_ticks() * 0.005) * 15) 
                screen.blit(pygame.transform.smoothscale(avatar_img, (anim_size, anim_size)), (int(sw*0.78), int(sh*0.65)))
            if pygame.time.get_ticks() < champ_display_until and champ_img:
                screen.blit(champ_img, ((sw - champ_img.get_width()) // 2, (sh - champ_img.get_height()) // 2))
                screen.blit(giant_font.render("BOOM!", True, HIGHLIGHT), ((sw - 200) // 2, int(sh*0.75)))

            if current_state == "ABORT_MENU":
                overlay = pygame.Surface((sw, sh))
                overlay.set_alpha(220)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))
                
                menu_y = int(sh * 0.35)
                txt_head = big_font.render("SPIEL ABBRECHEN?", True, HIGHLIGHT)
                screen.blit(txt_head, ((sw - txt_head.get_width()) // 2, menu_y))
                
                txt_start = title_font.render("> START = Weiterspielen <", True, (50, 255, 50))
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, menu_y + int(sh * 0.15)))
                
                txt_end = title_font.render("> SPIELERWECHSEL = Beenden <", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, menu_y + int(sh * 0.25)))
                
            if current_state == "WIN":
                overlay = pygame.Surface((sw, sh))
                overlay.set_alpha(220)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))
                
                win_y = int(sh * 0.25)
                txt_head = giant_font.render("GEWONNEN!", True, (50, 255, 50))
                screen.blit(txt_head, ((sw - txt_head.get_width()) // 2, win_y))
                
                txt_winner = big_font.render("Spiel beendet!", True, WHITE)
                screen.blit(txt_winner, ((sw - txt_winner.get_width()) // 2, win_y + int(sh * 0.25)))
                
                txt_start = title_font.render("> START = Spiel neu starten <", True, (50, 255, 50))
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, win_y + int(sh * 0.40)))
                
                txt_end = title_font.render("> SPIELERWECHSEL = Hauptmenü <", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, win_y + int(sh * 0.50)))
                
        pygame.display.flip(); clock.tick(30)
