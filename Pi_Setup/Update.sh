#!/bin/bash
# =====================================================================
# VisionPi2000 - Öffentliches UPDATE-Skript (Debian Trixie & OverlayFS)
# Inkl. rückwirkender RAM-, WLAN- & Systemdienst-Optimierung für Bestandsautomaten
# Hauptnutzer: visionpi2000
# =====================================================================

# WICHTIG: Vorherige Dateileichen im tmp-Ordner (RAM) löschen!
rm -rf /tmp/VisionPiRepoUpdate
rm -rf /tmp/paho_temp
rm -rf /tmp/qrcode_temp

echo "Lade neueste Dateien von GitHub in den RAM herunter..."
git clone --depth 1 https://github.com/muessio/VisionPi2000.git /tmp/VisionPiRepoUpdate

# SICHERHEITS-CHECK: Wurde wirklich etwas heruntergeladen?
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000" ]; then
    echo "FEHLER: Download fehlgeschlagen! Das Update wird abgebrochen."
    rm -rf /tmp/VisionPiRepoUpdate
    exit 1
fi

# 1. paho-mqtt direkt als reines Python-Modul in den Spielordner einbetten (Trixie-sicher ohne apt/pip!)
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000/paho" ]; then
    echo "Bette paho-mqtt Bibliothek direkt in das Spielverzeichnis ein..."
    mkdir -p /tmp/paho_temp
    git clone --depth 1 https://github.com/eclipse-paho/paho.mqtt.python.git /tmp/paho_temp
    if [ -d "/tmp/paho_temp/src/paho" ]; then
        cp -r /tmp/paho_temp/src/paho /tmp/VisionPiRepoUpdate/VisionPi2000/paho
        echo "paho-mqtt erfolgreich eingebettet!"
    else
        echo "WARNUNG: Konnte paho-mqtt nicht von GitHub laden."
    fi
    rm -rf /tmp/paho_temp
fi

# 1.2 qrcode direkt als reines Python-Modul in den Spielordner einbetten (Trixie-sicher ohne apt/pip!)
if [ ! -d "/tmp/VisionPiRepoUpdate/VisionPi2000/qrcode" ]; then
    echo "Bette qrcode Bibliothek direkt in das Spielverzeichnis ein..."
    mkdir -p /tmp/qrcode_temp
    git clone --depth 1 https://github.com/lincolnloop/python-qrcode.git /tmp/qrcode_temp
    if [ -d "/tmp/qrcode_temp/qrcode" ]; then
        cp -r /tmp/qrcode_temp/qrcode /tmp/VisionPiRepoUpdate/VisionPi2000/qrcode
        echo "qrcode erfolgreich eingebettet!"
    else
        echo "WARNUNG: Konnte qrcode nicht von GitHub laden."
    fi
    rm -rf /tmp/qrcode_temp
fi

# 2. Sounds direkt im schnellen RAM vorab generieren
echo "Generiere Sounds im RAM..."
cd /tmp/VisionPiRepoUpdate/VisionPi2000
mkdir -p sounds
if [ -f "generate_sounds.py" ]; then
    python3 generate_sounds.py
fi

# 3. Boot-Verzeichnis für settings.json ermitteln
BOOT_DIR="/boot/firmware"
if [ ! -d "$BOOT_DIR" ]; then BOOT_DIR="/boot"; fi

if [ ! -f "$BOOT_DIR/settings.json" ]; then
    echo '{"format": "4:3", "mapper": "display_mapper_Vision_Dart", "branch": "stable", "mqtt_broker": "broker.emqx.io"}' | sudo tee "$BOOT_DIR/settings.json" > /dev/null
    sudo chmod 666 "$BOOT_DIR/settings.json"
fi

# 4. PRÜFUNG: Ist das System im OverlayFS-Modus (/media/root-ro existiert) oder offen?
if mountpoint -q /media/root-ro; then
    echo "OverlayFS erkannt! Öffne /media/root-ro kurzzeitig zum Schreiben..."
    sudo mount -o remount,rw /media/root-ro
    if [ $? -ne 0 ]; then
        echo "FEHLER: Konnte /media/root-ro nicht entsperren!"
        rm -rf /tmp/VisionPiRepoUpdate
        exit 1
    fi
    SYS_ROOT="/media/root-ro"
    TARGET_DIR="/media/root-ro/home/visionpi2000/VisionPi2000"
    OVERLAY_ACTIVE=1
else
    echo "Standard-Dateisystem erkannt. Schreibe direkt..."
    SYS_ROOT=""
    TARGET_DIR="/home/visionpi2000/VisionPi2000"
    OVERLAY_ACTIVE=0
