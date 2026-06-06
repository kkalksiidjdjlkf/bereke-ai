# Quick Command Reference

## Installation & Setup (One-time)

```bash
# Install all required dependencies
pip install -r requirements_new.txt

# Verify installation
python validate_setup.py
```

## Running Monitoring Sessions

```bash
# Start a monitoring session (stores data in database automatically)
python main.py

# This will:
# 1. Start real-time face/voice/breathing analysis
# 2. Store all results in wellbeing_monitor.db
# 3. Generate a report after session ends
# 4. Save report as wellbeing_report_X_TIMESTAMP.txt

# Controls during monitoring:
# - Press 's' to save a video snapshot
# - Press 'q' or ESC to stop monitoring
```

## Querying & Analyzing Data

### Interactive Mode (Recommended for Beginners)

```bash
# Launch interactive query tool
python query_database.py

# Then select from menu:
# 1 - List all sessions
# 2 - Show session details
# 3 - Generate report
# 4 - Show statistics
# 5 - Export to JSON
# 6 - Compare sessions
```

### Command-Line Mode (For Quick Queries)

```bash
# List all monitoring sessions you've done
python query_database.py --sessions

# View all data from session 1
python query_database.py --session 1

# Generate readable report for session 1
python query_database.py --report 1

# Get statistics for session 1
python query_database.py --stats 1

# Export session 1 data as JSON (for external tools)
python query_database.py --export 1

# Compare sessions 1, 2, and 3 (see differences)
python query_database.py --compare 1,2,3
```

## Learning & Testing

```bash
# Learn the system with demo data
python database_demo.py

# This will:
# 1. Create sample database with test data
# 2. Generate example reports
# 3. Show JSON export format
# 4. Demonstrate all API capabilities
```

## File Management

```bash
# View generated reports
cat wellbeing_report_1_*.txt

# Export all sessions to separate JSON files
python query_database.py --export 1
python query_database.py --export 2
python query_database.py --export 3

# Backup your database
cp wellbeing_monitor.db wellbeing_monitor_backup.db
```

## Typical Workflow

```bash
# Day 1: First monitoring session
python main.py
# (Session 1 is created and stored)

# Day 2: Second monitoring session
python main.py
# (Session 2 is created and stored)

# Day 3: View your progress
python query_database.py --sessions
# (See both sessions 1 and 2)

python query_database.py --session 1
# (View session 1 in detail)

python query_database.py --session 2
# (View session 2 details)

python query_database.py --compare 1,2
# (Compare improvement/changes)

# Generate report for sharing
python query_database.py --report 1
# (Creates wellbeing_report_1_DATE.txt)

# Export for spreadsheet analysis
python query_database.py --export 1
# (Creates session_1_DATE.json)
```

## Understanding Your Data

| Metric | Range | Meaning |
|--------|-------|---------|
| **Fatigue Score** | 0.0-1.0 | 0=Alert, 1=High fatigue |
| **Stress Score** | 0.0-1.0 | 0=Relaxed, 1=High stress |
| **Anxiety Score** | 0.0-1.0 | 0=Calm, 1=Very anxious |
| **Breathing Rate** | 12-20 | Normal breaths/min |
| **Overall Concern** | 0.0-1.0 | 0=Low, 1=High concern |

## Troubleshooting Commands

```bash
# Check if database exists
ls -la wellbeing_monitor.db

# Delete old demo database if needed
rm demo.db

# Verify Python installation
python --version

# Check dependencies
python -c "import cv2; import mediapipe; print('✅ All installed')"

# Test database directly
python -c "from database import WellbeingDatabase; db = WellbeingDatabase(); print('✅ Database OK')"
```

## Advanced: Direct Database Access

```bash
# Connect to database with SQL
sqlite3 wellbeing_monitor.db

# View all sessions
SELECT id, start_time, duration_seconds FROM sessions;

# View average stress from session 1
SELECT AVG(stress_score) FROM voice_analysis WHERE session_id = 1;

# Count all analysis records
SELECT COUNT(*) FROM face_analysis;

# Exit SQLite
.exit
```

## File Locations & Cleanup

```bash
# Current database location
wellbeing_monitor.db          # Main database

# Reports saved as
wellbeing_report_1_DATE.txt   # After each session
wellbeing_report_2_DATE.txt
wellbeing_report_3_DATE.txt

# Snapshots saved as (if pressed 's' during monitoring)
snapshot_DATE.png
snapshot_DATE.png

# Demo files (after running database_demo.py)
demo.db                       # Demo database
demo_report_DATE.txt         # Demo report
demo_export_DATE.json        # Demo JSON

# Cleanup demo files
rm demo.db demo_report_*.txt demo_export_*.json
```

## Configuration Changes

Edit `config.py` to customize:

```python
# How long to monitor (seconds)
MONITORING_DURATION_SECONDS = 30  # Change to 60 for 1 minute

# How often to analyze (seconds)
CHECK_INTERVAL_SECONDS = 5        # Change to 3 for more frequent

# Fatigue threshold (0-1)
EYE_ASPECT_RATIO_THRESHOLD = 0.2  # Lower = more sensitive

# Voice thresholds
STRESSED_PITCH_INCREASE = 1.3     # How much pitch increase = stressed

# Breathing thresholds
FAST_BREATHING_THRESHOLD = 25     # BPM that triggers alert
```

## Common Tasks

### Task: Track sleep deprivation
```bash
# Morning monitoring
python main.py
# Results in: wellbeing_report_1_*.txt

# Evening monitoring
python main.py
# Results in: wellbeing_report_2_*.txt

# Compare
python query_database.py --compare 1,2
```

### Task: Monitor stress changes
```bash
# Before stressful event
python main.py

# Take note of session ID

# After stressful event
python main.py

# View comparison
python query_database.py --compare 1,2
```

### Task: Track exercise recovery
```bash
# Before exercise
python main.py

# Do exercise

# After exercise (immediately)
python main.py

# After rest (30 minutes)
python main.py

# Compare all three
python query_database.py --compare 1,2,3
```

### Task: Share data with doctor
```bash
# Generate report
python query_database.py --report 1

# This creates: wellbeing_report_1_TIMESTAMP.txt

# Email the .txt file to your doctor

# Alternative: Export to JSON for your records
python query_database.py --export 1
# Creates: session_1_TIMESTAMP.json
```

## Help & Support

```bash
# Get help on query tool
python query_database.py --help

# Read documentation
cat DATABASE_SETUP.md      # Quick start
cat DATABASE.md            # Technical details
cat ARCHITECTURE_WITH_DB.md # System design

# Run demo to learn
python database_demo.py
```

## One-Liner Examples

```bash
# Install and run demo in one line
pip install -r requirements_new.txt && python database_demo.py

# Monitor and immediately view results
python main.py && python query_database.py --sessions

# Generate report immediately after monitoring
python main.py && python query_database.py --report 1

# Compare last two sessions
python query_database.py --compare 1,2

# Export today's monitoring
python query_database.py --export 1
```

---

## Quick Links

- 📖 **Read First**: `DATABASE_SETUP.md`
- 🏗️ **Architecture**: `ARCHITECTURE_WITH_DB.md`
- 🔧 **Technical Details**: `DATABASE.md`
- 📝 **Implementation**: `IMPLEMENTATION_SUMMARY.md`
- 🧪 **Try Demo**: `python database_demo.py`
- 🚀 **Start Monitoring**: `python main.py`

---

**Most Important Commands:**
```bash
python main.py                           # Start monitoring
python query_database.py --sessions      # See all your sessions
python query_database.py --report 1      # Generate report
```
