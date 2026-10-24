import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.last_sent = [[0 for _ in range(8)] for _ in range(9)]

        self.FONT = {
            "0": ["A","B","C","D","E","F"], "1": ["B","C"], "2": ["A","B","D","E","G"],
            "3": ["A","B","C","D","G"], "4": ["B","C","F","G"], "5": ["A","C","D","F","G"],
            "6": ["A","C","D","E","F","G"], "7": ["A","B","C"], "8": ["A","B","C","D","E","F","G"],
            "9": ["A","B","C","D","F","G"], " ": [], "-": ["G"]
        }

        self.MAPPING = {}
        self._generate_linear_fallback_mapping()

    def _generate_linear_fallback_mapping(self):
        """Erzeugt ein Basis-Mapping, damit das Display nicht dunkel bleibt."""
        player_chips = [(0, 2), (1, 2), (0, 5), (1, 5), (2, 2), (3, 2), (2, 5), (3, 5)]
        for p_idx, (chip, start_digit) in enumerate(player_chips):
            for d_idx in range(3): 
                digit_col = start_digit - d_idx
                self.MAPPING[f"P{p_idx+1}_D{d_idx+1}"] = {
                    "DP": (chip, digit_col, 0), "C": (chip, digit_col, 1),
                    "A": (chip, digit_col, 2), "B": (chip, digit_col, 3),
                    "D": (chip, digit_col, 4), "E": (chip, digit_col, 5),
                    "F": (chip, digit_col, 6), "G": (chip, digit_col, 7)
                }

    def set_light(self, state):
        if not self.ser: return
        try:
            cmd = b"LIGHT:ON\n" if state else b"LIGHT:OFF\n"
            self.ser.write(cmd)
            self.ser.flush()
        except: pass

    def _set_bit(self, chip, col, bit, state):
        if state: self.buffer[chip][col] |= (1 << bit)
        else: self.buffer[chip][col] &= ~(1 << bit)

    def set_digit(self, disp_name, char):
        if disp_name not in self.MAPPING: return
        char = str(char).upper()
        active_segments = self.FONT.get(char, [])
        for seg_name, coords in self.MAPPING[disp_name].items():
            if seg_name == "DP": continue
            chip, col, bit = coords
            self._set_bit(chip, col, bit, seg_name in active_segments)

    def set_score(self, player_idx, score):
        score_str = f"{max(0, score):03d}"
        p_num = player_idx + 1
        self.set_digit(f"P{p_num}_D1", score_str[0]) 
        self.set_digit(f"P{p_num}_D2", score_str[1]) 
        self.set_digit(f"P{p_num}_D3", score_str[2])

    def clear_all(self):
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.update()

    def update(self):
        if not self.ser: return
        for chip in range(9):
            for col in range(8):
                current_val = self.buffer[chip][col]
                if current_val != self.last_sent[chip][col]:
                    try:
                        cmd = f"RAW:{chip}:{col}:{current_val}\n"
                        self.ser.write(cmd.encode('ascii'))
                        self.ser.flush()
                        self.last_sent[chip][col] = current_val
                        time.sleep(0.002) 
                    except: pass
