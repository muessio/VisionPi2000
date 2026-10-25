import pygame
import math
import os
import random

VERSION = "1.3.8"
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
    def reset_timer(self):
        self.last_activity = pygame.time.get_ticks()
        if self.active: self.active = False; return True
        return False
    def check(self):
        if not self.active and pygame.time.get_ticks() - self.last_activity > self.timeout: self.active = True
        return self.active
    def update_and_draw(self, screen, font):
        pass

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
        except: pass

    title_font = pygame.font.SysFont("arial", 28, bold=True)
    big_font = pygame.font.SysFont("arial", 22, bold=True)
    giant_font = pygame.font.SysFont("arial", 90, bold=True)
    WHITE, HIGHLIGHT, RED_COL = (255, 255, 255), (255, 215, 0), (180, 30, 30)

    player_scores, player_marks = [0] * total_players, [{t: 0 for t in TARGETS} for _ in range(total_players)]
    darts_thrown, active_player = 0, 1
    round_num, round_points = 1, 0

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

    running, clock = True, pygame.time.Clock()

    while running:
        raw_data = None
        if ser and ser.in_waiting > 0:
            try: raw_data = ser.readline().decode('utf-8','ignore').strip()
            except: pass
            
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE: return
                elif e.key == pygame.K_p: raw_data = "BTN:PLAYER"
                elif e.key == pygame.K_SPACE: raw_data = "BTN:START"

        if raw_data:
            if raw_data in ["BTN:PLAYER", "IR:DETECT"]:
                darts_thrown = 0
                round_points = 0
                active_player = (active_player % total_players) + 1
                sync_hw_display(active_player - 1)
            elif raw_data.startswith("HIT:") or raw_data == "MISS:1":
                hit_seg = raw_data.split(":")[1] if raw_data.startswith("HIT:") else "MISS"
                p_idx = active_player - 1
                val, marks = parse_hit(hit_seg) if hit_seg != "MISS" else (0, 0)
                if val in TARGETS:
                    for _ in range(marks):
                        if player_marks[p_idx][val] < 3: player_marks[p_idx][val] += 1
                darts_thrown += 1
                sync_hw_display(p_idx)

        if bg_img: screen.blit(bg_img, (0, 0))
        else: screen.fill((0, 0, 0))

        screen.blit(title_font.render(f"SPIEL: Cricket | Runde {round_num}", True, HIGHLIGHT), (40, 20))
        screen.blit(big_font.render(f"AM ZUG: Spieler {active_player} | Score: {player_scores[active_player-1]}", True, WHITE), (40, 55))
        
        col_width = 85
        start_x = 160
        start_y = 100

        for j, target in enumerate(TARGETS):
            t_label = "BULL" if target == 25 else str(target)
            screen.blit(big_font.render(t_label, True, HIGHLIGHT), (start_x + j * col_width, start_y))

        row_height = 34
        for p in range(total_players):
            row_y = start_y + 35 + p * row_height
            screen.blit(big_font.render(f"P{p+1}", True, HIGHLIGHT if p == (active_player - 1) else WHITE), (40, row_y))

            for j, target in enumerate(TARGETS):
                marks = player_marks[p][target]
                screen.blit(big_font.render(f"{marks}/3", True, WHITE), (start_x + j * col_width, row_y))

        screen.blit(big_font.render(f"Pfeile geworfen: {darts_thrown} / 3", True, (150, 150, 150)), (40, screen.get_height() - 50))

        pygame.display.flip()
        clock.tick(30)
