"""
Wellbeing Monitoring App - API Client Examples
Demonstrates how to use the REST API from Python
"""

import requests
import json
from datetime import datetime, timedelta
import time

try:
    from anthropic import Anthropic
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False

# Configuration
API_BASE_URL = 'http://localhost:5000/api'
TIMEOUT = 10
CLAUDE_MODEL = 'claude-3-5-haiku-20241022'  # Claude Haiku 4.5 model

class WellbeingAppClient:
    """Client for Wellbeing Monitoring REST API with Claude Haiku 4.5 AI support"""
    
    def __init__(self, base_url=API_BASE_URL, enable_claude=True):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'WellbeingMonitorClient/2.0'
        })
        
        # Claude Haiku 4.5 support
        self.claude_enabled = enable_claude and HAS_CLAUDE
        self.claude_client = Anthropic() if self.claude_enabled else None
        self.claude_conversation_history = []
    
    def _request(self, method, endpoint, **kwargs):
        """Make HTTP request to API"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(
                method, url, timeout=TIMEOUT, **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return None
    
    # ─────────────────────────────────────────────────────────────────────
    # Health & Status
    # ─────────────────────────────────────────────────────────────────────
    
    def health_check(self):
        """Check API health"""
        return self._request('GET', '/health')
    
    def system_status(self):
        """Get system status"""
        return self._request('GET', '/status')
    
    # ─────────────────────────────────────────────────────────────────────
    # Sessions
    # ─────────────────────────────────────────────────────────────────────
    
    def get_all_sessions(self, page=1, limit=20):
        """Get paginated session list"""
        return self._request('GET', f'/sessions?page={page}&limit={limit}')
    
    def get_session(self, session_id):
        """Get detailed session data"""
        return self._request('GET', f'/sessions/{session_id}')
    
    def get_recent_sessions(self, days=7):
        """Get sessions from last N days"""
        return self._request('GET', f'/sessions/recent?days={days}')
    
    # ─────────────────────────────────────────────────────────────────────
    # Analysis Data
    # ─────────────────────────────────────────────────────────────────────
    
    def get_face_analysis(self, session_id):
        """Get face analysis for session"""
        return self._request('GET', f'/analysis/face/{session_id}')
    
    def get_voice_analysis(self, session_id):
        """Get voice analysis for session"""
        return self._request('GET', f'/analysis/voice/{session_id}')
    
    def get_breathing_analysis(self, session_id):
        """Get breathing analysis for session"""
        return self._request('GET', f'/analysis/breathing/{session_id}')
    
    def get_wellbeing_analysis(self, session_id):
        """Get wellbeing metrics for session"""
        return self._request('GET', f'/analysis/wellbeing/{session_id}')
    
    # ─────────────────────────────────────────────────────────────────────
    # Statistics
    # ─────────────────────────────────────────────────────────────────────
    
    def get_session_stats(self, session_id):
        """Get statistics for specific session"""
        return self._request('GET', f'/statistics/session/{session_id}')
    
    def get_timerange_stats(self, days=7):
        """Get statistics for time range"""
        return self._request('GET', f'/statistics/timerange?days={days}')
    
    # ─────────────────────────────────────────────────────────────────────
    # Recommendations
    # ─────────────────────────────────────────────────────────────────────
    
    def get_recommendations(self, session_id):
        """Get recommendations for session"""
        return self._request('GET', f'/recommendations/{session_id}')
    
    # ─────────────────────────────────────────────────────────────────────
    # Export & Comparison
    # ─────────────────────────────────────────────────────────────────────
    
    def export_session(self, session_id):
        """Export complete session data"""
        return self._request('GET', f'/export/session/{session_id}')
    
    def compare_sessions(self, session_ids):
        """Compare multiple sessions"""
        ids_param = '&'.join([f'ids={sid}' for sid in session_ids])
        return self._request('GET', f'/compare/sessions?{ids_param}')
    
    # ─────────────────────────────────────────────────────────────────────
    # Claude Haiku 4.5 AI Analysis
    # ─────────────────────────────────────────────────────────────────────
    
    def ai_analyze_session(self, session_id):
        """Get AI-powered analysis of a session using Claude Haiku 4.5"""
        if not self.claude_enabled:
            return {'error': 'Claude Haiku 4.5 not enabled or anthropic not installed'}
        
        try:
            # Get session data
            session = self.get_session(session_id)
            face_data = self.get_face_analysis(session_id)
            voice_data = self.get_voice_analysis(session_id)
            breathing_data = self.get_breathing_analysis(session_id)
            
            # Prepare analysis prompt
            analysis_data = {
                'session': session,
                'face_metrics': face_data,
                'voice_metrics': voice_data,
                'breathing_metrics': breathing_data
            }
            
            prompt = f"""Analyze this wellbeing monitoring session data and provide insights:

