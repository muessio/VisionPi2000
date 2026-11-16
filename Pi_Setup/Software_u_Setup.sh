#!/bin/bash
# =====================================================================
# VisionPi2000 - Öffentliches Master Installations- und Setup-Skript
# (Standard-Edition mit automatischem OverlayFS-Schreibschutz & MQTT Online)
# Hauptnutzer: visionpi2000
# =====================================================================

# 1. Paketlisten aktualisieren
sudo apt update

# 2. Sudo-Passwortabfrage für den Benutzer visionpi2000 deaktivieren
echo "Konfiguriere passwortlose Sudo-Rechte für visionpi2000..."
echo "visionpi2000 ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/visionpi2000
sudo chmod 0440 /etc/sudoers.d/visionpi2000

# 3. WPS-Dummy-Profil anlegen, falls noch kein WLAN konfiguriert ist
EXISTING_WIFI=$(nmcli -t -f TYPE,NAME connection show | grep "^wireless" | head -n 1)
if [ -z "$EXISTING_WIFI" ]; then
    echo "[INFO] Kein WLAN-Profil im System gefunden. Lege Dummy-Profil für WPS-Kopplung an..."
    sudo nmcli connection add type wifi ifname wlan0 con-name "VisionPi-Setup" ssid "VisionPi-Setup" \
        wifi-sec.key-mgmt wpa-psk \
        wifi-sec.psk "DummyPassword12345678" \
        autoconnect no
    echo "[INFO] Dummy-Profil erfolgreich erstellt."
else
    echo "[INFO] WLAN-Profil bereits vorhanden: $(echo "$EXISTING_WIFI" | cut -d: -f2)"
fi

# 4. USB-Stromlimit, Energiesparmodus & GPU-RAM in der Boot-Config anpassen
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ] && [ -f "/boot/config.txt" ]; then
    CONFIG_FILE="/boot/config.txt"
fi

if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "max_usb_current=1" "$CONFIG_FILE"; then
        echo "Füge max_usb_current=1 zur $CONFIG_FILE hinzu..."
        echo "max_usb_current=1" | sudo tee -a "$CONFIG_FILE"
    fi
fi

CMDLINE_FILE="/boot/firmware/cmdline.txt"
if [ ! -f "$CMDLINE_FILE" ] && [ -f "/boot/cmdline.txt" ]; then
    CMDLINE_FILE="/boot/cmdline.txt"
fi

if [ -f "$CMDLINE_FILE" ]; then
    if ! grep -q "usbcore.autosuspend=-1" "$CMDLINE_FILE"; then
        echo "Deaktiviere USB-Energiesparmodus in $CMDLINE_FILE..."
        sudo sed -i 's/$/ usbcore.autosuspend=-1/' "$CMDLINE_FILE"
    fi
fi

# 5. Grafische Minimal-Oberfläche, MQTT und Systemabhängigkeiten installieren
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y
sudo apt install git python3 python3-pygame python3-serial python3-paho-mqtt python3-qrcode pulseaudio alsa-utils unclutter curl -y

# 6. Unnötige Hintergrunddienste für 1-GB-RAM-Stabilität deaktivieren
echo "Deaktiviere nicht benötigte Hintergrunddienste (RAM-Optimierung)..."
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
for svc in "${UNUSED_SERVICES[@]}"; do
    sudo systemctl stop "$svc" 2>/dev/null
    sudo systemctl disable "$svc" 2>/dev/null
done

# 7. WLAN-Energiesparmodus deaktivieren
sudo mkdir -p /etc/NetworkManager/conf.d
cat << 'EOF' | sudo tee /etc/NetworkManager/conf.d/default-wifi-powersave-off.conf > /dev/null
[connection]
wifi.powersave = 2
EOF

# 8. Systemd-Journal im RAM auf max. 16 MB begrenzen
sudo mkdir -p /etc/systemd/journald.conf.d
cat << 'EOF' | sudo tee /etc/systemd/journald.conf.d/size-limit.conf > /dev/null
[Journal]
Storage=volatile
RuntimeMaxUse=16M
RuntimeMaxFileSize=4M
EOF

# 9. Grafischen Startmodus und LightDM Dienst erzwingen
sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

# 10. Öffentliches GitHub-Repository klonen (Zweig: stable)
echo "Lade Dateien von GitHub herunter (Zweig: stable)..."
mkdir -p /home/visionpi2000/VisionPi2000
rm -rf /tmp/VisionPiRepo
rm -rf /tmp/paho_temp
rm -rf /tmp/qrcode_temp

