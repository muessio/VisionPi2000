import pygame
import math
import os
import random
import time
import json

VERSION = "1.1.0"
GAMES = ["Cricket"]
OPTIONS = [
    "Standard",
    "Cut Throat",
    "You Pick It",
    "You Pick It (Cut Throat)",
    "Crazy (Zufall)",
    "Crazy (Cut Throat)"
]

def trigger_victory(ser, display=None):
    if os.path.exists("sounds/victory.wav"):
        try: pygame.mixer.Sound("sounds/victory.wav").play()
        except: pass
    if ser or display:
        try:
            for _ in range(6):
                if display: display.set_light(True)
                if ser: ser.write(b"TEST:ON\n"); ser.flush()
                time.sleep(0.25)
                
                if display: display.set_light(False)
                if ser: ser.write(b"TEST:OFF\n"); ser.flush()
                time.sleep(0.25)
                
            if display: display.set_light(True)
            if ser:
                ser.write(b"LAMP:PLAYER:2\n")
                ser.write(b"LAMP:START:0\n")
                ser.flush()
        except: pass

def get_bot_hit(marks, slot_targets, p_idx, mode):
    diff = 1 if "Stufe 1" in mode else (2 if "Stufe 2" in mode else 3)
    
    open_slots = []
    for s in range(len(slot_targets)):
        if slot_targets[s] is not None and marks[p_idx][s] < 3:
            open_slots.append(slot_targets[s])
            
    unpicked_slots = [s for s in range(len(slot_targets) - 1) if slot_targets[s] is None]
    if unpicked_slots and (not open_slots or random.random() < 0.6):
        used_nums = [t for t in slot_targets if t is not None]
        free_nums = [n for n in range(1, 21) if n not in used_nums]
        target = random.choice(free_nums) if free_nums else 20
    elif open_slots:
        target = random.choice(open_slots)
    else:
        target = slot_targets[0] if slot_targets[0] is not None else 20

    if diff == 1:
        return "b" if target == 25 else str(random.choice([1, 5, target]))
    elif diff == 2:
        r = random.random()
        return f"t{target}" if target != 25 and r < 0.3 else (str(target) if target != 25 and r < 0.8 else ("b" if target == 25 else str(random.randint(1, 20))))
    else:
        r = random.random()
        return f"t{target}" if target != 25 and r < 0.6 else (str(target) if target != 25 and r < 0.9 else ("db" if target == 25 and r < 0.5 else "b"))

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
        hint_surf = font.render("STANDBY – Beliebige Taste drücken zum Fortfahren", True, (120, 120, 120))
        screen.blit(hint_surf, hint_surf.get_rect(center=(self.width // 2, self.height - 40)))

def run_game(screen, ser, display, players, game_name, option, mode):
    is_berry_game = "Bullseye-Berry" in mode
    total_players = players + 1 if is_berry_game else players
    is_cut_throat = "Cut Throat" in option
    is_pick_it = "You Pick It" in option
    is_crazy = "Crazy" in option

    sw, sh = screen.get_width(), screen.get_height()
    screensaver = ScreenSaver(sw, sh)
    
    if hasattr(display, 'clear_all'):
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
            darker_overlay = pygame.Surface((sw, sh))
            darker_overlay.set_alpha(160)
            darker_overlay.fill((0, 0, 0))
            bg_img.blit(darker_overlay, (0, 0))
        except: pass

    avatar_path = {"Bullseye-Berry (Stufe 1)": "Bullseye-Berry_Original.png", "Bullseye-Berry (Stufe 2)": "Bullseye-Berry_Cyber.png", "Bullseye-Berry (Stufe 3)": "Bullseye-Berry_Ninja.png"}.get(mode, "")
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
    
    # Dynamische Schriftgröße für den Gewinner-Text (4:3 vs 16:9 angepasst)
    win_font_size = int(sh * 0.13) if sh <= 768 else int(sh * 0.23)
    win_font = pygame.font.SysFont("arial", win_font_size, bold=True)
    giant_font = pygame.font.SysFont("arial", int(sh * 0.23), bold=True)
    
    HIGHLIGHT, WHITE, RED_COL = (255, 215, 0), (255, 255, 255), (180, 30, 30)

    if is_pick_it:
        slot_targets = [None, None, None, None, None, None, 25]
    elif is_crazy:
        rand_nums = random.sample(range(1, 21), 6)
        rand_nums.sort(reverse=True)
        slot_targets = rand_nums + [25]
    else:
        slot_targets = [20, 19, 18, 17, 16, 15, 25]

    scores = [0] * total_players
    marks = {p: [0] * 7 for p in range(total_players)}
    darts_thrown, active_player = 0, 1
    round_num, round_points, switch_delay_timer = 1, 0, 0

    if ser:
        try: ser.write(b"LAMP:PLAYER:1\n"); ser.write(b"LAMP:START:0\n"); ser.flush()
        except: pass

    def sync_hw_display():
        try:
            display.clear_buffer()
            display.set_active_player(active_player - 1)
                
            for i in range(8):
                display.set_score(i, scores[i] if i < total_players else None)
            
            hw_keys = [20, 19, 18, 17, 16, 15]
            for s_idx, hw_key in enumerate(hw_keys):
                t_val = slot_targets[s_idx]
                
                for p in range(total_players):
                    display.set_cricket_marks(p, hw_key, marks[p][s_idx])
                
                if hasattr(display, 'CRICKET_TARGET_DISP') and hw_key in display.CRICKET_TARGET_DISP:
                    d_ten, d_unit = display.CRICKET_TARGET_DISP[hw_key]
                    if t_val is None:
                        display.set_disp_char(d_ten, "-")
                        display.set_disp_char(d_unit, "-")
                    else:
                        t_str = f"{t_val:2d}"
                        display.set_disp_char(d_ten, t_str[0])
                        display.set_disp_char(d_unit, t_str[1])

            for p in range(total_players):
                display.set_cricket_marks(p, 25, marks[p][6])
                        
            display.set_temp_score(round_points)
            display.set_turn(round_num)
            display.set_dart_arrows(3 - darts_thrown)
            display.update()
        except: pass

    def check_win(p_idx):
        if any(slot_targets[s] is None for s in range(7)):
            return False
        if not all(marks[p_idx][s] >= 3 for s in range(7)):
            return False
        if is_cut_throat:
            return all(scores[p_idx] <= scores[j] for j in range(total_players))
        return all(scores[p_idx] >= scores[j] for j in range(total_players))

    sync_hw_display()

    running, clock, current_state = True, pygame.time.Clock(), "GAME"
    champ_display_until, bot_timer = 0, 0
    combo_press_start = 0

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
                if active_player == total_players:
                    round_num += 1
                active_player = (active_player % total_players) + 1
                if sound_switch: sound_switch.play()
                if ser:
                    try: ser.write(b"LAMP:PLAYER:1\n"); ser.flush()
                    except: pass
                sync_hw_display(); bot_timer = 0; is_berrys_turn = (is_berry_game and active_player == total_players)

            if is_berrys_turn and switch_delay_timer == 0 and darts_thrown < 3:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800) 
                elif pygame.time.get_ticks() > bot_timer:
                    raw_data = f"HIT:{get_bot_hit(marks, slot_targets, active_player-1, mode)}"
                    bot_timer = 0 

            if raw_data and (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
                hit_segment = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                p_idx = active_player - 1
                
                if hit_segment == "MISS":
                    if sound_miss: sound_miss.play()
                elif hit_segment != "-":
                    seg = int(hit_segment.replace("t","").replace("d","").replace("b","25")) if hit_segment != "db" else 25
                    mult = 3 if "t" in hit_segment else (2 if "d" in hit_segment else 1)
                    
                    if is_pick_it and 1 <= seg <= 20 and seg not in slot_targets:
                        for s_i in range(6):
                            if slot_targets[s_i] is None:
                                slot_targets[s_i] = seg
                                break

                    hit_was_useful = False
                    if seg in slot_targets:
                        s_idx = slot_targets.index(seg)
                        for _ in range(mult):
                            if marks[p_idx][s_idx] < 3: 
                                marks[p_idx][s_idx] += 1
                                hit_was_useful = True
                            elif not all(marks[i][s_idx] >= 3 for i in range(total_players)):
                                if is_cut_throat:
                                    for other_p in range(total_players):
                                        if marks[other_p][s_idx] < 3:
                                            scores[other_p] += seg
                                    round_points += seg
                                else:
                                    scores[p_idx] += seg
                                    round_points += seg
                                hit_was_useful = True

                    if hit_was_useful:
                        if (mult == 3 and seg >= 18) or hit_segment in ["b", "db"]:
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
                sync_hw_display()
                
                if check_win(p_idx):
                    current_state = "WIN"
                    trigger_victory(ser, display)
                    display.clear_all()
                    sync_hw_display()

        elif current_state == "WIN" and (raw_data in ["BTN:PLAYER", "BTN:START"]):
            if raw_data == "BTN:PLAYER":
                if sound_switch: sound_switch.play()
                display.clear_all()
                return "menu"
            elif raw_data == "BTN:START":
                if sound_switch: sound_switch.play()
                if is_pick_it: slot_targets = [None, None, None, None, None, None, 25]
                elif is_crazy:
                    rand_nums = random.sample(range(1, 21), 6)
                    rand_nums.sort(reverse=True)
                    slot_targets = rand_nums + [25]
                else: slot_targets = [20, 19, 18, 17, 16, 15, 25]
                scores = [0] * total_players
                marks = {p: [0] * 7 for p in range(total_players)}
                darts_thrown, active_player, round_num, round_points, switch_delay_timer = 0, 1, 1, 0, 0
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
            screen.blit(title_font.render(f"SPIEL: Cricket | {option} | Runde {round_num}", True, HIGHLIGHT), (int(sw*0.04), int(sh*0.04)))
            name_surf = big_font.render(mode if is_berrys_turn else f"Spieler {active_player}", True, RED_COL if is_berrys_turn else WHITE)
            screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, int(sh*0.10)))
            temp_score_surf = title_font.render(f"Temp Score: {round_points}   |   Pfeile geworfen: {darts_thrown} / 3", True, (200, 200, 200))
            screen.blit(temp_score_surf, ((sw - temp_score_surf.get_width()) // 2, int(sh*0.18)))
            
            if darts_thrown >= 3 and not is_berrys_turn and current_state == "GAME":
                block_hint = title_font.render("Bitte Pfeile ziehen und Spielerwechsel drücken!", True, RED_COL)
                screen.blit(block_hint, ((sw - block_hint.get_width())//2, int(sh*0.25)))
            elif is_pick_it and None in slot_targets[:6] and current_state == "GAME":
                pick_hint = title_font.render("YOU PICK IT: Wirf auf eine freie Zahl (1–20), um sie auszuwählen!", True, (50, 255, 50))
                screen.blit(pick_hint, ((sw - pick_hint.get_width())//2, int(sh*0.25)))

            matrix_y = int(sh * 0.32)
            labels = ["B" if t == 25 else ("--" if t is None else str(t)) for t in slot_targets]
            
            col_w = int(sw * 0.07)
            score_w = int(sw * 0.12)
            name_w = int(sw * 0.15)
            total_w = name_w + score_w + len(labels) * col_w
            start_x = (sw - total_w) // 2
            
            pygame.draw.line(screen, (100,100,100), (start_x, matrix_y + int(sh*0.05)), (start_x + total_w, matrix_y + int(sh*0.05)), 2)
            screen.blit(title_font.render("Punkte", True, HIGHLIGHT), (start_x + name_w, matrix_y))
            for idx, lbl in enumerate(labels):
                lbl_col = (120, 120, 120) if lbl == "--" else HIGHLIGHT
                t_surf = title_font.render(lbl, True, lbl_col)
                screen.blit(t_surf, (start_x + name_w + score_w + idx * col_w + (col_w - t_surf.get_width())//2, matrix_y))
                
            row_h = int(sh * 0.065)
            for p_idx in range(total_players):
                p_y = matrix_y + int(sh*0.07) + p_idx * row_h
                p_color = HIGHLIGHT if p_idx == (active_player - 1) else WHITE
                p_label = "Berry" if (is_berry_game and p_idx == total_players - 1) else f"Spieler {p_idx+1}"
                
                if p_idx == (active_player - 1):
                    s_rect = pygame.Surface((total_w, row_h))
                    s_rect.set_alpha(40); s_rect.fill(HIGHLIGHT)
                    screen.blit(s_rect, (start_x, p_y - 5))

                screen.blit(title_font.render(p_label, True, p_color), (start_x, p_y))
                screen.blit(title_font.render(str(scores[p_idx]), True, p_color), (start_x + name_w, p_y))
                
                for s_idx in range(7):
                    hits = marks[p_idx][s_idx]
                    mark_x = start_x + name_w + score_w + s_idx * col_w + col_w // 2
                    mark_y = p_y + row_h // 2 - 5
                    c_size = int(row_h * 0.35)
                    lw = 4 
                    
                    if hits >= 1: 
                        pygame.draw.line(screen, p_color, (mark_x - c_size, mark_y + c_size), (mark_x + c_size, mark_y - c_size), lw)
                    if hits >= 2: 
                        pygame.draw.line(screen, p_color, (mark_x - c_size, mark_y - c_size), (mark_x + c_size, mark_y + c_size), lw)
                    if hits == 3: 
                        pygame.draw.circle(screen, p_color, (mark_x, mark_y), int(c_size * 1.3), lw)

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
                
                win_y = int(sh * 0.22)
                txt_head = win_font.render("GEWONNEN!", True, (50, 255, 50))
                screen.blit(txt_head, ((sw - txt_head.get_width()) // 2, win_y))
                
                winner_name = mode if is_berrys_turn else f"Spieler {active_player}"
                txt_winner = big_font.render(f"{winner_name} beendet!", True, WHITE)
                screen.blit(txt_winner, ((sw - txt_winner.get_width()) // 2, win_y + int(sh * 0.22)))
                
                txt_start = title_font.render("> START = Spiel neu starten <", True, (50, 255, 50))
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, win_y + int(sh * 0.36)))
                
                txt_end = title_font.render("> SPIELERWECHSEL = Hauptmenü <", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, win_y + int(sh * 0.46)))
                
        pygame.display.flip(); clock.tick(30)
