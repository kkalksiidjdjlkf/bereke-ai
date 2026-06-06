"""
Health Symptom Analyzer — камера арқылы симптомдарды анықтау
Based on DOC.FAI.ME medical reference document.

Detects via camera:
1. Skin changes: pallor (бозару), jaundice (сарғаю), cyanosis (көгеру),
   redness (қызару), rash (бөртпе), dryness (құрғақтық)
2. Pulse estimation via rPPG (remote photoplethysmography)
3. Respiratory rate from face/shoulder movement
4. Fever signs from facial redness patterns

DISCLAIMER: This is NOT a medical diagnostic tool.
All detections are estimates and require professional medical confirmation.
"""

import cv2
import numpy as np
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ===================== SKIN COLOR ANALYSIS =====================

class SkinColorAnalyzer:
    """Analyzes facial skin color in different color spaces to detect
    pallor, jaundice, cyanosis, and redness."""

    # Reference color ranges (in LAB color space for perceptual accuracy)
    # L: lightness (0-255), A: green-red (-128 to 127), B: blue-yellow (-128 to 127)

    def __init__(self):
        self.history = deque(maxlen=30)  # 30-frame smoothing
        self.baseline_lab = None
        self.baseline_samples = 0
        self.calibration_frames = 30  # frames to establish baseline

    def analyze_skin_region(self, face_crop_bgr: np.ndarray) -> Dict:
        """
        Analyze skin color from a face crop.

        Args:
            face_crop_bgr: BGR face image (OpenCV format)

        Returns:
            dict with scores for each skin condition (0.0 - 1.0)
        """
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            return self._empty_result()

        h, w = face_crop_bgr.shape[:2]
        if h < 20 or w < 20:
            return self._empty_result()

        # Extract skin-only pixels using HSV masking
        skin_mask = self._get_skin_mask(face_crop_bgr)
        skin_pixels_count = cv2.countNonZero(skin_mask)

        if skin_pixels_count < 100:
            return self._empty_result()

        # Convert to different color spaces for analysis
        lab_img = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2LAB)
        hsv_img = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2HSV)
        ycrcb_img = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2YCrCb)

        # Get mean values only for skin pixels
        lab_mean = cv2.mean(lab_img, mask=skin_mask)[:3]
        hsv_mean = cv2.mean(hsv_img, mask=skin_mask)[:3]
        ycrcb_mean = cv2.mean(ycrcb_img, mask=skin_mask)[:3]
        bgr_mean = cv2.mean(face_crop_bgr, mask=skin_mask)[:3]

        L, A, B_lab = lab_mean
        H, S, V = hsv_mean
        Y, Cr, Cb = ycrcb_mean
        B_bgr, G_bgr, R_bgr = bgr_mean

        # Update baseline during calibration
        if self.baseline_samples < self.calibration_frames:
            if self.baseline_lab is None:
                self.baseline_lab = np.array([L, A, B_lab])
            else:
                alpha = 1.0 / (self.baseline_samples + 1)
                self.baseline_lab = (1 - alpha) * self.baseline_lab + alpha * np.array([L, A, B_lab])
            self.baseline_samples += 1

        # ========== PALLOR (бозару / бледность) ==========
        # High Lightness + Low Saturation + Low redness (A channel)
        # Pale skin: high L, low A (less red), low Cr
        pallor_score = 0.0
        if L > 160:  # Very bright skin
            pallor_score += 0.3
        if S < 40:  # Very low saturation
            pallor_score += 0.3
        if A < 128:  # Green-shifted (less red than normal)
            pallor_score += min(0.4, (128 - A) / 60.0 * 0.4)
        if Cr < 135:  # Low red chrominance
            pallor_score += 0.2
        # Compare to baseline if available
        if self.baseline_lab is not None and self.baseline_samples >= self.calibration_frames:
            l_change = L - self.baseline_lab[0]
            a_change = self.baseline_lab[1] - A  # A dropping = paler
            if l_change > 15 and a_change > 5:
                pallor_score += 0.2
        pallor_score = min(1.0, max(0.0, pallor_score))

        # ========== JAUNDICE (сарғаю / желтуха) ==========
        # Yellow tint: high B channel in LAB, yellow hue in HSV
        jaundice_score = 0.0
        if B_lab > 145:  # Yellow-shifted in LAB B channel
            jaundice_score += min(0.5, (B_lab - 145) / 30.0 * 0.5)
        if 15 < H < 35 and S > 70:  # Yellow hue range with saturation
            jaundice_score += 0.3
        # Yellow = high R + high G + low B in BGR
        if R_bgr > 150 and G_bgr > 130 and B_bgr < 100:
            yellow_ratio = (R_bgr + G_bgr) / (2 * max(B_bgr, 1))
            if yellow_ratio > 2.0:
                jaundice_score += min(0.3, (yellow_ratio - 2.0) * 0.15)
        # Sclera analysis would need eye detection — we check overall face
        if self.baseline_lab is not None and self.baseline_samples >= self.calibration_frames:
            b_change = B_lab - self.baseline_lab[2]
            if b_change > 10:  # Sudden yellow shift
                jaundice_score += 0.2
        jaundice_score = min(1.0, max(0.0, jaundice_score))

        # ========== CYANOSIS (көгеру / цианоз) ==========
        # Blue tint: low B channel in LAB (toward blue), high blue in BGR
        cyanosis_score = 0.0
        if B_lab < 120:  # Blue-shifted in LAB
            cyanosis_score += min(0.4, (120 - B_lab) / 40.0 * 0.4)
        if B_bgr > R_bgr and B_bgr > G_bgr:  # Blue dominant
            cyanosis_score += 0.3
        if Cb > 128 + 15:  # Blue chrominance elevated
            cyanosis_score += min(0.3, (Cb - 143) / 30.0 * 0.3)
        # Low oxygen would show low saturation and blue tinge
        if V < 100 and S < 50:
            cyanosis_score += 0.2
        cyanosis_score = min(1.0, max(0.0, cyanosis_score))

        # ========== REDNESS / FEVER SIGN (қызару / покраснение) ==========
        # Increased redness: high A channel in LAB, high Cr
        redness_score = 0.0
        if A > 145:  # Red-shifted
            redness_score += min(0.4, (A - 145) / 25.0 * 0.4)
        if Cr > 160:  # High red chrominance
            redness_score += min(0.3, (Cr - 160) / 30.0 * 0.3)
        if R_bgr > 180 and R_bgr > G_bgr * 1.3:  # Red dominant
            redness_score += 0.3
        # Compare to baseline
        if self.baseline_lab is not None and self.baseline_samples >= self.calibration_frames:
            a_change = A - self.baseline_lab[1]
            if a_change > 8:  # Sudden redness increase
                redness_score += 0.2
        redness_score = min(1.0, max(0.0, redness_score))

        # ========== SKIN DRYNESS (құрғақтық) ==========
        # Detect via texture analysis — high-frequency content in grayscale
        gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
        # Apply Laplacian for texture detection
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        texture_var = laplacian.var()
        dryness_score = 0.0
        if texture_var > 500:  # High texture variance = rough/dry skin
            dryness_score += min(0.5, (texture_var - 500) / 2000.0 * 0.5)
        # Low saturation often accompanies dry skin
        if S < 50:
            dryness_score += 0.2
        # Uneven brightness
        local_std = gray.astype(float)
        blur = cv2.GaussianBlur(local_std, (15, 15), 0)
        diff = np.abs(local_std - blur)
        mean_diff = np.mean(diff[skin_mask > 0]) if skin_pixels_count > 0 else 0
        if mean_diff > 15:
            dryness_score += min(0.3, (mean_diff - 15) / 30.0 * 0.3)
        dryness_score = min(1.0, max(0.0, dryness_score))

        # ========== RASH DETECTION (бөртпе) ==========
        # Look for red spots/patches that differ from surrounding skin
        # STRICT: require very high color variance + absolute red intensity
        # to avoid false positives from lighting, glasses, webcam noise
        rash_score = 0.0
        if skin_pixels_count > 500:  # Need substantial skin area
            # Red channel deviation — only count if very high variance
            r_channel = face_crop_bgr[:, :, 2].astype(float)
            r_masked = r_channel[skin_mask > 0]
            r_mean = np.mean(r_masked)
            r_std = np.std(r_masked)
            # Very high std required (normal webcam noise: 15-35, real rash: 45+)
            if r_std > 45:
                rash_score += min(0.3, (r_std - 45) / 40.0 * 0.3)
            # Detect red spots: must be truly abnormal (>2.5 std) AND have high absolute red
            red_spots = ((r_channel > r_mean + 2.5 * r_std) & 
                         (r_channel > 180) &  # Absolute red threshold
                         (skin_mask > 0)).astype(np.uint8)
            spot_count = cv2.countNonZero(red_spots)
            spot_ratio = spot_count / max(skin_pixels_count, 1)
            if spot_ratio > 0.10:  # 10% of skin must be red spots (was 5%)
                rash_score += min(0.4, (spot_ratio - 0.10) * 3.0)
            # Color non-uniformity in A channel (LAB) — raise threshold
            a_channel = lab_img[:, :, 1].astype(float)
            a_masked = a_channel[skin_mask > 0]
            a_std = np.std(a_masked)
            if a_std > 18:  # Much higher threshold (was 10)
                rash_score += min(0.2, (a_std - 18) / 25.0 * 0.2)
        rash_score = min(1.0, max(0.0, rash_score))

        # ========== DETERMINE OVERALL SKIN HEALTH ==========
        scores = {
            'pallor': pallor_score,
            'jaundice': jaundice_score,
            'cyanosis': cyanosis_score,
            'redness': redness_score,
            'dryness': dryness_score,
            'rash': rash_score,
        }

        max_score = max(scores.values())
        if max_score > 0.6:
            overall = 'concerning'
        elif max_score > 0.3:
            overall = 'mild_concern'
        else:
            overall = 'normal'

        # Primary skin finding
        primary = max(scores, key=scores.get) if max_score > 0.2 else 'normal'

        # Alert level
        alert = 'none'
        if cyanosis_score > 0.5:
            alert = 'critical'
        elif max_score > 0.6:
            alert = 'warning'
        elif max_score > 0.3:
            alert = 'info'

        # Store in history for smoothing
        self.history.append(scores)

        # Smooth scores over history
        smoothed = {}
        for key in scores:
            vals = [h[key] for h in self.history]
            smoothed[key] = float(np.mean(vals))

        result = {
            'pallor_score': round(smoothed['pallor'], 3),
            'jaundice_score': round(smoothed['jaundice'], 3),
            'cyanosis_score': round(smoothed['cyanosis'], 3),
            'redness_score': round(smoothed['redness'], 3),
            'dryness_score': round(smoothed['dryness'], 3),
            'rash_score': round(smoothed['rash'], 3),
            'overall_skin_health': overall,
            'primary_finding': primary,
            'alert_level': alert,
            # Raw color values for debugging
            'lab_mean': [round(L, 1), round(A, 1), round(B_lab, 1)],
            'hsv_mean': [round(H, 1), round(S, 1), round(V, 1)],
        }

        return result

    def _get_skin_mask(self, bgr_img: np.ndarray) -> np.ndarray:
        """Create a binary mask of skin pixels using HSV + YCrCb dual thresholding."""
        hsv = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2HSV)
        ycrcb = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2YCrCb)

        # HSV skin range (broad to cover different skin tones)
        lower_hsv = np.array([0, 30, 60], dtype=np.uint8)
        upper_hsv = np.array([50, 255, 255], dtype=np.uint8)
        mask_hsv = cv2.inRange(hsv, lower_hsv, upper_hsv)

        # YCrCb skin range
        lower_ycrcb = np.array([0, 133, 77], dtype=np.uint8)
        upper_ycrcb = np.array([255, 173, 127], dtype=np.uint8)
        mask_ycrcb = cv2.inRange(ycrcb, lower_ycrcb, upper_ycrcb)

        # Combine both masks (AND for stricter skin detection)
        skin_mask = cv2.bitwise_and(mask_hsv, mask_ycrcb)

        # Clean up with morphology
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
        skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)

        return skin_mask

    def _empty_result(self) -> Dict:
        return {
            'pallor_score': 0.0, 'jaundice_score': 0.0, 'cyanosis_score': 0.0,
            'redness_score': 0.0, 'dryness_score': 0.0, 'rash_score': 0.0,
            'overall_skin_health': 'unknown', 'primary_finding': 'none',
            'alert_level': 'none', 'lab_mean': [0, 0, 0], 'hsv_mean': [0, 0, 0],
        }

    def reset(self):
        """Reset analyzer state."""
        self.history.clear()
        self.baseline_lab = None
        self.baseline_samples = 0


