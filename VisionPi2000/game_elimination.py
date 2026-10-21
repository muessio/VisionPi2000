import pygame
import math
import os
import random

VERSION = "1.0.0"
GAMES = ["301 Elimination"]
OPTIONS = ["Standard", "Schnell"]

def parse_hit(hit_str):
    if hit_str == "-": return 0
    if hit_str == "b": return 25   
    if hit_str == "db": return 50  
    if hit_str.startswith("d"): return int(hit_str[1:]) * 2
    if hit_str.startswith("t"): return int(hit_str[1:]) * 3
    return int(hit_str)

def get_bot_hit(score, target, diff):
    rem = target - score
    if rem <= 0: return "-"
    hit_chance = {1: 0.25, 2: 0.60, 3: 0.90}[diff]
    if random.random() < hit_chance:
        if rem <= 20: return str(rem)
        elif rem <= 40 and rem % 2 == 0: return f"d{rem//2}"
        else: return "20"
    else: return str(random.randint(1, 15)) if rem > 20 else "-"

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

    title_font, big_font, giant_font = pygame.font.SysFont("arial", 28, bold=True), pygame.font.SysFont("arial", 38, bold=True), pygame.font.SysFont("arial", 180, bold=True)
    WHITE, HIGHLIGHT, RED_COL = (255, 255, 255), (255, 215, 0), (180, 30, 30)

    target_score = 301
    player_scores, darts_thrown, active_player, round_start_score = [0] * players, 0, 1, 0
    for i in range(players): update_score_display(i, player_scores[i])

    running, clock, current_state, bot_timer, combo_press_start = True, pygame.time.Clock(), "GAME", 0, 0

    while running:
        raw_data = ser.readline().decode('utf-8','ignore').strip() if ser and ser.in_waiting > 0 else None
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key in [pygame.K_SPACE, pygame.K_ESCAPE]: raw_data = "BTN:START"
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_1: raw_data = "HIT:t20"
                elif e.key == pygame.K_0: raw_data = "HIT:WIN_CHEAT" 
                elif e.key == pygame.K_r: raw_data = "BTN:RED"
                elif e.key == pygame.K_b: raw_data = "BTN:BLUE"
                elif e.key == pygame.K_g: raw_data = "BTN:GREY"

        keys = pygame.key.get_pressed()
        is_combo_keys = keys[pygame.K_r] and keys[pygame.K_b] and keys[pygame.K_g]
        is_combo_serial = raw_data == "BTN:COMBO"

        trigger_abort = False
        
        # Combo-Check für Abbruch (3 Sekunden halten)
        if is_combo_serial:
            trigger_abort = True
        elif is_combo_keys:
            if combo_press_start == 0: combo_press_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - combo_press_start >= 3000:
                trigger_abort = True
        else: 
            combo_press_start = 0

        if trigger_abort:
            confirming = True
            if ser:
                try: ser.reset_input_buffer()
                except: pass
                
            while confirming:
                screen.fill((20, 20, 25))
                screen.blit(big_font.render("SPIEL ABBRECHEN?", True, RED_COL), (330, 180))
                screen.blit(title_font.render("Spiel abbrechen mit Taste Spielerwechsel", True, WHITE), (240, 280))
                screen.blit(title_font.render("Weiterspielen mit Taste Start", True, HIGHLIGHT), (310, 340))
                pygame.display.flip()
                
                cancel_action = None
                for ev in pygame.event.get():
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_p: cancel_action = "YES" # Spielerwechsel zum Abbrechen
                        elif ev.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]: cancel_action = "NO"
                if ser and ser.in_waiting > 0:
                    s_in = ser.readline().decode('utf-8','ignore').strip()
                    if s_in == "BTN:PLAYER": cancel_action = "YES" # Spielerwechsel zum Abbrechen
                    elif s_in == "BTN:START": cancel_action = "NO" # Start zum Weiterspielen
                    
                if cancel_action == "YES": return 
                elif cancel_action == "NO": confirming = False; combo_press_start = 0
                
            raw_data = None # Verhindert, dass der Druck noch etwas anderes auslöst

        is_berrys_turn = (active_player == 2 and "Bullseye-Berry" in mode)
        if is_berrys_turn and current_state == "GAME" and raw_data is None:
            if bot_timer == 0: bot_timer = pygame.time.get_ticks() + random.randint(1200, 1800)
            elif pygame.time.get_ticks() > bot_timer:
                diff = 1 if "Leicht" in mode else (3 if "Schwer" in mode else 2)
                raw_data = f"HIT:{get_bot_hit(player_scores[1], target_score, diff)}"
                bot_timer = 0 
        elif not is_berrys_turn: bot_timer = 0

        if raw_data:
            if current_state == "GAME":
                # Manueller Spielerwechsel (überspringt den Rest des Zuges)
                if raw_data == "BTN:PLAYER":
                    darts_thrown = 0
                    active_player = (active_player % players) + 1
                    
                elif raw_data == "BTN:START": running = False 
                elif raw_data.startswith("HIT:"):
                    hit_segment = raw_data.split(":")[1] if raw_data != "HIT:WIN_CHEAT" else "WIN_CHEAT"
                    
                    if hit_segment != "-":
                        if hit_segment.startswith("t") and sound_triple: sound_triple.play()
                        elif (hit_segment.startswith("d") or hit_segment == "db") and sound_double: sound_double.play()
                        elif sound_single: sound_single.play()

                    points = (target_score - player_scores[active_player-1]) if hit_segment == "WIN_CHEAT" else parse_hit(hit_segment)
                    if darts_thrown == 0: round_start_score = player_scores[active_player-1]
                    
                    new_score = player_scores[active_player-1] + points
                    if new_score > target_score: 
                        player_scores[active_player-1] = round_start_score
                        darts_thrown = 3
                    else:
                        player_scores[active_player-1] = new_score
                        darts_thrown += 1
                        for p_idx in range(players):
                            if p_idx != (active_player - 1) and player_scores[p_idx] == new_score:
                                player_scores[p_idx] = 0
                                update_score_display(p_idx, 0)
                        update_score_display(active_player-1, new_score)
                        if new_score == target_score: current_state = "WIN"

                    if darts_thrown >= 3 and current_state == "GAME":
                        darts_thrown, active_player = 0, (active_player % players) + 1
            elif current_state == "WIN" and raw_data == "BTN:START": running = False

        screen.fill((20, 20, 25))
        if current_state == "GAME":
            screen.blit(title_font.render(f"SPIEL: {game_name}  |  {option} (v{VERSION})", True, HIGHLIGHT), (40, 60))
            p_name = mode if is_berrys_turn else f"Spieler {active_player}"
            screen.blit(big_font.render(f"AM ZUG: {p_name}", True, RED_COL if is_berrys_turn else WHITE), (350, 120))
            screen.blit(giant_font.render(str(player_scores[active_player-1]), True, WHITE), (350, 280))
            if is_berrys_turn and avatar_img:
                anim_size = int(220 + math.sin(pygame.time.get_ticks() * 0.005) * 15) 
                screen.blit(pygame.transform.smoothscale(avatar_img, (anim_size, anim_size)), (800, 500))
        elif current_state == "WIN":
            screen.blit(giant_font.render("GEWONNEN!", True, (50, 255, 50)), (200, 250))
            
        pygame.display.flip(); clock.tick(30)
        
