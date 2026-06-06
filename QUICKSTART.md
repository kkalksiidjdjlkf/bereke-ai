# 🚀 Quick Start Guide for Beginners

This guide will get you running the wellbeing monitoring system in under 10 minutes!

---

## Step 1: Verify You Have Python (2 minutes)

Open a terminal and check your Python version:

```bash
python3 --version
```

You should see `Python 3.8` or higher. If not, [install Python](https://www.python.org/downloads/).

---

## Step 2: Navigate to Project Directory (1 minute)

```bash
cd ~/Desktop/стартап
```

Or wherever you saved the project.

---

## Step 3: Install Python Packages (3 minutes)

Install all dependencies in one command:

```bash
pip install -r requirements.txt
```

**On macOS**, if you want audio support:
```bash
brew install portaudio
pip install pyaudio
```

**Expected output:**
```
Collecting opencv-python==4.8.1.78
  Downloading opencv_python-4.8.1.78-cp311-cp311-macosx_11_6_x86_64.whl
  ...
Successfully installed opencv-python-4.8.1.78 mediapipe-0.10.5 librosa-0.10.0 ...
```

---

## Step 4: Validate Your Setup (1 minute)

Run the validation script:

```bash
python validate_setup.py
```

You should see ✅ marks next to:
- Python Version
- Dependencies  
- Camera
- Project Files

If anything shows ❌, the script will tell you how to fix it.

---

## Step 5: Start Monitoring! (3 minutes)

Run the main application:

```bash
python main.py
```

**What you'll see:**
1. **Initialization messages** - System loading
2. **Video window** - Your face with landmarks drawn
3. **Console output** - Detailed analysis every 5 seconds

**Controls:**
- Press `q` to quit
- Press `ESC` to quit  
- Press `s` to save a screenshot

**Let it run for at least 30 seconds** to see meaningful analysis!

---

## Example: First Run Output

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
Press 'q' or ESC to exit early

🎤 Audio capture started

============================================================
🏥 WELLBEING MONITORING REPORT
============================================================
Time: 2026-02-10T15:30:45.123456

Overall Status: ✅ All indicators suggest good wellbeing.
Concern Level: LOW
Primary Concern: fatigue

------------------------------------------------------------
📊 DETAILED METRICS:
------------------------------------------------------------

👁  Facial Analysis:
   Fatigue Level: LOW
   Fatigue Score: 0.12/1.0
   Eyes Status: OPEN
   Face Detected: Yes

🎤 Voice Analysis:
   Stress Level: LOW
   Stress Score: 0.18/1.0
   Anxiety Level: LOW
   Anxiety Score: 0.08/1.0
   Pitch: 125 Hz
   Speech Rate: 140 WPM
   Loudness: 0.10

🫁 Breathing Analysis:
   Breathing Status: NORMAL
   Breathing Rate: 16 BPM
   Irregularity: 0.12

------------------------------------------------------------
💡 RECOMMENDATIONS:
------------------------------------------------------------
1. ✅ All systems normal. You're doing well!
2. 👍 No significant stress or fatigue detected.
3. 😊 Keep maintaining this balanced state.

============================================================
```

---

## Next Steps After First Run

### Option A: Explore Examples
Learn how to use the system as a library:

```bash
python examples.py
```

This shows:
1. How to use individual analyzers
2. Voice analysis examples
3. Integration examples
4. Custom application examples

### Option B: Customize Configuration
Edit [config.py](config.py) to adjust:
- Monitoring duration
- Thresholds for stress/fatigue detection
- Recommendation messages
- Camera settings

Example: Make monitoring longer (120 seconds)
```python
MONITORING_DURATION_SECONDS = 120
```

### Option C: Read Full Documentation
- [README.md](README.md) - Full feature documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical deep-dive
- Code comments - Well-commented for learning

---

## Troubleshooting

### "Camera not opening"
1. Check if another app is using your camera (FaceTime, Zoom, etc.)
2. Close that app and try again
3. Give Python permission to use camera:
   - **macOS**: System Preferences → Security & Privacy → Camera

### "ImportError: No module named..."
Run setup again:
```bash
pip install -r requirements.txt
```

### "No face detected in video"
- Check lighting (good natural light is best)
- Position face 20-60 cm from camera
- Center your face in frame
- Try restarting the app

### Audio not working (optional)
This is fine! System works without audio. If you want it:

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Ubuntu/Debian:**
```bash
sudo apt-get install portaudio19-dev
pip install pyaudio
```

---

## Understanding the Output

### Concern Levels
| Level | Meaning | What to Do |
|-------|---------|-----------|
| 🟢 LOW | All good | Keep it up! |
| 🟡 MODERATE | Some concern | Take a break, stretch |
| 🔴 HIGH | Notable issues | Follow recommendations |

### What Each Analyzer Detects

**Face (Fatigue Detector):**
- Looks at eye closure and blink patterns
- Score 0.0 = alert, 1.0 = very fatigued

**Voice (Stress/Anxiety Detector):**
- Pitch increase = stress
- Speech speed = anxiety
- Loudness changes = emotion

**Breathing (Health Indicator):**
- Normal: 12-20 breaths per minute
- Fast: >25 = stress/anxiety
- Irregular: unstable rhythm

---

## Running Multiple Sessions

To monitor yourself over time:

```bash
# Run 1: First thing in morning
python main.py

# Run 2: Middle of workday
python main.py

# Run 3: After evening exercise
python main.py
```

Patterns will emerge showing your typical stress/fatigue levels.

---

## Integration with Your Code

If you want to use this in another Python project:

```python
from face_analyzer import FaceAnalyzer
from voice_analyzer import VoiceAnalyzer
from breathing_analyzer import BreathingAnalyzer
from wellbeing_monitor import WellbeingMonitor

# Initialize
monitor = WellbeingMonitor()

# Your code here...
# Get face data, audio data, breathing data

# Analyze
analysis = monitor.aggregate_analysis(
    face_data, 
    voice_data, 
    breathing_data
)

# Use results
print(f"Concern level: {analysis['concern_level']}")
print(f"Recommendations: {analysis['recommendations']}")
```

See [examples.py](examples.py) for more!

---

## Important Reminders ⚕️

```
⚠️ THIS IS NOT A MEDICAL DEVICE ⚠️

This system:
✅ Detects patterns and provides wellness insights
❌ CANNOT diagnose medical conditions
❌ Is NOT a replacement for healthcare professionals
❌ Should not be used for medical decisions

For medical concerns, always consult a doctor!
```

---

## Customization Ideas

Once you're comfortable:

1. **Change monitoring duration** - Edit `MONITORING_DURATION_SECONDS`
2. **Add your own messages** - Edit `RECOMMENDATIONS` dict
3. **Adjust sensitivity** - Change threshold values
4. **Save data** - Modify code to write analysis to CSV/database
5. **Create dashboard** - Parse console output and visualize

---

## Getting Help

1. **Check config.py comments** - Well-documented
2. **Read code comments** - Detailed explanations in each file
3. **See ARCHITECTURE.md** - Technical deep-dive
4. **Try examples.py** - Learning examples
5. **Check error messages** - They're designed to help

---

## What's Next?

After mastering the basics:

- [ ] Run examples.py
- [ ] Customize config.py
- [ ] Review ARCHITECTURE.md
- [ ] Explore the source code
- [ ] Create your own analysis script
- [ ] Build a data visualization dashboard
- [ ] Integrate with other apps

---

**You're all set! Enjoy monitoring your wellbeing! 🎉**

Questions? Check the full [README.md](README.md) or review the code comments.

Happy wellness! 🌟
