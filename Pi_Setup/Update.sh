#!/bin/bash
# =====================================================================
# VisionPi2000 - Öffentliches UPDATE-Skript (Mit Boot-Partition MQTT-Fallback)
# Hauptnutzer: visionpi2000
# =====================================================================

# WICHTIG: Vorherige Dateileichen im tmp-Ordner (RAM) löschen!
rm -rf /tmp/VisionPiRepoUpdate

echo "Lade neueste Dateien von GitHub in den RAM herunter..."
git clone --depth 1 https://github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# SICHERHEITS-CHECK: Wurde wirklich etwas heruntergeladen?
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Das Update wird abgebrochen."
    rm -rf /tmp/VisionPiRepoUpdate
    exit 1
fi

# Boot-Verzeichnis ermitteln
BOOT_DIR="/boot/firmware"
if [ ! -d "$BOOT_DIR" ]; then BOOT_DIR="/boot"; fi

if [ ! -f "$BOOT_DIR/settings.json" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart", "branch": "stable", "mqtt_broker": "broker.emqx.io"}' | sudo tee "$BOOT_DIR/settings.json" > /dev/null
    sudo chmod 666 "$BOOT_DIR/settings.json"
fi

# =====================================================================
# MQTT-FALLBACK DIREKT AUF DER BOOT-PARTITION (Läuft immer garantiert!)
# =================python3-paho-mqtt lokal vorbereiten=================
if ! python3 -c "import paho.mqtt.client" >/dev/null 2>&1; then
    echo "paho-mqtt Modul nicht im System gefunden. Installiere es direkt auf der Boot-Partition..."
    sudo mkdir -p "$BOOT_DIR/python_libs"
    # Wir laden das paho-mqtt Paket via pip direkt in den offenen Boot-Ordner herunter
    sudo pip3 install paho-mqtt --target="$BOOT_DIR/python_libs" --no-deps >/dev/null 2>&1
    
    # Python-Pfad dauerhaft für den Benutzer in der .bashrc oder Umgebung hinterlegen
    if ! grep -q "python_libs" /home/visionpi2000/.bashrc; then
        echo 'export PYTHONPATH="$PYTHONPATH:/boot/firmware/python_libs"' >> /home/visionpi2000/.bashrc
        echo 'export PYTHONPATH="$PYTHONPATH:/boot/python_libs"' >> /home/visionpi2000/.bashrc
    fi
fi

# Sounds direkt im schnellen RAM vorab generieren
echo "Generiere Sounds im RAM..."
cd /tmp/VisionPiRepoUpdate/VisionPi2000
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
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
echo "Update & MQTT-Fallback erfolgreich eingerichtet!"
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
