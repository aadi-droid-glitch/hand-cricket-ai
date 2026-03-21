"""
test_camera.py
--------------
Camera + MediaPipe test for mediapipe 0.10.30+
Run with: python test_camera.py
Press Q to quit.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from mediapipe.tasks.python.core import base_options as base_options_module
import time
import urllib.request
import os

# ── Download model if not present ────────────────────────────────────────
MODEL_PATH = "hand_landmarker.task"
if not os.path.exists(MODEL_PATH):
    print("Downloading hand landmark model (~25MB)...")
    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    urllib.request.urlretrieve(url, MODEL_PATH)
    print("Downloaded!")

# ── Setup ─────────────────────────────────────────────────────────────────
options = HandLandmarkerOptions(
    base_options=base_options_module.BaseOptions(model_asset_path=MODEL_PATH),
    num_hands=1,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.5,
    running_mode=vision.RunningMode.IMAGE,
)

print("Opening camera... press Q to quit.")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

prev_time = 0

with HandLandmarker.create_from_options(options) as detector:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame  = cv2.flip(frame, 1)
        rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = detector.detect(mp_img)

        h, w = frame.shape[:2]

        if result.hand_landmarks:
            # Draw dots manually — no framework dependency
            for hand in result.hand_landmarks:
                for lm in hand:
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (cx, cy), 5, (0, 255, 136), -1)

            cv2.putText(frame, 'HAND DETECTED', (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 136), 2)
            print("Hand detected!     ", end='\r')
        else:
            cv2.putText(frame, 'Show your hand...', (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 80, 80), 2)
            print("No hand yet...     ", end='\r')

        # FPS
        curr_time = time.time()
        fps = int(1 / (curr_time - prev_time + 0.001))
        prev_time = curr_time
        cv2.putText(frame, f'FPS: {fps}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 136), 2)

        cv2.imshow('Hand Cricket AI — Camera Test', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
print("\nDone! If green dots appeared on your hand — we are ready!")