fi

echo "Aktualisiere Spieldateien (inkl. eingebettetem paho-mqtt & qrcode) in $TARGET_DIR..."
sudo mkdir -p "$TARGET_DIR"
sudo rm -rf "$TARGET_DIR"/*
sudo cp -r /tmp/VisionPiRepoUpdate/VisionPi2000/* "$TARGET_DIR"/

# Symlink zur settings.json auf der Boot-Partition wiederherstellen
sudo rm -f "$TARGET_DIR/settings.json"
sudo ln -s "$BOOT_DIR/settings.json" "$TARGET_DIR/settings.json"

# Dateiberechtigungen auf dem Zielsystem glattziehen
sudo chown -R visionpi2000:visionpi2000 "$TARGET_DIR"

# =====================================================================
# 5. SYSTEM-OPTIMIERUNGEN FÜR BESTANDSAUTOMATEN PERMANENT NACHRÜSTEN
# =====================================================================
echo "Wende RAM-, Journal- und WLAN-Optimierungen dauerhaft auf das System an..."

# 5.1 WLAN-Ländercode (DE) fest in cmdline.txt auf der Boot-Partition verankern
CMDLINE_FILE="$BOOT_DIR/cmdline.txt"
if [ -f "$CMDLINE_FILE" ]; then
    if ! grep -q "cfg80211.ieee80211_regdom=" "$CMDLINE_FILE"; then
        echo "Setze WLAN-Ländercode (DE) fest in $CMDLINE_FILE..."
        sudo sed -i 's/$/ cfg80211.ieee80211_regdom=DE/' "$CMDLINE_FILE"
    fi
fi

# 5.2 Persistente systemd-rfkill Sperren auf der echten SD-Karte auf 0 (entsperrt) setzen
if [ -d "${SYS_ROOT}/var/lib/systemd/rfkill" ]; then
    for rf in "${SYS_ROOT}"/var/lib/systemd/rfkill/*; do
        [ -f "$rf" ] && echo 0 | sudo tee "$rf" > /dev/null
    done
fi

# 5.3 NetworkManager State-Datei direkt auf der echten SD-Karte auf WirelessEnabled=true setzen
sudo mkdir -p "${SYS_ROOT}/var/lib/NetworkManager"
cat << 'EOF' | sudo tee "${SYS_ROOT}/var/lib/NetworkManager/NetworkManager.state" > /dev/null
[main]
NetworkingEnabled=true
WirelessEnabled=true
WWANEnabled=true
EOF

# 5.4 WPS-Dummy-Profil direkt als echte Datei auf die SD-Karte schreiben, falls noch kein WLAN existiert
NM_CONN_DIR="${SYS_ROOT}/etc/NetworkManager/system-connections"
sudo mkdir -p "$NM_CONN_DIR"
if [ -z "$(sudo ls -A "$NM_CONN_DIR"/*.nmconnection 2>/dev/null)" ]; then
    echo "[INFO] Bestandsautomat hat kein WLAN-Profil. Schreibe permanentes WPS-Dummy-Profil..."
    cat << 'EOF' | sudo tee "$NM_CONN_DIR/VisionPi-Setup.nmconnection" > /dev/null
[connection]
id=VisionPi-Setup
uuid=8f8b4e2a-1b3c-4d5e-9f0a-123456789abc
type=wifi
interface-name=wlan0
autoconnect=false

[wifi]
mode=infrastructure
ssid=VisionPi-Setup

[wifi-security]
key-mgmt=wpa-psk
psk=DummyPassword12345678

[ipv4]
method=auto

[ipv6]
addr-gen-mode=default
method=auto
EOF
    sudo chmod 600 "$NM_CONN_DIR/VisionPi-Setup.nmconnection"
    sudo chown root:root "$NM_CONN_DIR/VisionPi-Setup.nmconnection"
    echo "[INFO] WPS-Dummy-Profil erfolgreich auf SD-Karte hinterlegt."
else
    echo "[INFO] WLAN-Profil bereits auf SD-Karte vorhanden."
fi

# 5.5 Openbox-Autostart auf der SD-Karte aktualisieren (automatischer WLAN-Restore aus settings.json beim Booten)
OPENBOX_DIR="${SYS_ROOT}/home/visionpi2000/.config/openbox"
sudo mkdir -p "$OPENBOX_DIR"
cat << 'EOF' | sudo tee "$OPENBOX_DIR/autostart" > /dev/null
# Mauszeiger nach 0,1 Sekunden Inaktivität komplett ausblenden
unclutter -idle 0.1 -root &

# Bildschirmschoner und Stromsparmodus von X11 deaktivieren
xset s off
xset -dpms
xset s noblank

# Gespeichertes WLAN aus settings.json beim Booten automatisch wiederherstellen
python3 -c '
import json, subprocess, os
for p in ["/boot/firmware/settings.json", "/boot/settings.json"]:
    if os.path.exists(p):
        try:
            d = json.load(open(p))
            ssid = d.get("wifi_ssid") or d.get("ssid") or d.get("wlan_ssid")
            psk = d.get("wifi_psk") or d.get("psk") or d.get("wifi_password") or d.get("password") or d.get("wlan_psk")
            if ssid and psk:
                subprocess.run(["sudo", "nmcli", "radio", "wifi", "on"], stderr=subprocess.DEVNULL)
                r = subprocess.run(["sudo", "nmcli", "connection", "modify", "VisionPi-Setup", "802-11-wireless.ssid", str(ssid), "802-11-wireless-security.key-mgmt", "wpa-psk", "802-11-wireless-security.psk", str(psk), "connection.autoconnect", "yes"], stderr=subprocess.DEVNULL)
                if r.returncode != 0:
                    subprocess.run(["sudo", "nmcli", "connection", "add", "type", "wifi", "ifname", "wlan0", "con-name", "VisionPi-Setup", "ssid", str(ssid), "wifi-sec.key-mgmt", "wpa-psk", "wifi-sec.psk", str(psk), "autoconnect", "yes"], stderr=subprocess.DEVNULL)
                subprocess.run(["sudo", "nmcli", "connection", "up", "VisionPi-Setup"], stderr=subprocess.DEVNULL)
        except Exception:
            pass
        break
' &

# In den Spielordner wechseln und starten
cd /home/visionpi2000/VisionPi2000
python3 visionpi.py &
EOF
sudo chown -R visionpi2000:visionpi2000 "${SYS_ROOT}/home/visionpi2000/.config"

# 5.6 Systemd-Journal im RAM auf max. 16 MB deckeln (verhindert Volllaufen des 1GB RAM!)
sudo mkdir -p "${SYS_ROOT}/etc/systemd/journald.conf.d"
cat << 'EOF' | sudo tee "${SYS_ROOT}/etc/systemd/journald.conf.d/size-limit.conf" > /dev/null
[Journal]
Storage=volatile
RuntimeMaxUse=16M
RuntimeMaxFileSize=4M
EOF

# 5.7 WLAN-Powersave dauerhaft abschalten (stabile Online-Matches & Webstream)
sudo mkdir -p "${SYS_ROOT}/etc/NetworkManager/conf.d"
cat << 'EOF' | sudo tee "${SYS_ROOT}/etc/NetworkManager/conf.d/default-wifi-powersave-off.conf" > /dev/null
[connection]
wifi.powersave = 2
EOF

# 5.8 Unnötige Hintergrunddienste permanent auf der SD-Karte deaktivieren
UNUSED_SERVICES=(
    "bluetooth.service"
    "hciuart.service"
    "ModemManager.service"
    "avahi-daemon.service"
    "avahi-daemon.socket"
    "cups.service"
    "cups-browsed.service"
    "triggerhappy.service"
    "triggerhappy.socket"
    "apt-daily.timer"
    "apt-daily-upgrade.timer"
    "man-db.timer"
)

if [ "$OVERLAY_ACTIVE" -eq 1 ]; then
    for svc in "${UNUSED_SERVICES[@]}"; do
        sudo chroot /media/root-ro systemctl disable "$svc" 2>/dev/null
    done
else
    for svc in "${UNUSED_SERVICES[@]}"; do
        sudo systemctl stop "$svc" 2>/dev/null
        sudo systemctl disable "$svc" 2>/dev/null
    done
fi

# RAM aufräumen
rm -rf /tmp/VisionPiRepoUpdate

# Schreibpuffer zwingend auf die SD-Karte leeren
sync

# Falls OverlayFS aktiv war, die echte SD-Karte sofort wieder verriegeln
if [ "$OVERLAY_ACTIVE" -eq 1 ]; then
    echo "Verriegle /media/root-ro wieder (Read-Only)..."
    sudo mount -o remount,ro /media/root-ro
fi

echo "========================================================================="
echo "Update & System-Optimierung erfolgreich! Permanent auf SD-Karte gespeichert."
echo "Das System wird in 5 Sekunden neu gestartet..."
echo "========================================================================="
sleep 5
sudo reboot
