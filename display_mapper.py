import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        # Virtueller Speicher für die 9 Chips (U1-U9) mit je 8 Spalten
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.last_sent = [[0 for _ in range(8)] for _ in range(9)]

        # 7-Segment Font (A-G)
        self.FONT = {
            "0": ["A","B","C","D","E","F"], "1": ["B","C"], "2": ["A","B","D","E","G"],
            "3": ["A","B","C","D","G"], "4": ["B","C","F","G"], "5": ["A","C","D","F","G"],
            "6": ["A","C","D","E","F","G"], "7": ["A","B","C"], "8": ["A","B","C","D","E","F","G"],
            "9": ["A","B","C","D","F","G"], " ": [], "-": ["G"]
        }

        # -------------------------------------------------------------------
        # HIER TRÄGST DU DIE SCHALTPLAN-TABELLEN EIN (FLEISSARBEIT)
        # Aufbau der Namen z.B.: "P1_D1" (Spieler 1 Hunderter), "P1_D2" (Zehner), "P1_D3" (Einer)
        # -------------------------------------------------------------------
        self.MAPPING = {
            # BEISPIEL: Die Einer-Stelle von Spieler 1 (entspricht DISP1 im Schaltplan)
            "P1_D3": { 
                "G": (0, 7, 7), "F": (0, 7, 6), "E": (0, 7, 5), "D": (0, 7, 4),
                "B": (0, 7, 3), "A": (0, 7, 2), "C": (0, 7, 1)
            },
            # HIER DIE WEITEREN ZIFFERN FÜR ALLE SPIELER EINTRAGEN...
            # "P1_D2": { ... }, "P1_D1": { ... }, 
            # "P2_D3": { ... }, ...
        }

    def set_light(self, state):
        """Steuert das 230V Relais für die Beleuchtung (LICHT GEFIXT!)"""
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
        """Schreibt eine Zahl/Zeichen in ein logisches Display (z.B. P1_D3)."""
        if disp_name not in self.MAPPING: return
        char = str(char).upper()
        active_segments = self.FONT.get(char, [])
        for seg_name, coords in self.MAPPING[disp_name].items():
            if seg_name == "DP": continue
            chip, col, bit = coords
            self._set_bit(chip, col, bit, seg_name in active_segments)

    def set_score(self, player_idx, score):
        """Bequeme Funktion für Spiele: Schreibt einen 3-stelligen Score für Spieler X"""
        score_str = f"{max(0, score):03d}"
        p_num = player_idx + 1
        # Mappt auf die Namen "P1_D1" (Hunderter), "P1_D2" (Zehner), "P1_D3" (Einer)
        self.set_digit(f"P{p_num}_D1", score_str[0]) 
        self.set_digit(f"P{p_num}_D2", score_str[1]) 
        self.set_digit(f"P{p_num}_D3", score_str[2])

    def clear_all(self):
        """Löscht das gesamte Display und den Zwischenspeicher"""
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.update()

    def update(self):
        """Sendet nur die Änderungen an den Arduino, um Flackern zu verhindern"""
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
                        time.sleep(0.002) # Winzige Pause für die Signalstabilität
                    except: pass
