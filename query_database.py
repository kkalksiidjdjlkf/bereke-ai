"""
Database Query Utility
Allows viewing, analyzing, and exporting monitoring data from the database.

Usage:
    python query_database.py              # Show menu
    python query_database.py --sessions   # List all sessions
    python query_database.py --session 1  # Show session 1 details
    python query_database.py --report 1   # Generate report for session 1
    python query_database.py --stats 1    # Show statistics for session 1
"""

import argparse
import json
from datetime import datetime
from database import WellbeingDatabase
from tabulate import tabulate


class DatabaseQueryTool:
    """Tool for querying and analyzing wellbeing database."""
    
    def __init__(self, db_path="wellbeing_monitor.db"):
        """Initialize query tool."""
        self.db = WellbeingDatabase(db_path)
    
    def list_sessions(self):
        """Display all monitoring sessions."""
        sessions = self.db.get_user_history(limit=100)
        
        if not sessions:
            print("❌ No sessions found in database.")
            return
        
        print("\n" + "="*100)
        print("📋 ALL MONITORING SESSIONS")
        print("="*100)
        
        table_data = []
        for session in sessions:
            duration = session['duration_seconds']
            if duration:
                duration_str = f"{duration:.1f}s"
            else:
                duration_str = "Ongoing"
            
            table_data.append([
                session['id'],
                session['start_time'][:19],
                duration_str,
                session['environment'],
                session['user_notes'][:40] if session['user_notes'] else "-"
            ])
        
        headers = ["ID", "Start Time", "Duration", "Environment", "Notes"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print(f"\nTotal sessions: {len(sessions)}")
    
    def show_session_details(self, session_id: int):
        """Display detailed information about a session."""
        summary = self.db.get_session_summary(session_id)
        stats = self.db.get_session_statistics(session_id)
        
        session = summary['session']
        
        print("\n" + "="*100)
        print(f"📊 SESSION {session_id} DETAILS")
        print("="*100)
        
        # Session info
        print(f"\n📌 Session Information:")
        print(f"  • ID: {session['id']}")
        print(f"  • Start: {session['start_time']}")
        print(f"  • End: {session['end_time']}")
        if session['duration_seconds']:
            print(f"  • Duration: {session['duration_seconds']:.1f} seconds")
        print(f"  • Environment: {session['environment']}")
        if session['user_notes']:
            print(f"  • Notes: {session['user_notes']}")
        
        # Face analysis
        face_stats = stats['face']
        print(f"\n👤 Face Analysis:")
        if face_stats['avg_fatigue'] is not None:
            print(f"  • Average Fatigue Score: {face_stats['avg_fatigue']:.3f}")
            print(f"  • Peak Fatigue: {face_stats['max_fatigue']:.3f}")
            print(f"  • Average Blink Rate: {face_stats['avg_blink_rate']:.1f} blinks/min")
            print(f"  • Average Eye Openness: {face_stats['avg_eye_openness']:.1%}")
            print(f"  • Samples: {len(summary['face_analysis'])}")
        else:
            print(f"  • No data available")
        
        # Voice analysis
        voice_stats = stats['voice']
        print(f"\n🎤 Voice Analysis:")
        if voice_stats['avg_stress'] is not None:
            print(f"  • Average Stress Score: {voice_stats['avg_stress']:.3f}")
            print(f"  • Peak Stress: {voice_stats['max_stress']:.3f}")
            print(f"  • Average Anxiety Score: {voice_stats['avg_anxiety']:.3f}")
            print(f"  • Average Pitch: {voice_stats['avg_pitch']:.1f} Hz")
            print(f"  • Average Speech Rate: {voice_stats['avg_speech_rate']:.1f} WPM")
            print(f"  • Average Loudness: {voice_stats['avg_loudness']:.4f} RMS")
            print(f"  • Samples: {len(summary['voice_analysis'])}")
        else:
            print(f"  • No data available")
        
        # Breathing analysis
        breathing_stats = stats['breathing']
        print(f"\n💨 Breathing Analysis:")
        if breathing_stats['avg_breathing_rate'] is not None:
            print(f"  • Average Breathing Rate: {breathing_stats['avg_breathing_rate']:.1f} BPM")
            print(f"  • Peak Breathing Rate: {breathing_stats['max_breathing_rate']:.1f} BPM")
            print(f"  • Breathing Irregularity: {breathing_stats['avg_irregularity']:.3f}")
            print(f"  • Samples: {len(summary['breathing_analysis'])}")
        else:
            print(f"  • No data available")
        
        # Overall wellbeing
        wellbeing_stats = stats['wellbeing']
        print(f"\n💚 Overall Wellbeing:")
        if wellbeing_stats['avg_concern'] is not None:
            print(f"  • Average Concern Score: {wellbeing_stats['avg_concern']:.3f}")
            print(f"  • Peak Concern: {wellbeing_stats['max_concern']:.3f}")
            print(f"  • Analyses: {wellbeing_stats['analysis_count']}")
        else:
            print(f"  • No data available")
        
        # Recommendations
        if summary['recommendations']:
            print(f"\n📝 Recommendations:")
            for rec in summary['recommendations']:
                priority_emoji = "⚠️ " if rec['priority'] == 'high' else "ℹ️ " if rec['priority'] == 'medium' else "✅ "
                print(f"  {priority_emoji}[{rec['priority'].upper()}] {rec['recommendation_text']}")
    
    def show_statistics(self, session_id: int):
        """Display statistics for a session."""
        stats = self.db.get_session_statistics(session_id)
        
        print("\n" + "="*100)
        print(f"📈 STATISTICS FOR SESSION {session_id}")
        print("="*100)
        
        # Face stats
        print(f"\n👤 Face Analysis Statistics:")
        face = stats['face']
        print(f"  Fatigue Score:")
        print(f"    Average: {face['avg_fatigue'] or 'N/A'}")
        print(f"    Maximum: {face['max_fatigue'] or 'N/A'}")
        print(f"  Blink Rate:")
        print(f"    Average: {face['avg_blink_rate'] or 'N/A'} blinks/min")
        print(f"  Eye Openness:")
        print(f"    Average: {(face['avg_eye_openness'] or 0)*100:.1f}%")
        
        # Voice stats
        print(f"\n🎤 Voice Analysis Statistics:")
        voice = stats['voice']
        print(f"  Stress Score:")
        print(f"    Average: {voice['avg_stress'] or 'N/A'}")
        print(f"    Maximum: {voice['max_stress'] or 'N/A'}")
        print(f"  Anxiety Score:")
        print(f"    Average: {voice['avg_anxiety'] or 'N/A'}")
        print(f"  Pitch:")
        print(f"    Average: {voice['avg_pitch'] or 'N/A'} Hz")
        print(f"  Speech Rate:")
        print(f"    Average: {voice['avg_speech_rate'] or 'N/A'} WPM")
        print(f"  Loudness:")
        print(f"    Average: {voice['avg_loudness'] or 'N/A'} RMS")
        
        # Breathing stats
        print(f"\n💨 Breathing Analysis Statistics:")
        breathing = stats['breathing']
        print(f"  Breathing Rate:")
        print(f"    Average: {breathing['avg_breathing_rate'] or 'N/A'} BPM")
        print(f"    Maximum: {breathing['max_breathing_rate'] or 'N/A'} BPM")
        print(f"  Irregularity:")
        print(f"    Average: {breathing['avg_irregularity'] or 'N/A'}")
        
        # Wellbeing stats
        print(f"\n💚 Overall Wellbeing Statistics:")
        wellbeing = stats['wellbeing']
        print(f"  Concern Score:")
        print(f"    Average: {wellbeing['avg_concern'] or 'N/A'}")
        print(f"    Maximum: {wellbeing['max_concern'] or 'N/A'}")
        print(f"  Analysis Count: {wellbeing['analysis_count'] or 'N/A'}")
    
    def generate_report(self, session_id: int, save_to_file: bool = True):
        """Generate and optionally save a comprehensive report."""
        report = self.db.generate_report(session_id)
        print(report)
        
        if save_to_file:
            filename = f"wellbeing_report_session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(report)
            print(f"\n✅ Report saved to: {filename}")
    
    def export_session_json(self, session_id: int):
        """Export session data as JSON."""
        summary = self.db.get_session_summary(session_id)
        stats = self.db.get_session_statistics(session_id)
        
        export_data = {
            'session': summary['session'],
            'statistics': {
                'face': stats['face'],
                'voice': stats['voice'],
                'breathing': stats['breathing'],
                'wellbeing': stats['wellbeing']
            },
            'analysis_counts': {
                'face_records': len(summary['face_analysis']),
                'voice_records': len(summary['voice_analysis']),
                'breathing_records': len(summary['breathing_analysis']),
                'wellbeing_analyses': len(summary['wellbeing_analysis']),
                'recommendations': len(summary['recommendations'])
            }
        }
        
        filename = f"session_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Data exported to: {filename}")
    
    def compare_sessions(self, session_ids: list):
        """Compare multiple sessions."""
        print("\n" + "="*100)
        print("📊 COMPARING SESSIONS")
        print("="*100)
        
        comparison_data = []
        
        for sid in session_ids:
            stats = self.db.get_session_statistics(sid)
            summary = self.db.get_session_summary(sid)
            
            session = summary['session']
            duration = session['duration_seconds'] or 0
            
            face = stats['face']
            voice = stats['voice']
            breathing = stats['breathing']
            wellbeing = stats['wellbeing']
            
            comparison_data.append({
                'Session ID': sid,
                'Duration (s)': f"{duration:.1f}",
                'Avg Fatigue': f"{face['avg_fatigue'] or 0:.3f}",
                'Avg Stress': f"{voice['avg_stress'] or 0:.3f}",
                'Avg Anxiety': f"{voice['avg_anxiety'] or 0:.3f}",
                'Avg Breathing': f"{breathing['avg_breathing_rate'] or 0:.1f}",
                'Avg Concern': f"{wellbeing['avg_concern'] or 0:.3f}"
            })
        
        print("\n")
        for data in comparison_data:
            for key, value in data.items():
                print(f"{key:20} {value:>15}")
            print()
    
    def show_menu(self):
        """Display interactive menu."""
        while True:
            print("\n" + "="*60)
            print("📊 WELLBEING DATABASE QUERY TOOL")
            print("="*60)
            print("\n1. List all sessions")
            print("2. Show session details")
            print("3. Generate report")
            print("4. Show statistics")
            print("5. Export session as JSON")
            print("6. Compare sessions")
            print("0. Exit")
            print()
            
            choice = input("Select option (0-6): ").strip()
            
            if choice == '1':
                self.list_sessions()
            elif choice == '2':
                try:
                    session_id = int(input("Enter session ID: "))
                    self.show_session_details(session_id)
                except ValueError:
                    print("❌ Invalid session ID")
            elif choice == '3':
                try:
                    session_id = int(input("Enter session ID: "))
                    self.generate_report(session_id)
                except ValueError:
                    print("❌ Invalid session ID")
            elif choice == '4':
                try:
                    session_id = int(input("Enter session ID: "))
                    self.show_statistics(session_id)
                except ValueError:
                    print("❌ Invalid session ID")
            elif choice == '5':
                try:
                    session_id = int(input("Enter session ID: "))
                    self.export_session_json(session_id)
                except ValueError:
                    print("❌ Invalid session ID")
            elif choice == '6':
                try:
                    ids_str = input("Enter session IDs (comma-separated): ")
                    session_ids = [int(i.strip()) for i in ids_str.split(',')]
                    self.compare_sessions(session_ids)
                except ValueError:
                    print("❌ Invalid session IDs")
            elif choice == '0':
                print("\n👋 Goodbye!\n")
                break
            else:
                print("❌ Invalid option")
        
        self.db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Wellbeing Database Query Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python query_database.py              # Interactive menu
  python query_database.py --sessions   # List all sessions
  python query_database.py --session 1  # Show session 1
  python query_database.py --report 1   # Generate report
  python query_database.py --stats 1    # Show statistics
  python query_database.py --export 1   # Export as JSON
        """
    )
    
    parser.add_argument('--sessions', action='store_true', help='List all sessions')
    parser.add_argument('--session', type=int, metavar='ID', help='Show session details')
    parser.add_argument('--report', type=int, metavar='ID', help='Generate report for session')
    parser.add_argument('--stats', type=int, metavar='ID', help='Show statistics for session')
    parser.add_argument('--export', type=int, metavar='ID', help='Export session as JSON')
    parser.add_argument('--compare', type=str, metavar='IDS', help='Compare sessions (comma-separated IDs)')
    parser.add_argument('--db', default='wellbeing_monitor.db', help='Database file path')
    
    args = parser.parse_args()
    
    query_tool = DatabaseQueryTool(args.db)
    
    # Handle command-line arguments
    if args.sessions:
        query_tool.list_sessions()
    elif args.session:
        query_tool.show_session_details(args.session)
    elif args.report:
        query_tool.generate_report(args.report)
    elif args.stats:
        query_tool.show_statistics(args.stats)
    elif args.export:
        query_tool.export_session_json(args.export)
    elif args.compare:
        try:
            session_ids = [int(i.strip()) for i in args.compare.split(',')]
            query_tool.compare_sessions(session_ids)
        except ValueError:
            print("❌ Invalid session IDs")
    else:
        # Interactive mode
        query_tool.show_menu()
    
    if not any([args.sessions, args.session, args.report, args.stats, args.export, args.compare]):
        pass  # Menu already closed
    else:
        query_tool.db.close()


if __name__ == "__main__":
    main()
