"""
web/app.py
----------
FastAPI backend for Hand Cricket AI.
Bridges the browser UI to the Python game engine and pattern brain.

Run with:
    uvicorn web.app:app --reload
"""

import random
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from brain.database  import init_db, get_or_create_player
from brain.tracker   import log_session, get_player_profile
from brain.predictor import Predictor
from engine.scorer   import Scorer

app = FastAPI()

# ── In-memory game state (one session at a time for now) ─────────────────
game_state = {}


# ── Startup ──────────────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    init_db()


# ── Static files ─────────────────────────────────────────────────────────
import os
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def index():
    return FileResponse(os.path.join(static_dir, "index.html"))


# ── Request models ────────────────────────────────────────────────────────
class PlayerRequest(BaseModel):
    name: str

class TossRequest(BaseModel):
    player_name: str
    call: str          # "odd" or "even"
    player_num: int    # human's toss number

class TossChoiceRequest(BaseModel):
    player_name: str
    choice: str        # "bat" or "bowl"

class BallRequest(BaseModel):
    player_name: str
    number: int        # human's number this ball


# ── Player profile ────────────────────────────────────────────────────────
@app.post("/api/player/load")
def load_player(req: PlayerRequest):
    name = req.name.strip().title()
    get_or_create_player(name)

    predictor = Predictor(name)
    profile   = get_player_profile(name)

    game_state[name] = {
        "predictor"   : predictor,
        "scorer"      : None,
        "innings"     : 0,
        "first_batter": None,
        "target"      : None,
        "innings1_log": [],
        "innings2_log": [],
        "innings1_runs": 0,
        "innings1_balls": 0,
        "ball_count"  : 0,
    }

    pred_score = predictor.predictability_score()
    summary    = predictor.summary()

    return {
        "name"          : name,
        "matches_played": profile.get("matches_played", 0) if profile else 0,
        "matches_won"   : profile.get("matches_won", 0)    if profile else 0,
        "total_runs"    : profile.get("total_runs", 0)     if profile else 0,
        "predictability": pred_score,
        "favourite"     : summary.get("favourite_number", "?"),
        "history_balls" : len(predictor.history),
    }


# ── Toss ──────────────────────────────────────────────────────────────────
@app.post("/api/toss/reveal")
def toss_reveal(req: TossRequest):
    name      = req.player_name.strip().title()
    ai_num    = random.randint(1, 10)
    total     = req.player_num + ai_num
    result    = "odd" if total % 2 != 0 else "even"
    caller_wins = result == req.call.lower()

    return {
        "player_num"  : req.player_num,
        "ai_num"      : ai_num,
        "total"       : total,
        "result"      : result,
        "caller_wins" : caller_wins,
        "winner"      : name if caller_wins else "AI",
    }


@app.post("/api/toss/choice")
def toss_choice(req: TossChoiceRequest):
    """After toss winner picks bat or bowl, set up innings order."""
    name   = req.player_name.strip().title()
    choice = req.choice.lower()
    state  = game_state.get(name, {})

    # Determine who bats first
    toss_winner = state.get("toss_winner", name)
    if toss_winner == name:
        first_batter = name if choice == "bat" else "AI"
    else:
        first_batter = "AI" if choice == "bat" else name

    state["first_batter"] = first_batter
    state["innings"]      = 1
    state["ball_count"]   = 0

    # Set up scorer for innings 1
    state["scorer"] = Scorer(player_name=first_batter, target=None)
    game_state[name] = state

    return {
        "first_batter": first_batter,
        "first_bowler": "AI" if first_batter == name else name,
        "message"     : f"{first_batter} bats first.",
    }


