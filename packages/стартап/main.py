"""
Wellbeing Monitoring System - Main Entry Point

This MVP (Minimum Viable Product) demonstrates:
- Real-time video capture and facial analysis
- Concurrent audio capture and voice analysis
- Breathing pattern analysis
- Aggregated wellness recommendations

Usage:
    python main.py

Controls:
    - Press 'q' or ESC to exit
    - Press 's' to save snapshot
"""

import cv2
import numpy as np
import threading
import queue
import time
from datetime import datetime

from face_analyzer import FaceAnalyzer
from voice_analyzer import VoiceAnalyzer
from breathing_analyzer import BreathingAnalyzer
from wellbeing_monitor import WellbeingMonitor
from database import WellbeingDatabase
from config import (
    CAMERA_ID,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    FPS,
    SAMPLE_RATE,
    AUDIO_DURATION_SECONDS,
    CHUNK_SIZE,
    MONITORING_DURATION_SECONDS,
    CHECK_INTERVAL_SECONDS,
)

# Try to import audio library
try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    print("⚠️  PyAudio not available. Voice analysis will be limited.")
    print("   To enable audio: pip install pyaudio")
    AUDIO_AVAILABLE = False


class WellbeingMonitoringSystem:
    """Main system that coordinates all monitoring components."""
    
    def __init__(self):
        """Initialize all analyzers and prepare monitoring system."""
        print("\n🔧 Initializing Wellbeing Monitoring System...")
        
        # Initialize analyzers
        self.face_analyzer = FaceAnalyzer()
        self.voice_analyzer = VoiceAnalyzer()
        self.breathing_analyzer = BreathingAnalyzer(SAMPLE_RATE)
        self.monitor = WellbeingMonitor()
        
        # Initialize database
        self.db = WellbeingDatabase()
        self.session_id = None
        
        # Initialize video capture
        self.cap = cv2.VideoCapture(CAMERA_ID)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera. Please check camera connection.")
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        
        # Audio capture state (if available)
        self.audio_queue = queue.Queue()
        self.audio_thread = None
        self.stop_audio = False
        
        # Frame buffer for analysis
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        
        # Timing
        self.start_time = time.time()
        self.last_analysis_time = 0
        
        print("✅ System initialized successfully!")
        print(f"📷 Camera: {FRAME_WIDTH}x{FRAME_HEIGHT} @ {FPS} FPS")
        if AUDIO_AVAILABLE:
            print(f"🎤 Audio: {SAMPLE_RATE} Hz")
        print(f"💾 Database: wellbeing_monitor.db")
        
    def capture_audio_thread(self):
        """
        Background thread that captures audio from microphone.
        Runs continuously if audio is available.
        """
        if not AUDIO_AVAILABLE:
            return
        
        try:
            import pyaudio
            
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
            )
            
            print("🎤 Audio capture started")
            
            while not self.stop_audio:
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    self.audio_queue.put(audio_data)
                except Exception as e:
                    print(f"⚠️  Audio capture error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            print("🎤 Audio capture stopped")
            
        except Exception as e:
            print(f"⚠️  Failed to initialize audio: {e}")
            self.AUDIO_AVAILABLE = False
    
    def collect_audio_chunk(self, duration_seconds=AUDIO_DURATION_SECONDS):
        """
        Collect audio data from the queue for a specified duration.
        
        Args:
            duration_seconds: How long to collect audio (seconds)
            
        Returns:
            numpy array of audio samples, or None if no data
        """
        if not AUDIO_AVAILABLE or self.audio_queue.empty():
            return None
        
        audio_frames = []
        target_samples = int(SAMPLE_RATE * duration_seconds)
        
        try:
            while len(audio_frames) < target_samples:
                if not self.audio_queue.empty():
                    chunk = self.audio_queue.get(timeout=0.1)
                    audio_frames.extend(chunk)
                else:
                    break
        except queue.Empty:
            pass
        
        if audio_frames:
            return np.array(audio_frames, dtype=np.float32)
        return None
    
    def analyze_frame_and_audio(self):
        """
        Perform analysis on latest frame and audio data.
        
        Returns:
            dict: Comprehensive analysis results
        """
        with self.frame_lock:
            if self.latest_frame is None:
                return None
            frame = self.latest_frame.copy()
        
        # Analyze face
        face_analysis = self.face_analyzer.analyze_frame(frame)
        
        # Analyze audio (if available)
        voice_analysis = None
        breathing_analysis = None
        
        if AUDIO_AVAILABLE:
            audio_data = self.collect_audio_chunk()
            if audio_data is not None and len(audio_data) > 0:
                voice_analysis = self.voice_analyzer.analyze_audio(audio_data)
                breathing_analysis = self.breathing_analyzer.analyze_audio(audio_data)
        
        # Use empty dictionaries if audio analysis failed
        if voice_analysis is None:
            voice_analysis = {
                'stress_score': 0.0,
                'anxiety_score': 0.0,
                'pitch_hz': 0.0,
                'speech_rate_wpm': 0.0,
                'loudness_db': 0.0,
            }
        
        if breathing_analysis is None:
            breathing_analysis = {
                'breathing_rate': 0.0,
                'breathing_status': 'unknown',
                'breathing_irregularity': 0.0,
            }
        
        # Aggregate analysis
        comprehensive_analysis = self.monitor.aggregate_analysis(
            face_analysis,
            voice_analysis,
            breathing_analysis
        )
        
        return comprehensive_analysis, face_analysis
    
    def run_monitoring_loop(self, duration_seconds=MONITORING_DURATION_SECONDS):
        """
        Run the main monitoring loop.
        
        Args:
            duration_seconds: How long to monitor (seconds)
        """
        print("\n" + "="*60)
        print(f"🔍 Starting {duration_seconds}-second monitoring session...")
        print("="*60)
        
        # Create database session
        self.session_id = self.db.create_session(
            user_notes="Real-time wellbeing monitoring",
            environment="office"
        )
        
        print("Press 'q' or ESC to exit early\n")
        
        # Start audio capture thread
        self.stop_audio = False
        if AUDIO_AVAILABLE:
            self.audio_thread = threading.Thread(target=self.capture_audio_thread)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            time.sleep(0.5)  # Let audio thread start
        
        self.start_time = time.time()
        analysis_count = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to capture frame")
                    break
                
                # Store frame for analysis
                with self.frame_lock:
                    self.latest_frame = frame
                
                # Check if it's time for analysis
                current_time = time.time()
                elapsed = current_time - self.start_time
                
                if elapsed - self.last_analysis_time >= CHECK_INTERVAL_SECONDS:
                    self.last_analysis_time = elapsed
                    analysis_count += 1
                    
                    # Perform analysis
                    result = self.analyze_frame_and_audio()
                    if result is not None:
                        analysis, face_data = result
                        
                        # Store all analysis results in database
                        self.db.store_face_analysis(self.session_id, face_data)
                        
                        # Extract voice and breathing data from the analysis
                        voice_data = {
                            'stress_score': analysis.get('stress_score', 0.0),
                            'anxiety_score': analysis.get('anxiety_score', 0.0),
                            'pitch_hz': analysis.get('pitch_hz', 0.0),
                            'pitch_variation': analysis.get('pitch_variation', 0.0),
                            'speech_rate_wpm': analysis.get('speech_rate_wpm', 0.0),
                            'loudness_rms': analysis.get('loudness_rms', 0.0),
                            'loudness_status': analysis.get('loudness_status', 'normal'),
                            'voice_quality': analysis.get('voice_quality', 'good'),
                            'primary_indicator': 'stress' if analysis.get('stress_score', 0.0) > 0.5 else 'normal'
                        }
                        
                        breathing_data = {
                            'breathing_rate': analysis.get('breathing_rate', 0.0),
                            'breathing_status': analysis.get('breathing_status', 'unknown'),
                            'breathing_irregularity': analysis.get('breathing_irregularity', 0.0),
                            'energy_level': analysis.get('energy_level', 0.0),
                            'rhythm_consistency': analysis.get('rhythm_consistency', 0.0),
                            'primary_indicator': analysis.get('breathing_status', 'normal')
                        }
                        
                        self.db.store_voice_analysis(self.session_id, voice_data)
                        self.db.store_breathing_analysis(self.session_id, breathing_data)
                        self.db.store_wellbeing_analysis(self.session_id, analysis)
                        
                        # Print report
                        self.monitor.print_comprehensive_report(analysis)
                
                # Display video with face landmarks
                annotated_frame = face_data.get('annotated_frame', frame)
                
                # Add status text
                cv2.putText(annotated_frame, f"Elapsed: {elapsed:.1f}s",
                           (10, self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow("Wellbeing Monitor", annotated_frame)
                
                # Check for exit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("\n⏹️  Monitoring stopped by user")
                    break
                
                if key == ord('s'):  # 's' for snapshot
                    filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    cv2.imwrite(filename, annotated_frame)
                    print(f"📸 Snapshot saved: {filename}")
                
                # Check if monitoring duration exceeded
                if elapsed >= duration_seconds:
                    print(f"\n✅ Monitoring session complete ({duration_seconds}s)")
                    break
        
        finally:
            # Cleanup
            self.stop_audio = True
            if self.audio_thread:
                self.audio_thread.join(timeout=2)
            
            cv2.destroyAllWindows()
            self.cap.release()
            
            # End database session
            if self.session_id:
                self.db.end_session(self.session_id)
            
            # Print session summary
            self.print_session_summary()
    
    def print_session_summary(self):
        """Print a summary of the monitoring session."""
        summary = self.monitor.get_session_summary()
        
        print("\n" + "="*60)
        print("📊 SESSION SUMMARY")
        print("="*60)
        print(f"Duration: {summary.get('duration_seconds', 'N/A')}s")
        print(f"Samples collected: {summary.get('num_samples', 0)}")
        print(f"Average concern level: {summary.get('average_concern', 0):.2f}")
        print(f"Peak concern level: {summary.get('peak_concern', 0):.2f}")
        print(f"Trend: {summary.get('trend', 'unknown')}")
        print("="*60)
        
        if len(self.monitor.analysis_history) > 0:
            print("\n💾 Full analysis data saved in memory (Python session)")
        
        # Generate and save database report
        if self.session_id:
            report = self.db.generate_report(self.session_id)
            print("\n" + report)
            
            # Save report to file
            report_filename = f"wellbeing_report_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_filename, 'w') as f:
                f.write(report)
            print(f"\n📄 Report saved to: {report_filename}")
            
            # Close database
            self.db.close()
        
        print("\n👋 Thank you for using the Wellbeing Monitoring System!\n")


def main():
    """Main entry point."""
    print("""
╔════════════════════════════════════════════════════════════╗
║    AI-BASED NON-MEDICAL WELLBEING MONITORING SYSTEM       ║
║                     MVP v1.0                              ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    try:
        system = WellbeingMonitoringSystem()
        system.run_monitoring_loop(duration_seconds=MONITORING_DURATION_SECONDS)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  System stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
