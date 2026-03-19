"""
scorer.py
---------
Tracks runs, wickets, chase targets and determines win conditions.

Responsibilities:
  - Maintain current score and balls faced
  - Record each ball with context (for pattern brain later)
  - Evaluate win / loss / tie conditions
  - Determine if a super over is needed
"""


class Scorer:
    def __init__(self, player_name: str, target: int = None):
        """
        player_name : the batter's name
        target      : runs needed to win (None when batting first)
        """
        self.player_name = player_name
        self.target       = target          # None means batting first
        self.runs         = 0
        self.balls_faced  = 0
        self.is_out       = False
        self.ball_log     = []              # raw data for pattern brain later

    # ------------------------------------------------------------------ #
    #  Core scoring                                                        #
    # ------------------------------------------------------------------ #

    def add_ball(self, batter_num: int, bowler_num: int) -> dict:
        """
        Process one ball.

        Returns a result dict:
            {
                "out"      : bool,
                "runs"     : int,          # runs scored this ball (0 if out)
                "total"    : int,          # cumulative score
                "won"      : bool,         # chaser reached/passed target
                "ball_num" : int
            }
        """
        self.balls_faced += 1
        out = (batter_num == bowler_num)

        if out:
            self.is_out = True
            runs_this_ball = 0
        else:
            runs_this_ball = batter_num
            self.runs += runs_this_ball

        # Log every ball with context — pattern brain will read this later
        self.ball_log.append({
            "ball_num"    : self.balls_faced,
            "batter_num"  : batter_num,
            "bowler_num"  : bowler_num,
            "out"         : out,
            "runs_scored" : runs_this_ball,
            "total_after" : self.runs,
            "target"      : self.target,
            "score_bracket": self._score_bracket(),
            "pressure"    : self._pressure_state(),
        })

        won = self._check_win()

        return {
            "out"      : out,
            "runs"     : runs_this_ball,
            "total"    : self.runs,
            "won"      : won,
            "ball_num" : self.balls_faced,
        }

    # ------------------------------------------------------------------ #
    #  Win / loss logic                                                    #
    # ------------------------------------------------------------------ #

    def _check_win(self) -> bool:
        """Returns True only for the chaser reaching/passing the target."""
        if self.target is not None and self.runs >= self.target:
            return True
        return False

    def get_target_for_chaser(self) -> int:
        """Returns the target the next player needs to beat."""
        return self.runs + 1

    # ------------------------------------------------------------------ #
    #  Context helpers (used in ball log for pattern brain)               #
    # ------------------------------------------------------------------ #

    def _score_bracket(self) -> str:
        if self.runs < 50:
            return "0-50"
        elif self.runs < 100:
            return "50-100"
        elif self.runs < 150:
            return "100-150"
        else:
            return "150+"

    def _pressure_state(self) -> str:
        """Rough pressure classification — will be enriched later."""
        if self.target is None:
            return "normal"
        runs_needed = self.target - self.runs
        if runs_needed <= 1:
            return "last_ball"
        elif runs_needed <= 10:
            return "high_pressure"
        else:
            return "normal"

    # ------------------------------------------------------------------ #
    #  Display helpers                                                     #
    # ------------------------------------------------------------------ #

    def scorecard(self) -> str:
        status = "OUT" if self.is_out else "batting"
        return (
            f"{self.player_name}: {self.runs} runs "
            f"off {self.balls_faced} balls [{status}]"
        )

    def chase_status(self) -> str:
        if self.target is None:
            return ""
        needed = self.target - self.runs
        if needed <= 0:
            return f"  ✅ Target reached! {self.player_name} wins!"
        return f"  Needs {needed} more run(s) to win."