git clone --branch stable --depth 1 https://github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

if [ ! -d "/tmp/VisionPiRepo/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Überprüfe die Internetverbindung."
    exit 1
fi

# 11. paho-mqtt direkt in das Spielverzeichnis einbetten
if [ ! -d "/tmp/VisionPiRepo/VisionPi2000/paho" ]; then
    echo "Bette paho-mqtt Bibliothek direkt in das Spielverzeichnis ein..."
    mkdir -p /tmp/paho_temp
    git clone --depth 1 https://github.com/eclipse-paho/paho.mqtt.python.git /tmp/paho_temp
    if [ -d "/tmp/paho_temp/src/paho" ]; then
        cp -r /tmp/paho_temp/src/paho /tmp/VisionPiRepo/VisionPi2000/paho
        echo "paho-mqtt erfolgreich eingebettet!"
    fi
    rm -rf /tmp/paho_temp
fi

# 12. qrcode direkt in das Spielverzeichnis einbetten
if [ ! -d "/tmp/VisionPiRepo/VisionPi2000/qrcode" ]; then
    echo "Bette qrcode Bibliothek direkt in das Spielverzeichnis ein..."
    mkdir -p /tmp/qrcode_temp
    git clone --depth 1 https://github.com/lincolnloop/python-qrcode.git /tmp/qrcode_temp
    if [ -d "/tmp/qrcode_temp/qrcode" ]; then
        cp -r /tmp/qrcode_temp/qrcode /tmp/VisionPiRepo/VisionPi2000/qrcode
        echo "qrcode erfolgreich eingebettet!"
    fi
    rm -rf /tmp/qrcode_temp
fi

cp -r /tmp/VisionPiRepo/VisionPi2000/* /home/visionpi2000/VisionPi2000/
rm -rf /tmp/VisionPiRepo

# 13. settings.json auf der Boot-Partition ablegen und verlinken
BOOT_DIR="/boot/firmware"
if [ ! -d "$BOOT_DIR" ]; then BOOT_DIR="/boot"; fi

if [ ! -f "$BOOT_DIR/settings.json" ]; then
    echo "Erstelle settings.json auf der Boot-Partition..."
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart", "branch": "stable", "mqtt_broker": "broker.emqx.io"}' | sudo tee "$BOOT_DIR/settings.json" > /dev/null
fi
sudo chmod 666 "$BOOT_DIR/settings.json"

rm -f /home/visionpi2000/VisionPi2000/settings.json
ln -s "$BOOT_DIR/settings.json" /home/visionpi2000/VisionPi2000/settings.json

# 14. Berechtigungen für den Benutzer 'visionpi2000' setzen
sudo usermod -a -G audio,dialout visionpi2000

# 15. LightDM Autologin konfigurieren
sudo mkdir -p /etc/lightdm/lightdm.conf.d
sudo bash -c 'cat << '\''EOF'\'' > /etc/lightdm/lightdm.conf.d/99-autologin.conf
[Seat:*]
autologin-user=visionpi2000
user-session=openbox
EOF'

# 16. Autostart-Skript für Openbox erstellen
mkdir -p /home/visionpi2000/.config/openbox
cat << 'EOF' > /home/visionpi2000/.config/openbox/autostart
# Mauszeiger nach 0,1 Sekunden Inaktivität komplett ausblenden
unclutter -idle 0.1 -root &

# Bildschirmschoner und Stromsparmodus von X11 deaktivieren
xset s off
xset -dpms
xset s noblank

# In den Spielordner wechseln und starten
cd /home/visionpi2000/VisionPi2000
python3 visionpi.py &
EOF

# 17. Sounds im Vorfeld generieren
echo "Generiere Sounds..."
cd /home/visionpi2000/VisionPi2000
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# 18. Dateiberechtigungen für den Benutzer absichern
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/VisionPi2000
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 19. Sound-Lautstärke auf 100% einstellen
amixer sset Master 100% 2>/dev/null

# 20. System-Schreibschutz (OverlayFS) aktivieren
echo "Aktiviere System-Schreibschutz (OverlayFS)..."
sudo raspi-config nonint enable_overlayfs
sudo raspi-config nonint disable_bootro 2>/dev/null

sync

echo "========================================================================="
echo "Öffentliche Erstinstallation & Schreibschutz erfolgreich abgeschlossen!"
echo "Das System wird in 5 Sekunden im geschützten Modus neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
