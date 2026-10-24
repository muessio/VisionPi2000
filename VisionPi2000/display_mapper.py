# Datei: display_mapper.py
import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        self.last_sent = [[-1 for _ in range(8)] for _ in range(10)]

        # Standard 7-Segment Font-Tabelle (A bis G Segmente)
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

        # Direkte Spalten-Zuordnung für die MAX7219 Digit-Register (0 bis 7)
        self.COL_TO_DIGIT = {
            "A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7
        }

        # Direkte Bit-Zuordnung der Segmente A-G auf die Pins 0-7
        self.ROW_TO_BIT = {
            "A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "DP": 7
        }

        # Chip-Zuordnung für die 41 Displays laut Schaltplan
        self.DISP_TABLE = {}
        for d in range(1, 42):
            if d <= 14:
                chip = (d - 1) // 7
                col = ["H", "D", "B", "F", "E", "A"][d % 6]
            elif d <= 18:
                chip = 2 if d < 17 else 3
                col = "F" if d in [4, 16] else ("A" if d == 5 else "E")
            elif d <= 24:
                chip = 4 + (d - 19) // 3
                col = "B"
            elif d <= 32:
                chip = 6 if d < 31 else 7
                col = "H"
            else:
                chip = 8
            
            # Universelles Fallback-Mapping, damit jedes Display direkt ansprechbar ist
            self.DISP_TABLE[d] = (chip, "A", {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7})

        # Exakte physische Display-Blöcke (Spieler 1 bis 8)
        self.PLAYER_DISP = {
            0: (1, 2, 3),     # Spieler 1 -> Block 1
            1: (4, 5, 6),     # Spieler 2 -> Block 2
            2: (7, 8, 9),     # Spieler 3 -> Block 3
            3: (10, 11, 12),  # Spieler 4 -> Block 4
            4: (13, 14, 15),  # Spieler 5 -> Block 5
            5: (16, 17, 18),  # Spieler 6 -> Block 6
            6: (19, 20, 21),  # Spieler 7 -> Block 7
            7: (22, 23, 24)   # Spieler 8 -> Block 8
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
        
        char = str(char).upper()
        active_segs = self.FONT.get(char, [])

        byte_val = 0
        for seg in active_segs:
            if seg in self.ROW_TO_BIT:
                byte_val |= (1 << self.ROW_TO_BIT[seg])

        self.buffer[chip][0] = byte_val
        if chip == 8:
            self.buffer[8][0] = byte_val
            self.buffer[9][0] = byte_val

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
                    time.sleep(0.003)
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
                        time.sleep(0.004)
                    except: pass
                        
