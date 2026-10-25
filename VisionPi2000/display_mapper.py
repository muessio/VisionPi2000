# Datei: display_mapper.py
import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        self.last_sent = [[-1 for _ in range(8)] for _ in range(10)]

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

        self.COL_TO_DIGIT = {
            "A": 2, "B": 6, "C": 5, "D": 4, "E": 3, "F": 7, "G": 1, "H": 0
        }

        self.ROW_TO_BIT = {
            1: 7, 2: 0, 3: 5, 4: 2, 5: 3, 6: 4, 7: 1, 8: 6
        }

        # Exakt verifizierte Segment-Zuordnungen anhand der Live-Board-Fotos:
        SEG_U1       = { "F": 1, "G": 2, "D": 3, "E": 4, "A": 5, "B": 6, "C": 7, "DP": 8 }
        SEG_U1_SPEC  = { "F": 1, "G": 2, "B": 3, "E": 4, "A": 5, "C": 6, "D": 7, "DP": 8 }
        # U2 laut Schaltplan Blatt 3: Zeile 3=F, Zeile 4=E, Zeile 6=G, Zeile 7=D
        SEG_U2       = { "C": 1, "B": 2, "F": 3, "E": 4, "A": 5, "G": 6, "D": 7, "DP": 8 }
        # U3 Fix: Aus "0" wurde "e" -> Zeile 6 ist G und Zeile 7 ist F!
        SEG_U3       = { "E": 1, "B": 2, "C": 3, "A": 4, "D": 5, "G": 6, "F": 7, "DP": 8 }
        SEG_U4       = { "B": 1, "DP": 2, "E": 3, "F": 4, "A": 5, "G": 6, "C": 7, "D": 8 }
        SEG_U5_U6    = { "B": 1, "DP": 2, "D": 3, "F": 4, "A": 5, "G": 6, "C": 7, "E": 8 }
        SEG_U7       = { "E": 1, "C": 2, "B": 3, "F": 4, "A": 5, "G": 6, "D": 7, "DP": 8 }
        SEG_U8       = { "F": 1, "C": 2, "DP": 3, "E": 4, "A": 5, "B": 6, "D": 7, "G": 8 }
        # U9 laut Schaltplan Blatt 3: Zeile 6=G, Zeile 7=DP, Zeile 8=B
        SEG_U9       = { "A": 1, "C": 2, "D": 3, "F": 4, "E": 5, "G": 6, "DP": 7, "B": 8 }

        self.DISP_TABLE = {
            # Strang D0: U1 (Chip 0), U3 (Chip 1)
            # Auf Block 1 braucht DISP3 das Spezial-Mapping, auf Block 3 braucht DISP9 das Standard-Mapping!
            1: (0, "H", SEG_U1), 2: (0, "D", SEG_U1), 3: (0, "B", SEG_U1_SPEC),
            7: (0, "F", SEG_U1), 8: (0, "E", SEG_U1), 9: (0, "A", SEG_U1_SPEC),
            10: (1, "H", SEG_U3), 11: (1, "D", SEG_U3), 12: (1, "B", SEG_U3),
            13: (1, "E", SEG_U3), 14: (1, "A", SEG_U3),
            
            # Strang D1: U2 (Chip 2), U4 (Chip 3)
            4: (2, "F", SEG_U2), 5: (2, "A", SEG_U2), 6: (2, "C", SEG_U2), 15: (2, "G", SEG_U2),
            16: (3, "D", SEG_U4), 17: (3, "A", SEG_U4), 18: (3, "E", SEG_U4),
            
            # Strang D2: U5 (Chip 4), U6 (Chip 5)
            19: (4, "B", SEG_U5_U6), 20: (4, "F", SEG_U5_U6), 21: (4, "E", SEG_U5_U6),
            22: (5, "B", SEG_U5_U6), 23: (5, "F", SEG_U5_U6), 24: (5, "E", SEG_U5_U6),
            
            # Strang D3: U7 (Chip 6), U8 (Chip 7)
            25: (6, "H", SEG_U7), 26: (6, "B", SEG_U7), 27: (6, "E", SEG_U7), 30: (6, "A", SEG_U7),
            31: (7, "D", SEG_U8), 32: (7, "B", SEG_U8),
            36: (7, "E", SEG_U8), 37: (7, "F", SEG_U8), 38: (7, "G", SEG_U8),
            
            # Strang D4: U9 (Chip 8)
            28: (8, "E", SEG_U9), 29: (8, "F", SEG_U9),
            33: (8, "C", SEG_U9), 34: (8, "D", SEG_U9), 35: (8, "B", SEG_U9),
            39: (8, "H", SEG_U9), 40: (8, "G", SEG_U9), 41: (8, "A", SEG_U9),
        }

        # =========================================================================
        # EXAKT VERIFIZIERTE SPIELER-BLÖCKE (Hunderter, Zehner, Einer von links nach rechts)
        # =========================================================================
        self.PLAYER_DISP = {
            0: (1, 2, 3),     # Block 1: 501 war bereits perfekt!
            1: (5, 4, 6),     # Block 2: bei Cricket ("  0") leuchtete die Mitte (4), also (5, 4, 6) oder (6, 4, 5)
            2: (7, 8, 9),     # Block 3: 5 stand auf 7 (links), 0 bei Cricket auf 9 (rechts)!
            3: (10, 11, 12),  # Block 4: bei 501 stand 5 rechts (10), bei Cricket 0 links (12) -> (10, 11, 12)!
            4: (30, 31, 32),  # Block 5
            5: (33, 34, 35),  # Block 6
            6: (36, 37, 38),  # Block 7
            7: (39, 40, 41),  # Block 8
        }

        self.TEMP_SCORE_DISP = (25, 26, 27)
        self.TURN_DISP       = (29, 28)

        # Grüne Cricket-Zielzahlen (Zehner links, Einer rechts)
        self.CRICKET_TARGET_DISP = {
            20: (14, 13),
            19: (16, 15),
            18: (18, 17),
            17: (20, 19),
            16: (22, 21),
            15: (24, 23),
        }

        self.CRICKET_LEDS = {
            0: { # Spieler 1 (PL1)
                20: [(2, "H", 5), (2, "G", 2), (2, "G", 3)],
                19: [(3, "F", 1), (3, "G", 2), (3, "H", 1)],
                18: [(3, "H", 5), (3, "F", 8), (3, "F", 7)],
                17: [(4, "D", 5), (4, "D", 7), (4, "D", 1)],
                16: [(5, "D", 2), (5, "D", 8), (5, "D", 1)],
                15: [(6, "D", 2), (6, "D", 6), (6, "D", 7)],
                25: [(6, "F", 5), (6, "F", 6), (6, "G", 3)],
            },
            1: { # Spieler 2 (PL2)
                20: [(2, "E", 4), (2, "H", 7), (2, "H", 1)],
                19: [(2, "H", 5), (3, "F", 3), (3, "H", 4)],
                18: [(3, "F", 6), (3, "H", 6), (3, "F", 2)],
                17: [(4, "C", 6), (4, "D", 2), (4, "D", 3)],
                16: [(5, "D", 7), (5, "D", 6), (5, "D", 5)],
                15: [(6, "D", 5), (6, "D", 1), (6, "D", 4)],
                25: [(6, "F", 1), (6, "F", 3), (6, "F", 7)],
            },
            2: { # Spieler 3 (PL3)
                20: [(2, "E", 8), (2, "E", 6), (2, "E", 3)],
                19: [(2, "E", 2), (2, "E", 1), (2, "H", 8)],
                18: [(3, "B", 1), (3, "B", 8), (3, "B", 7)],
                17: [(4, "H", 5), (4, "H", 4), (4, "H", 1)],
                16: [(5, "H", 2), (5, "H", 4), (5, "H", 1)],
                15: [(6, "G", 2), (6, "G", 6), (6, "G", 7)],
                25: [(6, "G", 4), (6, "G", 8), (6, "H", 2)],
            },
            3: { # Spieler 4 (PL4)
                20: [(2, "E", 5), (2, "E", 7), (2, "E", 1)],
                19: [(2, "E", 4), (3, "H", 3), (3, "H", 7)],
                18: [(3, "B", 6), (3, "H", 3), (3, "B", 7)],
                17: [(4, "H", 6), (4, "H", 7), (4, "H", 2)],
                16: [(5, "H", 7), (5, "H", 6), (5, "H", 5)],
                15: [(6, "G", 5), (6, "G", 1), (6, "G", 4)],
                25: [(6, "G", 3), (6, "G", 7), (6, "G", 8)],
            },
            4: { # Spieler 5 (PL5)
                20: [(1, "F", 5), (1, "F", 1), (1, "F", 6)],
                19: [(3, "C", 4), (3, "G", 2), (3, "C", 3)],
                18: [(3, "C", 1), (3, "C", 5), (3, "G", 7)],
                17: [(4, "C", 8), (4, "C", 1), (4, "C", 5)],
                16: [(5, "G", 4), (5, "A", 6), (5, "A", 2)],
                15: [(5, "C", 5), (5, "G", 5), (5, "G", 1)],
                25: [(7, "H", 6), (7, "H", 5), (7, "H", 1)],
            },
            5: { # Spieler 6 (PL6)
                20: [(1, "F", 2), (1, "F", 3), (1, "F", 6)],
                19: [(3, "G", 4), (3, "G", 6), (3, "G", 8)],
                18: [(3, "G", 1), (3, "C", 6), (3, "C", 8)],
                17: [(4, "C", 6), (4, "G", 6), (4, "C", 4)],
                16: [(5, "G", 8), (5, "A", 7), (5, "A", 8)],
                15: [(5, "G", 3), (5, "A", 3), (5, "A", 1)],
                25: [(7, "H", 7), (7, "H", 2), (7, "H", 4)],
            },
            6: { # Spieler 7 (PL7)
                20: [(1, "G", 4), (1, "G", 8), (1, "G", 7)],
                19: [(3, "G", 7), (3, "B", 2), (3, "B", 4)],
                18: [(4, "A", 3), (4, "A", 1), (4, "G", 1)],
                17: [(4, "A", 7), (4, "A", 2), (4, "A", 5)],
                16: [(5, "C", 6), (5, "A", 4), (5, "A", 5)],
                15: [(5, "C", 3), (5, "C", 2), (5, "C", 1)],
                25: [(7, "C", 8), (7, "C", 5), (7, "C", 1)],
            },
            7: { # Spieler 8 (PL8)
                20: [(1, "G", 2), (1, "G", 3), (1, "G", 6)],
                19: [(3, "C", 2), (3, "C", 6), (3, "C", 4)],
                18: [(4, "G", 4), (4, "G", 2), (4, "G", 7)],
                17: [(4, "G", 5), (4, "A", 6), (4, "A", 4)],
                16: [(5, "C", 8), (5, "A", 7), (5, "A", 3)],
                15: [(5, "G", 7), (5, "C", 7), (5, "C", 3)],
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

        self.DART_ARROW_LEDS = {
            1: [(2, "B", 5), (2, "B", 2), (2, "B", 6)],
            2: [(0, "G", 5), (0, "G", 1), (2, "B", 1)],
            3: [(0, "G", 4), (0, "G", 8), (2, "B", 7)],
        }

    def set_light(self, state):
        if not self.ser: return
        try:
            time.sleep(0.02)
            cmd = b"LIGHT:ON\n" if state else b"LIGHT:OFF\n"
            self.ser.write(cmd)
            self.ser.flush()
            time.sleep(0.02)
        except: pass

    def set_led(self, chip, col_letter, row_num, state):
        digit_idx = self.COL_TO_DIGIT[col_letter]
        bit_pos = self.ROW_TO_BIT[row_num]
        if state:
            self.buffer[chip][digit_idx] |= (1 << bit_pos)
        else:
            self.buffer[chip][digit_idx] &= ~(1 << bit_pos)
        if chip == 8:
            self.buffer[9][digit_idx] = self.buffer[8][digit_idx]

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
        if chip == 8:
            self.buffer[9][digit_idx] = byte_val

    def set_score(self, player_idx, score):
        if player_idx not in self.PLAYER_DISP:
            return
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
        d_hund, d_ten, d_unit = self.TEMP_SCORE_DISP
        if score is None or score == "":
            for d in (d_hund, d_ten, d_unit): self.set_disp_char(d, " ")
            return
        score_str = f"{max(0, min(999, int(score))):3d}"
        self.set_disp_char(d_hund, score_str[0])
        self.set_disp_char(d_ten,  score_str[1])
        self.set_disp_char(d_unit, score_str[2])

    def set_cricket_marks(self, player_idx, target, marks):
        if target in self.CRICKET_TARGET_DISP:
            d_ten, d_unit = self.CRICKET_TARGET_DISP[target]
            t_str = f"{target:2d}"
            self.set_disp_char(d_ten, t_str[0])
            self.set_disp_char(d_unit, t_str[1])

        if player_idx in self.CRICKET_LEDS and target in self.CRICKET_LEDS[player_idx]:
            leds = self.CRICKET_LEDS[player_idx][target]
            for i, (chip, col, row) in enumerate(leds):
                self.set_led(chip, col, row, i < marks)

    def clear_all(self):
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        self.last_sent = [[0 for _ in range(8)] for _ in range(10)]
        if not self.ser: return
        try:
            self.ser.write(b"CLEAR\n")
            self.ser.flush()
            time.sleep(0.04)
        except: pass

    def update(self):
        if not self.ser: return
        for chip in range(9):
            for digit in range(8):
                val = self.buffer[chip][digit]
                if val != self.last_sent[chip][digit]:
                    try:
                        self.ser.write(f"RAW:{chip}:{digit}:{val}\n".encode('ascii'))
                        self.ser.flush()
                        self.last_sent[chip][digit] = val
                        time.sleep(0.006)
                    except: pass
