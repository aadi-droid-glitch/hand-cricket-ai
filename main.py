"""
main.py
-------
Entry point for Hand Cricket AI — Phase 2.
Human vs AI — pattern brain active.

Run with:
    python main.py
"""

from brain.database  import init_db, get_or_create_player
from brain.tracker   import log_session, get_player_profile
from brain.predictor import Predictor
from engine.toss     import run_toss
from engine.game     import play_match


def get_player_name(prompt: str) -> str:
    name = input(prompt).strip()
    return name if name else "Player"


def show_insights(predictor: Predictor):
    s = predictor.summary()
    if "message" in s:
        print(f"\n  {s['message']}")
        return

    print("\n" + "=" * 40)
    print("         I N S I G H T S")
    print("=" * 40)
    print(f"\n  Player         : {s['player']}")
    print(f"  Total balls    : {s['total_balls']}")
    print(f"  Favourite no.  : {s['favourite_number']}")
    print(f"  Least used     : {s['least_used_number']}")
    print(f"  First ball     : {s['first_ball_tendency']} (most common opener)")
    print(f"  Predictability : {s['predictability']}")

    print("\n  Number distribution (non-out balls):")
    freq  = s["number_frequency"]
    total = sum(freq.values()) or 1
    for num in range(1, 11):
        count = freq.get(num, 0)
        pct   = count / total * 100
        bar   = "█" * int(pct / 4)
        print(f"    {num:>2}  {bar:<25} {pct:>5.1f}%  ({count})")
    print("=" * 40)


def main():
    print("\n" + "🏏 " * 14)
    print("       H A N D   C R I C K E T   A I")
    print("🏏 " * 14)
    print("\n  Phase 2 — Pattern Brain Active 🧠\n")

    init_db()

    human = get_player_name("  Your name: ")
    ai    = "AI"

    get_or_create_player(human)
    predictor = Predictor(human)

    print(f"\n  Welcome, {human}!")
    profile = get_player_profile(human)
    if profile and profile.get("matches_played", 0) > 0:
        mp  = profile["matches_played"]
        mw  = profile["matches_won"]
        avg = (profile["total_runs"] / profile["total_balls"] * 10
               if profile["total_balls"] > 0 else 0)
        print(f"  Matches played : {mp}")
        print(f"  Wins           : {mw}")
        print(f"  Scoring rate   : {avg:.1f} runs per 10 balls")
        pred = predictor.predictability_score()
        if pred >= 0:
            print(f"  Predictability : {pred}%  👁️")
    else:
        print("  No history yet — the AI is watching from ball one.")

    while True:
        print()
        # Pass human name so toss and game know who needs input
        toss_result = run_toss(human, ai, human=human)
        summary     = play_match(human, ai, human=human,
                                 toss_result=toss_result,
                                 predictor=predictor)
        session_id  = log_session(summary)
        print(f"\n  📊 Match saved. Session #{session_id}")
        show_insights(predictor)

        again = input("\n  Play again? (yes / no): ").strip().lower()
        if again not in ("yes", "y"):
            print(f"\n  See you next time, {human}.")
            print("  The pattern brain never forgets. 👁️\n")
            break


if __name__ == "__main__":
    main()
