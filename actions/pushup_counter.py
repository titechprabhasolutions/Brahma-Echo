"""
JARVIS plugin — Pushup Counter (webcam vision).

Say "Jarvis, count my pushups" (any language) — the HUD switches to the
live camera, a 5-second countdown lets you get into position, then JARVIS
counts your reps live on screen and finally delivers the result with
playful, teasing motivational commentary in your language.

Detection (two-tier):
  • If `mediapipe` is installed (pip install mediapipe): elbow-angle
    tracking — accurate from front or side view.
  • Otherwise: face-motion tracking with OpenCV only (zero extra
    dependencies) — place the camera on the floor in front of you so your
    head moves toward/away from it with each rep.

Session ends automatically: target reached, ~20 s without a rep, or the
3-minute safety cap. Just stand up when you're done.

Sessions are saved to memory/long_term.json ("pushup_sessions") so future
versions can track progress over time.
"""

import json
import time
from datetime import date
from pathlib import Path

import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent

PLUGIN = {
    "name": "pushup_counter",
    "description": (
        "Counts the user's pushups live through the WEBCAM. Use whenever the "
        "user says they are about to do pushups and wants them counted — e.g. "
        "'şınav çekeceğim say', 'count my pushups', 'pushup challenge'. "
        "If the user mentions a goal ('20 şınav çekeceğim'), pass it as "
        "'target'. The tool runs the WHOLE workout and only returns when the "
        "session ends (this can take a few minutes) — do not call other tools "
        "meanwhile. When the result comes back, deliver it in the user's "
        "language with playful, lightly TEASING motivational commentary "
        "(e.g. for 10 reps: congratulate them for being 'a perfectly average "
        "human'). Never use screen_process for pushup counting."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "The user's exact request, verbatim, in their own language.",
            },
            "target": {
                "type": "NUMBER",
                "description": "Rep goal if the user stated one (e.g. 20). Omit otherwise.",
            },
        },
        "required": ["query"],
    },
}

_COUNTDOWN_SECONDS   = 5
_MAX_SESSION_SECONDS = 180
_IDLE_END_SECONDS    = 20    # end after this long without a rep (once started)
_IDLE_ABORT_SECONDS  = 40    # abort if NO rep ever happens
_FPS                 = 20
_CYAN   = (255, 190, 40)     # JARVIS cyan-blue (BGR)
_BRIGHT = (255, 235, 130)


# ── config / camera (same pattern as calorie_counter) ───────────────────────

def _config() -> dict:
    try:
        return json.loads(
            (BASE_DIR / "config" / "api_keys.json").read_text(encoding="utf-8")
        )
    except Exception:
        return {}


