"""
database.py
-----------
Creates and manages the SQLite database for Hand Cricket AI.

Tables:
    players  — one row per player, profile + aggregate stats
    sessions — one row per match
    balls    — every single ball ever bowled with full context
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "hand_cricket.db")


def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # allows dict-style access to rows
    return conn


def init_db():
    """Creates all tables if they don't already exist."""
    conn = get_connection()
    c = conn.cursor()

    # ── Players ──────────────────────────────────────────────────────────
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

    # ── Sessions ─────────────────────────────────────────────────────────
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
            result          TEXT NOT NULL,   -- 'chase','defended','super_over'
            played_at       TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Balls ─────────────────────────────────────────────────────────────
    # This is the core behavioural dataset — every ball ever bowled.
    c.execute("""
        CREATE TABLE IF NOT EXISTS balls (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      INTEGER NOT NULL,
            player_name     TEXT    NOT NULL,   -- the BATTER
            innings         INTEGER NOT NULL,   -- 1 or 2
            ball_num        INTEGER NOT NULL,
            batter_num      INTEGER NOT NULL,   -- what batter showed
            bowler_num      INTEGER NOT NULL,   -- what bowler showed
            out             INTEGER NOT NULL,   -- 1 = out, 0 = not out
            runs_scored     INTEGER NOT NULL,
            total_after     INTEGER NOT NULL,   -- cumulative score after ball
            target          INTEGER,            -- NULL if batting first
            score_bracket   TEXT    NOT NULL,   -- '0-50','50-100','100-150','150+'
            pressure        TEXT    NOT NULL,   -- 'normal','high_pressure','last_ball'
            is_super_over   INTEGER DEFAULT 0,
            played_at       TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()
    print("  ✅ Database ready.")


def get_or_create_player(name: str) -> int:
    """Returns the player's ID, creating a new row if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO players (name) VALUES (?)", (name,))
    conn.commit()
    c.execute("SELECT id FROM players WHERE name = ?", (name,))
    row = c.fetchone()
    conn.close()
    return row["id"]


def update_player_stats(name: str, runs: int, balls: int,
                        got_out: bool, won: bool):
    """Updates aggregate stats on the player profile after a match."""
    conn = get_connection()
    c = conn.cursor()
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


if __name__ == "__main__":
    init_db()
    print("  Database initialised at:", os.path.abspath(DB_PATH))
