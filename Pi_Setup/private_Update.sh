#!/bin/bash
# =====================================================================
# VisionPi2000 - Update-Skript für FAT32 Boot-Partition
# =====================================================================

if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  exit 1
fi

if ! command -v git &> /dev/null; then
    sudo apt update && sudo apt install git -y
fi

# Zielverzeichnis auf der Boot-Partition ermitteln
if [ -d "/boot/firmware" ]; then 
    BOOT_DIR="/boot/firmware/VisionPi2000" 
else 
    BOOT_DIR="/boot/VisionPi2000" 
fi

rm -rf /tmp/VisionPiRepoUpdate
echo "Lade neueste Dateien von GitHub herunter..."
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# Prüfen, ob der Projekt-Unterordner existiert
if [ -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    SRC_DIR="/tmp/VisionPiRepoUpdate/VisionPi2000"
else
    SRC_DIR="/tmp/VisionPiRepoUpdate"
fi

echo "Aktualisiere den Zielordner..."
sudo mkdir -p "$BOOT_DIR"
sudo rm -rf "$BOOT_DIR"/*
sudo cp -r "$SRC_DIR"/* "$BOOT_DIR"/
rm -rf /tmp/VisionPiRepoUpdate

# Sounds direkt im Zielverzeichnis generieren
echo "Generiere Sounds..."
cd "$BOOT_DIR"
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
else
    echo "Warnung: generate_sounds.py nicht gefunden!"
fi

echo "========================================================================="
echo "Update erfolgreich! Das System wird in 3 Sekunden neu gestartet..."
echo "========================================================================="
sleep 3
sudo reboot
