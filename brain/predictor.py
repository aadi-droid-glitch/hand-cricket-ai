"""
predictor.py
------------
The pattern brain. Reads a player's ball history from the database
and uses it to predict what number they are most likely to throw next.

Strategy layers (applied in order of available data):

  1. Context-weighted frequency
  2. Streak detection
  3. Recent bias (last 5 balls)
  4. First ball tendency
  5. Global frequency fallback
  6. Pure random fallback
"""

import random
from collections import Counter
from brain.tracker import get_player_ball_history


def _frequency_table(balls: list, key: str = "batter_num") -> dict:
    """Returns a {number: count} dict from a list of ball dicts."""
    counts = Counter(b[key] for b in balls if not b["out"])
    return dict(counts)


def _full_frequency_table(balls: list) -> dict:
    """
    Returns frequency for ALL numbers 1-10, including zeros.
    This ensures least_used always finds the truly least thrown number.
    """
    base = {n: 0 for n in range(1, 11)}
    for b in balls:
        if not b["out"]:
            base[b["batter_num"]] = base.get(b["batter_num"], 0) + 1
    return base


def _weighted_choice(freq: dict) -> int:
    """Picks a number weighted by frequency. Higher = more likely."""
    if not freq:
        return random.randint(1, 10)
    numbers = list(freq.keys())
    weights = list(freq.values())
    return random.choices(numbers, weights=weights, k=1)[0]


def _merge_freq(base: dict, overlay: dict, overlay_weight: float = 2.0) -> dict:
    """Merges two frequency tables, giving overlay entries extra weight."""
    merged = dict(base)
    for num, count in overlay.items():
        merged[num] = merged.get(num, 0) + count * overlay_weight
    return merged


class Predictor:
    def __init__(self, player_name: str):
        self.player_name   = player_name
        self.history       = get_player_ball_history(player_name)
        self.session_balls = []

    def update(self, ball: dict):
        """Call after every batting ball to keep predictor current."""
        self.session_balls.append(ball)

    def predict(self, ball_num: int, score_bracket: str,
                pressure: str) -> int:
        """Returns the number the AI will bowl this ball."""
        all_balls = self.history + self.session_balls

        if not all_balls:
            return random.randint(1, 10)

        global_freq = _frequency_table(all_balls)

        # Layer 1: context-weighted frequency
        context_balls = [
            b for b in all_balls
            if b["score_bracket"] == score_bracket
            and b["pressure"]      == pressure
        ]
        context_freq = _frequency_table(context_balls) if context_balls else {}

        # Layer 4: first ball tendency
        if ball_num == 1:
            first_balls = [b for b in all_balls if b["ball_num"] == 1]
            first_freq  = _frequency_table(first_balls) if first_balls else {}
            if first_freq:
                freq = _merge_freq(global_freq, first_freq, overlay_weight=3.0)
                return _weighted_choice(freq)

        # Layer 3: recent bias
        recent      = self.session_balls[-5:] if len(self.session_balls) >= 2 else []
        recent_freq = _frequency_table(recent) if recent else {}

        # Blend all layers
        freq = _merge_freq(global_freq, context_freq, overlay_weight=2.0)
        freq = _merge_freq(freq,        recent_freq,  overlay_weight=2.5)

        # Layer 2: streak detection
        if len(self.session_balls) >= 2:
            last_two = [b["batter_num"] for b in self.session_balls[-2:]
                        if not b["out"]]
            if len(last_two) == 2 and last_two[0] == last_two[1]:
                streak_num = last_two[0]
                freq[streak_num] = freq.get(streak_num, 0) * 1.8

        return _weighted_choice(freq)

    def predictability_score(self) -> float:
        """
        Returns 0–100 score. Higher = more predictable.
        Needs at least 15 balls to be meaningful (raised from 10).
        Returns -1 if not enough data.
        """
        all_balls = self.history + self.session_balls
        non_out   = [b for b in all_balls if not b["out"]]

        if len(non_out) < 15:
            return -1

        hits  = 0
        total = 0

        for i, ball in enumerate(non_out):
            prior = non_out[:i]
            if len(prior) < 8:
                continue

            freq = _frequency_table(prior)
            if not freq:
                continue

            best_guess = max(freq, key=freq.get)
            if best_guess == ball["batter_num"]:
                hits += 1
            total += 1

        if total == 0:
            return -1

        score = round((hits / total) * 100, 1)
        # A 10% hit rate is expected by pure chance (1/10 numbers)
        # Anything above that is true predictability
        return score

    def summary(self) -> dict:
        """Returns pattern summary for the insights dashboard."""
        all_balls = self.history + self.session_balls
        if not all_balls:
            return {"message": "No data yet."}

        non_out = [b for b in all_balls if not b["out"]]
        if not non_out:
            return {"message": "No data yet."}

        # Use full table so zeros are visible for least_used
        full_freq = _full_frequency_table(non_out)
        thrown    = {k: v for k, v in full_freq.items() if v > 0}

        favourite  = max(full_freq, key=full_freq.get)

        # Least used = lowest count including zeros (truly never thrown)
        least_used = min(full_freq, key=full_freq.get)

        # First ball tendency — only report if seen 2+ times
        first_balls = [b["batter_num"] for b in all_balls if b["ball_num"] == 1]
        first_freq  = Counter(first_balls)
        if first_freq and first_freq.most_common(1)[0][1] >= 2:
            most_common_first = first_freq.most_common(1)[0][0]
        else:
            most_common_first = "Too early to tell"

        pred_score = self.predictability_score()
        if pred_score < 0:
            pred_label = f"Need {max(0, 15 - len(non_out))} more balls to calculate"
        elif pred_score <= 12:
            pred_label = f"{pred_score}%  (hard to read 👀)"
        elif pred_score <= 25:
            pred_label = f"{pred_score}%  (some patterns showing)"
        elif pred_score <= 40:
            pred_label = f"{pred_score}%  (getting predictable)"
        else:
            pred_label = f"{pred_score}%  (very predictable 😬)"

        return {
            "player"             : self.player_name,
            "total_balls"        : len(all_balls),
            "favourite_number"   : favourite,
            "least_used_number"  : least_used,
            "first_ball_tendency": most_common_first,
            "predictability"     : pred_label,
            "number_frequency"   : full_freq,
        }