# ===================== rPPG HEART RATE ESTIMATOR =====================

class HeartRateEstimator:
    """
    Estimates heart rate from facial video using remote photoplethysmography (rPPG).
    Analyzes subtle color changes in facial skin caused by blood flow.
    """

    def __init__(self, fps: float = 30.0, window_seconds: float = 10.0):
        self.fps = fps
        self.window_size = int(fps * window_seconds)
        self.green_channel_history = deque(maxlen=self.window_size)
        self.heart_rate = 0.0
        self.confidence = 0.0
        self.signal_quality = 'poor'

    def process_frame(self, face_crop_bgr: np.ndarray, skin_mask: Optional[np.ndarray] = None) -> Dict:
        """
        Process a frame for heart rate estimation.

        Args:
            face_crop_bgr: BGR face crop
            skin_mask: optional skin mask

        Returns:
            dict with estimated_heart_rate and confidence
        """
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            return {'estimated_heart_rate': 0, 'heart_rate_confidence': 0.0,
                    'signal_quality': 'poor'}

        # Extract mean green channel value (green is most sensitive to blood volume changes)
        if skin_mask is not None and cv2.countNonZero(skin_mask) > 50:
            green_mean = cv2.mean(face_crop_bgr[:, :, 1], mask=skin_mask)[0]
        else:
            # Use forehead region (most stable for rPPG)
            h, w = face_crop_bgr.shape[:2]
            forehead = face_crop_bgr[int(h * 0.05):int(h * 0.35), int(w * 0.25):int(w * 0.75)]
            if forehead.size > 0:
                green_mean = np.mean(forehead[:, :, 1])
            else:
                green_mean = np.mean(face_crop_bgr[:, :, 1])

        self.green_channel_history.append(green_mean)

        # Need enough samples for analysis
        if len(self.green_channel_history) < self.fps * 3:
            return {'estimated_heart_rate': 0, 'heart_rate_confidence': 0.0,
                    'signal_quality': 'collecting'}

        # Convert to numpy and detrend
        signal = np.array(self.green_channel_history)
        signal = signal - np.mean(signal)

        # Bandpass filter for heart rate range (0.7 - 4.0 Hz = 42 - 240 bpm)
        # Simple moving average subtraction as high-pass + low-pass
        window = max(3, int(self.fps / 4))
        smooth = np.convolve(signal, np.ones(window) / window, mode='same')
        filtered = signal - smooth

        # FFT analysis
        n = len(filtered)
        fft_vals = np.fft.fft(filtered)
        fft_freqs = np.fft.fftfreq(n, d=1.0 / self.fps)

        # Only positive frequencies in heart rate range
        positive_mask = (fft_freqs > 0.7) & (fft_freqs < 3.5)  # 42-210 bpm
        positive_freqs = fft_freqs[positive_mask]
        positive_magnitude = np.abs(fft_vals[positive_mask])

        if len(positive_magnitude) == 0:
            return {'estimated_heart_rate': 0, 'heart_rate_confidence': 0.0,
                    'signal_quality': 'poor'}

        # Find dominant frequency
        peak_idx = np.argmax(positive_magnitude)
        peak_freq = positive_freqs[peak_idx]
        peak_magnitude = positive_magnitude[peak_idx]

        # Heart rate from dominant frequency
        self.heart_rate = peak_freq * 60.0  # Convert Hz to BPM

        # Confidence based on signal-to-noise ratio
        total_power = np.sum(positive_magnitude ** 2)
        peak_power = peak_magnitude ** 2
        snr = peak_power / max(total_power - peak_power, 1e-6)
        self.confidence = min(1.0, snr / 3.0)

        # Signal quality assessment
        if self.confidence > 0.5:
            self.signal_quality = 'good'
        elif self.confidence > 0.2:
            self.signal_quality = 'fair'
        else:
            self.signal_quality = 'poor'

        return {
            'estimated_heart_rate': round(self.heart_rate, 1),
            'heart_rate_confidence': round(self.confidence, 3),
            'signal_quality': self.signal_quality,
        }

    def get_pulse_category(self) -> Tuple[str, str]:
        """
        Categorize pulse based on DOC.FAI.ME thresholds.

        Returns:
            (category_code, description)
        """
        hr = self.heart_rate
        if self.confidence < 0.2:
            return ('UNKNOWN', 'Сигнал жеткіліксіз / Недостаточный сигнал')
        if hr < 40:
            return ('CRITICAL_PULSE_LOW', 'ЖЕДЕЛ! Пульс <40 / КРИТИЧЕСКИ! Пульс <40')
        elif hr < 60:
            return ('BRADYCARDIA', 'Брадикардия (<60 bpm)')
        elif hr <= 100:
            return ('NORMAL', 'Қалыпты / Нормальный (60-100 bpm)')
        elif hr <= 130:
            return ('TACHYCARDIA', 'Тахикардия (>100 bpm)')
        else:
            return ('CRITICAL_PULSE_HIGH', 'ЖЕДЕЛ! Пульс >130 / КРИТИЧЕСКИ! Пульс >130')

    def reset(self):
        self.green_channel_history.clear()
        self.heart_rate = 0.0
        self.confidence = 0.0


