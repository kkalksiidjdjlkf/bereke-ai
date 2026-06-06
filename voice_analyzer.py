"""
Voice Analyzer Module
Analyzes audio characteristics to detect:
- Stress and anxiety (pitch changes, speech rate)
- Voice quality (loudness, tone)
- Emotional state through vocal patterns
"""

import librosa
import numpy as np
from collections import deque
import warnings
warnings.filterwarnings('ignore')

from config import (
    SAMPLE_RATE,
    NORMAL_PITCH_MIN,
    NORMAL_PITCH_MAX,
    STRESSED_PITCH_INCREASE,
    NORMAL_SPEECH_RATE,
    FAST_SPEECH_RATE,
    QUIET_THRESHOLD,
    LOUD_THRESHOLD
)


class VoiceAnalyzer:
    """Analyzes voice patterns for stress and emotional state."""
    
    def __init__(self):
        """Initialize voice analyzer with baseline data."""
        self.baseline_pitch = None  # Will be set from first audio sample
        self.pitch_history = deque(maxlen=30)  # Last 30 measurements
        self.speech_rate_history = deque(maxlen=30)
        self.loudness_history = deque(maxlen=30)
        
        # Stress score (0-1)
        self.stress_score = 0.0
        self.anxiety_score = 0.0
        
    def extract_pitch(self, audio_data):
        """
        Extract fundamental frequency (pitch) from audio using autocorrelation.
        
        Pitch changes are important indicators of stress:
        - Stressed people speak in higher pitches
        - Anxious people have more pitch variation
        
        Args:
            audio_data: numpy array of audio samples
            
        Returns:
            float: Estimated fundamental frequency (Hz), or 0 if detection fails
        """
        try:
            # Use librosa's piptrack algorithm to detect pitch
            # Piptrack is robust for speech analysis
            pitches, magnitudes = librosa.piptrack(
                y=audio_data,
                sr=SAMPLE_RATE,
                fmin=50,  # Minimum frequency (Hz)
                fmax=400  # Maximum frequency (Hz)
            )
            
            # Get the pitch with highest magnitude (most confident)
            index = magnitudes.argmax()
            pitch = pitches[index]
            
            return pitch
        except Exception as e:
            print(f"Warning: Pitch extraction failed: {e}")
            return 0.0
    
    def extract_speech_rate(self, audio_data):
        """
        Estimate speech rate by detecting onsets (speech activity).
        
        Speech rate indicators:
        - Fast speech (> 200 wpm) = stress/anxiety
        - Slow speech (< 80 wpm) = fatigue/depression
        - Normal (120-160 wpm) = relaxed
        
        Args:
            audio_data: numpy array of audio samples
            
        Returns:
            float: Estimated speech rate (words per minute)
        """
        try:
            # Detect onsets (speech starts)
            onset_frames = librosa.onset.onset_detect(y=audio_data, sr=SAMPLE_RATE)
            
            # Estimate speaking time
            onset_times = librosa.frames_to_time(onset_frames, sr=SAMPLE_RATE)
            
            if len(onset_times) < 2:
                return 0.0
            
            # Calculate frequency of onsets
            # More onsets = faster speech articulation
            total_time = len(audio_data) / SAMPLE_RATE
            onset_frequency = len(onset_times) / (total_time + 1e-6)  # Avoid division by zero
            
            # Convert to estimated words per minute (rough heuristic)
            # ~10 onsets per second ≈ 600 words per minute (maximum)
            # This is a simplified estimation
            speech_rate_wpm = (onset_frequency / 10.0) * 600
            
            return min(speech_rate_wpm, 300)  # Cap at 300 WPM
        except Exception as e:
            print(f"Warning: Speech rate extraction failed: {e}")
            return 0.0
    
    def extract_loudness(self, audio_data):
        """
        Extract loudness (RMS amplitude) from audio.
        
        Loudness patterns:
        - Quiet/whisper = 0.0-0.05 RMS = fatigue or depression
        - Normal speech = 0.05-0.15 RMS
        - Loud/shouting = 0.15-1.0 RMS = stress or anger
        
        Args:
            audio_data: numpy array of audio samples
            
        Returns:
            float: RMS (Root Mean Square) energy, normalized to 0-1
        """
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        # Normalize to 0-1 range (clip values)
        normalized_rms = np.clip(rms, 0, 1)
        
        return normalized_rms
    
    def analyze_audio(self, audio_data):
        """
        Analyze audio chunk for stress and anxiety indicators.
        
        Args:
            audio_data: numpy array of audio samples (mono, float32 -1.0 to 1.0)
            
        Returns:
            dict: Analysis results with keys:
                - 'stress_score': float (0-1, higher = more stressed)
                - 'anxiety_score': float (0-1, higher = more anxious)
                - 'pitch_hz': float (fundamental frequency in Hz)
                - 'speech_rate_wpm': float (estimated words per minute)
                - 'loudness_db': float (0-1 RMS amplitude)
                - 'pitch_variation': float (0-1, higher = more variation)
        """
        # Ensure audio is float and normalized
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # ===== PITCH ANALYSIS =====
        pitch = self.extract_pitch(audio_data)
        self.pitch_history.append(pitch)
        
        # Set baseline from first valid pitch measurement
        if self.baseline_pitch is None and pitch > 0:
            self.baseline_pitch = pitch
        
        # ===== SPEECH RATE ANALYSIS =====
        speech_rate = self.extract_speech_rate(audio_data)
        self.speech_rate_history.append(speech_rate)
        
        # ===== LOUDNESS ANALYSIS =====
        loudness = self.extract_loudness(audio_data)
        self.loudness_history.append(loudness)
        
        # ===== STRESS SCORE CALCULATION =====
        # Factors contributing to stress:
        stress_components = []
        
        # 1. Pitch elevation (speaking higher than baseline)
        if self.baseline_pitch and pitch > 0:
            pitch_ratio = pitch / (self.baseline_pitch + 1e-6)
            pitch_stress = min((pitch_ratio - 1.0) * 2, 1.0)  # Normalize
            stress_components.append(pitch_stress)
        
        # 2. Loudness extremes (very quiet or very loud)
        if loudness < QUIET_THRESHOLD:
            loudness_stress = QUIET_THRESHOLD - loudness
        elif loudness > LOUD_THRESHOLD:
            loudness_stress = (loudness - LOUD_THRESHOLD) / (1.0 - LOUD_THRESHOLD)
        else:
            loudness_stress = 0.0
        stress_components.append(loudness_stress)
        
        # 3. Fast speech rate
        if speech_rate > NORMAL_SPEECH_RATE:
            rapid_speech = min((speech_rate - NORMAL_SPEECH_RATE) / 100, 1.0)
            stress_components.append(rapid_speech)
        
        # Average stress components
        self.stress_score = np.mean(stress_components) if stress_components else 0.0
        
        # ===== ANXIETY SCORE CALCULATION =====
        # Anxiety is indicated by:
        # 1. High pitch variation (jittery voice)
        # 2. Rapid speech rate variation
        # 3. Loudness variation
        
        anxiety_components = []
        
        # Pitch variation
        if len(self.pitch_history) > 3:
            pitch_variation = np.std(self.pitch_history) / (np.mean(self.pitch_history) + 1e-6)
            anxiety_components.append(min(pitch_variation, 1.0))
        
        # Speech rate variation
        if len(self.speech_rate_history) > 3:
            speech_variation = np.std(self.speech_rate_history) / (np.mean(self.speech_rate_history) + 1e-6)
            anxiety_components.append(min(speech_variation, 1.0))
        
        # Loudness variation
        if len(self.loudness_history) > 3:
            loudness_variation = np.std(self.loudness_history)
            anxiety_components.append(loudness_variation)
        
        self.anxiety_score = np.mean(anxiety_components) if anxiety_components else 0.0
        
        # ===== BUILD RESULTS =====
        analysis = {
            'stress_score': float(np.clip(self.stress_score, 0, 1)),
            'anxiety_score': float(np.clip(self.anxiety_score, 0, 1)),
            'pitch_hz': float(pitch),
            'speech_rate_wpm': float(speech_rate),
            'loudness_db': float(loudness),
            'pitch_variation': float(np.std(self.pitch_history)) if len(self.pitch_history) > 1 else 0.0,
            'baseline_pitch': float(self.baseline_pitch) if self.baseline_pitch else None,
        }
        
        return analysis
    
    def get_stress_level(self):
        """
        Get current stress level as a human-readable string.
        
        Returns:
            str: 'low', 'moderate', or 'high'
        """
        if self.stress_score < 0.3:
            return 'low'
        elif self.stress_score < 0.6:
            return 'moderate'
        else:
            return 'high'
    
    def get_anxiety_level(self):
        """
        Get current anxiety level as a human-readable string.
        
        Returns:
            str: 'low', 'moderate', or 'high'
        """
        if self.anxiety_score < 0.3:
            return 'low'
        elif self.anxiety_score < 0.6:
            return 'moderate'
        else:
            return 'high'
    
    def reset(self):
        """Reset analyzer state for a new monitoring session."""
        self.baseline_pitch = None
        self.pitch_history.clear()
        self.speech_rate_history.clear()
        self.loudness_history.clear()
        self.stress_score = 0.0
        self.anxiety_score = 0.0
