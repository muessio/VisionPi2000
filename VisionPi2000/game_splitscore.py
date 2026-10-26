import pygame
import os
import json
import time

VERSION = "1.3.0"
GAMES = ["Split Score"]
OPTIONS = ["Standard"]

def trigger_victory(ser):
    if os.path.exists("sounds/victory.wav"):
        try: pygame.mixer.Sound("sounds/victory.wav").play()
        except: pass
    if ser:
        try:
            for _ in range(6):
                ser.write(b"TEST:ON\n"); ser.flush(); time.sleep(0.25)
                ser.write(b"TEST:OFF\n"); ser.flush(); time.sleep(0.25)
            ser.write(b"CLEAR\n"); ser.flush()
        except: pass

def run_game(screen, ser, display, players_count, game_name, option_name, mode_name):
    clock = pygame.time.Clock()
    sw, sh = screen.get_width(), screen.get_height()
    font = pygame.font.SysFont("arial", int(sh * 0.04), bold=True)
    
    is_16_9 = False
    try:
        with open("settings.json", "r") as f: is_16_9 = json.load(f).get("format", "4:3") == "16:9"
    except: pass
    bg_file = "background_16_9.png" if is_16_9 else "background.png"
    bg_img = pygame.transform.scale(pygame.image.load(bg_file).convert(), (sw, sh)) if os.path.exists(bg_file) else None

    scores = [40] * players_count
    targets = [15, 16, "D", 17, 18, "T", 19, 20, "B"]
    current_player = 0
    current_round = 0
    darts_thrown = 0
    round_points = 0
    switch_delay_timer = 0
    running = True

    if ser:
        try:
            ser.write(b"LAMP:PLAYER:1\n")
            ser.write(b"LAMP:START:0\n")
            ser.flush()
        except: pass

    def update_hardware():
        display.clear_all()
        display.set_active_player(current_player)
        for i in range(8): display.set_score(i, scores[i] if i < players_count else None)
        tgt = targets[current_round] if current_round < len(targets) else 0
        if isinstance(tgt, int): display.set_temp_score(tgt)
        else: display.set_temp_score(0) 
        display.set_dart_arrows(darts_thrown)
        display.update()

    update_hardware()

    while running:
        raw_data = ser.readline().decode('utf-8', 'ignore').strip() if ser and ser.in_waiting > 0 else None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE): running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif ev.key == pygame.K_i: raw_data = "IR:DETECT"
                
        if raw_data == "BTN:PLAYER":
            switch_delay_timer = pygame.time.get_ticks()
            raw_data = None
        elif raw_data == "IR:DETECT":
            if darts_thrown >= 3 and switch_delay_timer == 0:
                switch_delay_timer = pygame.time.get_ticks() + 1000
            raw_data = None
            
        if switch_delay_timer > 0 and pygame.time.get_ticks() >= switch_delay_timer:
            switch_delay_timer = 0
            current_player = (current_player + 1) % players_count
            if current_player == 0: current_round += 1
            darts_thrown = 0
            round_points = 0
            if current_round >= len(targets):
                update_hardware()
                trigger_victory(ser)
                running = False
                continue
            if ser:
                try: ser.write(b"LAMP:PLAYER:1\n"); ser.flush()
                except: pass
            update_hardware()

        if raw_data and raw_data.startswith("HIT:") and darts_thrown < 3:
            scores[current_player] += 15 
            round_points += 15
            darts_thrown += 1
            if darts_thrown == 3 and ser:
                try: ser.write(b"LAMP:PLAYER:2\n"); ser.flush()
                except: pass
            update_hardware()

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))
        
        target_str = str(targets[current_round]) if current_round < len(targets) else "Ende"
        screen.blit(font.render(f"Spiel: Split Score | Ziel: {target_str}", True, (255,215,0)), (int(sw*0.05), int(sh*0.05)))
        screen.blit(font.render(f"Spieler {current_player+1} ist am Zug (+{round_points})", True, (255,255,255)), (int(sw*0.05), int(sh*0.15)))
        screen.blit(font.render(f"Pfeile geworfen: {darts_thrown}/3", True, (255,255,255)), (int(sw*0.05), int(sh*0.25)))
        
        y_pos = int(sh * 0.85)
        for i in range(players_count):
            c = (255,215,0) if i == current_player else (255,255,255)
            screen.blit(font.render(f"P{i+1}: {scores[i]}", True, c), (int(sw * (0.05 + (i%4)*0.2)), y_pos if i < 4 else y_pos + int(sh*0.06)))

        pygame.display.flip(); clock.tick(30)
        
