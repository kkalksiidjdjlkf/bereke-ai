╔════════════════════════════════════════════════════════════════════════╗
║                                                                        ║
║           🎨 WELLBEING MONITORING - WEB & MOBILE APP 🚀              ║
║                                                                        ║
║                   Complete Application Guide                         ║
║                                                                        ║
╚════════════════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════════════════════
📱 QUICK START
═══════════════════════════════════════════════════════════════════════════════

STEP 1: START THE BACKEND API
────────────────────────────
Open terminal and run:
$ cd /Users/maks/Desktop/стартап
$ python app_backend.py

You should see:
✓ Server running on http://localhost:5000
✓ REST API ready for requests

STEP 2: OPEN THE DASHBOARD
──────────────────────────
In your browser, navigate to:
  → http://localhost:5000/dashboard
  
Or open the file directly:
  → Open app_dashboard.html in your browser

STEP 3: ACCESS FROM MOBILE
──────────────────────────
On your phone, connect to your computer:
  → http://<your-computer-ip>:5000
  
Example: http://192.168.1.100:5000

═══════════════════════════════════════════════════════════════════════════════
🏗️  SYSTEM ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════

                        ┌────────────────────────┐
                        │   Dashboard (HTML/JS)  │
                        │   app_dashboard.html   │
                        └────────────┬───────────┘
                                     │
                                     ▼
                        ┌────────────────────────┐
                        │   Flask REST API       │
                        │   app_backend.py       │
                        │   Port: 5000           │
                        └────────────┬───────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
                ┌──────────┐    ┌──────────┐    ┌──────────┐
                │ SQLite   │    │PostgreSQL│    │  Redis   │
                │ Database │    │ Database │    │  Cache   │
                └──────────┘    └──────────┘    └──────────┘

═══════════════════════════════════════════════════════════════════════════════
📚 APPLICATION COMPONENTS
═══════════════════════════════════════════════════════════════════════════════

FILE: app_backend.py (Flask REST API)
──────────────────────────────────────
Purpose:
  - REST API server for mobile/web app
  - Database query interface
  - Data export and comparison
  - Statistics calculation
  
Key Features:
  ✓ CORS enabled for cross-origin requests
  - 20+ REST endpoints
  - JSON response format
  - Error handling and status codes
  - Health checks
  - Pagination support

Running:
  $ python app_backend.py
  
Default Port: 5000

FILE: app_dashboard.html (Web Dashboard)
────────────────────────────────────────
Purpose:
  - Modern, responsive web interface
  - Works on desktop, tablet, mobile
  - Real-time data visualization
  - Session management
  
Key Features:
  ✓ 5 main sections:
    - Dashboard (overview)
    - Sessions (list & details)
    - Analysis (detailed metrics)
    - Statistics (trends & reporting)
    - Settings (configuration)
  
  ✓ Interactive charts
  ✓ Mobile-responsive design
  ✓ Real-time status updates
  ✓ Data export capabilities
  ✓ Session comparison

Supported Browsers:
  ✓ Chrome/Chromium
  ✓ Firefox
  ✓ Safari
  ✓ Edge
  ✓ Mobile browsers (iOS Safari, Chrome Android)

═══════════════════════════════════════════════════════════════════════════════
🔌 REST API ENDPOINTS
═══════════════════════════════════════════════════════════════════════════════

HEALTH & STATUS
───────────────
GET /api/health
  Returns: API health status
  Response: { status: "healthy", timestamp: "...", version: "2.0" }

GET /api/status
  Returns: System status
  Response: { status: "running", database_available: true }

SESSIONS
────────
GET /api/sessions?page=1&limit=20
  Returns: Paginated list of all sessions
  Response: { sessions: [...], pagination: {...} }

GET /api/sessions/<session_id>
  Returns: Complete session data with all analyses
  Response: { id, start_time, face_analysis: [...], voice_analysis: [...], ... }

GET /api/sessions/recent?days=7
  Returns: Recent sessions
  Response: { sessions: [...], days: 7 }

ANALYSIS DATA
─────────────
GET /api/analysis/face/<session_id>
  Returns: Face analysis data for session
  
GET /api/analysis/voice/<session_id>
  Returns: Voice analysis data for session
  
GET /api/analysis/breathing/<session_id>
  Returns: Breathing analysis data for session
  
GET /api/analysis/wellbeing/<session_id>
  Returns: Wellbeing metrics for session

STATISTICS
──────────
GET /api/statistics/session/<session_id>
  Returns: Session statistics and aggregates
  Response: { face_emotions, voice_metrics, breathing_metrics }

GET /api/statistics/timerange?days=7
  Returns: Statistics for time range
  Response: { timerange_days, sessions_count, face_statistics, ... }

RECOMMENDATIONS
────────────────
GET /api/recommendations/<session_id>
  Returns: Wellness recommendations for session
  Response: { recommendations: [...], count: N }

EXPORT & COMPARISON
────────────────────
GET /api/export/session/<session_id>
  Returns: Complete session data for download
  
