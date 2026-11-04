# Datei: game_fruit_splasher.py
# Version: 1.2.3
# VisionPi2000 - Fruit Splasher (Juice Press & Berry Hunt Edition - Fast-Load Cache & Immediate Victory Fix)

import pygame
import math
import os
import random
import time
import json

VERSION = "1.2.3"
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
    {"name": "Triple-Strawberry",  "fruit": "Strawberry",  "color": (255, 35, 55),   "hi": (255, 160, 170), "style": "strawberry"},
    {"name": "Bouncer-Blueberry",  "fruit": "Blueberry",   "color": (0, 160, 255),   "hi": (150, 225, 255), "style": "round"},
    {"name": "Checkout-Cherry",    "fruit": "Cherry",      "color": (220, 0, 55),    "hi": (255, 150, 175), "style": "cherry"},
    {"name": "Double-Dewberry",    "fruit": "Dewberry",    "color": (150, 40, 255),  "hi": (215, 170, 255), "style": "cluster"},
    {"name": "Flight-Huckleberry", "fruit": "Huckleberry", "color": (60, 90, 255),   "hi": (170, 190, 255), "style": "round"},
    {"name": "Scoring-Snowberry",  "fruit": "Snowberry",   "color": (225, 240, 255), "hi": (255, 255, 255), "style": "round"},
    {"name": "Master-Mulberry",    "fruit": "Mulberry",    "color": (200, 0, 175),   "hi": (255, 150, 240), "style": "cluster"}
]

GOLDEN_BERRY = {"name": "Golden-Raspberry", "fruit": "Golden-Berry", "color": (255, 215, 0), "hi": (255, 255, 190), "style": "cluster"}

# Modulweiter Asset-Cache verhindert erneutes Laden & Skalieren von SD-Karte bei jedem Spielstart
_ASSET_CACHE = {}


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
                    darker_overlay.fill((0, 0, 0))
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


def _shade(col, factor):
    return (
        max(0, min(255, int(col[0] * factor))),
        max(0, min(255, int(col[1] * factor))),
        max(0, min(255, int(col[2] * factor)))
    )


