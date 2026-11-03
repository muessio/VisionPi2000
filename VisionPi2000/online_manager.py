# Datei: online_manager.py
# Version: 1.2.3
# P2P / MQTT Online-Engine (Zwei-Stufen-Exit für alle Spielmodule, Crash-sicher, Surface-Cache, Disziplin-Filter)

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re
import math
import json
import time
import uuid
import queue
import random
import hashlib
import threading
import pygame

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

VERSION = "1.2.3"

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
    "Around the Clock": "game_aroundclock.py",
    "Fruit Splasher": "game_fruit_splasher.py"
}

DISCOVERY_TOPIC = "visionpi2000/v1/discovery"

# Cache für Cyber-Frames (verhindert ständige Surface-Allokation im RAM)
_frame_cache = {}


def find_image_file(preferred_names):
    if isinstance(preferred_names, str):
        preferred_names = [preferred_names]
    for name in preferred_names:
        if os.path.exists(name):
            return name
    try:
        files = os.listdir(".")
        files_lower = {f.lower(): f for f in files}
        for name in preferred_names:
            if name.lower() in files_lower:
                return files_lower[name.lower()]
    except Exception:
        pass
    return None


def get_file_signature(filepath):
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    game_file = GAME_TO_FILE.get(game_name, "game_x01.py")
    return {
        "visionpi.py": get_file_signature(os.path.join(base_dir, "visionpi.py")),
        "online_manager.py": get_file_signature(os.path.join(base_dir, "online_manager.py")),
        game_file: get_file_signature(os.path.join(base_dir, game_file))
    }


def verify_manifests(host_manifest, local_manifest):
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