GET /api/compare/sessions?ids=1&ids=2&ids=3
  Returns: Comparison of multiple sessions
  Response: { comparison: {...}, session_count: 3 }

═══════════════════════════════════════════════════════════════════════════════
🎨 DASHBOARD FEATURES
═══════════════════════════════════════════════════════════════════════════════

MAIN DASHBOARD
──────────────
- Overview cards showing:
  ✓ Face analysis confidence
  ✓ Voice energy levels
  ✓ Breathing rate
  ✓ Overall wellbeing score
  
- Activity chart (last 7 days)
- Quick statistics
- Real-time status indicator

SESSIONS TAB
────────────
- List of all sessions
- Session timestamps and durations
- Status indicators (completed/active)
- Detailed view modal
- Export individual sessions

ANALYSIS TAB
──────────────
- Select session to analyze
- Detailed metrics breakdown
- Analysis sample counts
- Data export option
- Metric visualization

STATISTICS TAB
──────────────
- Time range selector (7/14/30/90 days)
- Statistical summaries
- Metric trends
- Comparison capabilities
- Historical data view

SETTINGS TAB
────────────
- API URL configuration
- Auto-refresh toggle
- Dark mode option
- Data export
- Cache management
- System information

═══════════════════════════════════════════════════════════════════════════════
📱 MOBILE ACCESS
═══════════════════════════════════════════════════════════════════════════════

DESKTOP TO MOBILE:
──────────────────
1. Find your computer's IP address
   macOS:    ifconfig | grep "inet "
   Windows:  ipconfig
   Linux:    hostname -I

2. On mobile phone, open browser:
   http://<computer-ip>:5000

3. Grant permissions for:
   ✓ Camera (for video calls)
   ✓ Microphone (for audio)
   ✓ Notifications (for alerts)

RESPONSIVE DESIGN:
──────────────────
✓ Optimized for all screen sizes
✓ Touch-friendly buttons
✓ Swipe-enabled navigation
✓ Adaptive layout
✓ Full-screen support
✓ Landscape & portrait modes

═══════════════════════════════════════════════════════════════════════════════
🔄 DATA FLOW
═══════════════════════════════════════════════════════════════════════════════

Monitoring Session:
──────────────────
1. User starts monitoring in main.py
2. Data collected:
   - Face: emotion, confidence, landmarks
   - Voice: energy, pitch, tone
   - Breathing: rate, depth, pattern
3. Data stored in SQLite database
4. Session ends, analysis complete
5. Recommendations generated

Dashboard Access:
─────────────────
1. Dashboard loads
2. REST API called: GET /api/health
3. API queries database
4. Data formatted as JSON
5. Charts rendered on client
6. Live updates every 30 seconds

Data Export:
────────────
1. User selects session
2. REST API: GET /api/export/session/<id>
3. Complete JSON data returned
4. Browser downloads as .json file
5. Importable to other tools

═══════════════════════════════════════════════════════════════════════════════
🔧 ADVANCED SETUP
═══════════════════════════════════════════════════════════════════════════════

PRODUCTION DEPLOYMENT
─────────────────────
For production, use gunicorn instead of Flask dev server:

$ gunicorn -w 4 -b 0.0.0.0:5000 app_backend:app

This provides:
✓ Multiple worker processes
✓ Better performance
✓ Production-ready stability
✓ Request handling

NGINX REVERSE PROXY
───────────────────
For high-traffic scenarios, use nginx:

upstream backend {
    server localhost:5000;
}

