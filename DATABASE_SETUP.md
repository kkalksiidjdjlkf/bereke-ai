# Database Setup & Monitoring Guide

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements_new.txt
```

Required packages:
- `opencv-python` - Video capture and frame processing
- `mediapipe` - Face landmark detection
- `librosa` - Audio analysis
- `numpy` & `scipy` - Numerical computing
- `tabulate` - Table formatting for reports

### Step 2: Run Monitoring Session with Database Storage

```bash
python main.py
```

This will:
1. ✅ Initialize camera and audio
2. ✅ Create a new monitoring session in the database
3. ✅ Capture and analyze face, voice, breathing in real-time
4. ✅ Store all analysis results in SQLite database
5. ✅ Generate a comprehensive report at the end

### Step 3: Query Your Data

After monitoring, query the database:

```bash
# Interactive query tool
python query_database.py

# Or use command-line
python query_database.py --sessions
python query_database.py --session 1
python query_database.py --report 1
```

## 📊 What Gets Monitored

### Face Analysis
- **Fatigue Detection**: Eye closure ratios, blink patterns, eye openness
- **Emotion Indicators**: Facial expressions, mouth movements
- **Attention Level**: Face detection consistency

### Voice Analysis
- **Stress Detection**: Pitch changes, pitch variation
- **Anxiety Indicators**: Speech rate, voice tremor
- **Voice Quality**: Loudness, sound characteristics
- **Speech Patterns**: Rate and rhythm

### Breathing Analysis
- **Breathing Rate**: Breaths per minute (normal: 12-20 BPM)
- **Irregularity**: Rhythm consistency
- **Stress Indicators**: Fast breathing (>25 BPM = stressed)
- **Energy Level**: Derived from breathing patterns

## 📈 Database Files Generated

After each monitoring session, the system creates:

### 1. **wellbeing_monitor.db** (SQLite Database)
- Persistent storage of all monitoring data
- Can be queried multiple times
- Stores historical data for trend analysis

### 2. **wellbeing_report_{id}_{timestamp}.txt**
- Human-readable session report
- Contains statistics and analysis summary
- Automatically saved after each session

### 3. **Optional Snapshots**
- Press 's' during monitoring to save frame snapshots
- Saved as `snapshot_{timestamp}.png`

## 🎯 Monitoring Session Workflow

```
Start Monitoring (python main.py)
    ↓
[Create Database Session]
    ↓
[Real-time Monitoring Loop]
    ├→ Capture video frame
    ├→ Analyze face (every CHECK_INTERVAL_SECONDS)
    ├→ Capture audio
    ├→ Analyze voice
    ├→ Analyze breathing
    ├→ Aggregate wellbeing scores
    └→ STORE in database
    ↓
[User Ends Session or Duration Expires]
    ↓
[End Database Session]
    ↓
[Generate Session Report]
    ↓
[Display Report & Save to File]
```

## 💾 Database Tables & Data

### Core Tables

**sessions** - Monitoring session metadata
```
Every monitoring run creates one record with start_time, duration, environment, notes
```

**face_analysis** - Face data (multiple records per session)
```
Stored every CHECK_INTERVAL_SECONDS (default: 5 seconds)
Contains: fatigue_score, blink_rate, eye_openness, etc.
```

**voice_analysis** - Voice data (multiple records per session)
```
Stored every CHECK_INTERVAL_SECONDS
Contains: stress_score, anxiety_score, pitch_hz, speech_rate_wpm, etc.
```

**breathing_analysis** - Breathing data (multiple records per session)
```
Stored every CHECK_INTERVAL_SECONDS
Contains: breathing_rate, breathing_status, irregularity level, etc.
```

**wellbeing_analysis** - Aggregated scores (multiple records per session)
```
Stored every CHECK_INTERVAL_SECONDS
Contains: overall_concern_score, primary_concern, recommendations, etc.
```

**recommendations** - Generated recommendations
```
Associated with each wellbeing_analysis record
Contains the actual recommendation text and metadata
```

## 🔍 How to Use the Query Tool

### Menu Mode (Interactive)
```bash
python query_database.py
```

Options:
1. **List all sessions** - See all past monitoring sessions
2. **Show session details** - Deep dive into a specific session
3. **Generate report** - Create readable PDF report
4. **Show statistics** - View numerical summaries
5. **Export to JSON** - Get data for external analysis
6. **Compare sessions** - Track changes over time

### Command-Line Mode (Direct)
```bash
# List all sessions
python query_database.py --sessions

