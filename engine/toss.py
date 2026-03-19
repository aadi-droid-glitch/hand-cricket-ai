"""
toss.py
-------
Handles the toss at the start of every Hand Cricket game.

How it works:
  - Player 1 calls "odd" or "even"
  - Both players simultaneously reveal a number (1–10)
  - Sum of both numbers determines odd or even
  - Whoever wins the toss chooses to bat or bowl
"""


def get_toss_call(player_name: str) -> str:
    """Ask a player to call odd or even."""
    while True:
        call = input(f"\n{player_name}, call it — odd or even? ").strip().lower()
        if call in ("odd", "even"):
            return call
        print("  Please type 'odd' or 'even'.")


def get_toss_number(player_name: str) -> int:
    """Ask a player to reveal their toss number (1–10)."""
    while True:
        try:
            number = int(input(f"{player_name}, enter your number (1–10): ").strip())
            if 1 <= number <= 10:
                return number
            print("  Number must be between 1 and 10.")
        except ValueError:
            print("  Please enter a valid number.")


def resolve_toss(call: str, n1: int, n2: int) -> bool:
    """
    Returns True if the caller wins the toss.
    Caller wins if the sum matches their odd/even call.
    """
    total = n1 + n2
    result = "odd" if total % 2 != 0 else "even"
    return result == call


def get_batting_choice(player_name: str) -> str:
    """Ask the toss winner whether they want to bat or bowl."""
    while True:
        choice = input(f"\n{player_name} won the toss! Bat or bowl? ").strip().lower()
        if choice in ("bat", "bowl"):
            return choice
        print("  Please type 'bat' or 'bowl'.")


def run_toss(player1: str, player2: str) -> dict:
    """
    Runs the full toss sequence.

    Returns a dict:
        {
            "batter": <name of player who bats first>,
            "bowler": <name of player who bowls first>
        }
    """
    print("\n" + "=" * 40)
    print("           T O S S")
    print("=" * 40)

    # Player 1 makes the call
    call = get_toss_call(player1)

    # Both reveal numbers
    print("\nBoth players reveal your toss numbers:")
    n1 = get_toss_number(player1)
    n2 = get_toss_number(player2)

    total = n1 + n2
    result = "odd" if total % 2 != 0 else "even"
    print(f"\n  {player1} chose {n1}, {player2} chose {n2} → sum is {total} ({result})")

    caller_wins = resolve_toss(call, n1, n2)
    toss_winner = player1 if caller_wins else player2
    toss_loser  = player2 if caller_wins else player1

    print(f"  {player1} called {call.upper()} → {'correct' if caller_wins else 'wrong'}!")
    print(f"\n🏆 {toss_winner} wins the toss!")

    # Toss winner picks bat or bowl
    choice = get_batting_choice(toss_winner)

    if choice == "bat":
        batter = toss_winner
        bowler = toss_loser
    else:
        batter = toss_loser
        bowler = toss_winner

    print(f"\n  {batter} will bat first.")
    print(f"  {bowler} will bowl first.")
    print("=" * 40)

    return {"batter": batter, "bowler": bowler}
