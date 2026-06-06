"""
Face Analyzer Module
Analyzes facial features to detect:
- Fatigue (eye closure, blinking patterns)
- Stress/Emotion (facial expression, eye contact)
- General emotional state
"""

import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from config import (
    EYE_ASPECT_RATIO_THRESHOLD,
    EYE_ASPECT_RATIO_CONSEC_FRAMES,
    MOUTH_ASPECT_RATIO_THRESHOLD,
    SHOW_FACE_LANDMARKS
)

class FaceAnalyzer:
    """Analyzes facial expressions and patterns for wellbeing indicators."""
    
    def __init__(self):
        """Initialize MediaPipe Face Mesh for real-time face landmark detection."""
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Initialize MediaPipe Drawing utilities
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Track blink patterns for fatigue detection
        self.eye_closure_counter = 0
        self.total_blinks = 0
        self.blink_history = deque(maxlen=30)  # Last 30 frames of blink data
        
        # Fatigue score (0-1)
        self.fatigue_score = 0.0
        
        # Store last face detected time for timeout detection
        self.face_detected = False
        
    def calculate_eye_aspect_ratio(self, eye_landmarks):
        """
        Calculate Eye Aspect Ratio (EAR) to detect if eyes are open or closed.
        
        EAR = ||p2 - p6|| + ||p3 - p5|| / (2 * ||p1 - p4||)
        where p1-p6 are the eye landmark points
        
        Args:
            eye_landmarks: 6-point eye coordinates
            
        Returns:
            float: Eye aspect ratio (lower = more closed)
        """
        # Vertical distances
        vertical_1 = np.linalg.norm(np.array(eye_landmarks[1]) - np.array(eye_landmarks[5]))
        vertical_2 = np.linalg.norm(np.array(eye_landmarks[2]) - np.array(eye_landmarks[4]))
        
        # Horizontal distance
        horizontal = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[3]))
        
        # Calculate EAR
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear
    
    def calculate_mouth_aspect_ratio(self, mouth_landmarks):
        """
        Calculate Mouth Aspect Ratio (MAR) to detect mouth openness.
        Related to stress and emotional expression.
        
        Args:
            mouth_landmarks: 20-point mouth coordinates
            
        Returns:
            float: Mouth aspect ratio
        """
        # Vertical distances
        vertical_1 = np.linalg.norm(np.array(mouth_landmarks[1]) - np.array(mouth_landmarks[11]))
        vertical_2 = np.linalg.norm(np.array(mouth_landmarks[3]) - np.array(mouth_landmarks[9]))
        vertical_3 = np.linalg.norm(np.array(mouth_landmarks[7]) - np.array(mouth_landmarks[5]))
        
        # Horizontal distance
        horizontal = np.linalg.norm(np.array(mouth_landmarks[0]) - np.array(mouth_landmarks[6]))
        
        # Calculate MAR
        mar = (vertical_1 + vertical_2 + vertical_3) / (3.0 * horizontal)
        return mar
    
    def analyze_frame(self, frame):
        """
        Analyze a single video frame for facial features.
        
        Args:
            frame: OpenCV frame (numpy array)
            
        Returns:
            dict: Analysis results with keys:
                - 'fatigue_score': float (0-1, higher = more fatigued)
                - 'eye_closure': bool (eyes closed?)
                - 'mouth_open': bool (mouth open?)
                - 'landmarks_detected': bool
                - 'annotated_frame': frame with landmarks drawn
        """
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Run face detection
        results = self.face_mesh.process(rgb_frame)
        
        # Initialize results
        analysis = {
            'fatigue_score': self.fatigue_score,
            'eye_closure': False,
            'mouth_open': False,
            'landmarks_detected': False,
            'annotated_frame': frame.copy(),
            'blink_detected': False
        }
        
        if results.multi_face_landmarks:
            # Face detected
            self.face_detected = True
            face_landmarks = results.multi_face_landmarks[0]
            
            # Extract landmarks as normalized coordinates
            landmarks = []
            for landmark in face_landmarks.landmark:
                x = int(landmark.x * frame.shape[1])
                y = int(landmark.y * frame.shape[0])
                landmarks.append([x, y])
            
            landmarks = np.array(landmarks)
            
            # ===== EYE ANALYSIS (Fatigue Detection) =====
            # MediaPipe eye landmarks: 33, 133 (right eye), 362, 263 (left eye)
            right_eye = [landmarks[33], landmarks[160], landmarks[158], 
                        landmarks[133], landmarks[153], landmarks[144]]
            left_eye = [landmarks[362], landmarks[385], landmarks[387], 
                       landmarks[263], landmarks[373], landmarks[380]]
            
            # Calculate eye aspect ratio for both eyes
            right_ear = self.calculate_eye_aspect_ratio(right_eye)
            left_ear = self.calculate_eye_aspect_ratio(left_eye)
            avg_ear = (right_ear + left_ear) / 2.0
            
            # Check if eyes are closed
            eyes_closed = avg_ear < EYE_ASPECT_RATIO_THRESHOLD
            
            if eyes_closed:
                self.eye_closure_counter += 1
            else:
                # Eyes opened - record blink event
                if self.eye_closure_counter >= 1:
                    self.total_blinks += 1
                    self.blink_history.append(1)
                    analysis['blink_detected'] = True
                self.eye_closure_counter = 0
            
            analysis['eye_closure'] = eyes_closed
            
            # ===== MOUTH ANALYSIS (Stress/Emotion) =====
            # MediaPipe mouth landmarks
            mouth_landmarks = landmarks[61:81]
            mar = self.calculate_mouth_aspect_ratio(mouth_landmarks)
            
            mouth_open = mar > MOUTH_ASPECT_RATIO_THRESHOLD
            analysis['mouth_open'] = mouth_open
            
            # ===== FATIGUE SCORE CALCULATION =====
            # Fatigue increases with:
            # 1. Eye closure (higher eye_closure_counter)
            # 2. Slow blink rate (fatigue causes slower blinking)
            # 3. Reduced mouth movement
            
            # Eye closure contribution (0-1)
            eye_fatigue = min(self.eye_closure_counter / EYE_ASPECT_RATIO_CONSEC_FRAMES, 1.0)
            
            # Blink rate contribution (slower = more fatigued)
            current_blink_rate = len([x for x in self.blink_history if x == 1])
            blink_fatigue = max(0.0, 1.0 - (current_blink_rate / 10.0))
            
            # Combine into fatigue score
            self.fatigue_score = (eye_fatigue * 0.6 + blink_fatigue * 0.4)
            analysis['fatigue_score'] = self.fatigue_score
            
            # ===== VISUALIZATION (Optional) =====
            if SHOW_FACE_LANDMARKS:
                # Draw face mesh on frame
                annotated_frame = frame.copy()
                self.mp_drawing.draw_landmarks(
                    annotated_frame,
                    face_landmarks,
                    self.mp_face_mesh.FACEMESH_TESSELATION,
                    self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                
                # Draw eye status
                status_text = f"Eyes: {'CLOSED' if eyes_closed else 'OPEN'} | Mouth: {'OPEN' if mouth_open else 'CLOSED'}"
                cv2.putText(annotated_frame, status_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Draw fatigue score
                cv2.putText(annotated_frame, f"Fatigue: {self.fatigue_score:.2f}",
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                analysis['annotated_frame'] = annotated_frame
            
            analysis['landmarks_detected'] = True
        
        return analysis
    
    def get_fatigue_level(self):
        """
        Get current fatigue level as a human-readable string.
        
        Returns:
            str: 'low', 'moderate', or 'high'
        """
        if self.fatigue_score < 0.3:
            return 'low'
        elif self.fatigue_score < 0.6:
            return 'moderate'
        else:
            return 'high'
    
    def reset(self):
        """Reset analyzer state for a new monitoring session."""
        self.eye_closure_counter = 0
        self.total_blinks = 0
        self.blink_history.clear()
        self.fatigue_score = 0.0
        self.face_detected = False