Session Data:
{json.dumps(analysis_data, indent=2)}

Provide:
1. Key observations about the person's wellbeing
2. Emotional state assessment
3. Physical health indicators
4. Recommendations for improvement
5. Wellness score 0-100"""
            
            # Get Claude analysis
            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            return {
                'session_id': session_id,
                'model': CLAUDE_MODEL,
                'analysis': response.content[0].text
            }
        except Exception as e:
            return {'error': f'Claude analysis failed: {str(e)}'}
    
    def ai_get_recommendations(self, session_id):
        """Get personalized AI recommendations using Claude Haiku 4.5"""
        if not self.claude_enabled:
            return {'error': 'Claude Haiku 4.5 not enabled or anthropic not installed'}
        
        try:
            # Get session analysis
            session = self.get_session(session_id)
            stats = self.get_timerange_stats(days=7)
            
            prompt = f"""Based on this wellbeing session and 7-day statistics:

Current Session: {json.dumps(session, indent=2)}
7-Day Stats: {json.dumps(stats, indent=2)}

Provide detailed, actionable recommendations for:
1. Stress management
2. Sleep improvement
3. Physical activity
4. Breathing exercises
5. Mental health practices
6. Nutrition suggestions
Format as numbered list."""
            
            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1500,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            return {
                'session_id': session_id,
                'model': CLAUDE_MODEL,
                'recommendations': response.content[0].text
            }
        except Exception as e:
            return {'error': f'AI recommendations failed: {str(e)}'}
    
    def ai_chat(self, message):
        """Multi-turn conversation with Claude Haiku 4.5 about wellbeing"""
        if not self.claude_enabled:
            return {'error': 'Claude Haiku 4.5 not enabled or anthropic not installed'}
        
        try:
            # Add user message to history
            self.claude_conversation_history.append({
                'role': 'user',
                'content': message
            })
            
            # Get Claude response
            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1000,
                system="""You are a friendly AI wellness assistant powered by Claude Haiku 4.5. 
You help users understand their wellbeing monitoring data, provide health insights, 
and suggest improvements for physical and mental health.""",
                messages=self.claude_conversation_history
            )
            
            assistant_message = response.content[0].text
            
            # Add assistant response to history
            self.claude_conversation_history.append({
                'role': 'assistant',
                'content': assistant_message
            })
            
            return {
                'model': CLAUDE_MODEL,
                'message': assistant_message
            }
        except Exception as e:
            return {'error': f'AI chat failed: {str(e)}'}
    
    def ai_clear_history(self):
        """Clear conversation history"""
        self.claude_conversation_history = []
        return {'status': 'Conversation history cleared'}
    
    def ai_compare_with_analysis(self, session_ids):
        """Compare sessions with AI insights using Claude Haiku 4.5"""
        if not self.claude_enabled:
            return {'error': 'Claude Haiku 4.5 not enabled or anthropic not installed'}
        
        try:
            # Get comparison data
            comparison = self.compare_sessions(session_ids)
            
            prompt = f"""Analyze this comparison of multiple wellbeing sessions:

{json.dumps(comparison, indent=2)}

