# 🎨 Web & Mobile App - System Architecture Diagram

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WELLBEING MONITORING SYSTEM                     │
└─────────────────────────────────────────────────────────────────────┘

1. MONITORING LAYER
═══════════════════════════════════════════════════════════════════════
    
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Face Camera  │     │ Microphone   │     │ Breathing    │
    │ (Webcam)     │     │ (Audio)      │     │ (Detection)  │
    └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
           │                    │                    │
           └────────────┬───────┴────────────┬───────┘
                        │                    │
                        ▼                    ▼
                  ┌──────────────────────────────────┐
                  │    main.py                       │
                  │  (Main Monitoring Application)  │
                  └──────┬───────────────────────────┘
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
      ┌─────────┐  ┌──────────┐  ┌──────────┐
      │ Face    │  │ Voice    │  │Breathing │
      │Analyzer │  │Analyzer  │  │Analyzer  │
      └────┬────┘  └────┬─────┘  └────┬─────┘
           │             │             │
           └─────────────┼─────────────┘
                         │
                         ▼
          ┌──────────────────────────────┐
          │  wellbeing_monitor.py        │
          │  (Aggregation & Scoring)    │
          └──────────────┬───────────────┘
                         │
                         ▼

2. PERSISTENCE LAYER
════════════════════════════════════════════════════════════════════════
                         
              ┌───────────────────────────────┐
              │      database.py              │
              │   (Database Management)      │
              └────────────┬──────────────────┘
                           │
                           ▼
              ┌───────────────────────────────┐
              │    SQLite Database            │
              │  ┌──────────────────────────┐ │
              │  │ sessions table           │ │
              │  │ face_analysis table      │ │
              │  │ voice_analysis table     │ │
              │  │ breathing_analysis table │ │
              │  │ wellbeing_analysis table │ │
              │  │ recommendations table    │ │
              │  └──────────────────────────┘ │
              └───────────────┬────────────────┘
                              │

