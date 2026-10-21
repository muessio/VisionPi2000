#!/bin/bash
# =====================================================================
# VisionPi2000 - Privates UPDATE-Skript (Ordner exakt spiegeln)
# Hauptnutzer: visionpi2000
# =====================================================================

# Prüfen, ob ein Token übergeben wurde
if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Das Skript muss mit einem Token gestartet werden: sudo ./private_Update.sh DEIN_TOKEN"
  exit 1
fi

# Vorher prüfen, ob git überhaupt installiert ist (falls nicht, installieren)
if ! command -v git &> /dev/null; then
    echo "Git ist nicht installiert. Installiere Git..."
    sudo apt update && sudo apt install git -y
fi

# WICHTIG: Vorherige Dateileichen im tmp-Ordner zwingend löschen!
rm -rf /tmp/VisionPiRepoUpdate

echo "Lade neueste Dateien von GitHub herunter..."

# Temporär das komplette Repository in den tmp-Ordner laden
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# SICHERHEITS-CHECK: Wurde wirklich etwas heruntergeladen?
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Das Update wird abgebrochen, um deine Dateien zu schützen."
    exit 1
fi

echo "Download erfolgreich. Aktualisiere den VisionPi2000 Ordner..."

# 1. Alten Inhalt auf dem Pi komplett löschen
rm -rf /home/visionpi2000/VisionPi2000/*

# 2. Den frisch heruntergeladenen Inhalt kopieren
cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* /home/visionpi2000/VisionPi2000/

# 3. Danach direkt wieder aufräumen
rm -rf /tmp/VisionPiRepoUpdate

# Sounds neu generieren
echo "Prüfe und generiere ggf. neue Sounds..."
cd /home/visionpi2000/VisionPi2000
python3 generate_sounds.py

# Dateiberechtigungen wieder glattziehen
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/VisionPi2000

echo "========================================================================="
echo "Update erfolgreich! Alle Dateien wurden auf den neuesten Stand gebracht."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
