import pygame
import math
import os
import random

VERSION = "1.1.2"
GAMES = ["301", "501", "701"]
OPTIONS = ["Open In/Out", "Double In", "Double Out", "Master Out", "Double In/Out", "Double In / Master Out"]

def parse_hit(hit_str):
    if hit_str == "-": return 0
    if hit_str == "b": return 25   
    if hit_str == "db": return 50  
    if hit_str.startswith("d"): return int(hit_str[1:]) * 2
    if hit_str.startswith("t"): return int(hit_str[1:]) * 3
    return int(hit_str)

def check_double(hit_str):
    return hit_str.startswith("d") or hit_str == "db"

def check_master(hit_str):
    return hit_str.startswith("d") or hit_str.startswith("t") or hit_str in ["b", "db"]

def get_bot_hit(score, mode, option):
    diff = 1 
    if "Mittel" in mode: diff = 2
    elif "Schwer" in mode: diff = 3
    
    if "Out" in option and option != "Open In/Out":
        if score <= 40 and score % 2 == 0:
            target_double = score // 2
            hit_chance = {1: 0.10, 2: 0.35, 3: 0.80}[diff]
            if random.random() < hit_chance: return f"d{target_double}"
            else: return str(target_double) if random.random() < 0.5 else "-"
        elif score <= 40 and score % 2 != 0: return "1"

    if score <= 40 and option == "Open In/Out":
        hit_chance = {1: 0.30, 2: 0.60, 3: 0.95}[diff]
        if random.random() < hit_chance: return str(score)
        else: return "-"
        
    if diff == 1: return str(random.randint(1, 20))
    elif diff == 2:
        r = random.random()
        if r < 0.30: return "t20"
        elif r < 0.70: return "20"
        elif r < 0.85: return "t19"
        else: return str(random.choice([1, 5, 19]))
    else: 
        r = random.random()
        if r < 0.70: return "t20"
        elif r < 0.90: return "20"
        else: return "t19"

