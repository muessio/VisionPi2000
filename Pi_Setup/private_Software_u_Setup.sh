#!/bin/bash
# =====================================================================
# VisionPi2000 - Privates Erstinstallations- und Setup-Skript 
# (Inkl. automatischer Erstellung einer schreibbaren FAT32-Datenpartition)
# Hauptnutzer: visionpi2000
# =====================================================================

if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Das Skript muss mit einem Token gestartet werden: sudo ./private_Software_u_Setup.sh DEIN_TOKEN"
  exit 1
fi

sudo apt update
sudo apt install dosfstools -y

# --- AUTOMATISCHE DATEN-PARTITION (FAT32) ERSTELLEN ---
echo "Erstelle schreibbare FAT32-Datenpartition aus dem restlichen Speicher..."
ROOT_PART=$(findmnt / -o SOURCE -n)
DISK_DEV=$(echo "$ROOT_PART" | sed 's/[0-9p]*$//')
DATA_PART="${DISK_DEV}p3"
if [ ! -b "$DATA_PART" ]; then DATA_PART="${DISK_DEV}3"; fi

# Prüfen, ob Partition 3 schon existiert, falls nicht -> erstellen
if [ ! -b "$DATA_PART" ]; then
    echo "Lege Partition 3 an..."
    # fdisk: Neue Partition (n), Primär (p), Nummer 3, Default Start, Default Ende, Schreiben (w)
    echo -e "n\np\n3\n\n\nw" | sudo fdisk "$DISK_DEV" > /dev/null 2>&1
    sudo partprobe "$DISK_DEV"
    sleep 3
    
    echo "Formatiere Partition 3 als FAT32..."
    sudo mkfs.fat -F 32 "$DATA_PART"
fi

PROJECT_DIR="/home/visionpi2000/VisionPi2000"
sudo rm -rf "$PROJECT_DIR"
sudo mkdir -p "$PROJECT_DIR"

# In fstab eintragen für automatischen Mount beim Start
if ! grep -q "$DATA_PART" /etc/fstab; then
    echo "Trage neue Daten-Partition in /etc/fstab ein..."
    echo "$DATA_PART $PROJECT_DIR vfat defaults,umask=000 0 2" | sudo tee -a /etc/fstab
fi

# Partition sofort einhängen
sudo mount -a
# -------------------------------------------------------------

# 1.5. USB-Stromlimit auf Maximum setzen
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then CONFIG_FILE="/boot/config.txt"; fi
if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "max_usb_current=1" "$CONFIG_FILE"; then
        echo "Füge max_usb_current=1 zur $CONFIG_FILE hinzu..."
        echo "max_usb_current=1" | sudo tee -a "$CONFIG_FILE"
    fi
fi

# USB Energiesparmodus für Pi komplett deaktivieren
CMDLINE_FILE="/boot/firmware/cmdline.txt"
if [ ! -f "$CMDLINE_FILE" ]; then CMDLINE_FILE="/boot/cmdline.txt"; fi
if [ -f "$CMDLINE_FILE" ]; then
    if ! grep -q "usbcore.autosuspend=-1" "$CMDLINE_FILE"; then
        echo "Deaktiviere USB-Energiesparmodus in $CMDLINE_FILE..."
        sudo sed -i 's/$/ usbcore.autosuspend=-1/' "$CMDLINE_FILE"
    fi
fi

# 2. Grafische Minimal-Oberfläche und Abhängigkeiten installieren
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y
sudo apt install git python3 python3-pygame python3-serial pulseaudio alsa-utils unclutter -y

sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

# 3. GitHub-Repository klonen und direkt auf die neue Partition kopieren
echo "Lade Dateien von GitHub herunter..."
rm -rf /tmp/VisionPiRepo
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

if [ -d "/tmp/VisionPiRepo/VisionPi2000" ]; then
    SRC_DIR="/tmp/VisionPiRepo/VisionPi2000"
else
    SRC_DIR="/tmp/VisionPiRepo"
fi

sudo rm -rf "$PROJECT_DIR"/*
sudo cp -r "$SRC_DIR"/* "$PROJECT_DIR"/
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

# Settings.json direkt im Projektordner anlegen
SETTINGS_FILE="$PROJECT_DIR/settings.json"
if [ ! -f "$SETTINGS_FILE" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart"}' | sudo tee "$SETTINGS_FILE" > /dev/null
fi

# 7. Sounds generieren
echo "Generiere Sounds..."
cd "$PROJECT_DIR"
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# 8. Dateiberechtigungen im Home-Ordner sicherstellen
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 9. Sound einmalig auf 100% einstellen
amixer sset Master 100%

# 10. Schreibschutz (OverlayFS) aktivieren & Boot schreibbar lassen
echo "Aktiviere System-Schreibschutz (OverlayFS)..."
sudo raspi-config nonint enable_overlayfs
sudo raspi-config nonint disable_bootro

echo "========================================================================="
echo "Erstinstallation erfolgreich! Daten-Partition wurde automatisch erstellt."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