# ===================== RESPIRATORY RATE ESTIMATOR =====================

class RespiratoryRateEstimator:
    """
    Estimates respiratory rate from facial/shoulder movement in video.
    Tracks subtle vertical oscillations of the nose/chin area.
    """

    def __init__(self, fps: float = 30.0, window_seconds: float = 15.0):
        self.fps = fps
        self.window_size = int(fps * window_seconds)
        self.position_history = deque(maxlen=self.window_size)
        self.resp_rate = 0.0
        self.confidence = 0.0

    def process_frame(self, face_landmarks: Optional[np.ndarray],
                      nose_y: Optional[float] = None) -> Dict:
        """
        Process frame for respiratory rate estimation.

        Args:
            face_landmarks: facial landmarks array
            nose_y: Y-coordinate of nose tip (alternative to landmarks)

        Returns:
            dict with estimated respiratory rate
        """
        if nose_y is not None:
            self.position_history.append(nose_y)
        elif face_landmarks is not None and len(face_landmarks) > 33:
            # Use nose tip (landmark 33 in 68-point model)
            self.position_history.append(float(face_landmarks[33][1]))
        else:
            return {'estimated_resp_rate': 0, 'resp_rate_confidence': 0.0}

        if len(self.position_history) < self.fps * 5:
            return {'estimated_resp_rate': 0, 'resp_rate_confidence': 0.0,
                    'status': 'collecting'}

        # Analyze vertical oscillation
        signal = np.array(self.position_history)
        signal = signal - np.mean(signal)

        # FFT for breathing frequency (0.1 - 0.6 Hz = 6 - 36 bpm)
        n = len(signal)
        fft_vals = np.fft.fft(signal)
        fft_freqs = np.fft.fftfreq(n, d=1.0 / self.fps)

        mask = (fft_freqs > 0.1) & (fft_freqs < 0.6)
        freqs = fft_freqs[mask]
        magnitudes = np.abs(fft_vals[mask])

        if len(magnitudes) == 0:
            return {'estimated_resp_rate': 0, 'resp_rate_confidence': 0.0}

        peak_idx = np.argmax(magnitudes)
        peak_freq = freqs[peak_idx]
        peak_mag = magnitudes[peak_idx]

        self.resp_rate = peak_freq * 60.0

        total_power = np.sum(magnitudes ** 2)
        snr = peak_mag ** 2 / max(total_power - peak_mag ** 2, 1e-6)
        self.confidence = min(1.0, snr / 2.0)

        # Categorize breathing rate (DOC.FAI.ME thresholds)
        rate = self.resp_rate
        if rate < 12:
            status = 'slow'
        elif rate <= 20:
            status = 'normal'
        elif rate <= 25:
            status = 'elevated'
        else:
            status = 'fast'

        return {
            'estimated_resp_rate': round(self.resp_rate, 1),
            'resp_rate_confidence': round(self.confidence, 3),
            'breathing_status': status,
        }

    def get_breathing_category(self) -> Tuple[str, str]:
        """Categorize breathing based on DOC.FAI.ME."""
        rate = self.resp_rate
        if self.confidence < 0.2:
            return ('UNKNOWN', 'Insufficient data')
        if rate > 25:
            return ('FAST_BREATHING', f'Жылдам тыныс ({rate:.0f}/мин)')
        elif rate < 12:
            return ('IRREGULAR_BREATHING', f'Баяу тыныс ({rate:.0f}/мин)')
        else:
            return ('NORMAL', f'Қалыпты ({rate:.0f}/мин)')

    def reset(self):
        self.position_history.clear()
        self.resp_rate = 0.0
        self.confidence = 0.0


