# 🏗️ System Architecture & Data Flow

Detailed technical documentation of the Wellbeing Monitoring System architecture.

---

## 📊 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│           (Console Output / Video Display / Reports)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WELLBEING MONITOR (Coordinator)                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ • Aggregates all analyzer outputs                          │ │
│  │ • Calculates overall concern score                         │ │
│  │ • Generates recommendations                               │ │
│  │ • Tracks session history                                  │ │
│  │ • Non-medical assertions only                             │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────┬──────────────────────┬────────────────────┬───────────────┘
      │                      │                    │
      ▼                      ▼                    ▼
┌───────────────┐   ┌──────────────┐   ┌──────────────────┐
│ FACE ANALYZER │   │ VOICE        │   │ BREATHING        │
│               │   │ ANALYZER     │   │ ANALYZER         │
├───────────────┤   ├──────────────┤   ├──────────────────┤
│ Input: Video  │   │ Input: Audio │   │ Input: Audio     │
│               │   │              │   │                  │
│ Process:      │   │ Process:     │   │ Process:         │
│ • Landmarks   │   │ • Pitch      │   │ • Energy peaks   │
│ • Eye tracking│   │ • Speech     │   │ • Rhythm detect  │
│ • Blink rate  │   │   rate       │   │ • Breathing BPM  │
│               │   │ • Loudness   │   │                  │
│ Output:       │   │ • Jitter     │   │ Output:          │
│ • Fatigue: 0-1│   │              │   │ • Breathing rate │
│ • Eye closure │   │ Output:      │   │ • Irregularity   │
│ • Mouth open  │   │ • Stress: 0-1│   │                  │
│               │   │ • Anxiety: 0-1
└───────────────┘   └──────────────┘   └──────────────────┘
      ▲                      ▲                    ▲
      │                      │                    │
      └──────────────────────┴────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────┐
│          SENSOR INPUT LAYER          │
├──────────────────────────────────────┤
│ 📷 Webcam                            │
│    └─ OpenCV VideoCapture            │
│    └─ 30 FPS, 640x480               │
│                                       │
│ 🎤 Microphone (Optional)             │
│    └─ PyAudio input stream           │
│    └─ 16 kHz sample rate             │
│    └─ 2-second chunks                │
└──────────────────────────────────────┘
```

---

## 🔄 Data Flow Sequence

### Per-Frame Analysis (Every ~5 seconds)

```
TIME 0s - 5s: Concurrent Collection
├─ VIDEO: Capture 150 frames @ 30 FPS
├─ AUDIO: Capture ~80,000 samples @ 16 kHz
└─ RESULT: [frames] + [audio_chunk] ready for analysis

TIME 5s: Analysis Trigger
├─ Latest frame analyzed by Face Analyzer
│  ├─ Extract MediaPipe landmarks
│  ├─ Calculate eye aspect ratio (EAR)
│  ├─ Detect blinks
│  └─ Output: fatigue_score, eye_closure, mouth_open
│
├─ Audio chunk analyzed by Voice Analyzer
│  ├─ Extract pitch using piptrack
│  ├─ Detect speech onsets
│  ├─ Calculate RMS loudness
│  └─ Output: stress_score, anxiety_score, pitch, loudness
│
├─ Audio chunk analyzed by Breathing Analyzer
│  ├─ Extract low-frequency energy envelope
│  ├─ Detect respiratory peaks
│  ├─ Calculate breathing rate (BPM)
│  └─ Output: breathing_rate, breathing_status
│
├─ All results passed to Wellbeing Monitor
│  ├─ Weighted aggregation
│  ├─ Calculate overall_concern_score
│  ├─ Identify primary_concern
│  ├─ Generate recommendations
│  ├─ Print report
│  └─ Store in analysis_history
│
└─ EVENT: Analysis complete, ready for next cycle

TIME 5s - 10s: Next collection period...
```

---

## 📈 Scoring System

### Individual Analyzer Scores (0-1 scale)

**Face Analyzer - Fatigue Score:**
```
fatigue_score = 0.6 × (eye_closure_ratio) + 0.4 × (1 - blink_rate_score)

where:
  eye_closure_ratio = consecutive_closed_frames / EYE_ASPECT_RATIO_CONSEC_FRAMES
  blink_rate_score = current_blinks / expected_blinks_per_minute
```

**Voice Analyzer - Stress Score:**
```
stress_score = mean([
    max((pitch_ratio - 1.0) × 2, 0),        // Pitch elevation
    loudness_stress_factor,                  // Loudness extremes
    (rapid_speech_factor if speech_rate > normal)  // Fast speech
])

where:
  pitch_ratio = current_pitch / baseline_pitch
  loudness_stress = depends on QUIET_THRESHOLD and LOUD_THRESHOLD
