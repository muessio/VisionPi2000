# Datei: game_cyber_rallye.py
# Version: 1.0.0
# VisionPi2000 - Cyber Rallye (Etappen-Rennen mit Checkpoints & Cyber-Slot im Cyber-Circuit-Design)

import pygame
import math
import os
import random
import time

VERSION = "1.0.0"
GAMES = ["Cyber Rallye"]
OPTIONS = [
    "Sprint (500 km)",
    "Grand Prix (900 km)",
    "Battle-Rallye (600 km)"
]

RACER_COLORS = [
    (255, 0, 90),    # Spieler 1 - Neon Pink/Rot
    (0, 216, 255),   # Spieler 2 - Neon Cyan
    (0, 255, 157),   # Spieler 3 - Neon Grün
    (255, 205, 45),  # Spieler 4 - Gold
    (175, 70, 255),  # Spieler 5 - Violett
    (255, 115, 30),  # Spieler 6 - Orange
    (120, 235, 255), # Spieler 7 - Eisblau
    (255, 80, 200)   # Spieler 8 - Magenta
]
BERRY_COLOR = (255, 215, 0)

CHECKPOINT_TASKS = [
    {"id": "DOUBLE", "label": "Beliebiges DOUBLE treffen", "short": "DOUBLE"},
    {"id": "TRIPLE", "label": "Beliebiges TRIPLE treffen", "short": "TRIPLE"},
    {"id": "HIGH",   "label": "Zahl 15 bis 20 treffen",    "short": "15 - 20"},
    {"id": "ODD",    "label": "Ungerade Zahl treffen",     "short": "UNGERADE"}
]

SLOT_SYMBOLS = [
    {"id": "NITRO", "label": "NITRO",  "color": (0, 255, 157)},
    {"id": "TURBO", "label": "2x TURBO", "color": (0, 216, 255)},
    {"id": "EMP",   "label": "EMP",    "color": (255, 56, 76)},
    {"id": "PANNE", "label": "PANNE",  "color": (255, 165, 0)}
]

if not hasattr(pygame, "_vp2000_cache"):
    pygame._vp2000_cache = {}
_ASSET_CACHE = pygame._vp2000_cache
_frame_cache = {}


def draw_cyber_frame(surface, x, y, w, h, cut=22):
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


