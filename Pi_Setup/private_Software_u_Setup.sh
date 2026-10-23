#!/bin/bash
# =====================================================================
# VisionPi2000 - Private Installations- und Setup-Skript
# Hauptnutzer: visionpi2000
# =====================================================================

# Prüfen, ob ein Token übergeben wurde
if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Das Skript muss mit einem Token gestartet werden: sudo ./private_Software_u_Setup.sh DEIN_TOKEN"
  exit 1
fi

# 1. System updaten
sudo apt update
sudo apt upgrade -y

# 1.5. USB-Stromlimit auf Maximum setzen (hilft bei stromhungriger Peripherie wie Arduino)
CONFIG_FILE="/boot/firmware/config.txt"
if [ -f "$CONFIG_FILE" ]; then
    if ! grep -q "max_usb_current=1" "$CONFIG_FILE"; then
        echo "Füge max_usb_current=1 zur $CONFIG_FILE hinzu..."
        echo "max_usb_current=1" | sudo tee -a "$CONFIG_FILE"
    else
        echo "max_usb_current=1 ist bereits gesetzt."
    fi
else
    echo "Warnung: $CONFIG_FILE nicht gefunden, überspringe USB-Strombegrenzung."
fi

# 2. Grafische Minimal-Oberfläche und Abhängigkeiten installieren
# (git wird hier direkt mit installiert)
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y
sudo apt install git python3 python3-pygame python3-serial pulseaudio alsa-utils unclutter -y

# 2.5 Grafischen Startmodus und LightDM Dienst erzwingen (Kioskmodus-Fix)
sudo systemctl set-default graphical.target
sudo systemctl enable lightdm

# 3. GitHub-Repository klonen und Dateien am richtigen Ort ablegen
echo "Lade Dateien von GitHub herunter..."
mkdir -p /home/visionpi2000/VisionPi2000

# WICHTIG: Vorherige Dateileichen im tmp-Ordner zwingend löschen!
rm -rf /tmp/VisionPiRepo

# Das Repository über den Token ($1) sicher herunterladen
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

# SICHERHEITS-CHECK: Wurde wirklich etwas heruntergeladen?
if [ ! -d "/tmp/VisionPiRepo/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Überprüfe die Internetverbindung oder den Token."
    exit 1
fi

# KORREKTUR: Wieder gezielt aus dem VisionPi2000 Unterordner kopieren, damit die Struktur für den Kioskmodus stimmt!
cp -r /tmp/VisionPiRepo/VisionPi2000/* /home/visionpi2000/VisionPi2000/
rm -rf /tmp/VisionPiRepo

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

# 7. Sounds generieren (generate_sounds.py ausführen)
echo "Generiere Sounds..."
cd /home/visionpi2000/VisionPi2000
python3 generate_sounds.py

# 8. Dateiberechtigungen für den Benutzer sicherstellen (greift auch für neu generierte Sounds)
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/VisionPi2000
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 9. Sound einmalig auf 100% einstellen
amixer sset Master 100%

echo "========================================================================="
echo "Private Software-Installation und Setup erfolgreich abgeschlossen!"
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