def draw_cyber_frame(surface, x, y, w, h, cut=24):
    key = (w, h, cut)
    if key not in _frame_cache:
        if len(_frame_cache) > 6:
            _frame_cache.clear()
        NEON_GREEN = (0, 255, 157)
        NEON_CYAN = (0, 216, 255)
        NEON_RED = (255, 56, 76)
        GOLD_TRACE = (180, 140, 40)
        PANEL_BG = (8, 20, 32, 225)

        panel_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pts_local = [
            (cut, 0), (w - cut, 0), (w, cut), (w, h - cut),
            (w - cut, h), (cut, h), (0, h - cut), (0, cut)
        ]
        pygame.draw.polygon(panel_surf, PANEL_BG, pts_local)

        traces = [
            [(cut + 20, 14), (cut + 90, 14), (cut + 110, 34)],
            [(w - cut - 20, 14), (w - cut - 90, 14), (w - cut - 110, 34)],
            [(cut + 20, h - 14), (cut + 90, h - 14), (cut + 110, h - 34)],
            [(w - cut - 20, h - 14), (w - cut - 90, h - 14), (w - cut - 110, h - 34)]
        ]
        for tr in traces:
            pygame.draw.lines(panel_surf, (20, 65, 60, 160), False, tr, 2)
            pygame.draw.circle(panel_surf, (0, 255, 157, 160), tr[-1], 4, 1)

        pygame.draw.polygon(panel_surf, (0, 110, 75), pts_local, 6)
        pygame.draw.polygon(panel_surf, NEON_GREEN, pts_local, 2)

        c_len = int(h * 0.22)
        pygame.draw.line(panel_surf, NEON_RED, (0, cut), (cut, 0), 4)
        pygame.draw.line(panel_surf, NEON_RED, (0, h - cut), (cut, h), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (0, cut + 12), (0, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (0, h - cut - 12), (0, h - cut - c_len), 4)

        pygame.draw.line(panel_surf, NEON_RED, (w - cut, 0), (w, cut), 4)
        pygame.draw.line(panel_surf, NEON_RED, (w - cut, h), (w, h - cut), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (w - 1, cut + 12), (w - 1, cut + c_len), 4)
        pygame.draw.line(panel_surf, NEON_CYAN, (w - 1, h - cut - 12), (w - 1, h - cut - c_len), 4)

        for cx, cy in [(cut + 10, 8), (w - cut - 10, 8), (cut + 10, h - 8), (w - cut - 10, h - 8)]:
            pygame.draw.circle(panel_surf, GOLD_TRACE, (cx, cy), 4)

        _frame_cache[key] = panel_surf

    surface.blit(_frame_cache[key], (x, y))


class OnlineSession:
    def __init__(self, broker="broker.emqx.io", port=1883):
        self.broker = broker
        self.port = port
        self.client_id = f"vp2000_{uuid.uuid4().hex[:8]}"
        self.room_id = ""
        self.room_topic = ""

        self.is_host = False
        self.connected = False
        self.ever_connected = False
        self.disconnect_since = 0.0
        self.error_msg = ""

        self.active_rooms = {}

        self.players = []
        self.local_slots = []
        self.game_name = "501"
        self.option = "Double Out"
        self.match_seed = 0
        self.match_started = False
        self.host_manifest = {}
        self.handshake_ok = False
        self.handshake_status = "Suche nach kollisionsfreien Lobbys..."
        self.reported_mismatch = False

        self.peer_heartbeats = {}
        self.remote_aborted = False
        self.abort_reason = ""
        self.abort_timestamp = 0.0

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

                lwt_payload = json.dumps({
                    "type": "peer_left",
                    "sender_id": self.client_id,
                    "reason": "Verbindung verloren (Timeout)"
                })
                self.client.will_set(DISCOVERY_TOPIC, payload=lwt_payload, qos=0, retain=False)
            except Exception as e:
                self.error_msg = f"MQTT Init Fehler: {e}"
        else:
            self.error_msg = "paho-mqtt fehlt! (Bitte Update ausführen)"

    def connect(self):
        if not self.client:
            return False
        try:
            self.client.connect_async(self.broker, self.port, 10)
            self.client.loop_start()
            return True
        except Exception as e:
            self.error_msg = f"Verbindungsfehler: {e}"
            return False

    def trigger_remote_abort(self, reason="Mitspieler hat das Spiel verlassen!"):
        if not self.remote_aborted:
            self.remote_aborted = True
            self.abort_reason = reason
            self.abort_timestamp = time.time()

    def notify_leaving(self, reason="Spieler hat das Match beendet"):
        if self.connected and self.room_topic:
            try:
                self.publish_room({
                    "type": "match_abort",
                    "reason": reason
                })
            except Exception:
                pass

    def disconnect(self):
        """Nicht-blockierendes Trennen (verhindert Einfrieren bei totem Internet)."""
        self.connected = False
        client_ref = self.client
        self.client = None
        if not client_ref:
            return

        def _async_close():
            try:
                if self.room_topic:
                    payload = json.dumps({
                        "type": "match_abort",
                        "sender_id": self.client_id,
                        "reason": "Automat hat die Sitzung geschlossen"
                    })
                    client_ref.publish(self.room_topic, payload, qos=0)
                if self.is_host and self.room_id:
                    client_ref.publish(DISCOVERY_TOPIC, json.dumps({
                        "type": "room_closed",
                        "room_id": self.room_id,
                        "host_id": self.client_id
                    }), qos=0)
                time.sleep(0.05)
                client_ref.disconnect()
                client_ref.loop_stop()
            except Exception:
                pass

        t = threading.Thread(target=_async_close, daemon=True)
        t.start()
        t.join(timeout=0.35)

    def join_room_topic(self, new_room_id):
        if self.room_topic and self.connected and self.client:
            try:
                self.client.unsubscribe(self.room_topic)
            except Exception:
                pass
        self.room_id = new_room_id
        self.room_topic = f"visionpi2000/v1/room/{new_room_id}"
        self.reported_mismatch = False
        if self.connected and new_room_id and self.client:
            try:
                self.client.subscribe(self.room_topic, qos=0)
            except Exception:
                pass

    def generate_unique_room_id(self):
        suffix = uuid.uuid4().hex[:4].upper()
        return f"Lobby-{suffix}"

    def get_open_lobbies(self, target_game_name=None):
        now = time.time()
        open_list = []
        for r_id, info in sorted(self.active_rooms.items()):
            if (now - info.get("ts", 0) < 6.0) and info.get("state") == "OPEN":
                # FILTER: Nur Lobbys zulassen, die exakt dieselbe Disziplin (Spiel) hosten[cite: 11]
                if target_game_name and info.get("game_name") != target_game_name:
                    continue
                open_list.append(r_id)
        return open_list

    def publish_room(self, payload, qos=0):
        if not self.client or not self.connected or not self.room_topic:
            return
        payload["sender_id"] = self.client_id
        try:
            self.client.publish(self.room_topic, json.dumps(payload), qos=qos)
        except Exception:
            pass

    def broadcast_discovery_beacon(self):
        if not self.is_host or not self.connected or not self.room_id or not self.client:
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
        except Exception:
            pass

    def check_peer_timeouts(self):
        if not self.match_started or self.remote_aborted:
            return
        now = time.time()

        # 1. Prüfen, ob unsere eigene Internetverbindung länger als 5 Sekunden weg ist
        if not self.connected and self.disconnect_since > 0:
            if now - self.disconnect_since > 5.0:
                self.trigger_remote_abort("Eigene Internetverbindung unterbrochen!")
                return

        # 2. Prüfen, ob von einem Mitspieler seit > 7.0 Sekunden kein Heartbeat mehr kam
        remote_clients = {
            p["client_id"] for p in self.players if p["client_id"] != self.client_id
        }
        for rc_id in remote_clients:
            last_seen = self.peer_heartbeats.get(rc_id, now)
            if now - last_seen > 7.0:
                self.trigger_remote_abort("Verbindung zum Mitspieler abgebrochen (Timeout)!")
                break

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            self.ever_connected = True
            self.disconnect_since = 0.0
            try:
                client.subscribe(DISCOVERY_TOPIC, qos=0)
                if self.room_topic:
                    client.subscribe(self.room_topic, qos=0)
            except Exception:
                pass
        else:
            self.error_msg = f"Broker-Fehlercode: {rc}"

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        if self.disconnect_since == 0.0:
            self.disconnect_since = time.time()

    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            return

        sender = data.get("sender_id")
        if sender and sender != self.client_id:
            self.peer_heartbeats[sender] = time.time()

        if msg.topic == DISCOVERY_TOPIC:
            m_type = data.get("type")
            r_id = data.get("room_id")
            h_id = data.get("host_id")

            if m_type == "room_beacon" and r_id:
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

            elif m_type == "room_closed" and r_id:
                if r_id in self.active_rooms:
                    del self.active_rooms[r_id]
                if r_id == self.room_id and not self.is_host:
                    if self.match_started:
                        self.trigger_remote_abort("Host hat das Spiel verlassen!")
                    else:
                        self.players = []
                        self.local_slots = []
                        self.room_id = ""
                        self.handshake_status = "Host hat die Lobby geschlossen. Suche neue..."

            elif m_type == "peer_left" and sender:
                in_our_game = any(p["client_id"] == sender for p in self.players)
                if in_our_game:
                    if self.match_started:
                        self.trigger_remote_abort("Mitspieler-Verbindung abgebrochen!")
                    elif self.is_host:
                        remaining = [p for p in self.players if p["client_id"] != sender]
                        self.players = []
                        for idx, p in enumerate(remaining):
                            self.players.append({
                                "slot": idx,
                                "name": ONLINE_PLAYER_NAMES[idx],
                                "client_id": p["client_id"]
                            })
                        self.broadcast_lobby_state()
            return

        msg_type = data.get("type")

        if msg_type == "heartbeat":
            return

        if msg_type == "match_abort" and sender != self.client_id:
            reason = data.get("reason", "Mitspieler hat das Spiel beendet!")
            if self.match_started:
                self.trigger_remote_abort(reason)
            elif self.is_host:
                remaining = [p for p in self.players if p["client_id"] != sender]
                self.players = []
                for idx, p in enumerate(remaining):
                    self.players.append({
                        "slot": idx,
                        "name": ONLINE_PLAYER_NAMES[idx],
                        "client_id": p["client_id"]
                    })
                self.handshake_status = f"{self.room_id} bereit – Gast hat die Lobby verlassen."
                self.broadcast_lobby_state()
            return

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
                self.handshake_status = f"{self.room_id} bereit – {len(self.players)} Spieler verbunden (SHA-256 OK)!"
                self.broadcast_lobby_state()

            elif msg_type == "guest_version_mismatch" and not self.match_started:
                err_info = data.get("errors", "Unbekannte Abweichung")
                self.handshake_status = f"VERSION KONFLIKT (Gast abgelehnt): {err_info}"

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
                    self.reported_mismatch = False
                    if self.local_slots:
                        my_names = ", ".join(
                            [ONLINE_PLAYER_NAMES[s] for s in self.local_slots]
                        )
                        self.handshake_status = f"Handshake OK ({self.room_id})! Du bist: {my_names}"
                    else:
                        self.handshake_status = f"Code verifiziert ({self.room_id})! Fordere Slot an..."
                else:
                    err_str = " | ".join(errors)
                    self.handshake_status = "VERSION KONFLIKT: " + err_str
                    if not self.reported_mismatch:
                        self.reported_mismatch = True
                        self.publish_room({
                            "type": "guest_version_mismatch",
                            "errors": err_str
                        })

            elif msg_type == "match_start":
                if self.handshake_ok and self.local_slots:
                    self.players = data.get("players", self.players)
                    self.local_slots = [
                        p["slot"] for p in self.players if p["client_id"] == self.client_id
                    ]
                    self.match_seed = data.get("seed", 12345)
                    now = time.time()
                    for p in self.players:
                        self.peer_heartbeats[p["client_id"]] = now
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
        self.serial_proxy = None
        sh = screen.get_height()
        self.banner_font = pygame.font.SysFont("arial", int(sh * 0.021), bold=True)
        self.alert_font = pygame.font.SysFont("arial", int(sh * 0.034), bold=True)

    def set_active_player(self, active_player_idx):
        self.active_player_idx = active_player_idx
        self.darts_left = 3
        if self._real:
            try:
                self._real.set_active_player(active_player_idx)
            except Exception:
                pass

    def set_dart_arrows(self, arrows_count):
        self.darts_left = arrows_count
        if self._real:
            try:
                self._real.set_dart_arrows(arrows_count)
            except Exception:
                pass

    def draw_online_hud(self):
        try:
            # WICHTIG: Auch beim Zeichnen (jeden Frame) den Netzwerk-Poll triggern,
            # falls das Spielmodul gerade in einer Animation steckt!
            if self.serial_proxy:
                self.serial_proxy._poll()

            if not self._screen or not self._session.players:
                return
            sw, sh = self._screen.get_width(), self._screen.get_height()

            if self._session.remote_aborted:
                msg1 = f"ABBRUCH: {self._session.abort_reason}"
                msg2 = "Kehre automatisch ins Hauptmenü zurück..."
                s1 = self.alert_font.render(msg1, True, (255, 255, 255))
                s2 = self.banner_font.render(msg2, True, (255, 215, 0))
                bw = min(int(sw * 0.92), max(s1.get_width(), s2.get_width()) + 70)
                bh = s1.get_height() + s2.get_height() + 56
                bx, by = (sw - bw) // 2, (sh - bh) // 2
                draw_cyber_frame(self._screen, bx, by, bw, bh, cut=16)
                self._screen.blit(s1, ((sw - s1.get_width()) // 2, by + 18))
                self._screen.blit(s2, ((sw - s2.get_width()) // 2, by + 26 + s1.get_height()))
                return

            idx = self.active_player_idx
            if 0 <= idx < len(self._session.players):
                p_info = self._session.players[idx]
                p_name = p_info["name"]
                is_local = (idx in self._session.local_slots)
                status_txt = "DU BIST AM WURF" if is_local else "ONLINE-GEGNER WIRFT"
                border_col = (0, 255, 157) if is_local else (255, 56, 76)
                bg_col = (8, 36, 30) if is_local else (45, 12, 18)

                text = f"VisionPi2000 [{self._session.room_id}]  •  Spieler {idx + 1}: {p_name} ({status_txt})"
                surf = self.banner_font.render(text, True, (255, 255, 255))
                pad_x, pad_y = 20, 5
                rect_w = surf.get_width() + pad_x * 2
                rect_h = surf.get_height() + pad_y * 2
                rect_x = (sw - rect_w) // 2

                pygame.draw.rect(
                    self._screen, bg_col, (rect_x, 4, rect_w, rect_h), border_radius=8
                )
                pygame.draw.rect(
                    self._screen, border_col, (rect_x, 4, rect_w, rect_h), width=2, border_radius=8
                )
                self._screen.blit(surf, (rect_x + pad_x, 4 + pad_y))
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self._real, name)


class OnlineSerialProxy:
    def __init__(self, real_ser, session, display_proxy):
        self._real_ser = real_ser
        self._session = session
        self._disp = display_proxy
        self._disp.serial_proxy = self
        self._ready_queue = queue.Queue()
        self._last_ir_sent = 0.0
        self._last_beacon = time.time()
        self._last_heartbeat = time.time()
        self._last_abort_push = 0.0

    def _poll(self):
        try:
            now = time.time()

            if self._session.is_host and (now - self._last_beacon > 3.0):
                self._last_beacon = now
                self._session.broadcast_discovery_beacon()

            if now - self._last_heartbeat > 1.8:
                self._last_heartbeat = now
                self._session.publish_room({"type": "heartbeat"})
                self._session.check_peer_timeouts()

            # ZWEI-STUFEN-EXIT FÜR ALLE SPIELMODULE:
            # 1. BTN:COMBO öffnet das ABORT_MENU im Spielmodul
            # 2. BTN:PLAYER bestätigt im ABORT_MENU sofort "Beenden -> return 'menu'"
            if self._session.remote_aborted:
                if now - self._session.abort_timestamp > 2.0:
                    if now - self._last_abort_push > 0.35:
                        self._last_abort_push = now
                        if self._ready_queue.qsize() < 4:
                            self._ready_queue.put("BTN:COMBO")
                            self._ready_queue.put("BTN:PLAYER")
                return

            while not self._session.incoming_serial_queue.empty():
                try:
                    net_cmd = self._session.incoming_serial_queue.get_nowait()
                    self._ready_queue.put(net_cmd)
                except Exception:
                    break

            if self._real_ser and self._real_ser.in_waiting > 0:
                try:
                    raw_line = self._real_ser.readline().decode("utf-8", "ignore").strip()
                except Exception:
                    raw_line = ""

                if raw_line:
                    is_my_turn = (self._disp.active_player_idx in self._session.local_slots)

                    if raw_line == "BTN:COMBO":
                        self._session.notify_leaving("Mitspieler hat das Match abgebrochen!")
                        self._session.trigger_remote_abort("Match lokal abgebrochen!")
                        self._session.abort_timestamp = now - 2.1
                        self._ready_queue.put("BTN:COMBO")
                        self._ready_queue.put("BTN:PLAYER")

                    elif is_my_turn:
                        if raw_line.startswith("HIT:") or raw_line == "MISS:1":
                            self._session.publish_room({"type": "game_event", "cmd": raw_line})
                            self._ready_queue.put(raw_line)

                        elif raw_line in ["BTN:PLAYER", "BTN:START"]:
                            self._session.publish_room({"type": "game_event", "cmd": raw_line})
                            self._ready_queue.put(raw_line)

                        elif raw_line == "IR:DETECT":
                            if self._disp.darts_left <= 0 and (now - self._last_ir_sent >= 0.28):
                                self._last_ir_sent = now
                                self._session.publish_room({"type": "game_event", "cmd": "IR:DETECT"})
                                self._ready_queue.put("IR:DETECT")
        except Exception:
            pass

    @property
    def in_waiting(self):
        try:
            self._poll()
            return self._ready_queue.qsize()
        except Exception:
            return 0

    def readline(self):
        try:
            self._poll()
            if not self._ready_queue.empty():
                cmd = self._ready_queue.get_nowait()
                return (cmd + "\n").encode("utf-8")
        except Exception:
            pass
        return b""

    def write(self, data):
        if self._real_ser:
            try:
                return self._real_ser.write(data)
            except Exception:
                pass

    def flush(self):
        if self._real_ser:
            try:
                return self._real_ser.flush()
            except Exception:
                pass

    def reset_input_buffer(self):
        if self._real_ser:
            try:
                self._real_ser.reset_input_buffer()
            except Exception:
                pass
        # Bei aktivem Abbruch darf das Spielmodul die Exit-Signale nicht aus der Queue löschen!
        if not self._session.remote_aborted:
            try:
                with self._ready_queue.mutex:
                    self._ready_queue.queue.clear()
            except Exception:
                pass


def run_online_lobby_and_match(screen, ser, display, local_players, game_name, option, is_host, game_mod, settings):
    sw, sh = screen.get_width(), screen.get_height()
    clock = pygame.time.Clock()

    is_16_9 = (settings.get("format", "4:3") == "16:9") or ((sw / float(sh)) > 1.5)
    bg_candidates = ["background_16_9.png", "background_16_9.PNG", "background_16_9.jpg"] if is_16_9 else ["background.png", "Background.png", "background.PNG", "background.jpg"]
    bg_file = find_image_file(bg_candidates)
    bg_img = None
    if bg_file:
        try:
            raw_bg = pygame.image.load(bg_file).convert()
            bg_img = pygame.transform.scale(raw_bg, (sw, sh))
            darker = pygame.Surface((sw, sh))
            darker.set_alpha(165)
            darker.fill((4, 12, 20))
            bg_img.blit(darker, (0, 0))
        except Exception:
            pass

    header_file = find_image_file(["header.png", "Header.png", "HEADER.png"])
    header_img = None
    if header_file:
        try:
            raw_h = pygame.image.load(header_file).convert_alpha()
            header_h = int(sh * 0.18)
            header_w = int(raw_h.get_width() * (header_h / raw_h.get_height()))
            header_img = pygame.transform.smoothscale(raw_h, (header_w, header_h))
        except Exception:
            pass

    berry_avatars_precomputed = []
    for b_file in ["Bullseye-Berry_Cyber.png", "Bullseye-Berry_Original.png"]:
        f_found = find_image_file(b_file)
        if f_found:
            try:
                raw_av = pygame.image.load(f_found).convert_alpha()
                box_h_est = int(sh * 0.78)
                base_sz = int(box_h_est * 0.40)
                # 5 Animationsstufen einmalig vorab berechnen statt 30x pro Sekunde smoothscale!
                for offset in [-6, -3, 0, 3, 6]:
                    sz = base_sz + offset
                    berry_avatars_precomputed.append(pygame.transform.smoothscale(raw_av, (sz, sz)))
                break
            except Exception:
                pass

    role_font = pygame.font.SysFont("arial", int(sh * 0.026), bold=True)
    sub_font = pygame.font.SysFont("arial", int(sh * 0.023), bold=True)
    list_font = pygame.font.SysFont("arial", int(sh * 0.022), bold=True)
    small_font = pygame.font.SysFont("arial", int(sh * 0.019), bold=True)

    GOLD = (255, 205, 45)
    WHITE = (255, 255, 255)
    NEON_GREEN = (0, 255, 157)
    NEON_CYAN = (0, 216, 255)
    NEON_RED = (255, 56, 76)

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
        unique_id = session.generate_unique_room_id()
        session.join_room_topic(unique_id)
        session.handshake_status = f"{unique_id} geöffnet – SHA-256 bereit!"

    session.connect()

    last_broadcast = 0
    in_lobby = True

    while in_lobby:
        raw_data = None
        try:
            raw_data = ser.readline().decode("utf-8", "ignore").strip() if ser and ser.in_waiting > 0 else None
        except Exception:
            raw_data = None

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

        if raw_data in ["BTN:PLAYER", "BTN:COMBO"]:
            session.disconnect()
            return "menu"

        elif raw_data == "BTN:BLUE" and not is_host:
            # Nur Lobbys durchschalten, die exakt zur eigenen Spielauswahl passen[cite: 11]
            open_lobbies = session.get_open_lobbies(target_game_name=game_name)
            if len(open_lobbies) > 1:
                session.notify_leaving("Gast hat die Lobby gewechselt")
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
                now = time.time()
                for p in session.players:
                    session.peer_heartbeats[p["client_id"]] = now
                session.match_started = True
                session.broadcast_discovery_beacon()
                session.publish_room({
                    "type": "match_start",
                    "players": session.players,
                    "seed": session.match_seed
                }, qos=1)
                time.sleep(0.12)

        if session.connected:
            if not is_host:
                # FILTER: Dem Gast nur Lobbys vorschlagen, die exakt das am Automaten eingestellte Spiel hosten[cite: 11]
                open_lobbies = session.get_open_lobbies(target_game_name=game_name)
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

        if bg_img:
            screen.blit(bg_img, (0, 0))
        else:
            screen.fill((6, 17, 28))

        if header_img:
            screen.blit(header_img, ((sw - header_img.get_width()) // 2, 8))
            box_y = int(sh * 0.17)
            box_h = int(sh * 0.78)
        else:
            fallback_surf = role_font.render("VisionPi2000", True, GOLD)
            screen.blit(fallback_surf, ((sw - fallback_surf.get_width()) // 2, 10))
            box_y = int(sh * 0.08)
            box_h = int(sh * 0.86)

        box_w = int(sw * 0.90)
        box_x = (sw - box_w) // 2

        draw_cyber_frame(screen, box_x, box_y, box_w, box_h, cut=22)

        role_str = "ONLINE HOST-LOBBY" if is_host else "ONLINE GAST-BEITRITT"
        room_disp = session.room_id if session.room_id else "Suche offene Lobbys..."
        head_str = f"{role_str}  •  Disziplin: {session.game_name} ({session.option})  •  {room_disp}"
        head_surf = role_font.render(head_str, True, GOLD)
        screen.blit(head_surf, ((sw - head_surf.get_width()) // 2, box_y + int(box_h * 0.025)))

        if session.error_msg:
            stat_col, stat_txt = NEON_RED, session.error_msg
        elif not session.connected:
            stat_col, stat_txt = GOLD, "Verbinde mit MQTT-Broker..."
        else:
            stat_col = NEON_GREEN if session.handshake_ok else GOLD
            if "KONFLIKT" in session.handshake_status:
                stat_col = NEON_RED
            stat_txt = session.handshake_status

        stat_surf = small_font.render(f"Status / Handshake: {stat_txt}", True, stat_col)
        screen.blit(stat_surf, ((sw - stat_surf.get_width()) // 2, box_y + int(box_h * 0.095)))

        line_y = box_y + int(box_h * 0.145)
        pygame.draw.line(screen, NEON_GREEN, (box_x + 35, line_y), (box_x + box_w - 35, line_y), 2)
        pygame.draw.circle(screen, GOLD, (sw // 2, line_y), 5)

        slot_y = box_y + int(box_h * 0.175)
        slot_h = int(box_h * 0.085)
        card_w = int(box_w * 0.66) if berry_avatars_precomputed else int(box_w * 0.82)
        card_x = box_x + int(box_w * 0.05)

        for s_idx in range(8):
            berry_name = ONLINE_PLAYER_NAMES[s_idx]
            p_entry = next((p for p in session.players if p["slot"] == s_idx), None)
            cy = slot_y + s_idx * slot_h
            ch = slot_h - 6

            if p_entry:
                is_me = (p_entry["client_id"] == session.client_id)
                tag = "LOKAL (Dieser Automat)" if is_me else "ONLINE VERBUNDEN"
                border_c = NEON_GREEN if is_me else NEON_CYAN
                bg_c = (12, 50, 42) if is_me else (12, 38, 56)
                txt_c = WHITE
                line_str = f"Slot {s_idx + 1}:  {berry_name:<20}  •  [{tag}]"
            else:
                border_c = (35, 65, 80)
                bg_c = (10, 22, 34)
                txt_c = (110, 130, 145)
                line_str = f"Slot {s_idx + 1}:  {berry_name:<20}  •  [ Frei / Wartet ]"

            pygame.draw.rect(screen, bg_c, (card_x, cy, card_w, ch), border_radius=8)
            pygame.draw.rect(screen, border_c, (card_x, cy, card_w, ch), width=2, border_radius=8)

            s_surf = list_font.render(line_str, True, txt_c)
            screen.blit(s_surf, (card_x + 16, cy + (ch - s_surf.get_height()) // 2))

        if berry_avatars_precomputed:
            idx_anim = int((math.sin(pygame.time.get_ticks() * 0.005) + 1.0) * 2.49)
            idx_anim = max(0, min(len(berry_avatars_precomputed) - 1, idx_anim))
            av_scaled = berry_avatars_precomputed[idx_anim]
            base_sz = berry_avatars_precomputed[2].get_width()
            anim_sz = av_scaled.get_width()
            av_x = box_x + box_w - int(box_w * 0.27) + (base_sz - anim_sz) // 2
            av_y = box_y + int(box_h * 0.30) + (base_sz - anim_sz) // 2
            screen.blit(av_scaled, (av_x, av_y))

        if is_host:
            hint_str = "START drücken: Online-Match starten   |   SPIELERWECHSEL: Abbrechen"
        else:
            # Anzahl passender offener Lobbys anzeigen
            open_cnt = len(session.get_open_lobbies(target_game_name=game_name))
            if open_cnt > 1:
                hint_str = f"BLAU: Lobby wechseln ({open_cnt} passende offen)   |   SPIELERWECHSEL: Abbrechen"
            else:
                hint_str = "Warte auf Spielstart durch den Host...   |   SPIELERWECHSEL: Abbrechen"

        hint_surf = sub_font.render(hint_str, True, GOLD)
        screen.blit(hint_surf, ((sw - hint_surf.get_width()) // 2, box_y + box_h - int(box_h * 0.075)))

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
    except Exception:
        pass
    finally:
        pygame.display.flip = orig_flip
        session.disconnect()

    return "menu"
