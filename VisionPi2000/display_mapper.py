# Datei: display_mapper.py
import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.last_sent = [[-1 for _ in range(8)] for _ in range(9)]
        self.light_state = True

        self.FONT = {
            "0": ["A", "B", "C", "D", "E", "F"],
            "1": ["B", "C"],
            "2": ["A", "B", "D", "E", "G"],
            "3": ["A", "B", "C", "D", "G"],
            "4": ["B", "C", "F", "G"],
            "5": ["A", "C", "D", "F", "G"],
            "6": ["A", "C", "D", "E", "F", "G"],
            "7": ["A", "B", "C"],
            "8": ["A", "B", "C", "D", "E", "F", "G"],
            "9": ["A", "B", "C", "D", "F", "G"],
            " ": [],
            "-": ["G"]
        }

        # Exaktes physikalisches Spalten-Mapping der Löwen-Platine (A..H = DIG7..DIG0):
        self.COL_TO_DIGIT = {
            "A": 7, "B": 6, "C": 5, "D": 4, "E": 3, "F": 2, "G": 1, "H": 0
        }

        # Exakte Bit-Zuordnung der Zeilen 1..8 laut MAX7219-Pinout (Blatt 1 & 3):
        # 1(Pin 22)=SEGDP(Bit 7), 2(Pin 17)=SEGG(Bit 0), 3(Pin 15)=SEGF(Bit 1), 4(Pin 21)=SEGE(Bit 2),
        # 5(Pin 23)=SEGD(Bit 3),  6(Pin 20)=SEGC(Bit 4), 7(Pin 16)=SEGB(Bit 5), 8(Pin 14)=SEGA(Bit 6)
        self.ROW_TO_BIT = {
            1: 7, 2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6
        }

        # 100% verifizierte Segment-Tabellen laut Löwen-Schaltplan Blatt 3 (Zeile 1..8)
        SEG_U1    = { "A": 5, "B": 6, "C": 7, "D": 3, "E": 4, "F": 1, "G": 2, "DP": 8 }
        SEG_U2    = { "A": 5, "B": 2, "C": 1, "D": 7, "E": 4, "F": 3, "G": 6, "DP": 8 }
        SEG_U3    = { "A": 4, "B": 2, "C": 3, "D": 5, "E": 1, "F": 6, "G": 7, "DP": 8 }
        SEG_U4    = { "A": 5, "B": 1, "C": 7, "D": 8, "E": 3, "F": 4, "G": 6, "DP": 2 }
        SEG_U5_U6 = { "A": 5, "B": 1, "C": 7, "D": 3, "E": 8, "F": 4, "G": 6, "DP": 2 }
        SEG_U7    = { "A": 5, "B": 3, "C": 2, "D": 7, "E": 1, "F": 4, "G": 6, "DP": 8 }
        SEG_U8    = { "A": 5, "B": 6, "C": 2, "D": 7, "E": 4, "F": 1, "G": 8, "DP": 3 }
        SEG_U9    = { "A": 1, "B": 8, "C": 2, "D": 3, "E": 5, "F": 4, "G": 6, "DP": 7 }

        self.DISP_TABLE = {
            # U1 (Chip 0)
            1: (0, "H", SEG_U1), 2: (0, "D", SEG_U1), 3: (0, "B", SEG_U1),
            7: (0, "F", SEG_U1), 8: (0, "E", SEG_U1), 9: (0, "A", SEG_U1),
            
            # U3 (Chip 1)
            10: (1, "H", SEG_U3), 11: (1, "D", SEG_U3), 12: (1, "B", SEG_U3),
            13: (1, "E", SEG_U3), 14: (1, "A", SEG_U3),
            
            # U2 (Chip 2)
            4: (2, "F", SEG_U2), 5: (2, "A", SEG_U2), 6: (2, "C", SEG_U2), 15: (2, "G", SEG_U2),
            
            # U4 (Chip 3)
            16: (3, "D", SEG_U4), 17: (3, "A", SEG_U4), 18: (3, "E", SEG_U4),
            
            # U5 (Chip 4) & U6 (Chip 5)
            19: (4, "B", SEG_U5_U6), 20: (4, "F", SEG_U5_U6), 21: (4, "E", SEG_U5_U6),
            22: (5, "B", SEG_U5_U6), 23: (5, "F", SEG_U5_U6), 24: (5, "E", SEG_U5_U6),
            
            # U7 (Chip 6)
            25: (6, "H", SEG_U7), 26: (6, "B", SEG_U7), 27: (6, "E", SEG_U7), 30: (6, "A", SEG_U7),
            
            # U8 (Chip 7)
            31: (7, "D", SEG_U8), 32: (7, "B", SEG_U8),
            36: (7, "E", SEG_U8), 37: (7, "F", SEG_U8), 38: (7, "G", SEG_U8),
            
            # U9 (Chip 8)
            28: (8, "E", SEG_U9), 29: (8, "F", SEG_U9),
            33: (8, "C", SEG_U9), 34: (8, "D", SEG_U9), 35: (8, "B", SEG_U9),
            39: (8, "H", SEG_U9), 40: (8, "G", SEG_U9), 41: (8, "A", SEG_U9),
        }

        # Display-Zuordnung (Hunderter, Zehner, Einer) von links nach rechts
        self.PLAYER_DISP = {
            0: (1, 2, 3),     # Spieler 1: DISP1 (links), DISP2 (mitte), DISP3 (rechts)
            1: (4, 5, 6),     # Spieler 2: DISP4 (links), DISP5 (mitte), DISP6 (rechts)
            2: (7, 8, 9),     # Spieler 3: DISP7 (links), DISP8 (mitte), DISP9 (rechts)
            3: (10, 11, 12),  # Spieler 4: DISP10 (links), DISP11 (mitte), DISP12 (rechts)
            4: (30, 31, 32),  # Spieler 5: DISP30 (links), DISP31 (mitte), DISP32 (rechts)
            5: (33, 34, 35),  # Spieler 6: DISP33 (links), DISP34 (mitte), DISP35 (rechts)
            6: (36, 37, 38),  # Spieler 7: DISP36 (links), DISP37 (mitte), DISP38 (rechts)
            7: (39, 40, 41),  # Spieler 8: DISP39 (links), DISP40 (mitte), DISP41 (rechts)
        }

        # Oben rechts: 3-stelliges grünes Display (TEMP SCORE) und 2-stelliges Display (Runde/Pfeile)
        self.TEMP_SCORE_DISP = (25, 26, 27)
        self.TURN_DISP       = (28, 29)

        self.CRICKET_TARGET_DISP = {
            20: (13, 14),
            19: (15, 16),
            18: (17, 18),
            17: (19, 20),
            16: (21, 22),
            15: (23, 24),
        }

        # Grünes Bullseye-Symbol (BE1..BE7 auf U7 = Chip 6, Spalte C, Zeile 1..7 laut Blatt 3)
        self.BULLSEYE_ICON_LEDS = [
            (6, "C", 1), (6, "C", 2), (6, "C", 3), (6, "C", 4),
            (6, "C", 5), (6, "C", 6), (6, "C", 7)
        ]

        # Spieler-Lampen laut Schaltplan Blatt 3 (U1 Spalte C & U8 Spalte A)
        self.ALL_PL_LEDS = {
            1: [(0, "C", 6), (0, "C", 2)],
            2: [(0, "C", 7), (0, "C", 3)],
            3: [(0, "C", 5), (0, "C", 1)],
            4: [(0, "C", 4), (0, "C", 8)],
            5: [(7, "A", 4), (7, "A", 8)],
            6: [(7, "A", 1), (7, "A", 5)],
            7: [(7, "A", 6), (7, "A", 2)],
            8: [(7, "A", 7), (7, "A", 3)],
        }

        # 100% nach Löwen-Schaltplan Blatt 3 verifizierte Cricket-LED-Matrix (PL1..PL8, 20..15 & Bull)
        self.CRICKET_LEDS = {
            0: { # Spieler 1 (PL1)
                20: [(2, "H", 8), (2, "H", 6), (2, "H", 3)],
                19: [(2, "H", 2), (3, "H", 2), (3, "H", 1)],
                18: [(3, "F", 1), (3, "F", 2), (3, "F", 6)],
                17: [(4, "D", 5), (4, "D", 7), (4, "D", 1)],
                16: [(5, "D", 8), (5, "D", 4), (5, "D", 1)],
                15: [(5, "D", 2), (6, "F", 6), (6, "F", 2)],
                25: [(6, "D", 2), (6, "D", 6), (6, "D", 7)],
            },
            1: { # Spieler 2 (PL2)
                20: [(2, "H", 4), (2, "H", 7), (2, "H", 1)],
                19: [(2, "H", 5), (3, "H", 6), (3, "H", 4)],
                18: [(3, "F", 6), (3, "F", 3), (3, "F", 7)],
                17: [(4, "D", 6), (4, "D", 7), (4, "D", 2)],
                16: [(5, "D", 7), (5, "D", 6), (5, "D", 5)],
                15: [(5, "D", 3), (6, "F", 1), (6, "F", 5)],
                25: [(6, "D", 5), (6, "D", 1), (6, "D", 4)],
            },
            2: { # Spieler 3 (PL3)
                20: [(2, "E", 8), (2, "E", 6), (2, "E", 3)],
                19: [(2, "E", 2), (3, "H", 8), (3, "H", 3)],
                18: [(3, "B", 1), (3, "B", 8), (3, "B", 2)],
                17: [(4, "H", 5), (4, "H", 4), (4, "H", 1)],
                16: [(5, "H", 8), (5, "H", 4), (5, "H", 1)],
                15: [(5, "H", 2), (6, "F", 4), (6, "F", 7)],
                25: [(6, "G", 2), (6, "G", 6), (6, "G", 7)],
            },
            3: { # Spieler 4 (PL4)
                20: [(2, "E", 4), (2, "E", 7), (2, "E", 1)],
                19: [(2, "E", 5), (3, "F", 4), (3, "H", 7)],
                18: [(3, "B", 6), (3, "B", 3), (3, "B", 7)],
                17: [(4, "H", 6), (4, "H", 7), (4, "H", 2)],
                16: [(5, "H", 7), (5, "H", 6), (5, "H", 5)],
                15: [(5, "H", 3), (6, "F", 3), (6, "F", 8)],
                25: [(6, "G", 5), (6, "G", 1), (6, "G", 4)],
            },
            4: { # Spieler 5 (PL5)
                20: [(1, "F", 4), (1, "F", 1), (1, "F", 5)],
                19: [(3, "C", 7), (3, "C", 2), (3, "C", 8)],
                18: [(3, "C", 1), (3, "C", 5), (4, "G", 3)],
                17: [(4, "C", 8), (4, "C", 1), (4, "C", 5)],
                16: [(5, "G", 4), (5, "A", 6), (5, "A", 2)],
                15: [(5, "C", 3), (5, "G", 5), (5, "G", 1)],
                25: [(7, "H", 8), (7, "H", 5), (7, "H", 1)],
            },
            5: { # Spieler 6 (PL6)
                20: [(1, "F", 2), (1, "F", 3), (1, "F", 6)],
                19: [(3, "G", 4), (3, "G", 6), (3, "G", 8)],
                18: [(3, "G", 1), (3, "G", 5), (4, "G", 6)],
                17: [(4, "C", 6), (4, "C", 2), (4, "C", 4)],
                16: [(5, "G", 8), (5, "A", 1), (5, "A", 8)],
                15: [(5, "G", 2), (5, "G", 3), (5, "G", 7)],
                25: [(7, "H", 6), (7, "H", 2), (7, "H", 4)],
            },
            6: { # Spieler 7 (PL7)
                20: [(1, "G", 4), (1, "G", 8), (1, "G", 7)],
                19: [(3, "F", 7), (3, "G", 2), (3, "C", 3)],
                18: [(4, "A", 3), (4, "G", 1), (4, "G", 8)],
                17: [(4, "A", 7), (4, "A", 1), (4, "A", 5)],
                16: [(5, "C", 4), (5, "A", 4), (5, "A", 5)],
                15: [(5, "C", 5), (5, "C", 6), (5, "C", 1)],
                25: [(7, "C", 8), (7, "C", 5), (7, "C", 1)],
            },
            7: { # Spieler 8 (PL8)
                20: [(1, "G", 2), (1, "G", 3), (1, "G", 6)],
                19: [(3, "C", 4), (3, "C", 6), (3, "G", 7)],
                18: [(4, "G", 4), (4, "G", 2), (4, "G", 7)],
                17: [(4, "A", 6), (4, "A", 2), (4, "A", 4)],
                16: [(5, "C", 8), (5, "A", 7), (5, "A", 3)],
                15: [(5, "G", 3), (5, "C", 7), (5, "C", 2)],
                25: [(7, "C", 6), (7, "C", 2), (7, "C", 4)],
            }
        }

        self.PLAYER_ACTIVE_LEDS = {
            0: [(0, "C", 6), (0, "C", 2)],
            1: [(0, "C", 7), (0, "C", 3)],
            2: [(0, "C", 5), (0, "C", 1)],
            3: [(0, "C", 4), (0, "C", 8)],
            4: [(7, "A", 4), (7, "A", 8)],
            5: [(7, "A", 1), (7, "A", 5)],
            6: [(7, "A", 6), (7, "A", 2)],
            7: [(7, "A", 7), (7, "A", 3)],
        }

        # Grüne Dartpfeil-Symbole oben links (DART 1A..3C auf U1 Spalte G & U2 Spalte B)
        self.DART_ARROW_LEDS = {
            1: [(2, "B", 5), (2, "B", 2), (2, "B", 6)],
            2: [(0, "G", 5), (0, "G", 1), (2, "B", 1)],
            3: [(0, "G", 4), (0, "G", 8), (2, "B", 7)],
        }

    def set_light(self, state):
        self.light_state = bool(state)
        if not self.ser: return
        try:
            cmd = b"LIGHT:ON\n" if state else b"LIGHT:OFF\n"
            self.ser.write(cmd)
            self.ser.flush()
            time.sleep(0.015)
        except: pass

    def check_light_auto_on(self):
        if not self.light_state:
            self.set_light(True)

    def test_single_chip(self, chip_idx, digit_idx, bit_val=0xFF):
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        if 0 <= chip_idx < 9 and 0 <= digit_idx < 8:
            self.buffer[chip_idx][digit_idx] = bit_val
        self.update()

    def set_led(self, chip, col_letter, row_num, state):
        if not (0 <= chip < 9): return
        digit_idx = self.COL_TO_DIGIT[col_letter]
        bit_pos = self.ROW_TO_BIT[row_num]
        if state:
            self.buffer[chip][digit_idx] |= (1 << bit_pos)
        else:
            self.buffer[chip][digit_idx] &= ~(1 << bit_pos)

    def set_pl_lamp(self, lamp_num, state):
        self.check_light_auto_on()
        if lamp_num in self.ALL_PL_LEDS:
            for chip, col, row in self.ALL_PL_LEDS[lamp_num]:
                self.set_led(chip, col, row, state)

    def set_active_player(self, active_player_idx):
        """Schaltet die Lampe des aktuell aktiven Spielers (0..7) ein und alle anderen aus."""
        self.check_light_auto_on()
        for p_idx, leds in self.PLAYER_ACTIVE_LEDS.items():
            state = (p_idx == active_player_idx)
            for chip, col, row in leds:
                self.set_led(chip, col, row, state)

    def set_dart_arrows(self, arrows_count):
        """Schaltet 0 bis 3 grüne Dartpfeil-Symbole (übrige Pfeile) ein."""
        self.check_light_auto_on()
        arrows_count = max(0, min(3, int(arrows_count or 0)))
        for arrow_num in (1, 2, 3):
            state = (arrow_num <= arrows_count)
            for chip, col, row in self.DART_ARROW_LEDS[arrow_num]:
                self.set_led(chip, col, row, state)

    def set_bullseye_icon(self, state=True):
        """Schaltet das grüne Bullseye-Kreissymbol rechts neben der 15 (BE1..BE7 auf U7 Spalte C) ein/aus."""
        self.check_light_auto_on()
        for chip, col, row in self.BULLSEYE_ICON_LEDS:
            self.set_led(chip, col, row, state)

    def set_disp_char(self, disp_num, char, dot=False):
        if disp_num not in self.DISP_TABLE:
            return
        chip, col_letter, seg_order = self.DISP_TABLE[disp_num]
        digit_idx = self.COL_TO_DIGIT[col_letter]

        char = str(char).upper()
        active_segs = list(self.FONT.get(char, []))
        if dot:
            active_segs.append("DP")

        byte_val = 0
        for seg in active_segs:
            if seg in seg_order:
                row_num = seg_order[seg]
                bit_pos = self.ROW_TO_BIT[row_num]
                byte_val |= (1 << bit_pos)

        self.buffer[chip][digit_idx] = byte_val

    def set_score(self, player_idx, score):
        if player_idx not in self.PLAYER_DISP:
            return
        self.check_light_auto_on()
        d_hund, d_ten, d_unit = self.PLAYER_DISP[player_idx]
        if score is None or score == "":
            self.set_disp_char(d_hund, " ")
            self.set_disp_char(d_ten,  " ")
            self.set_disp_char(d_unit, " ")
            return

        score = max(0, min(999, int(score)))
        score_str = f"{score:3d}"
        self.set_disp_char(d_hund, score_str[0])
        self.set_disp_char(d_ten,  score_str[1])
        self.set_disp_char(d_unit, score_str[2])

    def set_temp_score(self, score):
        """Zeigt oben rechts (TEMP SCORE, DISP25-27) die Wurfsumme oder den aktuellen Punktestand an."""
        self.check_light_auto_on()
        d_hund, d_ten, d_unit = self.TEMP_SCORE_DISP
        if score is None or score == "":
            for d in (d_hund, d_ten, d_unit): self.set_disp_char(d, " ")
            return
        score_str = f"{max(0, min(999, int(score))):3d}"
        self.set_disp_char(d_hund, score_str[0])
        self.set_disp_char(d_ten,  score_str[1])
        self.set_disp_char(d_unit, score_str[2])

    def set_turn(self, value):
        """Zeigt ganz oben rechts (neben dem C-Symbol, DISP28-29) die Runde oder übrige Pfeile an."""
        self.check_light_auto_on()
        d_ten, d_unit = self.TURN_DISP
        if value is None or value == "":
            self.set_disp_char(d_ten,  " ")
            self.set_disp_char(d_unit, " ")
            return
        val_str = f"{max(0, min(99, int(value))):2d}"
        self.set_disp_char(d_ten,  val_str[0])
        self.set_disp_char(d_unit, val_str[1])

    def set_cricket_marks(self, player_idx, target, marks):
        self.check_light_auto_on()
        if target in self.CRICKET_TARGET_DISP:
            d_ten, d_unit = self.CRICKET_TARGET_DISP[target]
            t_str = f"{target:2d}"
            self.set_disp_char(d_ten, t_str[0])
            self.set_disp_char(d_unit, t_str[1])
        elif target == 25:
            # Grünes Bullseye-Symbol neben der 15 aktivieren!
            self.set_bullseye_icon(True)

        if player_idx in self.CRICKET_LEDS and target in self.CRICKET_LEDS[player_idx]:
            leds = self.CRICKET_LEDS[player_idx][target]
            for i, (chip, col, row) in enumerate(leds):
                self.set_led(chip, col, row, i < marks)

    def clear_all(self):
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.last_sent = [[-1 for _ in range(8)] for _ in range(9)]
        if not self.ser: return
        try:
            self.ser.write(b"CLEAR\n")
            self.ser.flush()
            time.sleep(0.03)
        except: pass

    def update(self):
        if not self.ser: return
        
        all_full = all(self.buffer[c][d] == 255 for c in range(9) for d in range(8))
        if all_full:
            if not all(self.last_sent[c][d] == 255 for c in range(9) for d in range(8)):
                try:
                    self.ser.write(b"FILL\n")
                    self.ser.flush()
                    for c in range(9):
                        for d in range(8):
                            self.last_sent[c][d] = 255
                    time.sleep(0.03)
                except: pass
            return

        for chip in range(9):
            for digit in range(8):
                val = self.buffer[chip][digit]
                if val != self.last_sent[chip][digit]:
                    try:
                        self.ser.write(f"RAW:{chip}:{digit}:{val}\n".encode('ascii'))
                        self.ser.flush()
                        self.last_sent[chip][digit] = val
                        time.sleep(0.012)
                    except: pass
