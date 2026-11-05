"""SQLite persistence: users, saved places, conversation sessions, rides."""

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from .models import Place, User

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    phone TEXT PRIMARY KEY,
    name TEXT NOT NULL DEFAULT '',
    pin_hash TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS places (
    phone TEXT NOT NULL,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    lat REAL,
    lng REAL,
    PRIMARY KEY (phone, name)
);
CREATE TABLE IF NOT EXISTS sessions (
    phone TEXT PRIMARY KEY,
    service TEXT NOT NULL,
    state TEXT NOT NULL,
    data TEXT NOT NULL,
    expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS rides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_ride_id TEXT NOT NULL,
    status TEXT NOT NULL,
    pickup TEXT NOT NULL,
    dropoff TEXT NOT NULL,
    info TEXT NOT NULL DEFAULT '{}',
    active INTEGER NOT NULL DEFAULT 1,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL,
    direction TEXT NOT NULL,
    channel TEXT NOT NULL,
    body TEXT NOT NULL,
    ts REAL NOT NULL
);
"""


@dataclass
class Session:
    """A multi-step conversation in progress (e.g. waiting for YES)."""

    service: str
    state: str
    data: dict
    expires_at: float


@dataclass
class Ride:
    id: int
    phone: str
    provider: str
    provider_ride_id: str
    status: str
    pickup: Place
    dropoff: Place
    info: dict
    active: bool


class Store:
    def __init__(self, path: str = ":memory:", clock: Callable[[], float] = time.time):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.clock = clock
        self._lock = threading.RLock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(SCHEMA)
            self._db.commit()

    def _exec(self, sql: str, params=()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._db.execute(sql, params)
            self._db.commit()
            return cur

    def _all(self, sql: str, params=()) -> List[sqlite3.Row]:
        with self._lock:
            return self._db.execute(sql, params).fetchall()

    # -- users ---------------------------------------------------------------
    def get_user(self, phone: str) -> Optional[User]:
        rows = self._all("SELECT phone, name, pin_hash FROM users WHERE phone = ?", (phone,))
        return User(**dict(rows[0])) if rows else None

    def add_user(self, phone: str, name: str = "", pin_hash: Optional[str] = None) -> User:
        self._exec(
            "INSERT INTO users (phone, name, pin_hash, created_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(phone) DO UPDATE SET name = excluded.name, pin_hash = excluded.pin_hash",
            (phone, name, pin_hash, self.clock()),
        )
        return User(phone, name, pin_hash)

    def list_users(self) -> List[User]:
        return [User(**dict(r)) for r in self._all("SELECT phone, name, pin_hash FROM users ORDER BY phone")]

    def remove_user(self, phone: str) -> bool:
        with self._lock:
            for table in ("places", "sessions", "rides", "messages"):
                self._db.execute(f"DELETE FROM {table} WHERE phone = ?", (phone,))
            cur = self._db.execute("DELETE FROM users WHERE phone = ?", (phone,))
            self._db.commit()
            return cur.rowcount > 0

    # -- saved places --------------------------------------------------------
    def save_place(self, phone: str, place: Place) -> None:
        self._exec(
            "INSERT OR REPLACE INTO places (phone, name, address, lat, lng) VALUES (?, ?, ?, ?, ?)",
            (phone, place.name.lower(), place.address, place.lat, place.lng),
        )

    def get_place(self, phone: str, name: str) -> Optional[Place]:
        rows = self._all(
            "SELECT name, address, lat, lng FROM places WHERE phone = ? AND name = ?",
            (phone, name.strip().lower()),
        )
        return Place(**dict(rows[0])) if rows else None

    def list_places(self, phone: str) -> List[Place]:
        rows = self._all("SELECT name, address, lat, lng FROM places WHERE phone = ? ORDER BY name", (phone,))
        return [Place(**dict(r)) for r in rows]

    def delete_place(self, phone: str, name: str) -> bool:
        cur = self._exec("DELETE FROM places WHERE phone = ? AND name = ?", (phone, name.strip().lower()))
        return cur.rowcount > 0

    # -- sessions ------------------------------------------------------------
    def get_session(self, phone: str) -> Optional[Session]:
        rows = self._all("SELECT service, state, data, expires_at FROM sessions WHERE phone = ?", (phone,))
        if not rows:
            return None
        r = rows[0]
        if r["expires_at"] < self.clock():
            self.clear_session(phone)
            return None
        return Session(r["service"], r["state"], json.loads(r["data"]), r["expires_at"])

    def set_session(self, phone: str, service: str, state: str, data: dict, expires_at: float) -> None:
        self._exec(
            "INSERT OR REPLACE INTO sessions (phone, service, state, data, expires_at) VALUES (?, ?, ?, ?, ?)",
            (phone, service, state, json.dumps(data), expires_at),
        )

    def clear_session(self, phone: str) -> None:
        self._exec("DELETE FROM sessions WHERE phone = ?", (phone,))

    # -- rides ---------------------------------------------------------------
    def _ride(self, r: sqlite3.Row) -> Ride:
        return Ride(
            id=r["id"],
            phone=r["phone"],
            provider=r["provider"],
            provider_ride_id=r["provider_ride_id"],
            status=r["status"],
            pickup=Place.from_dict(json.loads(r["pickup"])),
            dropoff=Place.from_dict(json.loads(r["dropoff"])),
            info=json.loads(r["info"]),
            active=bool(r["active"]),
        )

    def create_ride(self, phone, provider, provider_ride_id, status, pickup: Place, dropoff: Place, info: dict) -> Ride:
        now = self.clock()
        cur = self._exec(
            "INSERT INTO rides (phone, provider, provider_ride_id, status, pickup, dropoff, info, active, "
            "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
            (phone, provider, provider_ride_id, status, json.dumps(pickup.to_dict()),
             json.dumps(dropoff.to_dict()), json.dumps(info), now, now),
        )
        return self.get_ride(cur.lastrowid)

    def get_ride(self, ride_id: int) -> Optional[Ride]:
        rows = self._all("SELECT * FROM rides WHERE id = ?", (ride_id,))
        return self._ride(rows[0]) if rows else None

    def update_ride(self, ride_id: int, status: str, info: dict, active: bool) -> None:
        self._exec(
            "UPDATE rides SET status = ?, info = ?, active = ?, updated_at = ? WHERE id = ?",
            (status, json.dumps(info), int(active), self.clock(), ride_id),
        )

    def active_ride(self, phone: str) -> Optional[Ride]:
        rows = self._all("SELECT * FROM rides WHERE phone = ? AND active = 1 ORDER BY id DESC LIMIT 1", (phone,))
        return self._ride(rows[0]) if rows else None

    def active_rides(self, provider: Optional[str] = None) -> List[Ride]:
        if provider:
            rows = self._all("SELECT * FROM rides WHERE active = 1 AND provider = ?", (provider,))
        else:
            rows = self._all("SELECT * FROM rides WHERE active = 1")
        return [self._ride(r) for r in rows]

    # -- message log (only used when log_messages is on) ---------------------
    def log_message(self, phone: str, direction: str, channel: str, body: str) -> None:
        self._exec(
            "INSERT INTO messages (phone, direction, channel, body, ts) VALUES (?, ?, ?, ?, ?)",
            (phone, direction, channel, body, self.clock()),
        )
