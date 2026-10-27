#!/bin/bash
# =====================================================================
# VisionPi2000 - Öffentliches UPDATE-Skript (Stable-Edition mit OverlayFS)
# Hauptnutzer: visionpi2000
# =====================================================================

# WICHTIG: Vorherige Dateileichen im tmp-Ordner (RAM) löschen!
rm -rf /tmp/VisionPiRepoUpdate

echo "Lade neueste Dateien vom stable-Branch in den RAM herunter..."
git clone --depth 1 -b stable https://github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# SICHERHEITS-CHECK: Wurde wirklich etwas heruntergeladen?
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Das Update wird abgebrochen."
    rm -rf /tmp/VisionPiRepoUpdate
    exit 1
fi

# Sounds direkt im schnellen RAM vorab generieren
echo "Generiere Sounds im RAM..."
cd /tmp/VisionPiRepoUpdate/VisionPi2000
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# Boot-Verzeichnis für settings.json ermitteln
BOOT_DIR="/boot/firmware"
if [ ! -d "$BOOT_DIR" ]; then BOOT_DIR="/boot"; fi

if [ ! -f "$BOOT_DIR/settings.json" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart"}' | sudo tee "$BOOT_DIR/settings.json" > /dev/null
    sudo chmod 666 "$BOOT_DIR/settings.json"
fi

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

# Schreibpuffer zwingend auf die SD-Karte leeren
sync

# Falls OverlayFS aktiv war, die echte SD-Karte sofort wieder verriegeln
if [ "$OVERLAY_ACTIVE" -eq 1 ]; then
    echo "Verriegle /media/root-ro wieder (Read-Only)..."
    sudo mount -o remount,ro /media/root-ro
fi

echo "========================================================================="
echo "Update erfolgreich! Permanent auf SD-Karte gespeichert."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
