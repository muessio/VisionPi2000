import wave
import struct
import math
import os

os.makedirs("sounds", exist_ok=True)

VERSION = "1.4.0"

def save_wav(filename, audio_data, sample_rate=44100):
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for s in audio_data:
            # Maximale Aussteuerung für richtig Druck (Sättigung)
            val = int(max(-1.0, min(1.0, s)) * 32767)
            f.writeframesraw(struct.pack('<h', val))

def generate_arcade_sounds():
    print(f"Generiere Sounds (VisionPi2000 Generator v{VERSION}) - Laut & Krass...")
    
    # 1. CLICK (Menü)
    click = []
    for i in range(int(44100 * 0.05)):
        t = i / 44100.0
        val = math.copysign(0.3, math.sin(2 * math.pi * 800 * t)) * math.exp(-t * 100)
        click.append(val)
    save_wav("sounds/click.wav", click)

    # 2. START
    start = []
    for freq in [440.0, 554.37, 659.25, 880.0]:
        for i in range(int(44100 * 0.1)):
            t = i / 44100.0
            start.append(math.copysign(0.3, math.sin(2 * math.pi * freq * t)))
    save_wav("sounds/start.wav", start)

    # 3. SPIELERWECHSEL
    switch_player = []
    for i in range(int(44100 * 0.12)):
        t = i / 44100.0
        freq = 900 - t * 300
        val = math.copysign(0.3, math.sin(2 * math.pi * freq * t)) * math.exp(-t * 20)
        switch_player.append(val)
    save_wav("sounds/switch_player.wav", switch_player)

    # 4. BUST / ÜBERWORFEN (Jetzt extrem krass, tief und brachial)
    bust = []
    for i in range(int(44100 * 0.35)):  # Länger für epischen Fail-Effekt
        t = i / 44100.0
        # Brutaler Frequenzabsturz von tiefem Bass in den Keller
        freq = max(30, 220 - (t * 500))
        # Aggressive Rechteckwelle + sub-harmonische Welle für maximalen Druck
        v1 = math.copysign(1.0, math.sin(2 * math.pi * freq * t))
        v2 = math.copysign(1.0, math.sin(2 * math.pi * (freq * 0.5) * t))
        val = (v1 * 0.7 + v2 * 0.5)
        # Langsamerer Hüllkurven-Abfall, damit der Sound richtig nachhallt und drückt
        envelope = math.exp(-t * 4)
        bust.append(val * envelope)
    save_wav("sounds/bust.wav", bust)

    # 5. MISS / FEHLWURF (Jetzt deutlich lauter und präsenter)
    miss = []
    for i in range(int(44100 * 0.25)):
        t = i / 44100.0
        freq1 = max(60, 180 - (t * 450))
        freq2 = max(50, 130 - (t * 350)) 
        
        # Volle Rechteck-Power für den Buzzer-Effekt
        v1 = math.copysign(1.0, math.sin(2 * math.pi * freq1 * t))
        v2 = math.copysign(1.0, math.sin(2 * math.pi * freq2 * t))
        
        # Höhere Amplitude (0.35 statt 0.2) für spürbar mehr Lautstärke
        val = (v1 + v2) * 0.35
        envelope = math.exp(-t * 6)
        miss.append(val * envelope)
    save_wav("sounds/miss.wav", miss)

    # 6. CHAMP / BULLSEYE FANFARE
    champ = []
    for i in range(int(44100 * 0.15)):
        champ.append(math.copysign(0.3, math.sin(2 * math.pi * 783.99 * (i / 44100.0))))
    for i in range(int(44100 * 0.05)): champ.append(0)
    for i in range(int(44100 * 0.8)):
        t = i / 44100.0
        champ.append(math.copysign(0.3, math.sin(2 * math.pi * 1046.50 * t)) * math.exp(-t * 3))
    save_wav("sounds/champ.wav", champ)

    # 7. HIT SINGLE
    hit_s = []
    for i in range(int(44100 * 0.08)):
        t = i / 44100.0
        val = math.copysign(0.25, math.sin(2 * math.pi * 350 * t)) * math.exp(-t * 40)
        hit_s.append(val)
    save_wav("sounds/hit_single.wav", hit_s)

    # 8. HIT DOUBLE
    hit_d = []
    for i in range(int(44100 * 0.1)):
        t = i / 44100.0
        val = math.copysign(0.3, math.sin(2 * math.pi * 600 * t)) * math.exp(-t * 30)
        hit_d.append(val)
    save_wav("sounds/hit_double.wav", hit_d)

    # 9. HIT TRIPLE
    hit_t = []
    for i in range(int(44100 * 0.12)):
        t = i / 44100.0
        freq = 500 + t * 2000
        val = math.copysign(0.35, math.sin(2 * math.pi * freq * t)) * math.exp(-t * 25)
        hit_t.append(val)
    save_wav("sounds/hit_triple.wav", hit_t)

    # 10. VICTORY / SIEGERMELODIE (Neu hinzugefügt)
    victory = []
    # Schnelles, aufsteigendes C-Dur Arpeggio (C5, E5, G5)
    for freq in [523.25, 659.25, 783.99]:
        for i in range(int(44100 * 0.12)):
            t = i / 44100.0
            victory.append(math.copysign(0.3, math.sin(2 * math.pi * freq * t)))
    # Langer, gehaltener C6 Schluss-Akkord
    for i in range(int(44100 * 1.2)):
        t = i / 44100.0
        val = math.copysign(0.3, math.sin(2 * math.pi * 1046.50 * t)) * math.exp(-t * 1.5)
        victory.append(val)
    save_wav("sounds/victory.wav", victory)

    print("\nAlle 10 Sounds (inklusive Siegermelodie) erfolgreich generiert!")

if __name__ == "__main__":
    generate_arcade_sounds()
    
