import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.last_sent = [[0 for _ in range(8)] for _ in range(9)]

        # -------------------------------------------------------------------
        # 1. DER LÖWEN-FONT (HARDWARE-ANGEPASST)
        # Die Kabelreihenfolge in EINER Spalte ist laut Plan IMMER:
        # Bit 7=F, Bit 6=G, Bit 5=D, Bit 4=E, Bit 3=A, Bit 2=B, Bit 1=C, Bit 0=DP
        # Wir rechnen die Zeichen direkt in fertige Hex-Bytes um!
        # -------------------------------------------------------------------
        self.FONT = {
            "0": 0xBE, # 10111110 (F,D,E,A,B,C)
            "1": 0x06, # 00000110 (B,C)
            "2": 0x7C, # 01111100 (G,D,E,A,B)
            "3": 0x6E, # 01101110 (G,D,A,B,C)
            "4": 0xC6, # 11000110 (F,G,B,C)
            "5": 0xEA, # 11101010 (F,G,D,A,C)
            "6": 0xFA, # 11111010 (F,G,D,E,A,C)
            "7": 0x0E, # 00001110 (A,B,C)
            "8": 0xFE, # 11111110 (Alle außer DP)
            "9": 0xEE, # 11101110 (F,G,D,A,B,C)
            " ": 0x00, # Alles aus
            "-": 0x40  # 01000000 (Nur G)
        }

        # -------------------------------------------------------------------
        # 2. KOMPLETTES MAPPING ALLER 41 ZIFFERN (LAUT SCHALTPLAN!)
        # Format: DISP_Nummer: (Chip, Spalte)
        # Chip-Zuordnung: U1=0, U3=1, U2=2, U4=3, U5=4, U6=5, U7=6, U8=7, U9=8
        # -------------------------------------------------------------------
        self.DIGITS = {
            # --- CHIP U1 (0) ---
            9: (0, 0), 3: (0, 1), 2: (0, 3), 8: (0, 4), 7: (0, 5), 1: (0, 7),
            # --- CHIP U3 (1) ---
            14: (1, 0), 12: (1, 1), 11: (1, 3), 13: (1, 4), 10: (1, 7),
            # --- CHIP U2 (2) ---
            5: (2, 0), 6: (2, 2), 4: (2, 5), 15: (2, 6),
            # --- CHIP U4 (3) ---
            17: (3, 0), 16: (3, 3), 18: (3, 4),
            # --- CHIP U5 (4) ---
            19: (4, 1), 21: (4, 4), 20: (4, 5),
            # --- CHIP U6 (5) ---
            22: (5, 1), 24: (5, 4), 23: (5, 5),
            # --- CHIP U7 (6) ---
            30: (6, 0), 26: (6, 1), 27: (6, 4), 25: (6, 7),
            # --- CHIP U8 (7) ---
            32: (7, 1), 31: (7, 3), 36: (7, 4), 37: (7, 5), 38: (7, 6),
            # --- CHIP U9 (8) (Runden/Spiele Anzeigen) ---
            41: (8, 0), 35: (8, 1), 33: (8, 2), 34: (8, 3), 
            28: (8, 4), 29: (8, 5), 40: (8, 6), 39: (8, 7)
        }

        # -------------------------------------------------------------------
        # 3. SPIELER ZU DISP ZUORDNUNG (Logische Verknüpfung)
        # Aufbau: Spieler_Index (0-7): (DISP_Hunderter, DISP_Zehner, DISP_Einer)
        # Wenn eine Stelle am Automaten fehlt, steht dort 'None'
        # -------------------------------------------------------------------
        self.PLAYER_DISP = {
            0: (3, 2, 1),       # Spieler 1: DISP3, DISP2, DISP1
            1: (6, 5, 4),       # Spieler 2: DISP6, DISP5, DISP4
            2: (9, 8, 7),       # Spieler 3: DISP9, DISP8, DISP7
            3: (12, 11, 10),    # Spieler 4: DISP12, DISP11, DISP10
            4: (None, 14, 13),  # Spieler 5: (Hunderter fehlt oft), DISP14, DISP13
            5: (17, 16, 15),    # Spieler 6: DISP17, DISP16, DISP15
            6: (21, 20, 19),    # Spieler 7: DISP21, DISP20, DISP19
            7: (24, 23, 22)     # Spieler 8: DISP24, DISP23, DISP22
        }

    def set_light(self, state):
        if not self.ser: return
        try:
            cmd = b"LIGHT:ON\n" if state else b"LIGHT:OFF\n"
            self.ser.write(cmd)
            self.ser.flush()
        except: pass

    def set_raw_digit(self, disp_num, char):
        """Schreibt ein Zeichen DIREKT auf eine DISP-Nummer (1 bis 41)"""
        if disp_num not in self.DIGITS: return
        char = str(char).upper()
        if char not in self.FONT: return
        
        chip, col = self.DIGITS[disp_num]
        
        # Das komplette Byte für diese Ziffer überschreiben!
        self.buffer[chip][col] = self.FONT[char]

    def set_score(self, player_idx, score):
        """Übersetzt einen 3-stelligen Score auf die passenden DISP-Blöcke der Spieler"""
        if player_idx not in self.PLAYER_DISP: return
        score_str = f"{max(0, score):03d}"
        
        disp_h, disp_z, disp_e = self.PLAYER_DISP[player_idx]
        
        if disp_h: self.set_raw_digit(disp_h, score_str[0])
        if disp_z: self.set_raw_digit(disp_z, score_str[1])
        if disp_e: self.set_raw_digit(disp_e, score_str[2])

    def set_cricket_led(self, chip, col, bit, state):
        """Schaltet einzelne LEDs (z.B. Cricket) ohne die restlichen in der Spalte zu löschen"""
        if state:
            self.buffer[chip][col] |= (1 << bit)
        else:
            self.buffer[chip][col] &= ~(1 << bit)

    def clear_all(self):
        """Löscht das gesamte Display"""
        self.buffer = [[0 for _ in range(8)] for _ in range(9)]
        self.update()

    def update(self):
        """Sendet nur die Änderungen an den Arduino"""
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
