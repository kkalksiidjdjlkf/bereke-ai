# 🎨 Web & Mobile App - Quick Reference

## 🚀 Quick Start (30 seconds)

```bash
cd /Users/maks/Desktop/стартап
chmod +x app-start.sh
./app-start.sh
```

Then:
1. Choose option "3" (Both Backend + Dashboard)
2. Dashboard opens automatically
3. API runs in background
4. Visit: http://localhost:5000

## 📱 Two Components

### 1. **Flask API Backend** (`app_backend.py`)
- REST API server
- Port: 5000
- Provides data to dashboard and mobile apps
- 20+ endpoints

### 2. **Web Dashboard** (`app_dashboard.html`)
- Modern, responsive web interface
- Works on any browser
- Works on mobile phones
- Real-time charts and statistics

## 🎯 Main Features

- **Dashboard**: Overview of all metrics
- **Sessions**: Browse all monitoring sessions
- **Analysis**: Detailed breakdown of session data
- **Statistics**: Trends and historical data
- **Settings**: API configuration and options
- **Export**: Download session data as JSON
- **Mobile-Ready**: Works perfectly on phones

## 📊 REST API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get all sessions
curl http://localhost:5000/api/sessions

# Get session details
curl http://localhost:5000/api/sessions/1

# Get statistics (last 7 days)
curl http://localhost:5000/api/statistics/timerange?days=7

# Export session data
curl http://localhost:5000/api/export/session/1 > session_1.json
```

## 🔗 Access URLs

| Device | URL | Notes |
|--------|-----|-------|
| Local Computer | http://localhost:5000 | Direct access |
| Mobile (Same Network) | http://192.168.x.x:5000 | Use computer IP |
| API Only | http://localhost:5000/api | JSON endpoints |

## 🎮 Dashboard Sections

### Overview
- 4 main metric cards
- 7-day activity chart
- Quick statistics

### Sessions
- Complete session list
- Clickable details modal
- Status indicators
- Export individual sessions

### Analysis
- Select session dropdown
- Sample counts
- Metric visualization
- Data export

### Statistics
- Time range selector
- Statistical summaries
- Trends chart
- Historical comparison

### Settings
- API URL configuration
- Auto-refresh toggle
- Dark mode option
- Data export/import
- System info

## 🔧 Configuration

### Change API URL
Settings → API Configuration → Enter new URL

### Enable Auto-Refresh
Settings → Display Options → Check "Auto-refresh"

### Export Data
Sessions → Select session → Export button

Or API:
```bash
curl http://localhost:5000/api/export/session/1 > my_session.json
```

## 📱 Mobile Usage

### On Phone
1. Find computer IP: `ifconfig | grep "inet "`
2. Open browser on phone
3. Visit: `http://computer-ip:5000`
4. Full dashboard available!

### Permissions
- Camera: Optional (for future features)
- Microphone: Optional
- Storage: For exports
- Location: Not used

## ⚙️ Advanced Usage

### Use Different Port
```bash
python3 app_backend.py --port 8000
```

### Production Deployment
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_backend:app
```

### Docker Integration
```bash
docker-compose up -d
docker-compose logs -f
```

## 🐛 Troubleshooting

### Dashboard won't load
1. Check API is running: http://localhost:5000/api/health
2. Clear browser cache: Ctrl+Shift+Del
3. Check console: F12 → Console tab

### Port 5000 in use
```bash
# Find process
lsof -i :5000

# Kill it
kill -9 <PID>

# Or use different port:
python3 app_backend.py --port 8000
```

### Mobile can't connect
1. Use computer IP (not localhost)
2. Both on same WiFi network
3. Firewall allows port 5000
4. Try restarting router

### Slow performance
- Use pagination (limit results)
- Enable auto-refresh (less frequent)
- Clear browser cache
- Reduce chart complexity

## 📈 Data Flow

```
Monitor Session (main.py)
    ↓
Data Collected (face, voice, breathing)
    ↓
Stored in Database (database.py)
    ↓
API Queries (app_backend.py)
    ↓
Dashboard Display (app_dashboard.html)
    ↓
User Views Results (browser/mobile)
```

## 🔐 Security (Current State)

⚠️ **Development Mode:**
- No authentication
- All sessions accessible
- CORS allows all origins
- No rate limiting

✅ **For Production:**
- Add user authentication
- Implement JWT tokens
- Enable HTTPS
- Add access controls
- Enable rate limiting

## 📚 File Reference

| File | Purpose | Size | Status |
|------|---------|------|--------|
| `app_backend.py` | Flask API server | 600+ lines | ✓ Complete |
| `app_dashboard.html` | Web dashboard | 1200+ lines | ✓ Complete |
| `app-start.sh` | Quick start script | 150+ lines | ✓ Complete |
| `requirements_app.txt` | Python dependencies | 5 packages | ✓ Complete |
| `APP_GUIDE.md` | Full documentation | 500+ lines | ✓ Complete |

## 🎓 Learning Resources

- Dashboard code: Comments in JavaScript
- API code: Comments in Python
- API docs: See APP_GUIDE.md "REST API Endpoints"
- Examples: APP_GUIDE.md "Sample API Calls"

## 🎯 Common Tasks

### View all sessions
```bash
curl http://localhost:5000/api/sessions | python -m json.tool
```

### Get session statistics
```bash
curl http://localhost:5000/api/statistics/session/1
```

### Compare two sessions
```bash
curl "http://localhost:5000/api/compare/sessions?ids=1&ids=2"
```

### Get recommendations
```bash
curl http://localhost:5000/api/recommendations/1
```

### Get time range stats
```bash
curl http://localhost:5000/api/statistics/timerange?days=30
```

## 📞 Support

For issues:
1. Check APP_GUIDE.md Troubleshooting section
2. Check terminal output for error messages
3. Use browser F12 Console for client-side errors
4. Check port availability: `lsof -i :5000`

## ✅ Quick Checklist

Before reporting issues:
- [ ] Python 3 installed
- [ ] Flask installed (`pip install flask flask-cors`)
- [ ] Database exists
- [ ] Port 5000 available
- [ ] Running from correct directory
- [ ] Database has session data
- [ ] Browser cache cleared
- [ ] No firewall blocking port 5000

## 🚀 Next Steps

1. **Start the app**: `./app-start.sh`
2. **Run monitoring**: `make monitor`
3. **View results**: Open dashboard
4. **Export data**: Use API endpoint
5. **Share access**: Give IP to friends/family
6. **Deploy**: Use Docker for production

---

**Last Updated**: February 10, 2026  
**Status**: ✅ Production Ready  
**Version**: 2.0
