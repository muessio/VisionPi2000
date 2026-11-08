# Datei: game_x01.py
# Version: 1.1.8
# VisionPi2000 - X01 (301, 501, 701) - Cyber-Circuit-Design, Berry-Rahmenfarben & Fast-Load Cache

import pygame
import math
import os
import random
import time

VERSION = "1.1.8"
GAMES = ["301", "501", "701"]
OPTIONS = ["Open In/Out", "Double In", "Double Out", "Master Out", "Double In/Out", "Double In / Master Out"]

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
    """Zeichnet den gecachten VisionPi2000 Cyber-Tech-Rahmen wie im Service-Menü."""
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


def draw_cyber_player_card(surface, x, y, w, h, p_col, is_act, cut=12):
    """Zeichnet eine gecachte Spieler-/Team-Karte im Cyber-Circuit-Stil mit Berry-Farben ohne Rand-Clipping."""
    key = ("cyber_card_v2", w, h, p_col, is_act, cut)
    if key not in _frame_cache:
        if len(_frame_cache) > 32:
            _frame_cache.clear()
        card_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_col = (18, 42, 62, 235) if is_act else (8, 20, 32, 220)
        
        r = w - 3
        b = h - 3
        pts = [
            (cut, 2), (r - cut, 2), (r, cut), (r, b - cut),
            (r - cut, b), (cut, b), (2, b - cut), (2, cut)
        ]
        pygame.draw.polygon(card_surf, bg_col, pts)

        if is_act:
            glow_col = (p_col[0], p_col[1], p_col[2], 95)
            pygame.draw.polygon(card_surf, glow_col, pts, 7)

        pygame.draw.polygon(card_surf, p_col, pts, 4 if is_act else 3)

        div_y = int(h * 0.30)
        line_col = p_col if is_act else (p_col[0] // 2, p_col[1] // 2, p_col[2] // 2, 200)
        pygame.draw.line(card_surf, line_col, (12, div_y), (w - 12, div_y), 2)

        dot_col = (255, 205, 45) if is_act else (140, 115, 40)
        for cx, cy in [(cut + 6, 8), (r - cut - 6, 8), (cut + 6, b - 6), (r - cut - 6, b - 6)]:
            pygame.draw.circle(card_surf, dot_col, (cx, cy), 3)

        _frame_cache[key] = card_surf

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
            for _ in range(3):
                if display: display.set_light(True)
                if ser: ser.write(b"TEST:ON
"); ser.flush()
                time.sleep(0.15)
                
                if display: display.set_light(False)
                if ser: ser.write(b"TEST:OFF
"); ser.flush()
                time.sleep(0.15)
                
            if display: display.set_light(True)
            if ser:
                ser.write(b"LAMP:PLAYER:2
")
                ser.write(b"LAMP:START:1
")
                ser.flush()
        except Exception:
            pass


def parse_hit(hit_str):
    if hit_str == "-": return 0
    if hit_str == "b": return 25   
    if hit_str == "db": return 50  
    if hit_str.startswith("d"): return int(hit_str[1:]) * 2
    if hit_str.startswith("t"): return int(hit_str[1:]) * 3
    return int(hit_str)

def check_double(hit_str): return hit_str.startswith("d") or hit_str == "db"
def check_master(hit_str): return hit_str.startswith("d") or hit_str.startswith("t") or hit_str in ["b", "db"]

def get_bot_hit(score, mode, option):
    diff = 1 
    if "Stufe 2" in mode: diff = 2
    elif "Stufe 3" in mode: diff = 3
    if option != "Open In/Out":
        if score <= 40 and score % 2 == 0:
            target_double = score // 2
            if random.random() < {1: 0.10, 2: 0.35, 3: 0.80}[diff]: return f"d{target_double}"
            else: return str(target_double) if random.random() < 0.5 else "-"
        elif score <= 40 and score % 2 != 0: return "1"
    if score <= 40 and option == "Open In/Out":
        if random.random() < {1: 0.30, 2: 0.60, 3: 0.95}[diff]: return str(score)
        else: return "-"
    if diff == 1: return str(random.randint(1, 20))
    elif diff == 2:
        r = random.random()
        return "t20" if r < 0.30 else ("20" if r < 0.70 else ("t19" if r < 0.85 else str(random.choice([1, 5, 19]))))
    else: 
        r = random.random()
        return "t20" if r < 0.70 else ("20" if r < 0.90 else "t19")


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


def build_turn_order(total_players, is_team_mode):
    if not is_team_mode:
        return list(range(1, total_players + 1))
    num_teams = (total_players + 1) // 2
    order = []
    for member_slot in range(2):
        for t in range(num_teams):
            p = t * 2 + 1 + member_slot
            if p <= total_players:
                order.append(p)
    return order


def run_game(screen, ser, display, players, game_name, option, mode):
    is_berry_game = "Bullseye-Berry" in mode
    is_team_mode = ("Team" in mode) and (players >= 2)
    total_players = players + 1 if is_berry_game else players
    num_teams = (total_players + 1) // 2 if is_team_mode else total_players

    turn_order = build_turn_order(total_players, is_team_mode)
    turn_idx = 0
    active_player = turn_order[turn_idx]

    def get_team_idx(p_idx):
        return (p_idx // 2) if is_team_mode else p_idx

    def set_team_score(p_idx, val):
        if is_team_mode:
            t = p_idx // 2
            for m in (t * 2, t * 2 + 1):
                if m < total_players:
                    player_scores[m] = val
        else:
            player_scores[p_idx] = val

    def set_team_in_checked(p_idx, val):
        if is_team_mode:
            t = p_idx // 2
            for m in (t * 2, t * 2 + 1):
                if m < total_players:
                    player_in_checked[m] = val
        else:
            player_in_checked[p_idx] = val

    sw, sh = screen.get_width(), screen.get_height()
    screensaver = ScreenSaver(sw, sh)
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
    sound_bust = _get_sound("sounds/bust.wav")
    sound_miss = _get_sound("sounds/miss.wav")

    title_font = _get_font(int(sh * 0.030))
    big_font = _get_font(int(sh * 0.044))
    
    sb_font_size = int(sh * 0.025) if total_players <= 4 else (int(sh * 0.021) if total_players <= 6 else int(sh * 0.018))
    scoreboard_font = _get_font(sb_font_size)

    win_font_size = int(sh * 0.12) if sh <= 768 else int(sh * 0.16)
    win_font = _get_font(win_font_size)
    giant_font = _get_font(int(sh * 0.20))
    
    HIGHLIGHT, WHITE, RED_COL = (255, 205, 45), (255, 255, 255), (255, 56, 76)
    NEON_GREEN, NEON_CYAN = (0, 255, 157), (0, 216, 255)

    try: start_score = int(game_name)
    except Exception: start_score = 501
    player_scores = [start_score] * total_players
    has_double_in = option in ["Double In", "Double In/Out", "Double In / Master Out"]
    has_double_out = option in ["Double Out", "Double In/Out"]
    has_master_out = option in ["Master Out", "Double In / Master Out"]
    player_in_checked = [not has_double_in for _ in range(total_players)]
    
    darts_thrown, round_num, round_points = 0, 1, 0
    round_start_score, round_start_in_checked = start_score, player_in_checked[0]
    switch_delay_timer = 0

    if ser:
        try: ser.write(b"LAMP:PLAYER:1
"); ser.write(b"LAMP:START:0
"); ser.flush()
        except Exception: pass

    def sync_hw_display():
        display.clear_buffer()
        for i in range(8):
            display.set_score(i, max(0, player_scores[i]) if i < total_players else None)
        display.set_active_player(active_player - 1)
        display.set_dart_arrows(3 - darts_thrown)
        display.set_temp_score(round_points)
        display.set_turn(round_num)
        display.update()
    sync_hw_display()

    running, clock, current_state = True, pygame.time.Clock(), "GAME"
    champ_display_until, bot_timer, combo_press_start = 0, 0, 0

    while running:
        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
        is_berrys_turn = (is_berry_game and active_player == total_players)

        for event in pygame.event.get():
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer(): raw_data = None; continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif event.key == pygame.K_i: raw_data = "IR:DETECT"
                elif event.key == pygame.K_0: raw_data = "HIT:WIN_CHEAT"
                elif event.key == pygame.K_r: raw_data = "BTN:RED"
                elif event.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif event.key == pygame.K_g: raw_data = "BTN:GREY"
                elif event.key == pygame.K_SPACE: raw_data = "BTN:START"
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

        elif current_state == "WIN":
            # Sofortige Tasten-Reaktion im Sieg-Zustand (Start für Neustart, Spielerwechsel für Hauptmenü)
            if raw_data == "BTN:PLAYER" or keys[pygame.K_p]:
                if sound_switch: sound_switch.play()
                display.clear_all()
                return "menu"
            elif raw_data == "BTN:START" or keys[pygame.K_SPACE]:
                if sound_switch: sound_switch.play()
                player_scores = [start_score] * total_players
                player_in_checked = [not has_double_in for _ in range(total_players)]
                turn_idx = 0
                active_player = turn_order[turn_idx]
                darts_thrown, round_num, round_points = 0, 1, 0
                round_start_score, round_start_in_checked = start_score, player_in_checked[0]
                switch_delay_timer = 0
                current_state = "GAME"
                if ser:
                    try: ser.write(b"LAMP:PLAYER:1
"); ser.write(b"LAMP:START:0
"); ser.flush()
                    except Exception: pass
                display.clear_all()
                sync_hw_display()
                raw_data = None

        elif current_state == "GAME":
            if raw_data == "BTN:PLAYER":
                switch_delay_timer = pygame.time.get_ticks(); raw_data = None
            elif raw_data == "IR:DETECT":
                if darts_thrown >= 3 and not is_berrys_turn: switch_delay_timer = pygame.time.get_ticks() + 2000
                raw_data = None
            
            if is_berrys_turn and darts_thrown >= 3 and switch_delay_timer == 0:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + 1000
                elif pygame.time.get_ticks() > bot_timer: switch_delay_timer = pygame.time.get_ticks() + 1000; bot_timer = 0

            if switch_delay_timer > 0 and pygame.time.get_ticks() >= switch_delay_timer:
                switch_delay_timer, darts_thrown, round_points = 0, 0, 0
                turn_idx = (turn_idx + 1) % len(turn_order)
                if turn_idx == 0:
                    round_num += 1
                active_player = turn_order[turn_idx]
                round_start_score = player_scores[active_player - 1]
                round_start_in_checked = player_in_checked[active_player - 1]
                if sound_switch: sound_switch.play()
                if ser:
                    try: ser.write(b"LAMP:PLAYER:1
"); ser.flush()
                    except Exception: pass
                sync_hw_display(); bot_timer = 0; is_berrys_turn = (is_berry_game and active_player == total_players)

            if is_berrys_turn and switch_delay_timer == 0 and darts_thrown < 3:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800) 
                elif pygame.time.get_ticks() > bot_timer:
                    raw_data = f"HIT:{get_bot_hit(player_scores[active_player-1], mode, option)}"; bot_timer = 0 

        if raw_data and current_state == "GAME":
            if (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
                hit_segment = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                p_idx = active_player - 1
                
                if darts_thrown == 0:
                    round_start_score = player_scores[p_idx]
                    round_start_in_checked = player_in_checked[p_idx]
                    round_points = 0

                points = 0
                is_double = False
                is_master = False
                
                if hit_segment == "MISS":
                    if sound_miss: sound_miss.play()
                elif hit_segment != "-":
                    points = player_scores[p_idx] if hit_segment == "WIN_CHEAT" else parse_hit(hit_segment)
                    is_double = check_double(hit_segment)
                    is_master = check_master(hit_segment)

                bust = False
                if not player_in_checked[p_idx] and hit_segment != "MISS":
                    if hit_segment == "WIN_CHEAT" or is_double: 
                        set_team_in_checked(p_idx, True)
                    else: 
                        points = 0  

                new_score = player_scores[p_idx] - points if player_in_checked[p_idx] else player_scores[p_idx]

                if new_score < 0: bust = True
                elif option != "Open In/Out":
                    if new_score == 1: bust = True
                    elif new_score == 0:
                        if has_master_out and not is_master and hit_segment != "WIN_CHEAT": bust = True
                        elif has_double_out and not is_double and hit_segment != "WIN_CHEAT": bust = True

                if hit_segment == "MISS":
                    darts_thrown += 1
                    if darts_thrown == 3 and ser:
                        try: ser.write(b"LAMP:PLAYER:2
"); ser.flush()
                        except Exception: pass
                    sync_hw_display()
                elif bust: 
                    if sound_bust: sound_bust.play()
                    set_team_score(p_idx, round_start_score)
                    set_team_in_checked(p_idx, round_start_in_checked)
                    round_points = 0
                    darts_thrown = 3 
                    if ser:
                        try: ser.write(b"LAMP:PLAYER:2
"); ser.flush()
                        except Exception: pass
                    sync_hw_display()
                else:
                    set_team_score(p_idx, new_score)
                    round_points += points
                    darts_thrown += 1
                    
                    if points > 0 or (player_in_checked[p_idx] and not round_start_in_checked):
                        if hit_segment in ["t18", "t19", "t20", "b", "db"]:
                            champ_display_until = pygame.time.get_ticks() + 2000
                            if sound_champ: sound_champ.play()
                        elif "t" in hit_segment and sound_triple: sound_triple.play()
                        elif ("d" in hit_segment or hit_segment == "db") and sound_double: sound_double.play()
                        elif sound_single: sound_single.play()
                    elif sound_single and hit_segment != "-": 
                        sound_single.play()

                    if darts_thrown == 3 and ser and new_score > 0:
                        try: ser.write(b"LAMP:PLAYER:2
"); ser.flush()
                        except Exception: pass
                    
                    sync_hw_display()

                    if new_score == 0:
                        current_state = "WIN"
                        trigger_victory(ser, display)
                        display.clear_all()
                        sync_hw_display()

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font); pygame.display.flip(); clock.tick(30); continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((6, 17, 28))

        if current_state in ["GAME", "ABORT_MENU", "WIN"]:
            hud_w = int(sw * 0.90)
            hud_x = (sw - hud_w) // 2
            hud_y = int(sh * 0.02)
            hud_h = int(sh * 0.635)
            draw_cyber_frame(screen, hud_x, hud_y, hud_w, hud_h, cut=22)

            mode_tag = "  •  TEAM-MODUS" if is_team_mode else ""
            head_txt = f"SPIEL: {game_name}   •   {option.upper()}{mode_tag}   •   RUNDE {round_num}"
            head_surf = title_font.render(head_txt, True, HIGHLIGHT)
            screen.blit(head_surf, ((sw - head_surf.get_width()) // 2, hud_y + int(sh * 0.018)))

            line_y = hud_y + int(sh * 0.068)
            pygame.draw.line(screen, NEON_GREEN, (hud_x + 35, line_y), (hud_x + hud_w - 35, line_y), 2)
            pygame.draw.circle(screen, HIGHLIGHT, (sw // 2, line_y), 5)

            act_col = PLAYER_COLORS[0] if is_berrys_turn else (PLAYER_COLORS[get_team_idx(active_player - 1) % len(PLAYER_COLORS)] if is_team_mode else PLAYER_COLORS[(active_player - 1) % len(PLAYER_COLORS)])
            if is_berrys_turn:
                active_label = mode
            elif is_team_mode:
                active_label = f"Spieler {active_player} (Team {get_team_idx(active_player - 1) + 1})"
            else:
                active_label = f"Spieler {active_player}"
                
            name_surf = big_font.render(f"▶  {active_label}  ◀", True, act_col)
            screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, int(sh * 0.105)))
            
            temp_score_surf = title_font.render(f"Runden-Punkte:  {round_points}", True, NEON_CYAN)
            screen.blit(temp_score_surf, ((sw - temp_score_surf.get_width()) // 2, int(sh * 0.165)))
            
            score_surf = giant_font.render(str(player_scores[active_player-1]), True, WHITE)
            screen.blit(score_surf, ((sw - score_surf.get_width()) // 2, int(sh * 0.205)))
            
            if has_double_in and not player_in_checked[active_player-1] and current_state == "GAME":
                in_hint = title_font.render("⚡ DOUBLE IN ERFORDERLICH! ⚡", True, HIGHLIGHT)
                in_w = in_hint.get_width() + 36
                in_h = in_hint.get_height() + 10
                in_x = (sw - in_w) // 2
                in_y = int(sh * 0.455)
                pygame.draw.rect(screen, (45, 36, 12), (in_x, in_y, in_w, in_h), border_radius=8)
                pygame.draw.rect(screen, HIGHLIGHT, (in_x, in_y, in_w, in_h), 2, border_radius=8)
                screen.blit(in_hint, (in_x + 18, in_y + 5))

            if darts_thrown >= 3 and not is_berrys_turn and current_state == "GAME":
                block_hint = title_font.render("Bitte Pfeile ziehen  ▶  IR-Sensor oder Spielerwechsel drücken!", True, RED_COL)
                bh_w = block_hint.get_width() + 40
                bh_h = block_hint.get_height() + 10
                bh_x = (sw - bh_w) // 2
                bh_y = int(sh * 0.525)
                pygame.draw.rect(screen, (42, 14, 22), (bh_x, bh_y, bh_w, bh_h), border_radius=8)
                pygame.draw.rect(screen, RED_COL, (bh_x, bh_y, bh_w, bh_h), 2, border_radius=8)
                screen.blit(block_hint, (bh_x + 20, bh_y + 5))

            darts_surf = title_font.render(f"Pfeile: {darts_thrown} / 3", True, (200, 215, 225))
            d_total_w = darts_surf.get_width() + 90
            d_start_x = (sw - d_total_w) // 2
            d_y = int(sh * 0.592)
            screen.blit(darts_surf, (d_start_x, d_y))
            dot_base_x = d_start_x + darts_surf.get_width() + 25
            dot_cy = d_y + darts_surf.get_height() // 2
            for d_i in range(3):
                is_rem = d_i < (3 - darts_thrown)
                c_dot = NEON_GREEN if is_rem else (35, 60, 75)
                pygame.draw.circle(screen, c_dot, (dot_base_x + d_i * 24, dot_cy), 8)
                pygame.draw.circle(screen, HIGHLIGHT if is_rem else (70, 95, 110), (dot_base_x + d_i * 24, dot_cy), 8, 2)

            sb_y = int(sh * 0.68)
            box_h = int(sh * 0.28)
            
            if is_team_mode:
                p_box_w = int(sw * 0.90 / num_teams) - 10
                sb_x = (sw - (num_teams * (p_box_w + 10) - 10)) // 2
                active_team = get_team_idx(active_player - 1)
                
                for t in range(num_teams):
                    px = sb_x + t * (p_box_w + 10)
                    is_act = (t == active_team)
                    p1 = t * 2 + 1
                    p2 = t * 2 + 2
                    members_str = f"P{p1}/P{p2}" if p2 <= total_players else f"P{p1}"
                    p_col = PLAYER_COLORS[t % len(PLAYER_COLORS)]
                    
                    draw_cyber_player_card(screen, px, sb_y, p_box_w, box_h, p_col, is_act, cut=12)

                    t_name = f"Team {t+1} ({members_str})"
                    pn_surf = scoreboard_font.render(t_name, True, p_col)
                    screen.blit(pn_surf, (px + (p_box_w - pn_surf.get_width()) // 2, sb_y + int(box_h * 0.08)))

                    t_score = player_scores[t * 2]
                    sc_surf = big_font.render(str(t_score), True, HIGHLIGHT if is_act else WHITE)
                    screen.blit(sc_surf, (px + (p_box_w - sc_surf.get_width()) // 2, sb_y + int(box_h * 0.44)))
            else:
                p_box_w = int(sw * 0.90 / total_players) - 10
                sb_x = (sw - (total_players * (p_box_w + 10) - 10)) // 2
                
                for i in range(total_players):
                    px = sb_x + i * (p_box_w + 10)
                    is_act = (i == (active_player - 1))
                    p_n = "Berry" if (is_berry_game and i == total_players - 1) else f"Spieler {i+1}"
                    p_col = PLAYER_COLORS[0] if (is_berry_game and i == total_players - 1) else PLAYER_COLORS[i % len(PLAYER_COLORS)]
                    
                    draw_cyber_player_card(screen, px, sb_y, p_box_w, box_h, p_col, is_act, cut=12)

                    pn_surf = scoreboard_font.render(p_n, True, p_col)
                    screen.blit(pn_surf, (px + (p_box_w - pn_surf.get_width()) // 2, sb_y + int(box_h * 0.08)))

                    sc_surf = big_font.render(str(player_scores[i]), True, HIGHLIGHT if is_act else WHITE)
                    screen.blit(sc_surf, (px + (p_box_w - sc_surf.get_width()) // 2, sb_y + int(box_h * 0.44)))

            if is_berrys_turn and avatar_frames:
                idx_anim = int((math.sin(pygame.time.get_ticks() * 0.005) + 1.0) * 2.49)
                idx_anim = max(0, min(len(avatar_frames) - 1, idx_anim))
                av_scaled = avatar_frames[idx_anim]
                screen.blit(av_scaled, (int(sw*0.72), int(sh*0.22)))
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
                
                if is_berrys_turn:
                    winner_name = mode
                elif is_team_mode:
                    win_t = get_team_idx(active_player - 1)
                    p1 = win_t * 2 + 1
                    p2 = win_t * 2 + 2
                    m_str = f"Spieler {p1} & {p2}" if p2 <= total_players else f"Spieler {p1}"
                    winner_name = f"Team {win_t + 1} ({m_str})"
                else:
                    winner_name = f"Spieler {active_player}"
                    
                txt_winner = big_font.render(f"{winner_name} beendet!", True, act_col)
                screen.blit(txt_winner, ((sw - txt_winner.get_width()) // 2, pop_y + int(pop_h * 0.42)))
                pygame.draw.line(screen, NEON_GREEN, (pop_x + 50, pop_y + int(pop_h * 0.56)), (pop_x + pop_w - 50, pop_y + int(pop_h * 0.56)), 2)
                
                txt_start = title_font.render("▶  START = Spiel neu starten  ◀", True, NEON_GREEN)
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, pop_y + int(pop_h * 0.66)))
                
                txt_end = title_font.render("▶  SPIELERWECHSEL = Hauptmenü  ◀", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, pop_y + int(pop_h * 0.80)))
                
        pygame.display.flip(); clock.tick(30)
