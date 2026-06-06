# System Architecture with Database Integration

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│               WELLBEING MONITORING SYSTEM v2                        │
│                    with Database Integration                        │
└─────────────────────────────────────────────────────────────────────┘

                         HARDWARE INPUTS
                              │
                  ┌───────────┴──────────┬──────────┐
                  ▼                      ▼          ▼
              CAMERA              MICROPHONE    [SYSTEM STATE]
              (Video)             (Audio)      (Environment)
                  │                   │          │
                  └───────────────────┴──────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   MAIN MONITORING   │
                    │   SYSTEM (main.py)  │
                    └─────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
          FACE ANALYZER  VOICE ANALYZER  BREATHING ANALYZER
          (landmarks)    (pitch, stress)  (rate pattern)
                │             │             │
                └─────────────┼─────────────┘
                              │
                              ▼
                  ┌──────────────────────────┐
                  │  WELLBEING MONITOR       │
                  │  (aggregation engine)    │
                  │  • Combine scores        │
                  │  • Identify concerns     │
                  │  • Generate recommendations
                  └──────────────────────────┘
                              │
                ┌─────────────┴──────────────┐
                ▼                            ▼
        ┌──────────────────┐         ┌──────────────────┐
        │   REAL-TIME      │         │   DATABASE       │
        │   DISPLAY        │         │   STORAGE        │
        │                  │         │                  │
        │ • Video feed     │         │ wellbeing_       │
        │ • Status info    │         │ monitor.db       │
        │ • Alerts         │         │                  │
        │ • Current scores │         │ ┌──────────────┐ │
        │                  │         │ │ - sessions   │ │
        │                  │         │ │ - face_data  │ │
        │                  │         │ │ - voice_data │ │
        │                  │         │ │ - breathing  │ │
        │                  │         │ │ - wellbeing  │ │
        │                  │         │ │ - recommend. │ │
        │                  │         │ └──────────────┘ │
        └──────────────────┘         └──────────────────┘
                │                            │
                │                            ▼
                │                    ┌──────────────────┐
                │                    │  QUERY & ANALYSIS│
                │                    │  (query_database)│
                │                    │                  │
                │                    │ • List sessions  │
                │                    │ • View details   │
                │                    │ • Generate report│
                │                    │ • Statistics     │
                │                    │ • Export JSON    │
                │                    │ • Compare data   │
                │                    └──────────────────┘
                │                            │
                └────────────────────────────┴──────────┐
                                             │
                     ┌───────────────────────┼───────────────────────┐
                     ▼                       ▼                       ▼
              ┌────────────────┐    ┌──────────────────┐   ┌─────────────────┐
              │  REPORT FILE   │    │  JSON EXPORT     │   │  VISUAL DISPLAY │
              │                │    │                  │   │                 │
              │ report_*.txt   │    │ session_*.json   │   │ Real-time graph │
              │                │    │                  │   │ History chart   │
              │ • Summary      │    │ • Statistics     │   │ Trend analysis  │
              │ • Statistics   │    │ • Session data   │   │                 │
              │ • Metrics      │    │ • Timestamps     │   │                 │
              │ • Recommend.   │    │ • Structure      │   │                 │
              └────────────────┘    └──────────────────┘   └─────────────────┘
```

## Data Flow During Monitoring

```
START MONITORING SESSION
        │
        ▼
    ┌─────────────────────────────────┐
    │ Create Session in Database      │
    │ - session_id generated          │
    │ - start_time recorded           │
    └─────────────────────────────────┘
        │
        │ ┌─ MONITORING LOOP (every 5 seconds) ──────┐
        │ │                                           │
        ├─┼─► Capture video frame                    │
        │ │                                           │
        ├─┼─► Analyze face                           │
        │ │     └─► Store in face_analysis table    │
        │ │                                           │
        ├─┼─► Capture audio chunk                    │
        │ │                                           │
        ├─┼─► Analyze voice                          │
        │ │     └─► Store in voice_analysis table   │
        │ │                                           │
        ├─┼─► Analyze breathing                      │
        │ │     └─► Store in breathing_analysis tbl │
        │ │                                           │
        ├─┼─► Aggregate scores                       │
        │ │     └─► Store in wellbeing_analysis tbl │
        │ │         └─► Store recommendations       │
        │ │                                           │
        ├─┼─► Display to user                        │
        │ │                                           │
        └─┴─ Continue or user exits ──────────────────┘
        │
        ▼
    ┌─────────────────────────────────┐
    │ End Session                     │
    │ - end_time recorded             │
    │ - duration calculated           │
    └─────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────┐
    │ Generate Report                 │
    │ - Calculate statistics          │
    │ - Create summary                │
    │ - Save to file                  │
    └─────────────────────────────────┘
        │
        ▼
    ┌─────────────────────────────────┐
    │ Session Complete                │
    │ - Database closed               │
    │ - User has full history record  │
    └─────────────────────────────────┘
```

## Database Table Relationships

```
┌──────────────────┐
│    sessions      │ (1 per monitoring session)
│                  │
│ id (PK)          │
│ start_time       │
│ end_time         │
│ duration_seconds │
│ user_notes       │
│ environment      │
└────────┬─────────┘
         │
         │ (one-to-many)
         │
    ┌────┴────────────────────────────────┬──────────────────────┐
    │                                      │                      │
    ▼                                      ▼                      ▼
