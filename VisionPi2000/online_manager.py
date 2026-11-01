# Datei: online_manager.py
# Version: 1.1.1
# P2P / MQTT Online-Engine mit eindeutigen Lobby-IDs, Handshake & Serial-Proxy

import os
import re
import json
import time
import uuid
import queue
import random
import hashlib
import pygame

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

VERSION = "1.1.1"

# Die 8 festen Online-Spieler-Slots für die Lobby (Die Bullseye-Berrys)
ONLINE_PLAYER_NAMES = [
    "Bullseye-Berry",       # Slot 0 (Spieler 1 / Host)
    "Triple-Strawberry",    # Slot 1 (Spieler 2)
    "Bouncer-Blueberry",    # Slot 2 (Spieler 3)
    "Checkout-Cherry",      # Slot 3 (Spieler 4)
    "Double-Dewberry",      # Slot 4 (Spieler 5)
    "Flight-Huckleberry",   # Slot 5 (Spieler 6)
    "Scoring-Snowberry",    # Slot 6 (Spieler 7)
    "Master-Mulberry"       # Slot 7 (Spieler 8)
]

GAME_TO_FILE = {
    "301": "game_x01.py",
    "501": "game_x01.py",
    "701": "game_x01.py",
    "Cricket": "game_cricket.py",
    "Elimination": "game_elimination.py",
    "Split Score": "game_splitscore.py",
    "Shanghai": "game_shanghai.py",
    "Around the Clock": "game_aroundclock.py"
}

DISCOVERY_TOPIC = "visionpi2000/v1/discovery"


def get_file_signature(filepath):
    """Berechnet den SHA-256 Hash und liest den VERSION-String per Regex aus."""
    if not os.path.exists(filepath):
        return {"exists": False, "sha256": "", "version": "missing"}
    try:
        with open(filepath, "rb") as f:
            raw_bytes = f.read()
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()
        content = raw_bytes.decode("utf-8", errors="ignore")
        match = re.search(
            r'^(?:VERSION|__version__)\s*=\s*["\']([^"\']+)["\']',
            content,
            re.MULTILINE
        )
        ver_str = match.group(1) if match else "unknown"
        return {"exists": True, "sha256": sha256_hash, "version": ver_str}
    except Exception as e:
        return {"exists": False, "sha256": "", "version": f"err:{e}"}


