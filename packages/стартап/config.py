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

# ============= BREATHING ANALYSIS THRESHOLDS =============
NORMAL_BREATHING_RATE_MIN = 12  # Breaths per minute
NORMAL_BREATHING_RATE_MAX = 20
FAST_BREATHING_THRESHOLD = 25  # Indicates stress/anxiety

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
    'breathing': [
        "🫁 Breathing patterns appear irregular.",
        "🌬️  Try the 4-4-4 breathing technique: inhale for 4, hold for 4, exhale for 4.",
        "⚖️  Normalize your breathing to calm your nervous system.",
    ],
    'normal': [
        "✅ All systems normal. You're doing well!",
        "👍 No significant stress or fatigue detected.",
        "😊 Keep maintaining this balanced state.",
    ]
}

# ============= DEBUG SETTINGS =============
DEBUG_MODE = False  # Set to True for verbose logging
SHOW_FACE_LANDMARKS = True  # Draw landmarks on video
VISUALIZE_AUDIO = False  # Display audio waveforms