def _open_camera():
    import platform
    try:
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
    except AttributeError:
        backend = 0
    cap = cv2.VideoCapture(int(_config().get("camera_index", 0)), backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    for _ in range(6):
        cap.read()
    return cap


def _emit_frame(frame_sig, frame: np.ndarray) -> None:
    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    if ok:
        frame_sig.emit(buf.tobytes())


# ── rep counting state machine ───────────────────────────────────────────────

class _RepCounter:
    """Counts full down→up cycles of a raw 'down-ness' signal (bigger =
    lower). Tracks the signal's own min/max range (with slow decay) so it
    self-calibrates to any camera distance or body size."""

    def __init__(self, min_rel_amplitude: float = 0.18):
        self._min_rel = min_rel_amplitude
        self.lo = None
        self.hi = None
        self.state = "up"
        self.reps = 0

    def update(self, v: float) -> bool:
        if self.lo is None:
            self.lo = self.hi = float(v)
            return False
        # decay range toward the current value, then expand to include it
        self.lo = min(self.lo + (v - self.lo) * 0.002, v)
        self.hi = max(self.hi + (v - self.hi) * 0.002, v)
        rng = self.hi - self.lo
        if rng < max(abs(self.hi), 1e-6) * self._min_rel:
            return False   # not enough movement observed yet
        pos = (v - self.lo) / rng
        if self.state == "up" and pos > 0.70:
            self.state = "down"
        elif self.state == "down" and pos < 0.30:
            self.state = "up"
            self.reps += 1
            return True
        return False


# ── detectors: return a 'down-ness' signal (bigger = lower), or None ────────

def _make_pose_detector():
    """MediaPipe elbow-angle tracking. Returns fn(frame)->float|None,
    or None if mediapipe isn't installed."""
    try:
        import mediapipe as mp
        pose = mp.solutions.pose.Pose(model_complexity=0,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5)
        L = mp.solutions.pose.PoseLandmark
    except Exception:
        # mediapipe missing, or an incompatible version without the
        # legacy solutions API — face tracking takes over either way
        return None

    def _angle(a, b, c) -> float:
        ba = np.array([a.x - b.x, a.y - b.y])
        bc = np.array([c.x - b.x, c.y - b.y])
        cos = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
        return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))

    def _signal(frame: np.ndarray):
        res = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        lm = getattr(res, "pose_landmarks", None)
        if not lm:
            return None
        pts = lm.landmark
        best = None
        for s, e, w in ((L.LEFT_SHOULDER, L.LEFT_ELBOW, L.LEFT_WRIST),
                        (L.RIGHT_SHOULDER, L.RIGHT_ELBOW, L.RIGHT_WRIST)):
            vis = min(pts[s].visibility, pts[e].visibility, pts[w].visibility)
            if vis < 0.5:
                continue
            ang = _angle(pts[s], pts[e], pts[w])   # 180 = arm straight
            if best is None or vis > best[1]:
                best = (ang, vis)
        if best is None:
            return None
        # straight arm (170°) -> 0.0 (up) … bent arm (60°) -> 1.0 (down)
        return float(np.clip((170.0 - best[0]) / 110.0, 0.0, 1.0))

    return _signal


def _make_face_detector():
    """OpenCV-only fallback: face area grows as the user lowers toward a
    floor-placed camera. Returns fn(frame)->float|None."""
    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    def _signal(frame: np.ndarray):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
        faces = cascade.detectMultiScale(small, 1.15, 4, minSize=(30, 30))
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        return float(w * h)   # bigger face = closer = down

    return _signal


# ── on-frame overlay (ASCII/digits only — cv2.putText can't render more) ────

def _draw_overlay(frame, reps, target, state, flash_until, countdown=None):
    out = frame.copy()
    h, w = out.shape[:2]
    if countdown is not None:
        txt = str(countdown)
        size = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, 6.0, 8)[0]
        cv2.putText(out, txt, ((w - size[0]) // 2, (h + size[1]) // 2),
                    cv2.FONT_HERSHEY_DUPLEX, 6.0, _BRIGHT, 8, cv2.LINE_AA)
        return out
    big = time.time() < flash_until
    scale = 4.0 if big else 2.8
    color = _BRIGHT if big else _CYAN
    label = f"{reps}" + (f"/{int(target)}" if target else "")
    cv2.putText(out, label, (24, 90), cv2.FONT_HERSHEY_DUPLEX,
                scale, color, 6 if big else 4, cv2.LINE_AA)
    # state hint bar at the bottom: fills while DOWN
    bar_w = int(w * (0.9 if state == "down" else 0.15))
    cv2.rectangle(out, (0, h - 10), (bar_w, h), _CYAN, -1)
    return out


# ── persistence (memory/long_term.json, additive — other keys preserved) ────

def _record_session(reps: int, seconds: float) -> int:
    """Append session, return today's total reps. Never raises."""
    try:
        path = BASE_DIR / "memory" / "long_term.json"
        data = {}
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        sessions = data.get("pushup_sessions")
        if not isinstance(sessions, list):
            sessions = []
        today = date.today().isoformat()
        sessions.append({"date": today, "reps": reps, "seconds": round(seconds)})
        data["pushup_sessions"] = sessions[-100:]
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                        encoding="utf-8")
        return sum(s.get("reps", 0) for s in sessions if s.get("date") == today)
    except Exception:
        return reps


# ── entry point ──────────────────────────────────────────────────────────────

