"""
Database API Demo
Shows how to use the WellbeingDatabase API programmatically.

Run this script to understand the database capabilities:
    python database_demo.py
"""

from database import WellbeingDatabase
from datetime import datetime
import json


def demo_basic_operations():
    """Demonstrate basic database operations."""
    print("\n" + "="*70)
    print("DEMO 1: Basic Database Operations")
    print("="*70)
    
    # Initialize database
    db = WellbeingDatabase("demo.db")
    
    # Create a new session
    print("\n1️⃣  Creating a new monitoring session...")
    session_id = db.create_session(
        user_notes="Demo monitoring session",
        environment="office"
    )
    print(f"   ✅ Session created with ID: {session_id}")
    
    # Store sample face analysis
    print("\n2️⃣  Storing face analysis data...")
    face_data = {
        'fatigue_score': 0.35,
        'eye_closure_ratio': 0.15,
        'blink_rate': 18.5,
        'blink_consistency': 0.85,
        'eye_openness': 0.90,
        'mouth_openness': 0.08,
        'face_detected': True,
        'primary_indicator': 'normal'
    }
    db.store_face_analysis(session_id, face_data)
    print(f"   ✅ Face analysis stored")
    print(f"      Fatigue Score: {face_data['fatigue_score']}")
    print(f"      Blink Rate: {face_data['blink_rate']} blinks/min")
    
    # Store sample voice analysis
    print("\n3️⃣  Storing voice analysis data...")
    voice_data = {
        'stress_score': 0.25,
        'anxiety_score': 0.15,
        'pitch_hz': 155.0,
        'pitch_variation': 0.08,
        'speech_rate_wpm': 165.0,
        'loudness_rms': 0.18,
        'loudness_status': 'normal',
        'voice_quality': 'good',
        'primary_indicator': 'normal'
    }
    db.store_voice_analysis(session_id, voice_data)
    print(f"   ✅ Voice analysis stored")
    print(f"      Stress Score: {voice_data['stress_score']}")
    print(f"      Pitch: {voice_data['pitch_hz']} Hz")
    
    # Store sample breathing analysis
    print("\n4️⃣  Storing breathing analysis data...")
    breathing_data = {
        'breathing_rate': 16.5,
        'breathing_status': 'normal',
        'breathing_irregularity': 0.12,
        'energy_level': 0.75,
        'rhythm_consistency': 0.88,
        'primary_indicator': 'normal'
    }
    db.store_breathing_analysis(session_id, breathing_data)
    print(f"   ✅ Breathing analysis stored")
    print(f"      Breathing Rate: {breathing_data['breathing_rate']} BPM")
    print(f"      Status: {breathing_data['breathing_status']}")
    
    # Store wellbeing analysis
    print("\n5️⃣  Storing aggregated wellbeing analysis...")
    wellbeing_data = {
        'overall_concern_score': 0.25,
        'primary_concern': 'none',
        'secondary_concern': 'none',
        'fatigue_score': face_data['fatigue_score'],
        'stress_score': voice_data['stress_score'],
        'anxiety_score': voice_data['anxiety_score'],
        'breathing_score': 0.1,
        'recommendations': [
            {'text': 'You are doing well. Keep up the healthy habits!', 
             'type': 'positive', 'priority': 'low', 'category': 'wellbeing'},
            {'text': 'Maintains good breathing patterns during monitoring', 
             'type': 'feedback', 'priority': 'low', 'category': 'breathing'}
        ],
        'concern_level': 'low'
    }
    db.store_wellbeing_analysis(session_id, wellbeing_data)
    print(f"   ✅ Wellbeing analysis stored")
    print(f"      Overall Concern Score: {wellbeing_data['overall_concern_score']}")
    print(f"      Concern Level: {wellbeing_data['concern_level']}")
    
    # End the session
    print("\n6️⃣  Ending monitoring session...")
    db.end_session(session_id)
    print(f"   ✅ Session {session_id} ended")
    
    return db, session_id


def demo_retrieval(db, session_id):
    """Demonstrate data retrieval operations."""
    print("\n" + "="*70)
    print("DEMO 2: Data Retrieval Operations")
    print("="*70)
    
    # Get session summary
    print("\n1️⃣  Retrieving session summary...")
    summary = db.get_session_summary(session_id)
    
    print(f"\n   Session Info:")
    session = summary['session']
    print(f"      ID: {session['id']}")
    print(f"      Start: {session['start_time']}")
    print(f"      Duration: {session['duration_seconds']:.1f}s")
    print(f"      Environment: {session['environment']}")
    
    print(f"\n   Records Stored:")
    print(f"      Face analyses: {len(summary['face_analysis'])}")
    print(f"      Voice analyses: {len(summary['voice_analysis'])}")
    print(f"      Breathing analyses: {len(summary['breathing_analysis'])}")
    print(f"      Wellbeing analyses: {len(summary['wellbeing_analysis'])}")
    print(f"      Recommendations: {len(summary['recommendations'])}")
    
    # Get statistics
    print("\n2️⃣  Calculating session statistics...")
    stats = db.get_session_statistics(session_id)
    
    print(f"\n   Face Statistics:")
    face_stats = stats['face']
    print(f"      Average Fatigue: {face_stats['avg_fatigue']:.3f}")
    print(f"      Max Fatigue: {face_stats['max_fatigue']:.3f}")
    print(f"      Average Blink Rate: {face_stats['avg_blink_rate']:.1f} blinks/min")
    
    print(f"\n   Voice Statistics:")
    voice_stats = stats['voice']
    print(f"      Average Stress: {voice_stats['avg_stress']:.3f}")
    print(f"      Max Stress: {voice_stats['max_stress']:.3f}")
    print(f"      Average Pitch: {voice_stats['avg_pitch']:.1f} Hz")
    
    print(f"\n   Breathing Statistics:")
    breathing_stats = stats['breathing']
    print(f"      Average Rate: {breathing_stats['avg_breathing_rate']:.1f} BPM")
    print(f"      Max Rate: {breathing_stats['max_breathing_rate']:.1f} BPM")
    
    print(f"\n   Overall Wellbeing:")
    wellbeing_stats = stats['wellbeing']
    print(f"      Average Concern: {wellbeing_stats['avg_concern']:.3f}")
    print(f"      Analyses Performed: {wellbeing_stats['analysis_count']}")


