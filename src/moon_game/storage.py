from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import NamedTuple

_CONNECTION: sqlite3.Connection | None = None

_SEED_ROVERS = (
    ("hauler", "Тягач", 140.0, "rover", 10, 180.0),
    ("runner", "Бегун", 160.0, "rover", 4, 95.0),
    ("scout", "Разведчик", 120.0, "rover", 6, 120.0),
)

_SEED_ORDERS = (
    ("mail", "Почта", "crater", 3, 50, 13.0),
    ("tools", "Инструменты", "crater", 8, 80, 24.0),
    ("samples", "Образцы", "ridge", 6, 80, 24.0),
    ("ore", "Руда", "crater", 20, 200, 24.0),
)


class RoverRow(NamedTuple):
    id: str
    name: str
    speed: float
    image_key: str
    capacity: int
    battery_max: float


class OrderRow(NamedTuple):
    id: str
    name: str
    endpoint_id: str
    weight: int
    reward: int
    deadline: float


def database_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "moon.sqlite"


def load_rover_rows() -> list[RoverRow]:
    rows = (
        _connect()
        .execute(
            """
        SELECT id, name, speed, image_key, capacity, battery_max
        FROM rovers
        ORDER BY rowid
        """
        )
        .fetchall()
    )
    return [
        RoverRow(
            id=row["id"],
            name=row["name"],
            speed=row["speed"],
            image_key=row["image_key"],
            capacity=row["capacity"],
            battery_max=row["battery_max"],
        )
        for row in rows
    ]


def load_order_rows() -> list[OrderRow]:
    rows = (
        _connect()
        .execute(
            """
        SELECT id, name, endpoint_id, weight, reward, deadline
        FROM orders
        ORDER BY rowid
        """
        )
        .fetchall()
    )
    return [
        OrderRow(
            id=row["id"],
            name=row["name"],
            endpoint_id=row["endpoint_id"],
            weight=row["weight"],
            reward=row["reward"],
            deadline=row["deadline"],
        )
        for row in rows
    ]


def log_delivery_start(
    rover_id: str,
    order_id: str,
    route_id: str,
    *,
    day_number: int,
    started_at: float,
) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO deliveries (
            rover_id, order_id, route_id, day_number, started_at, state
        )
        VALUES (?, ?, ?, ?, ?, 'active')
        """,
        (rover_id, order_id, route_id, day_number, started_at),
    )
    conn.commit()


def log_delivery_end(
    rover_id: str,
    *,
    state: str,
    finished_at: float,
    reward: int,
) -> None:
    conn = _connect()
    conn.execute(
        """
        UPDATE deliveries
        SET state = ?, finished_at = ?, reward = ?
        WHERE id = (
            SELECT id FROM deliveries
            WHERE rover_id = ? AND state = 'active'
            ORDER BY id DESC
            LIMIT 1
        )
        """,
        (state, finished_at, reward, rover_id),
    )
    conn.commit()


def log_event(
    kind: str,
    *,
    day_number: int,
    elapsed: float,
    rover_id: str | None = None,
    order_id: str | None = None,
    route_id: str | None = None,
) -> None:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO events (
            kind, day_number, elapsed, rover_id, order_id, route_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (kind, day_number, elapsed, rover_id, order_id, route_id),
    )
    conn.commit()


def _connect() -> sqlite3.Connection:
    global _CONNECTION
    if _CONNECTION is not None:
        return _CONNECTION
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    _init_schema(connection)
    _seed_catalog(connection)
    _CONNECTION = connection
    return connection


def _init_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS rovers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            speed REAL NOT NULL,
            image_key TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            battery_max REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            endpoint_id TEXT NOT NULL,
            weight INTEGER NOT NULL,
            reward INTEGER NOT NULL,
            deadline REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rover_id TEXT NOT NULL,
            order_id TEXT NOT NULL,
            route_id TEXT NOT NULL,
            day_number INTEGER NOT NULL,
            started_at REAL NOT NULL,
            finished_at REAL,
            state TEXT NOT NULL,
            reward INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT NOT NULL,
            day_number INTEGER NOT NULL,
            elapsed REAL NOT NULL,
            rover_id TEXT,
            order_id TEXT,
            route_id TEXT
        );
        """
    )
    connection.commit()


def _seed_catalog(connection: sqlite3.Connection) -> None:
    rover_count = connection.execute("SELECT COUNT(*) FROM rovers").fetchone()[0]
    if rover_count == 0:
        connection.executemany(
            """
            INSERT INTO rovers (
                id, name, speed, image_key, capacity, battery_max
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            _SEED_ROVERS,
        )
    order_count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if order_count == 0:
        connection.executemany(
            """
            INSERT INTO orders (
                id, name, endpoint_id, weight, reward, deadline
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            _SEED_ORDERS,
        )
    connection.commit()
