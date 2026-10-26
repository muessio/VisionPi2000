#!/bin/bash
# =====================================================================
# VisionPi2000 - Private Installations- und Setup-Skript
# Hauptnutzer: visionpi2000
# =====================================================================

if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Das Skript muss mit einem Token gestartet werden: sudo ./private_Software_u_Setup.sh DEIN_TOKEN"
  exit 1
fi

sudo apt update

# 1.5. USB-Stromlimit auf Maximum setzen
CONFIG_FILE="/boot/firmware/config.txt"
if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "max_usb_current=1" "$CONFIG_FILE"; then
        echo "Füge max_usb_current=1 zur $CONFIG_FILE hinzu..."
        echo "max_usb_current=1" | sudo tee -a "$CONFIG_FILE"
    fi
fi

# --- NEU: USB Energiesparmodus für Pi 3B komplett deaktivieren ---
CMDLINE_FILE="/boot/firmware/cmdline.txt"
if [ ! -f "$CMDLINE_FILE" ]; then CMDLINE_FILE="/boot/cmdline.txt"; fi
if [ -f "$CMDLINE_FILE" ]; then
    if ! grep -q "usbcore.autosuspend=-1" "$CMDLINE_FILE"; then
        echo "Deaktiviere USB-Energiesparmodus in $CMDLINE_FILE..."
        # Fügt den Parameter ganz ans Ende der bestehenden Zeile an
        sudo sed -i 's/$/ usbcore.autosuspend=-1/' "$CMDLINE_FILE"
    fi
fi
# -----------------------------------------------------------------

# 2. Grafische Minimal-Oberfläche und Abhängigkeiten installieren
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y
sudo apt install git python3 python3-pygame python3-serial pulseaudio alsa-utils unclutter -y

sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

# 3. GitHub-Repository klonen
echo "Lade Dateien von GitHub herunter..."
mkdir -p /home/visionpi2000/VisionPi2000

rm -rf /tmp/VisionPiRepo
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

if [ ! -d "/tmp/VisionPiRepo/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Überprüfe die Internetverbindung oder den Token."
    exit 1
fi

cp -r /tmp/VisionPiRepo/VisionPi2000/* /home/visionpi2000/VisionPi2000/
rm -rf /tmp/VisionPiRepo

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
unclutter -idle 0.1 -root &
xset s off
xset -dpms
xset s noblank
cd /home/visionpi2000/VisionPi2000
python3 visionpi.py &
EOF

# --- NEU: Auslagerung der settings.json auf die dauerhafte Boot-Partition ---
SETTINGS_BOOT="/boot/firmware/settings.json"
if [ ! -d "/boot/firmware" ]; then SETTINGS_BOOT="/boot/settings.json"; fi

if [ ! -f "$SETTINGS_BOOT" ]; then
    echo "Erstelle ausgelagerte settings.json auf der FAT32-Boot-Partition..."
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart"}' | sudo tee "$SETTINGS_BOOT" > /dev/null
fi

# Lösche die Standard-Datei aus dem Spielordner und ersetze sie durch den Link
rm -f /home/visionpi2000/VisionPi2000/settings.json
ln -sf "$SETTINGS_BOOT" /home/visionpi2000/VisionPi2000/settings.json

# WICHTIG: Erlaube dem normalen User Schreibzugriff auf die Boot-Partition in der fstab
if ! grep -q "umask=000" /etc/fstab; then
    echo "Passe fstab an, um Schreibrechte für settings.json zu garantieren..."
    sudo sed -i -E 's/(vfat\s+defaults)/\1,umask=000/' /etc/fstab
fi
# ----------------------------------------------------------------------------

# 7. Sounds generieren
echo "Generiere Sounds..."
cd /home/visionpi2000/VisionPi2000
python3 generate_sounds.py

# 8. Dateiberechtigungen sicherstellen
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/VisionPi2000
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 9. Sound einmalig auf 100% einstellen
amixer sset Master 100%

# --- NEU: Schreibschutz (OverlayFS) aktivieren ---
echo "Aktiviere System-Schreibschutz (OverlayFS)..."
sudo raspi-config nonint enable_overlayfs
# Die Boot-Partition MUSS zwingend schreibbar bleiben für unsere ausgelagerte JSON!
sudo raspi-config nonint disable_bootro
# -------------------------------------------------

echo "========================================================================="
echo "Private Software-Installation und Setup erfolgreich abgeschlossen!"
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
