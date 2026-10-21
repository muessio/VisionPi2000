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

# 2. Grafische Minimal-Oberfläche und Abhängigkeiten installieren
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y
sudo apt install git python3 python3-pygame python3-serial pulseaudio alsa-utils unclutter -y

# 3. GitHub-Repository klonen und Dateien am richtigen Ort ablegen
echo "Lade Dateien von GitHub herunter..."
mkdir -p /home/visionpi2000/VisionPi2000

# Das Repository über den Token ($1) sicher herunterladen
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepo

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

# 7. Dateiberechtigungen für den Benutzer sicherstellen
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/VisionPi2000
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/.config

# 8. Sound einmalig auf 100% einstellen
amixer sset Master 100%

echo "========================================================================="
echo "Private Software-Installation und Setup erfolgreich abgeschlossen!"
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