class ScreenSaver:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.timeout = 10 * 60 * 1000  # 10 Minuten
        self.last_activity = pygame.time.get_ticks()
        self.active = False
        
        self.avatars = []
        berry_files = [
            "Bullseye-Berry_Original.png",
            "Bullseye-Berry_Cyber.png",
            "Bullseye-Berry_Ninja.png",
            "Bullseye-Berry_Champ.png"
        ]
        
        for file in berry_files:
            if os.path.exists(file):
                try:
                    img = pygame.image.load(file).convert_alpha()
                    img = pygame.transform.smoothscale(img, (100, 100))
                    x = random.randint(50, width - 150)
                    y = random.randint(50, height - 150)
                    vx = random.choice([-2, 2])
                    vy = random.choice([-2, 2])
                    self.avatars.append({"img": img, "x": x, "y": y, "vx": vx, "vy": vy})
                except:
                    pass
        self.font = pygame.font.SysFont("arial", 20, bold=True)

    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active:
            self.active = False
            return True
        return False

    def check(self):
        if not self.active:
            if pygame.time.get_ticks() - self.last_activity > self.timeout:
                self.active = True
        return self.active

    def update_and_draw(self, screen):
        if not self.active: return
        screen.fill((0, 0, 0))
        for av in self.avatars:
            av["x"] += av["vx"]
            av["y"] += av["vy"]
            if av["x"] <= 0 or av["x"] >= self.width - 100: av["vx"] *= -1
            if av["y"] <= 0 or av["y"] >= self.height - 100: av["vy"] *= -1
            screen.blit(av["img"], (av["x"], av["y"]))
        hint_surf = self.font.render("STANDBY – Beliebige Taste drücken zum Fortfahren", True, (120, 120, 120))
        hint_rect = hint_surf.get_rect(center=(self.width // 2, self.height - 40))
        screen.blit(hint_surf, hint_rect)

def run_game(screen, ser, players, game_name, option, mode):
    is_berry_game = "Bullseye-Berry" in mode
    total_players = players + 1 if is_berry_game else players
    screensaver = ScreenSaver(screen.get_width(), screen.get_height())

    PLAYER_MAP = [(0, 2), (1, 2), (0, 5), (1, 5), (2, 2), (3, 2), (2, 5), (3, 5)]

    def send_to_display(chip, digit, value):
        if ser:
            try: ser.write(f"DISP:{chip}:{digit}:{value}\n".encode('utf-8'))
            except: pass

    def update_score_display(player_idx, score):
        if player_idx >= len(PLAYER_MAP): return
        chip, start_digit = PLAYER_MAP[player_idx]
        if score < 0: score = 0
        score_str = f"{score:03d}" 
        send_to_display(chip, start_digit, int(score_str[0])) 
        send_to_display(chip, start_digit-1, int(score_str[1])) 
        send_to_display(chip, start_digit-2, int(score_str[2])) 

    if ser:
        for c in range(10):
            for d in range(8):
                send_to_display(c, d, 15)

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

    champ_img = None
    if os.path.exists("Bullseye-Berry_Champ.png"):
        try: champ_img = pygame.transform.smoothscale(pygame.image.load("Bullseye-Berry_Champ.png").convert_alpha(), (350, 350))
        except: pass
        
    sound_champ = pygame.mixer.Sound("sounds/champ.wav") if os.path.exists("sounds/champ.wav") else None
    sound_single = pygame.mixer.Sound("sounds/hit_single.wav") if os.path.exists("sounds/hit_single.wav") else None
    sound_double = pygame.mixer.Sound("sounds/hit_double.wav") if os.path.exists("sounds/hit_double.wav") else None
    sound_triple = pygame.mixer.Sound("sounds/hit_triple.wav") if os.path.exists("sounds/hit_triple.wav") else None

    title_font, big_font, giant_font = pygame.font.SysFont("arial", 28, bold=True), pygame.font.SysFont("arial", 38, bold=True), pygame.font.SysFont("arial", 180, bold=True)
    HIGHLIGHT, WHITE, RED_COL = (255, 215, 0), (255, 255, 255), (180, 30, 30)

    try:
        start_score = int(game_name)
    except:
        start_score = 501

    player_scores = [start_score] * total_players
    
    # Sichere Prüfung für Double In
    has_double_in = option is not None and "Double In" in option
    player_in_checked = [not has_double_in for _ in range(total_players)]
    
    darts_thrown, active_player = 0, 1
    
    for i in range(total_players):
        update_score_display(i, player_scores[i])

    running, clock, current_state = True, pygame.time.Clock(), "GAME"
    champ_display_until, bot_timer, combo_press_start = 0, 0, 0

    while running:
        raw_data = None
        if ser:
            try:
                if ser.in_waiting > 0:
                    raw_data = ser.readline().decode('utf-8','ignore').strip()
            except:
                pass
            
        for event in pygame.event.get():
            if event.type in [pygame.KEYDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
                if screensaver.reset_timer():
                    raw_data = None
                    continue
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_ESCAPE]: 
                    pass
                elif event.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif event.key == pygame.K_1: raw_data = "HIT:t20"
                elif event.key == pygame.K_2: raw_data = "HIT:19"
                elif event.key == pygame.K_3: raw_data = "HIT:d16" 
                elif event.key == pygame.K_0: raw_data = "HIT:WIN_CHEAT" 
                elif event.key == pygame.K_r: raw_data = "BTN:RED"
                elif event.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif event.key == pygame.K_g: raw_data = "BTN:GREY"

        if raw_data and screensaver.reset_timer():
            raw_data = None
            continue

        keys = pygame.key.get_pressed()
        is_combo_keys = keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]
        is_combo_serial = (raw_data == "BTN:COMBO")

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
                    try:
                        s_in = ser.readline().decode('utf-8','ignore').strip()
                        if s_in == "BTN:PLAYER": cancel_action = "YES" 
                        elif s_in == "BTN:START": cancel_action = "NO" 
                    except:
                        pass
                    
                if cancel_action == "YES": return 
                elif cancel_action == "NO": confirming = False; combo_press_start = 0
                
            raw_data = None 

        is_berrys_turn = (is_berry_game and active_player == total_players)
        
        if is_berrys_turn and raw_data == "BTN:PLAYER":
            raw_data = None

        if is_berrys_turn and current_state == "GAME" and raw_data is None:
            if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800) 
            elif pygame.time.get_ticks() > bot_timer:
                raw_data = f"HIT:{get_bot_hit(player_scores[active_player-1], mode, option)}"
                bot_timer = 0 
        elif not is_berrys_turn: bot_timer = 0

        if raw_data:
            if current_state == "GAME":
                if raw_data == "BTN:PLAYER":
                    darts_thrown = 0
                    active_player = (active_player % total_players) + 1
                    update_score_display(active_player-1, player_scores[active_player-1])
                elif raw_data.startswith("HIT:"):
                    hit_segment = raw_data.split(":")[1] if raw_data != "HIT:WIN_CHEAT" else "WIN_CHEAT"
                    
                    if hit_segment != "-":
                        if hit_segment.startswith("t") and sound_triple: sound_triple.play()
                        elif (hit_segment.startswith("d") or hit_segment == "db") and sound_double: sound_double.play()
                        elif sound_single: sound_single.play()

                    if hit_segment in ["t18", "t19", "t20", "b", "db"]:
                        champ_display_until = pygame.time.get_ticks() + 2000
                        if sound_champ: sound_champ.play()
                    
                    p_idx = active_player - 1
                    points = player_scores[p_idx] if hit_segment == "WIN_CHEAT" else parse_hit(hit_segment)
                    is_double = check_double(hit_segment)
                    is_master = check_master(hit_segment)
                    
                    bust = False
                    
                    # Double In Logik prüfen
                    if not player_in_checked[p_idx]:
                        if hit_segment == "WIN_CHEAT":
                            player_in_checked[p_idx] = True
                        elif is_double:
                            player_in_checked[p_idx] = True
                        else:
                            points = 0  # Zählt nicht, solange kein Double getroffen wurde

                    if player_in_checked[p_idx]:
                        new_score = player_scores[p_idx] - points
                    else:
                        new_score = player_scores[p_idx]

                    if new_score < 0: 
                        bust = True
                    elif option and "Out" in option and option != "Open In/Out":
                        if new_score == 1:
                            bust = True
                        elif new_score == 0:
                            if option and "Master Out" in option:
                                if not is_master and hit_segment != "WIN_CHEAT": bust = True
                            elif option and "Double Out" in option:
                                if not is_double and hit_segment != "WIN_CHEAT": bust = True

                    if bust: 
                        darts_thrown = 3 
                    else:
                        player_scores[p_idx] = new_score
                        darts_thrown += 1
                        update_score_display(p_idx, new_score)
                        if new_score == 0: current_state = "WIN"

                    if darts_thrown >= 3 and current_state == "GAME":
                        darts_thrown, active_player = 0, (active_player % total_players) + 1
                        update_score_display(active_player-1, player_scores[active_player-1])
            elif current_state == "WIN":
                if raw_data == "BTN:START": running = False

        if screensaver.check():
            screensaver.update_and_draw(screen)
            pygame.display.flip()
            clock.tick(30)
            continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        if current_state == "GAME":
            screen.blit(title_font.render(f"SPIEL: {game_name}  |  {option}", True, HIGHLIGHT), (40, 60))
            p_name = mode if is_berrys_turn else f"Spieler {active_player}"
            screen.blit(big_font.render(f"AM ZUG: {p_name}", True, RED_COL if is_berrys_turn else WHITE), ((screen.get_width() - 300)//2, 120))
            screen.blit(giant_font.render(str(player_scores[active_player-1]), True, WHITE), ((screen.get_width() - 400)//2, 220))
            
            if has_double_in and not player_in_checked[active_player-1]:
                in_hint = font.render("DOUBLE IN ERFORDERLICH!", True, HIGHLIGHT)
                screen.blit(in_hint, ((screen.get_width() - in_hint.get_width())//2, 430))

            screen.blit(big_font.render(f"Pfeile geworfen: {darts_thrown} / 3", True, (150, 150, 150)), (350, 600))

            if is_berrys_turn and avatar_img:
                anim_size = int(220 + math.sin(pygame.time.get_ticks() * 0.005) * 15) 
                screen.blit(pygame.transform.smoothscale(avatar_img, (anim_size, anim_size)), (800, 500))

            if pygame.time.get_ticks() < champ_display_until and champ_img:
                screen.blit(champ_img, ((screen.get_width() - 350) // 2, screen.get_height() // 2 - 100))
                screen.blit(giant_font.render("BOOM!", True, HIGHLIGHT), ((screen.get_width() - 200) // 2, screen.get_height() // 2 + 180))
        elif current_state == "WIN":
            screen.blit(giant_font.render("GEWONNEN!", True, (50, 255, 50)), (200, 100))
            winner_name = mode if (is_berrys_turn) else f"Spieler {active_player}"
            screen.blit(big_font.render(f"{winner_name} beendet!", True, WHITE), (250, 350))

        pygame.display.flip(); clock.tick(30)
        
