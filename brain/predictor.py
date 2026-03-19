"""
predictor.py
------------
The pattern brain. Reads a player's ball history from the database
and uses it to predict what number they are most likely to throw next.

Strategy layers (applied in order of available data):

  1. Context-weighted frequency
       — How often has this player thrown each number in this
         exact context (score bracket + pressure state)?

  2. Streak avoidance
       — Did the player just throw the same number 2+ times?
         Humans usually stop repeating. Boost probability of that number.
         (counter-intuitive: they might think "surely I'll switch" but
          sometimes they don't — like the 10-in-a-row story)

  3. Recent bias (last 5 balls)
       — What has the player thrown in the last 5 balls?
         Recent behaviour outweighs historical averages.

  4. First ball tendency
       — On ball 1 of an innings, use the player's historical
         first-ball distribution specifically.

  5. Global frequency fallback
       — If not enough context data exists, fall back to overall
         number frequency across all sessions.

  6. Pure random fallback
       — Brand new player with zero history. Pick randomly.
"""

import random
from collections import Counter
from brain.tracker import get_player_ball_history


# ── Helpers ──────────────────────────────────────────────────────────────

def _frequency_table(balls: list, key: str = "batter_num") -> dict:
    """Returns a {number: count} dict from a list of ball dicts."""
    counts = Counter(b[key] for b in balls if not b["out"])
    return dict(counts)


def _weighted_choice(freq: dict) -> int:
    """
    Picks a number 1-10 weighted by frequency.
    Higher frequency = more likely to be chosen as the bowl number.
    """
    if not freq:
        return random.randint(1, 10)

    numbers = list(freq.keys())
    weights = list(freq.values())
    return random.choices(numbers, weights=weights, k=1)[0]


def _merge_freq(base: dict, overlay: dict, overlay_weight: float = 2.0) -> dict:
    """
    Merges two frequency tables, giving overlay entries extra weight.
    Used to blend historical + recent data.
    """
    merged = dict(base)
    for num, count in overlay.items():
        merged[num] = merged.get(num, 0) + count * overlay_weight
    return merged


# ── Core predictor ────────────────────────────────────────────────────────

class Predictor:
    def __init__(self, player_name: str):
        self.player_name = player_name
        self.history     = get_player_ball_history(player_name)
        self.session_balls = []   # balls from current session (added live)

    def update(self, ball: dict):
        """Call this after every ball to keep the predictor current."""
        self.session_balls.append(ball)

    def predict(self, ball_num: int, score_bracket: str,
                pressure: str) -> int:
        """
        Returns the number the AI will bowl this ball.

        Parameters:
            ball_num      : current ball number in this innings
            score_bracket : '0-50' | '50-100' | '100-150' | '150+'
            pressure      : 'normal' | 'high_pressure' | 'last_ball'
        """
        all_balls = self.history + self.session_balls

        # ── Layer 6: pure random (no data at all) ────────────────────────
        if not all_balls:
            return random.randint(1, 10)

        # ── Layer 5: global frequency baseline ──────────────────────────
        global_freq = _frequency_table(all_balls)

        # ── Layer 1: context-weighted frequency ──────────────────────────
        context_balls = [
            b for b in all_balls
            if b["score_bracket"] == score_bracket
            and b["pressure"]      == pressure
        ]
        context_freq = _frequency_table(context_balls) if context_balls else {}

        # ── Layer 4: first ball tendency ─────────────────────────────────
        if ball_num == 1:
            first_balls = [b for b in all_balls if b["ball_num"] == 1]
            first_freq  = _frequency_table(first_balls) if first_balls else {}
            if first_freq:
                # First ball data is very reliable — give it strong weight
                freq = _merge_freq(global_freq, first_freq, overlay_weight=3.0)
                return _weighted_choice(freq)

        # ── Layer 3: recent bias (last 5 balls this session) ─────────────
        recent = self.session_balls[-5:] if len(self.session_balls) >= 2 else []
        recent_freq = _frequency_table(recent) if recent else {}

        # ── Blend: context + recent on top of global ─────────────────────
        freq = _merge_freq(global_freq, context_freq, overlay_weight=2.0)
        freq = _merge_freq(freq,        recent_freq,  overlay_weight=2.5)

        # ── Layer 2: streak detection ────────────────────────────────────
        # If player threw same number 2+ times recently, boost it further
        if len(self.session_balls) >= 2:
            last_two = [b["batter_num"] for b in self.session_balls[-2:]
                        if not b["out"]]
            if len(last_two) == 2 and last_two[0] == last_two[1]:
                streak_num = last_two[0]
                # They've repeated — might keep going (boost) or stop.
                # We boost since streaks DO happen (the 10x story).
                freq[streak_num] = freq.get(streak_num, 0) * 1.8

        return _weighted_choice(freq)

    def predictability_score(self) -> float:
        """
        Returns a 0–100 score showing how predictable this player is.
        Based on what % of their balls the AI could have predicted correctly
        using only prior history (leave-one-out estimate).

        Returns -1 if not enough data.
        """
        all_balls = self.history + self.session_balls
        if len(all_balls) < 10:
            return -1

        hits   = 0
        total  = 0

        for i, ball in enumerate(all_balls):
            if ball["out"]:
                continue
            prior = all_balls[:i]
            if len(prior) < 5:
                continue

            freq = _frequency_table(prior)
            if not freq:
                continue

            # What would the AI have guessed?
            best_guess = max(freq, key=freq.get)
            if best_guess == ball["batter_num"]:
                hits += 1
            total += 1

        if total == 0:
            return -1

        return round((hits / total) * 100, 1)

    def summary(self) -> dict:
        """
        Returns a human-readable pattern summary for the insights dashboard.
        """
        all_balls = self.history + self.session_balls
        if not all_balls:
            return {"message": "No data yet."}

        non_out = [b for b in all_balls if not b["out"]]
        freq    = _frequency_table(non_out)

        if not freq:
            return {"message": "No data yet."}

        favourite   = max(freq, key=freq.get)
        least_used  = min(freq, key=freq.get)
        first_balls = [b["batter_num"] for b in all_balls if b["ball_num"] == 1]
        first_freq  = Counter(first_balls)
        most_common_first = first_freq.most_common(1)[0][0] if first_freq else "?"

        pred_score  = self.predictability_score()
        pred_label  = (
            f"{pred_score}%" if pred_score >= 0
            else "Not enough data yet"
        )

        return {
            "player"            : self.player_name,
            "total_balls"       : len(all_balls),
            "favourite_number"  : favourite,
            "least_used_number" : least_used,
            "first_ball_tendency": most_common_first,
            "predictability"    : pred_label,
            "number_frequency"  : freq,
        }