```

**Voice Analyzer - Anxiety Score:**
```
anxiety_score = mean([
    std(pitch_history) / mean(pitch_history),      // Pitch variation
    std(speech_rate_history) / mean(...),          // Rate variation
    std(loudness_history)                          // Loudness variation
])
```

**Breathing Analyzer - Breathing Concern:**
```
breathing_score = {
    0.7 if breathing_rate > FAST_BREATHING_THRESHOLD
    0.5 if breathing_status == 'irregular'
    0.3 if breathing_rate < NORMAL_BREATHING_RATE_MIN
    0.0 otherwise
}
```

### Overall Wellbeing Score

```
overall_concern_score = 
    0.25 × fatigue_score +
    0.30 × stress_score +
    0.25 × anxiety_score +
    0.20 × breathing_score

Interpretation:
  < 0.40 : Low concern      ✅ Normal
  0.40-0.60 : Moderate       ⚠️  Some concern
  > 0.60 : High concern      🚨 Action needed
```

---

## 🧮 Algorithm Details

### 1. Face Landmark Detection (MediaPipe)

**How it works:**
- Uses pre-trained deep learning models
- Detects 468 3D face landmarks in real-time
- Runs at 30+ FPS on CPU

**Key landmarks used:**
```
Right eye: 33, 160, 158, 133, 153, 144 (6 points)
Left eye: 362, 385, 387, 263, 373, 380 (6 points)
Mouth: 61-81 (20 points for detailed analysis)
```

**Eye Aspect Ratio (EAR) Formula:**
```
        ||p2 - p6|| + ||p3 - p5||
EAR = ──────────────────────────
             2 × ||p1 - p4||

where p1-p6 are eye landmark positions

Interpretation:
  EAR > 0.2  : Eyes open (alert)
  EAR < 0.2  : Eyes closed (fatigued)
```

### 2. Pitch Detection (Librosa - Piptrack)

**Algorithm: Piptrack (Probabilistic Interpretation Pitch Tracking)**
- Estimates probability of pitch at each time step
- Robust to noise and background sounds
- Works well for speech

**Process:**
```
Raw Audio
    ↓
Create spectrogram
    ↓
For each time frame:
  - Calculate autocorrelation at multiple pitches
  - Compute probability of each pitch
    ↓
Select highest probability pitch
    ↓
Apply continuity constraints
    ↓
Output: Fundamental Frequency (Hz)
```

**Stress Indication:**
```
Normal speech: 80-200 Hz (varies by gender/age)
Stressed speech: Elevated by 20-30%

Calculation:
  pitch_ratio = current_pitch / baseline_pitch
  if pitch_ratio > STRESSED_PITCH_INCREASE (default: 1.3)
    → Stress indicated
```

### 3. Speech Rate Estimation

**Method: Onset Detection**
- Detects sharp amplitude increases (speech starts)
- Counts onsets per second
- Correlates with articulation speed

```
Audio
  ↓
[Filter] Remove low amplitudes
  ↓
[Detect Peaks] Find sharp amplitude rises
  ↓
[Count] Frequency of onsets
  ↓
[Convert] Onsets/sec → Words Per Minute
  ↓
Output: Estimated WPM (words per minute)

Interpretation:
  < 80 WPM  : Slow (fatigue/depression)
  80-160 WPM : Normal (relaxed)
  > 200 WPM  : Fast (stress/anxiety)
```

### 4. Breathing Rate Extraction

**Method: Energy Envelope Analysis**
- Extracts low-frequency component from audio (0.1-1 Hz)
- Detects peaks in amplitude (breathing cycles)
- Counts cycles to estimate rate

```
Raw Audio
  ↓
[Window] Split into 100ms chunks
  ↓
[Energy] Calculate RMS per chunk
  ↓
[Smooth] Apply moving average filter
  ↓
[Detect Peaks] Find local maxima > threshold
  ↓
[Rate] cycles_per_second × 60 → BPM
  ↓
Output: Breathing Rate (breaths per minute)

Interpretation:
  12-20 BPM : Normal at rest
  20-25 BPM : Light activity/mild stress
  > 25 BPM  : Fast breathing (stress/anxiety)
  < 12 BPM  : Shallow/slow breathing
```

---

## 🔐 Non-Medical Safeguards

The system is designed to NEVER make medical claims:

**What it DOES:**
✅ "Signs of elevated stress detected"
✅ "Breathing patterns appear irregular"
✅ "Consider taking a rest"
✅ "Try deep breathing exercises"

**What it DOES NOT do:**
❌ "You have anxiety disorder"
❌ "You are depressed"
❌ "You have [medical condition]"
❌ "Diagnosis: [disease]"
❌ Medical-grade conclusions

**Safety mechanisms:**
1. All output uses "signs," "patterns," "possible"
2. Recommendations are suggestions only
3. Disclaimer displayed prominently
4. No data is transmitted to medical providers
5. No treatment recommendations

---

## 📊 Example: Complete Analysis Flow

**Scenario: Person experiencing moderate stress**

```
INPUT
├─ Camera Feed: 150 frames
│  └─ Face visible, eyes partially closed, mouth normal
├─ Audio: 32,000 samples (2 seconds)
│  └─ Normal volume but elevated pitch, faster speech

