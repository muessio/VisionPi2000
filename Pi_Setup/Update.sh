#!/bin/bash
# =====================================================================
# VisionPi2000 - Öffentliches UPDATE-Skript (Debian Trixie & OverlayFS)
# Inkl. rückwirkender RAM-, WLAN- & Systemdienst-Optimierung für Bestandsautomaten
# Hauptnutzer: visionpi2000
# =====================================================================

# 1. Vorherige Dateileichen im tmp-Ordner (RAM) bereinigen
rm -rf /tmp/VisionPiRepoUpdate
rm -rf /tmp/paho_temp
rm -rf /tmp/qrcode_temp

# 2. Neueste Spieldateien von GitHub (stable) in den RAM herunterladen
echo "Lade neueste Dateien von GitHub (Zweig: stable) in den RAM herunter..."
git clone --branch stable --depth 1 https://github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Das Update wird abgebrochen."
    rm -rf /tmp/VisionPiRepoUpdate
    exit 1
fi

# 3. paho-mqtt direkt als reines Python-Modul einbetten
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000/paho" ]; then
    echo "Bette paho-mqtt Bibliothek direkt in das Spielverzeichnis ein..."
    mkdir -p /tmp/paho_temp
    git clone --depth 1 https://github.com/eclipse-paho/paho.mqtt.python.git /tmp/paho_temp
    if [ -d "/tmp/paho_temp/src/paho" ]; then
        cp -r /tmp/paho_temp/src/paho /tmp/VisionPiRepoUpdate/VisionPi2000/paho
        echo "paho-mqtt erfolgreich eingebettet!"
    else
        echo "WARNUNG: Konnte paho-mqtt nicht von GitHub laden."
    fi
    rm -rf /tmp/paho_temp
fi

# 4. qrcode direkt als reines Python-Modul einbetten
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000/qrcode" ]; then
    echo "Bette qrcode Bibliothek direkt in das Spielverzeichnis ein..."
    mkdir -p /tmp/qrcode_temp
    git clone --depth 1 https://github.com/lincolnloop/python-qrcode.git /tmp/qrcode_temp
    if [ -d "/tmp/qrcode_temp/qrcode" ]; then
        cp -r /tmp/qrcode_temp/qrcode /tmp/VisionPiRepoUpdate/VisionPi2000/qrcode
        echo "qrcode erfolgreich eingebettet!"
    else
        echo "WARNUNG: Konnte qrcode nicht von GitHub laden."
    fi
    rm -rf /tmp/qrcode_temp
fi

# 5. Sounds im RAM vorab generieren
echo "Generiere Sounds im RAM..."
cd /tmp/VisionPiRepoUpdate/VisionPi2000
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# 6. Boot-Verzeichnis für settings.json ermitteln
BOOT_DIR="/boot/firmware"
if [ ! -d "$BOOT_DIR" ]; then BOOT_DIR="/boot"; fi

