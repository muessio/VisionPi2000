#!/bin/bash
# =====================================================================
# VisionPi2000 - Private Installations- und Setup-Skript (Volle Automatik)
# Hauptnutzer: visionpi2000
# =====================================================================

# Prüfen, ob ein Token übergeben wurde
if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Das Skript muss mit einem Token gestartet werden: sudo ./private_Software_u_Setup.sh DEIN_TOKEN"
  exit 1
fi

# 1. Nur Paketlisten aktualisieren
sudo apt update

# 1.5. USB-Stromlimit auf Maximum setzen
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

# 2. Grafische Minimal-Oberfläche und Abhängigkeiten installieren
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y
sudo apt install git python3 python3-pygame python3-serial pulseaudio alsa-utils unclutter curl -y

# 2.5 Grafischen Startmodus und LightDM Dienst erzwingen
sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

# 3. GitHub-Repository klonen und Dateien ablegen
echo "Lade Dateien von GitHub herunter..."
mkdir -p /home/visionpi2000/VisionPi2000
rm -rf /tmp/VisionPiRepo

git clone --depth 1 https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

if [ ! -d "/tmp/VisionPiRepo/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Überprüfe die Internetverbindung oder den Token."
    exit 1
fi

cp -r /tmp/VisionPiRepo/VisionPi2000/* /home/visionpi2000/VisionPi2000/
rm -rf /tmp/VisionPiRepo

# 3.5 WICHTIG: settings.json dauerhaft auf die ungeschützte Boot-Partition legen & verlinken!
BOOT_DIR="/boot/firmware"
if [ ! -d "$BOOT_DIR" ]; then BOOT_DIR="/boot"; fi

if [ ! -f "$BOOT_DIR/settings.json" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart"}' | sudo tee "$BOOT_DIR/settings.json" > /dev/null
fi
sudo chmod 666 "$BOOT_DIR/settings.json"

# Symlink im Spielordner erstellen, damit ALLE Spiele (X01, Cricket etc.) automatisch auf Boot lesen/schreiben
rm -f /home/visionpi2000/VisionPi2000/settings.json
ln -s "$BOOT_DIR/settings.json" /home/visionpi2000/VisionPi2000/settings.json

# 4. Berechtigungen für den Benutzer 'visionpi2000' setzen (Audio & Arduino/USB)
sudo usermod -a -G audio,dialout visionpi2000

# 5. LightDM Autologin konfigurieren
sudo mkdir -p /etc/lightdm/lightdm.conf.d
sudo bash -c 'cat << 'EOF' > /etc/lightdm/lightdm.conf.d/99-autologin.conf
[Seat:*]
autologin-user=visionpi2000
user-session=openbox
EOF'

# 6. Autostart-Skript für Openbox erstellen
mkdir -p /home/visionpi2000/.config/openbox
cat << 'EOF' > /home/visionpi2000/.config/openbox/autostart
# Mauszeiger nach 0,1 Sekunden Inaktivität komplett ausblenden
unclutter -idle 0.1 -root &

# Bildschirmschoner und Stromsparmodus deaktivieren
xset s off
xset -dpms
xset s noblank

# In den Spielordner wechseln und starten
cd /home/visionpi2000/VisionPi2000
python3 visionpi.py &
EOF

# 7. Sounds generieren
echo "Generiere Sounds..."
cd /home/visionpi2000/VisionPi2000
python3 generate_sounds.py

# 8. Dateiberechtigungen für den Benutzer sicherstellen
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/VisionPi2000
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 9. Sound einmalig auf 100% einstellen
amixer sset Master 100% 2>/dev/null

# 10. OverlayFS (Schreibschutz für Systempartition) aktivieren, Boot-Partition offen lassen
echo "Aktiviere System-Schreibschutz (OverlayFS)..."
sudo raspi-config nonint enable_overlayfs
sudo raspi-config nonint disable_bootro 2>/dev/null

sync

echo "========================================================================="
echo "Ersteinrichtung & Schreibschutz-Aktivierung erfolgreich abgeschlossen!"
echo "Das System wird in 5 Sekunden im geschützten Modus neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
