🎰 Bereke AI: Gambling Behavior Monitor
An intelligent behavioral analysis system designed to detect early signs of gambling addiction (ludomania) and high-risk behavior during online gaming sessions.
⚠️ DISCLAIMER: This system is for behavioral monitoring purposes only. It is NOT a medical diagnostic tool. If you or someone you know is struggling with gambling addiction, please seek help from a professional healthcare provider or a support organization.
📋 Table of Contents
Project Overview
Key Features
How Detection Works
Architecture
Installation & Setup
Configuration
Important Disclaimer
🎯 Project Overview
Bereke AI is a specialized tool designed to help users identify risky gambling patterns in real-time. By analyzing facial micro-expressions, voice reactions, and respiratory patterns, the system detects signs of emotional instability, such as "chasing losses," high-stress states, or the loss of control that often precedes problematic gambling behaviors.
✨ Key Features
Behavioral Detection
📉 "Chasing Losses" Detection: Analyzes sudden changes in facial expressions and reaction speed after a loss.
😤 Emotional Over-arousal: Identifies acute stress through voice pitch shifts and erratic breathing.
🕒 Loss of Time Control: Monitors session duration and blinking patterns to detect cognitive fatigue.
🔊 Agitation/Dopamine Spikes: Monitors tone and volume fluctuations that correlate with high-stakes excitement or frustration.
Real-time Feedback
The system provides immediate, non-intrusive notifications:
"High tension detected. We recommend taking a short break."
"Your reactions suggest an elevated emotional state. Consider stepping away from the game."
🧠 How Detection Works
1. Facial Analysis (MediaPipe)
Focus Tracking: Detects "blank stares" or loss of concentration, which often precede impulsive betting.
Micro-expressions: Analyzes muscle tension around the eyes and mouth associated with frustration or desperation.
2. Voice Analysis
Stress Levels: Detects pitch elevation (Hz) often associated with high-stakes losses or sudden excitement.
Speech Rate: Analyzes acceleration in speech, which can signal a state of emotional affect.
3. Respiratory Analysis
Breath Irregularity: Monitors for shallow, rapid, or gasping breathing patterns, which are physical indicators of the "fight or flight" response triggered during gambling.
🏗️ Architecture
[User Playing Casino Game]
      │
      ▼
[Capture Modules] (Camera + Microphone)
      │
┌─────┴───────────────────────┐
│   Behavioral Analysis Engine │
│ - Face (Emotion/Fatigue)    │
│ - Voice (Stress/Reaction)   │
│ - Breath (Adrenaline)       │
└─────┬───────────────────────┘
      │
[Gambling Risk Monitor] ──> 💡 Trigger Alert
                            💡 Optional Session Pause
🚀 Installation & Setup
Clone the repository:
cd ~/Desktop/стартап
2. **Setup virtual environment:**
   ```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
Install dependencies:
pip install -r requirements.txt
4. **Run the system:**
   ```bash
python main.py
⚙️ Configuration (config.py)
Adjust the sensitivity thresholds in config.py to match your monitoring requirements:
Python
# Threshold for loss-reaction sensitivity
STRESS_REACTION_THRESHOLD = 0.75 

# Max recommended session time before a mandatory break
MAX_SESSION_TIME_MINUTES = 45

# Enable/Disable real-time popup alerts
ENABLE_ALERTS = True
⚠️ Important Disclaimer
Note: Bereke AI is not a medical device. The behavioral signs detected are indicators, not a definitive diagnosis of addiction. Relying solely on this AI is not a substitute for professional counseling. If you feel you are losing control of your gaming habits, please reach out to gambling help support services in your region.
Bereke AI: Helping you maintain control and play responsibly.