def build_local_manifest(game_name):
    """Erstellt die Prüfsummen für visionpi.py und das gewählte Spielmodul."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    game_file = GAME_TO_FILE.get(game_name, "game_x01.py")
    return {
        "visionpi.py": get_file_signature(os.path.join(base_dir, "visionpi.py")),
        game_file: get_file_signature(os.path.join(base_dir, game_file))
    }


def verify_manifests(host_manifest, local_manifest):
    """Vergleicht die lokalen Dateien des Gastes mit den Vorgaben des Hosts."""
    mismatches = []
    for fname, h_sig in host_manifest.items():
        l_sig = local_manifest.get(fname, {})
        if not l_sig.get("exists"):
            mismatches.append(f"{fname} fehlt lokal")
        elif h_sig.get("version") != l_sig.get("version"):
            mismatches.append(
                f"{fname} Version ({l_sig.get('version')} != {h_sig.get('version')})"
            )
        elif h_sig.get("sha256") != l_sig.get("sha256"):
            mismatches.append(f"{fname} Datei-Hash weicht ab (Code unterschiedlich)")
    return (len(mismatches) == 0), mismatches


class OnlineSession:
    def __init__(self, broker="broker.emqx.io", port=1883):
        self.broker = broker
        self.port = port
        self.client_id = f"vp2000_{uuid.uuid4().hex[:8]}"
        self.room_id = ""
        self.room_topic = ""

        self.is_host = False
        self.connected = False
        self.error_msg = ""

        # Speichert alle aktiven Lobbys im Netz: { "Lobby-XXXX": { ... info ... } }
        self.active_rooms = {}

        # Lobby-Status
        self.players = []
        self.local_slots = []
        self.game_name = "501"
        self.option = "Double Out"
        self.match_seed = 0
        self.match_started = False
        self.host_manifest = {}
        self.handshake_ok = False
        self.handshake_status = "Suche nach kollisionsfreien Lobbys..."

        self.incoming_serial_queue = queue.Queue()

        self.client = None
        if MQTT_AVAILABLE:
            try:
                if hasattr(mqtt, "CallbackAPIVersion"):
                    self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, self.client_id)
                else:
                    self.client = mqtt.Client(self.client_id)
                self.client.on_connect = self._on_connect
                self.client.on_message = self._on_message
                self.client.on_disconnect = self._on_disconnect
            except Exception as e:
                self.error_msg = f"MQTT Init Fehler: {e}"
        else:
            self.error_msg = "paho-mqtt fehlt! (sudo apt install python3-paho-mqtt)"

    def connect(self):
        if not self.client:
            return False
        try:
            self.client.connect_async(self.broker, self.port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            self.error_msg = f"Verbindungsfehler: {e}"
            return False

    def disconnect(self):
        if self.is_host and self.room_id and self.connected:
            try:
                self.client.publish(DISCOVERY_TOPIC, json.dumps({
                    "type": "room_closed",
                    "room_id": self.room_id,
                    "host_id": self.client_id
                }), qos=1)
            except:
                pass
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except:
                pass
        self.connected = False

    def join_room_topic(self, new_room_id):
        if self.room_topic and self.connected:
            try:
                self.client.unsubscribe(self.room_topic)
            except:
                pass
        self.room_id = new_room_id
        self.room_topic = f"visionpi2000/v1/room/{new_room_id}"
        if self.connected and new_room_id:
            try:
                self.client.subscribe(self.room_topic, qos=1)
            except:
                pass

    def generate_unique_room_id(self):
        """Erzeugt eine absolut kollisionsfreie, eindeutige Lobby-ID mit Zufalls-Hex."""
        suffix = uuid.uuid4().hex[:4].upper()
        return f"Lobby-{suffix}"

    def get_open_lobbies(self):
        """Liefert alle aktuell offenen Lobbys für Gäste zurück."""
        now = time.time()
        open_list = []
        for r_id, info in sorted(self.active_rooms.items()):
            if (now - info.get("ts", 0) < 6.0) and info.get("state") == "OPEN":
                open_list.append(r_id)
        return open_list

    def publish_room(self, payload):
        if not self.client or not self.connected or not self.room_topic:
            return
        payload["sender_id"] = self.client_id
        try:
            self.client.publish(self.room_topic, json.dumps(payload), qos=1)
        except:
            pass

    def broadcast_discovery_beacon(self):
        """Sendet als Host den Status auf dem globalen Discovery-Kanal."""
        if not self.is_host or not self.connected or not self.room_id:
            return
        state = "PLAYING" if self.match_started else "OPEN"
        beacon = {
            "type": "room_beacon",
            "room_id": self.room_id,
            "host_id": self.client_id,
            "state": state,
            "game_name": self.game_name,
            "option": self.option,
            "players_count": len(self.players)
        }
        try:
            self.client.publish(DISCOVERY_TOPIC, json.dumps(beacon), qos=0)
        except:
            pass

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            client.subscribe(DISCOVERY_TOPIC, qos=1)
            if self.room_topic:
                client.subscribe(self.room_topic, qos=1)
        else:
            self.error_msg = f"Broker-Fehlercode: {rc}"

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except:
            return

        if msg.topic == DISCOVERY_TOPIC:
            m_type = data.get("type")
            r_id = data.get("room_id")
            h_id = data.get("host_id")
            if m_type == "room_beacon" and r_id:
                # Kollisions-Schutz: Sollte per extremem Zufall eine Lobby-ID doppelt vergeben werden,
                # generiert der jüngere Host sofort einen neuen eindeutigen Code.
                if (self.is_host and not self.match_started and r_id == self.room_id
                        and h_id and h_id != self.client_id):
                    new_id = self.generate_unique_room_id()
                    self.join_room_topic(new_id)
                    self.broadcast_discovery_beacon()
                    return

                self.active_rooms[r_id] = {
                    "host_id": h_id,
                    "state": data.get("state", "OPEN"),
                    "game_name": data.get("game_name", ""),
                    "option": data.get("option", ""),
                    "players_count": data.get("players_count", 1),
                    "ts": time.time()
                }
            elif m_type == "room_closed" and r_id in self.active_rooms:
                del self.active_rooms[r_id]
            return

        sender = data.get("sender_id")
        msg_type = data.get("type")

        if self.is_host:
            if msg_type == "guest_hello" and not self.match_started:
                req_count = max(1, min(8, int(data.get("local_players", 1))))
                existing = [p for p in self.players if p["client_id"] == sender]
                if not existing and len(self.players) + req_count <= 8:
                    for _ in range(req_count):
                        slot_idx = len(self.players)
                        self.players.append({
                            "slot": slot_idx,
                            "name": ONLINE_PLAYER_NAMES[slot_idx],
                            "client_id": sender
                        })
                self.broadcast_lobby_state()

            elif msg_type == "game_event" and sender != self.client_id:
                cmd = data.get("cmd")
                if cmd:
                    self.incoming_serial_queue.put(cmd)

        else:
            if msg_type == "host_lobby":
                self.game_name = data.get("game_name", "501")
                self.option = data.get("option", "Standard")
                self.host_manifest = data.get("manifest", {})
                self.players = data.get("players", [])
                self.local_slots = [
                    p["slot"] for p in self.players if p["client_id"] == self.client_id
                ]

                local_man = build_local_manifest(self.game_name)
                ok, errors = verify_manifests(self.host_manifest, local_man)
                self.handshake_ok = ok
                if ok:
                    if self.local_slots:
                        my_names = ", ".join(
                            [ONLINE_PLAYER_NAMES[s] for s in self.local_slots]
                        )
                        self.handshake_status = f"Handshake OK ({self.room_id})! Du bist: {my_names}"
                    else:
                        self.handshake_status = f"Code verifiziert ({self.room_id})! Fordere Slot an..."
                else:
                    self.handshake_status = "VERSION KONFLIKT: " + " | ".join(errors)

            elif msg_type == "match_start":
                if self.handshake_ok and self.local_slots:
                    self.players = data.get("players", self.players)
                    self.local_slots = [
                        p["slot"] for p in self.players if p["client_id"] == self.client_id
                    ]
                    self.match_seed = data.get("seed", 12345)
                    self.match_started = True

            elif msg_type == "game_event" and sender != self.client_id:
                cmd = data.get("cmd")
                if cmd:
                    self.incoming_serial_queue.put(cmd)

    def broadcast_lobby_state(self):
        if not self.is_host:
            return
        self.broadcast_discovery_beacon()
        self.publish_room({
            "type": "host_lobby",
            "game_name": self.game_name,
            "option": self.option,
            "manifest": self.host_manifest,
            "players": self.players
        })


class OnlineDisplayProxy:
    def __init__(self, real_display, session, screen):
        self._real = real_display
        self._session = session
        self._screen = screen
        self.active_player_idx = 0
        self.darts_left = 3
        sh = screen.get_height()
        self.banner_font = pygame.font.SysFont("arial", int(sh * 0.022), bold=True)

    def set_active_player(self, active_player_idx):
        self.active_player_idx = active_player_idx
        self.darts_left = 3
        if self._real:
            self._real.set_active_player(active_player_idx)

    def set_dart_arrows(self, arrows_count):
        self.darts_left = arrows_count
        if self._real:
            self._real.set_dart_arrows(arrows_count)

    def draw_online_hud(self):
        if not self._screen or not self._session.players:
            return
        idx = self.active_player_idx
        if 0 <= idx < len(self._session.players):
            p_info = self._session.players[idx]
            p_name = p_info["name"]
            is_local = (idx in self._session.local_slots)
            status_txt = "DU BIST AM WURF" if is_local else "ONLINE-GEGNER WIRFT"
            bg_col = (20, 110, 40) if is_local else (130, 30, 30)

            text = f"ONLINE [{self._session.room_id}]  •  Spieler {idx + 1}: {p_name} ({status_txt})"
            surf = self.banner_font.render(text, True, (255, 255, 255))
            sw = self._screen.get_width()
            pad_x, pad_y = 18, 4
            rect_w = surf.get_width() + pad_x * 2
            rect_h = surf.get_height() + pad_y * 2
            rect_x = (sw - rect_w) // 2

            pygame.draw.rect(
                self._screen, bg_col, (rect_x, 4, rect_w, rect_h), border_radius=8
            )
            pygame.draw.rect(
                self._screen, (255, 215, 0), (rect_x, 4, rect_w, rect_h), width=2, border_radius=8
            )
            self._screen.blit(surf, (rect_x + pad_x, 4 + pad_y))

    def __getattr__(self, name):
        return getattr(self._real, name)


class OnlineSerialProxy:
    def __init__(self, real_ser, session, display_proxy):
        self._real_ser = real_ser
        self._session = session
        self._disp = display_proxy
        self._ready_queue = queue.Queue()
        self._last_ir_sent = 0
        self._last_beacon = time.time()

    def _poll(self):
        if self._session.is_host and (time.time() - self._last_beacon > 3.0):
            self._last_beacon = time.time()
            self._session.broadcast_discovery_beacon()

        while not self._session.incoming_serial_queue.empty():
            try:
                net_cmd = self._session.incoming_serial_queue.get_nowait()
                self._ready_queue.put(net_cmd)
            except:
                break

        if self._real_ser and self._real_ser.in_waiting > 0:
            try:
                raw_line = self._real_ser.readline().decode("utf-8", "ignore").strip()
            except:
                raw_line = ""

            if raw_line:
                is_my_turn = (self._disp.active_player_idx in self._session.local_slots)

                if raw_line == "BTN:COMBO":
                    self._ready_queue.put(raw_line)

                elif is_my_turn:
                    if raw_line.startswith("HIT:") or raw_line == "MISS:1":
                        self._session.publish_room({"type": "game_event", "cmd": raw_line})
                        self._ready_queue.put(raw_line)

                    elif raw_line in ["BTN:PLAYER", "BTN:START"]:
                        self._session.publish_room({"type": "game_event", "cmd": raw_line})
                        self._ready_queue.put(raw_line)

                    elif raw_line == "IR:DETECT":
                        if self._disp.darts_left <= 0 and (time.time() - self._last_ir_sent > 2.0):
                            self._last_ir_sent = time.time()
                            self._session.publish_room({"type": "game_event", "cmd": "IR:DETECT"})
                            self._ready_queue.put("IR:DETECT")

    @property
    def in_waiting(self):
        self._poll()
        return self._ready_queue.qsize()

    def readline(self):
        self._poll()
        if not self._ready_queue.empty():
            cmd = self._ready_queue.get_nowait()
            return (cmd + "\n").encode("utf-8")
        return b""

    def write(self, data):
        if self._real_ser:
            try:
                return self._real_ser.write(data)
            except:
                pass

    def flush(self):
        if self._real_ser:
            try:
                return self._real_ser.flush()
            except:
                pass

    def reset_input_buffer(self):
        if self._real_ser:
            try:
                self._real_ser.reset_input_buffer()
            except:
                pass
        with self._ready_queue.mutex:
            self._ready_queue.queue.clear()


def run_online_lobby_and_match(screen, ser, display, local_players, game_name, option, is_host, game_mod, settings):
    sw, sh = screen.get_width(), screen.get_height()
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", int(sh * 0.040), bold=True)
    sub_font = pygame.font.SysFont("arial", int(sh * 0.026), bold=True)
    list_font = pygame.font.SysFont("arial", int(sh * 0.028), bold=True)
    small_font = pygame.font.SysFont("arial", int(sh * 0.021), bold=True)

    HIGHLIGHT = (255, 215, 0)
    WHITE = (255, 255, 255)
    GREEN = (80, 255, 80)
    RED_COL = (220, 50, 50)

    broker = settings.get("mqtt_broker", "broker.emqx.io")

    session = OnlineSession(broker=broker)
    session.is_host = is_host
    session.game_name = game_name
    session.option = option

    if is_host:
        session.host_manifest = build_local_manifest(game_name)
        for i in range(min(8, local_players)):
            session.players.append({
                "slot": i,
                "name": ONLINE_PLAYER_NAMES[i],
                "client_id": session.client_id
            })
        session.local_slots = list(range(len(session.players)))
        session.handshake_ok = True
        # Generiere sofort eine eindeutige, kollisionsfreie Lobby-ID
        unique_id = session.generate_unique_room_id()
        session.join_room_topic(unique_id)
        session.handshake_status = f"{unique_id} geöffnet – SHA-256 bereit!"

    session.connect()

    last_broadcast = 0
    in_lobby = True

    while in_lobby:
        raw_data = ser.readline().decode("utf-8", "ignore").strip() if ser and ser.in_waiting > 0 else None
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                session.disconnect()
                return "menu"
            elif ev.type == pygame.KEYDOWN:
                if ev.key in [pygame.K_p, pygame.K_ESCAPE]:
                    raw_data = "BTN:PLAYER"
                elif ev.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    raw_data = "BTN:START"
                elif ev.key == pygame.K_b:
                    raw_data = "BTN:BLUE"

        if raw_data == "BTN:PLAYER":
            session.disconnect()
            return "menu"

        elif raw_data == "BTN:BLUE" and not is_host:
            open_lobbies = session.get_open_lobbies()
            if len(open_lobbies) > 1:
                cur_idx = open_lobbies.index(session.room_id) if session.room_id in open_lobbies else -1
                next_room = open_lobbies[(cur_idx + 1) % len(open_lobbies)]
                session.players = []
                session.local_slots = []
                session.handshake_ok = False
                session.join_room_topic(next_room)
                session.handshake_status = f"Wechsle zu {next_room}..."

        elif raw_data == "BTN:START" and is_host and session.room_id:
            if len(session.players) >= 1 and session.connected:
                session.match_seed = random.randint(100000, 999999)
                session.match_started = True
                session.broadcast_discovery_beacon()
                session.publish_room({
                    "type": "match_start",
                    "players": session.players,
                    "seed": session.match_seed
                })
                time.sleep(0.15)

        if session.connected:
            if not is_host:
                open_lobbies = session.get_open_lobbies()
                if not session.room_id and open_lobbies:
                    session.join_room_topic(open_lobbies[0])
                    session.handshake_status = f"Lobby {open_lobbies[0]} gefunden – prüfe Versionen..."
                elif session.room_id and session.room_id not in open_lobbies and not session.local_slots:
                    if open_lobbies:
                        session.join_room_topic(open_lobbies[0])

            if time.time() - last_broadcast > 1.2:
                last_broadcast = time.time()
                if is_host and session.room_id:
                    session.broadcast_lobby_state()
                elif not is_host and session.room_id:
                    if session.handshake_ok and not session.local_slots:
                        session.publish_room({
                            "type": "guest_hello",
                            "local_players": local_players
                        })

        if session.match_started:
            in_lobby = False
            break

        screen.fill((12, 14, 24))
        box_w, box_h = int(sw * 0.86), int(sh * 0.86)
        box_x, box_y = (sw - box_w) // 2, (sh - box_h) // 2
        pygame.draw.rect(screen, (18, 22, 36), (box_x, box_y, box_w, box_h), border_radius=16)
        pygame.draw.rect(screen, HIGHLIGHT, (box_x, box_y, box_w, box_h), width=3, border_radius=16)

        role_str = "HOST-LOBBY" if is_host else "GAST-BEITRITT"
        head_surf = title_font.render(f"VISION PI 2000 ONLINE  •  {role_str}", True, HIGHLIGHT)
        screen.blit(head_surf, ((sw - head_surf.get_width()) // 2, box_y + int(box_h * 0.04)))

        room_disp = session.room_id if session.room_id else "Suche offene Lobbys..."
        sub_txt = f"Spiel: {session.game_name} ({session.option})   |   Lobby-ID: {room_disp}"
        sub_surf = sub_font.render(sub_txt, True, WHITE)
        screen.blit(sub_surf, ((sw - sub_surf.get_width()) // 2, box_y + int(box_h * 0.12)))

        if session.error_msg:
            stat_col, stat_txt = RED_COL, session.error_msg
        elif not session.connected:
            stat_col, stat_txt = HIGHLIGHT, "Verbinde mit MQTT-Broker..."
        else:
            stat_col = GREEN if session.handshake_ok else HIGHLIGHT
            if not session.handshake_ok and "KONFLIKT" in session.handshake_status:
                stat_col = RED_COL
            stat_txt = session.handshake_status

        stat_surf = small_font.render(f"Status / Handshake: {stat_txt}", True, stat_col)
        screen.blit(stat_surf, ((sw - stat_surf.get_width()) // 2, box_y + int(box_h * 0.19)))

        pygame.draw.line(
            screen, (80, 80, 100),
            (box_x + 40, box_y + int(box_h * 0.25)),
            (box_x + box_w - 40, box_y + int(box_h * 0.25)), 2
        )

        slot_y = box_y + int(box_h * 0.28)
        slot_h = int(box_h * 0.068)
        for s_idx in range(8):
            berry_name = ONLINE_PLAYER_NAMES[s_idx]
            p_entry = next((p for p in session.players if p["slot"] == s_idx), None)
            if p_entry:
                is_me = (p_entry["client_id"] == session.client_id)
                tag = "LOKAL (Dieser Automat)" if is_me else "ONLINE VERBUNDEN"
                col = GREEN if is_me else HIGHLIGHT
                line_str = f"Slot {s_idx + 1}:  {berry_name:<22}  —  [{tag}]"
            else:
                col = (90, 90, 110)
                line_str = f"Slot {s_idx + 1}:  {berry_name:<22}  —  [ Frei / Wartet ]"

            s_surf = list_font.render(line_str, True, col)
            screen.blit(s_surf, (box_x + int(box_w * 0.10), slot_y + s_idx * slot_h))

        if is_host:
            hint_str = "START drücken: Online-Match starten   |   SPIELERWECHSEL: Abbrechen"
        else:
            open_cnt = len(session.get_open_lobbies())
            if open_cnt > 1:
                hint_str = f"BLAU: Lobby wechseln ({open_cnt} offen)   |   SPIELERWECHSEL: Abbrechen"
            else:
                hint_str = "Warte auf Spielstart durch den Host...   |   SPIELERWECHSEL: Abbrechen"

        hint_surf = sub_font.render(hint_str, True, HIGHLIGHT)
        screen.blit(hint_surf, ((sw - hint_surf.get_width()) // 2, box_y + box_h - int(box_h * 0.08)))

        pygame.display.flip()
        clock.tick(30)

    random.seed(session.match_seed)

    total_online_players = max(1, min(8, len(session.players)))
    disp_proxy = OnlineDisplayProxy(display, session, screen)
    ser_proxy = OnlineSerialProxy(ser, session, disp_proxy)

    orig_flip = pygame.display.flip

    def hooked_flip():
        disp_proxy.draw_online_hud()
        orig_flip()

    pygame.display.flip = hooked_flip
    try:
        game_mod.run_game(
            screen,
            ser_proxy,
            disp_proxy,
            total_online_players,
            session.game_name,
            session.option,
            "Normales Spiel"
        )
    finally:
        pygame.display.flip = orig_flip
        session.disconnect()

    return "menu"
