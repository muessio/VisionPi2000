import pygame
import math
import os
import random

VERSION = "1.0.0"
GAMES = ["Around the Clock"]
OPTIONS = ["Standard", "Mit Bull"]
TARGETS = list(range(1, 21)) + [25]

def parse_hit_clock(hit_str, current_target):
    if hit_str in ["-", "WIN_CHEAT"]: return 0
    try: val = int(hit_str.replace("d", "").replace("t", "").replace("b", "25"))
    except: return 0
    return 1 if val == current_target else 0

def get_bot_hit(current_target, diff):
    if random.random() < {1: 0.40, 2: 0.70, 3: 0.95}[diff]:
        return str(current_target if current_target != 25 else "b")
    return str(random.choice([1, 5, 20]))

def run_game(screen, ser, players, game_name, option, mode):
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

    berry_images = {
        "Bullseye-Berry (Leicht)": "Bullseye-Berry_Original.png",
        "Bullseye-Berry (Mittel)": "Bullseye-Berry_Cyber.png",
        "Bullseye-Berry (Schwer)": "Bullseye-Berry_Ninja.png"
    }
    avatar_img = pygame.image.load(berry_images[mode]).convert_alpha() if mode in berry_images and os.path.exists(berry_images[mode]) else None

    sound_single = pygame.mixer.Sound("sounds/hit_single.wav") if os.path.exists("sounds/hit_single.wav") else None
    sound_double = pygame.mixer.Sound("sounds/hit_double.wav") if os.path.exists("sounds/hit_double.wav") else None
    sound_triple = pygame.mixer.Sound("sounds/hit_triple.wav") if os.path.exists("sounds/hit_triple.wav") else None

    title_font, big_font, giant_font = pygame.font.SysFont("arial", 28, bold=True), pygame.font.SysFont("arial", 38, bold=True), pygame.font.SysFont("arial", 120, bold=True)
    WHITE, HIGHLIGHT, RED_COL = (255, 255, 255), (255, 215, 0), (180, 30, 30)

    active_targets = TARGETS if option == "Mit Bull" else TARGETS[:-1]
    player_target_indices, darts_thrown, active_player = [0] * players, 0, 1
    for i in range(players): update_score_display(i, active_targets[0])

    running, clock, current_state, bot_timer, winner_name, combo_press_start = True, pygame.time.Clock(), "GAME", 0, "", 0

    while running:
        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_SPACE, pygame.K_ESCAPE]: raw_data = "BTN:START"
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_r: raw_data = "BTN:RED"
                elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif e.key == pygame.K_g: raw_data = "BTN:GREY"

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]:
            if combo_press_start == 0: combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 1500:
                confirming = True
                while confirming:
                    screen.fill((20, 20, 25))
                    screen.blit(big_font.render("SPIEL ABBRECHEN?", True, RED_COL), (330, 180))
                    screen.blit(title_font.render("Drücke [ START ] = Spiel beenden", True, WHITE), (210, 280))
                    screen.blit(title_font.render("Drücke [ SPIELERWECHSEL ] = Weiterspielen", True, HIGHLIGHT), (140, 340))
                    pygame.display.flip()
                    
                    cancel_action = None
                    for ev in pygame.event.get():
                        if ev.type == pygame.KEYDOWN:
                            if ev.key in [pygame.K_SPACE, pygame.K_RETURN]: cancel_action = "YES"
                            elif ev.key == pygame.K_p: cancel_action = "NO"
                    if ser and ser.in_waiting > 0:
                        s_in = ser.readline().decode('utf-8','ignore').strip()
                        if s_in == "BTN:START": cancel_action = "YES"
                        elif s_in == "BTN:PLAYER": cancel_action = "NO"
                    if cancel_action == "YES": return 
                    elif cancel_action == "NO": confirming = False; combo_press_start = 0
        else: combo_press_start = 0

        is_berrys_turn = (active_player == 2 and "Bullseye-Berry" in mode)
        if is_berrys_turn and current_state == "GAME" and raw_data is None:
            if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800)
            elif pygame.time.get_ticks() > bot_timer:
                diff = 1 if "Leicht" in mode else (3 if "Schwer" in mode else 2)
                curr_t = active_targets[player_target_indices[active_player - 1]]
                raw_data = f"HIT:{get_bot_hit(curr_t, diff)}"
                bot_timer = 0
        elif not is_berrys_turn: bot_timer = 0

        if raw_data:
            if current_state == "GAME":
                if raw_data == "BTN:START": running = False 
                elif raw_data.startswith("HIT:"):
                    hit_seg = raw_data.split(":")[1]
                    if hit_seg != "-":
                        if hit_seg.startswith("t") and sound_triple: sound_triple.play()
                        elif (hit_seg.startswith("d" ) or hit_seg == "db") and sound_double: sound_double.play()
                        elif sound_single: sound_single.play()

                    p_idx = active_player - 1
                    curr_target_val = active_targets[player_target_indices[p_idx]]
                    if parse_hit_clock(hit_seg, curr_target_val) > 0:
                        player_target_indices[p_idx] += 1
                        if player_target_indices[p_idx] >= len(active_targets):
                            current_state, winner_name = "WIN", (mode if is_berrys_turn else f"Spieler {active_player}")
                        else: update_score_display(p_idx, active_targets[player_target_indices[p_idx]])
                    
                    darts_thrown += 1
                    if darts_thrown >= 3 and current_state == "GAME":
                        darts_thrown, active_player = 0, active_player + 1
                        if active_player > players: active_player = 1
            elif current_state == "WIN" and raw_data == "BTN:START": running = False

        screen.fill((20, 20, 25))
        if current_state == "GAME":
            p_idx = active_player - 1
            curr_target_val = active_targets[player_target_indices[p_idx]]
            screen.blit(title_font.render(f"SPIEL: {game_name}  |  {option} (v{VERSION})", True, HIGHLIGHT), (40, 60))
            screen.blit(giant_font.render(f"ZIEL: {'BULL' if curr_target_val == 25 else curr_target_val}", True, (50, 255, 50)), (150, 120))
            p_name = mode if is_berrys_turn else f"Spieler {active_player}"
            screen.blit(big_font.render(f"AM ZUG: {p_name} | Fortschritt: {player_target_indices[p_idx]}/{len(active_targets)}", True, RED_COL if is_berrys_turn else WHITE), (150, 300))
            if is_berrys_turn and avatar_img:
                anim_size = int(220 + math.sin(pygame.time.get_ticks() * 0.005) * 15) 
                screen.blit(pygame.transform.smoothscale(avatar_img, (anim_size, anim_size)), (800, 500))
        elif current_state == "WIN":
            screen.blit(giant_font.render(f"{winner_name} GEWINNT!" if winner_name else "SPIELENDE!", True, (50, 255, 50)), (150, 250))
            
        pygame.display.flip(); clock.tick(30)
