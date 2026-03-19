"""
toss.py
-------
Handles the toss at the start of every Hand Cricket game.

How it works:
  - Human player calls odd or even
  - Both reveal a number simultaneously
  - Sum decides odd or even → winner picks bat or bowl
"""

import random


def get_toss_call(player_name: str) -> str:
    """Ask the human to call odd or even."""
    while True:
        call = input(f"\n{player_name}, call it — odd or even? ").strip().lower()
        if call in ("odd", "even"):
            return call
        print("  Please type 'odd' or 'even'.")


def get_toss_number(player_name: str, is_ai: bool = False) -> int:
    """Get a toss number — human types, AI picks randomly."""
    if is_ai:
        n = random.randint(1, 10)
        print(f"  AI entered: {n}")
        return n
    while True:
        try:
            number = int(input(f"  {player_name}, enter your number (1–10): ").strip())
            if 1 <= number <= 10:
                return number
            print("  Number must be between 1 and 10.")
        except ValueError:
            print("  Please enter a valid number.")


def resolve_toss(call: str, n1: int, n2: int) -> bool:
    """Returns True if the caller wins."""
    total  = n1 + n2
    result = "odd" if total % 2 != 0 else "even"
    return result == call


def get_batting_choice(player_name: str, is_ai: bool = False) -> str:
    """Toss winner chooses bat or bowl."""
    if is_ai:
        choice = random.choice(["bat", "bowl"])
        print(f"  AI chose to {choice}.")
        return choice
    while True:
        choice = input(f"\n{player_name} won the toss! Bat or bowl? ").strip().lower()
        if choice in ("bat", "bowl"):
            return choice
        print("  Please type 'bat' or 'bowl'.")


def run_toss(player1: str, player2: str, human: str) -> dict:
    """
    Runs the full toss sequence.
    human : the human player's name (so AI inputs are automated)

    Returns {"batter": <name>, "bowler": <name>}
    """
    print("\n" + "=" * 40)
    print("           T O S S")
    print("=" * 40)

    # Human always makes the call
    call = get_toss_call(human)

    print("\n  Both players reveal your toss numbers:")
    p1_is_ai = (player1 != human)
    p2_is_ai = (player2 != human)

    n1 = get_toss_number(player1, is_ai=p1_is_ai)
    n2 = get_toss_number(player2, is_ai=p2_is_ai)

    total  = n1 + n2
    result = "odd" if total % 2 != 0 else "even"
    print(f"\n  {player1} chose {n1}, {player2} chose {n2} → sum is {total} ({result})")

    caller_wins = resolve_toss(call, n1, n2)
    toss_winner = player1 if caller_wins else player2
    toss_loser  = player2 if caller_wins else player1

    print(f"  {human} called {call.upper()} → {'correct!' if caller_wins == (player1 == human) else 'wrong!'}")
    print(f"\n🏆 {toss_winner} wins the toss!")

    winner_is_ai = (toss_winner != human)
    choice = get_batting_choice(toss_winner, is_ai=winner_is_ai)

    batter = toss_winner  if choice == "bat"  else toss_loser
    bowler = toss_loser   if choice == "bat"  else toss_winner

    print(f"\n  {batter} will bat first.")
    print(f"  {bowler} will bowl first.")
    print("=" * 40)

    return {"batter": batter, "bowler": bowler}
