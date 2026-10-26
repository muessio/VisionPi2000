#!/bin/bash
# =====================================================================
# VisionPi2000 - Privates UPDATE-Skript (Ordner exakt spiegeln)
# Inkl. intelligenter Schreibschutz-Umgehung (OverlayFS Bypass)
# =====================================================================

if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Das Skript muss mit einem Token gestartet werden: sudo ./private_Update.sh DEIN_TOKEN"
  exit 1
fi

if ! command -v git &> /dev/null; then
    echo "Git ist nicht installiert. Installiere Git..."
    sudo apt update && sudo apt install git -y
fi

# --- NEU: Schreibschutz (OverlayFS) sicher umgehen ---
TARGET_DIR="/home/visionpi2000/VisionPi2000"
MOUNT_POINT=""

# Prüfen, ob der Pi im Read-Only (OverlayFS) Modus läuft
if grep -q "overlay / " /proc/mounts; then
    echo "Schreibschutz (OverlayFS) ist aktiv!"
    echo "Hänge die physische SD-Karte ein, um das Update permanent zu speichern..."
    # Echte Partition aus der fstab auslesen und in temporären Ordner mounten
    ROOT_DEV=$(awk '$2 == "/" {print $1}' /etc/fstab)
    MOUNT_POINT="/mnt/root_rw"
    sudo mkdir -p "$MOUNT_POINT"
    sudo mount "$ROOT_DEV" "$MOUNT_POINT"
    TARGET_DIR="$MOUNT_POINT/home/visionpi2000/VisionPi2000"
else
    # Falls kein OverlayFS aktiv ist, einfach sicherheitshalber RW mounten
    sudo mount -o remount,rw /
fi
# -----------------------------------------------------

rm -rf /tmp/VisionPiRepoUpdate
echo "Lade neueste Dateien von GitHub herunter..."
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Update wird abgebrochen."
    if [ -n "$MOUNT_POINT" ]; then sudo umount "$MOUNT_POINT"; fi
    exit 1
fi

# --- NEU: Sounds VOR dem Kopieren generieren ---
# (Wenn wir das in /tmp machen, landen die fertigen Wav-Dateien 
# direkt auf der echten Partition, statt im flüchtigen RAM zu verpuffen)
echo "Prüfe und generiere ggf. neue Sounds..."
cd /tmp/VisionPiRepoUpdate/VisionPi2000
python3 generate_sounds.py
# -----------------------------------------------

echo "Download erfolgreich. Aktualisiere den VisionPi2000 Ordner..."

# 1. Alten Inhalt auf dem Pi komplett löschen
sudo rm -rf ${TARGET_DIR}/*

# 2. Den frisch heruntergeladenen Inhalt kopieren
sudo cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* ${TARGET_DIR}/

# 3. Danach direkt wieder aufräumen
rm -rf /tmp/VisionPiRepoUpdate

# --- NEU: Symlink für ausgelagerte Einstellungen wiederherstellen ---
sudo rm -f ${TARGET_DIR}/settings.json
SETTINGS_BOOT="/boot/firmware/settings.json"
if [ ! -d "/boot/firmware" ]; then SETTINGS_BOOT="/boot/settings.json"; fi
sudo ln -sf "$SETTINGS_BOOT" ${TARGET_DIR}/settings.json
# --------------------------------------------------------------------

# Dateiberechtigungen wieder glattziehen
sudo chown -R visionpi2000:visionpi2000 ${TARGET_DIR}

# Schreibschutz wiederherstellen (Mount aushängen oder RO remounten)
if [ -n "$MOUNT_POINT" ]; then
    sudo umount "$MOUNT_POINT"
else
    sudo mount -o remount,ro /
fi

echo "========================================================================="
echo "Update erfolgreich! Alle Dateien wurden permanent auf die SD-Karte geschrieben."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