3. API LAYER
════════════════════════════════════════════════════════════════════════
                              │
                              ▼
              ┌───────────────────────────────┐
              │    app_backend.py             │
              │   (Flask REST API Server)    │
              │                               │
              │   ┌─────────────────────────┐ │
              │   │ /api/health             │ │
              │   │ /api/sessions           │ │
              │   │ /api/analysis/*         │ │
              │   │ /api/statistics/*       │ │
              │   │ /api/export/*           │ │
              │   │ /api/compare/*          │ │
              │   └─────────────────────────┘ │
              │                               │
              │   Port: 5000                 │
              │   CORS: Enabled              │
              └─────────┬─────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
    JSON            JSON            JSON
    HTTP/1.1        HTTP/1.1        HTTP/1.1

4. CLIENT LAYER
════════════════════════════════════════════════════════════════════════
        │               │               │
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐   ┌─────────────────┐  ┌─────────────┐
   │ Browser │   │ Mobile Browser  │  │ Python      │
   │ (Web)   │   │ (Phone/Tablet)  │  │ Script      │
   │         │   │                 │  │             │
   │ Chrome  │   │ iOS Safari      │  │ Requests    │
   │ Firefox │   │ Chrome Android  │  │ Curl        │
   │ Safari  │   │                 │  │ Custom Code │
   │ Edge    │   │                 │  │             │
   └────┬────┘   └────────┬────────┘  └──────┬──────┘
        │                 │                  │
        └─────────────────┼──────────────────┘
                          │
                          ▼
            ┌──────────────────────────────┐
            │  app_dashboard.html          │
            │  (Responsive Web Dashboard)  │
            │                              │
            │  ┌────────────────────────┐  │
            │  │ Dashboard Tab          │  │
            │  │ • Metric cards         │  │
            │  │ • Activity chart       │  │
            │  │ • Quick stats          │  │
            │  │                        │  │
            │  │ Sessions Tab           │  │
            │  │ • Session list         │  │
            │  │ • Details modal        │  │
            │  │ • Export button        │  │
            │  │                        │  │
            │  │ Analysis Tab           │  │
            │  │ • Session selector     │  │
            │  │ • Detailed metrics     │  │
            │  │                        │  │
            │  │ Statistics Tab         │  │
            │  │ • Time range selector  │  │
            │  │ • Trends chart        │  │
            │  │                        │  │
            │  │ Settings Tab           │  │
            │  │ • API configuration    │  │
            │  │ • Display options      │  │
            │  └────────────────────────┘  │
            │                              │
            │  Real-time Updates           │
            │  Touch Optimized             │
            │  Mobile Responsive           │
            └──────────────────────────────┘
                         │
                         │
         ┌───────────────┴───────────────┐
         │                               │
    USER VIEWING                   DEVICE SCREEN
      Desktop                    Desktop/Mobile/Tablet
     Computer                    Phone/Tablet
```

## Component Relationships

```
MONITORING                DATABASE              API                DISPLAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

main.py ──[stores]──→ SQLite ──[queries]──→ Flask ──[returns]──→ Dashboard
    ↓                    ↓                     ↓                     ↓
Face Analyzer        Sessions             /api/health         Metric Cards
Voice Analyzer       Face analysis        /api/sessions       Charts
Breathing            Voice analysis       /api/analysis       Statistics
Aggregation          Breathing            /api/statistics     Settings

                                          /api/export          Export/Share
                                          /api/compare         Compare Data
```

## Data Request Example (User Perspective)

```
User opens Browser
    ↓
Requests: http://localhost:5000
    ↓
Flask serves: app_dashboard.html
    ↓
JavaScript initializes
    ↓
Makes AJAX request: /api/statistics/timerange?days=7
    ↓
Flask queries SQLite database
    ↓
Returns JSON response
    ↓
JavaScript processes data
    ↓
Chart.js renders visualization
    ↓
User sees beautiful dashboard!
```

## Mobile Access Flow

```
User's Phone Browser
    ↓
GET http://192.168.1.100:5000
    ↓
Flask returns HTML (app_dashboard.html)
    ↓
JavaScript loads (Chart.js, icons)
    ↓
Layout adapts to mobile screen
    ↓
Touch handlers enabled
    ↓
API calls via fetch()
    ↓
Real-time data updates
    ↓
Perfect mobile experience!
```

## Technology Stack Visualization

```
        ╔════════════════════════════════════╗
        ║      CLIENT TECHNOLOGIES           ║
        ║ HTML5, CSS3, JavaScript            ║
        ║ Chart.js, Font Awesome             ║
        ║ Responsive Design                  ║
        ╚════════════════════════════════════╝
                        △
                        │
        ╔═══════════════╩═══════════════╗
        ║   API TECHNOLOGIES            ║
        ║ Flask (Python 2.3.3)          ║
        ║ CORS, JSON                    ║
        ║ HTTP REST                     ║
        ╚═══════════════╦═══════════════╝
                        │
        ╔═══════════════╩═══════════════╗
        ║  DATABASE TECHNOLOGIES        ║
        ║ SQLite 3                      ║
        ║ 6 Tables                      ║
        ║ Indexed Queries               ║
        ╚═══════════════╦═══════════════╝
                        │
        ╔═══════════════╩═══════════════╗
        ║  MONITORING TECHNOLOGIES      ║
        ║ OpenCV (Face)                 ║
        ║ Librosa (Voice)               ║
        ║ MediaPipe (Breathing)         ║
        ║ NumPy/SciPy (Math)            ║
        ╚═══════════════╦═══════════════╝
                        │
        ╔═══════════════╩═══════════════╗
        ║  DEPLOYMENT TECHNOLOGIES      ║
        ║ Docker                        ║
        ║ docker-compose                ║
        ║ Gunicorn (Production)         ║
        ╚════════════════════════════════╝
```

## File Relationship Map

```
User Input
    │
    ├─→ main.py ────────────────────┐
    │       │                        │
    │       ├─→ face_analyzer.py     │
    │       ├─→ voice_analyzer.py    ├─→ database.py ──→ SQLite
    │       └─→ breathing_analyzer.py│
    │       │                        │
    │       └─→ wellbeing_monitor.py─┘
    │
    └─→ app_backend.py ←─ database.py ←─ SQLite
            │
            ├─ /api/health
            ├─ /api/sessions
            ├─ /api/analysis/*
            ├─ /api/statistics/*
            ├─ /api/export
            └─ /api/compare
                    │
                    └─→ app_dashboard.html
                            │
                            ├─ Dashboard Charts
                            ├─ Sessions List
                            ├─ Analysis Metrics
                            ├─ Statistics Trends
                            └─ Settings Panel
                                    │
                                    └─→ User Display
```

## Real-Time Data Update Cycle

```
1. Dashboard loads (every 30 sec if auto-refresh enabled)
   ↓
2. JavaScript timer fires
   ↓
3. fetch('/api/statistics/timerange?days=7')
   ↓
4. Flask receives request
   ↓
5. Queries SQLite database
   ↓
6. Aggregates results
   ↓
7. Returns JSON response
   ↓
8. JavaScript updates DOM
   ↓
9. Chart.js re-renders
   ↓
10. User sees fresh data
    ↓
11. Loop continues...
```

## Security Architecture

```
                    ┌─────────────────────┐
                    │  External Request   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  CORS Middleware    │
                    │  (app_backend.py)   │
                    └──────────┬──────────┘ ✓ Check origin
                               │
                    ┌──────────▼──────────┐
                    │  Flask Routes       │
                    └──────────┬──────────┘ ✓ Validate input
                               │
                    ┌──────────▼──────────┐
                    │  Database Query     │
                    │  (Parameterized)    │
                    └──────────┬──────────┘ ✓ SQL Injection safe
                               │
                    ┌──────────▼──────────┐
                    │  JSON Response      │
                    │  (Serialized)       │
                    └──────────┬──────────┘ ✓ Type safe
                               │
                    ┌──────────▼──────────┐
                    │  Client Receives    │
                    │  (Trusted Browser)  │
                    └─────────────────────┘ ✓ HTTPS (optional)
```

---

**Last Updated**: February 10, 2026  
**Architecture Version**: 2.0  
**Status**: ✅ Complete and Verified
