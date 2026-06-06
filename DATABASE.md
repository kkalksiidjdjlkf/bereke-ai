# Database Integration Guide

## Overview

The Wellbeing Monitoring System now includes a comprehensive SQLite database that stores all monitoring data, enabling:

- **Persistent storage** of all face, voice, and breathing analysis
- **Historical tracking** across multiple monitoring sessions
- **Statistical analysis** and trend detection
- **Report generation** for individual sessions
- **Data export** in multiple formats

## Database Schema

The system uses SQLite with the following tables:

### 1. `sessions`
Stores information about monitoring sessions.

```
• id (INTEGER PRIMARY KEY)
• start_time (TIMESTAMP)
• end_time (TIMESTAMP, nullable)
• duration_seconds (REAL)
• user_notes (TEXT)
• environment (TEXT)
• created_at (TIMESTAMP)
```

### 2. `face_analysis`
Stores face analysis results from each analysis iteration.

```
• id (INTEGER PRIMARY KEY)
• session_id (INTEGER - Foreign Key)
• timestamp (TIMESTAMP)
• fatigue_score (REAL: 0-1)
• eye_closure_ratio (REAL: 0-1)
• blink_rate (REAL: blinks/min)
• blink_consistency (REAL: 0-1)
• eye_openness (REAL: 0-1)
• mouth_openness (REAL: 0-1)
• face_detected (BOOLEAN)
• primary_indicator (TEXT)
```

### 3. `voice_analysis`
Stores voice analysis results.

```
• id (INTEGER PRIMARY KEY)
• session_id (INTEGER - Foreign Key)
• timestamp (TIMESTAMP)
• stress_score (REAL: 0-1)
• anxiety_score (REAL: 0-1)
• pitch_hz (REAL)
• pitch_variation (REAL)
• speech_rate_wpm (REAL)
• loudness_rms (REAL)
• loudness_status (TEXT: normal, quiet, loud)
• voice_quality (TEXT)
• primary_indicator (TEXT)
```

### 4. `breathing_analysis`
Stores breathing pattern analysis results.

```
• id (INTEGER PRIMARY KEY)
• session_id (INTEGER - Foreign Key)
• timestamp (TIMESTAMP)
• breathing_rate (REAL: breaths/min)
• breathing_status (TEXT: normal, fast, irregular, slow)
• breathing_irregularity (REAL: 0-1)
• energy_level (REAL: 0-1)
• rhythm_consistency (REAL: 0-1)
• primary_indicator (TEXT)
```

### 5. `wellbeing_analysis`
Stores aggregated wellbeing analysis and overall scores.

```
• id (INTEGER PRIMARY KEY)
• session_id (INTEGER - Foreign Key)
• timestamp (TIMESTAMP)
• overall_concern_score (REAL: 0-1)
• primary_concern (TEXT)
• secondary_concern (TEXT)
• fatigue_score (REAL: 0-1)
• stress_score (REAL: 0-1)
• anxiety_score (REAL: 0-1)
• breathing_score (REAL: 0-1)
• recommendations (JSON)
• concern_level (TEXT: low, medium, high)
```

### 6. `recommendations`
Stores individual recommendations generated for each analysis.

```
• id (INTEGER PRIMARY KEY)
• session_id (INTEGER - Foreign Key)
• wellbeing_analysis_id (INTEGER - Foreign Key)
• timestamp (TIMESTAMP)
• recommendation_text (TEXT)
• recommendation_type (TEXT)
• priority (TEXT: low, medium, high)
• category (TEXT)
```

## Getting Started

### 1. Installation

Install the required dependencies:

```bash
pip install -r requirements_new.txt
```

### 2. Starting a Monitoring Session

The database is automatically initialized when you run the main monitoring system:

```bash
python main.py
```

**What happens:**
- A new session is created in the database
- All face, voice, and breathing analysis results are stored
- Overall wellbeing analysis is aggregated every CHECK_INTERVAL_SECONDS
- At the end, the session is finalized and a report is generated

### 3. Data Storage Workflow

During a monitoring session:

```
main.py
  └── Creates session
  └── Starts monitoring loop
      ├── Captures frames and audio
      ├── Analyzes face
      ├── Analyzes voice
      ├── Analyzes breathing
      ├── Aggregates wellbeing analysis
      └── Stores ALL results in database
  └── Ends session
  └── Generates report
```

## Querying the Database

### Method 1: Interactive Tool

```bash
python query_database.py
```

This launches an interactive menu:

```
1. List all sessions
2. Show session details
3. Generate report
4. Show statistics
5. Export session as JSON
6. Compare sessions
0. Exit
```

### Method 2: Command-Line Arguments

```bash
# List all sessions
python query_database.py --sessions

# Show details for session 1
python query_database.py --session 1

# Generate full report for session 1
python query_database.py --report 1

# Show statistics for session 1
python query_database.py --stats 1

# Export session 1 as JSON
python query_database.py --export 1

# Compare sessions 1, 2, and 3
python query_database.py --compare 1,2,3
```

### Method 3: Python API