def draw_cyber_player_card(surface, x, y, w, h, p_col, is_act, cut=12, div_ratio=0.30):
    key = ("cyber_card_v3", w, h, p_col, is_act, cut, div_ratio)
    if key not in _frame_cache:
        if len(_frame_cache) > 48:
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

        if div_ratio > 0:
            div_y = int(h * div_ratio)
            line_col = p_col if is_act else (p_col[0] // 2, p_col[1] // 2, p_col[2] // 2, 200)
            pygame.draw.line(card_surf, line_col, (12, div_y), (w - 12, div_y), 2)

        dot_col = (255, 205, 45) if is_act else (140, 115, 40)
        for cx, cy in [(cut + 6, 8), (r - cut - 6, 8), (cut + 6, b - 6), (r - cut - 6, b - 6)]:
            pygame.draw.circle(card_surf, dot_col, (cx, cy), 3)

        _frame_cache[key] = card_surf

    surface.blit(_frame_cache[key], (x, y))


def _get_cached_sound(path):
    key = f"snd_{path}"
    if key not in _ASSET_CACHE:
        if os.path.exists(path):
            try:
                _ASSET_CACHE[key] = pygame.mixer.Sound(path)
            except Exception:
                _ASSET_CACHE[key] = None
        else:
            _ASSET_CACHE[key] = None
    return _ASSET_CACHE[key]


def _get_cached_font(size):
    key = f"font_{size}"
    if key not in _ASSET_CACHE:
        _ASSET_CACHE[key] = pygame.font.SysFont("arial", size, bold=True)
    return _ASSET_CACHE[key]


def _get_cached_bg(sw, sh, is_16_9):
    key = f"bg_{sw}_{sh}_{is_16_9}"
    if key not in _ASSET_CACHE:
        bg_candidates = ["background_16_9.jpg", "background_16_9.png"] if is_16_9 else ["background.jpg", "background.png"]
        bg_img = None
        for bf in bg_candidates:
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
        _ASSET_CACHE[key] = bg_img
    return _ASSET_CACHE[key]


def trigger_victory(ser, display=None):
    snd_vic = _get_cached_sound("sounds/victory.wav")
    if snd_vic:
        try:
            snd_vic.play()
        except Exception:
            pass
    if ser or display:
        try:
            for _ in range(6):
                if display:
                    display.set_light(True)
                if ser:
                    ser.write(b"TEST:ON\n")
                    ser.flush()
                time.sleep(0.25)

                if display:
                    display.set_light(False)
                if ser:
                    ser.write(b"TEST:OFF\n")
                    ser.flush()
                time.sleep(0.25)

            if display:
                display.set_light(True)
            if ser:
                ser.write(b"LAMP:PLAYER:2\n")
                ser.write(b"LAMP:START:0\n")
                ser.flush()
        except Exception:
            pass


def check_task_fulfilled(task_id, seg, mult):
    if task_id == "DOUBLE":
        return mult == 2
    elif task_id == "TRIPLE":
        return mult == 3
    elif task_id == "HIGH":
        return 15 <= seg <= 20
    elif task_id == "ODD":
        return (1 <= seg <= 20) and (seg % 2 == 1)
    return False


def get_bot_hit(cp_task, mode):
    diff = 1 if "Stufe 1" in mode else (2 if "Stufe 2" in mode else 3)
    hit_chance = 0.45 if diff == 1 else (0.70 if diff == 2 else 0.88)

    if cp_task is not None:
        tid = cp_task["id"]
        if random.random() < hit_chance:
            if tid == "DOUBLE":
                return f"d{random.choice([20, 16, 18, 12, 10])}"
            elif tid == "TRIPLE":
                return f"t{random.choice([20, 19, 18])}"
            elif tid == "HIGH":
                return str(random.randint(15, 20))
            elif tid == "ODD":
                return str(random.choice([19, 17, 15, 13, 11, 9, 7, 5, 3, 1]))
        return str(random.randint(1, 20))

    r = random.random()
    if diff == 1:
        if r < 0.08:
            return "b"
        return str(random.choice([20, 19, 18, 12, 5, 1, 7, 14]))
    elif diff == 2:
        if r < 0.12:
            return "b"
        elif r < 0.30:
            return f"t{random.choice([20, 19, 18])}"
        elif r < 0.55:
            return f"d{random.choice([20, 19, 18])}"
        return str(random.choice([20, 19, 18, 17, 16]))
    else:
        if r < 0.14:
            return "db"
        elif r < 0.52:
            return f"t{random.choice([20, 19])}"
        elif r < 0.78:
            return f"d{random.choice([20, 19, 18])}"
        return "20"


class ScreenSaver:
    def __init__(self, width, height):
        self.width, self.height, self.active, self.last_activity = width, height, False, pygame.time.get_ticks()
        if "ss_avatars" not in _ASSET_CACHE:
            imgs = []
            for file in ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]:
                if os.path.exists(file):
                    try:
                        imgs.append(pygame.transform.smoothscale(pygame.image.load(file).convert_alpha(), (100, 100)))
                    except Exception:
                        pass
            _ASSET_CACHE["ss_avatars"] = imgs

        self.avatars = []
        for img in _ASSET_CACHE["ss_avatars"]:
            self.avatars.append({
                "img": img,
                "x": random.randint(50, max(60, width - 150)),
                "y": random.randint(50, max(60, height - 150)),
                "vx": random.choice([-2, 2]),
                "vy": random.choice([-2, 2])
            })

    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active:
            self.active = False
            return True
        return False

    def check(self):
        if not self.active and pygame.time.get_ticks() - self.last_activity > 600000:
            self.active = True
        return self.active

    def update_and_draw(self, screen, font):
        if not self.active:
            return
        screen.fill((0, 0, 0))
        for av in self.avatars:
            av["x"] += av["vx"]
            av["y"] += av["vy"]
            if av["x"] <= 0 or av["x"] >= self.width - 100:
                av["vx"] *= -1
            if av["y"] <= 0 or av["y"] >= self.height - 100:
                av["vy"] *= -1
            screen.blit(av["img"], (av["x"], av["y"]))
        hint_surf = font.render("STANDBY – Beliebige Taste drücken zum Fortfahren", True, (120, 120, 120))
        screen.blit(hint_surf, hint_surf.get_rect(center=(self.width // 2, self.height - 40)))


def run_game(screen, ser, display, players, game_name, option, mode):
    is_berry_game = "Bullseye-Berry" in mode
    total_players = min(8, players + 1 if is_berry_game else players)

    if "900" in option:
        target_km, stage_step, num_stages = 900, 150, 6
    elif "600" in option:
        target_km, stage_step, num_stages = 600, 100, 6
    else:
        target_km, stage_step, num_stages = 500, 100, 5
    is_battle = "Battle" in option

    sw, sh = screen.get_width(), screen.get_height()
    screensaver = ScreenSaver(sw, sh)

    if hasattr(display, 'clear_all'):
        display.clear_all()

    is_16_9 = (sw / float(sh)) > 1.5
    bg_img = _get_cached_bg(sw, sh, is_16_9)

    avatar_path = {
        "Bullseye-Berry (Stufe 1)": "Bullseye-Berry_Original.png",
        "Bullseye-Berry (Stufe 2)": "Bullseye-Berry_Cyber.png",
        "Bullseye-Berry (Stufe 3)": "Bullseye-Berry_Ninja.png"
    }.get(mode, "")
    av_key = f"av_{avatar_path}_{sh}"
    if avatar_path and av_key not in _ASSET_CACHE:
        frames = []
        if os.path.exists(avatar_path):
            try:
                raw_av = pygame.image.load(avatar_path).convert_alpha()
                base_sz = int(sh * 0.25)
                for offset in [-8, -4, 0, 4, 8]:
                    sz = base_sz + offset
                    frames.append(pygame.transform.smoothscale(raw_av, (sz, sz)))
            except Exception:
                pass
        _ASSET_CACHE[av_key] = frames
    avatar_frames = _ASSET_CACHE.get(av_key, [])

    sound_champ = _get_cached_sound("sounds/champ.wav")
    sound_single = _get_cached_sound("sounds/hit_single.wav")
    sound_double = _get_cached_sound("sounds/hit_double.wav")
    sound_triple = _get_cached_sound("sounds/hit_triple.wav")
    sound_switch = _get_cached_sound("sounds/switch_player.wav")
    sound_miss = _get_cached_sound("sounds/miss.wav")
    sound_bust = _get_cached_sound("sounds/bust.wav")

    tiny_font = _get_cached_font(int(sh * 0.018))
    small_font = _get_cached_font(int(sh * 0.022))
    sb_font_size = int(sh * 0.028) if total_players <= 4 else int(sh * 0.021)
    scoreboard_font = _get_cached_font(sb_font_size)
    title_font = _get_cached_font(int(sh * 0.028))
    big_font = _get_cached_font(int(sh * 0.042))
    win_font = _get_cached_font(int(sh * 0.12) if sh <= 768 else int(sh * 0.15))

    HIGHLIGHT, WHITE, RED_COL, NEON_GREEN, NEON_CYAN = (255, 205, 45), (255, 255, 255), (255, 56, 76), (0, 255, 157), (0, 216, 255)

    def reset_match_state():
        return (
            [0] * total_players,          # km_scores
            [0] * total_players,          # stages_cleared (0..num_stages-1)
            [None] * total_players,       # cp_tasks (None or dict)
            [False] * total_players,      # turbo_active (2x für aktuelle/nächste Aufnahme)
            0, 1, 1, 0, 0, 0, 0           # darts_thrown, active_player, round_num, round_points, switch_delay_timer, piezo_block_until, winner_idx
        )

    (km_scores, stages_cleared, cp_tasks, turbo_active,
     darts_thrown, active_player, round_num, round_points,
     switch_delay_timer, piezo_block_until, winner_idx) = reset_match_state()

    banner_text, banner_col, banner_until = "", HIGHLIGHT, 0
    slot_anim_start, slot_anim_until = 0, 0
    slot_result_sym = None
    slot_result_text = ""

    def set_banner(text, col, duration=2000):
        nonlocal banner_text, banner_col, banner_until
        banner_text, banner_col = text, col
        banner_until = pygame.time.get_ticks() + duration

    if ser:
        try:
            ser.write(b"LAMP:PLAYER:1\n")
            ser.write(b"LAMP:START:0\n")
            ser.flush()
        except Exception:
            pass

    def sync_hw_display():
        try:
            display.clear_buffer()
            display.set_active_player(active_player - 1)
            display.set_bullseye_icon(True)

            for i in range(8):
                display.set_score(i, km_scores[i] if i < total_players else None)

            act_idx = active_player - 1
            hw_keys = [20, 19, 18, 17, 16, 15]
            for s_idx, hw_key in enumerate(hw_keys):
                if s_idx < num_stages:
                    if s_idx < stages_cleared[act_idx]:
                        display.set_cricket_marks(act_idx, hw_key, 3)
                    elif s_idx == stages_cleared[act_idx] and cp_tasks[act_idx] is not None:
                        display.set_cricket_marks(act_idx, hw_key, 1)
                    if hasattr(display, 'CRICKET_TARGET_DISP') and hw_key in display.CRICKET_TARGET_DISP:
                        d_ten, d_unit = display.CRICKET_TARGET_DISP[hw_key]
                        st_str = f"{s_idx + 1:2d}"
                        display.set_disp_char(d_ten, st_str[0])
                        display.set_disp_char(d_unit, st_str[1])

            display.set_temp_score(round_points)
            display.set_turn(round_num)
            display.set_dart_arrows(3 - darts_thrown)
            display.update()
        except Exception:
            pass

    sync_hw_display()

    running, clock, current_state = True, pygame.time.Clock(), "GAME"
    bot_timer, combo_press_start = 0, 0

    while running:
        now = pygame.time.get_ticks()
        raw_data = ser.readline().decode('utf-8', 'ignore').strip() if ser and ser.in_waiting > 0 else None
        is_berrys_turn = (is_berry_game and active_player == total_players)

        for event in pygame.event.get():
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer():
                    raw_data = None
                    continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    raw_data = "BTN:PLAYER"
                elif event.key == pygame.K_SPACE:
                    raw_data = "BTN:START"
                elif event.key == pygame.K_i:
                    raw_data = "IR:DETECT"
                elif event.key == pygame.K_ESCAPE:
                    running = False

        if raw_data and screensaver.reset_timer():
            raw_data = None
            continue

        keys = pygame.key.get_pressed()
        if raw_data == "BTN:COMBO":
            current_state = "ABORT_MENU"
            raw_data = None
        elif keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
            if combo_press_start == 0:
                combo_press_start = now
            elif now - combo_press_start >= 3000:
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
                if sound_switch:
                    sound_switch.play()
                display.clear_all()
                return "menu"

        elif current_state == "GAME":
            if raw_data == "BTN:PLAYER":
                switch_delay_timer = now
                raw_data = None
            elif raw_data == "IR:DETECT":
                if darts_thrown >= 3 and not is_berrys_turn:
                    switch_delay_timer = now + 1000
                raw_data = None

            if is_berrys_turn and darts_thrown >= 3 and switch_delay_timer == 0 and now >= slot_anim_until:
                if bot_timer == 0:
                    bot_timer = now + 1000
                elif now > bot_timer:
                    switch_delay_timer = now + 1000
                    bot_timer = 0

            if switch_delay_timer > 0 and now >= switch_delay_timer:
                prev_idx = active_player - 1
                if turbo_active[prev_idx] and darts_thrown > 0:
                    turbo_active[prev_idx] = False
                switch_delay_timer, darts_thrown, round_points = 0, 0, 0
                piezo_block_until = now + 1500
                if active_player == total_players:
                    round_num += 1
                active_player = (active_player % total_players) + 1
                if sound_switch:
                    sound_switch.play()
                if ser:
                    try:
                        ser.write(b"LAMP:PLAYER:1\n")
                        ser.flush()
                    except Exception:
                        pass
                sync_hw_display()
                bot_timer = 0
                is_berrys_turn = (is_berry_game and active_player == total_players)

            if is_berrys_turn and switch_delay_timer == 0 and darts_thrown < 3 and now >= slot_anim_until:
                if bot_timer == 0:
                    bot_timer = now + random.randint(1100, 1650)
                elif now > bot_timer:
                    raw_data = f"HIT:{get_bot_hit(cp_tasks[active_player - 1], mode)}"
                    bot_timer = 0

            if raw_data == "MISS:1" and now < piezo_block_until:
                raw_data = None
            elif raw_data and (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
                hit_segment = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                p_idx = active_player - 1

                if hit_segment == "MISS":
                    if sound_miss:
                        sound_miss.play()
                elif hit_segment != "-":
                    seg = 25 if hit_segment in ("b", "db") else int(hit_segment.replace("t", "").replace("d", ""))
                    mult = 3 if "t" in hit_segment else (2 if ("d" in hit_segment or hit_segment == "db") else 1)

                    if seg == 25:
                        # BULLSEYE -> CYBER-SLOT (BOXENSTOPP)
                        picked = random.choices(SLOT_SYMBOLS, weights=[35, 30, 20, 15], k=1)[0]
                        slot_result_sym = picked
                        slot_anim_start = now
                        slot_anim_until = now + 1800

                        if picked["id"] == "NITRO":
                            bonus = 100 if mult == 2 else 60
                            if cp_tasks[p_idx] is not None:
                                cp_tasks[p_idx] = None
                                stages_cleared[p_idx] += 1
                            km_scores[p_idx] = min(target_km, km_scores[p_idx] + bonus)
                            round_points += bonus
                            slot_result_text = f"NITRO-BOOST! +{bonus} km"
                            if sound_champ:
                                sound_champ.play()
                        elif picked["id"] == "TURBO":
                            turbo_active[p_idx] = True
                            slot_result_text = "TURBO 2x AKTIV!"
                            if sound_triple:
                                sound_triple.play()
                        elif picked["id"] == "EMP":
                            rivals = [i for i in range(total_players) if i != p_idx and km_scores[i] > 0]
                            if rivals:
                                leader = max(rivals, key=lambda i: km_scores[i])
                                km_scores[leader] = max(0, km_scores[leader] - 40)
                                slot_result_text = f"EMP! Spieler {leader + 1} -40 km"
                            else:
                                km_scores[p_idx] = min(target_km, km_scores[p_idx] + 40)
                                round_points += 40
                                slot_result_text = "EMP-SCHILD! +40 km"
                            if sound_double:
                                sound_double.play()
                        else:
                            slot_result_text = "MOTORSCHADEN! 0 Bonus"
                            if sound_bust:
                                sound_bust.play()

                        set_banner(slot_result_text, picked["color"], 2200)

                    else:
                        gained_km = 0
                        if cp_tasks[p_idx] is not None:
                            if check_task_fulfilled(cp_tasks[p_idx]["id"], seg, mult):
                                cp_tasks[p_idx] = None
                                stages_cleared[p_idx] += 1
                                gained_km = (seg * mult) * (2 if turbo_active[p_idx] else 1)
                                set_banner(f"CHECKPOINT GEKNACKT! +{gained_km} km", NEON_GREEN, 2000)
                                if sound_champ:
                                    sound_champ.play()
                            else:
                                set_banner(f"SCHRANKE ZU! ({cp_tasks[p_idx]['short']})", RED_COL, 1400)
                                if sound_miss:
                                    sound_miss.play()
                        else:
                            gained_km = (seg * mult) * (2 if turbo_active[p_idx] else 1)
                            if mult == 3 and sound_triple:
                                sound_triple.play()
                            elif mult == 2 and sound_double:
                                sound_double.play()
                            elif sound_single:
                                sound_single.play()

                        if gained_km > 0:
                            old_km = km_scores[p_idx]
                            new_km = old_km + gained_km
                            next_cp_km = (stages_cleared[p_idx] + 1) * stage_step

                            if next_cp_km < target_km and new_km >= next_cp_km:
                                km_scores[p_idx] = next_cp_km
                                round_points += (next_cp_km - old_km)
                                cp_tasks[p_idx] = random.choice(CHECKPOINT_TASKS)
                                set_banner(f"CHECKPOINT {stages_cleared[p_idx] + 1}: {cp_tasks[p_idx]['short']}!", HIGHLIGHT, 2200)
                            else:
                                km_scores[p_idx] = min(target_km, new_km)
                                round_points += (km_scores[p_idx] - old_km)

                            if is_battle and total_players > 1:
                                for r_i in range(total_players):
                                    if r_i != p_idx and old_km < km_scores[r_i] <= km_scores[p_idx]:
                                        km_scores[r_i] = max(0, km_scores[r_i] - 30)
                                        set_banner(f"CRASH! Spieler {r_i + 1} -30 km!", RED_COL, 1800)

                    if km_scores[p_idx] >= target_km:
                        winner_idx = p_idx
                        current_state = "WIN"
                        trigger_victory(ser, display)

                darts_thrown += 1
                if darts_thrown == 3 and current_state == "GAME" and ser:
                    try:
                        ser.write(b"LAMP:PLAYER:2\n")
                        ser.flush()
                    except Exception:
                        pass
                sync_hw_display()

        elif current_state == "WIN" and raw_data in ["BTN:PLAYER", "BTN:START"]:
            if raw_data == "BTN:PLAYER":
                if sound_switch:
                    sound_switch.play()
                display.clear_all()
                return "menu"
            elif raw_data == "BTN:START":
                if sound_switch:
                    sound_switch.play()
                (km_scores, stages_cleared, cp_tasks, turbo_active,
                 darts_thrown, active_player, round_num, round_points,
                 switch_delay_timer, piezo_block_until, winner_idx) = reset_match_state()
                current_state = "GAME"
                if ser:
                    try:
                        ser.write(b"LAMP:PLAYER:1\n")
                        ser.write(b"LAMP:START:0\n")
                        ser.flush()
                    except Exception:
                        pass
                display.clear_all()
                sync_hw_display()
                raw_data = None

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font)
            pygame.display.flip()
            clock.tick(30)
            continue

        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # --- 1. TOP HEADER (90% BREITE) ---
        top_w = int(sw * 0.90)
        top_x = (sw - top_w) // 2
        top_y = int(sh * 0.015)
        top_h = int(sh * 0.18)
        draw_cyber_frame(screen, top_x, top_y, top_w, top_h, cut=16)

        head_str = f"CYBER RALLYE   •   {option.upper()}   •   RUNDE {round_num}"
        head_surf = title_font.render(head_str, True, HIGHLIGHT)
        screen.blit(head_surf, ((sw - head_surf.get_width()) // 2, top_y + int(sh * 0.012)))

        line_y = top_y + int(sh * 0.050)
        pygame.draw.line(screen, NEON_GREEN, (top_x + 30, line_y), (top_x + top_w - 30, line_y), 2)
        pygame.draw.circle(screen, HIGHLIGHT, (sw // 2, line_y), 4)

        act_idx = active_player - 1
        act_col = BERRY_COLOR if is_berrys_turn else RACER_COLORS[act_idx % len(RACER_COLORS)]
        p_title = "Bullseye-Berry" if is_berrys_turn else f"Spieler {active_player}"
        name_surf = big_font.render(f"▶  {p_title}  ◀", True, act_col)
        screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, top_y + int(sh * 0.060)))

        if cp_tasks[act_idx] is not None:
            sub_str = f"CHECKPOINT-AUFGABE: {cp_tasks[act_idx]['label']}   •   BULL = Cyber-Slot   •   Pfeile: {darts_thrown}/3"
            sub_col = RED_COL
        else:
            turbo_txt = "  [TURBO 2x AKTIV!]" if turbo_active[act_idx] else ""
            sub_str = f"Strecke frei! Punkte = km{turbo_txt}   •   BULL = Cyber-Slot   •   Pfeile: {darts_thrown}/3"
            sub_col = NEON_CYAN
        sub_surf = small_font.render(sub_str, True, sub_col)
        screen.blit(sub_surf, ((sw - sub_surf.get_width()) // 2, top_y + int(sh * 0.128)))

        # --- 2. NEON HIGHWAY STRECKENKARTE ---
        track_y = int(sh * 0.215)
        track_h = int(sh * 0.30)
        draw_cyber_frame(screen, top_x, track_y, top_w, track_h, cut=16)

        road_x = top_x + int(top_w * 0.06)
        road_w = int(top_w * 0.88)
        road_cy = track_y + int(track_h * 0.56)
        road_h = int(track_h * 0.26)

        pygame.draw.rect(screen, (14, 28, 44), (road_x, road_cy - road_h // 2, road_w, road_h), border_radius=8)
        pygame.draw.rect(screen, NEON_CYAN, (road_x, road_cy - road_h // 2, road_w, road_h), 2, border_radius=8)

        # Gestrichelte Mittellinie
        for dx in range(road_x + 15, road_x + road_w - 15, 32):
            pygame.draw.line(screen, (50, 120, 140), (dx, road_cy), (min(dx + 16, road_x + road_w - 10), road_cy), 2)

        # Checkpoints & Ziel auf der Strecke
        for cp_i in range(1, num_stages + 1):
            cp_km = cp_i * stage_step
            px = road_x + int(road_w * (cp_km / float(target_km)))
            is_finish = (cp_i == num_stages)
            cp_col = NEON_GREEN if is_finish else HIGHLIGHT
            pygame.draw.line(screen, cp_col, (px, road_cy - road_h // 2 - 14), (px, road_cy + road_h // 2 + 10), 3 if is_finish else 2)
            lbl = "ZIEL" if is_finish else f"CP{cp_i}"
            lbl_s = tiny_font.render(lbl, True, cp_col)
            screen.blit(lbl_s, (px - lbl_s.get_width() // 2, road_cy - road_h // 2 - 32))
            km_s = tiny_font.render(f"{cp_km}km", True, (150, 175, 195))
            screen.blit(km_s, (px - km_s.get_width() // 2, road_cy + road_h // 2 + 14))

        # Spieler-Marker auf dem Highway
        for i in range(total_players):
            p_col = BERRY_COLOR if (is_berry_game and i == total_players - 1) else RACER_COLORS[i % len(RACER_COLORS)]
            prog = km_scores[i] / float(target_km)
            mx = road_x + int(road_w * prog)
            lane_off = ((i % 4) - 1.5) * int(road_h * 0.22)
            my = int(road_cy + lane_off)
            rad = 12 if i == act_idx else 9
            if i == act_idx:
                pygame.draw.circle(screen, WHITE, (mx, my), rad + 3, 2)
            pygame.draw.circle(screen, p_col, (mx, my), rad)
            tag = "B" if (is_berry_game and i == total_players - 1) else str(i + 1)
            tag_s = tiny_font.render(tag, True, (0, 0, 0))
            screen.blit(tag_s, tag_s.get_rect(center=(mx, my)))

        # --- 3. SPIELER-KARTEN UNTEN ---
        cols = min(4, total_players)
        rows = math.ceil(total_players / float(cols))
        gap_c = 12
        card_w = (top_w - (cols - 1) * gap_c) // cols if cols > 1 else top_w
        grid_y = int(sh * 0.54)
        card_h = int(sh * (0.35 if rows == 1 else 0.19))

        for i in range(total_players):
            r_idx, c_idx = i // cols, i % cols
            cx = top_x + c_idx * (card_w + gap_c)
            cur_cw = (top_x + top_w - cx) if (c_idx == cols - 1) else card_w
            cy = grid_y + r_idx * (card_h + 12)
            p_col = BERRY_COLOR if (is_berry_game and i == total_players - 1) else RACER_COLORS[i % len(RACER_COLORS)]
            is_act = (i == act_idx)

            draw_cyber_player_card(screen, cx, cy, cur_cw, card_h, p_col, is_act, cut=12, div_ratio=0.26)

            lbl = "Bullseye-Berry" if (is_berry_game and i == total_players - 1) else f"Spieler {i + 1}"
            n_s = scoreboard_font.render(lbl, True, p_col)
            screen.blit(n_s, (cx + (cur_cw - n_s.get_width()) // 2, cy + int(card_h * 0.04)))

            km_s = big_font.render(f"{km_scores[i]} km", True, HIGHLIGHT if is_act else WHITE)
            screen.blit(km_s, (cx + (cur_cw - km_s.get_width()) // 2, cy + int(card_h * 0.34)))

            if cp_tasks[i] is not None:
                st_txt, st_col = f"STOP: {cp_tasks[i]['short']}", RED_COL
            elif turbo_active[i]:
                st_txt, st_col = "TURBO 2x AKTIV", NEON_CYAN
            else:
                st_txt, st_col = f"Etappe {min(num_stages, stages_cleared[i] + 1)}/{num_stages}", NEON_GREEN
            st_s = tiny_font.render(st_txt, True, st_col)
            screen.blit(st_s, (cx + (cur_cw - st_s.get_width()) // 2, cy + int(card_h * 0.74)))

        # --- 4. CYBER-SLOT ANIMATION BEI BULLSEYE ---
        if now < slot_anim_until and slot_result_sym:
            sw_box, sh_box = int(sw * 0.56), int(sh * 0.28)
            sx_box, sy_box = (sw - sw_box) // 2, (sh - sh_box) // 2
            draw_cyber_frame(screen, sx_box, sy_box, sw_box, sh_box, cut=18)

            sl_head = title_font.render("CYBER-SLOT  •  BOXENSTOPP", True, HIGHLIGHT)
            screen.blit(sl_head, ((sw - sl_head.get_width()) // 2, sy_box + 14))

            elapsed = now - slot_anim_start
            reel_w = int(sw_box * 0.26)
            reel_h = int(sh_box * 0.38)
            reel_y = sy_box + int(sh_box * 0.28)
            for r_i in range(3):
                rx = sx_box + int(sw_box * (0.08 + r_i * 0.29))
                locked = elapsed > (450 + r_i * 300)
                sym = slot_result_sym if locked else SLOT_SYMBOLS[(now // 60 + r_i) % len(SLOT_SYMBOLS)]
                pygame.draw.rect(screen, (12, 26, 40), (rx, reel_y, reel_w, reel_h), border_radius=8)
                pygame.draw.rect(screen, sym["color"], (rx, reel_y, reel_w, reel_h), 3, border_radius=8)
                r_s = small_font.render(sym["label"], True, sym["color"])
                screen.blit(r_s, r_s.get_rect(center=(rx + reel_w // 2, reel_y + reel_h // 2)))

            if elapsed > 1100:
                res_s = title_font.render(slot_result_text, True, slot_result_sym["color"])
                screen.blit(res_s, ((sw - res_s.get_width()) // 2, sy_box + sh_box - int(sh_box * 0.22)))

        # --- 5. HINWEISE, BANNER & AVATAR ---
        if darts_thrown >= 3 and not is_berrys_turn and current_state == "GAME":
            block_hint = title_font.render("Bitte Pfeile ziehen  ▶  IR-Sensor oder Spielerwechsel drücken!", True, RED_COL)
            bh_w, bh_h = block_hint.get_width() + 36, block_hint.get_height() + 10
            bh_x, bh_y = (sw - bh_w) // 2, int(sh * 0.92)
            pygame.draw.rect(screen, (42, 14, 22), (bh_x, bh_y, bh_w, bh_h), border_radius=8)
            pygame.draw.rect(screen, RED_COL, (bh_x, bh_y, bh_w, bh_h), 2, border_radius=8)
            screen.blit(block_hint, (bh_x + 18, bh_y + 5))

        if now < banner_until and banner_text and now >= slot_anim_until:
            b_surf = big_font.render(banner_text, True, banner_col)
            bx, by = (sw - b_surf.get_width()) // 2, int(sh * 0.85)
            pygame.draw.rect(screen, (0, 0, 0), (bx - 20, by - 8, b_surf.get_width() + 40, b_surf.get_height() + 16), border_radius=12)
            pygame.draw.rect(screen, banner_col, (bx - 20, by - 8, b_surf.get_width() + 40, b_surf.get_height() + 16), 3, border_radius=12)
            screen.blit(b_surf, (bx, by))

        if is_berrys_turn and avatar_frames:
            idx_anim = max(0, min(len(avatar_frames) - 1, int((math.sin(now * 0.005) + 1.0) * 2.49)))
            screen.blit(avatar_frames[idx_anim], (int(sw * 0.78), int(sh * 0.24)))

        # --- 6. ABORT & WIN OVERLAYS ---
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

            txt_head = win_font.render("ZIEL ERREICHT!", True, NEON_GREEN)
            screen.blit(txt_head, ((sw - txt_head.get_width()) // 2, pop_y + int(pop_h * 0.08)))

            win_col = BERRY_COLOR if (is_berry_game and winner_idx == total_players - 1) else RACER_COLORS[winner_idx % len(RACER_COLORS)]
            winner_name = "Bullseye-Berry" if (is_berry_game and winner_idx == total_players - 1) else f"Spieler {winner_idx + 1}"
            txt_winner = big_font.render(f"{winner_name} gewinnt die Rallye!", True, win_col)
            screen.blit(txt_winner, ((sw - txt_winner.get_width()) // 2, pop_y + int(pop_h * 0.42)))
            pygame.draw.line(screen, NEON_GREEN, (pop_x + 50, pop_y + int(pop_h * 0.56)), (pop_x + pop_w - 50, pop_y + int(pop_h * 0.56)), 2)

            txt_start = title_font.render("▶  START = Spiel neu starten  ◀", True, NEON_GREEN)
            screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, pop_y + int(pop_h * 0.66)))
            txt_end = title_font.render("▶  SPIELERWECHSEL = Hauptmenü  ◀", True, RED_COL)
            screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, pop_y + int(pop_h * 0.80)))

        pygame.display.flip()
        clock.tick(30)