Provide:
1. Trends observed across sessions
2. Improvements or deteriorations
3. Patterns in emotional and physical states
4. Overall wellness trajectory
5. Priority areas for attention"""
            
            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1500,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            return {
                'model': CLAUDE_MODEL,
                'comparison_analysis': response.content[0].text
            }
        except Exception as e:
            return {'error': f'Comparison analysis failed: {str(e)}'}


# ═════════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═════════════════════════════════════════════════════════════════════════════

def example_basic_usage():
    """Basic API usage example"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic API Usage")
    print("="*70 + "\n")
    
    client = WellbeingAppClient()
    
    # Check health
    print("Checking API health...")
    health = client.health_check()
    if health:
        print(f"✓ API Status: {health.get('status')}")
        print(f"  Version: {health.get('version')}")
        print(f"  Timestamp: {health.get('timestamp')}")
    
    # Get recent sessions
    print("\nFetching recent sessions...")
    sessions_data = client.get_recent_sessions(days=7)
    if sessions_data:
        sessions = sessions_data.get('sessions', [])
        print(f"✓ Found {len(sessions)} sessions in last 7 days")
        for session in sessions[:3]:  # Show first 3
            print(f"  - Session {session['id']}: {session['start_time']}")


def example_detailed_analysis():
    """Detailed session analysis example"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Detailed Session Analysis")
    print("="*70 + "\n")
    
    client = WellbeingAppClient()
    
    # Get first session
    sessions_data = client.get_all_sessions(limit=1)
    if not sessions_data or not sessions_data.get('sessions'):
        print("No sessions available. Run monitoring first!")
        return
    
    session_id = sessions_data['sessions'][0]['id']
    print(f"Analyzing session {session_id}...\n")
    
    # Get analysis data
    face_data = client.get_face_analysis(session_id)
    voice_data = client.get_voice_analysis(session_id)
    breathing_data = client.get_breathing_analysis(session_id)
    
    print(f"Face Analysis: {len(face_data.get('data', []))} samples")
    if face_data.get('data'):
        avg_confidence = sum(d['confidence'] for d in face_data['data']) / len(face_data['data'])
        print(f"  Average Confidence: {avg_confidence:.2f}")
    
    print(f"\nVoice Analysis: {len(voice_data.get('data', []))} samples")
    if voice_data.get('data'):
        avg_energy = sum(d['energy'] for d in voice_data['data']) / len(voice_data['data'])
        print(f"  Average Energy: {avg_energy:.2f}")
    
    print(f"\nBreathing Analysis: {len(breathing_data.get('data', []))} samples")
    if breathing_data.get('data'):
        avg_rate = sum(d['rate'] for d in breathing_data['data']) / len(breathing_data['data'])
        print(f"  Average Rate: {avg_rate:.2f} bpm")


def example_statistics():
    """Statistics and trends example"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Statistics & Trends")
    print("="*70 + "\n")
    
    client = WellbeingAppClient()
    
    # Get statistics for different time ranges
    for days in [7, 14, 30]:
        stats = client.get_timerange_stats(days=days)
        if stats:
            print(f"\nLast {days} Days Statistics:")
            print(f"  Sessions: {stats.get('sessions_count')}")
            
            face_stats = stats.get('face_statistics', {})
            if face_stats.get('avg_confidence'):
                print(f"  Face Confidence: {face_stats['avg_confidence']:.2f}")
            
            voice_stats = stats.get('voice_statistics', {})
            if voice_stats.get('avg_energy'):
                print(f"  Voice Energy: {voice_stats['avg_energy']:.2f}")
            
            breathing_stats = stats.get('breathing_statistics', {})
            if breathing_stats.get('avg_breathing_rate'):
                print(f"  Breathing Rate: {breathing_stats['avg_breathing_rate']:.2f}")


