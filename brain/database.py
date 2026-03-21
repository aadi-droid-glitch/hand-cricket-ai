"""
brain/database.py
-----------------
SQLite database setup. Path is always relative to project root
so it works both locally and on Railway/Render.
"""

import sqlite3
import os

# Always resolve to project root regardless of where script is run from
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "hand_cricket.db")


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS players (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    UNIQUE NOT NULL,
            matches_played  INTEGER DEFAULT 0,
            matches_won     INTEGER DEFAULT 0,
            total_runs      INTEGER DEFAULT 0,
            total_balls     INTEGER DEFAULT 0,
            times_out       INTEGER DEFAULT 0,
            created_at      TEXT    DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            player1         TEXT NOT NULL,
            player2         TEXT NOT NULL,
            first_batter    TEXT NOT NULL,
            innings1_runs   INTEGER NOT NULL,
            innings1_balls  INTEGER NOT NULL,
            innings2_runs   INTEGER NOT NULL,
            innings2_balls  INTEGER NOT NULL,
            winner          TEXT NOT NULL,
            result          TEXT NOT NULL,
            played_at       TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS balls (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL,
            player_name     TEXT    NOT NULL,
            innings         INTEGER NOT NULL,
            ball_num        INTEGER NOT NULL,
            batter_num      INTEGER NOT NULL,
            bowler_num      INTEGER NOT NULL,
            out             INTEGER NOT NULL,
            runs_scored     INTEGER NOT NULL,
            total_after     INTEGER NOT NULL,
            target          INTEGER,
            score_bracket   TEXT    NOT NULL,
            pressure        TEXT    NOT NULL,
            is_super_over   INTEGER DEFAULT 0,
            played_at       TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()


def get_or_create_player(name: str) -> int:
    conn = get_connection()
    c    = conn.cursor()
    c.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
    conn.commit()
    c.execute("SELECT id FROM players WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    return row["id"]


def update_player_stats(name: str, runs: int, balls: int,
                        got_out: bool, won: bool):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""
        UPDATE players SET
            matches_played = matches_played + 1,
            matches_won    = matches_won    + ?,
            total_runs     = total_runs     + ?,
            total_balls    = total_balls    + ?,
            times_out      = times_out      + ?
        WHERE name = ?
    """, (1 if won else 0, runs, balls, 1 if got_out else 0, name))
    conn.commit()
    conn.close()
