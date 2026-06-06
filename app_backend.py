"""
Flask REST API Backend for Bereke AI
Анализ лица (эмоции, усталость 0-100%), голоса (эмоции, стресс 0-100%).
Сохранение в базу, статистика за 7 дней.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path
from datetime import datetime, timedelta
import base64
import numpy as np
from PIL import Image
import tempfile
import torch
from transformers import pipeline
import onnxruntime as ort
import cv2
from ultralytics import YOLO
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("⚠️  DeepFace not available (requires tensorflow). Face recognition disabled.")
import logging
from database import WellbeingDatabase
from lstm_predictor import LSTMPredictor
from gambling_analyzer import GamblingAnalyzer

# ===================== EASY MONEY ML IMPORTS =====================
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.calibration import CalibratedClassifierCV

# Suppress DeepFace verbose logs
logging.getLogger('deepface').setLevel(logging.WARNING)

# ===================== INIT =====================
app = Flask(__name__)
CORS(app)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = 'wellbeing-monitoring-secret-key'
db = WellbeingDatabase()

# ===================== LOAD MODELS =====================
print("🔄 Loading face emotion model (emotion-ferplus-8 ONNX)...")
# emotion-ferplus-8: trained on FER+ real human faces dataset
# Input: 1x1x64x64 grayscale float32
# Output: 8 emotions: neutral, happiness, surprise, sadness, anger, disgust, fear, contempt
FACE_LABELS = ["Neutral", "Happy", "Surprise", "Sad", "Angry", "Disgust", "Fear", "Contempt"]
face_onnx = ort.InferenceSession("./models/emotion-ferplus-8.onnx")
print("✅ Face emotion model loaded (emotion-ferplus-8, 8 classes, real faces)")

print("🔄 Loading voice emotion model...")
voice_pipe = pipeline("audio-classification", model="./models/voice_model", feature_extractor="./models/voice_model")
print("✅ Voice emotion model loaded")

print("🔄 Loading audio emotion model...")
audio_emotion_pipe = pipeline("audio-classification", model="./models/audio_emotion_model", feature_extractor="./models/audio_emotion_model")
print("✅ Audio emotion model loaded")

# ===================== YOLO PERSON TRACKER =====================
print("🔄 Loading YOLO person tracker...")
yolo_model = YOLO('yolov8n.pt')
_yolo_track_ids = {}  # track_id -> latest person info
print("✅ YOLO person tracker loaded")

# ===================== LSTM PREDICTOR =====================
print("💡 Loading LSTM predictor...")
_lstm_predictors = {}  # session_id -> LSTMPredictor
print("✅ LSTM predictor ready")

# ===================== GAMBLING ANALYZER =====================
_gambling_analyzers = {}  # session_id -> GamblingAnalyzer
print("🎰 Gambling addiction analyzer ready")

# ===================== EASY MONEY ML MODELS =====================
print("🎰 Training Easy Money behavioral risk models...")

EM_FEATURE_NAMES = [
    'depositsPerSession', 'accountDepleted', 'chasingLossEvents', 'rapidBetCount',
    'sessionLengthMinutes', 'betIncreaseAfterLoss', 'nightSession', 'switchedGameCount',
    'martingaleEvents', 'reinvestmentEvents', 'betEscalationRate', 'avgBetToBalanceRatio',
    'lossStreak5Plus', 'consecutiveDays',
]

def _em_generate_training_data(n=5000):
    np.random.seed(42)
    X, y = [], []
    for _ in range(n):
        is_pg = np.random.random() < 0.28
        if is_pg:
            row = [
                np.clip(np.random.gamma(2.8, 0.7), 0, 10),
                np.clip(np.random.gamma(3.0, 0.8), 0, 10),
                np.clip(np.random.gamma(3.5, 1.2), 0, 15),
                np.clip(np.random.gamma(2.5, 3.0), 0, 30),
                np.clip(np.random.gamma(3.0, 28), 0, 300),
                np.clip(np.random.gamma(2.8, 1.2), 0, 15),
                1 if np.random.random() < 0.45 else 0,
                np.clip(np.random.gamma(2.2, 1.5), 0, 12),
                np.clip(np.random.gamma(2.5, 1.3), 0, 12),
                np.clip(np.random.gamma(2.0, 1.2), 0, 10),
                np.clip(np.random.normal(0.45, 0.3), -0.5, 2),
                np.clip(np.random.beta(3, 4) * 0.8, 0, 1),
                np.clip(np.random.gamma(2, 1.2), 0, 8),
                np.clip(np.random.gamma(3, 2.5), 0, 30),
            ]
        else:
            row = [
                np.clip(np.random.gamma(1.1, 0.5), 0, 10),
                np.clip(np.random.gamma(1.0, 0.6), 0, 10),
                np.clip(np.random.gamma(0.8, 0.9), 0, 15),
                np.clip(np.random.gamma(1.0, 1.5), 0, 30),
                np.clip(np.random.gamma(2.0, 14), 0, 300),
                np.clip(np.random.gamma(0.9, 0.8), 0, 15),
                1 if np.random.random() < 0.18 else 0,
                np.clip(np.random.gamma(1.0, 0.8), 0, 12),
                np.clip(np.random.gamma(0.7, 0.8), 0, 12),
                np.clip(np.random.gamma(0.8, 0.7), 0, 10),
                np.clip(np.random.normal(0.05, 0.2), -0.5, 2),
                np.clip(np.random.beta(1.5, 8) * 0.5, 0, 1),
                np.clip(np.random.gamma(0.6, 0.8), 0, 8),
                np.clip(np.random.gamma(1.5, 1.2), 0, 30),
            ]
        X.append(row)
        y.append(1 if is_pg else 0)
    return np.array(X), np.array(y)

def _em_extract_features(data):
    cs = data.get('crossSession', {})
    return np.array([[
        float(data.get('depositsPerSession', 0)),
        float(data.get('accountDepleted', 0)),
        float(data.get('chasingLossEvents', 0)),
        float(data.get('rapidBetCount', 0)),
        float(data.get('sessionLengthMinutes', 0)),
        float(data.get('betIncreaseAfterLoss', 0)),
        1.0 if data.get('nightSession', False) else 0.0,
        float(data.get('switchedGameCount', 0)),
        float(data.get('martingaleEvents', 0)),
        float(data.get('reinvestmentEvents', 0)),
        float(data.get('betEscalationRate', 0)),
        float(data.get('avgBetToBalanceRatio', 0)),
        float(data.get('lossStreak5Plus', 0)),
        float(cs.get('consecutiveDays', 0)),
    ]])

# Train models
_em_X, _em_y = _em_generate_training_data(5000)
_em_X_train, _em_X_test, _em_y_train, _em_y_test = train_test_split(
    _em_X, _em_y, test_size=0.2, random_state=42, stratify=_em_y
)
_em_scaler = StandardScaler()
_em_X_train_s = _em_scaler.fit_transform(_em_X_train)
_em_X_test_s = _em_scaler.transform(_em_X_test)

_em_rf_base = RandomForestClassifier(
    n_estimators=300, max_depth=10, min_samples_split=4, min_samples_leaf=2,
    class_weight={0: 1, 1: 3}, random_state=42, n_jobs=-1
)
_em_rf = CalibratedClassifierCV(_em_rf_base, cv=3, method='sigmoid')
_em_rf.fit(_em_X_train_s, _em_y_train)

_em_gb = GradientBoostingClassifier(
    n_estimators=200, learning_rate=0.04, max_depth=5, min_samples_split=5,
    subsample=0.8, random_state=42
)
_em_gb.fit(_em_X_train_s, _em_y_train)

_em_rf_auc = roc_auc_score(_em_y_test, _em_rf.predict_proba(_em_X_test_s)[:, 1])
_em_gb_auc = roc_auc_score(_em_y_test, _em_gb.predict_proba(_em_X_test_s)[:, 1])
_em_ens_proba = _em_rf.predict_proba(_em_X_test_s)[:, 1] * 0.6 + _em_gb.predict_proba(_em_X_test_s)[:, 1] * 0.4
_em_ens_auc = roc_auc_score(_em_y_test, _em_ens_proba)

_em_rf_base.fit(_em_X_train_s, _em_y_train)
print(f"✅ Easy Money models trained — RF AUC: {_em_rf_auc:.4f}, GB AUC: {_em_gb_auc:.4f}, Ensemble: {_em_ens_auc:.4f}")
# ===================== LOAD KNOWN FACES CACHE =====================
print("🔄 Loading known faces database...")
_known_faces_cache = None  # will be loaded lazily on first use

# ===================== BLINK DETECTION (EAR via cv2.face LBF landmarks) =====================
print("🔄 Loading face landmark model for blink detection...")
_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
_facemark = cv2.face.createFacemarkLBF()
_facemark.loadModel('./models/lbfmodel.yaml')
print("✅ Face landmark model loaded")

# 68-point landmark indices for eyes (0-indexed)
# Right eye: points 36-41, Left eye: points 42-47
EAR_THRESHOLD = 0.21  # Below = blink (relaxed for smoothed EAR values)
EAR_OPEN_THRESHOLD = 0.26  # Above = eyes open (wider hysteresis band)
BLINK_MIN_CLOSED_FRAMES = 1  # Just 1 frame below threshold = blink detected
_blink_state = {}  # { session_id: { 'count': int, 'closed_frames': int, 'confirmed_closed': bool } }
_recognition_state = {}  # { session_id: { 'frame_count': int, 'last_person': str|None } }

# PERCLOS tracking for fatigue: percentage of time eyes are closed over sliding window
_ear_history = {}  # { session_id: [ear_values...] } - last 60 readings (~9 seconds at 150ms)
_ear_smooth = {}  # { session_id: [last 3 raw EAR values for smoothing] }

# Temporal smoothing for emotion scores (EMA = Exponential Moving Average)
_emotion_ema = {}  # { session_id: {'smile': float, 'anger': float, 'sadness': float} }
EMOTION_EMA_ALPHA = 0.45  # 0-1, higher = more responsive, lower = smoother


def _ear(pts, indices):
    """Eye Aspect Ratio from 6 points. Low EAR = closed eye."""
    p1, p2, p3, p4, p5, p6 = [pts[i] for i in indices]
    v1 = np.linalg.norm(p2 - p6)  # vertical 1
    v2 = np.linalg.norm(p3 - p5)  # vertical 2
    h = np.linalg.norm(p1 - p4)   # horizontal
    if h < 1e-6:
        return 0.3
    return (v1 + v2) / (2.0 * h)


def _detect_blink_and_eyes(frame_bgr, session_id):
    """Detect blinks via EAR (Eye Aspect Ratio) using 68 face landmarks.
    Returns: (blink_count, eye_openness_pct 0-100, ear_value, face_found, face_bbox, smile_score, anger_landmark, sadness_landmark, landmarks_68)"""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    # Equalize histogram for better detection in varying lighting
    gray = cv2.equalizeHist(gray)
    h, w = gray.shape[:2]
    # Real face in front of camera should be at least 1/5 of frame width
    min_face = max(60, min(w, h) // 5)
    faces = _face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(min_face, min_face))

    if len(faces) == 0:
        return (_get_blink_count(session_id), 0, 0.0, False, None, 0, 0, 0, None)

    # Pick the largest face (most likely the real one in front of camera)
    areas = [fw * fh for (_, _, fw, fh) in faces]
    best_idx = int(np.argmax(areas))
    fx, fy, fw, fh = faces[best_idx]

    # Filter: face must be at least 3% of frame area — screens show small faces
    face_area_pct = (fw * fh) / (w * h) * 100
    if face_area_pct < 3.0:
        return (_get_blink_count(session_id), 0, 0.0, False, None, 0, 0, 0, None)

    # Format for facemark: single face rect
    faces_arr = np.array([[fx, fy, fw, fh]])
    try:
        ok, landmarks_list = _facemark.fit(gray, faces_arr)
    except Exception:
        return (_get_blink_count(session_id), 0, 0.0, False, None, 0, 0, 0, None)

    if not ok or len(landmarks_list) == 0:
        return (_get_blink_count(session_id), 0, 0.0, False, None, 0, 0, 0, None)

    pts = landmarks_list[0][0]  # shape (68, 2)

    # Sanity check: landmarks should span a reasonable portion of the face bbox
    lm_xmin, lm_xmax = pts[:, 0].min(), pts[:, 0].max()
    lm_ymin, lm_ymax = pts[:, 1].min(), pts[:, 1].max()
    lm_w = lm_xmax - lm_xmin
    lm_h = lm_ymax - lm_ymin
    # If landmarks are too compressed (< 40% of face bbox), it's likely a false detection
    if lm_w < fw * 0.35 or lm_h < fh * 0.35:
        return (_get_blink_count(session_id), 0, 0.0, False, None, 0, 0, 0, None)

    # Right eye: 36..41, Left eye: 42..47
    ear_right = _ear(pts, [36, 37, 38, 39, 40, 41])
    ear_left = _ear(pts, [42, 43, 44, 45, 46, 47])
    ear_raw = (ear_left + ear_right) / 2.0

    # Temporal smoothing: rolling average of last 3 EAR values to filter landmark jitter
    sid = str(session_id) if session_id else '_global'
    if sid not in _ear_smooth:
        _ear_smooth[sid] = []
    _ear_smooth[sid].append(ear_raw)
    if len(_ear_smooth[sid]) > 2:
        _ear_smooth[sid] = _ear_smooth[sid][-2:]
    ear_avg = sum(_ear_smooth[sid]) / len(_ear_smooth[sid])

    # Eye openness as percentage (EAR ~0.15=closed, ~0.30=open)
    eye_openness = int(round(min(100, max(0, (ear_avg - 0.12) / 0.22 * 100))))

    # Debug: print EAR every 10th frame to trace blink detection
    if sid not in _ear_smooth.get('_dbg_cnt', {}):
        if '_dbg_cnt' not in _ear_smooth: _ear_smooth['_dbg_cnt'] = {}
        _ear_smooth['_dbg_cnt'][sid] = 0
    _ear_smooth['_dbg_cnt'][sid] += 1
    if _ear_smooth['_dbg_cnt'][sid] % 10 == 0:
        bcount = _blink_state.get(sid, {}).get('count', 0)
        print(f"👁️ EAR raw={ear_raw:.3f} avg={ear_avg:.3f} openness={eye_openness}% blinks={bcount}")

    # Blink detection with hysteresis + consecutive frame requirement
    if sid not in _blink_state:
        _blink_state[sid] = {'count': 0, 'closed_frames': 0, 'confirmed_closed': False}

    state = _blink_state[sid]

    # Hysteresis: use lower threshold to enter "closed", higher to exit
    if ear_avg < EAR_THRESHOLD:
        state['closed_frames'] += 1
    elif ear_avg > EAR_OPEN_THRESHOLD:
        # Eyes opened — count blink only if we had confirmed closure
        if state['confirmed_closed']:
            state['count'] += 1
            state['confirmed_closed'] = False
        state['closed_frames'] = 0
    # else: in hysteresis band — don't change state

    # Confirm closure only after minimum consecutive frames
    if state['closed_frames'] >= BLINK_MIN_CLOSED_FRAMES:
        state['confirmed_closed'] = True

    # Track EAR history for PERCLOS fatigue detection
    if sid not in _ear_history:
        _ear_history[sid] = []
    _ear_history[sid].append(ear_avg)
    if len(_ear_history[sid]) > 60:
        _ear_history[sid] = _ear_history[sid][-60:]

    # ========================================================
    # LANDMARK GEOMETRY
    # Normalize by outer-eye distance (more stable than inner-eye)
    # ========================================================
    outer_eye_dist = np.linalg.norm(pts[36] - pts[45])  # outer eye corners
    if outer_eye_dist < 1e-6:
        outer_eye_dist = 1.0
    D = outer_eye_dist  # shorthand

    # Mouth measurements
    mouth_w = np.linalg.norm(pts[48] - pts[54])            # mouth corner to corner
    mouth_h = np.linalg.norm(pts[51] - pts[57])            # top lip to bottom lip
    corner_l = pts[48]                                      # left mouth corner
    corner_r = pts[54]                                      # right mouth corner
    nose_base = pts[33]                                     # nose bottom center

    # MAR = Mouth Aspect Ratio (like EAR but for mouth)
    # When smiling: mouth widens → MAR decreases (wide but thin)
    # When talking: mouth opens → MAR increases
    mar = mouth_h / (mouth_w + 1e-6)

    # Smile Ratio: mouth width relative to face width (outer eyes)
    smile_ratio = mouth_w / D  # typically 0.55-0.65 neutral, 0.70+ smile

    # Corner-to-nose angle: corners RISE when smiling
    # Calculate how high corners are relative to nose base
    # Positive = corners below nose (neutral), less positive = corners rising (smile)
    corner_y_avg = (corner_l[1] + corner_r[1]) / 2.0
    nose_to_corner_drop = (corner_y_avg - nose_base[1]) / D  # positive = corners below nose

    # ========================================================
    # 1) SMILE — simple and reliable
    # ========================================================
    # S1: Mouth gets WIDER relative to face (most reliable)
    s1 = max(0.0, (smile_ratio - 0.58) * 250)  # 0 at 0.58, 100 at 0.98

    # S2: Mouth corners RISE toward nose level
    # Neutral: corners ~0.35D below nose. Smile: ~0.20D below nose
    s2 = max(0.0, (0.35 - nose_to_corner_drop) * 200)  # corners rising

    # S3: Mouth opens slightly (teeth visible = thin+wide mouth)
    s3 = max(0.0, (mouth_h / D - 0.05) * 40) if smile_ratio > 0.60 else 0.0

    smile_score = max(0, min(100, int(s1 + s2 + s3)))

    # ========================================================
    # 2) ANGER — brow and mouth
    # ========================================================
    # Inner brow distance (normalized)
    inner_brow_dist = np.linalg.norm(pts[21] - pts[22]) / D
    # Brow height above eye
    brow_r_y = (pts[19][1] + pts[20][1] + pts[21][1]) / 3.0
    brow_l_y = (pts[22][1] + pts[23][1] + pts[24][1]) / 3.0
    eye_r_y = (pts[37][1] + pts[38][1]) / 2.0
    eye_l_y = (pts[43][1] + pts[44][1]) / 2.0
    brow_drop_r = (eye_r_y - brow_r_y) / D  # positive = brow above eye
    brow_drop_l = (eye_l_y - brow_l_y) / D
    avg_brow_height = (brow_drop_r + brow_drop_l) / 2.0

    # A1: Brows come together (furrow)
    a1 = max(0.0, (0.22 - inner_brow_dist) * 300)  # close brows
    # A2: Brows drop low
    a2 = max(0.0, (0.12 - avg_brow_height) * 350)  # low brows
    # A3: Mouth tightens (thin lips, not wide)
    a3 = max(0.0, (0.06 - mar) * 80) if smile_ratio < 0.62 else 0.0

    # Anti-anger: smiling cancels anger
    anger_penalty = smile_score * 0.4
    anger_landmark = max(0, min(100, int(a1 + a2 + a3 - anger_penalty)))

    # ========================================================
    # 3) SADNESS — drooping corners and oblique brows
    # ========================================================
    # D1: Mouth corners DROP below normal
    d1 = max(0.0, (nose_to_corner_drop - 0.35) * 200)  # corners sinking

    # D2: Mouth narrows
    d2 = max(0.0, (0.56 - smile_ratio) * 150)  # narrow mouth

    # D3: Inner brows rise relative to outer (oblique/sad brows)
    inner_brow_avg_y = (pts[21][1] + pts[22][1]) / 2.0
    outer_brow_avg_y = (pts[17][1] + pts[26][1]) / 2.0
    brow_oblique = (outer_brow_avg_y - inner_brow_avg_y) / D
    d3 = max(0.0, brow_oblique * 80)

    sadness_landmark = max(0, min(100, int(d1 + d2 + d3)))

    return (state['count'], eye_openness, round(ear_avg, 3), True,
            (fx, fy, fw, fh), smile_score, anger_landmark, sadness_landmark, pts)


def _get_blink_count(session_id):
    """Get current blink count without modifying state."""
    sid = str(session_id) if session_id else '_global'
    return _blink_state.get(sid, {}).get('count', 0)


# ===================== ULTRA-FAST BLINK-ONLY DETECTOR =====================
# Stripped down: Haar cascade + LBF landmarks → EAR → blink count
# NO smoothing, NO smile/anger/sadness, NO geometry — pure speed (~10-20ms)
_blink_face_cascade_fast = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def _detect_blink_fast(frame_bgr, session_id):
    """Ultra-fast blink detection. Returns (blink_count, eye_openness, ear, face_found)."""
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    h, w = gray.shape[:2]
    min_face = max(30, min(w, h) // 4)
    # Faster: scaleFactor=1.2, minNeighbors=3
    faces = _blink_face_cascade_fast.detectMultiScale(gray, 1.2, 3, minSize=(min_face, min_face))

    sid = str(session_id) if session_id else '_global'
    if len(faces) == 0:
        return (_blink_state.get(sid, {}).get('count', 0), 0, 0.0, False)

    # Largest face
    areas = [fw * fh for (_, _, fw, fh) in faces]
    best_idx = int(np.argmax(areas))
    fx, fy, fw, fh = faces[best_idx]

    faces_arr = np.array([[fx, fy, fw, fh]])
    try:
        ok, landmarks_list = _facemark.fit(gray, faces_arr)
    except Exception:
        return (_blink_state.get(sid, {}).get('count', 0), 0, 0.0, False)

    if not ok or len(landmarks_list) == 0:
        return (_blink_state.get(sid, {}).get('count', 0), 0, 0.0, False)

    pts = landmarks_list[0][0]

    # Raw EAR — NO smoothing for instant response
    ear_right = _ear(pts, [36, 37, 38, 39, 40, 41])
    ear_left = _ear(pts, [42, 43, 44, 45, 46, 47])
    ear_raw = (ear_left + ear_right) / 2.0

    eye_openness = int(round(min(100, max(0, (ear_raw - 0.12) / 0.22 * 100))))

    # Blink state machine (no smoothing — raw EAR directly)
    if sid not in _blink_state:
        _blink_state[sid] = {'count': 0, 'closed_frames': 0, 'confirmed_closed': False}
    state = _blink_state[sid]

    if ear_raw < EAR_THRESHOLD:
        state['closed_frames'] += 1
    elif ear_raw > EAR_OPEN_THRESHOLD:
        if state['confirmed_closed']:
            state['count'] += 1
            state['confirmed_closed'] = False
        state['closed_frames'] = 0

    if state['closed_frames'] >= BLINK_MIN_CLOSED_FRAMES:
        state['confirmed_closed'] = True

    # Also feed EAR into history for PERCLOS (used by frame endpoint)
    if sid not in _ear_history:
        _ear_history[sid] = []
    _ear_history[sid].append(ear_raw)
    if len(_ear_history[sid]) > 60:
        _ear_history[sid] = _ear_history[sid][-60:]

    return (state['count'], eye_openness, round(ear_raw, 3), True)
    return _blink_state.get(sid, {}).get('count', 0)


def _face_emotion(image_np):
    """Анализ эмоций по лицу через emotion-ferplus-8 ONNX.
    Input: BGR numpy array (cropped face).
    Returns: dict label->probability (8 emotions)."""
    # Convert to grayscale and resize to 64x64
    if len(image_np.shape) == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
    else:
        gray = image_np
    gray = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)
    # CLAHE — adaptive contrast enhancement, critical for emotion recognition
    # Normalizes lighting so the model sees clear facial features
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
    gray = clahe.apply(gray)
    # Normalize to 0-1 float32, shape: 1x1x64x64
    img = gray.astype(np.float32) / 255.0
    img = img.reshape(1, 1, 64, 64)
    # Run inference
    logits = face_onnx.run(None, {'Input3': img})[0][0]
    # Temperature-scaled softmax (T<1 = more decisive, less flat distribution)
    # Without this the model often outputs ~12-15% for every emotion
    TEMPERATURE = 1.5
    scaled = (logits - np.max(logits)) / TEMPERATURE
    exp_logits = np.exp(scaled)
    probs = exp_logits / exp_logits.sum()
    return {FACE_LABELS[i]: float(probs[i]) for i in range(len(FACE_LABELS))}


def _yolo_detect_persons(frame_bgr):
    """Detect persons in frame via YOLO.
    Filters out false positives (hands, arms, objects) by requiring:
    - High confidence (>0.55)
    - Minimum bbox size (at least 5% of frame area)
    - Reasonable aspect ratio (height >= 0.4 * width — not extremely flat)
    Returns: list of dicts with person info."""
    try:
        results = yolo_model.predict(frame_bgr, classes=[0], verbose=False, conf=0.55)
        persons = []
        fh, fw = frame_bgr.shape[:2]
        frame_area = fw * fh
        if results[0].boxes is not None and len(results[0].boxes) > 0:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            confs = results[0].boxes.conf.cpu().tolist()
            for i, (box, conf) in enumerate(zip(boxes, confs)):
                x1, y1, x2, y2 = box
                bw = x2 - x1
                bh = y2 - y1
                box_area = bw * bh
                # Skip tiny detections (< 5% of frame) — likely hands/objects
                if box_area < frame_area * 0.05:
                    continue
                # Skip very flat boxes (hand across frame) — person should be tall-ish
                if bh < bw * 0.4:
                    continue
                persons.append({
                    'id': i + 1,
                    'bbox': [x1, y1, x2, y2],
                    'confidence': round(float(conf), 2),
                })
        return persons
    except Exception as e:
        print(f"⚠️ YOLO error: {e}")
        return []


def _analyze_person_face(frame_bgr, bbox):
    """Run full face analysis on a person crop using DeepFace + landmarks."""
    x1, y1, x2, y2 = bbox
    h, w = frame_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    crop = frame_bgr[y1:y2, x1:x2]
    if crop.size == 0 or crop.shape[0] < 30 or crop.shape[1] < 30:
        return None
    result = {}

    # Fast ONNX emotion analysis (~5ms vs DeepFace ~1-2s)
    try:
        onnx_scores = _face_emotion(crop)
        pct = {k: int(round(v * 100)) for k, v in onnx_scores.items()}
        dominant = max(pct, key=pct.get)
        result['emotion_percent'] = pct
        result['dominant_emotion'] = dominant
    except Exception:
        result['emotion_percent'] = {}
        result['dominant_emotion'] = 'Unknown'

    # --- Override Neutral → Tired when eyes are droopy ---
    if result.get('dominant_emotion') == 'Neutral':
        # Check eye_openness after landmarks analysis below
        _person_might_be_tired = True
    else:
        _person_might_be_tired = False

    # --- Landmarks: eye openness, smile, anger, sadness ---
    try:
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        ch, cw = gray.shape[:2]
        min_face_sz = max(20, min(cw, ch) // 5)
        faces = _face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(min_face_sz, min_face_sz))
        if len(faces) > 0:
            areas = [fw * fh for (_, _, fw, fh) in faces]
            best = int(np.argmax(areas))
            fx, fy, fw, fh = faces[best]
            faces_arr = np.array([[fx, fy, fw, fh]])
            ok, lm_list = _facemark.fit(gray, faces_arr)
            if ok and len(lm_list) > 0:
                pts = lm_list[0][0]
                # EAR
                ear_r = _ear(pts, [36,37,38,39,40,41])
                ear_l = _ear(pts, [42,43,44,45,46,47])
                ear_avg = (ear_l + ear_r) / 2.0
                eye_openness = int(round(min(100, max(0, (ear_avg - 0.12) / 0.22 * 100))))
                result['eye_openness'] = eye_openness
                result['ear'] = float(round(ear_avg, 3))
                # Geometry
                outer_eye_dist = max(1e-6, np.linalg.norm(pts[36] - pts[45]))
                D = outer_eye_dist
                mouth_w = np.linalg.norm(pts[48] - pts[54])
                mouth_h = np.linalg.norm(pts[51] - pts[57])
                mar = mouth_h / (mouth_w + 1e-6)
                smile_ratio = mouth_w / D
                corner_y_avg = (pts[48][1] + pts[54][1]) / 2.0
                nose_to_corner_drop = (corner_y_avg - pts[33][1]) / D
                # Smile
                s1 = max(0.0, (smile_ratio - 0.58) * 250)
                s2 = max(0.0, (0.35 - nose_to_corner_drop) * 200)
                s3 = max(0.0, (mouth_h / D - 0.05) * 40) if smile_ratio > 0.60 else 0.0
                result['smile_score'] = max(0, min(100, int(s1 + s2 + s3)))
                # Anger
                inner_brow_dist = np.linalg.norm(pts[21] - pts[22]) / D
                brow_r_y = (pts[19][1] + pts[20][1] + pts[21][1]) / 3.0
                brow_l_y = (pts[22][1] + pts[23][1] + pts[24][1]) / 3.0
                eye_r_y = (pts[37][1] + pts[38][1]) / 2.0
                eye_l_y = (pts[43][1] + pts[44][1]) / 2.0
                avg_brow_h = ((eye_r_y - brow_r_y) + (eye_l_y - brow_l_y)) / 2.0 / D
                a1 = max(0.0, (0.22 - inner_brow_dist) * 300)
                a2 = max(0.0, (0.12 - avg_brow_h) * 350)
                a3 = max(0.0, (0.06 - mar) * 80) if smile_ratio < 0.62 else 0.0
                anger_penalty = result.get('smile_score', 0) * 0.4
                result['anger_score'] = max(0, min(100, int(a1 + a2 + a3 - anger_penalty)))
                # Sadness
                d1 = max(0.0, (nose_to_corner_drop - 0.35) * 200)
                d2 = max(0.0, (0.56 - smile_ratio) * 150)
                inner_brow_avg_y = (pts[21][1] + pts[22][1]) / 2.0
                outer_brow_avg_y = (pts[17][1] + pts[26][1]) / 2.0
                brow_oblique = (outer_brow_avg_y - inner_brow_avg_y) / D
                d3 = max(0.0, brow_oblique * 80)
                result['sad_score'] = max(0, min(100, int(d1 + d2 + d3)))
    except Exception:
        pass

    # --- Final: override Neutral → Tired if eyes are very droopy ---
    if _person_might_be_tired and result.get('eye_openness', 100) < 40:
        result['dominant_emotion'] = 'Tired'

    # --- Per-person fatigue estimation ---
    eye_op = result.get('eye_openness', 80)
    if eye_op >= 55:
        p_eye_fatigue = 0
    elif eye_op >= 35:
        p_eye_fatigue = int((55 - eye_op) * 2.5)
    else:
        p_eye_fatigue = int(50 + (35 - eye_op) * 1.5)

    ep = result.get('emotion_percent', {})
    neg = (ep.get('Angry', 0) + ep.get('Sad', 0) + ep.get('Fear', 0) + ep.get('Disgust', 0))
    p_neg_fatigue = min(30, int(neg * 0.15))

    result['fatigue_percent'] = min(100, max(0, p_eye_fatigue + p_neg_fatigue))

    # --- Per-person wellbeing score (0-100, higher = better) ---
    # Components: eye openness (positive), smile (positive), low fatigue (positive),
    #             low anger (positive), low sadness (positive)
    wb_eye = min(30, int(eye_op * 0.30))            # 0-30
    wb_smile = min(25, int(result.get('smile_score', 0) * 0.25))  # 0-25
    wb_fatigue = max(0, 25 - int(result['fatigue_percent'] * 0.25))  # 0-25
    wb_anger = max(0, 10 - int(result.get('anger_score', 0) * 0.10))  # 0-10
    wb_sad = max(0, 10 - int(result.get('sad_score', 0) * 0.10))    # 0-10
    result['wellbeing_score'] = min(100, max(0, wb_eye + wb_smile + wb_fatigue + wb_anger + wb_sad))

    return result if result else None


# ===================== BLINK ONLY (ultra-fast, max fps) =====================
@app.route('/api/analyze/blink', methods=['POST'])
def analyze_blink():
    """Ultra-fast blink-only detection (~10-20ms per frame).
    Uses stripped-down Haar + LBF → raw EAR. No YOLO, no emotion, no gambling."""
    try:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get('image', '')
        session_id = data.get('session_id')

        if not image_b64:
            return jsonify({'error': 'No image data'}), 400
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        img_bytes = base64.b64decode(image_b64)
        arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'error': 'Failed to decode image'}), 400

        blink_count, eye_openness, ear_val, face_found = _detect_blink_fast(frame, session_id)

        return jsonify({
            'blink_rate': int(blink_count),
            'eye_openness_percent': int(eye_openness),
            'ear': float(ear_val),
            'face_detected': bool(face_found),
        }), 200
    except Exception:
        sid = str(session_id) if session_id else '_global'
        return jsonify({'blink_rate': _blink_state.get(sid, {}).get('count', 0), 'face_detected': False}), 200


# ===================== ANALYZE FRAME (full, with emotion) =====================
@app.route('/api/analyze/frame', methods=['POST'])
def analyze_frame():
    try:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get('image', '')
        session_id = data.get('session_id')

        if not image_b64:
            return jsonify({'error': 'No image data'}), 400
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        img_bytes = base64.b64decode(image_b64)
        arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'error': 'Failed to decode image'}), 400

        import time as _time
        _t0 = _time.time()

        # Blink & eye detection first to know if face is present
        blink_count, eye_openness, ear_val, face_found, face_bbox, smile_score, anger_landmark, sadness_landmark, landmarks_68 = _detect_blink_and_eyes(frame, session_id)
        _t1 = _time.time()

        if face_found:
            # Crop face region for emotion analysis
            if face_bbox:
                fx, fy, fw_f, fh_f = face_bbox
                h_frame, w_frame = frame.shape[:2]
                pad_x = int(fw_f * 0.15)
                pad_y = int(fh_f * 0.15)
                x1 = max(0, fx - pad_x)
                y1 = max(0, fy - pad_y)
                x2 = min(w_frame, fx + fw_f + pad_x)
                y2 = min(h_frame, fy + fh_f + pad_y)
                face_crop = frame[y1:y2, x1:x2]
            else:
                face_crop = frame

            # Fast ONNX emotion analysis (~5ms vs DeepFace ~1-2s)
            scores = _face_emotion(face_crop)

            pct = {k: int(round(v * 100)) for k, v in scores.items()}
            dominant = max(pct, key=pct.get)

            # --- IMPROVED FATIGUE ALGORITHM ---
            sid_f = str(session_id) if session_id else '_global'
            ear_hist = _ear_history.get(sid_f, [])
            perclos = 0
            if len(ear_hist) >= 10:
                closed_count = sum(1 for e in ear_hist if e < EAR_THRESHOLD)
                perclos = closed_count / len(ear_hist) * 100

            ear_trend_fatigue = 0
            if len(ear_hist) >= 20:
                first_half = np.mean(ear_hist[:len(ear_hist)//2])
                second_half = np.mean(ear_hist[len(ear_hist)//2:])
                ear_drop = first_half - second_half
                if ear_drop > 0:
                    ear_trend_fatigue = min(30, int(ear_drop * 300))

            if eye_openness >= 55:
                instant_eye_fatigue = 0
            elif eye_openness >= 35:
                instant_eye_fatigue = int((55 - eye_openness) * 2.5)
            else:
                instant_eye_fatigue = int(50 + (35 - eye_openness) * 1.5)

            neg_score = (scores.get("Angry", 0) + scores.get("Sad", 0) + scores.get("Fear", 0) + scores.get("Contempt", 0)) / 4.0

            fatigue = int(round(
                perclos * 0.35 +
                instant_eye_fatigue * 0.25 +
                ear_trend_fatigue +
                neg_score * 100 * 0.20
            ))
            fatigue = min(100, max(0, fatigue))

            # ========================================
            # COMBINE MODEL + LANDMARKS
            # Both contribute independently — take the MAX of the two
            # Each score = max(DeepFace primary emotion %, landmark score)
            # All formulas are equal and balanced on the same scale.
            # ========================================

            # --- SMILE ---
            model_happy = scores.get("Happy", 0) * 100
            lm_smile = float(smile_score)
            smile_final = max(0, min(100, int(max(model_happy, lm_smile))))

            # --- ANGER ---
            model_anger = scores.get("Angry", 0) * 100
            lm_anger = float(anger_landmark)
            anger_final = max(0, min(100, int(max(model_anger, lm_anger))))

            # --- SADNESS ---
            model_sad = scores.get("Sad", 0) * 100
            lm_sad = float(sadness_landmark)
            sad_final = max(0, min(100, int(max(model_sad, lm_sad))))

            # ========================================
            # TEMPORAL SMOOTHING (EMA) — prevents flickering
            # ========================================
            ema_key = str(session_id) if session_id else '_global'
            if ema_key not in _emotion_ema:
                _emotion_ema[ema_key] = {'smile': float(smile_final), 'anger': float(anger_final), 'sadness': float(sad_final)}
            else:
                ema = _emotion_ema[ema_key]
                a = EMOTION_EMA_ALPHA
                ema['smile'] = a * smile_final + (1 - a) * ema['smile']
                ema['anger'] = a * anger_final + (1 - a) * ema['anger']
                ema['sadness'] = a * sad_final + (1 - a) * ema['sadness']

            ema = _emotion_ema[ema_key]
            smile_score = max(0, min(100, int(round(ema['smile']))))
            anger_score = max(0, min(100, int(round(ema['anger']))))
            sad_score = max(0, min(100, int(round(ema['sadness']))))

            # --- Recalculate dominant using COMBINED scores (model + landmarks + EMA) ---
            # Override the raw DeepFace dominant with our fused scores
            combined_emotions = {
                'Happy': smile_score,
                'Angry': anger_score,
                'Sad': sad_score,
                'Neutral': pct.get('Neutral', 0),
                'Surprise': pct.get('Surprise', 0),
                'Fear': pct.get('Fear', 0),
                'Disgust': pct.get('Disgust', 0),
            }
            dominant = max(combined_emotions, key=combined_emotions.get)
            # Also update pct to reflect combined scores for consistency
            pct['Happy'] = smile_score
            pct['Angry'] = anger_score
            pct['Sad'] = sad_score

            # --- Override to "Tired" when fatigued + neutral face ---
            # If fatigue >= 35% and eyes are droopy (<40%) and emotion is Neutral → Tired
            if dominant == 'Neutral' and fatigue >= 35 and eye_openness < 40:
                dominant = 'Tired'
                # Add Tired to pct for pie chart
                pct['Tired'] = fatigue
                pct['Neutral'] = max(0, pct.get('Neutral', 0) - fatigue)
        else:
            # No face — zero everything
            pct = {k: 0 for k in FACE_LABELS}
            dominant = "None"
            fatigue = 0
            eye_openness = 0
            smile_score = 0
            anger_score = 0
            sad_score = 0

        result = {
            'fatigue_score': round(fatigue / 100.0, 2),
            'fatigue_percent': fatigue,
            'eye_closure_ratio': round((100 - eye_openness) / 100.0, 2),
            'eye_openness_percent': eye_openness,
            'blink_rate': int(blink_count),
            'ear': float(ear_val),
            'emotion_percent': pct,
            'dominant_emotion': dominant,
            'smile_score': int(smile_score),
            'anger_score': int(anger_score),
            'sad_score': int(sad_score),
            'face_detected': bool(face_found),
            'timestamp': datetime.now().isoformat(),
        }

        # === Face Recognition: identify who this person is ===
        # Throttled: only run DeepFace.represent every 5th frame to save CPU
        recognized_person = None
        if face_found and _known_faces_cache is None:
            _load_known_faces_cache()
        sid_rec = str(session_id) if session_id else '_global'
        if sid_rec not in _recognition_state:
            _recognition_state[sid_rec] = {'frame_count': 0, 'last_person': None}
        _recognition_state[sid_rec]['frame_count'] += 1
        if face_found and _known_faces_cache:
            if _recognition_state[sid_rec]['frame_count'] % 5 == 1:  # every 5th frame
                try:
                    emb, _ = _get_face_embedding(frame)
                    if emb is not None:
                        recognized_person = _recognize_face(emb)
                        _recognition_state[sid_rec]['last_person'] = recognized_person
                except Exception:
                    pass
            else:
                recognized_person = _recognition_state[sid_rec]['last_person']
        result['recognized_person'] = recognized_person

        # === YOLO: detect and track all persons ===
        persons = _yolo_detect_persons(frame)
        result['people_count'] = len(persons)
        persons_detail = []

        # Build main analysis result (from Haar cascade largest face)
        _main_emotion = {
            'emotion_percent': pct,
            'dominant_emotion': dominant,
            'smile_score': int(smile_score),
            'anger_score': int(anger_score),
            'sad_score': int(sad_score),
            'eye_openness': int(eye_openness),
            'ear': float(ear_val),
            'fatigue_percent': fatigue,
            'wellbeing_score': min(100, max(0,
                min(30, int(eye_openness * 0.30)) +
                min(25, int(smile_score * 0.25)) +
                max(0, 25 - int(fatigue * 0.25)) +
                max(0, 10 - int(anger_score * 0.10)) +
                max(0, 10 - int(sad_score * 0.10))
            )),
        } if face_found else None

        # Match main Haar cascade face to the best-overlapping YOLO person
        matched_main_idx = -1
        if face_found and face_bbox and _main_emotion and len(persons) > 0:
            fx, fy, fw_f, fh_f = face_bbox
            face_cx = fx + fw_f / 2.0
            face_cy = fy + fh_f / 2.0
            best_overlap = 0
            for mi, mp in enumerate(persons):
                px1, py1, px2, py2 = mp['bbox']
                # Face center must be inside person bbox
                if px1 <= face_cx <= px2 and py1 <= face_cy <= py2:
                    # Calculate intersection area
                    ix1 = max(fx, px1)
                    iy1 = max(fy, py1)
                    ix2 = min(fx + fw_f, px2)
                    iy2 = min(fy + fh_f, py2)
                    if ix1 < ix2 and iy1 < iy2:
                        overlap = (ix2 - ix1) * (iy2 - iy1)
                        if overlap > best_overlap:
                            best_overlap = overlap
                            matched_main_idx = mi
            # Fallback: if no overlap found but only 1 person, match to person #0
            if matched_main_idx == -1 and len(persons) == 1:
                matched_main_idx = 0

        for i, p in enumerate(persons):
            info = dict(p)
            if i == matched_main_idx and _main_emotion:
                # This person matches the Haar cascade face — reuse main analysis
                info['emotion'] = dict(_main_emotion)
                info['is_main'] = True
                # Reuse main recognized person
                info['recognized_person'] = recognized_person
            else:
                # Independent analysis for this person
                emotion = _analyze_person_face(frame, p['bbox'])
                if emotion:
                    info['emotion'] = emotion
                info['is_main'] = False
                # Try to recognize this person individually (throttled — every 5th frame)
                info['recognized_person'] = None
                if _known_faces_cache and _recognition_state.get(sid_rec, {}).get('frame_count', 0) % 5 == 1:
                    try:
                        px1, py1, px2, py2 = p['bbox']
                        person_crop = frame[max(0,int(py1)):min(frame.shape[0],int(py2)),
                                            max(0,int(px1)):min(frame.shape[1],int(px2))]
                        if person_crop.size > 0:
                            emb_p, _ = _get_face_embedding(person_crop)
                            if emb_p is not None:
                                info['recognized_person'] = _recognize_face(emb_p)
                    except Exception:
                        pass
            persons_detail.append(info)
        result['persons'] = persons_detail

        # === Gambling Addiction Analysis ===
        sid_g = str(session_id) if session_id else '_global'
        if sid_g not in _gambling_analyzers:
            _gambling_analyzers[sid_g] = GamblingAnalyzer(fps=7.0)
        gambling_result = None
        if face_found and landmarks_68 is not None and face_bbox is not None:
            gambling_result = _gambling_analyzers[sid_g].analyze(
                landmarks_68=landmarks_68,
                face_bbox=face_bbox,
                frame_shape=frame.shape,
                blink_count=blink_count,
                ear_value=ear_val,
                yolo_persons=persons,
            )
        else:
            # Face temporarily lost — return last known gambling state
            gambling_result = _gambling_analyzers[sid_g]._build_result()
        result['gambling'] = gambling_result

        if session_id:
            try:
                gambling_risk_val = 0.0
                if gambling_result and 'gambling_risk' in gambling_result:
                    gambling_risk_val = gambling_result['gambling_risk']
                db.store_face_analysis(session_id, {
                    'fatigue_score': fatigue / 100.0,
                    'eye_closure_ratio': (100 - eye_openness) / 100.0,
                    'blink_rate': float(blink_count),
                    'blink_consistency': 1.0,
                    'eye_openness': eye_openness / 100.0,
                    'mouth_openness': 0.0,
                    'face_detected': face_found,
                    'primary_indicator': dominant,
                    'gambling_risk_score': gambling_risk_val,
                })
            except Exception as e:
                print(f"⚠️ store_face_analysis: {e}")

        _t2 = _time.time()
        print(f"⏱️ Frame: blink={int((_t1-_t0)*1000)}ms total={int((_t2-_t0)*1000)}ms face={'✅' if face_found else '❌'} people={result.get('people_count',0)}")
        return jsonify(result), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ===================== ANALYZE VOICE (from frontend spectral data) =====================
@app.route('/api/analyze/voice', methods=['POST'])
def analyze_voice():
    """Frontend sends { rms, clarity, speech_rate_label, syllables_per_sec, session_id }."""
    try:
        data = request.get_json(silent=True) or {}
        rms = float(data.get('rms', 0))
        clarity = int(data.get('clarity', 0))
        speech_rate_label = data.get('speech_rate_label', 'Нет звука')
        syllables_per_sec = float(data.get('syllables_per_sec', 0))
        session_id = data.get('session_id')

        # Stress: higher RMS + faster speech = more stress
        stress_rms = min(50, int(round(rms * 200)))  # 0-50 from volume
        stress_rate = min(50, int(round(syllables_per_sec * 7)))  # 0-50 from speech speed
        stress = min(100, stress_rms + stress_rate)

        # Voice level label
        rms_pct = min(100, int(round(rms * 500)))
        if rms_pct < 15:
            quality = 'Тихий'
        elif rms_pct < 50:
            quality = 'Средний'
        else:
            quality = 'Громкий'

        result = {
            'stress_score': round(stress / 100.0, 2),
            'stress_percent': stress,
            'voice_quality': quality,
            'rms': rms,
            'clarity': clarity,
            'speech_rate_label': speech_rate_label,
            'syllables_per_sec': syllables_per_sec,
            'timestamp': datetime.now().isoformat(),
        }

        if session_id:
            try:
                import time
                _last_voice_store = getattr(analyze_voice, '_last_store_time', 0)
                now_ts = time.time()
                if now_ts - _last_voice_store >= 2.0:
                    analyze_voice._last_store_time = now_ts
                    db.store_voice_analysis(session_id, {
                        'stress_score': stress / 100.0,
                        'anxiety_score': 0.0,
                        'pitch_hz': 0.0,
                        'pitch_variation': 0.0,
                        'speech_rate_wpm': syllables_per_sec * 60,
                        'loudness_rms': rms,
                        'loudness_status': quality,
                        'voice_quality': quality,
                        'primary_indicator': speech_rate_label,
                    })
            except Exception as e:
                print(f"⚠️ store_voice_analysis: {e}")

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== ANALYZE AUDIO (base64 wav) =====================
@app.route('/api/analyze/audio', methods=['POST'])
def analyze_audio():
    try:
        data = request.get_json(silent=True) or {}
        audio_b64 = data.get('audio', '')
        session_id = data.get('session_id')

        if not audio_b64:
            return jsonify({'error': 'No audio data'}), 400
        if ',' in audio_b64:
            audio_b64 = audio_b64.split(',', 1)[1]

        audio_bytes = base64.b64decode(audio_b64)
        tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        tmp.write(audio_bytes)
        tmp.close()
        audio_path = tmp.name

        # Voice model (4 класса: neu, hap, ang, sad)
        vr = voice_pipe(audio_path)
        voice_pct = {x['label']: int(round(x['score'] * 100)) for x in vr}

        # Audio emotion model (7 классов)
        ar = audio_emotion_pipe(audio_path)
        audio_pct = {x['label']: int(round(x['score'] * 100)) for x in ar}
        audio_scores = {x['label']: float(x['score']) for x in ar}

        # Стресс = max(Angry, Fearful, Disgusted)
        stress = int(round(100 * max(
            audio_scores.get('Angry', 0),
            audio_scores.get('Fearful', 0),
            audio_scores.get('Disgusted', 0),
        )))

        dominant = max(audio_pct, key=audio_pct.get)

        result = {
            'voice_emotion_percent': voice_pct,
            'audio_emotion_percent': audio_pct,
            'stress_percent': stress,
            'dominant_emotion': dominant,
            'timestamp': datetime.now().isoformat(),
        }

        if session_id:
            try:
                db.store_voice_analysis(session_id, {
                    'stress_score': stress / 100.0,
                    'anxiety_score': 0.0,
                    'pitch_hz': 0.0,
                    'pitch_variation': 0.0,
                    'speech_rate_wpm': 0.0,
                    'loudness_rms': 0.0,
                    'loudness_status': 'normal',
                    'voice_quality': 'good',
                    'primary_indicator': dominant,
                })
            except Exception as e:
                print(f"⚠️ store_voice_analysis: {e}")

        os.remove(audio_path)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== SESSIONS =====================
@app.route('/api/sessions', methods=['POST'])
def create_session():
    try:
        data = request.get_json(silent=True) or {}
        sid = db.create_session(
            user_notes=data.get('user_notes', ''),
            environment=data.get('environment', 'local'),
        )
        return jsonify({'session_id': sid}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/end/<int:session_id>', methods=['POST'])
def end_session(session_id):
    try:
        db.end_session(session_id)
        # Clean up blink tracking for this session
        _blink_state.pop(str(session_id), None)
        _ear_history.pop(str(session_id), None)
        _emotion_ema.pop(str(session_id), None)
        _gambling_analyzers.pop(str(session_id), None)
        return jsonify({'status': 'ended', 'session_id': session_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    try:
        sessions = db.get_user_history(limit=100)
        return jsonify({'sessions': sessions, 'count': len(sessions)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/latest', methods=['GET'])
def get_latest_session():
    try:
        sessions = db.get_user_history(limit=1)
        if not sessions:
            return jsonify({'session': None}), 200
        summary = db.get_session_summary(sessions[0]['id'])
        return jsonify({'session': summary}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/recent', methods=['GET'])
def get_recent_sessions():
    """Return recent sessions as array with quick stats."""
    try:
        sessions = db.get_user_history(limit=50)
        # Enrich each session with quick stats
        for sess in sessions:
            try:
                qs = db.get_session_quick_stats(sess['id'])
                sess['stats'] = qs
            except Exception:
                sess['stats'] = {}
        return jsonify(sessions), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session_detail(session_id):
    try:
        summary = db.get_session_summary(session_id)
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== STATISTICS =====================
@app.route('/api/statistics/session/<int:session_id>', methods=['GET'])
def get_session_statistics(session_id):
    try:
        stats = db.get_session_statistics(session_id)
        return jsonify({'session_id': session_id, **stats}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics/timerange', methods=['GET'])
def get_statistics_timerange():
    """Статистика за последние N дней (по умолчанию 7).
    Возвращает: кол-во сессий, средний % усталости лица, средний % стресса голоса,
    время последней сессии, все анализы по каждой сессии."""
    try:
        days = int(request.args.get('days', 7))
        since = (datetime.now() - timedelta(days=days)).isoformat()

        all_sessions = db.get_user_history(limit=10000)
        sessions = [s for s in all_sessions if s.get('start_time', '') >= since]
        sids = [s['id'] for s in sessions]

        face_vals = []
        voice_vals = []
        analyses = []

        for sid in sids:
            stat = db.get_session_statistics(sid)
            if stat.get('face') and stat['face'].get('avg_fatigue') is not None:
                face_vals.append(stat['face']['avg_fatigue'] * 100)
            if stat.get('voice') and stat['voice'].get('avg_stress') is not None:
                voice_vals.append(stat['voice']['avg_stress'] * 100)

            summary = db.get_session_summary(sid)
            analyses.append({
                'session_id': sid,
                'start_time': summary.get('session', {}).get('start_time'),
                'face_analysis': summary.get('face_analysis', []),
                'voice_analysis': summary.get('voice_analysis', []),
            })

        avg_face = int(round(np.mean(face_vals))) if face_vals else 0
        avg_voice = int(round(np.mean(voice_vals))) if voice_vals else 0
        last_time = sessions[0]['start_time'] if sessions else None

        return jsonify({
            'timerange_days': days,
            'sessions_count': len(sessions),
            'avg_face_fatigue_percent': avg_face,
            'avg_voice_stress_percent': avg_voice,
            'last_session_time': last_time,
            'sessions': sessions,
            'analyses': analyses,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== METRICS SUMMARY =====================
@app.route('/api/metrics/summary', methods=['GET'])
def get_metrics_summary():
    """Aggregated metrics from last N sessions for the Metrics page."""
    try:
        limit = int(request.args.get('limit', 10))
        data = db.get_aggregated_metrics(limit)
        face = data.get('face', {})
        voice = data.get('voice', {})
        eye_vals = data.get('face_eye_values', [])
        stress_vals = data.get('voice_stress_values', [])

        total_face = int(face.get('total', 0) or 0)
        face_detected = int(face.get('detected', 0) or 0)

        # Eye Contact %
        eye_contact = round(face_detected / total_face * 100) if total_face > 0 else 0

        # Smile Detection %
        happy_count = int(face.get('happy', 0) or 0)
        smile_pct = round(happy_count / total_face * 100) if total_face > 0 else 0

        # Voice Clarity (inverse of stress)
        avg_stress = float(voice.get('avg_stress', 0) or 0)
        voice_clarity = max(0, min(100, round((1 - avg_stress) * 100)))

        # Voice Tone (from loudness)
        avg_loudness = float(voice.get('avg_loudness', 0) or 0)
        voice_tone = max(0, min(100, round(avg_loudness * 800)))

        # Voice Consistency (from stress stability)
        if len(stress_vals) > 1:
            voice_consistency = max(0, min(100, round((1 - float(np.std(stress_vals)) * 3) * 100)))
        else:
            voice_consistency = 85 if stress_vals else 0

        # Voice Speed (placeholder based on measurement count)
        total_voice = int(voice.get('total', 0) or 0)
        voice_speed = 75 if total_voice > 5 else (50 if total_voice > 0 else 0)

        # Respiration Stability (from eye openness consistency)
        if len(eye_vals) > 1:
            resp_stability = max(0, min(100, round((1 - float(np.std(eye_vals)) * 3) * 100)))
        else:
            resp_stability = 0

        # Speech Rate label
        if avg_loudness > 0.15:
            speech_rate = 'Быстрый'
        elif avg_loudness > 0.06:
            speech_rate = 'Средний'
        elif avg_loudness > 0.02:
            speech_rate = 'Спокойный'
        else:
            speech_rate = '—'

        # Emotion distribution for donut chart
        emotions = {}
        emotion_map = {
            'neutral': 'Спокойный', 'happy': 'Счастливый', 'angry': 'Злой',
            'sad': 'Грустный', 'surprise': 'Удивлённый', 'other_em': 'Другое'
        }
        if total_face > 0:
            for key, label in emotion_map.items():
                cnt = int(face.get(key, 0) or 0)
                pct = round(cnt / total_face * 100)
                if pct > 0:
                    emotions[label] = pct
            # Merge disgust/fear/contempt into 'Другое'
            extra = sum(int(face.get(k, 0) or 0) for k in ('disgust', 'fear', 'contempt'))
            if extra > 0:
                extra_pct = round(extra / total_face * 100)
                emotions['Другое'] = emotions.get('Другое', 0) + extra_pct

        return jsonify({
            'face_emotions': emotions,
            'voice_metrics': {
                'clarity': voice_clarity, 'speed': voice_speed,
                'tone': voice_tone, 'consistency': voice_consistency,
            },
            'eye_contact': eye_contact,
            'smile_detection': smile_pct,
            'voice_clarity': voice_clarity,
            'speech_rate': speech_rate,
            'respiration_stability': resp_stability,
            'total_face_measurements': total_face,
            'total_voice_measurements': total_voice,
            'sessions_count': data.get('sessions_count', 0),
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ===================== HEALTH / STATUS =====================
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0',
        'service': 'wellbeing-monitoring-api',
    }), 200


@app.route('/api/status', methods=['GET'])
def system_status():
    return jsonify({
        'status': 'running',
        'database_available': True,
        'timestamp': datetime.now().isoformat(),
    }), 200


# ===================== KNOWN FACES / FACE RECOGNITION =====================
# In-memory cache of known face embeddings for fast matching
# _known_faces_cache initialized at top of file (line ~67)
_face_recognition_model = 'Facenet'  # DeepFace model for embeddings (compact + accurate)
_face_recognition_threshold = 0.55   # Cosine distance threshold — lower = stricter

def _load_known_faces_cache():
    """Load known faces from DB into memory for fast recognition."""
    global _known_faces_cache
    try:
        faces = db.get_known_faces()
        _known_faces_cache = []
        for f in faces:
            _known_faces_cache.append({
                'id': f['id'],
                'name': f['name'],
                'embedding': np.array(f['embedding'], dtype=np.float32),
            })
        print(f"✅ Known faces cache loaded: {len(_known_faces_cache)} faces")
    except Exception as e:
        print(f"⚠️ Failed to load known faces cache: {e}")
        _known_faces_cache = []

def _get_face_embedding(frame_bgr):
    """Extract face embedding from a BGR frame using DeepFace.
    Returns: (embedding_list, face_crop_b64) or (None, None)"""
    if not DEEPFACE_AVAILABLE:
        return None, None
    try:
        results = DeepFace.represent(
            img_path=frame_bgr,
            model_name=_face_recognition_model,
            enforce_detection=True,
            detector_backend='opencv',
        )
        if results and len(results) > 0:
            embedding = results[0]['embedding']
            # Get face area for thumbnail
            facial_area = results[0].get('facial_area', {})
            x = facial_area.get('x', 0)
            y = facial_area.get('y', 0)
            w = facial_area.get('w', frame_bgr.shape[1])
            h = facial_area.get('h', frame_bgr.shape[0])
            # Crop face for thumbnail
            face_crop = frame_bgr[max(0,y):min(frame_bgr.shape[0],y+h),
                                   max(0,x):min(frame_bgr.shape[1],x+w)]
            if face_crop.size > 0:
                face_crop_resized = cv2.resize(face_crop, (120, 120))
                _, buf = cv2.imencode('.jpg', face_crop_resized, [cv2.IMWRITE_JPEG_QUALITY, 80])
                face_b64 = base64.b64encode(buf).decode('utf-8')
            else:
                face_b64 = ''
            return embedding, face_b64
        return None, None
    except Exception as e:
        print(f"⚠️ Face embedding extraction failed: {e}")
        return None, None

def _recognize_face(embedding):
    """Match a face embedding against known faces.
    Returns: { id, name, distance } or None"""
    global _known_faces_cache
    if _known_faces_cache is None:
        _load_known_faces_cache()
    if not _known_faces_cache:
        return None
    emb = np.array(embedding, dtype=np.float32)
    # Normalize for cosine similarity
    emb_norm = emb / (np.linalg.norm(emb) + 1e-10)
    best_match = None
    best_distance = float('inf')
    for known in _known_faces_cache:
        known_norm = known['embedding'] / (np.linalg.norm(known['embedding']) + 1e-10)
        # Cosine distance = 1 - cosine_similarity
        cos_sim = np.dot(emb_norm, known_norm)
        distance = 1.0 - cos_sim
        if distance < best_distance:
            best_distance = distance
            best_match = known
    if best_match and best_distance < _face_recognition_threshold:
        return {
            'id': best_match['id'],
            'name': best_match['name'],
            'distance': round(float(best_distance), 4),
            'confidence': round(float(1.0 - best_distance) * 100, 1),
        }
    return None


@app.route('/api/faces/register', methods=['POST'])
def register_face():
    """Register a new face.
    Input: { image: base64, name: string }
    Scans the face, extracts embedding, stores in DB."""
    try:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get('image', '')
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'error': 'Имя не указано'}), 400
        if not image_b64:
            return jsonify({'error': 'Нет изображения'}), 400
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        img_bytes = base64.b64decode(image_b64)
        arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'error': 'Не удалось декодировать изображение'}), 400

        embedding, thumbnail = _get_face_embedding(frame)
        if embedding is None:
            return jsonify({'error': 'Лицо не обнаружено. Убедитесь, что лицо хорошо видно в камере.'}), 400

        # Check if this face already exists
        match = _recognize_face(embedding)
        if match and match['confidence'] > 80:
            return jsonify({
                'error': f'Это лицо уже зарегистрировано как "{match["name"]}" (совпадение {match["confidence"]}%)',
                'existing_name': match['name'],
                'existing_id': match['id'],
            }), 409

        face_id = db.add_known_face(name, embedding, thumbnail)
        # Refresh cache
        _load_known_faces_cache()

        return jsonify({
            'id': face_id,
            'name': name,
            'thumbnail': thumbnail,
            'message': f'Лицо "{name}" успешно зарегистрировано',
        }), 201
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/faces', methods=['GET'])
def list_faces():
    """List all registered faces."""
    try:
        faces = db.get_known_faces()
        result = []
        for f in faces:
            result.append({
                'id': f['id'],
                'name': f['name'],
                'thumbnail': f.get('thumbnail', ''),
                'created_at': f.get('created_at', ''),
            })
        return jsonify({'faces': result, 'count': len(result)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/faces/<int:face_id>', methods=['DELETE'])
def delete_face(face_id):
    """Delete a registered face."""
    try:
        deleted = db.delete_known_face(face_id)
        if deleted:
            _load_known_faces_cache()
            return jsonify({'message': 'Лицо удалено', 'id': face_id}), 200
        return jsonify({'error': 'Лицо не найдено'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/faces/recognize', methods=['POST'])
def recognize_face_endpoint():
    """Recognize a face from an image.
    Input: { image: base64 }
    Returns: matched person or null."""
    try:
        data = request.get_json(silent=True) or {}
        image_b64 = data.get('image', '')
        if not image_b64:
            return jsonify({'error': 'Нет изображения'}), 400
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]

        img_bytes = base64.b64decode(image_b64)
        arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'error': 'Не удалось декодировать изображение'}), 400

        embedding, _ = _get_face_embedding(frame)
        if embedding is None:
            return jsonify({'recognized': False, 'message': 'Лицо не обнаружено'}), 200

        match = _recognize_face(embedding)
        if match:
            return jsonify({
                'recognized': True,
                'person': match,
            }), 200
        else:
            return jsonify({'recognized': False, 'message': 'Лицо не распознано'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== GAMBLING ANALYSIS ENDPOINTS =====================

def _get_gambling_analyzer(session_id):
    """Get or create gambling analyzer for session."""
    sid = str(session_id) if session_id else '_global'
    if sid not in _gambling_analyzers:
        _gambling_analyzers[sid] = GamblingAnalyzer(fps=7.0)
    return _gambling_analyzers[sid]


@app.route('/api/gambling/status', methods=['GET'])
def gambling_status():
    """Get current gambling addiction risk status for session."""
    try:
        session_id = request.args.get('session_id')
        analyzer = _get_gambling_analyzer(session_id)
        result = analyzer._build_result()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/gambling/summary', methods=['GET'])
def gambling_summary():
    """Get gambling analysis summary for session."""
    try:
        session_id = request.args.get('session_id')
        analyzer = _get_gambling_analyzer(session_id)
        summary = analyzer.get_summary()
        return jsonify(summary), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== LSTM PREDICTION ENDPOINTS =====================

def _get_lstm_predictor(session_id):
    """Get or create LSTM predictor for session."""
    sid = str(session_id) if session_id else '_global'
    if sid not in _lstm_predictors:
        _lstm_predictors[sid] = LSTMPredictor(sequence_length=10)
    return _lstm_predictors[sid]


@app.route('/api/lstm/predict', methods=['POST'])
def lstm_predict():
    """
    Add data point and get LSTM prediction.
    POST: { session_id, fatigue_score, stress_score, anxiety_score,
            blink_rate_score, mouth_tension, head_velocity, eye_fixation, self_touching }
    """
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get('session_id')
        
        fatigue = float(data.get('fatigue_score', 0))
        stress = float(data.get('stress_score', 0))
        anxiety = float(data.get('anxiety_score', 0))
        blink_rate_score = float(data.get('blink_rate_score', 0))
        mouth_tension = float(data.get('mouth_tension', 0))
        head_velocity = float(data.get('head_velocity', 0))
        eye_fixation = float(data.get('eye_fixation', 0))
        self_touching = float(data.get('self_touching', 0))
        
        predictor = _get_lstm_predictor(session_id)
        result = predictor.add_data_point(fatigue, stress, anxiety,
                                          blink_rate_score, mouth_tension,
                                          head_velocity, eye_fixation, self_touching)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lstm/statistics', methods=['GET'])
def lstm_statistics():
    """Get LSTM statistics for session."""
    try:
        session_id = request.args.get('session_id')
        predictor = _get_lstm_predictor(session_id)
        stats = predictor.get_statistics()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lstm/train', methods=['POST'])
def lstm_train():
    """Trigger online training for session."""
    try:
        data = request.get_json(silent=True) or {}
        session_id = data.get('session_id')
        epochs = int(data.get('epochs', 30))
        
        predictor = _get_lstm_predictor(session_id)
        predictor.train_online(epochs=epochs)
        
        return jsonify({'status': 'ok', 'message': 'Обучение завершено'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== EASY MONEY ENDPOINTS =====================

@app.route('/api/easymoney/health', methods=['GET'])
def em_health():
    """Easy Money ML backend health check."""
    return jsonify({
        'status': 'ok',
        'version': 'v3-integrated',
        'features': len(EM_FEATURE_NAMES),
        'training_samples': 5000,
        'models': {
            'rf_auc': round(_em_rf_auc, 4),
            'gb_auc': round(_em_gb_auc, 4),
            'ens_auc': round(_em_ens_auc, 4),
        }
    })


@app.route('/api/easymoney/predict', methods=['POST'])
def em_predict():
    """Predict gambling addiction risk from behavioral features."""
    try:
        data = request.json
        features = _em_extract_features(data)
        features_s = _em_scaler.transform(features)

        rf_score = float(_em_rf.predict_proba(features_s)[0][1])
        gb_score = float(_em_gb.predict_proba(features_s)[0][1])
        ens_score = rf_score * 0.6 + gb_score * 0.4

        risk_pct = round(ens_score * 100)
        level = 'HIGH' if risk_pct >= 70 else 'MEDIUM' if risk_pct >= 40 else 'LOW'

        # Top-3 risky features
        fv = features[0]
        normed = fv / (np.array([6, 6, 10, 15, 180, 8, 1, 8, 8, 6, 1, 1, 5, 30]) + 1e-9)
        top_idx = np.argsort(normed)[::-1][:3]
        top_features = [EM_FEATURE_NAMES[i] for i in top_idx]

        return jsonify({
            'riskScore': risk_pct,
            'riskLevel': level,
            'rfScore': round(rf_score * 100),
            'gbScore': round(gb_score * 100),
            'ensembleScore': round(ens_score * 100),
            'topRiskFactors': top_features,
            'model': 'RF+GB Calibrated Ensemble v3 (integrated)'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/easymoney/feature_importance', methods=['GET'])
def em_feature_importance():
    """Get feature importance from Random Forest model."""
    return jsonify({
        name: round(float(imp), 4)
        for name, imp in zip(EM_FEATURE_NAMES, _em_rf_base.feature_importances_)
    })


@app.route('/api/easymoney/batch_predict', methods=['POST'])
def em_batch_predict():
    """Batch predict gambling risk for multiple sessions."""
    try:
        sessions = request.json
        results = []
        for session in sessions:
            features_s = _em_scaler.transform(_em_extract_features(session))
            score = (
                float(_em_rf.predict_proba(features_s)[0][1]) * 0.6 +
                float(_em_gb.predict_proba(features_s)[0][1]) * 0.4
            )
            results.append({
                'sessionId': session.get('sessionId', 'unknown'),
                'riskScore': round(score * 100),
                'riskLevel': 'HIGH' if score >= 0.7 else 'MEDIUM' if score >= 0.4 else 'LOW'
            })
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/easymoney/combined_analysis', methods=['POST'])
def em_combined_analysis():
    """
    Combined analysis: merge face-based gambling data with behavioral data.
    Accepts both facial analysis data (from Bereke AI camera) and
    behavioral data (from Easy Money tracker).
    """
    try:
        data = request.json or {}
        session_id = data.get('session_id')

        # 1. Face-based gambling analysis (from Bereke)
        face_risk = 0
        gambling_analyzer = _get_gambling_analyzer(session_id)
        face_result = gambling_analyzer._build_result()
        face_risk = face_result.get('addiction_risk_score', 0) * 100

        # 2. Behavioral ML prediction (from EasyMoney tracker)
        behavioral_data = data.get('behavioral', {})
        behavior_risk = 0
        if behavioral_data:
            features = _em_extract_features(behavioral_data)
            features_s = _em_scaler.transform(features)
            rf_score = float(_em_rf.predict_proba(features_s)[0][1])
            gb_score = float(_em_gb.predict_proba(features_s)[0][1])
            behavior_risk = (rf_score * 0.6 + gb_score * 0.4) * 100

        # 3. Combined score (weighted: 40% face, 60% behavioral)
        combined_risk = face_risk * 0.4 + behavior_risk * 0.6
        level = 'HIGH' if combined_risk >= 70 else 'MEDIUM' if combined_risk >= 40 else 'LOW'

        return jsonify({
            'combinedRiskScore': round(combined_risk),
            'faceRiskScore': round(face_risk),
            'behaviorRiskScore': round(behavior_risk),
            'riskLevel': level,
            'faceAnalysis': face_result,
            'model': 'Bereke+EasyMoney Combined v1'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ===================== FRONTEND SERVING =====================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    try:
        root = os.path.abspath(os.path.dirname(__file__))
        safe = os.path.normpath(path)
        target = os.path.join(root, safe)
        if path and os.path.isfile(target):
            return send_from_directory(root, safe)
        return send_from_directory(root, 'index.html')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===================== ERROR HANDLERS =====================
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'status': 404}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'status': 500}), 500


# ===================== MAIN =====================
if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   Bereke AI - REST API Backend                         ║
    ║   http://localhost:5000                                   ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
