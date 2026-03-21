"""
test_gesture.py — v3 (debug mode)
----------------------------------
Shows live finger state debug info so we can see exactly
what the classifier is reading per finger.

Press SPACE to snapshot. Press Q to quit.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.core import base_options as base_options_module
import time, sys, os
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from web.gesture import (classify_number, classify_stable,
                          get_number_label, _finger_states,
                          _is_palm_facing_camera)

MODEL_PATH = "hand_landmarker.task"
if not os.path.exists(MODEL_PATH):
    import urllib.request
    print("Downloading model...")
    urllib.request.urlretrieve(
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
        MODEL_PATH
    )

options = HandLandmarkerOptions(
    base_options=base_options_module.BaseOptions(model_asset_path=MODEL_PATH),
    num_hands=1,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.5,
    running_mode=vision.RunningMode.IMAGE,
)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Cannot open camera.")
    exit()

STATE_IDLE = "idle"
STATE_COUNTDOWN = "countdown"
STATE_RESULT = "result"

state           = STATE_IDLE
countdown_start = 0
COUNTDOWN_SECS  = 3
result_start    = 0
RESULT_SECS     = 2
snapshot_result = 0
recent_readings = []

print("Press SPACE to countdown+snapshot. Press Q to quit.")

with HandLandmarker.create_from_options(options) as detector:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame  = cv2.flip(frame, 1)
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(mp_img)

        h, w   = frame.shape[:2]
        now    = time.time()
        current_num  = 0
        debug_lines  = []

        if result.hand_landmarks:
            hand = result.hand_landmarks[0]

            # Draw dots
            for lm in hand:
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(frame, (cx, cy), 5, (0, 255, 136), -1)

            # Debug info
            palm_facing = _is_palm_facing_camera(hand)
            f           = _finger_states(hand, palm_facing)
            current_num = classify_number(hand)

            debug_lines = [
                f"Palm facing cam: {'YES' if palm_facing else 'NO'}",
                f"Thumb : {'UP' if f['thumb']  else '--'}",
                f"Index : {'UP' if f['index']  else '--'}",
                f"Middle: {'UP' if f['middle'] else '--'}",
                f"Ring  : {'UP' if f['ring']   else '--'}",
                f"Pinky : {'UP' if f['pinky']  else '--'}",
            ]
        else:
            debug_lines = ["No hand detected"]

        # ── Draw debug panel (top right) ─────────────────────────────────
        panel_x = w - 230
        cv2.rectangle(frame, (panel_x - 10, 10),
                      (w - 10, 175), (20, 20, 20), -1)
        for i, line in enumerate(debug_lines):
            color = (0, 255, 136) if "UP" in line else (120, 120, 120)
            if "Palm" in line:
                color = (255, 200, 0)
            cv2.putText(frame, line, (panel_x, 35 + i * 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1)

        # ── States ────────────────────────────────────────────────────────
        if state == STATE_IDLE:
            recent_readings.append(current_num)
            if len(recent_readings) > 10:
                recent_readings.pop(0)

            color = (0, 255, 136) if current_num > 0 else (80, 80, 80)
            cv2.putText(frame, str(current_num) if current_num else "?",
                        (w//2 - 40, h//2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 4, color, 8)
            cv2.putText(frame, get_number_label(current_num),
                        (10, h - 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
            cv2.putText(frame, "SPACE = countdown  Q = quit",
                        (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 1)

        elif state == STATE_COUNTDOWN:
            elapsed   = now - countdown_start
            remaining = COUNTDOWN_SECS - elapsed
            recent_readings.append(current_num)
            if len(recent_readings) > 15:
                recent_readings.pop(0)

            if remaining > 0:
                cv2.putText(frame, str(int(remaining) + 1),
                            (w//2 - 40, h//2 + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 170, 0), 10)
                cv2.putText(frame, "HOLD STEADY",
                            (10, h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 170, 0), 2)
            else:
                snapshot_result = classify_stable(recent_readings, min_votes=3)
                recent_readings = []
                state        = STATE_RESULT
                result_start = now

        elif state == STATE_RESULT:
            color = (0, 255, 136) if snapshot_result > 0 else (255, 68, 85)
            disp  = str(snapshot_result) if snapshot_result > 0 else "?"
            cv2.putText(frame, "SHOW!", (w//2 - 80, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 136), 4)
            cv2.putText(frame, disp,
                        (w//2 - 60, h//2 + 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 5, color, 12)
            cv2.putText(frame, get_number_label(snapshot_result),
                        (10, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            if now - result_start > RESULT_SECS:
                state = STATE_IDLE
                recent_readings = []

        cv2.imshow('Hand Cricket — Gesture Debug', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' ') and state == STATE_IDLE:
            state = STATE_COUNTDOWN
            countdown_start = time.time()
            recent_readings = []
            print("Countdown! Hold your sign.")

cap.release()
cv2.destroyAllWindows()
print("Done!")