def example_export_data():
    """Export session data example"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Export Session Data")
    print("="*70 + "\n")
    
    client = WellbeingAppClient()
    
    # Get first session
    sessions_data = client.get_all_sessions(limit=1)
    if not sessions_data or not sessions_data.get('sessions'):
        print("No sessions available!")
        return
    
    session_id = sessions_data['sessions'][0]['id']
    
    print(f"Exporting session {session_id}...\n")
    
    # Export session
    export_data = client.export_session(session_id)
    if export_data:
        # Save to file
        filename = f'session_{session_id}_export.json'
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        # Show summary
        print(f"✓ Exported to: {filename}")
        print(f"  Size: {len(json.dumps(export_data))} bytes")
        print(f"  Contains:")
        print(f"    - Face analysis: {len(export_data.get('face_data', []))} samples")
        print(f"    - Voice analysis: {len(export_data.get('voice_data', []))} samples")
        print(f"    - Breathing analysis: {len(export_data.get('breathing_data', []))} samples")


def example_comparison():
    """Compare sessions example"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Compare Sessions")
    print("="*70 + "\n")
    
    client = WellbeingAppClient()
    
    # Get multiple sessions
    sessions_data = client.get_all_sessions(limit=3)
    if not sessions_data or len(sessions_data.get('sessions', [])) < 2:
        print("Need at least 2 sessions to compare!")
        return
    
    session_ids = [s['id'] for s in sessions_data['sessions'][:3]]
    print(f"Comparing sessions: {session_ids}\n")
    
    # Compare
    comparison = client.compare_sessions(session_ids)
    if comparison:
        print("Comparison Results:")
        for key, data in comparison.get('comparison', {}).items():
            print(f"\n  {key}:")
            print(f"    Duration: {data.get('duration')} minutes")
            print(f"    Face Confidence: {data.get('face_confidence', 'N/A')}")
            print(f"    Voice Energy: {data.get('voice_energy', 'N/A')}")
            print(f"    Breathing Rate: {data.get('breathing_rate', 'N/A')}")


def example_continuous_monitoring():
    """Continuous monitoring example"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Continuous Monitoring (Real-time Updates)")
    print("="*70 + "\n")
    
    client = WellbeingAppClient()
    
    print("Monitoring API every 5 seconds. Press Ctrl+C to stop.\n")
    
    try:
        iteration = 0
        while iteration < 6:  # Run for 30 seconds
            iteration += 1
            print(f"Update #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Check health
            health = client.health_check()
            if health and health.get('status') == 'healthy':
                print("  ✓ API Healthy")
            
            # Get recent stats
            stats = client.get_timerange_stats(days=1)
            if stats:
                print(f"  Sessions today: {stats.get('sessions_count')}")
            
            print()
            if iteration < 6:
                time.sleep(5)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def example_batch_operations():
    """Batch operations example"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Batch Operations")
    print("="*70 + "\n")
    
    client = WellbeingAppClient()
    
    print("Exporting all sessions from last 7 days...\n")
    
    # Get all sessions from last 7 days
    sessions_data = client.get_recent_sessions(days=7)
    if not sessions_data:
        print("No sessions available!")
        return
    
    sessions = sessions_data.get('sessions', [])
    print(f"Found {len(sessions)} sessions.\n")
    
    # Export each session
    exported = 0
    for i, session in enumerate(sessions[:5], 1):  # Export first 5
        session_id = session['id']
        export_data = client.export_session(session_id)
        
        if export_data:
            filename = f'batch_export_session_{session_id}.json'
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            print(f"  {i}. Exported session {session_id} → {filename}")
            exported += 1
    
    print(f"\n✓ Batch export complete: {exported} sessions exported")