def run(parameters: dict, player=None, session_memory=None) -> str:
    try:
        target = int(parameters.get("target") or 0)
    except Exception:
        target = 0

    def _log(msg: str) -> None:
        if player:
            try:
                player.write_log(msg)
            except Exception:
                pass

    win        = getattr(player, "_win", None) if player else None
    frame_sig  = getattr(win, "_cam_frame_sig", None)
    stream_sig = getattr(win, "_cam_stream_sig", None)

    detector = _make_pose_detector()
    mode = "elbow tracking (mediapipe)"
    if detector is None:
        detector = _make_face_detector()
        mode = "face-motion tracking (place camera on the floor in front of you)"

    cap = _open_camera()
    if cap is None:
        return ("I couldn't access the camera — it may be in use by another "
                "feature or application.")

    counter = _RepCounter()
    flash_until = 0.0
    view_open = False
    started = time.time()
    last_rep_time = started
    end_reason = "finished"
    try:
        if stream_sig:
            stream_sig.emit(True)
            view_open = True
        _log(f"JARVIS: Pushup session started — {mode}.")

        # Phase 1 — countdown so the user can get into position
        t0 = time.time()
        while time.time() - t0 < _COUNTDOWN_SECONDS:
            ok, frm = cap.read()
            if ok and frm is not None and frame_sig:
                remaining = _COUNTDOWN_SECONDS - int(time.time() - t0)
                _emit_frame(frame_sig,
                            _draw_overlay(frm, 0, target, "up", 0,
                                          countdown=max(1, remaining)))
            time.sleep(1.0 / _FPS)

        # Phase 2 — count
        started = time.time()
        last_rep_time = started
        while True:
            now = time.time()
            if now - started > _MAX_SESSION_SECONDS:
                end_reason = "time limit"
                break
            idle = now - last_rep_time
            if counter.reps > 0 and idle > _IDLE_END_SECONDS:
                end_reason = "user stopped"
                break
            if counter.reps == 0 and idle > _IDLE_ABORT_SECONDS:
                end_reason = "no pushups detected"
                break
            if target and counter.reps >= target:
                end_reason = "target reached"
                break

            ok, frm = cap.read()
            if not ok or frm is None:
                time.sleep(1.0 / _FPS)
                continue
            sig = detector(frm)
            if sig is not None and counter.update(sig):
                last_rep_time = time.time()
                flash_until = last_rep_time + 0.6
                if counter.reps % 10 == 0 or (target and counter.reps == target):
                    _log(f"JARVIS: Pushup {counter.reps} 💪")
            if frame_sig:
                _emit_frame(frame_sig,
                            _draw_overlay(frm, counter.reps, target,
                                          counter.state, flash_until))
            time.sleep(1.0 / _FPS)
    finally:
        try:
            cap.release()
        except Exception:
            pass
        if view_open:
            stream_sig.emit(False)

    reps = counter.reps
    seconds = max(1.0, time.time() - started)

    if reps == 0:
        return ("The session ended without a single detected pushup "
                f"({end_reason}). Tell the user — with gentle teasing — that "
                "zero pushups were counted, and remind them the camera must "
                "clearly see them (or their face, in face-tracking mode).")

    today_total = _record_session(reps, seconds)
    pace = reps / (seconds / 60.0)

    if player:
        try:
            player.show_content(
                "💪 PUSHUP SESSION",
                (f"Reps: {reps}" + (f" / {target}" if target else "") + "\n"
                 f"Duration: {int(seconds)} s\n"
                 f"Pace: {pace:.1f} reps/min\n"
                 f"Today's total: {today_total}\n"
                 f"Ended: {end_reason}\n"
                 f"Mode: {mode}"),
            )
        except Exception:
            pass

    return (f"Pushup session finished ({end_reason}). Reps: {reps}"
            + (f" of the {target} targeted" if target else "")
            + f". Duration: {int(seconds)} seconds ({pace:.1f} reps/min)."
            f" Today's total: {today_total}. Deliver this to the user in "
            "their language with playful, lightly teasing motivational "
            "commentary about the number.")
