"""
Example Usage: Programmatic API
Shows how to use the wellbeing monitoring system as a library
in your own Python applications.
"""

import numpy as np
import time
from face_analyzer import FaceAnalyzer
from voice_analyzer import VoiceAnalyzer
from breathing_analyzer import BreathingAnalyzer
from wellbeing_monitor import WellbeingMonitor


def example_1_basic_usage():
    """
    Example 1: Basic instantiation and usage of individual analyzers.
    Use this to understand each analyzer independently.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Analyzer Usage")
    print("="*60)
    
    # Create analyzers
    face_analyzer = FaceAnalyzer()
    voice_analyzer = VoiceAnalyzer()
    breathing_analyzer = BreathingAnalyzer(sample_rate=16000)
    
    # Simulate analysis data
    print("\n1. Face Analyzer:")
    print(f"   - Initialized: ✓")
    print(f"   - Fatigue score: {face_analyzer.fatigue_score:.2f}")
    print(f"   - Blinks detected: {face_analyzer.total_blinks}")
    
    print("\n2. Voice Analyzer:")
    print(f"   - Initialized: ✓")
    print(f"   - Stress score: {voice_analyzer.stress_score:.2f}")
    print(f"   - Anxiety score: {voice_analyzer.anxiety_score:.2f}")
    
    print("\n3. Breathing Analyzer:")
    print(f"   - Initialized: ✓")
    print(f"   - Breathing rate: {breathing_analyzer.breathing_rate:.0f} BPM")


def example_2_voice_analysis():
    """
    Example 2: Detailed voice analysis example.
    Shows how to analyze audio data for stress/anxiety indicators.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Voice Analysis")
    print("="*60)
    
    voice_analyzer = VoiceAnalyzer()
    
    # Create synthetic audio samples (in real use, load from microphone/file)
    sample_rate = 16000
    duration = 2
    
    # Generate three different audio scenarios
    
    # Scenario 1: Normal speech
    print("\nScenario 1: Normal voice")
    normal_audio = np.sin(2 * np.pi * 120 * np.arange(sample_rate * duration) / sample_rate) * 0.1
    normal_audio = normal_audio.astype(np.float32)
    result = voice_analyzer.analyze_audio(normal_audio)
    print(f"  Stress: {result['stress_score']:.2f}  Anxiety: {result['anxiety_score']:.2f}")
    print(f"  Pitch: {result['pitch_hz']:.0f} Hz  Speech rate: {result['speech_rate_wpm']:.0f} WPM")
    
    # Scenario 2: Elevated pitch (stressed)
    print("\nScenario 2: Elevated pitch (stressed)")
    stress_audio = np.sin(2 * np.pi * 180 * np.arange(sample_rate * duration) / sample_rate) * 0.15
    stress_audio = stress_audio.astype(np.float32)
    result = voice_analyzer.analyze_audio(stress_audio)
    print(f"  Stress: {result['stress_score']:.2f}  Anxiety: {result['anxiety_score']:.2f}")
    print(f"  Pitch: {result['pitch_hz']:.0f} Hz  Speech rate: {result['speech_rate_wpm']:.0f} WPM")
    
    # Scenario 3: Very loud (stressed)
    print("\nScenario 3: Very loud voice")
    loud_audio = np.sin(2 * np.pi * 140 * np.arange(sample_rate * duration) / sample_rate) * 0.5
    loud_audio = loud_audio.astype(np.float32)
    result = voice_analyzer.analyze_audio(loud_audio)
    print(f"  Stress: {result['stress_score']:.2f}  Anxiety: {result['anxiety_score']:.2f}")
    print(f"  Loudness: {result['loudness_db']:.2f}")


