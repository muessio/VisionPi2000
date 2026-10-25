import pygame
import math
import os
import random

VERSION = "1.4.0"
GAMES = ["Cricket"]
OPTIONS = ["Standard"]
TARGETS = [15, 16, 17, 18, 19, 20, 25]

def parse_hit(hit_str):
    if hit_str in ["-", "WIN_CHEAaT", "MISS"]: return (0, 0)
    if hit_str == "b": return (25, 1)   
    if hit_str == "db": return (25, 2)  
    mult = 3 if hit_str.startswith("t") else (2 if hit_str.startswith("d") else 1)
    return (int(hit_str.replace("d", "").replace("t", "")), mult)

def get_bot_hit(bot_marks, p1_marks, diff):
    if random.random() < {1: 0.30, 2: 0.60, 3: 0.95}[diff]:
        for t in [20, 19, 18, 17, 16, 15, 25]:
            if bot_marks[t] < 3 or p1_marks[t] < 3:
                return "b" if t == 25 else (f"t{t}" if diff == 3 and random.random() < 0.5 else str(t))
        return "20"
    return str(random.randint(1, 14))

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
    is_berry_game = "Bullseye-Berry" in mode
    total_players = players + 1 if is_berry_game else players
    screensaver = ScreenSaver(screen.get_width(), screen.get_height())

    try:
        display.clear_all()
    except:
        pass

    bg_img = None
    if os.path.exists("background.png"):
        try:
            raw_bg = pygame.image.load("background.png").convert()
            bg_img = pygame.transform.scale(raw_bg, (screen.get_width(), screen.get_height()))
            darker_overlay = pygame.Surface((screen.get_width(), screen.get_height()))
            darker_overlay.set_alpha(120)
            darker_overlay.fill((0, 0, 0))
            bg_img.blit(darker_overlay, (0, 0))
        except: pass

    berry_images = {"Bullseye-Berry (Leicht)": "Bullseye-Berry_Original.png", "Bullseye-Berry (Mittel)": "Bullseye-Berry_Cyber.png", "Bullseye-Berry (Schwer)": "Bullseye-Berry_Ninja.png"}
    avatar_path = berry_images.get(mode, "")
    avatar_img = pygame.image.load(avatar_path).convert_alpha() if avatar_path and os.path.exists(avatar_path) else None
    champ_img = None
    if os.path.exists("Bullseye-Berry_Champ.png"):
        try: champ_img = pygame.transform.smoothscale(pygame.image.load("Bullseye-Berry_Champ.png").convert_alpha(), (350, 350))
        except: pass

    sound_single = pygame.mixer.Sound("sounds/hit_single.wav") if os.path.exists("sounds/hit_single.wav") else None
    sound_double = pygame.mixer.Sound("sounds/hit_double.wav") if os.path.exists("sounds/hit_double.wav") else None
    sound_triple = pygame.mixer.Sound("sounds/hit_triple.wav") if os.path.exists("sounds/hit_triple.wav") else None
    sound_switch = pygame.mixer.Sound("sounds/switch_player.wav") if os.path.exists("sounds/switch_player.wav") else None
    sound_champ = pygame.mixer.Sound("sounds/champ.wav") if os.path.exists("sounds/champ.wav") else None

    title_font = pygame.font.SysFont("arial", 28, bold=True)
    big_font = pygame.font.SysFont("arial", 28, bold=True)
    giant_font = pygame.font.SysFont("arial", 90, bold=True)
    WHITE, HIGHLIGHT, RED_COL = (255, 255, 255), (255, 215, 0), (180, 30, 30)

    player_scores, player_marks = [0] * total_players, [{t: 0 for t in TARGETS} for _ in range(total_players)]
    darts_thrown, active_player = 0, 1
    round_num, round_points = 1, 0
    champ_display_until = 0
    combo_press_start = 0

    def sync_hw_display(update_player_idx=None):
        try:
            if update_player_idx is None:
                for p in range(total_players):
                    display.set_score(p, max(0, player_scores[p]))
                    for t in TARGETS:
                        if hasattr(display, 'set_cricket_marks'):
                            display.set_cricket_marks(p, t, player_marks[p][t])
            else:
                display.set_score(update_player_idx, max(0, player_scores[update_player_idx]))
                for t in TARGETS:
                    if hasattr(display, 'set_cricket_marks'):
                        display.set_cricket_marks(update_player_idx, t, player_marks[update_player_idx][t])
            display.set_active_player(active_player - 1)
            display.set_dart_arrows(3 - darts_thrown)
            display.set_temp_score(round_points)
            display.set_turn(round_num)
            display.update()
        except:
            pass

    sync_hw_display()

    running, clock, current_state, bot_timer = True, pygame.time.Clock(), "GAME", 0

    def check_win():
        for i in range(total_players):
            if all(player_marks[i][t] >= 3 for t in TARGETS) and all(player_scores[i] >= player_scores[j] for j in range(total_players)): return True
        return False

    while running:
        raw_data = None
        if ser and ser.in_waiting > 0:
            try: raw_data = ser.readline().decode('utf-8','ignore').strip()
            except: pass
            
        for e in pygame.event.get():
            if e.type in [pygame.KEYDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer(): raw_data = None; continue
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_i: raw_data = "IR:DETECT"
                elif e.key == pygame.K_r: raw_data = "BTN:RED"
                elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif e.key == pygame.K_g: raw_data = "BTN:GREY"
                elif e.key == pygame.K_0: raw_data = "HIT:WIN_CHEAaT"
                elif e.key == pygame.K_SPACE: raw_data = "BTN:START"

        if raw_data and screensaver.reset_timer(): raw_data = None; continue

        # Abbruch-Combo Überprüfung (Rot + Blau + Grau bzw. BTN:COMBO)
        keys = pygame.key.get_pressed()
        trigger_abort = False
        if raw_data == "BTN:COMBO":
            trigger_abort = True
        elif keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
            if combo_press_start == 0:
                combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 2000:
                trigger_abort = True
        else:
            combo_press_start = 0

        if trigger_abort:
            confirming = True
            if ser:
                try: ser.reset_input_buffer()
                except: pass
            while confirming:
                if bg_img: screen.blit(bg_img, (0, 0))
                else: screen.fill((0, 0, 0))
                screen.blit(big_font.render("SPIEL ABBRECHEN?", True, RED_COL), (330, 180))
                screen.blit(title_font.render("Spiel abbrechen mit Taste Spielerwechsel", True, WHITE), (240, 280))
                screen.blit(title_font.render("Weiterspielen mit Taste Start", True, HIGHLIGHT), (310, 340))
                pygame.display.flip()
                cancel_action = None
                for ev in pygame.event.get():
                    if ev.type == pygame.KEYDOWN:
                        if ev.key in [pygame.K_p, pygame.K_ESCAPE]: cancel_action = "YES"
                        elif ev.key in [pygame.K_SPACE, pygame.K_RETURN]: cancel_action = "NO"
                if ser and ser.in_waiting > 0:
                    try:
                        s_in = ser.readline().decode('utf-8','ignore').strip()
                        if s_in == "BTN:PLAYER": cancel_action = "YES"
                        elif s_in == "BTN:START": cancel_action = "NO"
                    except: pass
                if cancel_action == "YES": return
                elif cancel_action == "NO":
                    confirming = False
                    combo_press_start = 0
            raw_data = None

        is_berrys_turn = (is_berry_game and active_player == total_players)
        if is_berrys_turn and raw_data in ["BTN:PLAYER", "IR:DETECT"]: raw_data = None

        if is_berrys_turn and current_state == "GAME" and raw_data is None:
            if darts_thrown < 3:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800)
                elif pygame.time.get_ticks() > bot_timer:
                    diff = 1 if "Leicht" in mode else (3 if "Schwer" in mode else 2)
                    raw_data = f"HIT:{get_bot_hit(player_marks[total_players-1], player_marks[0], diff)}"
                    bot_timer = 0
            else:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + 1500
                elif pygame.time.get_ticks() > bot_timer:
                    darts_thrown = 0
                    round_points = 0
                    if active_player == total_players: round_num += 1
                    active_player = (active_player % total_players) + 1
                    if sound_switch is not None: sound_switch.play()
                    sync_hw_display(active_player - 1)
                    bot_timer = 0
        elif not is_berrys_turn: bot_timer = 0

        if raw_data:
            if current_state == "GAME":
                if raw_data in ["BTN:PLAYER", "IR:DETECT"]:
                    if sound_switch is not None: sound_switch.play()
                    darts_thrown = 0
                    round_points = 0
                    if active_player == total_players: round_num += 1
                    active_player = (active_player % total_players) + 1
                    sync_hw_display(active_player - 1)
                
                elif (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
                    hit_seg = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                    
                    is_special_hit = hit_seg in ["t16", "t17", "t18", "t19", "t20", "b", "db"]
                    if is_special_hit:
                        champ_display_until = pygame.time.get_ticks() + 2000
                        if sound_champ is not None: sound_champ.play()
                    elif hit_seg != "-" and hit_seg != "MISS":
                        if hit_seg.startswith("t") and sound_triple is not None: sound_triple.play()
                        elif (hit_seg.startswith("d") or hit_seg == "db") and sound_double is not None: sound_double.play()
                        elif sound_single is not None: sound_single.play()
                    elif hit_seg == "MISS" and sound_single is not None:
                        sound_single.play()

                    p_idx = active_player - 1
                    val, marks = parse_hit(hit_seg) if hit_seg != "MISS" else (0, 0)
                    if val in TARGETS:
                        for _ in range(marks):
                            if player_marks[p_idx][val] < 3: player_marks[p_idx][val] += 1
                            elif not all(player_marks[i][val] >= 3 for i in range(total_players)):
                                player_scores[p_idx] += val
                                round_points += val
                    darts_thrown += 1
                    sync_hw_display(p_idx)
                    if check_win(): current_state = "WIN"
            elif current_state == "WIN" and raw_data == "BTN:START": running = False

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font)
            pygame.display.flip()
            clock.tick(30)
            continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        if current_state == "GAME":
            screen.blit(title_font.render(f"SPIEL: {game_name}  |  Runde {round_num}", True, HIGHLIGHT), (40, 20))
            p_name = mode if is_berrys_turn else f"Spieler {active_player}"
            screen.blit(big_font.render(f"AM ZUG: {p_name} | Score: {player_scores[active_player-1]}", True, RED_COL if is_berrys_turn else WHITE), (40, 55))
            
            col_width = 100
            start_x = 140
            start_y = 110

            for j, target in enumerate(TARGETS):
                t_label = "BULL" if target == 25 else str(target)
                lbl_surf = big_font.render(t_label, True, HIGHLIGHT)
                screen.blit(lbl_surf, (start_x + j * col_width + (col_width - lbl_surf.get_width()) // 2, start_y))

            row_height = 45
            for p in range(total_players):
                row_y = start_y + 40 + p * row_height
                p_n = f"P{p+1}" if not (is_berry_game and p == total_players-1) else "Berry"
                c = HIGHLIGHT if p == (active_player - 1) else WHITE
                name_surf = big_font.render(p_n, True, c)
                screen.blit(name_surf, (40, row_y))

                for j, target in enumerate(TARGETS):
                    marks = player_marks[p][target]
                    m_surf = big_font.render(f"{marks}/3", True, (50, 255, 50) if marks == 3 else WHITE)
                    screen.blit(m_surf, (start_x + j * col_width + (col_width - m_surf.get_width()) // 2, row_y))

            if darts_thrown >= 3 and not is_berrys_turn:
                block_hint = title_font.render("Bitte Pfeile ziehen und Spielerwechsel drücken!", True, RED_COL)
                screen.blit(block_hint, ((screen.get_width() - block_hint.get_width())//2, screen.get_height() - 75))
            
            screen.blit(big_font.render(f"Pfeile geworfen: {darts_thrown} / 3", True, (150, 150, 150)), (40, screen.get_height() - 50))

            if pygame.time.get_ticks() < champ_display_until and champ_img is not None:
                screen.blit(champ_img, ((screen.get_width() - 350) // 2, (screen.get_height() - 350) // 2))
                screen.blit(giant_font.render("BOOM!", True, HIGHLIGHT), ((screen.get_width() - 200) // 2, (screen.get_height() // 2 + 150)))
            elif is_berrys_turn and avatar_img:
                anim_size = int(150 + math.sin(pygame.time.get_ticks() * 0.005) * 10) 
                screen.blit(pygame.transform.smoothscale(avatar_img, (anim_size, anim_size)), (880, 200))
        elif current_state == "WIN":
            screen.blit(giant_font.render("GEWONNEN!", True, (50, 255, 50)), (250, 250))
            
        pygame.display.flip(); clock.tick(30)