if [ ! -f "$BOOT_DIR/settings.json" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart", "branch": "stable", "mqtt_broker": "broker.emqx.io"}' | sudo tee "$BOOT_DIR/settings.json" > /dev/null
    sudo chmod 666 "$BOOT_DIR/settings.json"
fi

# 7. Prüfen, ob das System im OverlayFS-Modus läuft, und kurzzeitig entsperren
if mountpoint -q /media/root-ro; then
    echo "OverlayFS erkannt! Öffne /media/root-ro kurzzeitig zum Schreiben..."
    sudo mount -o remount,rw /media/root-ro
    if [ $? -ne 0 ]; then
        echo "FEHLER: Konnte /media/root-ro nicht entsperren!"
        rm -rf /tmp/VisionPiRepoUpdate
        exit 1
    fi
    SYS_ROOT="/media/root-ro"
    TARGET_DIR="/media/root-ro/home/visionpi2000/VisionPi2000"
    OVERLAY_ACTIVE=1
else
    echo "Standard-Dateisystem erkannt. Schreibe direkt..."
    SYS_ROOT=""
    TARGET_DIR="/home/visionpi2000/VisionPi2000"
    OVERLAY_ACTIVE=0
fi

# 8. WLAN global einschalten, falls es durch den Status 'unavailable' blockiert wurde
echo "Aktiviere WLAN-Funkschnittstelle..."
sudo nmcli radio wifi on

# 9. Prüfen und ggf. WPS-Dummy-Profil bei Bestandsautomaten nachrüsten
EXISTING_WIFI=$(sudo chroot "${SYS_ROOT:-/}" nmcli -t -f TYPE,NAME connection show 2>/dev/null | grep "^wireless" | head -n 1)
if [ -z "$EXISTING_WIFI" ]; then
    echo "[INFO] Bestandsautomat hat kein WLAN-Profil. Trage WPS-Dummy-Profil ein..."
    if [ "$OVERLAY_ACTIVE" -eq 1 ]; then
        sudo chroot /media/root-ro nmcli connection add type wifi ifname wlan0 con-name "VisionPi-Setup" ssid "VisionPi-Setup" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "DummyPassword12345678" autoconnect no 2>/dev/null
    else
        sudo nmcli connection add type wifi ifname wlan0 con-name "VisionPi-Setup" ssid "VisionPi-Setup" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "DummyPassword12345678" autoconnect no 2>/dev/null
    fi
    echo "[INFO] WPS-Dummy-Profil erfolgreich nachgerüstet."
else
    echo "[INFO] WLAN-Profil bereits vorhanden: $(echo "$EXISTING_WIFI" | cut -d: -f2)"
fi

# 10. Spieldateien auf dem Zielsystem aktualisieren
echo "Aktualisiere Spieldateien in $TARGET_DIR..."
sudo mkdir -p "$TARGET_DIR"
sudo rm -rf "$TARGET_DIR"/*
sudo cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* "$TARGET_DIR"/

# 11. Symlink zur settings.json auf der Boot-Partition wiederherstellen
sudo rm -f "$TARGET_DIR/settings.json"
sudo ln -s "$BOOT_DIR/settings.json" "$TARGET_DIR/settings.json"

# 12. Dateiberechtigungen auf dem Zielsystem glattziehen
sudo chown -R visionpi2000:visionpi2000 "$TARGET_DIR"

# 13. System-Optimierungen permanent nachrüsten (Journal, WLAN-Powersave, Dienste)
echo "Wende RAM-, Journal- und WLAN-Optimierungen dauerhaft auf das System an..."

# 13.1 Systemd-Journal im RAM auf max. 16 MB deckeln
sudo mkdir -p "${SYS_ROOT}/etc/systemd/journald.conf.d"
cat << 'EOF' | sudo tee "${SYS_ROOT}/etc/systemd/journald.conf.d/size-limit.conf" > /dev/null
[Journal]
Storage=volatile
RuntimeMaxUse=16M
RuntimeMaxFileSize=4M
EOF

# 13.2 WLAN-Powersave dauerhaft abschalten
sudo mkdir -p "${SYS_ROOT}/etc/NetworkManager/conf.d"
cat << 'EOF' | sudo tee "${SYS_ROOT}/etc/NetworkManager/conf.d/default-wifi-powersave-off.conf" > /dev/null
[connection]
wifi.powersave = 2
EOF

# 13.3 Unnötige Hintergrunddienste permanent deaktivieren
UNUSED_SERVICES=(
    "bluetooth.service"
    "hciuart.service"
    "ModemManager.service"
    "avahi-daemon.service"
    "avahi-daemon.socket"
    "cups.service"
    "cups-browsed.service"
    "triggerhappy.service"
    "triggerhappy.socket"
    "apt-daily.timer"
    "apt-daily-upgrade.timer"
    "man-db.timer"
)

if [ "$OVERLAY_ACTIVE" -eq 1 ]; then
    for svc in "${UNUSED_SERVICES[@]}"; do
        sudo chroot /media/root-ro systemctl disable "$svc" 2>/dev/null
    done
else
    for svc in "${UNUSED_SERVICES[@]}"; do
        sudo systemctl stop "$svc" 2>/dev/null
        sudo systemctl disable "$svc" 2>/dev/null
    done
fi

# 14. Aufräumen und Schreibpuffer auf SD-Karte leeren
rm -rf /tmp/VisionPiRepoUpdate
sync

# 15. Falls OverlayFS aktiv war, Partition wieder verriegeln (Read-Only)
if [ "$OVERLAY_ACTIVE" -eq 1 ]; then
    echo "Verriegle /media/root-ro wieder (Read-Only)..."
    sudo mount -o remount,ro /media/root-ro
fi

echo "========================================================================="
echo "Update & System-Optimierung erfolgreich! Permanent auf SD-Karte gespeichert."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
