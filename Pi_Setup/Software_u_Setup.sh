# =====================================================================
# VisionPi2000 - Master Installations- und Setup-Skript
# Benutzer: visionpi2000
# =====================================================================

# 1. System updaten
sudo apt update
sudo apt upgrade -y

# 2. Grafische Minimal-Oberfläche (Openbox/LightDM) installieren
sudo apt install --no-install-recommends xserver-xorg x11-xserver-utils xinit openbox lightdm -y

# 3. Python-Umgebung sowie Bibliotheken für die Spiele & Arduino (Pygame & PySerial) installieren
sudo apt install python3 python3-pygame python3-serial pulseaudio alsa-utils -y

# 4. Berechtigungen für den Benutzer 'visionpi2000' setzen (Audio & Arduino/USB)
sudo usermod -a -G audio,dialout visionpi2000

# 5. LightDM Autologin konfigurieren (Direktstart in die Benutzeroberfläche ohne Passwort)
sudo mkdir -p /etc/lightdm/lightdm.conf.d
sudo bash -c 'cat << 'EOF' > /etc/lightdm/lightdm.conf.d/99-autologin.conf
[Seat:*]
autologin-user=visionpi2000
user-session=openbox
EOF'

# 6. Autostart-Skript für Openbox erstellen (Mauszeiger verstecken, Standby aus, Spiel starten)
mkdir -p /home/visionpi2000/.config/openbox
cat << 'EOF' > /home/visionpi2000/.config/openbox/autostart
# Maus komplett aus dem X-Server verbannen
xsetroot -cursor_name left_ptr &

# Bildschirmschoner und Stromsparmodus deaktivieren
xset s off
xset -dpms
xset s noblank

# Das Darts-Spiel im Vollbild starten
python3 /home/visionpi2000/VisionPi2000/visionpi.py &
EOF

# 7. Sound einmalig auf 100% einstellen
amixer sset Master 100%

echo "========================================================================="
echo "Basis-Einrichtung erfolgreich abgeschlossen!"
echo ""
echo "NÄCHSTER SCHRITT:"
echo "Kopiere deinen kompletten 'VisionPi2000'-Ordner (der die 'visionpi.py',"
echo "alle 'game_*.py'-Module, Bilder und den 'sounds'-Ordner enthält)"
echo "nach: /home/visionpi2000/VisionPi2000/"
echo ""
echo "Starte den Pi danach mit folgendem Befehl neu: sudo reboot"
echo "========================================================================="
