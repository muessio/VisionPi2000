import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.last_sent = [[0 for _ in range(8)] for _ in range(9)]

        # Standard 7-Segment Layout
        self.FONT = {
            "0": ["A","B","C","D","E","F"], "1": ["B","C"], "2": ["A","B","D","E","G"],
            "3": ["A","B","C","D","G"], "4": ["B","C","F","G"], "5": ["A","C","D","F","G"],
            "6": ["A","C","D","E","F","G"], "7": ["A","B","C"], "8": ["A","B","C","D","E","F","G"],
            "9": ["A","B","C","D","F","G"], " ": [], "-": ["G"]
        }

        # -------------------------------------------------------------------
        # DAS FINALE, KORREKTE MAPPING FÜR SPIELER 1 BIS 4
        # Unter Berücksichtigung des MAX7219 Hardware-Bit-Routings:
        # Row 1=Bit7, Row 2=Bit0, Row 3=Bit5, Row 4=Bit2, Row 5=Bit3, Row 6=Bit4, Row 7=Bit1, Row 8=Bit6
        # Koordinaten: (Chip, Spalte, Bit)
        # -------------------------------------------------------------------
        self.MAPPING = {
            # --- SPIELER 1 (Rechts oben) ---
            "P1_D1": { "F": (0, 1, 7), "G": (0, 1, 0), "D": (0, 1, 5), "E": (0, 1, 2), "A": (0, 1, 3), "B": (0, 1, 4), "C": (0, 1, 1), "DP": (0, 1, 6) }, # DISP3
            "P1_D2": { "F": (0, 3, 7), "G": (0, 3, 0), "D": (0, 3, 5), "E": (0, 3, 2), "A": (0, 4, 3), "B": (0, 4, 4), "C": (0, 4, 1), "DP": (0, 4, 6) }, # DISP2
            "P1_D3": { "F": (0, 7, 7), "G": (0, 7, 0), "E": (0, 7, 5), "D": (0, 7, 2), "A": (0, 7, 3), "B": (0, 7, 4), "C": (0, 7, 1), "DP": (0, 7, 6) }, # DISP1

            # --- SPIELER 2 (Rechts unten) ---
            "P2_D1": { "C": (2, 2, 7), "G": (2, 2, 0), "F": (2, 2, 5), "E": (2, 2, 2), "A": (2, 2, 3), "B": (2, 2, 4), "D": (2, 2, 1), "DP": (2, 2, 6) }, # DISP6
            "P2_D2": { "C": (2, 0, 7), "G": (2, 0, 0), "F": (2, 0, 5), "E": (2, 0, 2), "A": (2, 0, 3), "B": (2, 0, 4), "D": (2, 0, 1), "DP": (2, 0, 6) }, # DISP5
            "P2_D3": { "F": (2, 5, 7), "G": (2, 5, 0), "E": (2, 5, 5), "D": (2, 5, 2), "A": (2, 5, 3), "B": (2, 5, 4), "C": (2, 5, 1), "DP": (2, 5, 6) }, # DISP4

            # --- SPIELER 3 (Links oben) ---
            "P3_D1": { "F": (0, 0, 7), "G": (0, 0, 0), "E": (0, 0, 5), "D": (0, 0, 2), "A": (0, 0, 3), "B": (0, 0, 4), "C": (0, 0, 1), "DP": (0, 0, 6) }, # DISP9
            "P3_D2": { "A": (0, 3, 3), "B": (0, 3, 4), "C": (0, 3, 1), "DP": (0, 3, 6), "F": (0, 4, 7), "G": (0, 4, 0), "D": (0, 4, 5), "E": (0, 4, 2) }, # DISP8
            "P3_D3": { "F": (0, 5, 7), "G": (0, 5, 0), "D": (0, 5, 5), "E": (0, 5, 2), "A": (0, 5, 3), "B": (0, 5, 4), "C": (0, 5, 1), "DP": (0, 5, 6) }, # DISP7

            # --- SPIELER 4 (Links unten) ---
            "P4_D1": { "E": (1, 1, 7), "B": (1, 1, 0), "C": (1, 1, 5), "A": (1, 1, 2), "F": (1, 1, 3), "D": (1, 1, 4), "G": (1, 1, 1), "DP": (1, 1, 6) }, # DISP12
            "P4_D2": { "E": (1, 3, 7), "B": (1, 3, 0), "C": (1, 3, 5), "A": (1, 3, 2), "F": (1, 4, 3), "D": (1, 4, 4), "G": (1, 4, 1), "DP": (1, 4, 6) }, # DISP11
            "P4_D3": { "E": (1, 7, 7), "B": (1, 7, 0), "C": (1, 7, 5), "A": (1, 7, 2), "F": (1, 7, 3), "D": (1, 7, 4), "G": (1, 7, 1), "DP": (1, 7, 6) }  # DISP10
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
        
        # Leite den 3-stelligen String an die korrekten virtuellen Displays weiter
        self.set_digit(f"P{p_num}_D1", score_str[0]) 
        self.set_digit(f"P{p_num}_D2", score_str[1]) 
        self.set_digit(f"P{p_num}_D3", score_str[2])

    def clear_all(self):
        """Löscht das Display und erzwingt das Senden der Nullen an den Arduino"""
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        if self.ser:
            for chip in range(9):
                for col in range(8):
                    if self.last_sent[chip][col] != 0:
                        try:
                            self.ser.write(f"RAW:{chip}:{col}:0\n".encode('ascii'))
                            self.ser.flush()
                            self.last_sent[chip][col] = 0
                            time.sleep(0.002)
                        except: pass
        self.update()

    def update(self):
        """Sendet nur die Änderungen aus dem Puffer an den Arduino"""
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
