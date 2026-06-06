"""
Flask REST API Backend for Wellbeing Monitoring System
Provides REST endpoints for mobile/web app to access monitoring data
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import json
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from database import WellbeingDatabase
import os
from pathlib import Path

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for mobile/web clients

# Configuration
app.config['JSON_SORT_KEYS'] = False
app.secret_key = 'wellbeing-monitoring-secret-key'

# Initialize database
db_instance = WellbeingDatabase()


# ═════════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health_check():
    """Check API health status"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0',
            'service': 'wellbeing-monitoring-api'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
def system_status():
    """Get current system status"""
    try:
        data_dir = Path('./data')
        reports_dir = Path('./reports')
        
        return jsonify({
            'status': 'running',
            'database_available': True,
            'data_directory': str(data_dir),
            'has_data': data_dir.exists(),
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# SESSION ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get all sessions with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) as count FROM sessions')
        total = cursor.fetchone()['count']
        
        # Get paginated sessions
        cursor.execute('''
            SELECT id, user_id, start_time, end_time, duration_minutes,
                   session_type, status, notes
            FROM sessions
            ORDER BY start_time DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        sessions = []
        for row in cursor.fetchall():
            sessions.append(dict(row))
        
        conn.close()
        
        return jsonify({
            'sessions': sessions,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total,
                'pages': (total + limit - 1) // limit
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/<int:session_id>', methods=['GET'])
def get_session_details(session_id):
    """Get detailed session data"""
    try:
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = dict(session)
        
        # Get face analysis data
        cursor.execute('SELECT * FROM face_analysis WHERE session_id = ?', (session_id,))
        session_data['face_analysis'] = [dict(row) for row in cursor.fetchall()]
        
        # Get voice analysis data
        cursor.execute('SELECT * FROM voice_analysis WHERE session_id = ?', (session_id,))
        session_data['voice_analysis'] = [dict(row) for row in cursor.fetchall()]
        
        # Get breathing analysis data
        cursor.execute('SELECT * FROM breathing_analysis WHERE session_id = ?', (session_id,))
        session_data['breathing_analysis'] = [dict(row) for row in cursor.fetchall()]
        
        # Get wellbeing analysis data
        cursor.execute('SELECT * FROM wellbeing_analysis WHERE session_id = ?', (session_id,))
        session_data['wellbeing_analysis'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(session_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sessions/recent', methods=['GET'])
def get_recent_sessions():
    """Get recent sessions (last 7 days)"""
    try:
        days = request.args.get('days', 7, type=int)
        
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, user_id, start_time, end_time, duration_minutes,
                   session_type, status
            FROM sessions
            WHERE start_time >= datetime('now', '-' || ? || ' days')
            ORDER BY start_time DESC
        ''', (days,))
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'sessions': sessions,
            'days': days
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# ANALYSIS DATA ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/analysis/face/<int:session_id>', methods=['GET'])
def get_face_analysis(session_id):
    """Get face analysis data for a session"""
    try:
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM face_analysis WHERE session_id = ?', (session_id,))
        data = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'analysis_type': 'face',
            'data': data,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis/voice/<int:session_id>', methods=['GET'])
def get_voice_analysis(session_id):
    """Get voice analysis data for a session"""
    try:
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM voice_analysis WHERE session_id = ?', (session_id,))
        data = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'analysis_type': 'voice',
            'data': data,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis/breathing/<int:session_id>', methods=['GET'])
def get_breathing_analysis(session_id):
    """Get breathing analysis data for a session"""
    try:
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM breathing_analysis WHERE session_id = ?', (session_id,))
        data = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'analysis_type': 'breathing',
            'data': data,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analysis/wellbeing/<int:session_id>', methods=['GET'])
def get_wellbeing_analysis(session_id):
    """Get wellbeing analysis data for a session"""
    try:
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM wellbeing_analysis WHERE session_id = ?', (session_id,))
        data = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'analysis_type': 'wellbeing',
            'data': data,
            'count': len(data)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# STATISTICS & REPORTING ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/statistics/session/<int:session_id>', methods=['GET'])
def get_session_statistics(session_id):
    """Get statistics for a specific session"""
    try:
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = dict(cursor.fetchone())
        
        # Calculate face emotions average
        cursor.execute('''
            SELECT emotion, AVG(CAST(confidence AS FLOAT)) as avg_confidence
            FROM face_analysis
            WHERE session_id = ?
            GROUP BY emotion
        ''', (session_id,))
        face_emotions = {row['emotion']: row['avg_confidence'] for row in cursor.fetchall()}
        
        # Calculate voice metrics average
        cursor.execute('''
            SELECT AVG(CAST(energy AS FLOAT)) as avg_energy,
                   AVG(CAST(pitch AS FLOAT)) as avg_pitch,
                   COUNT(*) as samples
            FROM voice_analysis
            WHERE session_id = ?
        ''', (session_id,))
        voice_stats = dict(cursor.fetchone())
        
        # Calculate breathing average
        cursor.execute('''
            SELECT AVG(CAST(rate AS FLOAT)) as avg_rate,
                   AVG(CAST(depth AS FLOAT)) as avg_depth,
                   COUNT(*) as samples
            FROM breathing_analysis
            WHERE session_id = ?
        ''', (session_id,))
        breathing_stats = dict(cursor.fetchone())
        
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'session_info': session,
            'face_emotions': face_emotions,
            'voice_metrics': voice_stats,
            'breathing_metrics': breathing_stats
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/statistics/timerange', methods=['GET'])
def get_statistics_timerange():
    """Get statistics for a time range"""
    try:
        days = request.args.get('days', 7, type=int)
        
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get sessions in range
        cursor.execute('''
            SELECT id, start_time, duration_minutes
            FROM sessions
            WHERE start_time >= datetime('now', '-' || ? || ' days')
        ''', (days,))
        sessions = [dict(row) for row in cursor.fetchall()]
        
        # Calculate average metrics
        cursor.execute('''
            SELECT COUNT(DISTINCT session_id) as total_sessions,
                   COUNT(*) as total_face_samples
            FROM face_analysis
            WHERE session_id IN (
                SELECT id FROM sessions
                WHERE start_time >= datetime('now', '-' || ? || ' days')
            )
        ''', (days,))
        face_data = dict(cursor.fetchone())
        
        cursor.execute('''
            SELECT AVG(CAST(energy AS FLOAT)) as avg_energy,
                   AVG(CAST(pitch AS FLOAT)) as avg_pitch
            FROM voice_analysis
            WHERE session_id IN (
                SELECT id FROM sessions
                WHERE start_time >= datetime('now', '-' || ? || ' days')
            )
        ''', (days,))
        voice_data = dict(cursor.fetchone())
        
        cursor.execute('''
            SELECT AVG(CAST(rate AS FLOAT)) as avg_breathing_rate,
                   AVG(CAST(depth AS FLOAT)) as avg_breathing_depth
            FROM breathing_analysis
            WHERE session_id IN (
                SELECT id FROM sessions
                WHERE start_time >= datetime('now', '-' || ? || ' days')
            )
        ''', (days,))
        breathing_data = dict(cursor.fetchone())
        
        conn.close()
        
        return jsonify({
            'timerange_days': days,
            'sessions_count': len(sessions),
            'face_statistics': face_data,
            'voice_statistics': voice_data,
            'breathing_statistics': breathing_data,
            'sessions': sessions
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS ENDPOINT
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/recommendations/<int:session_id>', methods=['GET'])
def get_recommendations(session_id):
    """Get recommendations for a session"""
    try:
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, category, recommendation, priority, 
                   JSON_EXTRACT(metadata, '$') as metadata
            FROM recommendations
            WHERE session_id = ?
            ORDER BY priority DESC, timestamp DESC
        ''', (session_id,))
        
        recommendations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'session_id': session_id,
            'recommendations': recommendations,
            'count': len(recommendations)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# EXPORT ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/export/session/<int:session_id>', methods=['GET'])
def export_session(session_id):
    """Export session data as JSON"""
    try:
        format_type = request.args.get('format', 'json')
        
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all session data
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = dict(cursor.fetchone())
        
        cursor.execute('SELECT * FROM face_analysis WHERE session_id = ?', (session_id,))
        session['face_data'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM voice_analysis WHERE session_id = ?', (session_id,))
        session['voice_data'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM breathing_analysis WHERE session_id = ?', (session_id,))
        session['breathing_data'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM wellbeing_analysis WHERE session_id = ?', (session_id,))
        session['wellbeing_data'] = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute('SELECT * FROM recommendations WHERE session_id = ?', (session_id,))
        session['recommendations'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify(session), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# COMPARISON ENDPOINTS
# ═════════════════════════════════════════════════════════════════════════════

@app.route('/api/compare/sessions', methods=['GET'])
def compare_sessions():
    """Compare two or more sessions"""
    try:
        session_ids = request.args.getlist('ids', type=int)
        
        if len(session_ids) < 2:
            return jsonify({'error': 'At least 2 session IDs required'}), 400
        
        conn = sqlite3.connect(db_instance.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        comparison = {}
        
        for sid in session_ids:
            cursor.execute('SELECT * FROM sessions WHERE id = ?', (sid,))
            session = cursor.fetchone()
            
            if not session:
                continue
            
            cursor.execute('''
                SELECT AVG(CAST(confidence AS FLOAT)) as avg_confidence
                FROM face_analysis WHERE session_id = ?
            ''', (sid,))
            face_avg = cursor.fetchone()['avg_confidence']
            
            cursor.execute('''
                SELECT AVG(CAST(energy AS FLOAT)) as avg_energy
                FROM voice_analysis WHERE session_id = ?
            ''', (sid,))
            voice_avg = cursor.fetchone()['avg_energy']
            
            cursor.execute('''
                SELECT AVG(CAST(rate AS FLOAT)) as avg_rate
                FROM breathing_analysis WHERE session_id = ?
            ''', (sid,))
            breathing_avg = cursor.fetchone()['avg_rate']
            
            comparison[f'session_{sid}'] = {
                'session_id': sid,
                'start_time': dict(session)['start_time'],
                'duration': dict(session)['duration_minutes'],
                'face_confidence': face_avg,
                'voice_energy': voice_avg,
                'breathing_rate': breathing_avg
            }
        
        conn.close()
        
        return jsonify({
            'comparison': comparison,
            'session_count': len(comparison)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═════════════════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'status': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'status': 500
    }), 500


# ═════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   Wellbeing Monitoring System - REST API Backend          ║
    ║   Running on: http://localhost:5000                       ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    print("\nAPI Documentation: http://localhost:5000/api/docs")
    print("Health Check: http://localhost:5000/api/health")
    print("\n📚 Available Endpoints:")
    print("   GET  /api/health                    - Health status")
    print("   GET  /api/status                    - System status")
    print("   GET  /api/sessions                  - List all sessions")
    print("   GET  /api/sessions/<id>             - Session details")
    print("   GET  /api/sessions/recent           - Recent sessions")
    print("   GET  /api/analysis/face/<id>        - Face analysis")
    print("   GET  /api/analysis/voice/<id>       - Voice analysis")
    print("   GET  /api/analysis/breathing/<id>   - Breathing analysis")
    print("   GET  /api/analysis/wellbeing/<id>   - Wellbeing analysis")
    print("   GET  /api/statistics/session/<id>   - Session statistics")
    print("   GET  /api/statistics/timerange      - Statistics for time range")
    print("   GET  /api/recommendations/<id>      - Session recommendations")
    print("   GET  /api/export/session/<id>       - Export session data")
    print("   GET  /api/compare/sessions          - Compare sessions")
    print()
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
