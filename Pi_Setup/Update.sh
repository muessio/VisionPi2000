#!/bin/bash
# =====================================================================
# VisionPi2000 - Öffentliches Update-Skript (FAT32 Boot-Partition-Modus)
# =====================================================================

if ! command -v git &> /dev/null; then
    sudo apt update && sudo apt install git -y
fi

# Zielverzeichnis auf der dauerhaft beschreibbaren Boot-Partition ermitteln
BOOT_DIR="/boot/firmware/VisionPi2000"
if [ ! -d "/boot/firmware" ]; then BOOT_DIR="/boot/VisionPi2000"; fi

rm -rf /tmp/VisionPiRepoUpdate
echo "Lade neueste Dateien von GitHub herunter..."
git clone https://github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen!"
    exit 1
fi

echo "Aktualisiere den VisionPi2000 Ordner auf der Boot-Partition..."
sudo mkdir -p "$BOOT_DIR"
sudo rm -rf "$BOOT_DIR"/*
sudo cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* "$BOOT_DIR"/
rm -rf /tmp/VisionPiRepoUpdate

# settings.json direkt sichern (ohne fehlerhafte Symlinks auf FAT32)
SETTINGS_BOOT="/boot/firmware/settings.json"
if [ ! -d "/boot/firmware" ]; then SETTINGS_BOOT="/boot/settings.json"; fi

if [ ! -f "$SETTINGS_BOOT" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart"}' | sudo tee "$SETTINGS_BOOT" > /dev/null
fi
sudo cp "$SETTINGS_BOOT" "$BOOT_DIR/settings.json"

# Sounds im neuen Ordner generieren (direkt am Zielort)
echo "Generiere Sounds..."
cd "$BOOT_DIR"
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# Hinweis: chown auf der FAT32-Boot-Partition entfernt (verursacht keine Fehler mehr)

echo "========================================================================="
echo "Update erfolgreich! Permanent auf SD-Karte gespeichert."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
