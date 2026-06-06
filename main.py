"""
Wellbeing Monitoring System - Main Entry Point

This MVP (Minimum Viable Product) demonstrates:
- Real-time video capture and facial analysis
- Concurrent audio capture and voice analysis

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
from ultralytics import YOLO

from face_analyzer import FaceAnalyzer
from voice_analyzer import VoiceAnalyzer
from wellbeing_monitor import WellbeingMonitor
from lstm_predictor import LSTMPredictor
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
        print("\n🔧 Initializing Bereke AI...")
        
        # Initialize analyzers
        self.face_analyzer = FaceAnalyzer()
        self.voice_analyzer = VoiceAnalyzer()
        self.monitor = WellbeingMonitor()
        
        # Initialize YOLO person tracker
        print("🔍 Загрузка YOLO...")
        self.yolo_model = YOLO('yolov8n.pt')
        self.person_analyzers = {}   # track_id -> FaceAnalyzer
        self.person_statuses = {}    # track_id -> status string
        self.people_count = 0
        print("✅ YOLO готова")
        
        # Initialize LSTM predictor
        print("🧠 Загрузка LSTM...")
        self.lstm_predictor = LSTMPredictor(sequence_length=10)
        print("✅ LSTM готова")
        
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
        print("🎯 YOLO: трекинг людей включён")
        if AUDIO_AVAILABLE:
            print(f"🎤 Audio: {SAMPLE_RATE} Hz")
        
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
        
        # === YOLO: находим людей и анализируем каждого ===
        results = self.yolo_model.track(frame, persist=True, classes=[0], verbose=False)
        
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.int().cpu().tolist()
            track_ids = results[0].boxes.id.int().cpu().tolist()
            self.people_count = len(boxes)
            
            for box, track_id in zip(boxes, track_ids):
                x1, y1, x2, y2 = box
                person_crop = frame[max(0, y1):y2, max(0, x1):x2]
                
                if person_crop.size > 0 and person_crop.shape[0] > 30 and person_crop.shape[1] > 30:
                    # Создаём FaceAnalyzer для нового человека
                    if track_id not in self.person_analyzers:
                        self.person_analyzers[track_id] = FaceAnalyzer()
                    
                    pa = self.person_analyzers[track_id].analyze_frame(person_crop)
                    fatigue = pa.get('fatigue_score', 0.0)
                    eyes = 'ЗАКРЫТЫ' if pa.get('eye_closure', False) else 'ОТКРЫТЫ'
                    detected = pa.get('landmarks_detected', False)
                    
                    if detected:
                        if fatigue > 0.6:
                            status = f"Усталость: ВЫСОКАЯ ({fatigue:.2f})"
                        elif fatigue > 0.3:
                            status = f"Усталость: СРЕДНЯЯ ({fatigue:.2f})"
                        else:
                            status = f"OK ({fatigue:.2f})"
                        status += f" | Глаза: {eyes}"
                    else:
                        status = "Сканирование..."
                    
                    self.person_statuses[track_id] = status
        else:
            self.people_count = 0
        
        # Общий анализ лица на полном кадре
        face_analysis = self.face_analyzer.analyze_frame(frame)
        
        # Analyze audio (if available)
        voice_analysis = None
        
        if AUDIO_AVAILABLE:
            audio_data = self.collect_audio_chunk()
            if audio_data is not None and len(audio_data) > 0:
                voice_analysis = self.voice_analyzer.analyze_audio(audio_data)
        
        # Use empty dictionaries if audio analysis failed
        if voice_analysis is None:
            voice_analysis = {
                'stress_score': 0.0,
                'anxiety_score': 0.0,
                'pitch_hz': 0.0,
                'speech_rate_wpm': 0.0,
                'loudness_db': 0.0,
            }
        
        # Aggregate analysis
        comprehensive_analysis = self.monitor.aggregate_analysis(
            face_analysis,
            voice_analysis
        )
        
        # LSTM prediction
        fatigue_score = face_analysis.get('fatigue_score', 0.0)
        stress_score = voice_analysis.get('stress_score', 0.0)
        anxiety_score = voice_analysis.get('anxiety_score', 0.0)
        
        lstm_result = self.lstm_predictor.add_data_point(
            fatigue_score, stress_score, anxiety_score
        )
        
        # Add LSTM predictions to analysis
        comprehensive_analysis['lstm'] = lstm_result
        
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
        face_data = {}
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to capture frame")
                    break
                
                # Store frame for analysis
                with self.frame_lock:
                    self.latest_frame = frame
                
                # === YOLO трекинг каждый кадр ===
                display_frame = frame.copy()
                yolo_results = self.yolo_model.track(frame, persist=True, classes=[0], verbose=False)
                
                if yolo_results[0].boxes.id is not None:
                    boxes = yolo_results[0].boxes.xyxy.int().cpu().tolist()
                    track_ids = yolo_results[0].boxes.id.int().cpu().tolist()
                    current_people = len(boxes)
                    
                    for box, track_id in zip(boxes, track_ids):
                        x1, y1, x2, y2 = box
                        status = self.person_statuses.get(track_id, "Сканирование...")
                        
                        # Цвет по статусу
                        if "ВЫСОКАЯ" in status:
                            color = (0, 0, 255)    # Красный
                        elif "СРЕДНЯЯ" in status:
                            color = (0, 165, 255)  # Оранжевый
                        else:
                            color = (0, 255, 0)    # Зелёный
                        
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                        
                        label = f"Person {track_id} | {status}"
                        cv2.putText(display_frame, label, (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                else:
                    current_people = 0
                
                # Счётчик людей
                cv2.putText(display_frame, f"People in room: {current_people}", (20, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Проверка времени для полного анализа
                current_time = time.time()
                elapsed = current_time - self.start_time
                
                if elapsed - self.last_analysis_time >= CHECK_INTERVAL_SECONDS:
                    self.last_analysis_time = elapsed
                    analysis_count += 1
                    
                    result = self.analyze_frame_and_audio()
                    if result is not None:
                        analysis, face_data = result
                        self.monitor.print_comprehensive_report(analysis)
                        
                        if self.people_count > 0:
                            print(f"\n👥 Людей в кадре: {self.people_count}")
                            for tid, st in self.person_statuses.items():
                                print(f"   Person {tid}: {st}")
                
                # Время на экране
                cv2.putText(display_frame, f"Elapsed: {elapsed:.1f}s",
                           (10, int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow("Wellbeing Monitor", display_frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    print("\n⏹️  Monitoring stopped by user")
                    break
                
                if key == ord('s'):
                    filename = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    cv2.imwrite(filename, display_frame)
                    print(f"📸 Snapshot saved: {filename}")
                
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
        
        # LSTM Statistics
        lstm_stats = self.lstm_predictor.get_statistics()
        if lstm_stats['status'] == 'ok':
            print("\n🧠 LSTM PREDICTOR STATISTICS")
            print("-"*40)
            print(f"Total predictions: {lstm_stats['total_predictions']}")
            print(f"Anomalies detected: {lstm_stats['anomalies_detected']}")
            print(f"Data points collected: {lstm_stats['data_points_collected']}")
            if lstm_stats['average_predictions']:
                print(f"Avg predicted stress: {lstm_stats['average_predictions']['stress']:.2f}")
                print(f"Avg predicted fatigue: {lstm_stats['average_predictions']['fatigue']:.2f}")
            print("-"*40)
            
            # Train LSTM on collected data
            if lstm_stats['data_points_collected'] >= 15:
                print("\n🔄 Training LSTM on session data...")
                self.lstm_predictor.train_online(epochs=30)
        
        if len(self.monitor.analysis_history) > 0:
            print("\n💾 Full analysis data saved in memory (Python session)")
        
        print("\n👋 Thank you for using Bereke AI!\n")


def main():
    """Main entry point."""
    print("""
╔════════════════════════════════════════════════════════════╗
║                      Bereke AI                            ║
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
