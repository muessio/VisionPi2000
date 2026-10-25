# Datei: display_mapper.py
import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        self.last_sent = [[-1 for _ in range(8)] for _ in range(10)]
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

        # Originales, physikalisches Spalten-Mapping der Löwen-Platine
        self.COL_TO_DIGIT = {
            "A": 2, "B": 6, "C": 5, "D": 4, "E": 3, "F": 7, "G": 1, "H": 0
        }

        self.ROW_TO_BIT = {
            1: 7, 2: 0, 3: 5, 4: 2, 5: 3, 6: 4, 7: 1, 8: 6
        }

        # Feinjustierte Segment-Zuordnungen basierend auf der Bilderserie
        SEG_U1      = { "A": 5, "B": 6, "C": 7, "D": 3, "E": 4, "F": 1, "G": 2, "DP": 8 }
        SEG_U1_SPEC = { "A": 5, "B": 3, "C": 6, "D": 7, "E": 4, "F": 1, "G": 2, "DP": 8 }
        SEG_U2      = { "A": 5, "B": 2, "C": 1, "D": 3, "E": 4, "F": 7, "G": 6, "DP": 8 }
        SEG_U3      = { "A": 4, "B": 2, "C": 3, "D": 5, "E": 1, "F": 6, "G": 7, "DP": 8 }
        SEG_U4      = { "A": 5, "B": 1, "C": 7, "D": 8, "E": 3, "F": 4, "G": 6, "DP": 2 }
        SEG_U5_U6   = { "A": 5, "B": 1, "C": 7, "D": 3, "E": 8, "F": 4, "G": 6, "DP": 2 }
        SEG_U7      = { "A": 5, "B": 3, "C": 2, "D": 7, "E": 1, "F": 4, "G": 6, "DP": 8 }
        SEG_U8      = { "A": 5, "B": 3, "C": 2, "D": 7, "E": 4, "F": 1, "G": 8, "DP": 6 }
        SEG_U9      = { "A": 8, "B": 7, "C": 2, "D": 3, "E": 5, "F": 4, "G": 6, "DP": 1 }

        self.DISP_TABLE = {
            1: (0, "H", SEG_U1), 2: (0, "D", SEG_U1), 3: (0, "B", SEG_U1_SPEC),
            7: (0, "F", SEG_U1_SPEC), 8: (0, "E", SEG_U1), 9: (0, "A", SEG_U1_SPEC),
            10: (1, "H", SEG_U3), 11: (1, "D", SEG_U3), 12: (1, "B", SEG_U3),
            13: (1, "E", SEG_U3), 14: (1, "A", SEG_U3),
            
            4: (2, "F", SEG_U2), 5: (2, "A", SEG_U2), 6: (2, "C", SEG_U2), 15: (2, "G", SEG_U2),
            16: (3, "D", SEG_U4), 17: (3, "A", SEG_U4), 18: (3, "E", SEG_U4),
            
            19: (4, "B", SEG_U5_U6), 20: (4, "F", SEG_U5_U6), 21: (4, "E", SEG_U5_U6),
            22: (5, "B", SEG_U5_U6), 23: (5, "F", SEG_U5_U6), 24: (5, "E", SEG_U5_U6),
            
            25: (6, "H", SEG_U7), 26: (6, "B", SEG_U7), 27: (6, "E", SEG_U7), 30: (6, "A", SEG_U7),
            31: (7, "D", SEG_U8), 32: (7, "B", SEG_U8),
            36: (7, "E", SEG_U8), 37: (7, "F", SEG_U8), 38: (7, "G", SEG_U8),
            
            28: (8, "E", SEG_U9), 29: (8, "F", SEG_U9),
            33: (8, "C", SEG_U9), 34: (8, "D", SEG_U9), 35: (8, "B", SEG_U9),
            39: (8, "H", SEG_U9), 40: (8, "G", SEG_U9), 41: (8, "A", SEG_U9),
        }

        self.PLAYER_DISP = {
            0: (1, 2, 3),     
            1: (5, 4, 6),     
            2: (9, 8, 7),     
            3: (12, 11, 10),  
            4: (30, 31, 32),  
            5: (33, 34, 35),  
            6: (36, 37, 38),  
            7: (39, 40, 41),  
        }

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

        self.CRICKET_LEDS = {
            0: {
                20: [(2, "H", 5), (2, "G", 2), (2, "G", 3)],
                19: [(3, "F", 1), (3, "G", 2), (3, "H", 1)],
                18: [(3, "H", 5), (3, "F", 8), (3, "F", 7)],
                17: [(4, "D", 5), (4, "D", 7), (4, "D", 1)],
                16: [(5, "D", 2), (5, "D", 8), (5, "D", 1)],
                15: [(6, "D", 2), (6, "D", 6), (6, "D", 7)],
                25: [(6, "F", 5), (6, "F", 6), (6, "G", 3)],
            },
            1: {
                20: [(2, "E", 4), (2, "H", 7), (2, "H", 1)],
                19: [(2, "H", 5), (3, "F", 3), (3, "H", 4)],
                18: [(3, "F", 6), (3, "H", 6), (3, "F", 2)],
                17: [(4, "C", 6), (4, "D", 2), (4, "D", 3)],
                16: [(5, "D", 7), (5, "D", 6), (5, "D", 5)],
                15: [(6, "D", 5), (6, "D", 1), (6, "D", 4)],
                25: [(6, "F", 1), (6, "F", 3), (6, "F", 7)],
            },
            2: {
                20: [(2, "E", 8), (2, "E", 6), (2, "E", 3)],
                19: [(2, "E", 2), (2, "E", 1), (2, "H", 8)],
                18: [(3, "B", 1), (3, "B", 8), (3, "B", 7)],
                17: [(4, "H", 5), (4, "H", 4), (4, "H", 1)],
                16: [(5, "H", 2), (5, "H", 4), (5, "H", 1)],
                15: [(6, "G", 2), (6, "G", 6), (6, "G", 7)],
                25: [(6, "G", 4), (6, "G", 8), (6, "H", 2)],
            },
            3: {
                20: [(2, "E", 5), (2, "E", 7), (2, "E", 1)],
                19: [(2, "E", 4), (3, "H", 3), (3, "H", 7)],
                18: [(3, "B", 6), (3, "H", 3), (3, "B", 7)],
                17: [(4, "H", 6), (4, "H", 7), (4, "H", 2)],
                16: [(5, "H", 7), (5, "H", 6), (5, "H", 5)],
                15: [(6, "G", 5), (6, "G", 1), (6, "G", 4)],
                25: [(6, "G", 3), (6, "G", 7), (6, "G", 8)],
            },
            4: {
                20: [(1, "F", 5), (1, "F", 1), (1, "F", 6)],
                19: [(3, "C", 4), (3, "G", 2), (3, "C", 3)],
                18: [(3, "C", 1), (3, "C", 5), (3, "G", 7)],
                17: [(4, "C", 8), (4, "C", 1), (4, "C", 5)],
                16: [(5, "G", 4), (5, "A", 6), (5, "A", 2)],
                15: [(5, "C", 5), (5, "G", 5), (5, "G", 1)],
                25: [(7, "H", 6), (7, "H", 5), (7, "H", 1)],
            },
            5: {
                20: [(1, "F", 2), (1, "F", 3), (1, "F", 6)],
                19: [(3, "G", 4), (3, "G", 6), (3, "G", 8)],
                18: [(3, "G", 1), (3, "C", 6), (3, "C", 8)],
                17: [(4, "C", 6), (4, "G", 6), (4, "C", 4)],
                16: [(5, "G", 8), (5, "A", 7), (5, "A", 8)],
                15: [(5, "G", 3), (5, "A", 3), (5, "A", 1)],
                25: [(7, "H", 7), (7, "H", 2), (7, "H", 4)],
            },
            6: {
                20: [(1, "G", 4), (1, "G", 8), (1, "G", 7)],
                19: [(3, "G", 7), (3, "B", 2), (3, "B", 4)],
                18: [(4, "A", 3), (4, "A", 1), (4, "G", 1)],
                17: [(4, "A", 7), (4, "A", 2), (4, "A", 5)],
                16: [(5, "C", 6), (5, "A", 4), (5, "A", 5)],
                15: [(5, "C", 3), (5, "C", 2), (5, "C", 1)],
                25: [(7, "C", 8), (7, "C", 5), (7, "C", 1)],
            },
            7: {
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
        self.light_state = bool(state)
        if not self.ser: return
        try:
            cmd = b"LIGHT:ON\n" if state else b"LIGHT:OFF\n"
            self.ser.write(cmd)
            self.ser.flush()
            time.sleep(0.01)
        except: pass

    def check_light_auto_on(self):
        if not self.light_state:
            self.set_light(True)

    def test_single_chip(self, chip_idx, digit_idx, bit_val=0xFF):
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        if 0 <= chip_idx < 10 and 0 <= digit_idx < 8:
            self.buffer[chip_idx][digit_idx] = bit_val
            if chip_idx == 8:
                self.buffer[9][digit_idx] = bit_val
        self.update()

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
        self.check_light_auto_on()
        d_hund, d_ten, d_unit = self.TEMP_SCORE_DISP
        if score is None or score == "":
            for d in (d_hund, d_ten, d_unit): self.set_disp_char(d, " ")
            return
        score_str = f"{max(0, min(999, int(score))):3d}"
        self.set_disp_char(d_hund, score_str[0])
        self.set_disp_char(d_ten,  score_str[1])
        self.set_disp_char(d_unit, score_str[2])

    def set_cricket_marks(self, player_idx, target, marks):
        self.check_light_auto_on()
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
        self.last_sent = [[-1 for _ in range(8)] for _ in range(10)]
        if not self.ser: return
        try:
            self.ser.write(b"CLEAR\n")
            self.ser.flush()
            time.sleep(0.02)
        except: pass

    def update(self):
        if not self.ser: return
        
        all_full = all(self.buffer[c][d] == 255 for c in range(9) for d in range(8))
        if all_full:
            if not all(self.last_sent[c][d] == 255 for c in range(9) for d in range(8)):
                try:
                    self.ser.write(b"FILL\n")
                    self.ser.flush()
                    for c in range(10):
                        for d in range(8):
                            self.last_sent[c][d] = 255
                    time.sleep(0.02)
                except: pass
            return

        for chip in range(10):
            for digit in range(8):
                val = self.buffer[chip][digit]
                if val != self.last_sent[chip][digit]:
                    try:
                        self.ser.write(f"RAW:{chip}:{digit}:{val}\n".encode('ascii'))
                        self.ser.flush()
                        self.last_sent[chip][digit] = val
                        time.sleep(0.004)
                    except: pass
