# Datei: display_mapper.py
import time

class LoewenDisplay:
    def __init__(self, ser):
        self.ser = ser
        # 10 logische Chips im Arduino (5 Stränge à 2 Chips: 0..9)
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        self.last_sent = [[-1 for _ in range(8)] for _ in range(10)]

        # Standard 7-Segment Definition: Welche Segmente leuchten für welches Zeichen?
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

        # -------------------------------------------------------------------
        # HARDWARE-ÜBERSETZUNG MAX7219 (aus Schaltplan Blatt 1-3):
        #
        # 1. CHIP-INDEX IM ARDUINO (chain = chip / 2, chipIdx = chip % 2):
        #    Strang D0 (Pin 6):  U1 = Chip 0, U3 = Chip 1
        #    Strang D1 (Pin 7):  U2 = Chip 2, U4 = Chip 3
        #    Strang D2 (Pin 8):  U5 = Chip 4, U6 = Chip 5
        #    Strang D3 (Pin 9):  U7 = Chip 6, U8 = Chip 7
        #    Strang D4 (Pin 10): U9 = Chip 8 (Einzelchip am Strang -> im Arduino trotzdem über 8 & 9 gespiegelt)
        #
        # 2. SPALTEN A bis H -> MAX7219 DIG-Pins (0 bis 7):
        #    A(Pin 6)  = DIG2 -> digit 2
        #    B(Pin 5)  = DIG6 -> digit 6
        #    C(Pin 10) = DIG5 -> digit 5
        #    D(Pin 3)  = DIG4 -> digit 4
        #    E(Pin 7)  = DIG3 -> digit 3
        #    F(Pin 8)  = DIG7 -> digit 7
        #    G(Pin 11) = DIG1 -> digit 1
        #    H(Pin 2)  = DIG0 -> digit 0
        #
        # 3. ZEILEN 1 bis 8 -> MAX7219 SEG-Pins (Bit 0 bis 7 im Datenbyte):
        #    Row 1 (Pin 22 = SEG DP) -> Bit 7
        #    Row 2 (Pin 17 = SEG G)  -> Bit 0
        #    Row 3 (Pin 15 = SEG B)  -> Bit 5
        #    Row 4 (Pin 21 = SEG E)  -> Bit 2
        #    Row 5 (Pin 23 = SEG D)  -> Bit 3
        #    Row 6 (Pin 20 = SEG C)  -> Bit 4
        #    Row 7 (Pin 16 = SEG F)  -> Bit 1
        #    Row 8 (Pin 14 = SEG A)  -> Bit 6
        # -------------------------------------------------------------------

        self.COL_TO_DIGIT = {
            "A": 2, "B": 6, "C": 5, "D": 4, "E": 3, "F": 7, "G": 1, "H": 0
        }

        self.ROW_TO_BIT = {
            1: 7, 2: 0, 3: 5, 4: 2, 5: 3, 6: 4, 7: 1, 8: 6
        }

        # Exakte Segment-Reihenfolge (Zeile 1 bis 8) für die verschiedenen Chip-Gruppen laut Blatt 3:
        # Typ 1 (U1, U6_D22..24): Row1=F, Row2=G, Row3=D, Row4=E, Row5=A, Row6=B, Row7=C, Row8=DP
        SEG_ORDER_U1 = { "F": 1, "G": 2, "D": 3, "E": 4, "A": 5, "B": 6, "C": 7, "DP": 8 }
        # Typ 2 (U2): Row1=C, Row2=B, Row3=F, Row4=E, Row5=A, Row6=G, Row7=D, Row8=DP
        SEG_ORDER_U2 = { "C": 1, "B": 2, "F": 3, "E": 4, "A": 5, "G": 6, "D": 7, "DP": 8 }
        # Typ 3 (U3): Row1=E, Row2=B, Row3=C, Row4=A, Row5=D, Row6=F, Row7=G, Row8=DP
        SEG_ORDER_U3 = { "E": 1, "B": 2, "C": 3, "A": 4, "D": 5, "F": 6, "G": 7, "DP": 8 }
        # Typ 4 (U4): Row1=B, Row2=DP, Row3=E, Row4=F, Row5=A, Row6=G, Row7=C, Row8=D
        SEG_ORDER_U4 = { "B": 1, "DP": 2, "E": 3, "F": 4, "A": 5, "G": 6, "C": 7, "D": 8 }
        # Typ 5 (U5 & U6): Row1=B, Row2=DP, Row3=D, Row4=F, Row5=A, Row6=G, Row7=C, Row8=E
        SEG_ORDER_U5_U6 = { "B": 1, "DP": 2, "D": 3, "F": 4, "A": 5, "G": 6, "C": 7, "E": 8 }
        # Typ 6 (U7): Row1=E, Row2=C, Row3=B, Row4=F, Row5=A, Row6=G, Row7=D, Row8=DP
        SEG_ORDER_U7 = { "E": 1, "C": 2, "B": 3, "F": 4, "A": 5, "G": 6, "D": 7, "DP": 8 }
        # Typ 7 (U8): Row1=F, Row2=C, Row3=DP, Row4=E, Row5=A, Row6=B, Row7=D, Row8=G
        SEG_ORDER_U8 = { "F": 1, "C": 2, "DP": 3, "E": 4, "A": 5, "B": 6, "D": 7, "G": 8 }
        # Typ 8 (U9): Row1=A, Row2=C, Row3=D, Row4=F, Row5=E, Row6=G, Row7=DP, Row8=B
        SEG_ORDER_U9 = { "A": 1, "C": 2, "D": 3, "F": 4, "E": 5, "G": 6, "DP": 7, "B": 8 }

        # Definition aller 41 DISP-Ziffern: DISP_NR: (Chip_ID, Spaltenbuchstabe, Segment_Reihenfolge)
        self.DISP_TABLE = {
            # U1 (Chip 0)
            1: (0, "H", SEG_ORDER_U1),
            2: (0, "D", SEG_ORDER_U1),
            3: (0, "B", SEG_ORDER_U1),
            7: (0, "F", SEG_ORDER_U1),
            8: (0, "E", SEG_ORDER_U1),
            9: (0, "A", SEG_ORDER_U1),
            # U3 (Chip 1)
            10: (1, "H", SEG_ORDER_U3),
            11: (1, "D", SEG_ORDER_U3),
            12: (1, "B", SEG_ORDER_U3),
            13: (1, "E", SEG_ORDER_U3),
            14: (1, "A", SEG_ORDER_U3),
            # U2 (Chip 2)
            4: (2, "F", SEG_ORDER_U2),
            5: (2, "A", SEG_ORDER_U2),
            6: (2, "C", SEG_ORDER_U2),
            15: (2, "G", SEG_ORDER_U2),
            # U4 (Chip 3)
            16: (3, "D", SEG_ORDER_U4),
            17: (3, "A", SEG_ORDER_U4),
            18: (3, "E", SEG_ORDER_U4),
            # U5 (Chip 4)
            19: (4, "B", SEG_ORDER_U5_U6),
            20: (4, "F", SEG_ORDER_U5_U6),
            21: (4, "E", SEG_ORDER_U5_U6),
            # U6 (Chip 5)
            22: (5, "B", SEG_ORDER_U5_U6),
            23: (5, "F", SEG_ORDER_U5_U6),
            24: (5, "E", SEG_ORDER_U5_U6),
            # U7 (Chip 6)
            25: (6, "H", SEG_ORDER_U7),
            26: (6, "B", SEG_ORDER_U7),
            27: (6, "E", SEG_ORDER_U7),
            30: (6, "A", SEG_ORDER_U7),
            # U8 (Chip 7)
            31: (7, "D", SEG_ORDER_U8),
            32: (7, "B", SEG_ORDER_U8),
            36: (7, "E", SEG_ORDER_U8),
            37: (7, "F", SEG_ORDER_U8),
            38: (7, "G", SEG_ORDER_U8),
            # U9 (Chip 8 & 9, da U9 allein an D4 hängt, spiegeln wir auf 8 und 9)
            28: (8, "E", SEG_ORDER_U9),
            29: (8, "F", SEG_ORDER_U9),
            33: (8, "C", SEG_ORDER_U9),
            34: (8, "D", SEG_ORDER_U9),
            35: (8, "B", SEG_ORDER_U9),
            39: (8, "H", SEG_ORDER_U9),
            40: (8, "G", SEG_ORDER_U9),
            41: (8, "A", SEG_ORDER_U9),
        }

        # Zuordnung der 8 Spieler-Anzeigen (Hunderter, Zehner, Einer) zu den DISP-Nummern
        self.PLAYER_DISP = {
            0: (1, 2, 3),     # Spieler 1
            1: (4, 5, 6),     # Spieler 2
            2: (7, 8, 9),     # Spieler 3
            3: (10, 11, 12),  # Spieler 4
            4: (13, 14, 15),  # Spieler 5
            5: (16, 17, 18),  # Spieler 6
            6: (19, 20, 21),  # Spieler 7
            7: (22, 23, 24)   # Spieler 8
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
        """Berechnet das exakte Bitmuster für eine DISP-Ziffer (1..41) und schreibt es in den Puffer."""
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
        # Da U9 allein am Strang D4 hängt (kein zweiter kaskadierter Chip),
        # schreiben wir sicherheitshalber denselben Wert in Chip 8 und 9:
        if chip == 8:
            self.buffer[9][digit_idx] = byte_val

    def set_score(self, player_idx, score):
        """Schreibt den 3-stelligen Score eines Spielers (0..7) ohne führende Nullen."""
        if player_idx not in self.PLAYER_DISP:
            return
        score = max(0, min(999, int(score)))
        score_str = f"{score:3d}"  # Rechtsbündig mit Leerzeichen statt führender Nullen (z.B. " 40")

        d_hund, d_ten, d_unit = self.PLAYER_DISP[player_idx]
        self.set_disp_char(d_hund, score_str[0])
        self.set_disp_char(d_ten,  score_str[1])
        self.set_disp_char(d_unit, score_str[2])

    def set_temp_score(self, score):
        """Schreibt auf die grüne 3-stellige TEMP SCORE Anzeige oben rechts (DISP 25, 26, 27)."""
        score = max(0, min(999, int(score)))
        score_str = f"{score:3d}"
        self.set_disp_char(25, score_str[0])
        self.set_disp_char(26, score_str[1])
        self.set_disp_char(27, score_str[2])

    def set_led_matrix(self, chip, col_letter, row_num, state):
        """Schaltet gezielt eine einzelne LED (z.B. Pfeil-LEDs, Cricket-LEDs, Spieler-LEDs)."""
        if col_letter not in self.COL_TO_DIGIT or row_num not in self.ROW_TO_BIT:
            return
        digit_idx = self.COL_TO_DIGIT[col_letter]
        bit_pos = self.ROW_TO_BIT[row_num]
        if state:
            self.buffer[chip][digit_idx] |= (1 << bit_pos)
        else:
            self.buffer[chip][digit_idx] &= ~(1 << bit_pos)
        if chip == 8:
            self.buffer[9][digit_idx] = self.buffer[8][digit_idx]

    def clear_all(self):
        """Löscht alle Anzeigen garantiert und synchronisiert den Arduino."""
        self.buffer = [[0 for _ in range(8)] for _ in range(10)]
        if not self.ser: return
        for chip in range(10):
            for digit in range(8):
                try:
                    self.ser.write(f"RAW:{chip}:{digit}:0\n".encode('ascii'))
                    self.ser.flush()
                    self.last_sent[chip][digit] = 0
                    time.sleep(0.006)
                except: pass

    def update(self):
        """Sendet nur geänderte Register mit ausreichend Pause für den Arduino."""
        if not self.ser: return
        for chip in range(10):
            for digit in range(8):
                val = self.buffer[chip][digit]
                if val != self.last_sent[chip][digit]:
                    try:
                        self.ser.write(f"RAW:{chip}:{digit}:{val}\n".encode('ascii'))
                        self.ser.flush()
                        self.last_sent[chip][digit] = val
                        time.sleep(0.008)  # 8ms Pause verhindert Buffer-Overflow im Arduino!
                    except: pass
