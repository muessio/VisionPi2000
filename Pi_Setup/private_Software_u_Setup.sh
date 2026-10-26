#!/bin/bash
# =====================================================================
# VisionPi2000 - Permanentes Update über die beschreibbare Boot-Partition
# Hauptnutzer: visionpi2000
# =====================================================================

if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  exit 1
fi

if ! command -v git &> /dev/null; then
    sudo apt update && sudo apt install git -y
fi

# Zielverzeichnis auf der Boot-Partition ermitteln
if [ -d "/boot/firmware" ]; then BOOT_DIR="/boot/firmware/VisionPi2000"; else BOOT_DIR="/boot/VisionPi2000"; fi

rm -rf /tmp/VisionPiRepoUpdate
echo "Lade neueste Dateien von GitHub herunter..."
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# Prüfen, ob der Projekt-Unterordner existiert
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen oder VisionPi2000-Ordner nicht gefunden!"
    exit 1
fi

echo "Aktualisiere den VisionPi2000 Ordner auf der Boot-Partition..."
sudo mkdir -p "$BOOT_DIR"
sudo rm -rf "$BOOT_DIR"/*

# Inhalt aus dem Unterordner direkt in den Zielordner kopieren
sudo cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* "$BOOT_DIR"/
rm -rf /tmp/VisionPiRepoUpdate

# Sounds im neuen Ordner generieren und Verzeichnis absichern
echo "Generiere Sounds..."
cd "$BOOT_DIR"
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
else
    echo "Warnung: generate_sounds.py nicht gefunden!"
fi

echo "========================================================================="
echo "Update erfolgreich! Permanent auf SD-Karte gespeichert."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
