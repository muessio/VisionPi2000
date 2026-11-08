# Datei: game_splitscore.py
# Version: 1.1.5
# VisionPi2000 - Split Score - Berry-Rahmenfarben & Fast-Load Cache

import pygame
import math
import os
import random
import time

VERSION = "1.1.5"
GAMES = ["Split Score"]
OPTIONS = ["Standard"]

PLAYER_COLORS = [
    (255, 0, 90),     # Spieler 1 / Berry: Raspberry Pink
    (255, 45, 45),    # Spieler 2: Strawberry Red
    (0, 180, 255),    # Spieler 3: Blueberry Cyan
    (220, 0, 70),     # Spieler 4: Cherry
    (160, 50, 255),   # Spieler 5: Dewberry Purple
    (70, 100, 255),   # Spieler 6: Huckleberry Blue
    (235, 245, 255),  # Spieler 7: Snowberry White-Blue
    (210, 0, 180)    # Spieler 8: Mulberry Magenta
]

if not hasattr(pygame, "_vp2000_cache"):
    pygame._vp2000_cache = {}
_CACHE = pygame._vp2000_cache


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
                    darker_overlay.set_alpha(160)
                    darker_overlay.fill((0, 0, 0))
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

def get_target_name(tgt):
    """Gibt den ausgeschriebenen Namen für das Split-Score-Ziel zurück."""
    if tgt == "D": return "Double"
    if tgt == "T": return "Triple"
    if tgt == "B": return "Bullseye"
    return str(tgt)

