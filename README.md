# VisionPi2000 / OpenRetroDart

**Ein alternatives, plattformunabhängiges Open-Source-Software- und Hardwaresystem als Retrofitlösung für klassische elektronische Dartautomaten der 90er- und 2000er-Jahre (z. B. Turnierdart 2000 / Vision Dart Gehäuse).**

> **Wichtiger rechtlicher Hinweis (Disclaimer):**  
> *Dieses Projekt ist eine unabhängige, private Hobby-Entwicklung und steht in keinerlei Verbindung, Partnerschaft oder Sponsoring zu den Herstellern der Original-Hardware (wie Löwen-Entertainment o. Ä.). Alle genannten Marken-, Produkt- und Firmennamen sind Eigentum ihrer jeweiligen Inhaber und dienen hier ausschließlich der technischen Identifikation und Kompatibilitätsbeschreibung (Ersatzteil-, Reparatur- und Retrofit-Kontext). Das System greift nicht in geschützte Herstellungsverfahren ein, sondern stellt eine freie, alternative Open-Source-Firmware bereit, um defekte Original-Steuereinheiten privater Altgeräte durch moderne Eigenbau-Komponenten (z. B. Raspberry Pi / Arduino) zu ersetzen.*

---

## 🎯 Über das Projekt & Zielsetzung

Klassische Dartautomaten aus den späten 90er- und 2000er-Jahren (wie der **Turnierdart 2000** oder das **Vision Dart**) sind mechanisch oft unverwüstlich, leiden heute jedoch häufig unter defekten, veralteten oder nicht mehr beschaffbaren Original-Hauptplatinen (CPU-Boards). 

**VisionPi2000** bietet eine nachhaltige Open-Source-Retrofitlösung, um solche Automaten vor dem Elektroschrott zu bewahren. Das Konzept erlaubt es, die **voll funktionsfähige Original-Peripherie** weiterzuverwenden – namentlich:
* Das originale Gehäuse und die Treffer-Matrix,
* Die originalen kaskadierten MAX7219-basierten LED-/Segmentanzeigen, Cricket-Markierungen und Spieler-Statuslampen,
* Die originale **5-Tasten-Bedienung** (Rot, Blau, Grau, Start, Spielerwechsel) für die komplette Navigation und Steuerung im Gehäuse.

*(Hinweis zur Sensorik: Die gesamte Sensorik wird an dieser Stelle durch moderne Komponenten ersetzt und mit einer modernen, flexiblen Softwarelogik gesteuert).*

---

## ⚙️ Technische Besonderheiten des Systems

* **Präzises Hardware-Mapping (Display-Mapper):** Die mitgelieferte `display_mapper_Vision_Dart.py` wurde speziell für das originale Display-Layout des **Turnierdart 2000 / Vision Dart** entwickelt. Sie berücksichtigt exakt die platinenspezifischen Segment- und Zeilen-Zuordnungen der **klassischen Ausführung mit bedrahteter THT-LEDs** (keine SMD-Bestückung).
* **Vollständige 5-Tasten-Bedienung:** Die Software ist kompromisslos auf die Bedienung über die originalen Gehäusetasten optimiert, sodass kein externer Computer-Bildschirm oder Maus/Tastatur im Normalbetrieb notwendig ist.
* **Umfangreicher Spielekatalog:** Inklusive X01 (301, 501, 701 mit diversen In/Out-Optionen), Cricket, Shanghai, Split Score, Around the Clock, Elimination sowie einem integrierten Solo-/Bot-Modus (*Bullseye-Berry*).
* **Dynamische Bildschirmskalierung (Letterboxing):** Automatische Skalierung der GUI. Das System zwingt moderne 16:9-Monitore durch intelligente Skalierung (Letterboxing) in ein klassisches 4:3-Format, ohne dass runde Elemente (wie die virtuelle Dartscheibe oder Grafiken) verzerrt oder gestreckt werden.

---

## 🛠️ System-Eigenschaften & Betriebssystem-Hinweise (Version 1.1.0)

* **Bequeme Online-Installation:** Das System kann unkompliziert und schnell direkt per Online-Skript eingerichtet werden.
* **Ausfallsicheres Betriebssystem (Read-Only OS):** Das System ist dafür ausgelegt, auf einem schreibgeschützten (Read-Only) Raspberry Pi Image betrieben zu werden. 
  * **Vorteile:** Verhindert korrupte SD-Karten zuverlässig, wenn der Automat "hart" über den Hauptschalter ausgeschaltet wird. Einstellungen und Spielstände werden separat gespeichert.
