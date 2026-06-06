# 🏥 AI-Based Non-Medical Wellbeing Monitoring System

**A Python-based wellness monitoring system that analyzes facial expressions, voice patterns, and breathing to detect signs of stress and fatigue.**

⚠️ **DISCLAIMER: This system is for WELLNESS insights only, NOT for medical diagnosis. Always consult healthcare professionals for medical concerns.**

---

## 📋 Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Quick Start](#quick-start)
6. [How It Works](#how-it-works)
7. [File Structure](#file-structure)
8. [Configuration](#configuration)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)
11. [Future Improvements](#future-improvements)

---

## ✨ Features

### Core Capabilities
- ✅ **Real-time facial analysis** using MediaPipe for emotional state detection
- ✅ **Voice analysis** to detect stress and anxiety through pitch, speed, and loudness
- ✅ **Breathing pattern analysis** to identify irregular respiration
- ✅ **Fatigue detection** through eye closure and blink patterns
- ✅ **Non-medical recommendations** based on detected patterns
- ✅ **Session tracking** and trend analysis

### What It Detects
- 👁️ **Fatigue**: Eye closure duration, blink rate
- 😰 **Stress**: Voice pitch elevation, speech rate changes
- 😟 **Anxiety**: Voice variation, breathing irregularity
- 🫁 **Abnormal breathing**: Rapid or irregular respiration

### Output Examples

**When stress is detected:**
```
"😰 Signs of elevated stress detected.
🧘 Try deep breathing exercises (4-7-8 technique).
💪 Take a short walk or stretch to reduce tension."
```

**When all systems are normal:**
```
"✅ All systems normal. You're doing well!
👍 No significant stress or fatigue detected.
😊 Keep maintaining this balanced state."
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Main Application (main.py)             │
│  - Real-time video/audio capture        │
│  - Coordinate all analyzers             │
└──────────┬──────────────────────────────┘
           │
    ┌──────┴───────┬────────────┬──────────┐
    │              │            │          │
    ▼              ▼            ▼          ▼
┌────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│  Face  │  │  Voice   │  │ Breathing│  │WellbeingMon  │
│Analyzer│  │Analyzer  │  │Analyzer  │  │itor (Coord)  │
└────────┘  └──────────┘  └──────────┘  └──────────────┘

Data Flow:
📷 Camera → Face Analyzer → Fatigue Score
🎤 Microphone → Voice Analyzer → Stress + Anxiety Scores
🎤 Audio → Breathing Analyzer → Breathing Rate
         ↓
   Wellbeing Monitor (Combines all)
         ↓
💡 Recommendations & Report
```

### Module Responsibilities

| Module | Purpose | Key Outputs |
|--------|---------|-------------|
| `face_analyzer.py` | Facial feature analysis | Fatigue score, eye closure, mouth openness |
| `voice_analyzer.py` | Voice pattern analysis | Stress score, anxiety score, pitch, speech rate |
| `breathing_analyzer.py` | Respiration analysis | Breathing rate (BPM), irregularity |
| `wellbeing_monitor.py` | Aggregation & decisions | Overall concern score, recommendations |
| `config.py` | Configuration | Thresholds, parameters, messages |
| `main.py` | Entry point | Real-time monitoring loop |

---

## 📦 Requirements

### System Requirements
- **Python**: 3.8 or higher
- **WebCam**: Integrated or external camera
- **Microphone**: (Optional) For full audio analysis
- **OS**: Windows, macOS, or Linux

### Python Dependencies
```
opencv-python==4.8.1.78        # Video capture and image processing
mediapipe==0.10.5               # Face landmark detection
librosa==0.10.0                 # Audio analysis
numpy==1.24.3                   # Numerical operations
scipy==1.11.4                   # Signal processing
pyaudio                         # Microphone input (optional)
```

---

## 🚀 Installation

### Step 1: Clone Repository
```bash
cd ~/Desktop/стартап
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install PyAudio (for audio capture)
**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

Or download pre-built wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)

---

## ⚡ Quick Start

### Run the System
```bash
python main.py
```

### Expected Output
```
╔════════════════════════════════════════════════════════════╗
║    AI-BASED NON-MEDICAL WELLBEING MONITORING SYSTEM       ║
║                     MVP v1.0                              ║
╚════════════════════════════════════════════════════════════╝

🔧 Initializing Wellbeing Monitoring System...
✅ System initialized successfully!
📷 Camera: 640x480 @ 30 FPS
🎤 Audio: 16000 Hz

🔍 Starting 30-second monitoring session...
```

### Controls
- **`q` or `ESC`**: Exit monitoring
- **`s`**: Take snapshot
- **Video display**: Shows face landmarks and real-time analysis

---

## 🧠 How It Works

### 1. Face Analysis
**What it detects:**
- Eye aspect ratio (EAR) to determine if eyes are open/closed
- Blink frequency and duration
- Mouth movement patterns

**Formula:**
```
EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
where p1-p6 are eye landmark points
```

**Interpretation:**
- EAR < 0.2 → Eyes closed → Potential fatigue
- Low blink rate → Fatigue
- High blink rate → Alertness

### 2. Voice Analysis
**What it detects:**
- **Pitch** (fundamental frequency in Hz)
  - Normal: 80-200 Hz
  - Elevated: Indicates stress
- **Speech rate** (words per minute)
  - Normal: 120-160 WPM
  - Fast: >200 WPM indicates anxiety
  - Slow: <80 WPM indicates fatigue
- **Loudness** (RMS amplitude)
  - Quiet (<0.05): Fatigue or depression
  - Normal: 0.05-0.15
  - Loud (>0.15): Stress or intensity

**Method:**
- Uses librosa's pitch tracking (piptrack algorithm)
- Analyzes pitch variation for anxiety indicators
- Detects speech onsets for articulation rate

### 3. Breathing Analysis
**What it detects:**
- **Breathing rate** (breaths per minute)
  - Normal: 12-20 BPM
  - Elevated: >25 BPM (stress/anxiety)
- **Breathing regularity**: Variation in breath intervals
- **Irregular patterns**: Gasping, shallow breathing

**Method:**
- Extracts low-frequency energy from audio
- Detects peaks in respiratory signal
- Converts peak frequency to BPM

### 4. Aggregation & Scoring
**Overall Concern Score** (0-1):
```
Score = 0.25 × Fatigue + 0.30 × Stress + 0.25 × Anxiety + 0.20 × Breathing
```

**Interpretation:**
- < 0.40: Low concern ✅
- 0.40-0.60: Moderate concern ⚠️
- > 0.60: High concern 🚨

---

## 📁 File Structure

```
стартап/
├── main.py                    # Entry point - run this!
├── config.py                  # All configuration and thresholds
├── face_analyzer.py           # Facial expression analysis
├── voice_analyzer.py          # Voice and speech analysis
├── breathing_analyzer.py      # Respiration analysis
├── wellbeing_monitor.py       # Coordinator and recommendations
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## ⚙️ Configuration

Edit [config.py](config.py) to customize behavior:

### Monitoring Duration
```python
MONITORING_DURATION_SECONDS = 30  # Change to 60 for longer sessions
CHECK_INTERVAL_SECONDS = 5         # Analysis frequency
```

### Fatigue Thresholds
```python
EYE_ASPECT_RATIO_THRESHOLD = 0.2          # Lower = more closed eyes
EYE_ASPECT_RATIO_CONSEC_FRAMES = 10       # Frames to detect closure
```

### Stress/Anxiety Thresholds
```python
NORMAL_PITCH_MIN = 80
NORMAL_PITCH_MAX = 200
STRESSED_PITCH_INCREASE = 1.3              # 30% increase = stressed
```

### Concern Levels
```python
MILD_CONCERN_THRESHOLD = 0.4       # 0-1 scale
MODERATE_CONCERN_THRESHOLD = 0.6
HIGH_CONCERN_THRESHOLD = 0.8
```

### Custom Recommendations
```python
RECOMMENDATIONS = {
    'fatigue': [
        "Message 1",
        "Message 2",
        ...
    ],
    'stress': [...],
    'anxiety': [...],
    'breathing': [...],
    'normal': [...]
}
```

---

## 📊 Example Output

### Sample Console Report
```
============================================================
🏥 WELLBEING MONITORING REPORT
============================================================
Time: 2026-02-10T15:30:45.123456

Overall Status: ⚠️ Moderate stress levels detected. Take action to address.
Concern Level: MODERATE
Primary Concern: stress

------------------------------------------------------------
📊 DETAILED METRICS:
------------------------------------------------------------

👁  Facial Analysis:
   Fatigue Level: LOW
   Fatigue Score: 0.15/1.0
   Eyes Status: OPEN
   Face Detected: Yes

🎤 Voice Analysis:
   Stress Level: MODERATE
   Stress Score: 0.52/1.0
   Anxiety Level: MODERATE
   Anxiety Score: 0.48/1.0
   Pitch: 145 Hz
   Speech Rate: 175 WPM
   Loudness: 0.12

🫁 Breathing Analysis:
   Breathing Status: FAST
   Breathing Rate: 28 BPM
   Irregularity: 0.34

------------------------------------------------------------
💡 RECOMMENDATIONS:
------------------------------------------------------------
1. 😰 Signs of elevated stress detected.
2. 🧘 Try deep breathing exercises (4-7-8 technique).
3. 🫁 Breathing patterns appear irregular.
4. 🌬️ Try the 4-4-4 breathing technique: inhale for 4, hold for 4, exhale for 4.

============================================================
⚕️  IMPORTANT DISCLAIMER:
============================================================
This system provides WELLNESS indicators only.
It is NOT a medical diagnostic tool.
If symptoms persist or worsen, consult a healthcare professional.
============================================================
```

---

## 🐛 Troubleshooting

### Issue: Camera not opening
**Solution:**
- Check camera is not in use by another app
- Try different `CAMERA_ID` in config.py (usually 0, 1, or 2)
- Test with: `python -c "import cv2; cv2.VideoCapture(0).isOpened()"`

### Issue: PyAudio installation fails
**Solution:**
- Audio is optional. System still works without it
- On macOS: `brew install portaudio` first
- On Linux: `sudo apt-get install portaudio19-dev`
- Try: `pip install --no-cache-dir pyaudio`

### Issue: Face landmarks not detected
**Solution:**
- Ensure good lighting
- Face should be 20-60 cm from camera
- Center face in frame
- Try adjusting `min_detection_confidence` in `face_analyzer.py`

### Issue: "No module named ..."
**Solution:**
```bash
pip install -r requirements.txt
```

### Issue: Slow performance
**Solution:**
- Reduce `FRAME_WIDTH` and `FRAME_HEIGHT` in config.py
- Increase `CHECK_INTERVAL_SECONDS`
- Close other applications using GPU

---

## 🔮 Future Improvements

### Phase 2 (Medium-term)
- [ ] Web UI dashboard with real-time charts
- [ ] Historical data storage (SQLite/PostgreSQL)
- [ ] Machine learning model for better stress prediction
- [ ] Multi-person monitoring
- [ ] Wearable device integration (heart rate, sleep data)

### Phase 3 (Advanced)
- [ ] Deep learning model (LSTM) for pattern prediction
- [ ] Integration with smart home systems
- [ ] Mobile app (iOS/Android)
- [ ] Longitudinal studies and personalized baselines
- [ ] Integration with meditation/wellness apps

### Technical Improvements
- [ ] GPU acceleration for faster processing
- [ ] Edge computing optimization
- [ ] Cloud integration for remote monitoring
- [ ] Data encryption and privacy compliance (GDPR, HIPAA)

---

## 📚 References

### Computer Vision
- [MediaPipe Face Mesh](https://mediapipe.dev/)
- [OpenCV Documentation](https://docs.opencv.org/)
- [Eye Aspect Ratio Method](https://www.researchgate.net/publication/265138866_Real_Time_Eye_Gaze_Tracking_with_3D_Deformable_Eye-Face_Model)

### Audio Processing
- [Librosa Documentation](https://librosa.org/)
- [Pitch Detection Methods](https://en.wikipedia.org/wiki/Pitch_detection_algorithm)
- [Speech Rate Analysis](https://www.semanticscholar.org/paper)

### Wellness Science
- [Stress and Voice Changes](https://www.ncbi.nlm.nih.gov/)
- [Facial Expression Recognition](https://arxiv.org/abs/2106.15573)
- [Respiration and Emotion](https://www.frontiersin.org/)

---

## 📝 License

This project is provided as an educational tool. Use responsibly and ethically.

## ⚠️ Important Notes

1. **NOT A MEDICAL DEVICE**: This system cannot diagnose, treat, or prevent medical conditions
2. **PRIVACY**: Use only with user consent. Don't store data without permission
3. **ACCURACY**: Ground-truth is limited. Use as a wellness tool, not diagnostic
4. **BIAS**: May have variable accuracy across different demographics
5. **CONSULT PROFESSIONALS**: Always seek professional help for health concerns

---

## 🤝 Contributing

Want to improve this system?

1. Test and report issues
2. Suggest features or improvements
3. Optimize code for performance
4. Add support for new sensors

---

## 📧 Support

For issues or questions:
1. Check the Troubleshooting section
2. Review code comments
3. Consult the architecture documentation

---

**Happy monitoring! Stay well! 🌟**