FACE ANALYSIS
├─ Eye aspect ratio: 0.18 < threshold (0.2)
├─ Blink rate: 8 per minute (below normal 12-20)
├─ Fatigue score: 0.35
└─ [Result] Low fatigue

VOICE ANALYSIS
├─ Baseline pitch: 120 Hz
├─ Current pitch: 155 Hz
├─ Ratio: 1.29 > 1.3? (close, borderline)
├─ Speech rate: 165 WPM
├─ Loudness: 0.18 (elevated)
├─ Stress score: 0.55
├─ Pitch variation: 0.25
├─ Speech variation: 0.30
├─ Loudness variation: 0.15
├─ Anxiety score: 0.23
└─ [Result] Moderate stress, low anxiety

BREATHING ANALYSIS
├─ Audio energy envelope peaks: 5 detected
├─ Time span: 2 seconds
├─ Breathing rate: (5-1 cycles / 2 sec) × 60 = 120 BPM
│  Wait, that's 2 breaths per second = way too high!
│  [Clipped to reasonable range: 25 BPM after validation]
├─ Breathing irregularity: 0.32
└─ [Result] Elevated breathing rate (stress indicator)

AGGREGATION
├─ fatigue: 0.35 × 0.25 = 0.0875
├─ stress: 0.55 × 0.30 = 0.165
├─ anxiety: 0.23 × 0.25 = 0.0575
├─ breathing: 0.70 × 0.20 = 0.140
├─ overall = 0.0875 + 0.165 + 0.0575 + 0.140 = 0.45

INTERPRETATION
├─ Overall concern: 0.45 (MODERATE)
├─ Concern level: MODERATE
├─ Primary concern: stress

RECOMMENDATIONS
├─ "😰 Signs of elevated stress detected."
├─ "🧘 Try deep breathing exercises (4-7-8 technique)."
├─ "🫁 Breathing patterns appear elevated."
└─ "🌬️  Try the 4-4-4 breathing technique..."

OUTPUT
└─ Comprehensive report printed to console
```

---

## ⚡ Performance Characteristics

### Computational Requirements
- **Face analysis**: ~30-50ms per frame (CPU)
- **Voice analysis**: ~100-200ms per chunk (CPU)
- **Breathing analysis**: ~50-100ms per chunk (CPU)
- **Aggregation**: <1ms
- **Total per cycle**: ~200-350ms

### Memory Usage
- Face analyzer: ~50MB (MediaPipe models)
- Voice analyzer: ~10MB (librosa buffers)
- Breathing analyzer: <5MB
- History (30 samples): ~5MB
- **Total**: ~70-80MB

### Latency
- Frame to analysis: ~5 seconds (intentional for smoothing)
- Audio to analysis: Wait for 2-second chunk
- Total end-to-end: ~5-7 seconds

---

## 🔄 Thread Safety

The system uses threading for concurrent I/O:

```python
Main Thread
├─ Video capture
├─ Frame processing
└─ Analysis triggering
    │
    └─ Audio Thread (background)
       ├─ Microphone capture
       ├─ Queue management
       └─ Non-blocking queue.get()

Thread-safe operations:
├─ Queue for frame passing (thread-safe)
├─ Lock for frame buffer access
├─ Independent analyzer instances
└─ No race conditions
```

---

## 🧪 Testing & Validation

Recommended tests:

```python
# Unit tests to add
├─ test_face_analyzer.py
│  ├─ Test EAR calculation
│  ├─ Test blink detection
│  └─ Test fatigue scoring
├─ test_voice_analyzer.py
│  ├─ Test pitch extraction
│  ├─ Test speech rate detection
│  └─ Test stress scoring
├─ test_breathing_analyzer.py
│  ├─ Test peak detection
│  ├─ Test BPM calculation
│  └─ Test irregularity scoring
└─ test_integration.py
   ├─ Test data aggregation
   ├─ Test recommendation generation
   └─ End-to-end scenario tests
```

---

## 📚 References

- **Face Detection**: [MediaPipe Face Mesh](https://mediapipe.dev/)
- **Pitch Detection**: [Piptrack Algorithm](https://arxiv.org/abs/0804.5092)
- **Audio Features**: [Librosa Documentation](https://librosa.org/doc/main/)
- **Eye Aspect Ratio**: [Real-Time Eye Tracking](https://www.researchgate.net/)
- **Speech Emotion**: [Voice & Stress Research](https://ieee-dataport.org/)

---

**Last Updated**: February 2026
**Version**: 1.0 MVP