┌─────────────────┐              ┌──────────────────┐   ┌─────────────────┐
│ face_analysis   │              │ voice_analysis   │   │breathing_analysis
│                 │              │                  │   │                 │
│ id (PK)         │              │ id (PK)          │   │ id (PK)         │
│ session_id (FK) │              │ session_id (FK)  │   │ session_id (FK) │
│ timestamp       │              │ timestamp        │   │ timestamp       │
│ fatigue_score   │              │ stress_score     │   │ breathing_rate  │
│ eye_closure...  │              │ anxiety_score    │   │ breathing_status│
│ blink_rate      │              │ pitch_hz         │   │ irregularity    │
│ ...             │              │ speech_rate_wpm  │   │ ...             │
└─────────────────┘              │ loudness_rms     │   └─────────────────┘
                                 │ ...              │
                                 └──────────────────┘
                                          ▲
                                          │
                                          │ (aggregates)
                                          │
    ┌─────────────────────────────────────┘
    │
    ▼
┌──────────────────────┐
│ wellbeing_analysis   │ (aggregated scores, every cycle)
│                      │
│ id (PK)              │
│ session_id (FK)      │
│ timestamp            │
│ overall_concern_score
│ primary_concern      │
│ secondary_concern    │
│ fatigue_score        │
│ stress_score         │
│ anxiety_score        │
│ breathing_score      │
│ recommendations (JSON)
└──────────┬───────────┘
           │ (one-to-many)
           │
           ▼
┌──────────────────────────┐
│ recommendations          │ (individual recommendations)
│                          │
│ id (PK)                  │
│ wellbeing_analysis_id(FK)│
│ recommendation_text      │
│ recommendation_type      │
│ priority                 │
│ category                 │
└──────────────────────────┘
```

## Query Tool Architecture

```
┌──────────────────────────┐
│  query_database.py       │
│                          │
│  DatabaseQueryTool class │
└──────────┬───────────────┘
           │
    ┌──────┴──────────┬──────────┬──────────┬──────────┬──────────┐
    │                 │          │          │          │          │
    ▼                 ▼          ▼          ▼          ▼          ▼
┌─────────┐    ┌────────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
│  List   │    │ Session    │ │Generate│ │ Show   │ │Export  │ │ Compare  │
│Sessions │    │ Details    │ │ Report │ │Statistics│JSON    │ │ Sessions │
└────┬────┘    └──────┬─────┘ └────┬───┘ └───┬────┘ └───┬────┘ └────┬─────┘
     │                │            │         │          │           │
     └────────────────┴────────────┴─────────┴──────────┴───────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │  WellbeingDB     │
                    │  Methods:        │
                    │                  │
                    │ • query()        │
                    │ • statistics()   │
                    │ • report()       │
                    │ • export_json()  │
                    └──────────┬───────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  wellbeing_      │
                    │  monitor.db      │
                    │  (SQLite)        │
                    └──────────────────┘
```

## Component Responsibilities

### Face Analyzer
- Detects facial landmarks
- Calculates eye aspect ratio
- Counts and analyzes blinks
- Assesses eye closure duration
- Detects mouth movements
- Produces fatigue scores

### Voice Analyzer
- Extracts fundamental pitch
- Calculates pitch variation
- Measures speech rate
- Analyzes loudness
- Detects tremor/quality issues
- Produces stress/anxiety scores

### Breathing Analyzer
- Extracts energy patterns
- Identifies breathing cycles
- Calculates breathing rate
- Measures irregularity
- Detects abnormal patterns
- Produces breathing status

### Wellbeing Monitor
- Receives all analysis outputs
- Weights different factors
- Calculates overall concern score
- Identifies primary concerns
- Generates recommendations
- Returns comprehensive analysis

### Database
- Receives all analysis results
- Stores in persistent SQLite DB
- Maintains relationships
- Provides query interface
- Generates reports
- Enables data export

### Query Tool
- Loads database data
- Performs aggregations
- Calculates statistics
- Generates reports
- Exports to JSON
- Enables comparisons

## Timeline: Single Monitoring Session

```
Time: 0:00 ────────────────────────────────────────── 5:00
         │
         Set up camera & audio
              │
         Start monitoring session
         Create DB session
              │
         [Monitoring cycle every 5 seconds]
         
         t=5s: Analyze & store face, voice, breathing
         t=10s: Analyze & store face, voice, breathing
         t=15s: Analyze & store face, voice, breathing
         t=20s: Analyze & store face, voice, breathing
         t=25s: Analyze & store face, voice, breathing
         t=30s: Analyze & store face, voice, breathing
              │
         Duration reached or user exits
         End session & finalize in DB
         Generate report
              │
         Done! Data saved in database
         User can query anytime
```

## Security & Data Flow

```
┌─────────────────────────────────────────────────┐
│         WELLBEING MONITOR SYSTEM                │
│  (All processing happens locally on user PC)    │
└─────────────────────────────────────────────────┘
                      │
              ┌───────┴───────┐
              │               │
        LOCAL CAMERA    LOCAL MICROPHONE
              │               │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │  ANALYSIS     │
              │  (local CPU)  │
              └───────┬───────┘
                      │
              ┌───────▼───────────┐
              │  DATABASE         │
              │  - Local file     │
              │  - Not cloud      │
              │  - User controls  │
              │  - Easy backup    │
              └───────────────────┘
                      │
              ┌───────▼───────┐
              │  REPORTS      │
              │  - Local file │
              │  - User owns  │
              │  - No sharing │
              └───────────────┘

✅ 100% LOCAL PROCESSING
✅ NO DATA SHARED
✅ NO CLOUD DEPENDENCY
✅ USER CONTROLS ALL DATA
```

---

This architecture enables comprehensive monitoring with complete data persistence and analysis capabilities while maintaining complete user privacy and control.