# ===================== MAIN HEALTH ANALYZER =====================

class HealthAnalyzer:
    """
    Main health analyzer that combines all detection modules.
    Uses camera to detect symptoms from DOC.FAI.ME document.
    """

    def __init__(self, fps: float = 30.0):
        self.skin_analyzer = SkinColorAnalyzer()
        self.heart_rate_estimator = HeartRateEstimator(fps=fps)
        self.resp_rate_estimator = RespiratoryRateEstimator(fps=fps)
        self.fps = fps

        # Alert history for persistent alerts
        self.alert_history = deque(maxlen=10)
        self.detected_symptoms = []

    def analyze_frame(self, frame_bgr: np.ndarray,
                      face_bbox: Optional[Tuple] = None,
                      face_landmarks: Optional[np.ndarray] = None) -> Dict:
        """
        Full health analysis on a single frame.

        Args:
            frame_bgr: full BGR frame from camera
            face_bbox: (x, y, w, h) face bounding box
            face_landmarks: 68-point facial landmarks array

        Returns:
            dict with all health analysis results
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'face_detected': False,
            'skin_analysis': self.skin_analyzer._empty_result(),
            'heart_rate': {'estimated_heart_rate': 0, 'heart_rate_confidence': 0.0},
            'respiratory': {'estimated_resp_rate': 0, 'resp_rate_confidence': 0.0},
            'detected_conditions': [],
            'alert_level': 'none',
            'emergency': False,
        }

        if frame_bgr is None or frame_bgr.size == 0:
            return result

        # Extract face crop
        face_crop = None
        if face_bbox is not None:
            x, y, w, h = face_bbox
            fh, fw = frame_bgr.shape[:2]
            # Add padding
            pad_x = int(w * 0.1)
            pad_y = int(h * 0.1)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(fw, x + w + pad_x)
            y2 = min(fh, y + h + pad_y)
            face_crop = frame_bgr[y1:y2, x1:x2]
            result['face_detected'] = True

        if face_crop is not None and face_crop.size > 0:
            # 1. Skin color analysis
            skin_result = self.skin_analyzer.analyze_skin_region(face_crop)
            result['skin_analysis'] = skin_result

            # 2. Heart rate estimation (rPPG)
            skin_mask = self.skin_analyzer._get_skin_mask(face_crop)
            hr_result = self.heart_rate_estimator.process_frame(face_crop, skin_mask)
            result['heart_rate'] = hr_result

            # 3. Respiratory rate estimation
            nose_y = None
            if face_landmarks is not None and len(face_landmarks) > 33:
                nose_y = float(face_landmarks[33][1])
            resp_result = self.resp_rate_estimator.process_frame(
                face_landmarks, nose_y=nose_y)
            result['respiratory'] = resp_result

            # 4. Detect health conditions
            conditions = self._detect_conditions(skin_result, hr_result, resp_result)
            result['detected_conditions'] = conditions

            # 5. Overall alert level
            alert, emergency = self._determine_alert(conditions)
            result['alert_level'] = alert
            result['emergency'] = emergency

        return result

    def _detect_conditions(self, skin: Dict, hr: Dict, resp: Dict) -> List[Dict]:
        """Detect health conditions based on analysis results."""
        conditions = []

        # === Skin conditions ===
        skin_checks = [
            ('PALLOR', skin.get('pallor_score', 0), 0.4, 'Тері бозарған / Бледность кожи'),
            ('JAUNDICE', skin.get('jaundice_score', 0), 0.4, 'Тері сарғайған / Желтушность кожи'),
            ('CYANOSIS', skin.get('cyanosis_score', 0), 0.4, 'Тері көгерген / Цианоз кожи'),
            ('FACIAL_REDNESS', skin.get('redness_score', 0), 0.5, 'Бет қызарған / Покраснение лица'),
            ('SKIN_RASH', skin.get('rash_score', 0), 0.5, 'Тері бөртпесі / Кожная сыпь'),
            ('SKIN_DRYNESS', skin.get('dryness_score', 0), 0.5, 'Тері құрғақ / Сухость кожи'),
        ]

        for code, score, threshold, desc in skin_checks:
            if score >= threshold:
                severity = 'critical' if code == 'CYANOSIS' and score > 0.6 else \
                           'warning' if score > 0.6 else 'info'
                conditions.append({
                    'condition_code': code,
                    'confidence': round(score, 3),
                    'detected': True,
                    'raw_value': round(score, 3),
                    'threshold_value': threshold,
                    'face_region': 'face',
                    'notes': desc,
                    'severity': severity,
                })

        # === Heart rate conditions ===
        hr_value = hr.get('estimated_heart_rate', 0)
        hr_conf = hr.get('heart_rate_confidence', 0)
        if hr_conf > 0.3 and hr_value > 0:
            category, desc = self.heart_rate_estimator.get_pulse_category()
            if category not in ('NORMAL', 'UNKNOWN'):
                severity = 'critical' if 'CRITICAL' in category else 'warning'
                conditions.append({
                    'condition_code': category,
                    'confidence': round(hr_conf, 3),
                    'detected': True,
                    'raw_value': round(hr_value, 1),
                    'threshold_value': 60 if 'LOW' in category or category == 'BRADYCARDIA' else 100,
                    'face_region': 'face_rppg',
                    'notes': desc,
                    'severity': severity,
                })

        # === Respiratory conditions ===
        resp_rate = resp.get('estimated_resp_rate', 0)
        resp_conf = resp.get('resp_rate_confidence', 0)
        if resp_conf > 0.3 and resp_rate > 0:
            category, desc = self.resp_rate_estimator.get_breathing_category()
            if category not in ('NORMAL', 'UNKNOWN'):
                conditions.append({
                    'condition_code': category,
                    'confidence': round(resp_conf, 3),
                    'detected': True,
                    'raw_value': round(resp_rate, 1),
                    'threshold_value': 25 if category == 'FAST_BREATHING' else 12,
                    'face_region': 'face_movement',
                    'notes': desc,
                    'severity': 'warning',
                })

        self.detected_symptoms = conditions
        return conditions

    def _determine_alert(self, conditions: List[Dict]) -> Tuple[str, bool]:
        """Determine overall alert level and emergency status."""
        if not conditions:
            return ('none', False)

        severities = [c.get('severity', 'info') for c in conditions]
        emergency = 'critical' in severities

        if emergency:
            return ('critical', True)
        elif 'warning' in severities:
            return ('warning', False)
        else:
            return ('info', False)

    def get_summary(self) -> Dict:
        """Get a summary of current health status."""
        pulse_cat, pulse_desc = self.heart_rate_estimator.get_pulse_category()
        breath_cat, breath_desc = self.resp_rate_estimator.get_breathing_category()

        return {
            'heart_rate_bpm': round(self.heart_rate_estimator.heart_rate, 1),
            'heart_rate_category': pulse_cat,
            'heart_rate_description': pulse_desc,
            'resp_rate': round(self.resp_rate_estimator.resp_rate, 1),
            'resp_rate_category': breath_cat,
            'resp_rate_description': breath_desc,
            'active_symptoms': len(self.detected_symptoms),
            'symptoms': self.detected_symptoms,
        }

    def reset(self):
        """Reset all analyzers."""
        self.skin_analyzer.reset()
        self.heart_rate_estimator.reset()
        self.resp_rate_estimator.reset()
        self.alert_history.clear()
        self.detected_symptoms = []