* **Intelligente WLAN-Konfiguration:** Obwohl das System schreibgeschützt läuft, ist die WLAN-Einrichtung oder Änderung extrem einfach und komfortabel gelöst. Das System verlässt sich nicht auf eingefrorene Image-Daten, sondern liest WLAN-Zugangsdaten direkt von der FAT32-formatierten Boot-Partition aus einer `settings.json`. Dies ermöglicht zwei bequeme Wege zur WLAN-Einrichtung:
  1. **Über das Automaten-Service-Menü (WPS):** Navigiere am Automaten in das Service-Menü unter "WLAN & WPS". Drücke die Blaue Taste am Automaten und betätige die WPS-Taste an deinem Router. Das System extrahiert SSID und Passwort automatisch und sichert diese dauerhaft in der `settings.json` auf der Boot-Partition.
  2. **Manuell am PC (Offline):** Stecke die SD-Karte (oder den USB-Stick) einfach in einen Windows-, Mac- oder Linux-PC. Öffne das erkannte Laufwerk (unter Windows z. B. Laufwerk `E:\`, oft auch `bootfs` genannt) und bearbeite die direkt dort auf der obersten Ebene liegende Datei `settings.json` mit einem Texteditor. Trage dort unter `"wifi_ssid"` den Namen deines WLANs und unter `"wifi_password"` dein Passwort ein. Beim nächsten Einstecken in den Pi verbindet sich das System sofort.
* **Integriertes Service-Menü & Hardware-Diagnose:** Ein direkt über die Gehäusetasten erreichbares Menü ermöglicht tiefgreifende Hardware-Tests (Matrix-Drucktest, Sensor-Prüfung, Chip- und Segment-Tests für die MAX7219-Kaskaden) sowie das Umschalten von Bildschirmformaten. Das Menü bedient sich analog zum Hauptmenü mit **ROT** für Navigation, **BLAU** für Aktionen und **SPIELERWECHSEL** als universelle Zurück-Taste.
* **Online-Update (OTA) am Automaten:** Über das Service-Menü kann das System auf Knopfdruck per Shell-Skript aktualisiert werden. Das Skript entsperrt das Read-Only-Dateisystem automatisch (`remount,rw`), zieht die neuesten Updates aus dem Repository und schützt das System anschließend sofort wieder (`remount,ro`).

---

## 🧰 Benötigte Hardware & Stückliste

### Kernkomponenten & Peripherie
* **Host-System:** Raspberry Pi 4B (2 GB Variante) inklusive passendem Gehäuse und Micro-SD-Karte ($\ge$ 8 GB) – ca. **75,00 € – 95,00 €** (*Hinweis: Der Raspberry Pi 3B wurde aufgrund instabiler USB-Verbindungen als ungeeignet eingestuft*).
* **Interface-Brücke:** Arduino Mega 2560 Klon (kompatibles Board) – ca. **15,00 € – 20,00 €** zur Ansteuerung der Matrix, der gemultiplexten LED-/Segmentanzeigen (MAX7219-Kaskaden) sowie der modernen Sensor-Komponenten.
* **Anzeigen-Peripherie:** Originale LED-Kaskaden und Segmentdisplays des Automaten (in **bedrahteter Ausführung**).

### Ergänzende Hardware (aus Montage & Stückliste)
| Komponente | Beschreibung / Details | Ungefährer Preis |
| :--- | :--- | :--- |
| **GeeekPi Terminal Block Breakout Board** | HAT mit Reset-Button & LED-Anzeige für Arduino MEGA 2560 R3 | ca. 31,99 € |
| **Keenso Klemmenblock Breakout-Leiterplatte** | IDC20P 20Pin Schnittstellenhalterung mit DIN-Schienen-Montagefüßen | ca. 15,19 € |
| **DollaTek ATX-Netzteilplatine** | ATX-Netzteil Breakout-Transferplatine / Steckdosenverdrahtungsadapter | ca. 7,99 € |
| **Tbest Micro-HDMI-zu-VGA-Adapter** | Videokonverter-Adapter (1080P) für Raspberry Pi 4B mit Netzteilfunktion | ca. 9,87 € |
| **Nongxiang USB-Ladegerät (2er-Pack)** | 40W Mehrfachstecker (USB-A & USB-C, PD + QC3.0 Netzteile) | ca. 22,99 € |
| **Hailege E18-D80NK** | 2 Stk. Infrarot-Lichtschranken / Hindernisvermeidungssensoren | ca. 9,79 € |
| **Youmile Piezoelektrischer Keramik-Vibrationssensor** | 5 Stk. Modul Analogue Controller mit Dupont-Kabel | ca. 7,99 € |
| **JZK PAM8403 Mini Digital Verstärker** | 5 Stk. 5V 2x3W Dual Channel Mini HiFi Verstärker mit Poti | ca. 7,69 € |
| **QWORK Hutschiene (3 Stk.)** | Montageschiene DIN, 35 mm breit, 7,5 mm hoch, 300 mm lang | *Variabel* |
| **Binmiza Hutschiene Adapter Set** | 20 Stk. (10 Sätze) PCB DIN C45 Halter mit Schrauben | ca. 7,99 € |

---

### 💰 Gesamtkosten-Kalkulation (Ungefährer Richtwert)
* **Raspberry Pi 4B (2GB) inkl. Gehäuse & $\ge$8GB SD-Karte:** ca. 85,00 €
* **Arduino Mega 2560 Klon:** ca. 18,00 €
* **Zusatzhardware & Module (Breakout-Boards, ATX-Platine, Sensoren, Hutschiene etc.):** ca. 131,48 €

* **Ungefährer Gesamtpreis (Summe der Komponenten):** **ca. 234,48 €** *(exklusive variabel bepreister Hutschienen)*

---

## 🔌 Verdrahtung & Schnittstellenbeschreibung

> **⚠️ Wichtiger Sicherheitshinweis zur Verkabelung:**  
> Werden mehrere separate Netzteile/Stromquellen (z. B. USB-Netzteile für Raspberry Pi und Verstärker/Peripherie) im System verwendet, **müssen unbedingt sämtliche Massen (GND) aller verwendeten Netzteile und Komponenten sternförmig miteinander verbunden werden**, um Potentialunterschiede, Signalfehler und Fehlfunktionen bei der Datenübertragung zu verhindern!

Eine detaillierte, komplette Schnittstellenbeschreibung inklusive Pin-Belegungen, Diagrammen und der vollständigen Verdrahtungsanleitung für alle Komponenten befindet sich im beiliegenden Ordner **`arduino/`** in diesem Repository.

---

## 🚀 Installation & Schnellstart

> **⚠️ Wichtiger Hinweis für Pi4light OS (Trixi):**  
> Bei der Verwendung von Pi4light OS muss der Hauptbenutzer auf dem Raspberry Pi zwingend den Namen **`visionpi2000`** tragen, da Pfade und Skripte fest darauf ausgelegt sind!

### 1. Vorbereitung der Hardware
Flashe den bereitgestellten Arduino-Sketch (`Arduino-MEGA-2560_Schnittstellen_VisionPi2000.ino`) auf den Arduino Mega Klon.

### 2. Software-Installation (Zwei Wege)

**Weg A: Automatisierte Installation per Skript (Dringend empfohlen)**  
Das Skript installiert nicht nur das System, sondern richtet auch automatisch Autostart-Dienste, Systemabhängigkeiten (`NetworkManager`) und die korrekten Zugriffsrechte für die serielle Schnittstelle (Arduino) ein. 
Führe dazu das Installationsskript aus dem Ordner `Pi_Setup` dieses Repositories auf deinem Raspberry Pi aus.

**Weg B: Manuelle Installation (Nur für erfahrene Linux-Nutzer)**  
Wer das System komplett manuell aufsetzen möchte, muss neben dem Klonen der Python-Dateien zwingend folgende Schritte eigenständig durchführen:
* **Python-Abhängigkeiten installieren:** `pip install pygame pyserial` (bzw. über `apt install python3-pygame python3-serial`).
* **Systempakete:** Sicherstellen, dass `network-manager` (für die `nmcli`-Steuerung) und `wpasupplicant` (für WPS) installiert und aktiv sind. Ebenso `curl` für die OTA-Update-Funktion.
* **Berechtigungen:** Der ausführende Benutzer (`visionpi2000`) muss zwingend Mitglied der Gruppe `dialout` sein, um mit dem Arduino über USB/Serial kommunizieren zu dürfen (`sudo usermod -a -G dialout visionpi2000`).
* **Autostart:** Einrichten eines Systemd-Services oder einer Autostart-Routine (z. B. via `.bashrc` oder Wayland/X11-Kiosk), um `visionpi.py` beim Booten im Vollbildmodus zu starten.