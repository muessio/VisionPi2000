import pygame
import math
import os
import random
import time

VERSION = "1.2.1"
GAMES = ["Shanghai"]
OPTIONS = ["Standard"]
ROUNDS = [1, 2, 3, 4, 5, 6, 7]

def parse_hit_shanghai(hit_str, target):
    if hit_str in ["-", "WIN_CHEAT", "MISS"]: return (0, 0)
    is_double, is_triple = hit_str.startswith("d") or hit_str == "db", hit_str.startswith("t")
    try: val = int(hit_str.replace("d", "").replace("t", "").replace("b", "25"))
    except: return (0, 0)
    if val == target:
        if is_triple: return (target * 3, 3)
        if is_double: return (target * 2, 2)
        return (target, 1)
    return (0, 0)

def get_bot_hit(target, diff):
    if random.random() < {1: 0.35, 2: 0.65, 3: 0.90}[diff]:
        return f"t{target}" if (diff == 3 and random.random() < 0.25) else (f"d{target}" if diff >= 2 and random.random() < 0.55 else str(target))
    return str(random.choice([1, 5, 20]))

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

    def update_score_display(player_idx, score):
        display.set_score(player_idx, max(0, score))
        display.update()

    display.clear_all()

    bg_img = None
    if os.path.exists("background.png"):
        try: bg_img = pygame.transform.scale(pygame.image.load("background.png").convert(), (screen.get_width(), screen.get_height()))
        except: pass

    berry_images = {"Bullseye-Berry (Leicht)": "Bullseye-Berry_Original.png", "Bullseye-Berry (Mittel)": "Bullseye-Berry_Cyber.png", "Bullseye-Berry (Schwer)": "Bullseye-Berry_Ninja.png"}
    avatar_path = berry_images.get(mode, "")
    avatar_img = pygame.image.load(avatar_path).convert_alpha() if avatar_path and os.path.exists(avatar_path) else None

    sound_single = pygame.mixer.Sound("sounds/hit_single.wav") if os.path.exists("sounds/hit_single.wav") else None
    sound_double = pygame.mixer.Sound("sounds/hit_double.wav") if os.path.exists("sounds/hit_double.wav") else None
    sound_triple = pygame.mixer.Sound("sounds/hit_triple.wav") if os.path.exists("sounds/hit_triple.wav") else None

    title_font = pygame.font.SysFont("arial", 28, bold=True)
    big_font = pygame.font.SysFont("arial", 38, bold=True)
    giant_font = pygame.font.SysFont("arial", 90, bold=True)
    WHITE, HIGHLIGHT, RED_COL = (255, 255, 255), (255, 215, 0), (180, 30, 30)

    player_scores, player_multipliers = [0] * total_players, [{t: set() for t in ROUNDS} for _ in range(total_players)]
    darts_thrown, active_player, current_round_idx = 0, 1, 0
    for i in range(total_players): update_score_display(i, 0)

    running, clock, current_state, bot_timer, winner_name, combo_press_start = True, pygame.time.Clock(), "GAME", 0, "", 0

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
                elif e.key == pygame.K_SPACE: raw_data = "BTN:START"

        if raw_data and screensaver.reset_timer(): raw_data = None; continue

        keys = pygame.key.get_pressed()
        trigger_abort = False
        if raw_data == "BTN:COMBO": trigger_abort = True
        elif keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
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
                    except: pass
                if cancel_action == "YES": return 
                elif cancel_action == "NO": confirming = False; combo_press_start = 0
            raw_data = None 

        is_berrys_turn = (is_berry_game and active_player == total_players)
        if is_berrys_turn and raw_data in ["BTN:PLAYER", "IR:DETECT"]: raw_data = None

        # === BOT LOGIK (INKL. AUTOMATISCHEM WEITERSCHALTEN NACH 3 PFEILEN) ===
        if is_berrys_turn and current_state == "GAME" and raw_data is None:
            if darts_thrown < 3:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800)
                elif pygame.time.get_ticks() > bot_timer:
                    diff = 1 if "Leicht" in mode else (3 if "Schwer" in mode else 2)
                    raw_data = f"HIT:{get_bot_hit(ROUNDS[current_round_idx], diff)}"
                    bot_timer = 0
            else:
                if bot_timer == 0: bot_timer = pygame.time.get_ticks() + 1500
                elif pygame.time.get_ticks() > bot_timer:
                    darts_thrown = 0
                    active_player += 1
                    if active_player > total_players:
                        active_player, current_round_idx = 1, current_round_idx + 1
                        if current_round_idx >= len(ROUNDS): current_state = "WIN"
                    bot_timer = 0
        elif not is_berrys_turn: bot_timer = 0

        if raw_data:
            if current_state == "GAME":
                if raw_data in ["BTN:PLAYER", "IR:DETECT"]:
                    darts_thrown = 0
                    active_player += 1
                    if active_player > total_players:
                        active_player, current_round_idx = 1, current_round_idx + 1
                        if current_round_idx >= len(ROUNDS): current_state = "WIN"
                
                elif (raw_data.startswith("HIT:") or raw_data == "MISS:1") and darts_thrown < 3:
                    hit_seg = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                    
                    if hit_seg != "-" and hit_seg != "MISS":
                        if hit_seg.startswith("t") and sound_triple: sound_triple.play()
                        elif (hit_seg.startswith("d") or hit_seg == "db") and sound_double: sound_double.play()
                        elif sound_single: sound_single.play()
                    elif hit_seg == "MISS" and sound_single:
                        sound_single.play()

                    target = ROUNDS[current_round_idx]
                    points, mult = parse_hit_shanghai(hit_seg, target) if hit_seg != "MISS" else (0, 0)
                    p_idx = active_player - 1
                    
                    if points > 0:
                        player_scores[p_idx] += points
                        player_multipliers[p_idx][target].add(mult)
                        update_score_display(p_idx, player_scores[p_idx])
                        if player_multipliers[p_idx][target] == {1, 2, 3}:
                            current_state, winner_name = "WIN", (mode if is_berrys_turn else f"Spieler {active_player}")
                    
                    darts_thrown += 1
            elif current_state == "WIN" and raw_data == "BTN:START": running = False

        if screensaver.check():
            screensaver.update_and_draw(screen, title_font)
            pygame.display.flip()
            clock.tick(30)
            continue

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        if current_state == "GAME":
            target = ROUNDS[current_round_idx] if current_round_idx < len(ROUNDS) else ROUNDS[-1]
            screen.blit(title_font.render(f"SPIEL: {game_name}  |  Runde {min(current_round_idx+1, 7)}/7", True, HIGHLIGHT), (40, 60))
            screen.blit(giant_font.render(f"ZIEL: {target}", True, (50, 255, 50)), (200, 120))
            p_name = mode if is_berrys_turn else f"Spieler {active_player}"
            screen.blit(big_font.render(f"AM ZUG: {p_name} | Score: {player_scores[active_player-1]}", True, RED_COL if is_berrys_turn else WHITE), (200, 300))
            
            if darts_thrown >= 3 and not is_berrys_turn:
                block_hint = title_font.render("Bitte Pfeile ziehen und Spielerwechsel drücken!", True, RED_COL)
                screen.blit(block_hint, ((screen.get_width() - block_hint.get_width())//2, 540))
            
            screen.blit(big_font.render(f"Pfeile geworfen: {darts_thrown} / 3", True, (150, 150, 150)), (350, 600))

            y_base = 660
            for i in range(total_players):
                p_n = "Berry" if (is_berry_game and i == total_players - 1) else f"P{i+1}"
                c = HIGHLIGHT if i == (active_player - 1) else WHITE
                surf = title_font.render(f"{p_n}: {player_scores[i]}", True, c)
                row, col = i % 2, i // 2
                items_in_row = (total_players + 1) // 2 if row == 0 else total_players // 2
                spacing = screen.get_width() // (items_in_row + 1)
                screen.blit(surf, ((col + 1) * spacing - surf.get_width() // 2, y_base + (row * 40)))

            if is_berrys_turn and avatar_img:
                anim_size = int(220 + math.sin(pygame.time.get_ticks() * 0.005) * 15) 
                screen.blit(pygame.transform.smoothscale(avatar_img, (anim_size, anim_size)), (800, 500))
        elif current_state == "WIN":
            screen.blit(giant_font.render(f"{winner_name} GEWINNT!" if winner_name else "SPIELENDE!", True, (50, 255, 50)), (150, 250))
            
        pygame.display.flip(); clock.tick(30)
