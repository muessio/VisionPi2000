# Datei: game_cricket.py
# Version: 1.1.6
# VisionPi2000 - Cricket - Cyber-Circuit-Design, Berry-Rahmenfarben, Vertikale Dynamik & You-Pick-It

import pygame
import math
import os
import random
import time

VERSION = "1.1.6"
GAMES = ["Cricket"]
OPTIONS = [
    "Standard",
    "Cut Throat",
    "You Pick It",
    "You Pick It (Cut Throat)",
    "Crazy (Zufall)",
    "Crazy (Cut Throat)"
]

PLAYER_COLORS = [
    (255, 0, 90),     # Spieler 1 / Berry: Raspberry Pink
    (255, 45, 45),    # Spieler 2: Strawberry Red
    (0, 180, 255),    # Spieler 3: Blueberry Cyan
    (220, 0, 70),     # Spieler 4: Cherry
    (160, 50, 255),   # Spieler 5: Dewberry Purple
    (70, 100, 255),   # Spieler 6: Huckleberry Blue
    (235, 245, 255),  # Spieler 7: Snowberry White-Blue
    (210, 0, 180)     # Spieler 8: Mulberry Magenta
]

if not hasattr(pygame, "_vp2000_cache"):
    pygame._vp2000_cache = {}
_CACHE = pygame._vp2000_cache
_frame_cache = {}


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


