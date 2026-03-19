"""
main.py
-------
Entry point for Hand Cricket AI — Phase 1 (terminal mode).

Run with:
    python main.py
"""

from engine.toss import run_toss
from engine.game import play_match


def get_player_name(prompt: str) -> str:
    name = input(prompt).strip()
    return name if name else "Player"


def main():
    print("\n" + "🏏 " * 14)
    print("       H A N D   C R I C K E T   A I")
    print("🏏 " * 14)
    print("\n  Phase 1 — Terminal Mode")
    print("  Pattern brain coming in Phase 2.\n")

    # Get player names
    p1 = get_player_name("  Player 1 name: ")
    p2 = get_player_name("  Player 2 name: ")

    while True:
        # Toss
        toss_result = run_toss(p1, p2)

        # Play match
        summary = play_match(p1, p2, toss_result)

        # Print ball logs (raw data — pattern brain reads this in Phase 2)
        print("\n  --- Ball log (innings 1) ---")
        for ball in summary["innings1_log"]:
            status = "OUT" if ball["out"] else f"+{ball['runs_scored']}"
            print(
                f"  Ball {ball['ball_num']:>2} | "
                f"Batter: {ball['batter_num']:>2}  Bowler: {ball['bowler_num']:>2} | "
                f"{status:>4} | Total: {ball['total_after']:>3} | "
                f"Bracket: {ball['score_bracket']} | Pressure: {ball['pressure']}"
            )

        print("\n  --- Ball log (innings 2) ---")
        for ball in summary["innings2_log"]:
            status = "OUT" if ball["out"] else f"+{ball['runs_scored']}"
            print(
                f"  Ball {ball['ball_num']:>2} | "
                f"Batter: {ball['batter_num']:>2}  Bowler: {ball['bowler_num']:>2} | "
                f"{status:>4} | Total: {ball['total_after']:>3} | "
                f"Bracket: {ball['score_bracket']} | Pressure: {ball['pressure']}"
            )

        # Play again?
        again = input("\n  Play again? (yes / no): ").strip().lower()
        if again not in ("yes", "y"):
            print("\n  Thanks for playing. Pattern brain is watching. 👁️\n")
            break


if __name__ == "__main__":
    main()
