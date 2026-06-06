"""
Gambling Addiction Analyzer
Analysis of behavioral patterns associated with gambling addiction.

5 key parameters:
1. Blink Rate — blink frequency (trance / panic)
2. Mouth Tension — mouth tension (waiting for result)
3. Head Velocity — head movement speed (impulsiveness / tilt)
4. Eye Fixation — gaze fixation at center (loss of reality)
5. Self-Touching — face covering with hands (realization of loss)
"""

import numpy as np
from collections import deque
import time


class GamblingAnalyzer:
    """Analyzer of gambling addiction signs based on facial landmarks."""

    def __init__(self, fps=7.0):
        """
        Args:
            fps: Expected frame rate of input data
        """
        self.fps = fps

        # ===== Blink Rate =====
        # Storage of blink times for rate calculation
        self._blink_times = deque(maxlen=200)
        self._last_blink_count = 0
        self._blink_rate_per_min = 0.0  # normal: 15-20/min

        # ===== Mouth Tension =====
        # Buffer of distances between lip corners (normalized)
        self._mouth_width_history = deque(maxlen=60)
        self._mouth_tension_score = 0.0  # 0-1

        # ===== Head Velocity =====
        # Face center positions for velocity calculation
        self._face_center_history = deque(maxlen=30)
        self._face_center_times = deque(maxlen=30)
        self._head_velocity = 0.0  # px/sec (normalized)
        self._head_velocity_score = 0.0  # 0-1

        # ===== Eye Fixation =====
        # Tracking gaze direction (how fixed the gaze is at center)
        self._gaze_positions = deque(maxlen=90)  # ~13 sec at 7fps
        self._eye_fixation_score = 0.0  # 0-1 (1 = full fixation)

        # ===== Self-Touching =====
        # Hand on face detection (via YOLO person + reduction of visible face area)
        self._face_area_history = deque(maxlen=30)
        self._self_touch_score = 0.0  # 0-1
        self._face_visibility_history = deque(maxlen=30)

        # ===== Overall addiction score =====
        self._addiction_risk_score = 0.0  # 0-1
        self._analysis_count = 0

        # ===== Risk zones =====
        self._zone_history = deque(maxlen=300)  # ~42 sec of history

    def analyze(self, landmarks_68, face_bbox, frame_shape,
                blink_count=0, ear_value=0.3, yolo_persons=None):
        """
        Main frame analysis method.

        Args:
            landmarks_68: numpy array (68, 2) — 68 facial LBF landmarks
            face_bbox: (x, y, w, h) — face bounding box
            frame_shape: (height, width) of the frame
            blink_count: current blink counter from _detect_blink_and_eyes
            ear_value: current EAR value
            yolo_persons: list of YOLO detections [{'bbox': [x1,y1,x2,y2], ...}]

        Returns:
            dict: analysis results
        """
        self._analysis_count += 1
        now = time.time()
        h_frame, w_frame = frame_shape[:2]

        if landmarks_68 is None or face_bbox is None:
            return self._build_result()

        pts = landmarks_68
        fx, fy, fw, fh = face_bbox

        # Normalization by distance between outer eye corners
        outer_eye_dist = np.linalg.norm(pts[36] - pts[45])
        if outer_eye_dist < 1e-6:
            outer_eye_dist = 1.0
        D = outer_eye_dist

        # ===== 1. BLINK RATE =====
        self._update_blink_rate(blink_count, now)

        # ===== 2. MOUTH TENSION =====
        self._update_mouth_tension(pts, D)

        # ===== 3. HEAD VELOCITY =====
        face_cx = fx + fw / 2.0
        face_cy = fy + fh / 2.0
        self._update_head_velocity(face_cx, face_cy, w_frame, now)

        # ===== 4. EYE FIXATION =====
        self._update_eye_fixation(pts, w_frame, h_frame)

        # ===== 5. SELF-TOUCHING =====
        self._update_self_touching(face_bbox, yolo_persons, w_frame, h_frame)

        # ===== OVERALL RISK =====
        self._calculate_addiction_risk()

        return self._build_result()

    # ----------------------------------------------------------------
    # 1. BLINK RATE
    # ----------------------------------------------------------------
    def _update_blink_rate(self, current_blink_count, now):
        """
        Blink Rate: blink frequency.
        - Low (<10/min): trance, hyperfocus on screen → sign of addiction
        - Normal (15-20/min): OK
        - High (>25/min): panic, fatigue, tilt
        """
        # Detect new blinks
        new_blinks = current_blink_count - self._last_blink_count
        if new_blinks > 0:
            for _ in range(new_blinks):
                self._blink_times.append(now)
        self._last_blink_count = current_blink_count

        # Calculate frequency over the last 60 seconds
        window = 60.0  # seconds
        recent = [t for t in self._blink_times if now - t < window]
        if len(recent) >= 2:
            elapsed = now - recent[0]
            if elapsed > 5.0:  # minimum 5 seconds for stability
                self._blink_rate_per_min = len(recent) / elapsed * 60.0
            else:
                self._blink_rate_per_min = 0.0
        else:
            self._blink_rate_per_min = 0.0

    def get_blink_rate_score(self):
        """
        Blink Rate Score: 0-1 (1 = alarming).
        Low (<10) = trance (bad). Normal (15-20) = OK. High (>25) = panic (bad).
        """
        rate = self._blink_rate_per_min
        if rate < 1.0:
            return 0.0  # insufficient data
        if rate < 8:
            # Very low — trance/hyperfocus
            return min(1.0, (8 - rate) / 8.0 * 0.9 + 0.1)
        elif rate <= 22:
            # Normal zone
            return 0.0
        else:
            # High — panic/fatigue
            return min(1.0, (rate - 22) / 20.0)

    # ----------------------------------------------------------------
    # 2. MOUTH TENSION
    # ----------------------------------------------------------------
    def _update_mouth_tension(self, pts, D):
        """
        Mouth Tension: mouth strain.
        Distance between lip corners (pts[48] and pts[54]) normalized by D.
        Under tension lips compress → mouth_width decreases.
        Also: vertical lip compression (pts[51]-pts[57]).
        """
        mouth_w = np.linalg.norm(pts[48] - pts[54]) / D
        mouth_h = np.linalg.norm(pts[51] - pts[57]) / D

        # Tension = narrow + compressed mouth (not a smile)
        # Normal mouth: ~0.58-0.65 width, ~0.08-0.12 height
        # Tense: width < 0.55, height < 0.06
        width_tension = max(0.0, (0.58 - mouth_w) / 0.15)  # 0 at 0.58, 1 at 0.43
        height_tension = max(0.0, (0.07 - mouth_h) / 0.05)  # compressed lips

        tension = min(1.0, (width_tension * 0.6 + height_tension * 0.4))
        self._mouth_width_history.append(tension)

        # Window averaging
        if len(self._mouth_width_history) >= 3:
            self._mouth_tension_score = float(np.mean(list(self._mouth_width_history)[-15:]))
        else:
            self._mouth_tension_score = tension

    # ----------------------------------------------------------------
    # 3. HEAD VELOCITY
    # ----------------------------------------------------------------
    def _update_head_velocity(self, cx, cy, frame_width, now):
        """
        Head Velocity: head movement speed.
        Sharp movements = impulsiveness, tilt.
        Normalized by frame width.
        """
        self._face_center_history.append((cx, cy))
        self._face_center_times.append(now)

        if len(self._face_center_history) >= 3:
            positions = list(self._face_center_history)
            times = list(self._face_center_times)

            # Instantaneous velocity (last 3 frames)
            velocities = []
            for i in range(1, min(len(positions), 5)):
                dx = positions[-1][0] - positions[-i-1][0]
                dy = positions[-1][1] - positions[-i-1][1]
                dt = times[-1] - times[-i-1]
                if dt > 0.01:
                    speed = np.sqrt(dx**2 + dy**2) / dt / frame_width  # normalized
                    velocities.append(speed)

            if velocities:
                self._head_velocity = float(np.max(velocities))
            else:
                self._head_velocity = 0.0

        # Score: smooth scale
        # Normal movement: <0.1/sec (normalized)
        # Impulsive: >0.3/sec
        v = self._head_velocity
        if v < 0.08:
            self._head_velocity_score = 0.0
        elif v < 0.3:
            self._head_velocity_score = (v - 0.08) / 0.22 * 0.5
        else:
            self._head_velocity_score = min(1.0, 0.5 + (v - 0.3) / 0.4 * 0.5)

    # ----------------------------------------------------------------
    # 4. EYE FIXATION
    # ----------------------------------------------------------------
    def _update_eye_fixation(self, pts, w_frame, h_frame):
        """
        Eye Fixation: how fixed the gaze is at one point.
        Using average pupil position (iris landmarks approximately).
        For 68 LBF landmarks — eye center as approximation.
        High fixation = loss of reality (hyperfocus on screen).
        """
        # Right eye center: mean of pts[36:42]
        right_eye_center = np.mean(pts[36:42], axis=0)
        # Left eye center: mean of pts[42:48]
        left_eye_center = np.mean(pts[42:48], axis=0)
        # Average gaze
        gaze_center = (right_eye_center + left_eye_center) / 2.0

        # Normalize by frame size
        gaze_norm = (gaze_center[0] / w_frame, gaze_center[1] / h_frame)
        self._gaze_positions.append(gaze_norm)

        if len(self._gaze_positions) >= 10:
            positions = np.array(list(self._gaze_positions))
            # Standard deviation of gaze positions
            std_x = np.std(positions[:, 0])
            std_y = np.std(positions[:, 1])
            gaze_spread = np.sqrt(std_x**2 + std_y**2)

            # Less spread — higher fixation
            # Normal spread: >0.03 (eyes are moving)
            # Fixation: <0.01 (gaze is frozen)
            if gaze_spread < 0.005:
                self._eye_fixation_score = 1.0
            elif gaze_spread < 0.025:
                self._eye_fixation_score = max(0.0, (0.025 - gaze_spread) / 0.020)
            else:
                self._eye_fixation_score = 0.0
        else:
            self._eye_fixation_score = 0.0

    # ----------------------------------------------------------------
    # 5. SELF-TOUCHING
    # ----------------------------------------------------------------
    def _update_self_touching(self, face_bbox, yolo_persons, w_frame, h_frame):
        """
        Self-Touching: face occlusion by hands.
        Detected via:
        - Sharp decrease in visible face area (hand covers part)
        - Appearance of YOLO hands/objects over the face

        Main method: if face area sharply decreases or
        landmarks lose stability — likely a hand in front of the face.
        """
        fx, fy, fw, fh = face_bbox
        face_area = fw * fh
        frame_area = w_frame * h_frame

        # Normalized face area
        face_area_norm = face_area / max(frame_area, 1)
        self._face_area_history.append(face_area_norm)

        if len(self._face_area_history) >= 5:
            areas = list(self._face_area_history)
            # Baseline area (median over history)
            baseline = np.median(areas)
            current = areas[-1]

            if baseline > 0.005:
                # Sharp area decrease = something is occluding the face
                drop_ratio = 1.0 - (current / baseline)
                if drop_ratio > 0.15:
                    # Area dropped by >15% — likely hand on face
                    self._self_touch_score = min(1.0, drop_ratio / 0.4)
                else:
                    # Smooth decay
                    self._self_touch_score = max(0.0, self._self_touch_score * 0.85)
            else:
                self._self_touch_score = 0.0

            # Additionally: sharp area fluctuations (hand is moving)
            if len(areas) >= 10:
                recent_std = np.std(areas[-10:])
                if recent_std > baseline * 0.1:
                    self._self_touch_score = min(1.0,
                        self._self_touch_score + recent_std / baseline * 0.3)
        else:
            self._self_touch_score = 0.0

    # ----------------------------------------------------------------
    # OVERALL ADDICTION RISK
    # ----------------------------------------------------------------
    def _calculate_addiction_risk(self):
        """
        Combining 5 parameters into an overall addiction risk score.
        Weights are tuned by significance for gambling addiction.
        """
        blink_score = self.get_blink_rate_score()

        weights = {
            'blink_rate': 0.15,       # Trance / panic
            'mouth_tension': 0.20,    # Tension — waiting for result
            'head_velocity': 0.20,    # Impulsiveness / tilt
            'eye_fixation': 0.25,     # Loss of reality — most important
            'self_touching': 0.20,    # Realization of loss
        }

        risk = (
            blink_score * weights['blink_rate'] +
            self._mouth_tension_score * weights['mouth_tension'] +
            self._head_velocity_score * weights['head_velocity'] +
            self._eye_fixation_score * weights['eye_fixation'] +
            self._self_touch_score * weights['self_touching']
        )

        self._addiction_risk_score = min(1.0, max(0.0, risk))
        self._zone_history.append(self._addiction_risk_score)

    def get_risk_zone(self):
        """
        Determines the risk zone.

        Returns:
            str: 'normal', 'attention', 'warning', 'danger'
        """
        score = self._addiction_risk_score
        if score < 0.2:
            return 'normal'
        elif score < 0.45:
            return 'attention'
        elif score < 0.7:
            return 'warning'
        else:
            return 'danger'

    def get_recommendation(self):
        """Recommendation based on current state."""
        zone = self.get_risk_zone()
        blink = self.get_blink_rate_score()

        if zone == 'normal':
            return '✅ State is normal'
        elif zone == 'attention':
            if self._eye_fixation_score > 0.4:
                return '👁 You have been staring at one point for too long. Look away.'
            if self._mouth_tension_score > 0.4:
                return '😬 Mouth tension. Relax your jaw, take a breath.'
            return '⚠️ Pay attention to your state.'
        elif zone == 'warning':
            if self._head_velocity_score > 0.4:
                return '🔄 Impulsive movements. We recommend a pause!'
            if blink > 0.5:
                return '👀 Blinking is disrupted. You are in a trance or overexcited.'
            return '⚠️ Elevated risk. Take a break.'
        else:
            if self._self_touch_score > 0.4:
                return '🛑 You are covering your face. Stop and rest!'
            return '🛑 HIGH RISK! Take a break immediately!'

    def _build_result(self):
        """Builds the result dictionary."""
        blink_score = self.get_blink_rate_score()
        zone = self.get_risk_zone()

        return {
            'gambling_risk': round(self._addiction_risk_score, 3),
            'risk_zone': zone,
            'recommendation': self.get_recommendation(),

            # 5 parameters
            'blink_rate': {
                'blinks_per_min': round(self._blink_rate_per_min, 1),
                'score': round(blink_score, 3),
                'status': 'trance' if self._blink_rate_per_min < 10 and blink_score > 0.3
                         else 'panic' if self._blink_rate_per_min > 25
                         else 'normal'
            },
            'mouth_tension': {
                'score': round(self._mouth_tension_score, 3),
                'status': 'tension' if self._mouth_tension_score > 0.4
                         else 'normal'
            },
            'head_velocity': {
                'velocity': round(self._head_velocity, 4),
                'score': round(self._head_velocity_score, 3),
                'status': 'impulsiveness' if self._head_velocity_score > 0.4
                         else 'normal'
            },
            'eye_fixation': {
                'score': round(self._eye_fixation_score, 3),
                'status': 'hyperfocus' if self._eye_fixation_score > 0.5
                         else 'fixation' if self._eye_fixation_score > 0.25
                         else 'normal'
            },
            'self_touching': {
                'score': round(self._self_touch_score, 3),
                'status': 'detected' if self._self_touch_score > 0.3
                         else 'none'
            },

            'analysis_count': self._analysis_count,
        }

    def get_summary(self):
        """Final session summary."""
        if len(self._zone_history) == 0:
            return {'status': 'no_data'}

        history = list(self._zone_history)
        return {
            'total_analyses': self._analysis_count,
            'average_risk': round(float(np.mean(history)), 3),
            'max_risk': round(float(np.max(history)), 3),
            'time_in_danger': round(sum(1 for x in history if x >= 0.7) / len(history) * 100, 1),
            'time_in_warning': round(sum(1 for x in history if 0.45 <= x < 0.7) / len(history) * 100, 1),
            'time_normal': round(sum(1 for x in history if x < 0.2) / len(history) * 100, 1),
        }
