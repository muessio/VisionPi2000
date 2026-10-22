import pygame
import math
import os
import random

VERSION = "1.1.2"
GAMES = ["Split Score"]
OPTIONS = ["Standard"]
ROUNDS = ["15", "16", "Double", "17", "18", "Triple", "19", "20", "Bull"]

def check_hit_valid(hit_str, target):
    if hit_str in ["-", "WIN_CHEAT"]: return 0
    is_double, is_triple = hit_str.startswith("d") or hit_str == "db", hit_str.startswith("t")
    val = int(hit_str.replace("d", "").replace("t", "").replace("b", "25"))
    if target == "Double" and is_double: return val * 2
    if target == "Triple" and is_triple: return val * 3
    if target == "Bull" and val == 25: return 50 if is_double else 25
    if target in ["15", "16", "17", "18", "19", "20"] and val == int(target):
        return val * (3 if is_triple else (2 if is_double else 1))
    return 0

def get_bot_hit(target, diff):
    if random.random() < {1: 0.35, 2: 0.65, 3: 0.90}[diff]:
        if target == "Double": return f"d{random.randint(1,20)}"
        elif target == "Triple": return f"t{random.randint(1,20)}"
        elif target == "Bull": return "b"
        else: return target
    return str(random.randint(1, 14))

class ScreenSaver:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.timeout = 10 * 60 * 1000
        self.last_activity = pygame.time.get_ticks()
        self.active = False
        self.avatars = []
        for file in ["Bullseye-Berry_Original.png", "Bullseye-Berry_Cyber.png", "Bullseye-Berry_Ninja.png", "Bullseye-Berry_Champ.png"]:
            if os.path.exists(file):
                try:
                    img = pygame.transform.smoothscale(pygame.image.load(file).convert_alpha(), (100, 100))
                    self.avatars.append({"img": img, "x": random.randint(50, width - 150), "y": random.randint(50, height - 150), "vx": random.choice([-2, 2]), "vy": random.choice([-2, 2])})
                except: pass

    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active:
            self.active = False
            return True
        return False

    def check(self):
        if not self.active and pygame.time.get_ticks() - self.last_activity > self.timeout:
            self.active = True
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

