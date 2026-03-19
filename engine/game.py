"""
game.py — Phase 2 fixed
-----------------------
Key fixes:
  - Predictor only updates when human is BATTING (not bowling)
  - Bowler inputs number before AI reveals (no cheating)
  - Clear role separation throughout
"""

import random
from engine.scorer   import Scorer
from brain.predictor import Predictor


def get_number(player_name: str) -> int:
    """Prompt a human player for their number (1–10)."""
    while True:
        try:
            n = int(input(f"  {player_name}, your number (1–10): ").strip())
            if 1 <= n <= 10:
                return n
            print("  Must be 1–10.")
        except ValueError:
            print("  Enter a valid number.")


def ai_pick(predictor: Predictor = None, ball_num: int = 1,
            score_bracket: str = "0-50", pressure: str = "normal") -> int:
    """AI picks a number — via predictor if available, else random."""
    if predictor is not None:
        return predictor.predict(ball_num=ball_num,
                                 score_bracket=score_bracket,
                                 pressure=pressure)
    return random.randint(1, 10)


def play_innings(batter: str, bowler: str, human: str,
                 target: int = None, super_over: bool = False,
                 predictor: Predictor = None) -> Scorer:
    """
    Plays one full innings.

    batter    : who is batting
    bowler    : who is bowling
    human     : human player's name (determines who types input)
    predictor : only used when AI is bowling against human
                AND only updated when human is batting
    """
    scorer      = Scorer(player_name=batter, target=target)
    balls_limit = 6 if super_over else None
    human_is_batting = (batter == human)

    label = "SUPER OVER" if super_over else "INNINGS"
    print(f"\n{'=' * 40}")
    print(f"  {batter} is BATTING  [{label}]")
    if target:
        print(f"  Target: {target} runs")
    print(f"  Bowler: {bowler}")
    print(f"{'=' * 40}")

    ball_count = 0

    while True:
        ball_count += 1
        print(f"\n  Ball {ball_count}  |  Score: {scorer.runs}")
        if target:
            print(f"  {scorer.chase_status()}")

        print("  --- Reveal ---")

        if human_is_batting:
            # ── Human bats, AI bowls ─────────────────────────────────────
            # AI picks silently first, human types, then both revealed
            bowler_num = ai_pick(
                predictor     = predictor,
                ball_num      = ball_count,
                score_bracket = scorer._score_bracket(),
                pressure      = scorer._pressure_state(),
            )
            batter_num = get_number(human)
            print(f"  AI bowled:  {bowler_num}")

        else:
            # ── AI bats, Human bowls ─────────────────────────────────────
            # Human types bowl number first, then AI number revealed
            bowler_num = get_number(f"{human} (bowling)")
            batter_num = random.randint(1, 10)
            print(f"  AI batted:  {batter_num}")

        result = scorer.add_ball(batter_num, bowler_num)

        # Only update predictor when human is batting
        # We want to learn human's batting patterns, not bowling patterns
        if predictor is not None and human_is_batting:
            predictor.update(scorer.ball_log[-1])

        # ── Display result ───────────────────────────────────────────────
        if result["out"]:
            print(f"\n  💥 OUT! Both chose {batter_num}!")
            print(f"  {scorer.scorecard()}")
            break
        else:
            print(f"  +{result['runs']} runs  →  Total: {result['total']}")

        if result["won"]:
            print(f"\n  🏆 {batter} reaches the target!")
            print(f"  {scorer.scorecard()}")
            break

        if super_over and ball_count >= balls_limit:
            print(f"\n  Super over ended. {scorer.scorecard()}")
            break

    return scorer


def play_super_over(player1: str, player2: str, human: str,
                    first_batter: str,
                    predictor: Predictor = None) -> str:
    """Runs a super over (6 balls per side). Returns winner's name."""
    print("\n" + "🔥 " * 10)
    print("         S U P E R   O V E R")
    print("🔥 " * 10)

    second_batter = player2 if first_batter == player1 else player1
    first_bowler  = player2 if first_batter == player1 else player1
    second_bowler = player1 if first_batter == player1 else player2

    innings1 = play_innings(first_batter, first_bowler, human,
                            super_over=True, predictor=predictor)
    target   = innings1.get_target_for_chaser()

    innings2 = play_innings(second_batter, second_bowler, human,
                            target=target, super_over=True,
                            predictor=predictor)

    if innings2.runs >= target:
        return second_batter
    elif innings2.is_out or innings2.runs < target:
        return first_batter
    else:
        print("\n  Super over tied! Another super over...")
        return play_super_over(player1, player2, human,
                               second_batter, predictor)


def play_match(player1: str, player2: str, human: str,
               toss_result: dict,
               predictor: Predictor = None) -> dict:
    """
    Runs a complete Hand Cricket match.

    player1, player2 : the two players (one is "AI")
    human            : human player's name
    toss_result      : {"batter": <name>, "bowler": <name>}
    predictor        : loaded for human — AI uses this to bowl
    """
    first_batter  = toss_result["batter"]
    first_bowler  = player2 if first_batter == player1 else player1
    second_batter = player2 if first_batter == player1 else player1
    second_bowler = player1 if first_batter == player1 else player2

    # --- First innings ---
    innings1 = play_innings(first_batter, first_bowler, human,
                            predictor=predictor)
    target   = innings1.get_target_for_chaser()

    print(f"\n  {first_batter} scored {innings1.runs} runs.")
    print(f"  {second_batter} needs {target} to win.\n")
    input("  Press Enter when ready for the chase...")

    # --- Second innings ---
    innings2 = play_innings(second_batter, second_bowler, human,
                            target=target, predictor=predictor)

    # --- Result ---
    if innings2.runs >= target:
        winner = second_batter
        result = "chase"
    elif innings2.is_out and innings2.runs < target:
        winner = first_batter
        result = "defended"
    else:
        winner = None
        result = "tie"

    if result == "tie":
        winner = play_super_over(player1, player2, human,
                                 second_batter, predictor)
        result = "super_over"

    print("\n" + "=" * 40)
    print("         M A T C H   O V E R")
    print("=" * 40)
    print(f"\n  {first_batter}:  {innings1.runs} runs")
    print(f"  {second_batter}: {innings2.runs} runs")
    print(f"\n  🏆 Winner: {winner.upper()}")
    print("=" * 40)

    return {
        "player1"       : player1,
        "player2"       : player2,
        "first_batter"  : first_batter,
        "innings1_runs" : innings1.runs,
        "innings1_balls": innings1.balls_faced,
        "innings2_runs" : innings2.runs,
        "innings2_balls": innings2.balls_faced,
        "winner"        : winner,
        "result"        : result,
        "innings1_log"  : innings1.ball_log,
        "innings2_log"  : innings2.ball_log,
    }
