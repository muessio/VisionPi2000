#!/bin/bash
# =====================================================================
# VisionPi2000 - Privates Erstinstallations- und Setup-Skript 
# (Stabile Version: Nutzt die vorhandene /boot/firmware FAT32-Partition)
# Hauptnutzer: visionpi2000
# =====================================================================

if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Aufruf: sudo ./private_Software_u_Setup.sh DEIN_TOKEN"
  exit 1
fi

sudo apt update

# 1. USB-Stromlimit auf Maximum setzen und Energiesparmodus deaktivieren
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then CONFIG_FILE="/boot/config.txt"; fi
if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "max_usb_current=1" "$CONFIG_FILE"; then
        echo "max_usb_current=1" | sudo tee -a "$CONFIG_FILE"
    fi
fi

CMDLINE_FILE="/boot/firmware/cmdline.txt"
if [ ! -f "$CMDLINE_FILE" ]; then CMDLINE_FILE="/boot/cmdline.txt"; fi
if [ -f "$CMDLINE_FILE" ]; then
    if ! grep -q "usbcore.autosuspend=-1" "$CMDLINE_FILE"; then
        sudo sed -i 's/$/ usbcore.autosuspend=-1/' "$CMDLINE_FILE"
    fi
fi

# 2. Grafische Minimal-Oberfläche und Abhängigkeiten installieren
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y
sudo apt install git python3 python3-pygame python3-serial pulseaudio alsa-utils unclutter -y

sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

# 3. GitHub-Repository direkt auf die Boot-Partition klonen
BOOT_DIR="/boot/firmware/VisionPi2000"
if [ ! -d "/boot/firmware" ]; then BOOT_DIR="/boot/VisionPi2000"; fi

rm -rf /tmp/VisionPiRepo
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

if [ -d "/tmp/VisionPiRepo/VisionPi2000" ]; then
    SRC_DIR="/tmp/VisionPiRepo/VisionPi2000"
else
    SRC_DIR="/tmp/VisionPiRepo"
fi

sudo mkdir -p "$BOOT_DIR"
sudo rm -rf "$BOOT_DIR"/*
sudo cp -r "$SRC_DIR"/* "$BOOT_DIR"/
rm -rf /tmp/VisionPiRepo

# 4. Symlink vom Home-Ordner auf die Boot-Partition erstellen
sudo rm -rf /home/visionpi2000/VisionPi2000
ln -s "$BOOT_DIR" /home/visionpi2000/VisionPi2000

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

# Settings.json auf der Boot-Partition anlegen
SETTINGS_BOOT="$BOOT_DIR/settings.json"
if [ ! -f "$SETTINGS_BOOT" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart"}' | sudo tee "$SETTINGS_BOOT" > /dev/null
fi

# FAT32 fstab-Anpassung für volle Schreibrechte
if ! grep -q "umask=000" /etc/fstab; then
    sudo sed -i -E 's/(vfat\s+defaults)/\1,umask=000/' /etc/fstab
fi

# 7. Sounds generieren
cd "$BOOT_DIR"
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# 8. Dateiberechtigungen im Home-Ordner sicherstellen
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 9. Sound einmalig auf 100% einstellen
amixer sset Master 100%

# 10. Schreibschutz (OverlayFS) aktivieren & Boot schreibbar lassen
sudo raspi-config nonint enable_overlayfs
sudo raspi-config nonint disable_bootro

echo "========================================================================="
echo "Erstinstallation erfolgreich abgeschlossen!"
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