def run_game(screen, ser, players, game_name, option, mode):
    is_berry_game = "Bullseye-Berry" in mode
    total_players = players + 1 if is_berry_game else players
    screensaver = ScreenSaver(screen.get_width(), screen.get_height())

    PLAYER_MAP = [(0, 2), (1, 2), (0, 5), (1, 5), (2, 2), (3, 2), (2, 5), (3, 5)]

    def update_score_display(player_idx, score):
        if ser and player_idx < len(PLAYER_MAP):
            chip, start_digit = PLAYER_MAP[player_idx]
            score_str = f"{max(0, score):03d}" 
            ser.write(f"DISP:{chip}:{start_digit}:{score_str[0]}\nDISP:{chip}:{start_digit-1}:{score_str[1]}\nDISP:{chip}:{start_digit-2}:{score_str[2]}\n".encode('utf-8'))

    if ser:
        for c in range(10):
            for d in range(8):
                ser.write(f"DISP:{c}:{d}:15\n".encode('utf-8'))

    bg_img = None
    bg_path = os.path.join(os.getcwd(), "background.png")
    if os.path.exists(bg_path):
        try: bg_img = pygame.transform.scale(pygame.image.load(bg_path).convert(), (screen.get_width(), screen.get_height()))
        except: pass

    berry_images = {
        "Bullseye-Berry (Leicht)": "Bullseye-Berry_Original.png",
        "Bullseye-Berry (Mittel)": "Bullseye-Berry_Cyber.png",
        "Bullseye-Berry (Schwer)": "Bullseye-Berry_Ninja.png"
    }
    avatar_path = berry_images.get(mode, "")
    avatar_img = pygame.image.load(avatar_path).convert_alpha() if avatar_path and os.path.exists(avatar_path) else None

    sound_single = pygame.mixer.Sound("sounds/hit_single.wav") if os.path.exists("sounds/hit_single.wav") else None
    sound_double = pygame.mixer.Sound("sounds/hit_double.wav") if os.path.exists("sounds/hit_double.wav") else None
    sound_triple = pygame.mixer.Sound("sounds/hit_triple.wav") if os.path.exists("sounds/hit_triple.wav") else None

    title_font = pygame.font.SysFont("arial", 28, bold=True)
    big_font = pygame.font.SysFont("arial", 38, bold=True)
    giant_font = pygame.font.SysFont("arial", 120, bold=True)
    WHITE, HIGHLIGHT, RED_COL = (255, 255, 255), (255, 215, 0), (180, 30, 30)

    player_scores, darts_thrown, active_player, current_round_idx, hits_this_round = [40] * total_players, 0, 1, 0, 0
    for i in range(total_players): update_score_display(i, player_scores[i])

    running, clock, current_state, bot_timer, combo_press_start = True, pygame.time.Clock(), "GAME", 0, 0

    while running:
        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
        for e in pygame.event.get():
            if e.type in [pygame.KEYDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer():
                    raw_data = None
                    continue
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_SPACE, pygame.K_ESCAPE]: pass
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_r: raw_data = "BTN:RED"
                elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif e.key == pygame.K_g: raw_data = "BTN:GREY"

        if raw_data and screensaver.reset_timer():
            raw_data = None
            continue

        keys = pygame.key.get_pressed()
        is_combo_keys = keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]
        is_combo_serial = raw_data == "BTN:COMBO"

        trigger_abort = False
        if is_combo_serial: trigger_abort = True
        elif is_combo_keys:
            if combo_press_start == 0: combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 2000: trigger_abort = True
        else: combo_press_start = 0

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
                    s_in = ser.readline().decode('utf-8','ignore').strip()
                    if s_in == "BTN:PLAYER": cancel_action = "YES" 
                    elif s_in == "BTN:START": cancel_action = "NO" 
                    
                if cancel_action == "YES": return 
                elif cancel_action == "NO": confirming = False; combo_press_start = 0
                
            raw_data = None 

        is_berrys_turn = (is_berry_game and active_player == total_players)
        if is_berrys_turn and raw_data == "BTN:PLAYER": raw_data = None

        if is_berrys_turn and current_state == "GAME" and raw_data is None:
            if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800)
            elif pygame.time.get_ticks() > bot_timer:
                diff = 1 if "Leicht" in mode else (3 if "Schwer" in mode else 2)
                raw_data = f"HIT:{get_bot_hit(ROUNDS[current_round_idx], diff)}"
                bot_timer = 0
        elif not is_berrys_turn: bot_timer = 0

        if raw_data:
            if current_state == "GAME":
                if raw_data == "BTN:PLAYER":
                    if hits_this_round == 0:
                        player_scores[active_player-1] //= 2
                        update_score_display(active_player-1, player_scores[active_player-1])
                    darts_thrown, hits_this_round = 0, 0
                    active_player += 1
                    if active_player > total_players:
                        active_player, current_round_idx = 1, current_round_idx + 1
                        if current_round_idx >= len(ROUNDS): current_state = "WIN"
                elif raw_data.startswith("HIT:"):
                    hit_seg = raw_data.split(":")[1]
                    if hit_seg != "-":
                        if hit_seg.startswith("t") and sound_triple: sound_triple.play()
                        elif (hit_seg.startswith("d") or hit_seg == "db") and sound_double: sound_double.play()
                        elif sound_single: sound_single.play()

                    pts = check_hit_valid(hit_seg, ROUNDS[current_round_idx])
                    hits_this_round += pts
                    player_scores[active_player-1] += pts
                    darts_thrown += 1
                    update_score_display(active_player-1, player_scores[active_player-1])

                    if darts_thrown >= 3:
                        if hits_this_round == 0:
                            player_scores[active_player-1] //= 2
                            update_score_display(active_player-1, player_scores[active_player-1])
                        darts_thrown, hits_this_round = 0, 0
                        active_player += 1
                        if active_player > total_players:
                            active_player, current_round_idx = 1, current_round_idx + 1
                            if current_round_idx >= len(ROUNDS): current_state = "WIN"
            elif current_state == "WIN" and raw_data == "BTN:START": running = False

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font)
            pygame.display.flip()
            clock.tick(30)
            continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        if current_state == "GAME":
            screen.blit(title_font.render(f"SPIEL: {game_name}  |  Runde {current_round_idx+1}/9", True, HIGHLIGHT), (40, 60))
            screen.blit(giant_font.render(f"ZIEL: {ROUNDS[current_round_idx]}", True, (50, 255, 50)), (250, 120))
            p_name = mode if is_berrys_turn else f"Spieler {active_player}"
            screen.blit(big_font.render(f"AM ZUG: {p_name} | Score: {player_scores[active_player-1]}", True, RED_COL if is_berrys_turn else WHITE), (200, 350))
            
            # HIER DIE PFEIL-ANZEIGE FÜR SPLITSCORE
            screen.blit(big_font.render(f"Pfeile geworfen: {darts_thrown} / 3", True, (150, 150, 150)), (350, 600))

            if is_berrys_turn and avatar_img:
                anim_size = int(220 + math.sin(pygame.time.get_ticks() * 0.005) * 15) 
                screen.blit(pygame.transform.smoothscale(avatar_img, (anim_size, anim_size)), (800, 500))
        elif current_state == "WIN":
            screen.blit(giant_font.render("SPIELENDE!", True, (50, 255, 50)), (250, 250))
            
        pygame.display.flip(); clock.tick(30)
        
