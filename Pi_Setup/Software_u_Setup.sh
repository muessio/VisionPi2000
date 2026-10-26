#!/bin/bash
# =====================================================================
# VisionPi2000 - Öffentliches Master Installations- und Setup-Skript 
# (Inkl. automatischer 2/3-Partitionierung für die Boot-Partition)
# =====================================================================

sudo apt update
sudo apt install parted -y

# --- AUTOMATISCHE PARTITIONS-VERGRÖßERUNG (2/3 für Boot) ---
echo "Passe Partitionsgröße für die Boot-Partition an..."
ROOT_PART=$(findmnt / -o SOURCE -n)
DISK_DEV=$(echo "$ROOT_PART" | sed 's/[0-9p]*$//')

if [ -b "$DISK_DEV" ]; then
    TOTAL_MB=$(sudo blockdev --getsz "$DISK_DEV" 2>/dev/null | awk '{print $1 / 2048}')
    if [ -z "$TOTAL_MB" ] || [ "$TOTAL_MB" -eq 0 ]; then
        TOTAL_MB=$(sudo parted -s "$DISK_DEV" print | grep "Disk" | awk '{print $3}' | sed 's/MB//')
    fi
    
    if [ -n "$TOTAL_MB" ] && [ "$TOTAL_MB" -gt 1000 ]; then
        TARGET_MB=$(( (TOTAL_MB * 2) / 3 ))
        echo "SD-Gesamtgröße: ${TOTAL_MB} MB. Vergrößere Boot-Partition auf ${TARGET_MB} MB..."
        
        sudo parted -s "$DISK_DEV" resizepart 1 "${TARGET_MB}MB" 2>/dev/null
        
        BOOT_PART="${DISK_DEV}p1"
        if [ ! -b "$BOOT_PART" ]; then BOOT_PART="${DISK_DEV}1"; fi
        sudo resize2fs "$BOOT_PART" 2>/dev/null || true
        if command -v fatresize &> /dev/null; then
            sudo fatresize -s max "$BOOT_PART" 2>/dev/null
        else
            sudo apt install fatresize -y && sudo fatresize -s max "$BOOT_PART" 2>/dev/null
        fi
    fi
fi
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

# 3. GitHub-Repository klonen und direkt auf der Boot-Partition ablegen
echo "Lade Dateien von GitHub herunter..."
BOOT_DIR="/boot/firmware/VisionPi2000"
if [ ! -d "/boot/firmware" ]; then BOOT_DIR="/boot/VisionPi2000"; fi

rm -rf /tmp/VisionPiRepo
git clone https://github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

if [ ! -d "/tmp/VisionPiRepo/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Überprüfe die Internetverbindung."
    exit 1
fi

sudo mkdir -p "$BOOT_DIR"
sudo rm -rf "$BOOT_DIR"/*
sudo cp -r /tmp/VisionPiRepo/VisionPi2000/* "$BOOT_DIR"/
rm -rf /tmp/VisionPiRepo

# 4. Symlink vom Home-Ordner auf die Boot-Partition erstellen (im Linux-Dateisystem /home ist das erlaubt)
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

# Settings.json direkt auf der Boot-Partition anlegen (ohne fehlerhaften Symlink auf FAT32)
SETTINGS_BOOT="$BOOT_DIR/settings.json"
if [ ! -f "$SETTINGS_BOOT" ]; then
    echo "Erstelle settings.json auf der Boot-Partition..."
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart"}' | sudo tee "$SETTINGS_BOOT" > /dev/null
fi

if ! grep -q "umask=000" /etc/fstab; then
    echo "Passe fstab an..."
    sudo sed -i -E 's/(vfat\s+defaults)/\1,umask=000/' /etc/fstab
fi

# 7. Sounds generieren
echo "Generiere Sounds..."
cd "$BOOT_DIR"
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# 8. Dateiberechtigungen nur dort setzen, wo es erlaubt ist (Home-Ordner)
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 9. Sound einmalig auf 100% einstellen
amixer sset Master 100%

# 10. Schreibschutz (OverlayFS) aktivieren & Boot schreibbar lassen
echo "Aktiviere System-Schreibschutz (OverlayFS)..."
sudo raspi-config nonint enable_overlayfs
sudo raspi-config nonint disable_bootro

echo "========================================================================="
echo "Öffentliche Erstinstallation mit dynamischer Speicheraufteilung fertig!"
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