def draw_cyber_row_bar(surface, x, y, w, h, p_col, is_act):
    """Zeichnet einen gecachten Cricket-Spielerbalken im Cyber-Circuit-Stil ohne Rand-Clipping."""
    cut = max(6, min(12, h // 4))
    key = ("cyber_row_v2", w, h, p_col, is_act, cut)
    if key not in _frame_cache:
        if len(_frame_cache) > 32:
            _frame_cache.clear()
        bar_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_col = (18, 44, 64, 235) if is_act else (10, 22, 34, 215)
        r = w - 3
        b = h - 3
        pts = [
            (cut, 2), (r - cut, 2), (r, cut), (r, b - cut),
            (r - cut, b), (cut, b), (2, b - cut), (2, cut)
        ]
        pygame.draw.polygon(bar_surf, bg_col, pts)

        if is_act:
            glow_col = (p_col[0], p_col[1], p_col[2], 90)
            pygame.draw.polygon(bar_surf, glow_col, pts, 6)

        pygame.draw.polygon(bar_surf, p_col, pts, 4 if is_act else 3)

        dot_col = (255, 205, 45) if is_act else (140, 115, 40)
        for cx, cy in [(cut + 5, 7), (r - cut - 5, 7), (cut + 5, b - 5), (r - cut - 5, b - 5)]:
            pygame.draw.circle(bar_surf, dot_col, (cx, cy), 2)

        _frame_cache[key] = bar_surf

    surface.blit(_frame_cache[key], (x, y))


def _get_sound(path):
    key = f"snd_{path}"
    if key not in _CACHE:
        if os.path.exists(path):
            try:
                _CACHE[key] = pygame.mixer.Sound(path)
            except Exception:
                _CACHE[key] = None
        else:
            _CACHE[key] = None
    return _CACHE[key]


def _get_font(size):
    key = f"font_{size}"
    if key not in _CACHE:
        _CACHE[key] = pygame.font.SysFont("arial", size, bold=True)
    return _CACHE[key]


def _get_bg(sw, sh):
    is_16_9 = (sw / float(sh)) > 1.5
    key = f"bg_dark160_{sw}_{sh}_{is_16_9}"
    if key not in _CACHE:
        candidates = ["background_16_9.jpg", "background_16_9.png", "background_16_9.PNG"] if is_16_9 else ["background.jpg", "background.png", "Background.png", "background.PNG"]
        bg_img = None
        for bf in candidates:
            if os.path.exists(bf):
                try:
                    raw_bg = pygame.image.load(bf).convert()
                    bg_img = pygame.transform.scale(raw_bg, (sw, sh))
                    darker_overlay = pygame.Surface((sw, sh))
                    darker_overlay.set_alpha(165)
                    darker_overlay.fill((4, 12, 20))
                    bg_img.blit(darker_overlay, (0, 0))
                    break
                except Exception:
                    pass
        _CACHE[key] = bg_img
    return _CACHE[key]


def _get_avatar_frames(avatar_path, sh):
    if not avatar_path:
        return []
    key = f"av28_{avatar_path}_{sh}"
    if key not in _CACHE:
        frames = []
        if os.path.exists(avatar_path):
            try:
                raw_av = pygame.image.load(avatar_path).convert_alpha()
                base_sz = int(sh * 0.28)
                for offset in [-10, -5, 0, 5, 10]:
                    sz = base_sz + offset
                    frames.append(pygame.transform.smoothscale(raw_av, (sz, sz)))
            except Exception:
                pass
        _CACHE[key] = frames
    return _CACHE[key]


def _get_champ_img(sh):
    key = f"champ45_{sh}"
    if key not in _CACHE:
        if os.path.exists("Bullseye-Berry_Champ.png"):
            try:
                _CACHE[key] = pygame.transform.smoothscale(
                    pygame.image.load("Bullseye-Berry_Champ.png").convert_alpha(),
                    (int(sh * 0.45), int(sh * 0.45))
                )
            except Exception:
                _CACHE[key] = None
        else:
            _CACHE[key] = None
    return _CACHE[key]


def trigger_victory(ser, display=None):
    snd = _get_sound("sounds/victory.wav")
    if snd:
        try:
            snd.play()
        except Exception:
            pass
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
        except Exception:
            pass


def get_bot_hit(marks, slot_targets, p_idx, mode):
    diff = 1 if "Stufe 1" in mode else (2 if "Stufe 2" in mode else 3)
    
    open_slots = []
    for s in range(len(slot_targets)):
        if slot_targets[s] is not None and marks[p_idx][s] < 3:
            open_slots.append(slot_targets[s])
            
    if open_slots:
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
        if "ss_avatars_100" not in _CACHE:
            imgs = []
            for file in ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]:
                if os.path.exists(file):
                    try:
                        imgs.append(pygame.transform.smoothscale(pygame.image.load(file).convert_alpha(), (100, 100)))
                    except Exception:
                        pass
            _CACHE["ss_avatars_100"] = imgs
        self.avatars = [
            {"img": img, "x": random.randint(50, max(60, width - 150)), "y": random.randint(50, max(60, height - 150)), "vx": random.choice([-2, 2]), "vy": random.choice([-2, 2])}
            for img in _CACHE["ss_avatars_100"]
        ]
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
    total_players = min(8, players + 1 if is_berry_game else players)
    is_cut_throat = "Cut Throat" in option
    is_pick_it = "You Pick It" in option
    is_crazy = "Crazy" in option

    sw, sh = screen.get_width(), screen.get_height()
    screensaver = ScreenSaver(sw, sh)
    
    if hasattr(display, 'clear_all'):
        display.clear_all()

    bg_img = _get_bg(sw, sh)
    avatar_path = {"Bullseye-Berry (Stufe 1)": "Bullseye-Berry_Original.png", "Bullseye-Berry (Stufe 2)": "Bullseye-Berry_Cyber.png", "Bullseye-Berry (Stufe 3)": "Bullseye-Berry_Ninja.png"}.get(mode, "")
    avatar_frames = _get_avatar_frames(avatar_path, sh)
    champ_img = _get_champ_img(sh)

    sound_champ = _get_sound("sounds/champ.wav")
    sound_single = _get_sound("sounds/hit_single.wav")
    sound_double = _get_sound("sounds/hit_double.wav")
    sound_triple = _get_sound("sounds/hit_triple.wav")
    sound_switch = _get_sound("sounds/switch_player.wav")
    sound_miss = _get_sound("sounds/miss.wav")

    title_font = _get_font(int(sh * 0.030))
    big_font = _get_font(int(sh * 0.044))
    
    avail_matrix_h = int(sh * 0.56)
    row_h = min(int(sh * 0.12), max(int(sh * 0.058), avail_matrix_h // max(1, total_players)))
    row_gap = max(4, int(row_h * 0.10))
    box_h = row_h - row_gap
    
    sb_font_size = min(int(sh * 0.040), max(int(sh * 0.020), int(box_h * 0.46)))
    scoreboard_font = _get_font(sb_font_size)

    win_font_size = int(sh * 0.12) if sh <= 768 else int(sh * 0.16)
    win_font = _get_font(win_font_size)
    giant_font = _get_font(int(sh * 0.20))
    
    HIGHLIGHT, WHITE, RED_COL = (255, 205, 45), (255, 255, 255), (255, 56, 76)
    NEON_GREEN, NEON_CYAN = (0, 255, 157), (0, 216, 255)

    if is_pick_it:
        slot_targets = [None, None, None, None, None, None, 25]
        current_state = "PICK_NUMBERS"
    elif is_crazy:
        rand_nums = random.sample(range(1, 21), 6)
        rand_nums.sort(reverse=True)
        slot_targets = rand_nums + [25]
        current_state = "GAME"
    else:
        slot_targets = [20, 19, 18, 17, 16, 15, 25]
        current_state = "GAME"

    scores = [0] * total_players
    marks = {p: [0] * 7 for p in range(total_players)}
    darts_thrown, active_player = 0, 1
    round_num, round_points, switch_delay_timer = 1, 0, 0

    if ser:
        try: ser.write(b"LAMP:PLAYER:1\n"); ser.write(b"LAMP:START:0\n"); ser.flush()
        except Exception: pass

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
            if current_state == "PICK_NUMBERS":
                remaining_picks = sum(1 for x in slot_targets[:6] if x is None)
                display.set_dart_arrows(min(3, remaining_picks))
            else:
                display.set_dart_arrows(3 - darts_thrown)
            display.update()
        except Exception:
            pass

    def check_win(p_idx):
        if any(slot_targets[s] is None for s in range(7)):
            return False
        if not all(marks[p_idx][s] >= 3 for s in range(7)):
            return False
        if is_cut_throat:
            return all(scores[p_idx] <= scores[j] for j in range(total_players))
        return all(scores[p_idx] >= scores[j] for j in range(total_players))

    sync_hw_display()

    running, clock = True, pygame.time.Clock()
    prev_state = current_state
    champ_display_until, bot_timer = 0, 0
    combo_press_start = 0

    while running:
        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
        is_berrys_turn = (is_berry_game and active_player == total_players and current_state == "GAME")
        
        for event in pygame.event.get():
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer(): raw_data = None; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif event.key == pygame.K_SPACE: raw_data = "BTN:START"
                elif event.key == pygame.K_i: raw_data = "IR:DETECT"
                elif event.key == pygame.K_ESCAPE: running = False

        if raw_data and screensaver.reset_timer(): raw_data = None; continue

        keys = pygame.key.get_pressed()
        if raw_data == "BTN:COMBO": 
            if current_state != "ABORT_MENU":
                prev_state = current_state
            current_state = "ABORT_MENU"
            raw_data = None
        elif keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
            if combo_press_start == 0: 
                combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 3000: 
                if current_state != "ABORT_MENU":
                    prev_state = current_state
                current_state = "ABORT_MENU"
                combo_press_start = 0
                raw_data = None
        else: 
            combo_press_start = 0

        if current_state == "ABORT_MENU":
            if raw_data == "BTN:START":
                current_state = prev_state
                raw_data = None
            elif raw_data == "BTN:PLAYER":
                if sound_switch: sound_switch.play()
                display.clear_all()
                return "menu"

        elif current_state == "PICK_NUMBERS":
            if raw_data and raw_data.startswith("HIT:"):
                hit_segment = raw_data.split(":")[1]
                if hit_segment not in ["-", "b", "db"]:
                    seg = int(hit_segment.replace("t", "").replace("d", ""))
                    if 1 <= seg <= 20 and seg not in slot_targets:
                        for s_i in range(6):
                            if slot_targets[s_i] is None:
                                slot_targets[s_i] = seg
                                if sound_single: sound_single.play()
                                break
                        if None not in slot_targets[:6]:
                            current_state = "GAME"
                            darts_thrown = 0
                            active_player = 1
                            round_num = 1
                            round_points = 0
                            if sound_switch: sound_switch.play()
                        sync_hw_display()
                raw_data = None

        elif current_state == "GAME":
            if raw_data == "BTN:PLAYER":
                switch_delay_timer = pygame.time.get_ticks(); raw_data = None
            elif raw_data == "IR:DETECT":
                if darts_thrown >= 3 and not is_berrys_turn: switch_delay_timer = pygame.time.get_ticks() + 1000
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
                    except Exception: pass
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
                    except Exception: pass
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
                if is_pick_it:
                    slot_targets = [None, None, None, None, None, None, 25]
                    current_state = "PICK_NUMBERS"
                elif is_crazy:
                    rand_nums = random.sample(range(1, 21), 6)
                    rand_nums.sort(reverse=True)
                    slot_targets = rand_nums + [25]
                    current_state = "GAME"
                else:
                    slot_targets = [20, 19, 18, 17, 16, 15, 25]
                    current_state = "GAME"
                scores = [0] * total_players
                marks = {p: [0] * 7 for p in range(total_players)}
                darts_thrown, active_player, round_num, round_points, switch_delay_timer = 0, 1, 1, 0, 0
                if ser:
                    try: ser.write(b"LAMP:PLAYER:1\n"); ser.write(b"LAMP:START:0\n"); ser.flush()
                    except Exception: pass
                display.clear_all()
                sync_hw_display()
                raw_data = None

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font); pygame.display.flip(); clock.tick(30); continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((6, 17, 28))

        if current_state in ["PICK_NUMBERS", "GAME", "ABORT_MENU", "WIN"]:
            # --- GROSSES CYBER-CIRCUIT RAHMENPANEL FÜR CRICKET ---
            hud_w = int(sw * 0.92)
            hud_x = (sw - hud_w) // 2
            hud_y = int(sh * 0.02)
            hud_h = int(sh * 0.95)
            draw_cyber_frame(screen, hud_x, hud_y, hud_w, hud_h, cut=22)

            head_txt = f"SPIEL: CRICKET   •   {option.upper()}   •   RUNDE {round_num}"
            head_surf = title_font.render(head_txt, True, HIGHLIGHT)
            screen.blit(head_surf, ((sw - head_surf.get_width()) // 2, hud_y + int(sh * 0.016)))

            line_y = hud_y + int(sh * 0.064)
            pygame.draw.line(screen, NEON_GREEN, (hud_x + 35, line_y), (hud_x + hud_w - 35, line_y), 2)
            pygame.draw.circle(screen, HIGHLIGHT, (sw // 2, line_y), 5)

            act_col = PLAYER_COLORS[0] if is_berrys_turn else PLAYER_COLORS[(active_player - 1) % len(PLAYER_COLORS)]
            
            if current_state == "PICK_NUMBERS":
                picked_cnt = sum(1 for x in slot_targets[:6] if x is not None)
                name_surf = big_font.render(f"▶  Zahlenauswahl ({picked_cnt} / 6 gewählt)  ◀", True, HIGHLIGHT)
                screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, int(sh * 0.095)))
                pick_hint = title_font.render("YOU PICK IT: Bitte vor Spielbeginn 6 verschiedene Zahlen (1–20) drücken!", True, NEON_GREEN)
                screen.blit(pick_hint, ((sw - pick_hint.get_width()) // 2, int(sh * 0.165)))
            else:
                active_label = mode if is_berrys_turn else f"Spieler {active_player}"
                name_surf = big_font.render(f"▶  {active_label}  ◀", True, act_col)
                screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, int(sh * 0.095)))

                temp_score_surf = title_font.render(f"Runden-Punkte: {round_points}   •   Pfeile: {darts_thrown} / 3", True, NEON_CYAN)
                ts_total_w = temp_score_surf.get_width() + 85
                ts_x = (sw - ts_total_w) // 2
                ts_y = int(sh * 0.155)
                screen.blit(temp_score_surf, (ts_x, ts_y))
                dot_base_x = ts_x + temp_score_surf.get_width() + 22
                dot_cy = ts_y + temp_score_surf.get_height() // 2
                for d_i in range(3):
                    is_rem = d_i < (3 - darts_thrown)
                    c_dot = NEON_GREEN if is_rem else (35, 60, 75)
                    pygame.draw.circle(screen, c_dot, (dot_base_x + d_i * 22, dot_cy), 7)
                    pygame.draw.circle(screen, HIGHLIGHT if is_rem else (70, 95, 110), (dot_base_x + d_i * 22, dot_cy), 7, 2)
                
                if darts_thrown >= 3 and not is_berrys_turn and current_state == "GAME":
                    block_hint = title_font.render("Bitte Pfeile ziehen  ▶  IR-Sensor oder Spielerwechsel drücken!", True, RED_COL)
                    bh_w = block_hint.get_width() + 36
                    bh_h = block_hint.get_height() + 8
                    bh_x = (sw - bh_w) // 2
                    bh_y = int(sh * 0.205)
                    pygame.draw.rect(screen, (42, 14, 22), (bh_x, bh_y, bh_w, bh_h), border_radius=8)
                    pygame.draw.rect(screen, RED_COL, (bh_x, bh_y, bh_w, bh_h), 2, border_radius=8)
                    screen.blit(block_hint, (bh_x + 18, bh_y + 4))

            matrix_y = int(sh * 0.265)
            labels = ["B" if t == 25 else ("--" if t is None else str(t)) for t in slot_targets]
            
            col_w = int(sw * 0.075)
            score_w = int(sw * 0.12)
            name_w = int(sw * 0.16)
            total_w = name_w + score_w + len(labels) * col_w
            start_x = (sw - total_w) // 2
            
            pygame.draw.line(screen, NEON_GREEN, (start_x - 10, matrix_y + int(sh*0.042)), (start_x + total_w + 10, matrix_y + int(sh*0.042)), 2)
            screen.blit(title_font.render("Punkte", True, HIGHLIGHT), (start_x + name_w, matrix_y))
            for idx, lbl in enumerate(labels):
                lbl_col = (120, 135, 150) if lbl == "--" else HIGHLIGHT
                t_surf = title_font.render(lbl, True, lbl_col)
                screen.blit(t_surf, (start_x + name_w + score_w + idx * col_w + (col_w - t_surf.get_width())//2, matrix_y))
                
            rows_start_y = matrix_y + int(sh * 0.052)
            for p_idx in range(total_players):
                p_y = rows_start_y + p_idx * row_h
                is_act = (p_idx == (active_player - 1)) and (current_state != "PICK_NUMBERS")
                p_col = PLAYER_COLORS[0] if (is_berry_game and p_idx == total_players - 1) else PLAYER_COLORS[p_idx % len(PLAYER_COLORS)]
                p_label = "Berry" if (is_berry_game and p_idx == total_players - 1) else f"Spieler {p_idx+1}"
                
                draw_cyber_row_bar(screen, start_x - 12, p_y, total_w + 24, box_h, p_col, is_act)

                pn_s = scoreboard_font.render(p_label, True, p_col)
                sc_s = scoreboard_font.render(str(scores[p_idx]), True, HIGHLIGHT if is_act else WHITE)
                text_y = p_y + (box_h - pn_s.get_height()) // 2
                screen.blit(pn_s, (start_x + 8, text_y))
                screen.blit(sc_s, (start_x + name_w, text_y))
                
                c_size = max(8, int(min(box_h, col_w) * 0.28))
                lw = max(3, int(box_h * 0.08))
                mark_y = p_y + box_h // 2
                
                for s_idx in range(7):
                    hits = marks[p_idx][s_idx]
                    col_left = start_x + name_w + score_w + s_idx * col_w
                    pygame.draw.line(screen, (25, 55, 75), (col_left, p_y + 6), (col_left, p_y + box_h - 6), 1)
                    mark_x = col_left + col_w // 2
                    
                    if hits >= 1: 
                        pygame.draw.line(screen, p_col, (mark_x - c_size, mark_y + c_size), (mark_x + c_size, mark_y - c_size), lw)
                    if hits >= 2: 
                        pygame.draw.line(screen, p_col, (mark_x - c_size, mark_y - c_size), (mark_x + c_size, mark_y + c_size), lw)
                    if hits == 3: 
                        pygame.draw.circle(screen, HIGHLIGHT if is_act else p_col, (mark_x, mark_y), int(c_size * 1.28), lw)

            if is_berrys_turn and avatar_frames:
                idx_anim = int((math.sin(pygame.time.get_ticks() * 0.005) + 1.0) * 2.49)
                idx_anim = max(0, min(len(avatar_frames) - 1, idx_anim))
                screen.blit(avatar_frames[idx_anim], (int(sw*0.76), int(sh*0.60)))
            if pygame.time.get_ticks() < champ_display_until and champ_img:
                screen.blit(champ_img, ((sw - champ_img.get_width()) // 2, (sh - champ_img.get_height()) // 2))
                screen.blit(giant_font.render("BOOM!", True, HIGHLIGHT), ((sw - 200) // 2, int(sh*0.45)))

            if current_state == "ABORT_MENU":
                overlay = pygame.Surface((sw, sh))
                overlay.set_alpha(210)
                overlay.fill((4, 10, 18))
                screen.blit(overlay, (0, 0))
                
                pop_w, pop_h = int(sw * 0.66), int(sh * 0.46)
                pop_x, pop_y = (sw - pop_w) // 2, (sh - pop_h) // 2
                draw_cyber_frame(screen, pop_x, pop_y, pop_w, pop_h, cut=22)

                txt_head = big_font.render("SPIEL ABBRECHEN?", True, HIGHLIGHT)
                screen.blit(txt_head, ((sw - txt_head.get_width()) // 2, pop_y + int(pop_h * 0.14)))
                pygame.draw.line(screen, NEON_GREEN, (pop_x + 40, pop_y + int(pop_h * 0.32)), (pop_x + pop_w - 40, pop_y + int(pop_h * 0.32)), 2)
                
                txt_start = title_font.render("▶  START = Weiterspielen  ◀", True, NEON_GREEN)
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, pop_y + int(pop_h * 0.48)))
                
                txt_end = title_font.render("▶  SPIELERWECHSEL = Beenden  ◀", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, pop_y + int(pop_h * 0.68)))
                
            if current_state == "WIN":
                overlay = pygame.Surface((sw, sh))
                overlay.set_alpha(215)
                overlay.fill((4, 10, 18))
                screen.blit(overlay, (0, 0))
                
                pop_w, pop_h = int(sw * 0.78), int(sh * 0.66)
                pop_x, pop_y = (sw - pop_w) // 2, (sh - pop_h) // 2
                draw_cyber_frame(screen, pop_x, pop_y, pop_w, pop_h, cut=24)

                txt_head = win_font.render("GEWONNEN!", True, NEON_GREEN)
                screen.blit(txt_head, ((sw - txt_head.get_width()) // 2, pop_y + int(pop_h * 0.08)))
                
                winner_name = mode if is_berrys_turn else f"Spieler {active_player}"
                txt_winner = big_font.render(f"{winner_name} beendet!", True, act_col)
                screen.blit(txt_winner, ((sw - txt_winner.get_width()) // 2, pop_y + int(pop_h * 0.42)))
                pygame.draw.line(screen, NEON_GREEN, (pop_x + 50, pop_y + int(pop_h * 0.56)), (pop_x + pop_w - 50, pop_y + int(pop_h * 0.56)), 2)
                
                txt_start = title_font.render("▶  START = Spiel neu starten  ◀", True, NEON_GREEN)
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, pop_y + int(pop_h * 0.66)))
                
                txt_end = title_font.render("▶  SPIELERWECHSEL = Hauptmenü  ◀", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, pop_y + int(pop_h * 0.80)))
                
        pygame.display.flip(); clock.tick(30)
