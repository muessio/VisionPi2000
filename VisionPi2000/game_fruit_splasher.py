# Datei: game_fruit_splasher.py
# Version: 1.1.4
# VisionPi2000 - Fruit Splasher (Juice Press & Berry Hunt Edition)

import pygame
import math
import os
import random
import time
import json

VERSION = "1.1.4"
GAMES = ["Fruit Splasher"]
OPTIONS = [
    "Juice Press (Standard - 3 Beeren)",
    "Juice Press (Party - 5 Beeren)",
    "Juice Press (Battle - Bull klaut)",
    "Berry Hunt (10 Runden)",
    "Berry Hunt (15 Runden)"
]

BERRY_PROFILES = [
    {"name": "Bullseye-Berry",     "fruit": "Raspberry",   "color": (255, 0, 90),    "hi": (255, 130, 170), "style": "cluster"},
    {"name": "Triple-Strawberry",  "fruit": "Strawberry",  "color": (255, 45, 45),   "hi": (255, 160, 160), "style": "strawberry"},
    {"name": "Bouncer-Blueberry",  "fruit": "Blueberry",   "color": (0, 180, 255),   "hi": (150, 230, 255), "style": "round"},
    {"name": "Checkout-Cherry",    "fruit": "Cherry",      "color": (220, 0, 70),    "hi": (255, 140, 170), "style": "cherry"},
    {"name": "Double-Dewberry",    "fruit": "Dewberry",    "color": (160, 50, 255),  "hi": (215, 170, 255), "style": "cluster"},
    {"name": "Flight-Huckleberry", "fruit": "Huckleberry", "color": (70, 100, 255),  "hi": (170, 190, 255), "style": "round"},
    {"name": "Scoring-Snowberry",  "fruit": "Snowberry",   "color": (235, 245, 255), "hi": (255, 255, 255), "style": "round"},
    {"name": "Master-Mulberry",    "fruit": "Mulberry",    "color": (210, 0, 180),   "hi": (255, 150, 240), "style": "cluster"}
]

GOLDEN_BERRY = {"name": "Golden-Raspberry", "fruit": "Golden-Berry", "color": (255, 215, 0), "hi": (255, 255, 180), "style": "cluster"}


def trigger_victory(ser, display=None):
    if os.path.exists("sounds/victory.wav"):
        try:
            pygame.mixer.Sound("sounds/victory.wav").play()
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