# Get session 1 details
python query_database.py --session 1

# Generate report for session 1
python query_database.py --report 1

# Get statistics for session 1
python query_database.py --stats 1

# Export session 1 as JSON
python query_database.py --export 1

# Compare multiple sessions
python query_database.py --compare 1,2,3,4,5
```

## 🧪 Demo & Testing

Try the database demo to understand the system:

```bash
python database_demo.py
```

This creates:
- Demonstration database (demo.db)
- Sample session with face, voice, breathing data
- Example reports and JSON exports
- Shows all API capabilities

## 📝 Configuration

Modify `config.py` to customize monitoring:

```python
# Monitoring duration
MONITORING_DURATION_SECONDS = 30  # How long to monitor

# Analysis frequency
CHECK_INTERVAL_SECONDS = 5  # How often to analyze

# Face detection thresholds
EYE_ASPECT_RATIO_THRESHOLD = 0.2  # For fatigue detection

# Voice thresholds
STRESSED_PITCH_INCREASE = 1.3  # 30% pitch increase = stressed

# Breathing thresholds
FAST_BREATHING_THRESHOLD = 25  # BPM that indicates stress

# Database location
# Edit in query_database.py and main.py if needed
```

## 📊 Understanding the Scores

### Fatigue Score (0-1)
- **0.0-0.3**: Alert and well-rested
- **0.3-0.6**: Normal baseline
- **0.6-0.8**: Moderate fatigue signs
- **0.8-1.0**: High fatigue risk

### Stress Score (0-1)
- **0.0-0.2**: Relaxed
- **0.2-0.5**: Normal
- **0.5-0.8**: Moderate stress
- **0.8-1.0**: High stress

### Anxiety Score (0-1)
- **0.0-0.3**: Calm
- **0.3-0.6**: Slightly anxious
- **0.6-1.0**: Elevated anxiety

### Overall Concern Score (0-1)
- **0.0-0.4**: Low concern (MILD_CONCERN_THRESHOLD)
- **0.4-0.6**: Moderate concern (MODERATE_CONCERN_THRESHOLD)
- **0.6-0.8**: High concern (HIGH_CONCERN_THRESHOLD)
- **0.8-1.0**: Alert needed

## 🔐 Data Privacy & Storage

The database stores personal health data:
- Keep `wellbeing_monitor.db` secure
- Don't share with untrusted parties
- Export data carefully
- Consider encryption for sensitive deployments

## 🐛 Troubleshooting

### Database is locked
```
❌ Error: database is locked
✅ Solution: Close all other Python instances, restart app
```

### No data in database
```
❌ Face/voice/breathing data not storing
✅ Check:
   - Is face always detected? (face_detected = True)
   - Audio available? (AUDIO_AVAILABLE = True)
   - CHECK_INTERVAL_SECONDS is not too large
```

### Report not generated
```
❌ No report file created
✅ Check:
   - Session ended properly
   - Database connection active
   - Write permissions to directory
```

### Query tool shows no sessions
```
❌ python query_database.py --sessions shows nothing
✅ Check:
   - Have you run python main.py yet?
   - Using correct database file path?
   - Database file exists?
```

## 📚 File Structure

```
стартап/
├── main.py                    # Main monitoring system
├── database.py                # Database module (core)
├── query_database.py          # Database query tool
├── database_demo.py           # Demo script
├── config.py                  # Configuration
├── face_analyzer.py           # Face analysis
├── voice_analyzer.py          # Voice analysis
├── breathing_analyzer.py      # Breathing analysis
├── wellbeing_monitor.py       # Analysis aggregation
├── validate_setup.py          # Setup validation
├── README.md                  # Main documentation
├── DATABASE.md                # Database documentation
├── ARCHITECTURE.md            # System architecture
├── requirements_new.txt       # Dependencies (with tabulate)
└── wellbeing_monitor.db       # SQLite database (created on first run)
```

## 🚀 What's Next?

1. **Run monitoring**: `python main.py`
2. **Query results**: `python query_database.py`
3. **Analyze trends**: Track multiple sessions
4. **Export data**: Use JSON export for analysis
5. **Share reports**: Generate reports for healthcare providers

## 📞 Support

For issues or questions:
1. Check DATABASE.md for detailed technical documentation
2. Run database_demo.py to understand the system
3. Review config.py for customization options
4. Check ARCHITECTURE.md for system design details

---

**System Status**: ✅ Database integration complete and ready for monitoring!
