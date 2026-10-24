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

        SEG_U1 = { "F": 1, "G": 2, "D": 3, "E": 4, "A": 5, "B": 6, "C": 7, "DP": 8 }
        SEG_U1_DISP3 = { "F": 1, "G": 2, "B": 3, "E": 4, "A": 5, "C": 6, "D": 7, "DP": 8 }
        SEG_U2 = { "C": 1, "B": 2, "G": 3, "D": 4, "A": 5, "F": 6, "E": 7, "DP": 8 }
        SEG_U3 = { "E": 1, "B": 2, "C": 3, "A": 4, "D": 5, "F": 6, "G": 7, "DP": 8 }
        SEG_U4 = { "B": 1, "DP": 2, "E": 3, "F": 4, "A": 5, "G": 6, "C": 7, "D": 8 }
        SEG_U5_U6 = { "B": 1, "DP": 2, "D": 3, "F": 4, "A": 5, "G": 6, "C": 7, "E": 8 }
        SEG_U7 = { "E": 1, "C": 2, "B": 3, "F": 4, "A": 5, "G": 6, "D": 7, "DP": 8 }
        SEG_U8 = { "F": 1, "C": 2, "DP": 3, "E": 4, "A": 5, "B": 6, "D": 7, "G": 8 }
        SEG_U9 = { "A": 1, "C": 2, "D": 3, "F": 4, "E": 5, "G": 6, "DP": 7, "B": 8 }

        self.DISP_TABLE = {
            1: (0, "H", SEG_U1),
            2: (0, "D", SEG_U1),
            3: (0, "B", SEG_U1_DISP3),
            7: (0, "F", SEG_U1),
            8: (0, "E", SEG_U1),
            9: (0, "A", SEG_U1),
            10: (1, "H", SEG_U3),
            11: (1, "D", SEG_U3),
            12: (1, "B", SEG_U3),
            13: (1, "E", SEG_U3),
            14: (1, "A", SEG_U3),
            
            4: (2, "F", SEG_U2),
            5: (2, "A", SEG_U2),
            6: (2, "C", SEG_U2),
            15: (2, "G", SEG_U2),
            16: (3, "D", SEG_U4),
            17: (3, "A", SEG_U4),
            18: (3, "E", SEG_U4),
            
            19: (4, "B", SEG_U5_U6),
            20: (4, "F", SEG_U5_U6),
            21: (4, "E", SEG_U5_U6),
            22: (5, "B", SEG_U5_U6),
            23: (5, "F", SEG_U5_U6),
            24: (5, "E", SEG_U5_U6),
            
            25: (6, "H", SEG_U7),
            26: (6, "B", SEG_U7),
            27: (6, "E", SEG_U7),
            30: (6, "A", SEG_U7),
            31: (7, "D", SEG_U8),
            32: (7, "B", SEG_U8),
            36: (7, "E", SEG_U8),
            37: (7, "F", SEG_U8),
            38: (7, "G", SEG_U8),
            
            # Strang D4: U9 (Einzelchip auf Chain 4)
            28: (8, "E", SEG_U9),
            29: (8, "F", SEG_U9),
            33: (8, "C", SEG_U9),
            34: (8, "D", SEG_U9),
            35: (8, "B", SEG_U9),
            39: (8, "H", SEG_U9),
            40: (8, "G", SEG_U9),
            41: (8, "A", SEG_U9),
        }

        self.PLAYER_DISP = {
            0: (9, 8, 7),     
            1: (6, 5, 4),     
            2: (3, 2, 1),     
            3: (12, 11, 10),  
            4: (15, 14, 13),  
            5: (18, 17, 16),  
            6: (21, 20, 19),  
            7: (24, 23, 22)   
        }

        self.CRICKET_DISP_MAP = {
            15: 28, 16: 29, 17: 33, 18: 34, 19: 35, 20: 39, 25: 40
        }

    def set_light(self, state):
        if not self.ser: return
        try:
            cmd = b"LIGHT:ON\n" if state else b"LIGHT:OFF\n"
            self.ser.write(cmd)
            self.ser.flush()
            time.sleep(0.01)
        except: pass

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
        # Wenn U9 (Chip 8) angesprochen wird, auf beide Hälften von Chain 4 spiegeln
        if chip == 8:
            self.buffer[8][digit_idx] = byte_val
            self.buffer[9][digit_idx] = byte_val

    def set_score(self, player_idx, score):
        if player_idx not in self.PLAYER_DISP:
            return
        score = max(0, min(999, int(score)))
        score_str = f"{score:3d}"

        d_hund, d_ten, d_unit = self.PLAYER_DISP[player_idx]
        self.set_disp_char(d_hund, score_str[0])
        self.set_disp_char(d_ten,  score_str[1])
        self.set_disp_char(d_unit, score_str[2])

    def set_cricket_marks(self, player_idx, target, marks):
        if target not in self.CRICKET_DISP_MAP: 
            return
        disp_num = self.CRICKET_DISP_MAP[target]
        char_to_show = str(marks) if marks > 0 else " "
        self.set_disp_char(disp_num, char_to_show)

    def clear_all(self):
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        if not self.ser: return
        for chip in range(10):
            for digit in range(8):
                try:
                    self.ser.write(f"RAW:{chip}:{digit}:0\n".encode('ascii'))
                    self.ser.flush()
                    self.last_sent[chip][digit] = 0
                    time.sleep(0.005)
                except: pass

    def update(self):
        if not self.ser: return
        for chip in range(10):
            for digit in range(8):
                val = self.buffer[chip][digit]
                if val != self.last_sent[chip][digit]:
                    try:
                        self.ser.write(f"RAW:{chip}:{digit}:{val}\n".encode('ascii'))
                        self.ser.flush()
                        self.last_sent[chip][digit] = val
                        time.sleep(0.006)
                    except: pass