def example_3_integrated_monitoring():
    """
    Example 3: Integrated monitoring with aggregation.
    Shows how to combine all analyzers and generate recommendations.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Integrated Wellbeing Monitoring")
    print("="*60)
    
    monitor = WellbeingMonitor()
    voice_analyzer = VoiceAnalyzer()
    breathing_analyzer = BreathingAnalyzer(sample_rate=16000)
    
    # Simulate conditions: Normal, Stressed, Anxious
    scenarios = [
        {
            'name': 'Normal Conditions',
            'face': {'fatigue_score': 0.1, 'eye_closure': False, 'mouth_open': False,
                    'landmarks_detected': True},
            'voice': {'stress_score': 0.2, 'anxiety_score': 0.1, 'pitch_hz': 120,
                     'speech_rate_wpm': 140, 'loudness_db': 0.1},
            'breathing': {'breathing_rate': 16, 'breathing_status': 'normal',
                         'breathing_irregularity': 0.1},
        },
        {
            'name': 'Stressed Conditions',
            'face': {'fatigue_score': 0.3, 'eye_closure': False, 'mouth_open': False,
                    'landmarks_detected': True},
            'voice': {'stress_score': 0.7, 'anxiety_score': 0.5, 'pitch_hz': 180,
                     'speech_rate_wpm': 190, 'loudness_db': 0.2},
            'breathing': {'breathing_rate': 28, 'breathing_status': 'fast',
                         'breathing_irregularity': 0.4},
        },
        {
            'name': 'Anxious/Tired Conditions',
            'face': {'fatigue_score': 0.6, 'eye_closure': True, 'mouth_open': False,
                    'landmarks_detected': True},
            'voice': {'stress_score': 0.5, 'anxiety_score': 0.8, 'pitch_hz': 160,
                     'speech_rate_wpm': 170, 'loudness_db': 0.08},
            'breathing': {'breathing_rate': 24, 'breathing_status': 'irregular',
                         'breathing_irregularity': 0.6},
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{'---'*20}")
        print(f"Scenario: {scenario['name']}")
        print(f"{'---'*20}")
        
        # Run analysis
        analysis = monitor.aggregate_analysis(
            scenario['face'],
            scenario['voice'],
            scenario['breathing']
        )
        
        # Print results
        print(f"\nOverall concern: {analysis['concern_level'].upper()}")
        print(f"Primary concern: {analysis['primary_concern']}")
        print(f"\nTop recommendations:")
        for i, rec in enumerate(analysis['recommendations'][:3], 1):
            print(f"  {i}. {rec}")


def example_4_custom_usage():
    """
    Example 4: Custom implementation.
    Shows how to integrate into your own application.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Custom Application Integration")
    print("="*60)
    
    from wellbeing_monitor import WellbeingMonitor
    
    class MyWellnessApp:
        """Example app that uses the monitoring system."""
        
        def __init__(self):
            self.monitor = WellbeingMonitor()
            self.alerts = []
        
        def check_wellbeing(self, face_data, voice_data, breathing_data):
            """Check current wellbeing and log alerts."""
            analysis = self.monitor.aggregate_analysis(
                face_data, voice_data, breathing_data
            )
            
            # Store alert if concern detected
            if analysis['concern_level'] != 'low':
                self.alerts.append({
                    'timestamp': analysis['timestamp'],
                    'level': analysis['concern_level'],
                    'primary_concern': analysis['primary_concern'],
                    'recommendation': analysis['recommendations'][0]
                })
            
            return analysis
        
        def get_alerts(self):
            """Get all logged alerts."""
            return self.alerts
        
        def print_alert_summary(self):
            """Print summary of all alerts in session."""
            print(f"\nAlerts logged: {len(self.alerts)}")
            for i, alert in enumerate(self.alerts, 1):
                print(f"\n{i}. {alert['timestamp']}")
                print(f"   Level: {alert['level']}")
                print(f"   Concern: {alert['primary_concern']}")
                print(f"   Action: {alert['recommendation']}")
    
    # Usage
    app = MyWellnessApp()
    
    # Simulate multiple checks
    test_data = [
        {
            'face': {'fatigue_score': 0.1, 'eye_closure': False, 'mouth_open': False,
                    'landmarks_detected': True},
            'voice': {'stress_score': 0.2, 'anxiety_score': 0.1, 'pitch_hz': 120,
                     'speech_rate_wpm': 140, 'loudness_db': 0.1},
            'breathing': {'breathing_rate': 16, 'breathing_status': 'normal',
                         'breathing_irregularity': 0.1},
        },
        {
            'face': {'fatigue_score': 0.5, 'eye_closure': True, 'mouth_open': False,
                    'landmarks_detected': True},
            'voice': {'stress_score': 0.6, 'anxiety_score': 0.7, 'pitch_hz': 170,
                     'speech_rate_wpm': 200, 'loudness_db': 0.25},
            'breathing': {'breathing_rate': 30, 'breathing_status': 'fast',
                         'breathing_irregularity': 0.5},
        },
    ]
    
    for i, data in enumerate(test_data, 1):
        print(f"\n--- Check #{i} ---")
        analysis = app.check_wellbeing(data['face'], data['voice'], data['breathing'])
        print(f"Concern level: {analysis['concern_level']}")
    
    # Print summary
    app.print_alert_summary()


def main():
    """Run all examples."""
    print("""
╔════════════════════════════════════════════════════════════╗
║        WELLBEING MONITORING SYSTEM - USAGE EXAMPLES       ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Run examples
        example_1_basic_usage()
        example_2_voice_analysis()
        example_3_integrated_monitoring()
        example_4_custom_usage()
        
        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)
        print("\nFor more information:")
        print("  - Read README.md for detailed documentation")
        print("  - Run: python main.py  to start real-time monitoring")
        print("  - Edit: config.py  to customize thresholds")
        print("\n")
    
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
