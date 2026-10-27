#!/bin/bash
# =====================================================================
# VisionPi2000 - Privates UPDATE-Skript (Intelligenter OverlayFS-Durchgriff)
# Hauptnutzer: visionpi2000
# =====================================================================

if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Starten mit: sudo ./private_Update.sh DEIN_TOKEN"
  exit 1
fi

# WICHTIG: Vorherige Dateileichen im tmp-Ordner (RAM) löschen!
rm -rf /tmp/VisionPiRepoUpdate

echo "Lade neueste Dateien von GitHub in den RAM herunter..."
git clone --depth 1 https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# SICHERHEITS-CHECK: Wurde wirklich etwas heruntergeladen?
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Das Update wird abgebrochen."
    rm -rf /tmp/VisionPiRepoUpdate
    exit 1
fi

# Sounds direkt im schnellen RAM vorab generieren
echo "Generiere Sounds im RAM..."
cd /tmp/VisionPiRepoUpdate/VisionPi2000
python3 generate_sounds.py

# Boot-Verzeichnis für settings.json ermitteln
BOOT_DIR="/boot/firmware"
if [ ! -d "$BOOT_DIR" ]; then BOOT_DIR="/boot"; fi

# PRÜFUNG: Ist das System im OverlayFS-Modus (/media/root-ro existiert) oder offen?
if mountpoint -q /media/root-ro; then
    echo "OverlayFS erkannt! Öffne /media/root-ro kurzzeitig zum Schreiben..."
    sudo mount -o remount,rw /media/root-ro
    if [ $? -ne 0 ]; then
        echo "FEHLER: Konnte /media/root-ro nicht entsperren!"
        rm -rf /tmp/VisionPiRepoUpdate
        exit 1
    fi
    TARGET_DIR="/media/root-ro/home/visionpi2000/VisionPi2000"
    OVERLAY_ACTIVE=1
else
    echo "Standard-Dateisystem erkannt. Schreibe direkt..."
    TARGET_DIR="/home/visionpi2000/VisionPi2000"
    OVERLAY_ACTIVE=0
fi

echo "Aktualisiere Spieldateien in $TARGET_DIR..."
sudo mkdir -p "$TARGET_DIR"
sudo rm -rf "$TARGET_DIR"/*
sudo cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* "$TARGET_DIR"/

# Symlink zur settings.json auf der Boot-Partition wiederherstellen
sudo rm -f "$TARGET_DIR/settings.json"
sudo ln -s "$BOOT_DIR/settings.json" "$TARGET_DIR/settings.json"

# Dateiberechtigungen auf dem Zielsystem glattziehen
sudo chown -R visionpi2000:visionpi2000 "$TARGET_DIR"

# RAM aufräumen
rm -rf /tmp/VisionPiRepoUpdate

# Schreibpuffer zwingend auf die SD-Karte leeren und kurz warten, damit keine Datei mehr blockiert ist
sync
sleep 2

# Falls OverlayFS aktiv war, die echte SD-Karte wieder verriegeln
if [ "$OVERLAY_ACTIVE" -eq 1 ]; then
    echo "Verriegle /media/root-ro wieder (Read-Only)..."
    sudo mount -o remount,ro /media/root-ro || true
fi

echo "========================================================================="
echo "Update erfolgreich! Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