# ── Ball ──────────────────────────────────────────────────────────────────
@app.post("/api/ball/play")
def play_ball(req: BallRequest):
    """
    Process one ball.
    Human sends their number. Backend determines the other side's number.
    Returns result with full context.
    """
    name    = req.player_name.strip().title()
    state   = game_state.get(name)
    if not state:
        return {"error": "No active game. Load player first."}

    scorer      = state["scorer"]
    predictor   = state["predictor"]
    innings     = state["innings"]
    first_batter = state["first_batter"]
    ball_count  = state["ball_count"] + 1
    state["ball_count"] = ball_count

    # Determine who is batting and who is bowling this innings
    if innings == 1:
        batter = first_batter
        bowler = "AI" if first_batter == name else name
    else:
        batter = "AI" if first_batter == name else name
        bowler = name if first_batter == name else "AI"

    human_is_batting = (batter == name)

    # ── Pick numbers ────────────────────────────────────────────────────
    if human_is_batting:
        batter_num = req.number
        bowler_num = predictor.predict(
            ball_num      = ball_count,
            score_bracket = scorer._score_bracket(),
            pressure      = scorer._pressure_state(),
        )
    else:
        bowler_num = req.number   # human is bowling
        batter_num = random.randint(1, 10)

    # ── Process ball ────────────────────────────────────────────────────
    result = scorer.add_ball(batter_num, bowler_num)

    # Update predictor only on human batting balls
    if human_is_batting:
        predictor.update(scorer.ball_log[-1])

    response = {
        "ball_num"        : ball_count,
        "batter_num"      : batter_num,
        "bowler_num"      : bowler_num,
        "out"             : result["out"],
        "runs_this_ball"  : result["runs"],
        "total"           : result["total"],
        "won"             : result["won"],
        "human_is_batting": human_is_batting,
        "innings"         : innings,
        "innings_over"    : False,
        "match_over"      : False,
        "winner"          : None,
    }

    # ── Innings over? ────────────────────────────────────────────────────
    if result["out"] or result["won"]:
        response["innings_over"] = True

        if innings == 1:
            # Save innings 1 data, set up innings 2
            state["innings1_log"]   = scorer.ball_log.copy()
            state["innings1_runs"]  = scorer.runs
            state["innings1_balls"] = scorer.balls_faced
            target = scorer.runs + 1
            state["target"] = target

            # Set up scorer for innings 2
            second_batter = "AI" if first_batter == name else name
            state["scorer"]     = Scorer(player_name=second_batter, target=target)
            state["innings"]    = 2
            state["ball_count"] = 0

            response["target"]        = target
            response["innings1_runs"] = scorer.runs

        else:
            # Innings 2 over — match done
            state["innings2_log"]   = scorer.ball_log.copy()
            state["innings2_runs"]  = scorer.runs
            state["innings2_balls"] = scorer.balls_faced

            # Determine winner
            i1_runs = state["innings1_runs"]
            i2_runs = scorer.runs
            target  = state["target"]

            if result["won"]:
                winner = batter
            elif result["out"]:
                winner = "AI" if batter == name else name
            else:
                winner = None

            response["match_over"]    = True
            response["winner"]        = winner
            response["innings1_runs"] = i1_runs
            response["innings2_runs"] = i2_runs

            # Save to DB
            match_summary = {
                "player1"       : name,
                "player2"       : "AI",
                "first_batter"  : first_batter,
                "innings1_runs" : i1_runs,
                "innings1_balls": state["innings1_balls"],
                "innings2_runs" : i2_runs,
                "innings2_balls": scorer.balls_faced,
                "winner"        : winner,
                "result"        : "chase" if result["won"] else "defended",
                "innings1_log"  : state["innings1_log"],
                "innings2_log"  : state["innings2_log"],
            }
            from brain.tracker import log_session
            session_id = log_session(match_summary)
            response["session_id"] = session_id

            # Insights
            insights = predictor.summary()
            response["insights"] = insights

    game_state[name] = state
    return response


# ── Insights (standalone) ────────────────────────────────────────────────
@app.get("/api/insights/{player_name}")
def get_insights(player_name: str):
    name      = player_name.strip().title()
    predictor = Predictor(name)
    return predictor.summary()
