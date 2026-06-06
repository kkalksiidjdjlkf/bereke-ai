"""
Breathing Analyzer Module
Analyzes breathing patterns to detect:
- Breathing rate (respiration frequency)
- Breathing irregularity
- Signs of stress or anxiety through respiratory changes
"""

import numpy as np
from collections import deque
from config import (
    NORMAL_BREATHING_RATE_MIN,
    NORMAL_BREATHING_RATE_MAX,
    FAST_BREATHING_THRESHOLD
)


class BreathingAnalyzer:
    """
    Analyzes breathing patterns from audio or visual data.
    
    Note: This is a simplified MVP implementation that estimates breathing
    rate from audio energy variations in the low-frequency range.
    
    More advanced implementations could use:
    - Visual analysis of chest movement from video
    - Enhanced audio analysis with frequency domain processing
    - Multi-modal combination of audio + video
    """
    
    def __init__(self, sample_rate=16000):
        """
        Initialize breathing analyzer.
        
        Args:
            sample_rate: Audio sample rate (Hz)
        """
        self.sample_rate = sample_rate
        self.breathing_rate_history = deque(maxlen=30)
        self.energy_history = deque(maxlen=sample_rate)  # 1 second of energy samples
        
        # Breathing analysis state
        self.breathing_rate = 0
        self.breathing_irregularity = 0.0
        self.last_breath_time = 0
    
    def estimate_breathing_rate(self, audio_data):
        """
        Estimate breathing rate from audio data.
        
        Method:
        1. Apply low-pass filter to extract low-frequency components (0.1-1 Hz)
        2. Analyze energy envelope for periodic breathing cycles
        3. Count peaks in the respiration band
        
        Breathing characteristics:
        - Normal rest: 12-20 breaths per minute
        - Light activity: 20-30 BPM
        - Stress/anxiety: 25+ BPM (rapid/shallow breathing)
        - Hyperventilation: 30+ BPM
        
        Args:
            audio_data: numpy array of audio samples
            
        Returns:
            float: Estimated breathing rate (breaths per minute)
        """
        # Ensure proper float format
        audio_data = audio_data.astype(np.float32)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Get duration of audio
        duration_seconds = len(audio_data) / self.sample_rate
        
        # Extract low-frequency energy for breathing analysis
        # Breathing is in 0.1-1 Hz range (10-60 BPM)
        
        # Simple approach: divide audio into short windows and track energy
        window_size = self.sample_rate // 10  # 100ms windows
        
        if window_size < 2 or len(audio_data) < window_size:
            return 0.0
        
        # Calculate energy in each window
        energy_envelope = []
        for i in range(0, len(audio_data) - window_size, window_size):
            window = audio_data[i:i + window_size]
            energy = np.sqrt(np.mean(window ** 2))
            energy_envelope.append(energy)
        
        if len(energy_envelope) < 3:
            return 0.0
        
        energy_envelope = np.array(energy_envelope)
        
        # Apply smoothing to reduce noise
        kernel_size = 3
        if len(energy_envelope) >= kernel_size:
            smoothed = np.convolve(energy_envelope, 
                                  np.ones(kernel_size) / kernel_size, 
                                  mode='valid')
        else:
            smoothed = energy_envelope
        
        # Detect peaks in energy envelope (breathing cycles)
        if len(smoothed) < 2:
            return 0.0
        
        # Find local maxima by comparing with neighbors
        peaks = []
        for i in range(1, len(smoothed) - 1):
            if smoothed[i] > smoothed[i-1] and smoothed[i] > smoothed[i+1]:
                # Check if peak is significant enough
                if smoothed[i] > np.mean(smoothed) * 0.3:
                    peaks.append(i)
        
        # Estimate breathing rate from peak counts
        if len(peaks) < 2:
            # Not enough data to estimate
            return 0.0
        
        # Each peak represents roughly one breathing cycle
        # Convert to breaths per minute
        
        # Time between first and last peak
        peak_distance_windows = peaks[-1] - peaks[0]
        peak_distance_seconds = peak_distance_windows * (window_size / self.sample_rate)
        
        if peak_distance_seconds < 0.1:
            return 0.0
        
        # Number of cycles = number of peaks
        num_cycles = len(peaks) - 1
        breathing_rate = (num_cycles / peak_distance_seconds) * 60  # Convert to per minute
        
        # Clip to reasonable range (can't have negative or extreme rates)
        breathing_rate = np.clip(breathing_rate, 5, 80)
        
        return breathing_rate
    
    def analyze_audio(self, audio_data):
        """
        Analyze audio for breathing patterns.
        
        Args:
            audio_data: numpy array of audio samples
            
        Returns:
            dict: Analysis results with keys:
                - 'breathing_rate': float (breaths per minute)
                - 'breathing_irregularity': float (0-1, higher = more irregular)
                - 'breathing_status': str ('normal', 'fast', 'slow', 'irregular')
        """
        # Estimate breathing rate
        breathing_rate = self.estimate_breathing_rate(audio_data)
        self.breathing_rate = breathing_rate
        
        # Track history
        if breathing_rate > 0:
            self.breathing_rate_history.append(breathing_rate)
        
        # Calculate breathing irregularity from history
        irregularity = 0.0
        if len(self.breathing_rate_history) > 3:
            rates = list(self.breathing_rate_history)
            irregularity = np.std(rates) / (np.mean(rates) + 1e-6)
            irregularity = np.clip(irregularity, 0, 1)
        
        self.breathing_irregularity = irregularity
        
        # Determine breathing status
        if breathing_rate == 0:
            status = 'unknown'
        elif breathing_rate > FAST_BREATHING_THRESHOLD:
            status = 'fast'
        elif breathing_rate < NORMAL_BREATHING_RATE_MIN:
            status = 'slow'
        elif irregularity > 0.5:
            status = 'irregular'
        else:
            status = 'normal'
        
        # Build analysis results
        analysis = {
            'breathing_rate': float(breathing_rate),
            'breathing_irregularity': float(irregularity),
            'breathing_status': status,
            'rate_history': list(self.breathing_rate_history),
        }
        
        return analysis
    
    def get_breathing_level(self):
        """
        Get current breathing level as a human-readable string.
        
        Returns:
            str: 'normal', 'elevated', 'irregular', or 'unknown'
        """
        if self.breathing_rate == 0:
            return 'unknown'
        elif self.breathing_rate > FAST_BREATHING_THRESHOLD:
            return 'elevated'
        elif self.breathing_irregularity > 0.5:
            return 'irregular'
        else:
            return 'normal'
    
    def reset(self):
        """Reset analyzer state for a new monitoring session."""
        self.breathing_rate_history.clear()
        self.energy_history.clear()
        self.breathing_rate = 0
        self.breathing_irregularity = 0.0
        self.last_breath_time = 0
