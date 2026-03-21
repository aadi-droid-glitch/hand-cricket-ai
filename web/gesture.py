"""
web/gesture.py — v5
--------------------
Hand Cricket number mapping:

  1  → index only                    (thumb tucked)
  2  → index + middle                (thumb tucked)
  3  → index + middle + ring         (thumb tucked)
  4  → all four fingers              (thumb tucked)
  6  → thumb only                    (thumbs up 👍)
  7  → thumb + index
  8  → thumb + index + middle
  9  → thumb + index + middle + ring
  10 → all five out
"""


def _is_palm_facing_camera(landmarks) -> bool:
    wrist     = landmarks[0]
    index_mcp = landmarks[5]
    pinky_mcp = landmarks[17]
    v1x = index_mcp.x - wrist.x
    v1y = index_mcp.y - wrist.y
    v2x = pinky_mcp.x - wrist.x
    v2y = pinky_mcp.y - wrist.y
    return (v1x * v2y - v1y * v2x) > 0


def _finger_states(landmarks, palm_facing: bool) -> dict:
    lm = landmarks

    # Thumb: tip to the RIGHT of knuckle = extended (thumb out)
    thumb_out = lm[4].x > lm[3].x

    index_up  = lm[8].y  < lm[6].y
    middle_up = lm[12].y < lm[10].y
    ring_up   = lm[16].y < lm[14].y
    pinky_up  = lm[20].y < lm[18].y

    return {
        "thumb" : thumb_out,
        "index" : index_up,
        "middle": middle_up,
        "ring"  : ring_up,
        "pinky" : pinky_up,
    }


def classify_number(landmarks) -> int:
    palm_facing = _is_palm_facing_camera(landmarks)
    f           = _finger_states(landmarks, palm_facing)

    thumb  = f["thumb"]
    index  = f["index"]
    middle = f["middle"]
    ring   = f["ring"]
    pinky  = f["pinky"]

    count = sum([index, middle, ring, pinky])

    # ── No thumb: 1-4 ────────────────────────────────────────────────────
    if not thumb:
        if count == 0:
            return 0       # fist — no number
        if count == 1 and index:
            return 1
        if count == 2 and index and middle:
            return 2
        if count == 3 and index and middle and ring:
            return 3
        if count == 4:
            return 4

    # ── Thumb out: 6-10 ──────────────────────────────────────────────────
    if thumb:
        if count == 0:
            return 6       # thumbs up
        if count == 1 and index:
            return 7
        if count == 2 and index and middle:
            return 8
        if count == 3 and index and middle and ring:
            return 9
        if count == 4:
            return 10

    return 0


def classify_stable(history: list, min_votes: int = 4) -> int:
    if not history:
        return 0
    from collections import Counter
    counts = Counter(h for h in history if h > 0)
    if not counts:
        return 0
    best, votes = counts.most_common(1)[0]
    return best if votes >= min_votes else 0


def get_number_label(number: int) -> str:
    labels = {
        0 : "Hold steady...",
        1 : "1 — Index only",
        2 : "2 — Index + Middle",
        3 : "3 — Three fingers",
        4 : "4 — Four fingers",
        6 : "6 — Thumb only 👍",
        7 : "7 — Thumb + Index",
        8 : "8 — Thumb + Index + Middle",
        9 : "9 — Thumb + Three fingers",
        10: "10 — All five out",
    }
    return labels.get(number, "?")