def get_bot_hit(target, mode):
    diff = 1 if "Stufe 1" in mode else (2 if "Stufe 2" in mode else 3)
    if target == "D": return f"d{random.randint(1,20)}" if random.random() < (0.2*diff) else "20"
    if target == "T": return f"t{random.randint(1,20)}" if random.random() < (0.2*diff) else "20"
    if target == "B": return "b" if random.random() < (0.3*diff) else "20"
    return str(target) if random.random() < (0.3*diff) else str(random.randint(1,20))


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
        hint = font.render("STANDBY – Beliebige Taste drücken", True, (120, 120, 120))
        screen.blit(hint, hint.get_rect(center=(self.width // 2, self.height - 40)))


def run_game(screen, ser, display, players, game_name, option, mode):
    is_berry_game = "Bullseye-Berry" in mode
    total_players = min(8, players + 1 if is_berry_game else players)
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
    sound_miss = _get_sound("sounds/miss.wav")
    sound_bust = _get_sound("sounds/bust.wav")

    title_font = _get_font(int(sh * 0.032))
    big_font = _get_font(int(sh * 0.045))
    
    sb_font_size = int(sh * 0.026) if total_players <= 4 else (int(sh * 0.022) if total_players <= 6 else int(sh * 0.018))
    scoreboard_font = _get_font(sb_font_size)

    win_font_size = int(sh * 0.12) if sh <= 768 else int(sh * 0.20)
    win_font = _get_font(win_font_size)
    giant_font = _get_font(int(sh * 0.20))
    
    HIGHLIGHT, WHITE, RED_COL = (255, 215, 0), (255, 255, 255), (180, 30, 30)

    scores = [40] * total_players
    targets = [15, 16, "D", 17, 18, "T", 19, 20, "B"]
    darts_thrown, active_player, round_points, switch_delay_timer, current_round = 0, 1, 0, 0, 0

    if ser:
        try: ser.write(b"LAMP:PLAYER:1
"); ser.write(b"LAMP:START:0
"); ser.flush()
        except Exception: pass

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
            if raw_data == "BTN:PLAYER" or keys[pygame.K_p]:
                if sound_switch: sound_switch.play()
                display.clear_all()
                return "menu"
            elif raw_data == "BTN:START" or keys[pygame.K_SPACE]:
                if sound_switch: sound_switch.play()
                scores = [40] * total_players
                darts_thrown, active_player, round_points, switch_delay_timer, current_round = 0, 1, 0, 0, 0
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
                active_player = (active_player % total_players) + 1
                if active_player == 1: current_round += 1
                
                if current_round >= len(targets):
                    current_round = len(targets) - 1
                    current_state = "WIN"
                    trigger_victory(ser, display)
                    display.clear_all()
                    sync_hw_display()
                else:
                    if sound_switch: sound_switch.play()
                    if ser:
                        try: ser.write(b"LAMP:PLAYER:1
"); ser.flush()
                        except Exception: pass
                    sync_hw_display(); bot_timer = 0; is_berrys_turn = (is_berry_game and active_player == total_players)

            if is_berrys_turn and switch_delay_timer == 0 and darts_thrown < 3:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800) 
                elif pygame.time.get_ticks() > bot_timer:
                    raw_data = f"HIT:{get_bot_hit(targets[current_round], mode)}"; bot_timer = 0 

        if raw_data and current_state == "GAME":
            if (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
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
                if darts_thrown == 3:
                    if round_points == 0:
                        scores[p_idx] //= 2
                        if sound_bust: sound_bust.play()

                    # Sofortige Prüfung nach dem 3. Pfeil des letzten Spielers, ob das Spiel beendet ist!
                    # Verhindert, dass man auf IR-Sensor oder Spielerwechsel warten muss, bevor die Siegesmelodie kommt.
                    is_last_player = (active_player == total_players)
                    is_last_target = (current_round >= len(targets) - 1)
                    
                    if is_last_player and is_last_target:
                        current_state = "WIN"
                        trigger_victory(ser, display)
                        display.clear_all()
                        sync_hw_display()
                    elif ser:
                        try: ser.write(b"LAMP:PLAYER:2
"); ser.flush()
                        except Exception: pass
                
                sync_hw_display()

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font); pygame.display.flip(); clock.tick(30); continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        if current_state in ["GAME", "ABORT_MENU", "WIN"]:
            target_val = targets[current_round] if current_round < len(targets) else "Ende"
            target_str = get_target_name(target_val)
            
            screen.blit(title_font.render(f"SPIEL: Split Score | Ziel: {target_str}", True, HIGHLIGHT), (int(sw*0.04), int(sh*0.04)))
            act_col = PLAYER_COLORS[0] if is_berrys_turn else PLAYER_COLORS[(active_player - 1) % len(PLAYER_COLORS)]
            name_surf = big_font.render(mode if is_berrys_turn else f"Spieler {active_player}", True, act_col)
            screen.blit(name_surf, ((sw - name_surf.get_width()) // 2, int(sh*0.09)))
            temp_score_surf = title_font.render(f"Ziel-Modus: {target_str}", True, (200, 200, 200))
            screen.blit(temp_score_surf, ((sw - temp_score_surf.get_width()) // 2, int(sh*0.14)))
            score_surf = giant_font.render(str(scores[active_player-1]), True, WHITE)
            screen.blit(score_surf, ((sw - score_surf.get_width()) // 2, int(sh*0.19)))
            
            if darts_thrown >= 3 and not is_berrys_turn and current_state == "GAME":
                block_hint = title_font.render("Bitte Pfeile ziehen -> IR-Sensor oder Spielerwechsel drücken!", True, RED_COL)
                screen.blit(block_hint, ((sw - block_hint.get_width())//2, int(sh*0.56)))

            darts_surf = title_font.render(f"Pfeile: {darts_thrown} / 3", True, (180, 180, 180))
            screen.blit(darts_surf, ((sw - darts_surf.get_width()) // 2, int(sh*0.62)))

            sb_y = int(sh * 0.68)
            box_h = int(sh * 0.28)
            p_box_w = int(sw * 0.88 / total_players) - 10
            sb_x = (sw - (total_players * (p_box_w + 10) - 10)) // 2
            
            for i in range(total_players):
                px = sb_x + i * (p_box_w + 10)
                is_act = (i == (active_player - 1))
                p_n = "Berry" if (is_berry_game and i == total_players - 1) else f"Spieler {i+1}"
                p_col = PLAYER_COLORS[0] if (is_berry_game and i == total_players - 1) else PLAYER_COLORS[i % len(PLAYER_COLORS)]
                
                pygame.draw.rect(screen, (28, 52, 76) if is_act else (14, 24, 36), (px, sb_y, p_box_w, box_h), border_radius=12)
                pygame.draw.rect(screen, p_col, (px, sb_y, p_box_w, box_h), 4 if is_act else 2, border_radius=12)

                pn_surf = scoreboard_font.render(p_n, True, p_col)
                screen.blit(pn_surf, (px + (p_box_w - pn_surf.get_width()) // 2, sb_y + 10))

                sc_surf = big_font.render(str(scores[i]), True, HIGHLIGHT if is_act else WHITE)
                screen.blit(sc_surf, (px + (p_box_w - sc_surf.get_width()) // 2, sb_y + int(box_h * 0.40)))

            if is_berrys_turn and avatar_frames:
                idx_anim = int((math.sin(pygame.time.get_ticks() * 0.005) + 1.0) * 2.49)
                idx_anim = max(0, min(len(avatar_frames) - 1, idx_anim))
                screen.blit(avatar_frames[idx_anim], (int(sw*0.78), int(sh*0.38)))
            if pygame.time.get_ticks() < champ_display_until and champ_img:
                screen.blit(champ_img, ((sw - champ_img.get_width()) // 2, (sh - champ_img.get_height()) // 2))
                screen.blit(giant_font.render("BOOM!", True, HIGHLIGHT), ((sw - 200) // 2, int(sh*0.45)))

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
                screen.blit(txt_head, ((sw - win_font.get_width()) // 2, win_y))
                
                winner_name = mode if is_berrys_trigger_if_needed := is_berry_game else f"Spieler {active_player}"
                txt_winner = big_font.render(f"Spielende erreicht!", True, act_col)
                screen.blit(txt_winner, ((sw - txt_winner.get_width()) // 2, win_y + int(sh * 0.22)))
                
                txt_start = title_font.render("> START = Spiel neu starten <", True, (50, 255, 50))
                screen.blit(txt_start, ((sw - txt_start.get_width()) // 2, win_y + int(sh * 0.36)))
                
                txt_end = title_font.render("> SPIELERWECHSEL = Hauptmenü <", True, RED_COL)
                screen.blit(txt_end, ((sw - txt_end.get_width()) // 2, win_y + int(sh * 0.46)))
                
        pygame.display.flip(); clock.tick(30)