def demo_reports(db, session_id):
    """Demonstrate report generation."""
    print("\n" + "="*70)
    print("DEMO 3: Report Generation")
    print("="*70)
    
    print("\n1️⃣  Generating comprehensive session report...")
    report = db.generate_report(session_id)
    
    # Save to file
    filename = f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w') as f:
        f.write(report)
    
    print(f"\n   ✅ Report generated and saved to: {filename}")
    print(f"\n   Report Preview (first 50 lines):")
    print("   " + "-"*66)
    lines = report.split('\n')
    for line in lines[:50]:
        print("   " + line)
    
    if len(lines) > 50:
        print(f"   ... ({len(lines) - 50} more lines)")


def demo_export(db, session_id):
    """Demonstrate data export in JSON format."""
    print("\n" + "="*70)
    print("DEMO 4: JSON Data Export")
    print("="*70)
    
    print("\n1️⃣  Exporting session data as JSON...")
    
    summary = db.get_session_summary(session_id)
    stats = db.get_session_statistics(session_id)
    
    export_data = {
        'session': {
            'id': summary['session']['id'],
            'start_time': summary['session']['start_time'],
            'duration_seconds': summary['session']['duration_seconds'],
            'environment': summary['session']['environment']
        },
        'statistics': {
            'face': dict(stats['face']),
            'voice': dict(stats['voice']),
            'breathing': dict(stats['breathing']),
            'wellbeing': dict(stats['wellbeing'])
        },
        'record_counts': {
            'face_analyses': len(summary['face_analysis']),
            'voice_analyses': len(summary['voice_analysis']),
            'breathing_analyses': len(summary['breathing_analysis']),
            'wellbeing_analyses': len(summary['wellbeing_analysis']),
            'recommendations': len(summary['recommendations'])
        }
    }
    
    filename = f"demo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    print(f"\n   ✅ Data exported to: {filename}")
    print(f"\n   Exported Data Structure:")
    print(f"      • Session metadata")
    print(f"      • Statistical summaries")
    print(f"      • Record counts")
    print(f"\n   JSON Preview:")
    print("   " + "-"*66)
    preview = json.dumps(export_data, indent=2, default=str)
    for line in preview.split('\n')[:30]:
        print("   " + line)


def demo_history():
    """Demonstrate session history retrieval."""
    print("\n" + "="*70)
    print("DEMO 5: Session History")
    print("="*70)
    
    db = WellbeingDatabase("demo.db")
    
    print("\n1️⃣  Retrieving last 10 sessions from history...")
    history = db.get_user_history(limit=10)
    
    if history:
        print(f"\n   Found {len(history)} session(s):\n")
        for session in history:
            duration = session['duration_seconds']
            duration_str = f"{duration:.1f}s" if duration else "Ongoing"
            print(f"      ID: {session['id']}")
            print(f"         Start: {session['start_time'][:19]}")
            print(f"         Duration: {duration_str}")
            print(f"         Environment: {session['environment']}")
            if session['user_notes']:
                print(f"         Notes: {session['user_notes']}")
            print()
    else:
        print("   No sessions found!")
    
    db.close()


def main():
    """Run all demos."""
    print("""
╔════════════════════════════════════════════════════════════╗
║         WELLBEING DATABASE API DEMONSTRATION               ║
║                                                            ║
║  This demo shows how to use the database API              ║
║  programmatically for storing and retrieving data.        ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Run basic operations demo
        db, session_id = demo_basic_operations()
        
        # Run retrieval demo
        demo_retrieval(db, session_id)
        
        # Run report generation demo
        demo_reports(db, session_id)
        
        # Run export demo
        demo_export(db, session_id)
        
        # Close database
        db.close()
        
        # Run history demo
        demo_history()
        
        # Final summary
        print("\n" + "="*70)
        print("✅ DEMO COMPLETE")
        print("="*70)
        print("""
The demonstration showed:
1. Creating monitoring sessions
2. Storing face, voice, and breathing analysis
3. Storing aggregated wellbeing analysis
4. Retrieving session summaries
5. Calculating statistics
6. Generating comprehensive reports
7. Exporting data to JSON
8. Retrieving session history

For more information, see:
  - DATABASE.md - Complete database documentation
  - query_database.py - Query tool for database exploration
  - main.py - Main monitoring system with auto-storage

Files created during demo:
  - demo.db - Sample database
  - demo_report_*.txt - Sample reports
  - demo_export_*.json - Sample JSON exports
        """)
    
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
