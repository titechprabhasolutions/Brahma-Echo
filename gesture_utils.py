# gesture_utils.py
"""
Hand gesture recognition and classification utility for Brahma AI.

Recognizes:
- Open Palm (✋) -> Play / Pause
- Swipe Right (👉) -> Next Track / Next Slide
- Swipe Left (👈) -> Previous Track / Previous Slide
- Thumbs Up (👍) -> Volume Up
- Thumbs Down (👎) -> Volume Down
- Peace Sign (✌️) -> Instant Screenshot
- Pinch (🤏) -> Mouse Click
"""

import math
import time
from typing import Iterable, Optional


class GestureTracker:
    def __init__(self):
        self.prev_pinch = False
        self.last_palm_time = 0.0
        self.last_peace_time = 0.0
        self.last_swipe_time = 0.0
        self.last_volume_time = 0.0
        self.palm_held_start = 0.0
        self.pos_history: list[tuple[float, float, float]] = []  # (x, y, timestamp)


def estimate_gesture_state(
    landmarks: Optional[Iterable[tuple[float, float, float]]],
    screen_size: tuple[int, int] | bool | None = None,
    prev_pinch: bool = False,
    tracker: Optional[GestureTracker] = None,
) -> dict:
    """Translate hand landmarks into gesture state and high-level Air Actions."""
    if isinstance(screen_size, bool):
        prev_pinch = screen_size

    if not landmarks or len(landmarks) < 21:
        if tracker:
            tracker.pos_history.clear()
            tracker.palm_held_start = 0.0
        return {
            "hand_detected": False,
            "cursor": None,
            "pinch": False,
            "pinch_triggered": False,
            "gesture_name": "None",
            "action": None,
        }

    now = time.monotonic()
    wrist = landmarks[0]
    thumb_tip = landmarks[4]
    thumb_ip = landmarks[3]
    thumb_mcp = landmarks[2]

    index_tip = landmarks[8]
    index_pip = landmarks[6]
    index_mcp = landmarks[5]

    middle_tip = landmarks[12]
    middle_pip = landmarks[10]
    middle_mcp = landmarks[9]

    ring_tip = landmarks[16]
    ring_pip = landmarks[14]

    pinky_tip = landmarks[20]
    pinky_pip = landmarks[18]

    # Finger open/closed state
    index_open = index_tip[1] < index_pip[1]
    middle_open = middle_tip[1] < middle_pip[1]
    ring_open = ring_tip[1] < ring_pip[1]
    pinky_open = pinky_tip[1] < pinky_pip[1]

    # Distance measurements
    palm_scale = max(0.01, math.hypot(middle_mcp[0] - wrist[0], middle_mcp[1] - wrist[1]))
    thumb_open = math.hypot(thumb_tip[0] - wrist[0], thumb_tip[1] - wrist[1]) > (palm_scale * 0.9)

    # Pinch detection (Thumb tip to Index tip)
    pinch_dist = math.hypot(thumb_tip[0] - index_tip[0], thumb_tip[1] - index_tip[1])
    pinch = pinch_dist < (palm_scale * 0.35) or pinch_dist < 0.055

    # Cursor position (index fingertip normalized 0..1)
    cursor = (float(index_tip[0]), float(index_tip[1]))

    # Palm center position for swipe tracking
    palm_center_x = float(middle_mcp[0])
    palm_center_y = float(middle_mcp[1])

    gesture_name = "Open Hand"
    action = None

    # Track velocity for swipe gestures (👉 / 👈)
    swipe_action = None
    if tracker is not None:
        tracker.pos_history.append((palm_center_x, palm_center_y, now))
        # Keep last 0.35s
        tracker.pos_history = [p for p in tracker.pos_history if now - p[2] <= 0.35]

        if len(tracker.pos_history) >= 4 and (now - tracker.last_swipe_time) > 0.75:
            start_x = tracker.pos_history[0][0]
            end_x = tracker.pos_history[-1][0]
            dt = tracker.pos_history[-1][2] - tracker.pos_history[0][2]
            dx = end_x - start_x

            # Fast horizontal movement
            if dt > 0.04 and abs(dx) > 0.18:
                if dx > 0.18:
                    swipe_action = "swipe_right"
                    gesture_name = "Swipe Right 👉"
                    tracker.last_swipe_time = now
                elif dx < -0.18:
                    swipe_action = "swipe_left"
                    gesture_name = "Swipe Left 👈"
                    tracker.last_swipe_time = now

    if swipe_action:
        action = swipe_action

    elif pinch:
        gesture_name = "Pinch"

    # ✌️ Peace Sign (Index + Middle open, Ring + Pinky closed) -> Screenshot
    elif index_open and middle_open and not ring_open and not pinky_open:
        gesture_name = "Peace ✌️"
        if tracker is not None:
            if now - tracker.last_peace_time > 2.0:
                action = "screenshot"
                tracker.last_peace_time = now
        else:
            action = "screenshot"

    # 👍 Thumbs Up (All 4 fingers closed, thumb pointing up) -> Volume Up
    elif not index_open and not middle_open and not ring_open and not pinky_open and (thumb_tip[1] < thumb_ip[1] < thumb_mcp[1]):
        gesture_name = "Thumbs Up 👍"
        if tracker is not None:
            if now - tracker.last_volume_time > 0.14:
                action = "volume_up"
                tracker.last_volume_time = now
        else:
            action = "volume_up"

    # 👎 Thumbs Down (All 4 fingers closed, thumb pointing down) -> Volume Down
    elif not index_open and not middle_open and not ring_open and not pinky_open and (thumb_tip[1] > thumb_ip[1] > thumb_mcp[1]):
        gesture_name = "Thumbs Down 👎"
        if tracker is not None:
            if now - tracker.last_volume_time > 0.14:
                action = "volume_down"
                tracker.last_volume_time = now
        else:
            action = "volume_down"

    # ✋ Open Palm (All 5 fingers extended) -> Play / Pause
    elif thumb_open and index_open and middle_open and ring_open and pinky_open:
        gesture_name = "Open Palm ✋"
        if tracker is not None:
            if tracker.palm_held_start == 0.0:
                tracker.palm_held_start = now
            elif (now - tracker.palm_held_start) >= 0.45 and (now - tracker.last_palm_time) > 1.4:
                action = "play_pause"
                tracker.last_palm_time = now
        else:
            action = "play_pause"
    else:
        if tracker is not None:
            tracker.palm_held_start = 0.0
        if index_open:
            gesture_name = "Pointer"

    return {
        "hand_detected": True,
        "cursor": cursor,
        "pinch": pinch,
        "pinch_triggered": bool(pinch and not prev_pinch),
        "gesture_name": gesture_name,
        "action": action,
    }
