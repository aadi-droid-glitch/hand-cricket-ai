"""
tracker.py
----------
Logs every ball and session into the database.
This is the data pipeline between the game engine and the pattern brain.
"""

from brain.database import get_connection, get_or_create_player, update_player_stats


def log_session(match_summary: dict) -> int:
    """
    Logs a completed match into the sessions table.
    Also logs every ball from both innings into the balls table.
    Updates both players' aggregate stats.

    Returns the session_id.
    """
    conn = get_connection()
    c    = conn.cursor()

    # ── Insert session row ───────────────────────────────────────────────
    c.execute("""
        INSERT INTO sessions
            (player1, player2, first_batter,
             innings1_runs, innings1_balls,
             innings2_runs, innings2_balls,
             winner, result)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        match_summary["player1"],
        match_summary["player2"],
        match_summary["first_batter"],
        match_summary["innings1_runs"],
        match_summary["innings1_balls"],
        match_summary["innings2_runs"],
        match_summary["innings2_balls"],
        match_summary["winner"],
        match_summary["result"],
    ))
    session_id = c.lastrowid

    # ── Log innings 1 balls ──────────────────────────────────────────────
    _log_innings_balls(c, session_id,
                       player_name=match_summary["first_batter"],
                       innings=1,
                       ball_log=match_summary["innings1_log"])

    # ── Log innings 2 balls ──────────────────────────────────────────────
    second_batter = (
        match_summary["player2"]
        if match_summary["first_batter"] == match_summary["player1"]
        else match_summary["player1"]
    )
    _log_innings_balls(c, session_id,
                       player_name=second_batter,
                       innings=2,
                       ball_log=match_summary["innings2_log"])

    conn.commit()
    conn.close()

    # ── Ensure both players exist in players table ───────────────────────
    get_or_create_player(match_summary["player1"])
    get_or_create_player(match_summary["player2"])

    # ── Update aggregate stats ───────────────────────────────────────────
    winner = match_summary["winner"]

    # Player who batted first
    p1      = match_summary["first_batter"]
    p1_log  = match_summary["innings1_log"]
    p1_out  = p1_log[-1]["out"] if p1_log else False
    update_player_stats(p1,
                        runs    = match_summary["innings1_runs"],
                        balls   = match_summary["innings1_balls"],
                        got_out = p1_out,
                        won     = (winner == p1))

    # Player who batted second
    p2      = second_batter
    p2_log  = match_summary["innings2_log"]
    p2_out  = p2_log[-1]["out"] if p2_log else False
    update_player_stats(p2,
                        runs    = match_summary["innings2_runs"],
                        balls   = match_summary["innings2_balls"],
                        got_out = p2_out,
                        won     = (winner == p2))

    return session_id


def _log_innings_balls(cursor, session_id: int, player_name: str,
                       innings: int, ball_log: list):
    """Inserts every ball from one innings into the balls table."""
    for ball in ball_log:
        cursor.execute("""
            INSERT INTO balls
                (session_id, player_name, innings, ball_num,
                 batter_num, bowler_num, out, runs_scored,
                 total_after, target, score_bracket, pressure)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            player_name,
            innings,
            ball["ball_num"],
            ball["batter_num"],
            ball["bowler_num"],
            1 if ball["out"] else 0,
            ball["runs_scored"],
            ball["total_after"],
            ball.get("target"),
            ball["score_bracket"],
            ball["pressure"],
        ))


def get_player_ball_history(player_name: str) -> list:
    """
    Fetches every ball ever batted by this player.
    Used by the predictor to build pattern tables.
    """
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""
        SELECT * FROM balls
        WHERE player_name = ?
        ORDER BY played_at ASC, ball_num ASC
    """, (player_name,))
    rows = [dict(row) for row in c.fetchall()]
    conn.close()
    return rows


def get_player_profile(player_name: str) -> dict:
    """Returns the aggregate profile row for a player."""
    conn = get_connection()
    c    = conn.cursor()
    c.execute("SELECT * FROM players WHERE name = ?", (player_name,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}