```python
from database import WellbeingDatabase

# Initialize database
db = WellbeingDatabase("wellbeing_monitor.db")

# Get session summary
summary = db.get_session_summary(session_id=1)

# Get statistics
stats = db.get_session_statistics(session_id=1)

# Generate report
report = db.generate_report(session_id=1)
print(report)

# Get history
history = db.get_user_history(limit=10)

# Close connection
db.close()
```

## Reports and Analysis

### Automatic Session Report

After each monitoring session, a report is automatically generated:

```
File: wellbeing_report_{session_id}_{timestamp}.txt
```

Contains:
- Session metadata (start time, duration, environment)
- Face analysis summary (average/peak fatigue, blink patterns)
- Voice analysis summary (stress, anxiety, pitch, speech rate)
- Breathing analysis summary (rate, irregularity)
- Overall wellbeing assessment
- Personalized recommendations

### JSON Export

Export session data for external analysis:

```bash
python query_database.py --export 1
```

Generates: `session_1_{timestamp}.json`

Contains:
```json
{
  "session": { ... },
  "statistics": {
    "face": { ... },
    "voice": { ... },
    "breathing": { ... },
    "wellbeing": { ... }
  },
  "analysis_counts": { ... }
}
```

## Analysis Metrics Explanation

### Face Analysis

**Fatigue Score (0-1)**
- 0.0-0.3: Alert and focused
- 0.3-0.6: Normal baseline
- 0.6-0.8: Moderate fatigue
- 0.8-1.0: High fatigue risk

**Blink Metrics**
- Rate: Normal is 15-20 blinks/min
- Consistency: Measures regular blink patterns
- Eye Openness: Percentage of time eyes are open

### Voice Analysis

**Stress Score (0-1)**
- Elevated pitch (>1.3x baseline)
- Pitch variation stability
- Speech rate changes

**Anxiety Score (0-1)**
- Voice tremor and wavering
- Loudness variations
- Speech pattern irregularities

**Pitch Range**
- Normal speech: 80-200 Hz
- Stressed: >260 Hz (elevated)

**Speech Rate**
- Normal: 150 WPM
- Fast (stressed): >200 WPM

### Breathing Analysis

**Breathing Rate**
- Normal: 12-20 breaths/min
- Fast (stressed): >25 BPM
- Slow (relaxed): <12 BPM

**Irregularity Score (0-1)**
- Measures consistency of breathing rhythm
- 0.0: Perfect rhythm
- 1.0: Highly irregular

## Advanced Usage

### Trend Analysis

Compare multiple sessions to identify trends:

```bash
python query_database.py --compare 1,2,3,4,5
```

Shows comparative metrics across sessions.

### Custom Queries

Connect directly to the database with SQL:

```python
import sqlite3

conn = sqlite3.connect('wellbeing_monitor.db')
cursor = conn.cursor()

# Example: Get average stress over all sessions
cursor.execute('''
    SELECT 
        session_id,
        AVG(stress_score) as avg_stress
    FROM voice_analysis
    GROUP BY session_id
    ORDER BY avg_stress DESC
''')

for row in cursor.fetchall():
    print(f"Session {row[0]}: Avg Stress = {row[1]:.3f}")
```

### Data Cleanup

To archive old sessions:

```python
from database import WellbeingDatabase

db = WellbeingDatabase()

# Get old sessions
old_sessions = db.get_user_history(limit=100)

# Manually export before deletion if needed
for session in old_sessions:
    if old_enough(session['start_time']):
        # Create backup export
        report = db.generate_report(session['id'])
        # Save report...
        # Then delete from database if desired
```

## Configuration

Database path can be customized:

```python
# Use custom database location
db = WellbeingDatabase(db_path="/path/to/custom.db")
```

Database is created automatically in the working directory:
- Default: `wellbeing_monitor.db`

## Files Generated

After each monitoring session:

1. **Session Report**
   - `wellbeing_report_{session_id}_{timestamp}.txt`
   - Human-readable summary

2. **Optional Snapshots**
   - `snapshot_{timestamp}.png` (if 's' pressed during monitoring)

3. **Database**
   - `wellbeing_monitor.db` (persistent storage)

## Best Practices

### 1. Data Integrity
- Database is automatically backed up in reports
- Export important sessions as JSON
- Keep `wellbeing_monitor.db` in safe location

### 2. Privacy
- Database contains personal health data
- Store securely and don't share unnecessarily
- Consider encryption for sensitive deployments

### 3. Monitoring Sessions
- Use `user_notes` to add context
- Set `environment` for tracking location effects
- Regular monitoring (daily/weekly) is recommended

### 4. Report Generation
- Automatically created after each session
- Export periodically for analysis
- Share with healthcare provider if requested

## Troubleshooting

### Database locked error
- Close all other Python instances accessing the database
- Restart the application

### Missing tables
- Database auto-creates tables on first run
- Check file permissions on `wellbeing_monitor.db`

### No records in database
- Ensure analysis is running (CHECK_INTERVAL_SECONDS)
- Verify AUDIO_AVAILABLE setting
- Check that face is detected

## Summary

The database system provides:
- ✅ Automatic data persistence
- ✅ Historical tracking across sessions
- ✅ Comprehensive reporting
- ✅ Statistical analysis capabilities
- ✅ Data export for external analysis
- ✅ Easy querying and visualization

For questions or issues, refer to the main README.md and ARCHITECTURE.md files.
