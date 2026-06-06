"""
Database Module for Wellbeing Monitoring System
Handles persistent storage of all monitoring data:
- Session information
- Face analysis results
- Voice analysis results
- Breathing analysis results
- Overall wellbeing scores and recommendations
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class WellbeingDatabase:
    """Manages SQLite database for wellbeing monitoring data."""
    
    def __init__(self, db_path: str = "wellbeing_monitor.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._init_database()
    
    def _init_database(self):
        """Create database and initialize schema if needed."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration_seconds REAL,
                user_notes TEXT,
                environment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create face analysis records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                fatigue_score REAL,
                eye_closure_ratio REAL,
                blink_rate REAL,
                blink_consistency REAL,
                eye_openness REAL,
                mouth_openness REAL,
                face_detected BOOLEAN,
                primary_indicator TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Create voice analysis records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                stress_score REAL,
                anxiety_score REAL,
                pitch_hz REAL,
                pitch_variation REAL,
                speech_rate_wpm REAL,
                loudness_rms REAL,
                loudness_status TEXT,
                voice_quality TEXT,
                primary_indicator TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Create breathing analysis records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breathing_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                breathing_rate REAL,
                breathing_status TEXT,
                breathing_irregularity REAL,
                energy_level REAL,
                rhythm_consistency REAL,
                primary_indicator TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Create overall wellbeing records (aggregated results)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wellbeing_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                overall_concern_score REAL,
                primary_concern TEXT,
                secondary_concern TEXT,
                fatigue_score REAL,
                stress_score REAL,
                anxiety_score REAL,
                breathing_score REAL,
                recommendations TEXT,
                concern_level TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Create recommendations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                wellbeing_analysis_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                recommendation_text TEXT,
                recommendation_type TEXT,
                priority TEXT,
                category TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (wellbeing_analysis_id) REFERENCES wellbeing_analysis(id)
            )
        ''')
        
        self.connection.commit()
        print(f"✅ Database initialized: {self.db_path}")
    
    def create_session(self, user_notes: str = "", environment: str = "office") -> int:
        """
        Create a new monitoring session.
        
        Args:
            user_notes: Optional user notes about the session
            environment: Environment context (office, home, etc.)
            
        Returns:
            int: Session ID
        """
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO sessions (start_time, user_notes, environment)
            VALUES (?, ?, ?)
        ''', (now, user_notes, environment))
        
        self.connection.commit()
        session_id = cursor.lastrowid
        print(f"📝 Session {session_id} created at {now}")
        return session_id
    
    def end_session(self, session_id: int):
        """
        End a monitoring session.
        
        Args:
            session_id: Session ID to end
        """
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            SELECT start_time FROM sessions WHERE id = ?
        ''', (session_id,))
        
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row['start_time'])
            end_time = datetime.fromisoformat(now)
            duration = (end_time - start_time).total_seconds()
            
            cursor.execute('''
                UPDATE sessions 
                SET end_time = ?, duration_seconds = ?
                WHERE id = ?
            ''', (now, duration, session_id))
            
            self.connection.commit()
            print(f"✅ Session {session_id} ended. Duration: {duration:.1f}s")
    
    def store_face_analysis(self, session_id: int, face_data: Dict):
        """
        Store face analysis results.
        
        Args:
            session_id: Current session ID
            face_data: Dictionary from FaceAnalyzer.analyze_frame()
        """
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO face_analysis (
                session_id, timestamp, fatigue_score, eye_closure_ratio,
                blink_rate, blink_consistency, eye_openness, mouth_openness,
                face_detected, primary_indicator
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            now,
            face_data.get('fatigue_score', 0.0),
            face_data.get('eye_closure_ratio', 0.0),
            face_data.get('blink_rate', 0.0),
            face_data.get('blink_consistency', 0.0),
            face_data.get('eye_openness', 0.0),
            face_data.get('mouth_openness', 0.0),
            face_data.get('face_detected', False),
            face_data.get('primary_indicator', 'normal')
        ))
        
        self.connection.commit()
    
    def store_voice_analysis(self, session_id: int, voice_data: Dict):
        """
        Store voice analysis results.
        
        Args:
            session_id: Current session ID
            voice_data: Dictionary from VoiceAnalyzer.analyze_audio()
        """
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO voice_analysis (
                session_id, timestamp, stress_score, anxiety_score,
                pitch_hz, pitch_variation, speech_rate_wpm, loudness_rms,
                loudness_status, voice_quality, primary_indicator
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            now,
            voice_data.get('stress_score', 0.0),
            voice_data.get('anxiety_score', 0.0),
            voice_data.get('pitch_hz', 0.0),
            voice_data.get('pitch_variation', 0.0),
            voice_data.get('speech_rate_wpm', 0.0),
            voice_data.get('loudness_rms', 0.0),
            voice_data.get('loudness_status', 'normal'),
            voice_data.get('voice_quality', 'good'),
            voice_data.get('primary_indicator', 'normal')
        ))
        
        self.connection.commit()
    
    def store_breathing_analysis(self, session_id: int, breathing_data: Dict):
        """
        Store breathing analysis results.
        
        Args:
            session_id: Current session ID
            breathing_data: Dictionary from BreathingAnalyzer.analyze_audio()
        """
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO breathing_analysis (
                session_id, timestamp, breathing_rate, breathing_status,
                breathing_irregularity, energy_level, rhythm_consistency,
                primary_indicator
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            now,
            breathing_data.get('breathing_rate', 0.0),
            breathing_data.get('breathing_status', 'normal'),
            breathing_data.get('breathing_irregularity', 0.0),
            breathing_data.get('energy_level', 0.0),
            breathing_data.get('rhythm_consistency', 0.0),
            breathing_data.get('primary_indicator', 'normal')
        ))
        
        self.connection.commit()
    
    def store_wellbeing_analysis(self, session_id: int, analysis_data: Dict) -> int:
        """
        Store overall wellbeing analysis and recommendations.
        
        Args:
            session_id: Current session ID
            analysis_data: Dictionary from WellbeingMonitor.aggregate_analysis()
            
        Returns:
            int: Wellbeing analysis record ID
        """
        cursor = self.connection.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO wellbeing_analysis (
                session_id, timestamp, overall_concern_score, primary_concern,
                secondary_concern, fatigue_score, stress_score, anxiety_score,
                breathing_score, recommendations, concern_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            now,
            analysis_data.get('overall_concern_score', 0.0),
            analysis_data.get('primary_concern', 'unknown'),
            analysis_data.get('secondary_concern', 'none'),
            analysis_data.get('fatigue_score', 0.0),
            analysis_data.get('stress_score', 0.0),
            analysis_data.get('anxiety_score', 0.0),
            analysis_data.get('breathing_score', 0.0),
            json.dumps(analysis_data.get('recommendations', [])),
            analysis_data.get('concern_level', 'low')
        ))
        
        self.connection.commit()
        wellbeing_id = cursor.lastrowid
        
        # Store individual recommendations
        for rec in analysis_data.get('recommendations', []):
            cursor.execute('''
                INSERT INTO recommendations (
                    session_id, wellbeing_analysis_id, timestamp,
                    recommendation_text, recommendation_type, priority, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                wellbeing_id,
                now,
                rec.get('text', ''),
                rec.get('type', 'general'),
                rec.get('priority', 'medium'),
                rec.get('category', 'wellbeing')
            ))
        
        self.connection.commit()
        return wellbeing_id
    
    def get_session_summary(self, session_id: int) -> Dict:
        """
        Get comprehensive summary of a session.
        
        Args:
            session_id: Session ID to summarize
            
        Returns:
            dict: Complete session data
        """
        cursor = self.connection.cursor()
        
        # Get session info
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = dict(cursor.fetchone())
        
        # Get face analysis
        cursor.execute('SELECT * FROM face_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
        face_records = [dict(row) for row in cursor.fetchall()]
        
        # Get voice analysis
        cursor.execute('SELECT * FROM voice_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
        voice_records = [dict(row) for row in cursor.fetchall()]
        
        # Get breathing analysis
        cursor.execute('SELECT * FROM breathing_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
        breathing_records = [dict(row) for row in cursor.fetchall()]
        
        # Get wellbeing analysis
        cursor.execute('SELECT * FROM wellbeing_analysis WHERE session_id = ? ORDER BY timestamp', (session_id,))
        wellbeing_records = [dict(row) for row in cursor.fetchall()]
        
        # Get recommendations
        cursor.execute('SELECT * FROM recommendations WHERE session_id = ? ORDER BY timestamp', (session_id,))
        recommendations = [dict(row) for row in cursor.fetchall()]
        
        return {
            'session': session,
            'face_analysis': face_records,
            'voice_analysis': voice_records,
            'breathing_analysis': breathing_records,
            'wellbeing_analysis': wellbeing_records,
            'recommendations': recommendations
        }
    
    def get_session_statistics(self, session_id: int) -> Dict:
        """
        Calculate statistics for a session.
        
        Args:
            session_id: Session ID to analyze
            
        Returns:
            dict: Statistical summary
        """
        cursor = self.connection.cursor()
        
        stats = {}
        
        # Face analysis stats
        cursor.execute('''
            SELECT 
                AVG(fatigue_score) as avg_fatigue,
                MAX(fatigue_score) as max_fatigue,
                AVG(blink_rate) as avg_blink_rate,
                AVG(eye_openness) as avg_eye_openness
            FROM face_analysis
            WHERE session_id = ?
        ''', (session_id,))
        face_stats = dict(cursor.fetchone())
        stats['face'] = face_stats
        
        # Voice analysis stats
        cursor.execute('''
            SELECT 
                AVG(stress_score) as avg_stress,
                MAX(stress_score) as max_stress,
                AVG(anxiety_score) as avg_anxiety,
                AVG(pitch_hz) as avg_pitch,
                AVG(speech_rate_wpm) as avg_speech_rate,
                AVG(loudness_rms) as avg_loudness
            FROM voice_analysis
            WHERE session_id = ?
        ''', (session_id,))
        voice_stats = dict(cursor.fetchone())
        stats['voice'] = voice_stats
        
        # Breathing analysis stats
        cursor.execute('''
            SELECT 
                AVG(breathing_rate) as avg_breathing_rate,
                MAX(breathing_rate) as max_breathing_rate,
                AVG(breathing_irregularity) as avg_irregularity
            FROM breathing_analysis
            WHERE session_id = ?
        ''', (session_id,))
        breathing_stats = dict(cursor.fetchone())
        stats['breathing'] = breathing_stats
        
        # Wellbeing stats
        cursor.execute('''
            SELECT 
                AVG(overall_concern_score) as avg_concern,
                MAX(overall_concern_score) as max_concern,
                COUNT(*) as analysis_count
            FROM wellbeing_analysis
            WHERE session_id = ?
        ''', (session_id,))
        wellbeing_stats = dict(cursor.fetchone())
        stats['wellbeing'] = wellbeing_stats
        
        return stats
    
    def get_user_history(self, limit: int = 10) -> List[Dict]:
        """
        Get history of recent sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            list: Recent sessions with basic info
        """
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id, start_time, end_time, duration_seconds, user_notes, environment
            FROM sessions
            ORDER BY start_time DESC
            LIMIT ?
        ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def generate_report(self, session_id: int) -> str:
        """
        Generate a text report of a session.
        
        Args:
            session_id: Session ID to report on
            
        Returns:
            str: Formatted report
        """
        summary = self.get_session_summary(session_id)
        stats = self.get_session_statistics(session_id)
        
        report = []
        report.append("=" * 70)
        report.append("WELLBEING MONITORING SESSION REPORT")
        report.append("=" * 70)
        
        session = summary['session']
        report.append(f"\nSession ID: {session['id']}")
        report.append(f"Start Time: {session['start_time']}")
        report.append(f"End Time: {session['end_time']}")
        report.append(f"Duration: {session['duration_seconds']:.1f} seconds")
        if session['user_notes']:
            report.append(f"Notes: {session['user_notes']}")
        report.append(f"Environment: {session['environment']}")
        
        # Face analysis summary
        report.append("\n" + "-" * 70)
        report.append("FACE ANALYSIS")
        report.append("-" * 70)
        face_stats = stats['face']
        if face_stats['avg_fatigue'] is not None:
            report.append(f"Average Fatigue Score: {face_stats['avg_fatigue']:.2f}")
            report.append(f"Peak Fatigue: {face_stats['max_fatigue']:.2f}")
            report.append(f"Average Blink Rate: {face_stats['avg_blink_rate']:.2f} blinks/min")
            report.append(f"Average Eye Openness: {face_stats['avg_eye_openness']:.2f}%")
        
        # Voice analysis summary
        report.append("\n" + "-" * 70)
        report.append("VOICE ANALYSIS")
        report.append("-" * 70)
        voice_stats = stats['voice']
        if voice_stats['avg_stress'] is not None:
            report.append(f"Average Stress Score: {voice_stats['avg_stress']:.2f}")
            report.append(f"Peak Stress: {voice_stats['max_stress']:.2f}")
            report.append(f"Average Anxiety Score: {voice_stats['avg_anxiety']:.2f}")
            report.append(f"Average Pitch: {voice_stats['avg_pitch']:.1f} Hz")
            report.append(f"Average Speech Rate: {voice_stats['avg_speech_rate']:.1f} WPM")
            report.append(f"Average Loudness: {voice_stats['avg_loudness']:.3f} RMS")
        
        # Breathing analysis summary
        report.append("\n" + "-" * 70)
        report.append("BREATHING ANALYSIS")
        report.append("-" * 70)
        breathing_stats = stats['breathing']
        if breathing_stats['avg_breathing_rate'] is not None:
            report.append(f"Average Breathing Rate: {breathing_stats['avg_breathing_rate']:.1f} BPM")
            report.append(f"Peak Breathing Rate: {breathing_stats['max_breathing_rate']:.1f} BPM")
            report.append(f"Breathing Irregularity: {breathing_stats['avg_irregularity']:.2f}")
        
        # Overall wellbeing
        report.append("\n" + "-" * 70)
        report.append("OVERALL WELLBEING")
        report.append("-" * 70)
        wellbeing_stats = stats['wellbeing']
        if wellbeing_stats['avg_concern'] is not None:
            report.append(f"Average Concern Score: {wellbeing_stats['avg_concern']:.2f}")
            report.append(f"Peak Concern: {wellbeing_stats['max_concern']:.2f}")
            report.append(f"Analysis Count: {wellbeing_stats['analysis_count']}")
        
        # Recommendations
        if summary['recommendations']:
            report.append("\n" + "-" * 70)
            report.append("RECOMMENDATIONS")
            report.append("-" * 70)
            for rec in summary['recommendations']:
                report.append(f"• [{rec['priority'].upper()}] {rec['recommendation_text']}")
        
        report.append("\n" + "=" * 70)
        
        return "\n".join(report)
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("✅ Database connection closed")


if __name__ == "__main__":
    # Example usage
    db = WellbeingDatabase()
    
    # Create a sample session
    session_id = db.create_session(user_notes="Test monitoring session", environment="office")
    
    # Store sample data
    face_data = {
        'fatigue_score': 0.3,
        'eye_closure_ratio': 0.2,
        'blink_rate': 15.0,
        'blink_consistency': 0.8,
        'eye_openness': 0.85,
        'mouth_openness': 0.1,
        'face_detected': True,
        'primary_indicator': 'normal'
    }
    
    voice_data = {
        'stress_score': 0.2,
        'anxiety_score': 0.1,
        'pitch_hz': 150.0,
        'pitch_variation': 0.05,
        'speech_rate_wpm': 160.0,
        'loudness_rms': 0.15,
        'loudness_status': 'normal',
        'voice_quality': 'good',
        'primary_indicator': 'normal'
    }
    
    breathing_data = {
        'breathing_rate': 16.0,
        'breathing_status': 'normal',
        'breathing_irregularity': 0.1,
        'energy_level': 0.7,
        'rhythm_consistency': 0.9,
        'primary_indicator': 'normal'
    }
    
    db.store_face_analysis(session_id, face_data)
    db.store_voice_analysis(session_id, voice_data)
    db.store_breathing_analysis(session_id, breathing_data)
    
    analysis_data = {
        'overall_concern_score': 0.2,
        'primary_concern': 'none',
        'secondary_concern': 'none',
        'fatigue_score': 0.3,
        'stress_score': 0.2,
        'anxiety_score': 0.1,
        'breathing_score': 0.1,
        'recommendations': [
            {'text': 'You are doing well', 'type': 'positive', 'priority': 'low', 'category': 'wellbeing'}
        ],
        'concern_level': 'low'
    }
    
    db.store_wellbeing_analysis(session_id, analysis_data)
    
    # End session
    db.end_session(session_id)
    
    # Get summary
    summary = db.get_session_summary(session_id)
    print("\nSession Summary retrieved successfully")
    
    # Generate report
    report = db.generate_report(session_id)
    print(report)
    
    db.close()
