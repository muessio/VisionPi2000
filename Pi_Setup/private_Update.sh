#!/bin/bash
# =====================================================================
# VisionPi2000 - Privates UPDATE-Skript (Standard-Edition mit OverlayFS)
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

echo "Download erfolgreich. Bereite OverlayFS-Durchgriff vor..."

# 1. DIE MAGIE: Echte SD-Karte unter der Overlay-Glocke kurz aufschließen!
sudo mount -o remount,rw /media/root-ro

if [ $? -ne 0 ]; then
    echo "FEHLER: Konnte /media/root-ro nicht im Schreibmodus einhängen!"
    rm -rf /tmp/VisionPiRepoUpdate
    exit 1
fi

echo "Aktualisiere den VisionPi2000 Ordner auf der echten SD-Karte..."

# 2. Alten Inhalt auf der echten SD-Karte komplett löschen
sudo rm -rf /media/root-ro/home/visionpi2000/VisionPi2000/*

# 3. Den frisch heruntergeladenen Inhalt kopieren
sudo cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* /media/root-ro/home/visionpi2000/VisionPi2000/

# 4. Danach direkt wieder im RAM aufräumen
rm -rf /tmp/VisionPiRepoUpdate

# Sounds direkt für das Zielsystem generieren oder kopieren
echo "Prüfe und generiere ggf. neue Sounds..."
cd /media/root-ro/home/visionpi2000/VisionPi2000
sudo python3 generate_sounds.py

# Dateiberechtigungen glattziehen
sudo chown -R visionpi2000:visionpi2000 /media/root-ro/home/visionpi2000/VisionPi2000

# 5. Schreibpuffer leeren und echte SD-Karte sofort wieder verriegeln (ro)
sync
sudo mount -o remount,ro /media/root-ro

echo "========================================================================="
echo "Update erfolgreich! Alle Dateien wurden auf den neuesten Stand gebracht."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