def example_claude_analysis():
    """Claude Haiku 4.5 AI analysis example"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Claude Haiku 4.5 AI Analysis")
    print("="*70 + "\n")
    
    client = WellbeingAppClient(enable_claude=True)
    
    if not client.claude_enabled:
        print("⚠️  Claude Haiku 4.5 not available.")
        print("Install: pip install anthropic")
        print("Set ANTHROPIC_API_KEY environment variable")
        return
    
    # Get first session
    sessions_data = client.get_all_sessions(limit=1)
    if not sessions_data or not sessions_data.get('sessions'):
        print("No sessions available!")
        return
    
    session_id = sessions_data['sessions'][0]['id']
    print(f"Analyzing session {session_id} with Claude Haiku 4.5...\n")
    
    # Get AI analysis
    analysis = client.ai_analyze_session(session_id)
    if 'error' not in analysis:
        print("AI Analysis:")
        print("-" * 70)
        print(analysis['analysis'])
    else:
        print(f"Analysis failed: {analysis['error']}")


def example_claude_recommendations():
    """Claude Haiku 4.5 personalized recommendations example"""
    print("\n" + "="*70)
    print("EXAMPLE 9: Claude Haiku 4.5 AI Recommendations")
    print("="*70 + "\n")
    
    client = WellbeingAppClient(enable_claude=True)
    
    if not client.claude_enabled:
        print("⚠️  Claude Haiku 4.5 not available.")
        return
    
    # Get first session
    sessions_data = client.get_all_sessions(limit=1)
    if not sessions_data or not sessions_data.get('sessions'):
        print("No sessions available!")
        return
    
    session_id = sessions_data['sessions'][0]['id']
    print(f"Getting AI recommendations for session {session_id}...\n")
    
    # Get AI recommendations
    recommendations = client.ai_get_recommendations(session_id)
    if 'error' not in recommendations:
        print("Personalized Recommendations:")
        print("-" * 70)
        print(recommendations['recommendations'])
    else:
        print(f"Recommendations failed: {recommendations['error']}")


def example_claude_chat():
    """Claude Haiku 4.5 interactive chat example"""
    print("\n" + "="*70)
    print("EXAMPLE 10: Claude Haiku 4.5 AI Wellness Chat")
    print("="*70 + "\n")
    
    client = WellbeingAppClient(enable_claude=True)
    
    if not client.claude_enabled:
        print("⚠️  Claude Haiku 4.5 not available.")
        return
    
    print("Chat with AI Wellness Assistant (type 'quit' to exit)\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == 'quit':
            print("\nThank you for chatting!")
            break
        
        if not user_input:
            continue
        
        response = client.ai_chat(user_input)
        if 'error' not in response:
            print(f"\nAssistant: {response['message']}\n")
        else:
            print(f"Chat failed: {response['error']}\n")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║    Wellbeing Monitoring - API Client Examples             ║
    ║    Run this script to see API usage examples              ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check if API is running
    client = WellbeingAppClient()
    health = client.health_check()
    
    if not health:
        print("\n⚠️  API server is not running!")
        print("Start it with: python app_backend.py")
        exit(1)
    
    print(f"✓ Connected to API\n")
    
    # Choose example
    print("Available Examples:")
    print("  1. Basic Usage")
    print("  2. Detailed Analysis")
    print("  3. Statistics & Trends")
    print("  4. Export Data")
    print("  5. Compare Sessions")
    print("  6. Continuous Monitoring")
    print("  7. Batch Operations")
    print("  8. Claude Haiku 4.5 AI Analysis")
    print("  9. Claude Haiku 4.5 AI Recommendations")
    print("  10. Claude Haiku 4.5 AI Chat")
    print("  0. Run All")
    print()
    
    choice = input("Select example (0-10): ").strip()
    
    print()
    
    if choice == '1':
        example_basic_usage()
    elif choice == '2':
        example_detailed_analysis()
    elif choice == '3':
        example_statistics()
    elif choice == '4':
        example_export_data()
    elif choice == '5':
        example_comparison()
    elif choice == '6':
        example_continuous_monitoring()
    elif choice == '7':
        example_batch_operations()
    elif choice == '8':
        example_claude_analysis()
    elif choice == '9':
        example_claude_recommendations()
    elif choice == '10':
        example_claude_chat()
    elif choice == '0':
        print("Running all examples (excluding interactive chat)...")
        example_basic_usage()
        example_detailed_analysis()
        example_statistics()
        example_export_data()
        example_comparison()
        example_batch_operations()
        example_claude_analysis()
        example_claude_recommendations()
    else:
        print("Invalid choice!")
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)