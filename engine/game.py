"""
game.py
-------
The main game loop for Hand Cricket.

Handles:
  - A full innings (batting until out)
  - The chase innings
  - Super over if scores are tied
  - Feeding all ball data to Scorer and Predictor
"""

from engine.scorer   import Scorer
from brain.predictor import Predictor


def get_number(player_name: str) -> int:
    """Prompt a player for their number (1–10)."""
    while True:
        try:
            n = int(input(f"  {player_name}, your number (1–10): ").strip())
            if 1 <= n <= 10:
                return n
            print("  Must be 1–10.")
        except ValueError:
            print("  Enter a valid number.")


def play_innings(batter: str, bowler: str, target: int = None,
                 super_over: bool = False,
                 predictor: Predictor = None) -> Scorer:
    """
    Plays one full innings until the batter is out or (chasing) wins.
    If bowler == 'AI' and predictor is provided, uses pattern brain.
    Returns the Scorer object with full ball log.
    """
    import random
    scorer      = Scorer(player_name=batter, target=target)
    balls_limit = 6 if super_over else None

    label = "SUPER OVER" if super_over else "INNINGS"
    print(f"\n{'=' * 40}")
    print(f"  {batter} is BATTING  [{label}]")
    if target:
        print(f"  Target: {target} runs")
    if bowler == "AI":
        print(f"  Bowler: AI  🧠")
    print(f"{'=' * 40}")

    ball_count = 0

    while True:
        ball_count += 1
        print(f"\n  Ball {ball_count}  |  Score: {scorer.runs}")
        if target:
            print(f"  {scorer.chase_status()}")

        print("  --- Reveal ---")
        batter_num = get_number(batter)

        if bowler == "AI":
            if predictor is not None:
                bowler_num = predictor.predict(
                    ball_num      = ball_count,
                    score_bracket = scorer._score_bracket(),
                    pressure      = scorer._pressure_state(),
                )
            else:
                bowler_num = random.randint(1, 10)
            print(f"  AI bowled:  {bowler_num}")
        else:
            bowler_num = get_number(bowler)

        result = scorer.add_ball(batter_num, bowler_num)

        # Feed ball back to predictor for in-session learning
        if predictor is not None:
            predictor.update(scorer.ball_log[-1])

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


def play_super_over(player1: str, player2: str,
                    first_batter: str,
                    predictor: Predictor = None) -> str:
    """Runs a super over. Returns winner's name."""
    print("\n" + "🔥 " * 10)
    print("         S U P E R   O V E R")
    print("🔥 " * 10)

    second_batter = player2 if first_batter == player1 else player1
    first_bowler  = "AI" if second_batter == "AI" else second_batter
    second_bowler = "AI" if first_batter  == "AI" else first_batter

    innings1 = play_innings(first_batter, first_bowler,
                            super_over=True, predictor=predictor)
    target   = innings1.get_target_for_chaser()

    innings2 = play_innings(second_batter, second_bowler,
                            target=target, super_over=True,
                            predictor=predictor)

    if innings2.runs >= target:
        return second_batter
    elif innings2.is_out or innings2.runs < target:
        return first_batter
    else:
        print("\n  Super over tied! Another super over...")
        return play_super_over(player1, player2, second_batter, predictor)


def play_match(player1: str, player2: str, toss_result: dict,
               predictor: Predictor = None) -> dict:
    """
    Runs a complete Hand Cricket match.

    player2 should be "AI" when playing against the computer.
    predictor is the Predictor instance loaded for player1.
    """
    first_batter  = toss_result["batter"]
    first_bowler  = toss_result["bowler"]
    second_batter = player2 if first_batter == player1 else player1
    second_bowler = "AI"    if first_batter != "AI"    else player1

    # --- First innings ---
    innings1 = play_innings(first_batter, first_bowler,
                            predictor=predictor)
    target   = innings1.get_target_for_chaser()

    print(f"\n  {first_batter} scored {innings1.runs} runs.")
    print(f"  {second_batter} needs {target} to win.\n")
    input("  Press Enter when ready for the chase...")

    # --- Second innings ---
    innings2 = play_innings(second_batter, second_bowler,
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
        winner = play_super_over(player1, player2, second_batter, predictor)
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
