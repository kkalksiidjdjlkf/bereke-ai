# Configuration constants for the Wellbeing Monitoring System
# This file centralizes all configurable parameters

# ============= CAMERA SETTINGS =============
CAMERA_ID = 0  # Default camera (0 = built-in webcam)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# ============= AUDIO SETTINGS =============
SAMPLE_RATE = 16000  # Hz - Standard for speech analysis
CHUNK_SIZE = 2048  # Samples per audio chunk
AUDIO_DURATION_SECONDS = 2  # How long to record for analysis

# ============= FACE ANALYSIS THRESHOLDS =============
# Eye aspect ratio thresholds (for fatigue detection)
EYE_ASPECT_RATIO_THRESHOLD = 0.2  # Lower = more closed eyes = fatigue
EYE_ASPECT_RATIO_CONSEC_FRAMES = 10  # Frames to detect eye closure

# Mouth aspect ratio (for stress/emotion)
MOUTH_ASPECT_RATIO_THRESHOLD = 0.5

# ============= VOICE ANALYSIS THRESHOLDS =============
# Pitch range for stress detection (Hz)
NORMAL_PITCH_MIN = 80  # Male baseline
NORMAL_PITCH_MAX = 200  # Female baseline
STRESSED_PITCH_INCREASE = 1.3  # 30% increase = stressed

# Speech speed (phonemes per second)
NORMAL_SPEECH_RATE = 150  # Words per minute = ~2.5 per second
FAST_SPEECH_RATE = 200  # Indicates stress/anxiety

# Loudness (RMS amplitude)
QUIET_THRESHOLD = 0.05
LOUD_THRESHOLD = 0.2

# ============= RECOMMENDATION SYSTEM =============
# Stress/Fatigue score thresholds (0-1)
MILD_CONCERN_THRESHOLD = 0.4
MODERATE_CONCERN_THRESHOLD = 0.6
HIGH_CONCERN_THRESHOLD = 0.8

# Monitoring duration
MONITORING_DURATION_SECONDS = 30  # How long to monitor for MVP
CHECK_INTERVAL_SECONDS = 5  # How often to analyze in seconds

# ============= RECOMMENDATION MESSAGES =============
RECOMMENDATIONS = {
    'fatigue': [
        "👁  Fatigue patterns detected. Consider taking a short break.",
        "💤 Signs of drowziness. Try getting some fresh air or water.",
        "⚠️  High fatigue levels detected. Rest is recommended.",
    ],
    'stress': [
        "😰 Signs of elevated stress detected.",
        "🧘 Try deep breathing exercises (4-7-8 technique).",
        "💪 Take a short walk or stretch to reduce tension.",
    ],
    'anxiety': [
        "📊 Voice patterns suggest possible anxiety.",
        "🎵 Try listening to calming music or white noise.",
        "⏸️  Take a moment to pause and reset.",
    ],
    'normal': [
        "✅ All systems normal. You're doing well!",
        "👍 No significant stress or fatigue detected.",
        "😊 Keep maintaining this balanced state.",
    ]
}

# ============= GAMBLING ADDICTION ANALYSIS =============
# Blink Rate thresholds (blinks/min)
GAMBLING_BLINK_TRANCE = 10       # Below = trance / hyperfocus
GAMBLING_BLINK_NORMAL_MIN = 15   # Normal range start
GAMBLING_BLINK_NORMAL_MAX = 20   # Normal range end
GAMBLING_BLINK_PANIC = 25        # Above = panic / tilt

# Mouth Tension (normalized by outer eye distance D)
GAMBLING_MOUTH_TENSION_THRESHOLD = 0.55   # Width < this = tension
GAMBLING_MOUTH_HEIGHT_THRESHOLD = 0.07    # Height < this = clenched

# Head Velocity (normalized px/sec)
GAMBLING_HEAD_VELOCITY_NORMAL = 0.08   # Below = calm
GAMBLING_HEAD_VELOCITY_IMPULSE = 0.30  # Above = impulsive

# Eye Fixation (gaze spread std)
GAMBLING_FIXATION_FULL = 0.005   # Below = total fixation
GAMBLING_FIXATION_THRESHOLD = 0.025  # Below = significant fixation

# Self-Touching (face area drop)
GAMBLING_SELF_TOUCH_DROP = 0.15  # Area drop > 15% = hand on face
GAMBLING_SELF_TOUCH_FLUCTUATION = 0.10  # Area std > 10% baseline = hand moving

# Risk zone boundaries (0-1 score)
GAMBLING_RISK_NORMAL = 0.20      # Below = normal
GAMBLING_RISK_ATTENTION = 0.45   # Below = attention
GAMBLING_RISK_WARNING = 0.70     # Below = warning, above = danger

# Feature weights for combined risk score
GAMBLING_WEIGHT_BLINK_RATE = 0.15
GAMBLING_WEIGHT_MOUTH_TENSION = 0.20
GAMBLING_WEIGHT_HEAD_VELOCITY = 0.20
GAMBLING_WEIGHT_EYE_FIXATION = 0.25  # Most important
GAMBLING_WEIGHT_SELF_TOUCHING = 0.20

# ============= DEBUG SETTINGS =============
DEBUG_MODE = False  # Set to True for verbose logging
SHOW_FACE_LANDMARKS = True  # Draw landmarks on video
VISUALIZE_AUDIO = False  # Display audio waveforms