def draw_berry_icon(surface, cx, cy, radius, profile, pump_stage=0, max_stage=7):
    scale = 1.0 + (pump_stage / float(max(1, max_stage))) * 0.55
    r = max(10, int(radius * scale))
    col = profile["color"]
    hi = profile["hi"]
    dark_col = _shade(col, 0.52)
    deep_col = _shade(col, 0.28)
    style = profile["style"]

    if pump_stage >= max_stage - 1:
        pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.015)) * 8)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), r + 7 + pulse, 2)
        pygame.draw.circle(surface, col, (cx, cy), r + 4 + pulse, 2)

    leaf_col = (25, 215, 95)
    leaf_dark = (10, 135, 55)
    leaf_hi = (130, 250, 165)
    stem_col = (95, 175, 65)

    if style == "strawberry":
        pts = []
        pts_inner = []
        for i in range(36):
            t = (i / 36.0) * 2.0 * math.pi
            sin_t = math.sin(t)
            cos_t = math.cos(t)
            width_mod = 0.72 + 0.26 * (-cos_t) - 0.08 * (cos_t ** 2)
            x = cx + int(r * 1.05 * sin_t * width_mod)
            y_norm = -cos_t
            if y_norm < 0:
                y = cy + int(r * (0.68 * y_norm + 0.10 * (1.0 - abs(sin_t))))
            else:
                y = cy + int(r * (1.08 * y_norm))
            pts.append((x, y))
            pts_inner.append((cx + int((x - cx) * 0.86) - 1, cy + int((y - cy) * 0.86) - 1))

        pygame.draw.polygon(surface, dark_col, pts)
        pygame.draw.polygon(surface, col, pts_inner)
        pygame.draw.polygon(surface, deep_col, pts, 2)

        gloss_pts = [
            (cx - int(r * 0.52), cy - int(r * 0.30)),
            (cx - int(r * 0.25), cy - int(r * 0.42)),
            (cx - int(r * 0.32), cy + int(r * 0.12)),
            (cx - int(r * 0.56), cy - int(r * 0.02))
        ]
        pygame.draw.polygon(surface, hi, gloss_pts)

        seed_rows = [
            (-0.48, -0.22), (-0.16, -0.26), (0.16, -0.26), (0.48, -0.22),
            (-0.56,  0.04), (-0.28,  0.02), (0.00,  0.02), (0.28,  0.02), (0.56,  0.04),
            (-0.42,  0.30), (-0.14,  0.32), (0.14,  0.32), (0.42,  0.30),
            (-0.24,  0.58), (0.00,   0.62), (0.24,  0.58),
            (0.00,   0.84)
        ]
        sr = max(2, r // 11)
        for sx, sy in seed_rows:
            px = cx + int(r * sx)
            py = cy + int(r * sy)
            pygame.draw.circle(surface, dark_col, (px, py + 1), sr + 1)
            pygame.draw.polygon(surface, (255, 230, 95), [
                (px, py - sr),
                (px + sr, py + 1),
                (px, py + sr + 1),
                (px - sr, py + 1)
            ])

        top_y = cy - int(r * 0.58)
        pygame.draw.line(surface, stem_col, (cx, top_y), (cx + int(r * 0.14), top_y - int(r * 0.38)), max(3, r // 6))
        sepal_angles = [-1.15, -0.58, 0.0, 0.58, 1.15]
        for ang in sepal_angles:
            tip_x = cx + int(math.sin(ang) * r * 0.72)
            tip_y = top_y + int(math.cos(ang) * r * 0.34)
            left_x = cx + int(math.sin(ang - 0.35) * r * 0.25)
            right_x = cx + int(math.sin(ang + 0.35) * r * 0.25)
            base_y = top_y - int(r * 0.04)
            poly = [(cx, base_y), (left_x, top_y + int(r * 0.08)), (tip_x, tip_y), (right_x, top_y + int(r * 0.08))]
            pygame.draw.polygon(surface, leaf_col, poly)
            pygame.draw.polygon(surface, leaf_dark, poly, 1)
        pygame.draw.circle(surface, leaf_hi, (cx, top_y), max(2, r // 7))

    elif style == "cluster":
        top_y = cy - int(r * 0.72)
        pygame.draw.line(surface, stem_col, (cx, top_y), (cx + int(r * 0.15), top_y - int(r * 0.36)), max(3, r // 6))
        for side in (-1, 1):
            l_poly = [
                (cx, top_y + 2),
                (cx + side * int(r * 0.28), top_y - int(r * 0.24)),
                (cx + side * int(r * 0.62), top_y - int(r * 0.08)),
                (cx + side * int(r * 0.25), top_y + int(r * 0.10))
            ]
            pygame.draw.polygon(surface, leaf_col, l_poly)
            pygame.draw.polygon(surface, leaf_dark, l_poly, 1)

        sub_r = max(4, int(r * 0.29))
        drupelets = [
            (-0.36, -0.56), (0.0, -0.62), (0.36, -0.56),
            (-0.56, -0.26), (-0.19, -0.30), (0.19, -0.30), (0.56, -0.26),
            (-0.60,  0.06), (-0.22,  0.04), (0.22,  0.04), (0.60,  0.06),
            (-0.46,  0.38), (0.0,    0.36), (0.46,  0.38),
            (-0.24,  0.66), (0.24,   0.66),
            (0.0,    0.82)
        ]
        for ox, oy in drupelets:
            dx = cx + int(r * ox)
            dy = cy + int(r * oy)
            pygame.draw.circle(surface, deep_col, (dx, dy + 1), sub_r + 1)
            pygame.draw.circle(surface, dark_col, (dx, dy), sub_r)
            pygame.draw.circle(surface, col, (dx - 1, dy - 1), max(2, int(sub_r * 0.85)))
            pygame.draw.circle(surface, hi, (dx - sub_r // 3, dy - sub_r // 3), max(2, int(sub_r * 0.36)))
            pygame.draw.circle(surface, (255, 255, 255), (dx - sub_r // 3 - 1, dy - sub_r // 3 - 1), max(1, int(sub_r * 0.16)))

    elif style == "cherry":
        r_ch = max(6, int(r * 0.56))
        c1 = (cx - int(r * 0.46), cy + int(r * 0.30))
        c2 = (cx + int(r * 0.44), cy + int(r * 0.36))
        knot = (cx + int(r * 0.06), cy - int(r * 0.78))

        mid1 = (cx - int(r * 0.26), cy - int(r * 0.25))
        mid2 = (cx + int(r * 0.30), cy - int(r * 0.22))
        pygame.draw.lines(surface, stem_col, False, [knot, mid1, (c1[0], c1[1] - r_ch + 3)], max(2, r // 8))
        pygame.draw.lines(surface, stem_col, False, [knot, mid2, (c2[0], c2[1] - r_ch + 3)], max(2, r // 8))

        leaf_poly = [
            knot,
            (knot[0] + int(r * 0.35), knot[1] - int(r * 0.18)),
            (knot[0] + int(r * 0.68), knot[1] + int(r * 0.04)),
            (knot[0] + int(r * 0.30), knot[1] + int(r * 0.16))
        ]
        pygame.draw.polygon(surface, leaf_col, leaf_poly)
        pygame.draw.polygon(surface, leaf_dark, leaf_poly, 1)
        pygame.draw.circle(surface, leaf_hi, knot, max(2, r // 9))

        for c_pos in (c1, c2):
            kx, ky = c_pos
            pygame.draw.circle(surface, deep_col, (kx, ky + 1), r_ch + 1)
            pygame.draw.circle(surface, dark_col, (kx, ky), r_ch)
            pygame.draw.circle(surface, col, (kx - 1, ky - 1), int(r_ch * 0.88))
            pygame.draw.arc(surface, deep_col, (kx - r_ch // 3, ky - r_ch + 1, (r_ch * 2) // 3, r_ch // 3), 3.4, 6.0, 2)
            pygame.draw.circle(surface, hi, (kx - int(r_ch * 0.34), ky - int(r_ch * 0.32)), max(2, int(r_ch * 0.28)))
            pygame.draw.circle(surface, (255, 255, 255), (kx - int(r_ch * 0.38), ky - int(r_ch * 0.36)), max(1, int(r_ch * 0.14)))

    else:
        pygame.draw.circle(surface, deep_col, (cx, cy + 1), r + 1)
        pygame.draw.circle(surface, dark_col, (cx, cy), r)
        pygame.draw.circle(surface, col, (cx - int(r * 0.06), cy - int(r * 0.06)), int(r * 0.88))
        pygame.draw.circle(surface, _shade(col, 1.15), (cx - int(r * 0.18), cy - int(r * 0.18)), int(r * 0.62))

        pygame.draw.circle(surface, hi, (cx - int(r * 0.34), cy - int(r * 0.32)), max(3, int(r * 0.26)))
        pygame.draw.circle(surface, (255, 255, 255), (cx - int(r * 0.38), cy - int(r * 0.36)), max(2, int(r * 0.12)))

        crown_y = cy - int(r * 0.78)
        crown_pts = [
            (cx - int(r * 0.36), crown_y + int(r * 0.12)),
            (cx - int(r * 0.28), crown_y - int(r * 0.14)),
            (cx - int(r * 0.10), crown_y + int(r * 0.04)),
            (cx,                 crown_y - int(r * 0.18)),
            (cx + int(r * 0.10), crown_y + int(r * 0.04)),
            (cx + int(r * 0.28), crown_y - int(r * 0.14)),
            (cx + int(r * 0.36), crown_y + int(r * 0.12))
        ]
        pygame.draw.polygon(surface, deep_col, crown_pts)
        pygame.draw.lines(surface, hi, False, crown_pts, 1)


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

    is_hunt_mode = "Berry Hunt" in option
    is_battle_press = "Battle" in option
    target_splashes = 5 if "5 Beeren" in option else 3
    max_rounds = 15 if "15 Runden" in option else (10 if "10 Runden" in option else 99)
    max_pump = 7

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

    champ_key = f"champ_{sh}"
    if champ_key not in _ASSET_CACHE:
        if os.path.exists("Bullseye-Berry_Champ.png"):
            try:
                _ASSET_CACHE[champ_key] = pygame.transform.smoothscale(
                    pygame.image.load("Bullseye-Berry_Champ.png").convert_alpha(),
                    (int(sh * 0.42), int(sh * 0.42))
                )
            except Exception:
                _ASSET_CACHE[champ_key] = None
        else:
            _ASSET_CACHE[champ_key] = None
    champ_img = _ASSET_CACHE[champ_key]

    sound_champ = _get_cached_sound("sounds/champ.wav")
    sound_single = _get_cached_sound("sounds/hit_single.wav")
    sound_double = _get_cached_sound("sounds/hit_double.wav")
    sound_triple = _get_cached_sound("sounds/hit_triple.wav")
    sound_switch = _get_cached_sound("sounds/switch_player.wav")
    sound_miss = _get_cached_sound("sounds/miss.wav")

    tiny_font = _get_cached_font(int(sh * 0.018))
    small_font = _get_cached_font(int(sh * 0.022))

    sb_font_size = int(sh * 0.030) if total_players <= 4 else (int(sh * 0.025) if total_players <= 6 else int(sh * 0.020))
    scoreboard_font = _get_cached_font(sb_font_size)

    title_font = _get_cached_font(int(sh * 0.033))
    big_font = _get_cached_font(int(sh * 0.044))
    win_font_size = int(sh * 0.12) if sh <= 768 else int(sh * 0.20)
    win_font = _get_cached_font(win_font_size)

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
                act_p_idx = active_player - 1
                act_target = player_targets[act_p_idx]

                marks_led = min(3, int((pump_levels[act_p_idx] / float(max_pump)) * 3.99))
                display.set_cricket_marks(act_p_idx, 20, marks_led)

                for hw_key in hw_keys:
                    if hasattr(display, 'CRICKET_TARGET_DISP') and hw_key in display.CRICKET_TARGET_DISP:
                        d_ten, d_unit = display.CRICKET_TARGET_DISP[hw_key]
                        if hw_key == 20:
                            t_str = f"{act_target:2d}"
                            display.set_disp_char(d_ten, t_str[0])
                            display.set_disp_char(d_unit, t_str[1])
                        else:
                            display.set_disp_char(d_ten, " ")
                            display.set_disp_char(d_unit, " ")
            else:
                for s_idx, hw_key in enumerate(hw_keys):
                    if s_idx < len(hunt_targets) - 1:
                        t_val = hunt_targets[s_idx]
                        if hasattr(display, 'CRICKET_TARGET_DISP') and hw_key in display.CRICKET_TARGET_DISP:
                            d_ten, d_unit = display.CRICKET_TARGET_DISP[hw_key]
                            t_str = f"{t_val:2d}"
                            display.set_disp_char(d_ten, t_str[0])
                            display.set_disp_char(d_unit, t_str[1])
                if 25 in hunt_targets:
                    display.set_bullseye_icon(True)

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
                                splash_banner_text = "SPLASH! (+1)"
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
            p_title = "Bullseye-Berry" if is_berrys_turn else f"Spieler {active_player}"
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
                    border_col = prof["color"]
                    pygame.draw.rect(screen, card_bg, (cx, cy, card_w, card_h), border_radius=14)
                    pygame.draw.rect(screen, border_col, (cx, cy, card_w, card_h), width=4 if is_act else 2, border_radius=14)

                    lbl = "Bullseye-Berry" if (is_berry_game and i == total_players - 1) else f"Spieler {i + 1}"
                    t_s = title_font.render(lbl, True, prof["color"])
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
                    pygame.draw.rect(screen, prof["color"], (px, sb_y, p_box_w, int(sh * 0.22)), 4 if is_act else 2, border_radius=12)

                    p_name = "Berry" if (is_berry_game and i == total_players - 1) else f"Spieler {i + 1}"
                    pn_surf = scoreboard_font.render(p_name, True, prof["color"])
                    screen.blit(pn_surf, (px + (p_box_w - pn_surf.get_width()) // 2, sb_y + 10))

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
