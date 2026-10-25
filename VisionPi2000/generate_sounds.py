import wave
import struct
import math
import os

os.makedirs("sounds", exist_ok=True)

def save_wav(filename, audio_data, sample_rate=44100):
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for s in audio_data:
            val = int(max(-1.0, min(1.0, s)) * 32767)
            f.writeframesraw(struct.pack('<h', val))

def generate_arcade_sounds():
    print("Generiere erweiterte Retro-Arcade Sounds...")
    
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

    # 3. SPIELERWECHSEL (Neuer, markanter Bestätigungston)
    switch_player = []
    for i in range(int(44100 * 0.12)):
        t = i / 44100.0
        freq = 900 - t * 300  # Abfallender Ton zur Bestätigung
        val = math.copysign(0.3, math.sin(2 * math.pi * freq * t)) * math.exp(-t * 20)
        switch_player.append(val)
    save_wav("sounds/switch_player.wav", switch_player)

    # 4. CHAMP / BULLSEYE FANFARE
    champ = []
    for i in range(int(44100 * 0.15)):
        champ.append(math.copysign(0.3, math.sin(2 * math.pi * 783.99 * (i / 44100.0))))
    for i in range(int(44100 * 0.05)): champ.append(0)
    for i in range(int(44100 * 0.8)):
        t = i / 44100.0
        champ.append(math.copysign(0.3, math.sin(2 * math.pi * 1046.50 * t)) * math.exp(-t * 3))
    save_wav("sounds/champ.wav", champ)

    # 5. HIT SINGLE
    hit_s = []
    for i in range(int(44100 * 0.08)):
        t = i / 44100.0
        val = math.copysign(0.25, math.sin(2 * math.pi * 350 * t)) * math.exp(-t * 40)
        hit_s.append(val)
    save_wav("sounds/hit_single.wav", hit_s)

    # 6. HIT DOUBLE
    hit_d = []
    for i in range(int(44100 * 0.1)):
        t = i / 44100.0
        val = math.copysign(0.3, math.sin(2 * math.pi * 600 * t)) * math.exp(-t * 30)
        hit_d.append(val)
    save_wav("sounds/hit_double.wav", hit_d)

    # 7. HIT TRIPLE
    hit_t = []
    for i in range(int(44100 * 0.12)):
        t = i / 44100.0
        freq = 500 + t * 2000
        val = math.copysign(0.35, math.sin(2 * math.pi * freq * t)) * math.exp(-t * 25)
        hit_t.append(val)
    save_wav("sounds/hit_triple.wav", hit_t)

    print("\nAlle Sounds erfolgreich generiert!")

if __name__ == "__main__":
    generate_arcade_sounds()
