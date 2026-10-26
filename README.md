# VisionPi2000 / OpenRetroDart

**Ein alternatives, plattformunabhängiges Open-Source-Software- und Hardwaresystem zur Restauration und Modernisierung klassischer elektronischer Dartautomaten der 90er- und 2000er-Jahre (z. B. Turnierdart 2000 / Vision Dart Gehäuse).**

> **Wichtiger rechtlicher Hinweis (Disclaimer):**  
> *Dieses Projekt ist eine unabhängige, private Hobby-Entwicklung und steht in keinerlei Verbindung, Partnerschaft oder Sponsoring zu den Herstellern der Original-Hardware (wie Löwen-Entertainment o. Ä.). Alle genannten Marken-, Produkt- und Firmennamen sind Eigentum ihrer jeweiligen Inhaber und dienen hier ausschließlich der technischen Identifikation und Kompatibilitätsbeschreibung (Ersatzteil-, Reparatur- und Retrofit-Kontext). Das System greift nicht in geschützte Herstellungsverfahren ein, sondern stellt eine freie, alternative Open-Source-Firmware bereit, um defekte Original-Steuereinheiten privater Altgeräte durch moderne Eigenbau-Komponenten (z. B. Raspberry Pi / Arduino) zu ersetzen.*

---

## 🎯 Über das Projekt & Zielsetzung

Klassische Dartautomaten aus den späten 90er- und 2000er-Jahren (wie der **Turnierdart 2000** oder das **Vision Dart**) sind mechanisch oft unverwüstlich, leiden heute jedoch häufig unter defekten, veralteten oder nicht mehr beschaffbaren Original-Hauptplatinen (CPU-Boards). 

**VisionPi2000** bietet eine nachhaltige Open-Source-Lösung, um solche Automaten vor dem Elektroschrott zu bewahren. Das Konzept erlaubt es, die **voll funktionsfähige Original-Peripherie** weiterzuverwenden – namentlich:
* Das originale Gehäuse und die Treffer-Matrix,
* Die originalen kaskadierten MAX7219-basierten LED-/Segmentanzeigen, Cricket-Markierungen und Spieler-Statuslampen,
* Die originale **5-Tasten-Bedienung** (Rot, Blau, Grau, Start, Spielerwechsel) für die komplette Navigation und Steuerung im Gehäuse.

*(Hinweis zur Sensorik: Die gesamte Sensorik wird an dieser Stelle durch moderne Komponenten ersetzt und mit einer neuen, flexiblen Softwarelogik gesteuert).*

---

## ⚙️ Technische Besonderheiten des Systems

* **Präzises Hardware-Mapping (Display-Mapper):** Die mitgelieferte `display_mapper_Vision_Dart.py` wurde speziell für das originale Display-Layout des **Turnierdart 2000 / Vision Dart** entwickelt. Sie berücksichtigt exakt die platinenspezifischen Segment- und Zeilen-Zuordnungen der **klassischen Ausführung mit bedrahteten THT-LEDs** (keine SMD-Bestückung).
* **Vollständige 5-Tasten-Bedienung:** Die Software ist kompromisslos auf die Bedienung über die originalen Gehäusetasten optimiert, sodass kein externer Computer-Bildschirm oder Maus/Tastatur im Normalbetrieb notwendig ist.
* **Umfangreicher Spielekatalog:** Inklusive X01 (301, 501, 701 mit diversen In/Out-Optionen), Cricket, Shanghai, Split Score, Around the Clock, Elimination sowie einem integrierten Solo-/Bot-Modus (*Bullseye-Berry*).
* **Dynamische Bildschirmskalierung (Letterboxing):** Automatische Skalierung der GUI. Das System zwingt moderne 16:9-Monitore durch intelligente Skalierung (Letterboxing) in ein klassisches 4:3-Format, ohne dass runde Elemente (wie die virtuelle Dartscheibe oder Grafiken) verzerrt oder gestreckt werden.

---

## 🛠️ Neue Funktionen (ab Version 1.5)

* **Ausfallsicheres Betriebssystem (Read-Only OS):** Das System ist dafür ausgelegt, auf einem schreibgeschützten (Read-Only) Raspberry Pi Image betrieben zu werden. Dies verhindert korrupte SD-Karten, wenn der Automat "hart" über den Hauptschalter ausgeschaltet wird. Einstellungen werden auf einer separaten Partition (`settings.json`) gespeichert.
* **Integriertes Service-Menü & Hardware-Diagnose:** Ein direkt über die Gehäusetasten erreichbares Menü ermöglicht tiefgreifende Hardware-Tests (Matrix-Drucktest, Sensor-Prüfung, Chip- und Segment-Tests für die MAX7219-Kaskaden) sowie das Umschalten von Bildschirmformaten.
* **Online-Update (OTA) am Automaten:** Über das Service-Menü kann das System auf Knopfdruck per Shell-Skript aktualisiert werden. Das Skript entsperrt das Read-Only-Dateisystem automatisch (`remount,rw`), zieht die neuesten Updates aus dem Repository und schützt das System anschließend sofort wieder (`remount,ro`).

---

## 🧰 Benötigte Hardware & Stückliste

*(Eine detaillierte Stückliste mit exakten Bauteilbezeichnungen, Pin-Belegungen und Bezugsquellen wird in Kürze in diesem Repository ergänzt.)*

Grob-Übersicht des Setups:
* **Host-System:** Raspberry Pi (z. B. Pi 4B oder 3B) für die Programmlogik und das User Interface.
* **Interface-Brücke:** Arduino Mega zur Ansteuerung der Matrix, der gemultiplexten LED-/Segmentanzeigen (MAX7219-Kaskaden) sowie der modernen Sensor-Komponenten.
* **Anzeigen-Peripherie:** Originale LED-Kaskaden und Segmentdisplays des Automaten (in **bedrahteter Ausführung**).

---

## 🚀 Installation & Schnellstart

1. **Arduino vorbereiten:** Flashe den bereitgestellten Arduino-Sketch (`Arduino-MEGA-2560_Schnittstellen_VisionPi2000.ino`) auf den Arduino Mega.
2. **Abhängigkeiten installieren (Python):** Auf dem Raspberry Pi (oder einem Test-Rechner) müssen Pygame und PySerial installiert werden.
   ```bash
   pip install pygame pyserial
   