def draw_berry_icon(surface, cx, cy, radius, profile, pump_stage=0, max_stage=7):
    scale = 1.0 + (pump_stage / float(max(1, max_stage))) * 0.55
    r = max(8, int(radius * scale))
    col = profile["color"]
    hi = profile["hi"]
    style = profile["style"]

    if pump_stage >= max_stage - 1:
        pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.015)) * 8)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r + 6 + pulse, 2)

    leaf_col = (0, 230, 110)
    pygame.draw.line(surface, (120, 220, 90), (cx, cy - r + 2), (cx + 4, cy - r - int(r * 0.38)), max(2, r // 7))
    pygame.draw.polygon(surface, leaf_col, [
        (cx, cy - r + 4),
        (cx - int(r * 0.45), cy - r - int(r * 0.22)),
        (cx - int(r * 0.15), cy - r - int(r * 0.35))
    ])
    pygame.draw.polygon(surface, leaf_col, [
        (cx, cy - r + 4),
        (cx + int(r * 0.45), cy - r - int(r * 0.22)),
        (cx + int(r * 0.15), cy - r - int(r * 0.35))
    ])

    if style == "cluster":
        sub_r = max(4, int(r * 0.38))
        offsets = [
            (0, -int(r * 0.52)),
            (-int(r * 0.45), -int(r * 0.42)), (int(r * 0.45), -int(r * 0.42)),
            (-int(r * 0.58), 0), (0, -int(r * 0.05)), (int(r * 0.58), 0),
            (-int(r * 0.42), int(r * 0.42)), (int(r * 0.42), int(r * 0.42)),
            (0, int(r * 0.58))
        ]
        for ox, oy in offsets:
            pygame.draw.circle(surface, col, (cx + ox, cy + oy), sub_r)
            pygame.draw.circle(surface, (20, 20, 20), (cx + ox, cy + oy), sub_r, 1)
            pygame.draw.circle(surface, hi, (cx + ox - sub_r // 3, cy + oy - sub_r // 3), max(2, sub_r // 4))

    elif style == "strawberry":
        pts = [
            (cx - int(r * 0.85), cy - int(r * 0.45)),
            (cx + int(r * 0.85), cy - int(r * 0.45)),
            (cx + int(r * 0.65), cy + int(r * 0.35)),
            (cx, cy + int(r * 0.95)),
            (cx - int(r * 0.65), cy + int(r * 0.35))
        ]
        pygame.draw.polygon(surface, col, pts)
        pygame.draw.polygon(surface, (255, 255, 255), pts, 2)
        for sx, sy in [(-0.3, -0.1), (0.3, -0.1), (0.0, 0.15), (-0.25, 0.35), (0.25, 0.35), (0.0, 0.58)]:
            pygame.draw.circle(surface, (255, 230, 90), (cx + int(r * sx), cy + int(r * sy)), max(2, r // 10))

    elif style == "cherry":
        r_ch = max(5, int(r * 0.58))
        c1 = (cx - int(r * 0.45), cy + int(r * 0.22))
        c2 = (cx + int(r * 0.45), cy + int(r * 0.22))
        pygame.draw.line(surface, leaf_col, (cx, cy - r), c1, 3)
        pygame.draw.line(surface, leaf_col, (cx, cy - r), c2, 3)
        for c_pos in (c1, c2):
            pygame.draw.circle(surface, col, c_pos, r_ch)
            pygame.draw.circle(surface, (255, 255, 255), c_pos, r_ch, 1)
            pygame.draw.circle(surface, hi, (c_pos[0] - r_ch // 3, c_pos[1] - r_ch // 3), max(2, r_ch // 4))

    else:
        pygame.draw.circle(surface, col, (cx, cy), r)
        pygame.draw.circle(surface, (30, 30, 30), (cx, cy), r, 2)
        pygame.draw.circle(surface, hi, (cx - r // 3, cy - r // 3), max(3, r // 4))


def get_bot_hit(target_nums, mode):
    diff = 1 if "Stufe 1" in mode else (2 if "Stufe 2" in mode else 3)
    valid = [t for t in target_nums if t is not None]
    target = random.choice(valid) if valid else 20

    if diff == 1:
        if random.random() < 0.45:
            return "b" if target == 25 else str(target)
        return str(random.randint(1, 20))
    elif diff == 2:
        r = random.random()
        if target == 25:
            return "db" if r < 0.25 else ("b" if r < 0.65 else str(random.randint(1, 20)))
        return f"t{target}" if r < 0.22 else (f"d{target}" if r < 0.45 else (str(target) if r < 0.8 else str(random.randint(1, 20))))
    else:
        r = random.random()
        if target == 25:
            return "db" if r < 0.5 else ("b" if r < 0.85 else str(random.randint(1, 20)))
        return f"t{target}" if r < 0.5 else (f"d{target}" if r < 0.78 else (str(target) if r < 0.92 else "b"))


class ScreenSaver:
    def __init__(self, width, height):
        self.width, self.height, self.active, self.last_activity = width, height, False, pygame.time.get_ticks()
        self.avatars = []
        for file in ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]:
            if os.path.exists(file):
                try:
                    self.avatars.append({
                        "img": pygame.transform.smoothscale(pygame.image.load(file).convert_alpha(), (100, 100)),
                        "x": random.randint(50, width - 150),
                        "y": random.randint(50, height - 150),
                        "vx": random.choice([-2, 2]),
                        "vy": random.choice([-2, 2])
                    })
                except Exception:
                    pass

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

    is_hunt_mode = "Berry Hunt" in option
    is_battle_press = "Battle" in option
    target_splashes = 5 if "5 Beeren" in option else 3
    max_rounds = 15 if "15 Runden" in option else (10 if "10 Runden" in option else 99)
    max_pump = 7

    sw, sh = screen.get_width(), screen.get_height()
    screensaver = ScreenSaver(sw, sh)

    if hasattr(display, 'clear_all'):
        display.clear_all()

    is_16_9 = False
    try:
        with open("settings.json", "r") as f:
            is_16_9 = json.load(f).get("format", "4:3") == "16:9"
    except Exception:
        pass

    bg_candidates = ["background_16_9.jpg", "background_16_9.png"] if is_16_9 else ["background.jpg", "background.png"]
    bg_img = None
    for bf in bg_candidates:
        if os.path.exists(bf):
            try:
                raw_bg = pygame.image.load(bf).convert()
                bg_img = pygame.transform.scale(raw_bg, (sw, sh))
                darker_overlay = pygame.Surface((sw, sh))
                darker_overlay.set_alpha(165)
                darker_overlay.fill((0, 0, 0))
                bg_img.blit(darker_overlay, (0, 0))
                break
            except Exception:
                pass

    avatar_path = {
        "Bullseye-Berry (Stufe 1)": "Bullseye-Berry_Original.png",
        "Bullseye-Berry (Stufe 2)": "Bullseye-Berry_Cyber.png",
        "Bullseye-Berry (Stufe 3)": "Bullseye-Berry_Ninja.png"
    }.get(mode, "")
    avatar_frames = []
    if avatar_path and os.path.exists(avatar_path):
        try:
            raw_av = pygame.image.load(avatar_path).convert_alpha()
            base_sz = int(sh * 0.25)
            for offset in [-8, -4, 0, 4, 8]:
                sz = base_sz + offset
                avatar_frames.append(pygame.transform.smoothscale(raw_av, (sz, sz)))
        except Exception:
            pass

    champ_img = pygame.transform.smoothscale(
        pygame.image.load("Bullseye-Berry_Champ.png").convert_alpha(),
        (int(sh * 0.42), int(sh * 0.42))
    ) if os.path.exists("Bullseye-Berry_Champ.png") else None

    sound_champ = pygame.mixer.Sound("sounds/champ.wav") if os.path.exists("sounds/champ.wav") else None
    sound_single = pygame.mixer.Sound("sounds/hit_single.wav") if os.path.exists("sounds/hit_single.wav") else None
    sound_double = pygame.mixer.Sound("sounds/hit_double.wav") if os.path.exists("sounds/hit_double.wav") else None
    sound_triple = pygame.mixer.Sound("sounds/hit_triple.wav") if os.path.exists("sounds/hit_triple.wav") else None
    sound_switch = pygame.mixer.Sound("sounds/switch_player.wav") if os.path.exists("sounds/switch_player.wav") else None
    sound_miss = pygame.mixer.Sound("sounds/miss.wav") if os.path.exists("sounds/miss.wav") else None

    tiny_font = pygame.font.SysFont("arial", int(sh * 0.018), bold=True)
    small_font = pygame.font.SysFont("arial", int(sh * 0.022), bold=True)
    title_font = pygame.font.SysFont("arial", int(sh * 0.033), bold=True)
    big_font = pygame.font.SysFont("arial", int(sh * 0.044), bold=True)
    win_font_size = int(sh * 0.12) if sh <= 768 else int(sh * 0.20)
    win_font = pygame.font.SysFont("arial", win_font_size, bold=True)

    HIGHLIGHT, WHITE, RED_COL, NEON_GREEN = (255, 215, 0), (255, 255, 255), (255, 60, 80), (0, 255, 157)

    scores = [0] * total_players
    pump_levels = [0] * total_players
    player_targets = []
    used_t = []
    for _ in range(total_players):
        avail = [n for n in range(1, 21) if n not in used_t]
        pick = random.choice(avail) if avail else random.randint(1, 20)
        used_t.append(pick)
        player_targets.append(pick)

    hunt_targets = random.sample(range(1, 21), 6) + [25]
    hunt_profiles = [BERRY_PROFILES[i % len(BERRY_PROFILES)] for i in range(6)] + [GOLDEN_BERRY]

    particles = []
    splash_banner_text = ""
    splash_banner_col = HIGHLIGHT
    splash_banner_until = 0

    def spawn_splash(cx, cy, color, count=34):
        for _ in range(count):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(3.5, 14.0)
            particles.append({
                "x": float(cx),
                "y": float(cy),
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd - 2.0,
                "r": random.randint(4, 12),
                "color": color,
                "life": random.randint(18, 32)
            })

    darts_thrown, active_player = 0, 1
    round_num, round_points, switch_delay_timer = 1, 0, 0
    winner_idx = 0

    if display:
        try:
            display.set_bullseye_icon(True)
        except Exception:
            pass

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
                display.set_score(i, scores[i] if i < total_players else None)

            hw_keys = [20, 19, 18, 17, 16, 15]
            if not is_hunt_mode:
                for s_idx, hw_key in enumerate(hw_keys):
                    if s_idx < total_players:
                        t_val = player_targets[s_idx]
                        marks_led = min(3, int((pump_levels[s_idx] / float(max_pump)) * 3.99))
                        display.set_cricket_marks(s_idx, hw_key, marks_led)
                        if hasattr(display, 'CRICKET_TARGET_DISP') and hw_key in display.CRICKET_TARGET_DISP:
                            d_ten, d_unit = display.CRICKET_TARGET_DISP[hw_key]
                            t_str = f"{t_val:2d}"
                            display.set_disp_char(d_ten, t_str[0])
                            display.set_disp_char(d_unit, t_str[1])
            else:
                for s_idx, hw_key in enumerate(hw_keys):
                    t_val = hunt_targets[s_idx]
                    if hasattr(display, 'CRICKET_TARGET_DISP') and hw_key in display.CRICKET_TARGET_DISP:
                        d_ten, d_unit = display.CRICKET_TARGET_DISP[hw_key]
                        t_str = f"{t_val:2d}"
                        display.set_disp_char(d_ten, t_str[0])
                        display.set_disp_char(d_unit, t_str[1])

            display.set_temp_score(round_points)
            display.set_turn(round_num)
            display.set_dart_arrows(3 - darts_thrown)
            display.update()
        except Exception:
            pass

    sync_hw_display()

    running, clock, current_state = True, pygame.time.Clock(), "GAME"
    champ_display_until, bot_timer = 0, 0
    combo_press_start = 0

    while running:
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
                if sound_switch:
                    sound_switch.play()
                display.clear_all()
                return "menu"

        elif current_state == "GAME":
            if raw_data == "BTN:PLAYER":
                switch_delay_timer = pygame.time.get_ticks()
                raw_data = None
            elif raw_data == "IR:DETECT":
                if darts_thrown >= 3 and not is_berrys_turn:
                    switch_delay_timer = pygame.time.get_ticks() + 1000
                raw_data = None

            if is_berrys_turn and darts_thrown >= 3 and switch_delay_timer == 0:
                if bot_timer == 0:
                    bot_timer = pygame.time.get_ticks() + 1000
                elif pygame.time.get_ticks() > bot_timer:
                    switch_delay_timer = pygame.time.get_ticks() + 1000
                    bot_timer = 0

            if switch_delay_timer > 0 and pygame.time.get_ticks() >= switch_delay_timer:
                switch_delay_timer, darts_thrown, round_points = 0, 0, 0
                if active_player == total_players:
                    if is_hunt_mode and round_num >= max_rounds:
                        winner_idx = max(range(total_players), key=lambda i: scores[i])
                        current_state = "WIN"
                        trigger_victory(ser, display)
                        sync_hw_display()
                        continue
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

            if is_berrys_turn and switch_delay_timer == 0 and darts_thrown < 3 and current_state == "GAME":
                if bot_timer == 0:
                    bot_timer = pygame.time.get_ticks() + random.randint(1100, 1650)
                elif pygame.time.get_ticks() > bot_timer:
                    bot_targets = hunt_targets if is_hunt_mode else [player_targets[active_player - 1], 25]
                    raw_data = f"HIT:{get_bot_hit(bot_targets, mode)}"
                    bot_timer = 0

            if raw_data and (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
                hit_segment = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                p_idx = active_player - 1
                p_profile = BERRY_PROFILES[0] if is_berrys_turn else BERRY_PROFILES[p_idx % len(BERRY_PROFILES)]

                if hit_segment == "MISS":
                    if sound_miss:
                        sound_miss.play()
                elif hit_segment != "-":
                    seg = int(hit_segment.replace("t", "").replace("d", "").replace("b", "25")) if hit_segment != "db" else 25
                    mult = 3 if "t" in hit_segment else (2 if ("d" in hit_segment or hit_segment == "db") else 1)

                    if not is_hunt_mode:
                        my_target = player_targets[p_idx]
                        pumped = 0

                        if seg == my_target:
                            pumped = mult
                        elif seg == 25:
                            pumped = mult
                            if is_battle_press and total_players > 1:
                                rivals = [i for i in range(total_players) if i != p_idx and pump_levels[i] > 0]
                                if rivals:
                                    victim = max(rivals, key=lambda i: (scores[i], pump_levels[i]))
                                    stolen = min(pump_levels[victim], mult)
                                    pump_levels[victim] -= stolen
                                    splash_banner_text = f"BERRY STEAL! -{stolen} bei Spieler {victim + 1}!"
                                    splash_banner_col = GOLDEN_BERRY["color"]
                                    splash_banner_until = pygame.time.get_ticks() + 2000

                        if pumped > 0:
                            pump_levels[p_idx] += pumped
                            round_points += pumped

                            if pump_levels[p_idx] >= max_pump:
                                pump_levels[p_idx] = 0
                                scores[p_idx] += 1
                                avail = [n for n in range(1, 21) if n not in player_targets]
                                player_targets[p_idx] = random.choice(avail) if avail else random.randint(1, 20)

                                spawn_splash(sw // 2, int(sh * 0.52), p_profile["color"], count=48)
                                splash_banner_text = f"SPLASH! (+1)"
                                splash_banner_col = p_profile["color"]
                                splash_banner_until = pygame.time.get_ticks() + 2200
                                champ_display_until = pygame.time.get_ticks() + 1600
                                if sound_champ:
                                    sound_champ.play()
                            else:
                                spawn_splash(sw // 2, int(sh * 0.52), p_profile["color"], count=12 * mult)
                                if mult == 3 and sound_triple:
                                    sound_triple.play()
                                elif mult == 2 and sound_double:
                                    sound_double.play()
                                elif sound_single:
                                    sound_single.play()
                        else:
                            if sound_single:
                                sound_single.play()

                        if scores[p_idx] >= target_splashes:
                            winner_idx = p_idx
                            current_state = "WIN"
                            trigger_victory(ser, display)

                    else:
                        if seg in hunt_targets:
                            h_idx = hunt_targets.index(seg)
                            hit_prof = hunt_profiles[h_idx]
                            base_pts = 50 if seg == 25 else seg
                            pts = base_pts * mult
                            scores[p_idx] += pts
                            round_points += pts

                            spawn_splash(sw // 2, int(sh * 0.55), hit_prof["color"], count=38)
                            splash_banner_text = f"CRUSHED! +{pts} PTS"
                            splash_banner_col = hit_prof["color"]
                            splash_banner_until = pygame.time.get_ticks() + 1800

                            if seg != 25:
                                free_nums = [n for n in range(1, 21) if n not in hunt_targets]
                                if free_nums:
                                    hunt_targets[h_idx] = random.choice(free_nums)
                                hunt_profiles[h_idx] = random.choice(BERRY_PROFILES)

                            if seg == 25 or mult == 3:
                                if sound_champ:
                                    sound_champ.play()
                            elif mult == 2 and sound_double:
                                sound_double.play()
                            elif sound_single:
                                sound_single.play()
                        else:
                            if sound_single:
                                sound_single.play()

                darts_thrown += 1
                if darts_thrown == 3 and ser:
                    try:
                        ser.write(b"LAMP:PLAYER:2\n")
                        ser.flush()
                    except Exception:
                        pass
                sync_hw_display()

        elif current_state == "WIN" and (raw_data in ["BTN:PLAYER", "BTN:START"]):
            if raw_data == "BTN:PLAYER":
                if sound_switch:
                    sound_switch.play()
                display.clear_all()
                return "menu"
            elif raw_data == "BTN:START":
                if sound_switch:
                    sound_switch.play()
                scores = [0] * total_players
                pump_levels = [0] * total_players
                player_targets = random.sample(range(1, 21), total_players)
                hunt_targets = random.sample(range(1, 21), 6) + [25]
                darts_thrown, active_player, round_num, round_points, switch_delay_timer = 0, 1, 1, 0, 0
                current_state = "GAME"
                if display:
                    try:
                        display.set_bullseye_icon(True)
                    except Exception:
                        pass
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
            screen.fill((6, 17, 28))

        if current_state in ["GAME", "ABORT_MENU", "WIN"]:
            rnd_txt = f"Runde {round_num}/{max_rounds}" if is_hunt_mode else f"Runde {round_num} (Ziel: {target_splashes} Splashes)"
            screen.blit(title_font.render(f"FRUIT SPLASHER | {option} | {rnd_txt}", True, HIGHLIGHT), (int(sw * 0.04), int(sh * 0.035)))

            active_prof = BERRY_PROFILES[0] if is_berrys_turn else BERRY_PROFILES[(active_player - 1) % len(BERRY_PROFILES)]
            p_title = f"Bullseye-Berry" if is_berrys_turn else f"Spieler {active_player}"
            name_surf = big_font.render(p_title, True, active_prof["color"])
            screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, int(sh * 0.095)))

            if not is_hunt_mode:
                sub_str = f"Triff Segment [ {player_targets[active_player - 1]} ] oder [ BULL ] zum Aufpumpen!   |   Pfeile: {darts_thrown} / 3"
            else:
                sub_str = f"Runden-Punkte: {round_points}   |   Triff die markierten Beeren-Segmente!   |   Pfeile: {darts_thrown} / 3"
            sub_surf = title_font.render(sub_str, True, (220, 220, 220))
            screen.blit(sub_surf, ((sw - sub_surf.get_width()) // 2, int(sh * 0.165)))

            if darts_thrown >= 3 and not is_berrys_turn and current_state == "GAME":
                block_hint = title_font.render("Bitte Pfeile ziehen -> IR-Sensor oder Spielerwechsel drücken!", True, RED_COL)
                screen.blit(block_hint, ((sw - block_hint.get_width()) // 2, int(sh * 0.22)))

            if not is_hunt_mode:
                cols = min(4, total_players)
                rows = math.ceil(total_players / float(cols))
                card_w = int(sw * 0.88 / cols) - 16
                card_h = int(sh * (0.58 if rows == 1 else 0.30))
                grid_x = (sw - (cols * (card_w + 16) - 16)) // 2
                grid_y = int(sh * 0.28)

                for i in range(total_players):
                    r_idx = i // cols
                    c_idx = i % cols
                    cx = grid_x + c_idx * (card_w + 16)
                    cy = grid_y + r_idx * (card_h + 18)
                    prof = BERRY_PROFILES[0] if (is_berry_game and i == total_players - 1) else BERRY_PROFILES[i % len(BERRY_PROFILES)]
                    is_act = (i == active_player - 1)

                    card_bg = (22, 42, 62) if is_act else (12, 22, 34)
                    border_col = prof["color"] if is_act else (60, 80, 100)
                    pygame.draw.rect(screen, card_bg, (cx, cy, card_w, card_h), border_radius=14)
                    pygame.draw.rect(screen, border_col, (cx, cy, card_w, card_h), width=4 if is_act else 2, border_radius=14)

                    lbl = "Bullseye-Berry" if (is_berry_game and i == total_players - 1) else f"Spieler {i + 1}"
                    t_s = title_font.render(lbl, True, prof["color"] if is_act else WHITE)
                    screen.blit(t_s, (cx + (card_w - t_s.get_width()) // 2, cy + 6))

                    badge_txt1 = tiny_font.render(f"ZIEL: {player_targets[i]}", True, HIGHLIGHT)
                    badge_txt2 = tiny_font.render("BULLSEYE AKTIV", True, (0, 220, 255))
                    
                    screen.blit(badge_txt1, (cx + (card_w - badge_txt1.get_width()) // 2, cy + int(card_h * 0.15)))
                    screen.blit(badge_txt2, (cx + (card_w - badge_txt2.get_width()) // 2, cy + int(card_h * 0.26)))

                    base_rad = int(min(card_w, card_h) * 0.14)
                    draw_berry_icon(screen, cx + card_w // 2, cy + int(card_h * 0.52), base_rad, prof, pump_levels[i], max_pump)

                    bar_w = int(card_w * 0.82)
                    bar_h = int(card_h * 0.08)
                    bar_x = cx + (card_w - bar_w) // 2
                    bar_y = cy + card_h - bar_h - int(card_h * 0.18)
                    pygame.draw.rect(screen, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
                    fill_w = int(bar_w * (pump_levels[i] / float(max_pump)))
                    if fill_w > 0:
                        pygame.draw.rect(screen, prof["color"], (bar_x, bar_y, fill_w, bar_h), border_radius=6)
                    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_w, bar_h), 1, border_radius=6)

                    score_str = tiny_font.render(f"Splashes: {scores[i]}/{target_splashes}  |  Juice: {pump_levels[i]}/{max_pump}", True, NEON_GREEN if scores[i] > 0 else (190, 190, 190))
                    screen.blit(score_str, (cx + (card_w - score_str.get_width()) // 2, cy + card_h - int(card_h * 0.08)))

            else:
                hunt_y = int(sh * 0.28)
                card_w = int(sw * 0.12)
                card_h = int(sh * 0.32)
                gap = int(sw * 0.012)
                start_x = (sw - (7 * card_w + 6 * gap)) // 2

                for h_i in range(7):
                    hx = start_x + h_i * (card_w + gap)
                    t_num = hunt_targets[h_i]
                    h_prof = hunt_profiles[h_i]
                    is_gold = (t_num == 25)

                    pygame.draw.rect(screen, (18, 32, 48), (hx, hunt_y, card_w, card_h), border_radius=12)
                    pygame.draw.rect(screen, HIGHLIGHT if is_gold else h_prof["color"], (hx, hunt_y, card_w, card_h), 3 if is_gold else 2, border_radius=12)

                    num_lbl = "BULL" if is_gold else str(t_num)
                    n_surf = big_font.render(num_lbl, True, HIGHLIGHT if is_gold else WHITE)
                    screen.blit(n_surf, (hx + (card_w - n_surf.get_width()) // 2, hunt_y + 10))

                    draw_berry_icon(screen, hx + card_w // 2, hunt_y + int(card_h * 0.55), int(card_w * 0.25), h_prof, 2, 7)

                    pts_lbl = "50/100" if is_gold else f"{t_num} Pkt"
                    p_surf = small_font.render(pts_lbl, True, h_prof["color"])
                    screen.blit(p_surf, (hx + (card_w - p_surf.get_width()) // 2, hunt_y + card_h - int(sh * 0.045)))

                sb_y = int(sh * 0.65)
                p_box_w = int(sw * 0.88 / total_players) - 10
                sb_x = (sw - (total_players * (p_box_w + 10) - 10)) // 2
                for i in range(total_players):
                    px = sb_x + i * (p_box_w + 10)
                    prof = BERRY_PROFILES[0] if (is_berry_game and i == total_players - 1) else BERRY_PROFILES[i % len(BERRY_PROFILES)]
                    is_act = (i == active_player - 1)
                    pygame.draw.rect(screen, (28, 52, 76) if is_act else (14, 24, 36), (px, sb_y, p_box_w, int(sh * 0.22)), border_radius=12)
                    pygame.draw.rect(screen, prof["color"] if is_act else (70, 90, 110), (px, sb_y, p_box_w, int(sh * 0.22)), 3 if is_act else 1, border_radius=12)

                    p_name = "Berry" if (is_berry_game and i == total_players - 1) else f"Spieler {i + 1}"
                    pn_surf = title_font.render(p_name, True, prof["color"])
                    screen.blit(pn_surf, (px + (p_box_w - pn_surf.get_width()) // 2, sb_y + 12))

                    sc_surf = big_font.render(str(scores[i]), True, HIGHLIGHT if is_act else WHITE)
                    screen.blit(sc_surf, (px + (p_box_w - sc_surf.get_width()) // 2, sb_y + int(sh * 0.095)))

            for pt in particles[:]:
                pt["x"] += pt["vx"]
                pt["y"] += pt["vy"]
                pt["vy"] += 0.45
                pt["life"] -= 1
                if pt["life"] <= 0:
                    particles.remove(pt)
                else:
                    pygame.draw.circle(screen, pt["color"], (int(pt["x"]), int(pt["y"])), pt["r"])
                    pygame.draw.circle(screen, WHITE, (int(pt["x"]) - 2, int(pt["y"]) - 2), max(1, pt["r"] // 3))

            if pygame.time.get_ticks() < splash_banner_until and splash_banner_text:
                b_surf = big_font.render(splash_banner_text, True, splash_banner_col)
                bx = (sw - b_surf.get_width()) // 2
                by = int(sh * 0.88)
                pygame.draw.rect(screen, (0, 0, 0), (bx - 20, by - 8, b_surf.get_width() + 40, b_surf.get_height() + 16), border_radius=12)
                pygame.draw.rect(screen, splash_banner_col, (bx - 20, by - 8, b_surf.get_width() + 40, b_surf.get_height() + 16), 3, border_radius=12)
                screen.blit(b_surf, (bx, by))

            if is_berrys_turn and avatar_frames:
                idx_anim = int((math.sin(pygame.time.get_ticks() * 0.005) + 1.0) * 2.49)
                idx_anim = max(0, min(len(avatar_frames) - 1, idx_anim))
                screen.blit(avatar_frames[idx_anim], (int(sw * 0.80), int(sh * 0.68)))

            if pygame.time.get_ticks() < champ_display_until and champ_img:
                screen.blit(champ_img, ((sw - champ_img.get_width()) // 2, (sh - champ_img.get_height()) // 2))

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
                txt_head = win_font.render("BERRY SPLASH!", True, NEON_GREEN)
                screen.blit(txt_head, ((sw - txt_head.get_width()) // 2, win_y))

                win_prof = BERRY_PROFILES[0] if (is_berry_game and winner_idx == total_players - 1) else BERRY_PROFILES[winner_idx % len(BERRY_PROFILES)]
                winner_name = "Bullseye-Berry" if (is_berry_game and winner_idx == total_players - 1) else f"Spieler {winner_idx + 1}"
                txt_winner = big_font.render(f"{winner_name} gewinnt!", True, win_prof["color"])
                screen.blit(txt_winner, ((sw - txt_winner.get_width()) // 2, win_y + int(sh * 0.22)))

                txt_start = title_font.render("> START = Spiel neu starten <", True, (50, 255, 50))
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, win_y + int(sh * 0.36)))

                txt_end = title_font.render("> SPIELERWECHSEL = Hauptmenü <", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, win_y + int(sh * 0.46)))

        pygame.display.flip()
        clock.tick(30)