server {
    listen 80;
    server_name yourdomain.com;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

DOCKER DEPLOYMENT
─────────────────
The app is fully containerized:

$ docker-compose up -d
$ docker-compose logs -f wellbeing-monitor

CORS CONFIGURATION
──────────────────
API already configured to accept requests from:
✓ localhost:5000
✓ localhost:3000
✓ Mobile browsers
✓ Any origin (in dev mode)

For production, modify app_backend.py:
CORS(app, origins=['yourdomain.com'])

═══════════════════════════════════════════════════════════════════════════════
📊 SAMPLE API CALLS
═══════════════════════════════════════════════════════════════════════════════

Using cURL:
───────────

# Check health
$ curl http://localhost:5000/api/health

# Get all sessions
$ curl http://localhost:5000/api/sessions

# Get specific session
$ curl http://localhost:5000/api/sessions/1

# Get face analysis
$ curl http://localhost:5000/api/analysis/face/1

# Get statistics for last 7 days
$ curl http://localhost:5000/api/statistics/timerange?days=7

# Compare sessions
$ curl "http://localhost:5000/api/compare/sessions?ids=1&ids=2"

Using Python:
──────────────

import requests

# Get sessions
response = requests.get('http://localhost:5000/api/sessions')
sessions = response.json()
print(sessions['sessions'])

# Get session details
session_id = sessions['sessions'][0]['id']
response = requests.get(f'http://localhost:5000/api/sessions/{session_id}')
session = response.json()
print(session['face_analysis'])

Using JavaScript (in dashboard):
──────────────────────────────

// Fetch sessions
fetch('http://localhost:5000/api/sessions')
  .then(r => r.json())
  .then(data => console.log(data.sessions));

// Fetch session details
fetch('http://localhost:5000/api/sessions/1')
  .then(r => r.json())
  .then(data => console.log(data));

═══════════════════════════════════════════════════════════════════════════════
🐛 TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════════════

ISSUE: Port 5000 already in use
───────────────────────────────
Solution 1: Kill existing process
$ lsof -i :5000
$ kill -9 <PID>

Solution 2: Use different port
$ python app_backend.py --port 8000

ISSUE: Database not found
──────────────────────────
Solution:
1. Ensure database.py is in same directory
2. Run with proper working directory:
   $ cd /Users/maks/Desktop/стартап
   $ python app_backend.py

ISSUE: Dashboard not loading
────────────────────────────
Solution:
1. Check if API is running: http://localhost:5000/api/health
2. Check browser console for errors (F12)
3. Verify API URL in Settings tab
4. Clear browser cache: Ctrl+Shift+Delete (or ⌘+Shift+Delete)

ISSUE: CORS errors in browser
──────────────────────────────
Solution: Already configured in app_backend.py
If still having issues, modify:
CORS(app, origins=['*'])  # Allow all origins

ISSUE: Mobile can't connect to API
───────────────────────────────────
Solution:
1. Use computer IP instead of localhost
2. Ensure firewall allows port 5000
3. Check both devices on same network
4. Restart router if needed

═══════════════════════════════════════════════════════════════════════════════
📈 PERFORMANCE TIPS
═══════════════════════════════════════════════════════════════════════════════

OPTIMIZE DATABASE QUERIES
──────────────────────────
✓ Pagination limit lower on mobile
✓ Cache recent sessions data
✓ Use time-range filters
✓ Index frequently queried columns

IMPROVE UI PERFORMANCE
──────────────────────
✓ Use auto-refresh sparingly
✓ Lazy-load charts
✓ Minimize animations on mobile
✓ Compress images

REDUCE API CALLS
────────────────
✓ Batch requests
✓ Cache responses locally
✓ Use pagination
✓ Store data in localStorage

═══════════════════════════════════════════════════════════════════════════════
🔐 SECURITY NOTES
═══════════════════════════════════════════════════════════════════════════════

CURRENT SETUP (Development):
────────────────────────────
✓ API accessible without authentication
✓ All endpoints return data
✓ CORS enabled for all origins
✓ No rate limiting

FOR PRODUCTION:
────────────────
TODO: Implement authentication
  - Add JWT tokens
  - User login system
  - Session management

TODO: Add authorization
  - User-specific data
  - Role-based access
  - Data privacy controls

TODO: Enable HTTPS
  - SSL certificates
  - Secure cookies
  - HSTS headers

TODO: Add rate limiting
  - API throttling
  - DDoS protection
  - Request validation

═══════════════════════════════════════════════════════════════════════════════
📖 DETAILED DOCUMENTATION
═══════════════════════════════════════════════════════════════════════════════

For more details, see:
✓ app_backend.py - Code comments and docstrings
✓ app_dashboard.html - JavaScript comments
✓ DOCKER_GUIDE.md - Docker integration
✓ DATABASE.md - Database schema
✓ API_REFERENCE.md (coming) - Full API docs

═══════════════════════════════════════════════════════════════════════════════
🎯 NEXT STEPS
═══════════════════════════════════════════════════════════════════════════════

1. START THE APP ✓
   $ python app_backend.py

2. OPEN DASHBOARD ✓
   http://localhost:5000

3. RUN A MONITORING SESSION ✓
   $ make monitor

4. VIEW RESULTS ✓
   Dashboard → Sessions → Select session

5. EXPORT DATA ✓
   API → /api/export/session/<id>

═══════════════════════════════════════════════════════════════════════════════
✅ VERIFICATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

BEFORE FIRST USE:
[ ] app_backend.py exists
[ ] app_dashboard.html exists
[ ] requirements_app.txt exists
[ ] Database module available
[ ] Can run: python app_backend.py

AFTER STARTING SERVER:
[ ] Server shows "Running on http://localhost:5000"
[ ] No errors in terminal
[ ] /api/health returns 200 status

DASHBOARD FUNCTIONALITY:
[ ] Can open app_dashboard.html
[ ] Can see main dashboard
[ ] API connection shows "Connected"
[ ] Can navigate between tabs
[ ] Sessions load without errors

MOBILE ACCESS:
[ ] Can access from phone on same network
[ ] Layout adapts to mobile screen
[ ] Touch controls work properly
[ ] Charts display correctly

═══════════════════════════════════════════════════════════════════════════════
Created on: February 10, 2026
Version: 2.0 (With Web & Mobile App)
Status: ✅ READY TO USE
═══════════════════════════════════════════════════════════════════════════════
