#!/bin/bash
# =====================================================================
# VisionPi2000 - Privates UPDATE-Skript (Nur Dateien überschreiben)
# Hauptnutzer: visionpi2000
# =====================================================================

# Prüfen, ob ein Token übergeben wurde
if [ -z "$1" ]; then
  echo "Fehler: Kein GitHub-Token übergeben!"
  echo "Das Skript muss mit einem Token gestartet werden: sudo ./private_Update.sh DEIN_TOKEN"
  exit 1
fi

echo "Lade neueste Dateien von GitHub herunter..."

# Temporär das komplette Repository mit dem Token herunterladen
git clone https://${1}@github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# Alle Dateien im Zielordner überschreiben (-r rekursiv, -f ohne Nachfragen)
cp -rf /tmp/VisionPiRepoUpdate/VisionPi2000/* /home/visionpi2000/VisionPi2000/

# Aufräumen (Temporären Ordner löschen, damit es beim nächsten Update keine Fehler gibt)
rm -rf /tmp/VisionPiRepoUpdate

# Sounds neu generieren (falls du neue hinzugefügt hast)
echo "Prüfe und generiere ggf. neue Sounds..."
cd /home/visionpi2000/VisionPi2000
python3 generate_sounds.py

# Dateiberechtigungen wieder glattziehen
sudo chown -R visionpi2000:visionpi2000 /home/visionpi2000/VisionPi2000

echo "========================================================================="
echo "Update erfolgreich! Alle Dateien wurden auf den neuesten Stand gebracht."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
