"""
Wellbeing Monitor Coordinator
Aggregates data from all analyzers and generates wellness recommendations.

This module:
- Collects results from face, voice, and breathing analyzers
- Combines findings into an overall wellness score
- Generates personalized, non-medical recommendations
- Tracks patterns over monitoring sessions
"""

import numpy as np
from datetime import datetime
from config import (
    MILD_CONCERN_THRESHOLD,
    MODERATE_CONCERN_THRESHOLD,
    HIGH_CONCERN_THRESHOLD,
    RECOMMENDATIONS
)


class WellbeingMonitor:
    """Coordinates analysis from all sensors and generates recommendations."""
    
    def __init__(self):
        """Initialize the wellbeing monitor."""
        self.session_start_time = None
        self.analysis_history = []
        
        # Overall wellbeing score (0-1, higher = more concerns)
        self.overall_concern_score = 0.0
        self.primary_concern = None
        
    def aggregate_analysis(self, face_data, voice_data, breathing_data):
        """
        Combine results from all analyzers into overall assessment.
        
        Args:
            face_data: dict from FaceAnalyzer.analyze_frame()
            voice_data: dict from VoiceAnalyzer.analyze_audio()
            breathing_data: dict from BreathingAnalyzer.analyze_audio()
            
        Returns:
            dict: Comprehensive analysis with overall scores and recommendations
        """
        
        # ===== SCORE EXTRACTION =====
        # Normalize scores to 0-1 range
        fatigue_score = face_data.get('fatigue_score', 0.0)
        stress_score = voice_data.get('stress_score', 0.0)
        anxiety_score = voice_data.get('anxiety_score', 0.0)
        
        # Breathing status to score
        breathing_rate = breathing_data.get('breathing_rate', 0.0)
        breathing_status = breathing_data.get('breathing_status', 'unknown')
        
        breathing_score = 0.0
        if breathing_status == 'fast':
            breathing_score = 0.7
        elif breathing_status == 'irregular':
            breathing_score = 0.5
        elif breathing_status == 'slow':
            breathing_score = 0.3
        
        # ===== COMBINED CONCERN SCORE =====
        # Weighted combination of all factors
        # This represents the overall level of concern (0-1, higher = more concern)
        weights = {
            'fatigue': 0.25,      # Eye fatigue is important but not primary
            'stress': 0.30,       # Voice stress is highly indicative
            'anxiety': 0.25,      # Anxiety variation is important
            'breathing': 0.20     # Breathing abnormalities are concerning
        }
        
        combined_score = (
            fatigue_score * weights['fatigue'] +
            stress_score * weights['stress'] +
            anxiety_score * weights['anxiety'] +
            breathing_score * weights['breathing']
        )
        
        self.overall_concern_score = combined_score
        
        # ===== IDENTIFY PRIMARY CONCERN =====
        # Which factor is most elevated?
        concerns = {
            'fatigue': fatigue_score,
            'stress': stress_score,
            'anxiety': anxiety_score,
            'breathing': breathing_score
        }
        
        primary_concern = max(concerns, key=concerns.get)
        self.primary_concern = primary_concern
        
        # ===== BUILD COMPREHENSIVE ANALYSIS =====
        analysis = {
            'timestamp': datetime.now().isoformat(),
            
            # Individual scores
            'face': {
                'fatigue_score': fatigue_score,
                'fatigue_level': self._score_to_level(fatigue_score),
                'eye_closure': face_data.get('eye_closure', False),
                'mouth_open': face_data.get('mouth_open', False),
                'landmarks_detected': face_data.get('landmarks_detected', False),
            },
            
            'voice': {
                'stress_score': stress_score,
                'stress_level': self._score_to_level(stress_score),
                'anxiety_score': anxiety_score,
                'anxiety_level': self._score_to_level(anxiety_score),
                'pitch_hz': voice_data.get('pitch_hz', 0.0),
                'speech_rate_wpm': voice_data.get('speech_rate_wpm', 0.0),
                'loudness_rms': voice_data.get('loudness_db', 0.0),
            },
            
            'breathing': {
                'breathing_rate': breathing_rate,
                'breathing_status': breathing_status,
                'breathing_irregularity': breathing_data.get('breathing_irregularity', 0.0),
            },
            
            # Overall assessment
            'overall_concern_score': combined_score,
            'concern_level': self._score_to_level(combined_score),
            'primary_concern': primary_concern,
            
            # Recommendations
            'recommendations': self._generate_recommendations(
                fatigue_score, stress_score, anxiety_score, breathing_score
            ),
            
            # Wellness status
            'wellness_status': self._determine_wellness_status(
                combined_score, primary_concern
            ),
        }
        
        # Store in history
        self.analysis_history.append(analysis)
        
        return analysis
    
    def _score_to_level(self, score):
        """
        Convert numeric score to qualitative level.
        
        Args:
            score: float between 0-1
            
        Returns:
            str: 'low', 'moderate', or 'high'
        """
        if score < MILD_CONCERN_THRESHOLD:
            return 'low'
        elif score < MODERATE_CONCERN_THRESHOLD:
            return 'moderate'
        else:
            return 'high'
    
    def _generate_recommendations(self, fatigue, stress, anxiety, breathing):
        """
        Generate personalized recommendations based on detected patterns.
        
        Args:
            fatigue: fatigue score (0-1)
            stress: stress score (0-1)
            anxiety: anxiety score (0-1)
            breathing: breathing concern score (0-1)
            
        Returns:
            list: Recommended actions for the user
        """
        recommendations = []
        
        # ===== FATIGUE RECOMMENDATIONS =====
        if fatigue > MODERATE_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['fatigue'][0])
            if fatigue > HIGH_CONCERN_THRESHOLD:
                recommendations.append(RECOMMENDATIONS['fatigue'][2])
        elif fatigue > MILD_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['fatigue'][1])
        
        # ===== STRESS RECOMMENDATIONS =====
        if stress > MODERATE_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['stress'][0])
            recommendations.append(RECOMMENDATIONS['stress'][1])
        elif stress > MILD_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['stress'][1])
        
        # ===== ANXIETY RECOMMENDATIONS =====
        if anxiety > MODERATE_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['anxiety'][0])
            recommendations.append(RECOMMENDATIONS['anxiety'][1])
        elif anxiety > MILD_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['anxiety'][2])
        
        # ===== BREATHING RECOMMENDATIONS =====
        if breathing > MODERATE_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['breathing'][0])
            recommendations.append(RECOMMENDATIONS['breathing'][1])
        elif breathing > MILD_CONCERN_THRESHOLD:
            recommendations.append(RECOMMENDATIONS['breathing'][2])
        
        # ===== DEFAULT RECOMMENDATION =====
        if not recommendations:
            recommendations = RECOMMENDATIONS['normal']
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:5]  # Limit to top 5 recommendations
    
    def _determine_wellness_status(self, concern_score, primary_concern):
        """
        Determine overall wellness status.
        
        Args:
            concern_score: combined concern score (0-1)
            primary_concern: str, the main area of concern
            
        Returns:
            str: Wellness status message
        """
        if concern_score < MILD_CONCERN_THRESHOLD:
            return "✅ All indicators suggest good wellbeing."
        elif concern_score < MODERATE_CONCERN_THRESHOLD:
            return f"⚠️  Mild {primary_concern} detected. Consider brief adjustments."
        elif concern_score < HIGH_CONCERN_THRESHOLD:
            return f"⚠️⚠️  Moderate {primary_concern} levels. Take action to address."
        else:
            return f"🚨 High {primary_concern} levels detected. Immediate attention recommended."
    
    def print_comprehensive_report(self, analysis):
        """
        Print a formatted, easy-to-read wellness report.
        
        Args:
            analysis: dict from aggregate_analysis()
        """
        print("\n" + "="*60)
        print("🏥 WELLBEING MONITORING REPORT")
        print("="*60)
        print(f"Time: {analysis['timestamp']}\n")
        
        # Overall Status
        print(f"Overall Status: {analysis['wellness_status']}")
        print(f"Concern Level: {analysis['concern_level'].upper()}")
        print(f"Primary Concern: {analysis['primary_concern']}\n")
        
        # Individual Metrics
        print("-" * 60)
        print("📊 DETAILED METRICS:")
        print("-" * 60)
        
        # Face Analysis
        face = analysis['face']
        print(f"\n👁  Facial Analysis:")
        print(f"   Fatigue Level: {face['fatigue_level'].upper()}")
        print(f"   Fatigue Score: {face['fatigue_score']:.2f}/1.0")
        print(f"   Eyes Status: {'CLOSED' if face['eye_closure'] else 'OPEN'}")
        print(f"   Face Detected: {'Yes' if face['landmarks_detected'] else 'No'}")
        
        # Voice Analysis
        voice = analysis['voice']
        print(f"\n🎤 Voice Analysis:")
        print(f"   Stress Level: {voice['stress_level'].upper()}")
        print(f"   Stress Score: {voice['stress_score']:.2f}/1.0")
        print(f"   Anxiety Level: {voice['anxiety_level'].upper()}")
        print(f"   Anxiety Score: {voice['anxiety_score']:.2f}/1.0")
        print(f"   Pitch: {voice['pitch_hz']:.0f} Hz")
        print(f"   Speech Rate: {voice['speech_rate_wpm']:.0f} WPM")
        print(f"   Loudness: {voice['loudness_rms']:.2f}")
        
        # Breathing Analysis
        breathing = analysis['breathing']
        print(f"\n🫁 Breathing Analysis:")
        print(f"   Breathing Status: {breathing['breathing_status'].upper()}")
        print(f"   Breathing Rate: {breathing['breathing_rate']:.0f} BPM")
        print(f"   Irregularity: {breathing['breathing_irregularity']:.2f}")
        
        # Recommendations
        print("\n" + "-" * 60)
        print("💡 RECOMMENDATIONS:")
        print("-" * 60)
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"{i}. {rec}")
        
        # Important Disclaimer
        print("\n" + "="*60)
        print("⚕️  IMPORTANT DISCLAIMER:")
        print("="*60)
        print("This system provides WELLNESS indicators only.")
        print("It is NOT a medical diagnostic tool.")
        print("If symptoms persist or worsen, consult a healthcare professional.")
        print("="*60 + "\n")
    
    def get_session_summary(self):
        """
        Get a summary of the current monitoring session.
        
        Returns:
            dict: Session summary statistics
        """
        if not self.analysis_history:
            return {"status": "No analysis data collected yet"}
        
        # Extract trends from history
        concern_scores = [a['overall_concern_score'] for a in self.analysis_history]
        fatigue_scores = [a['face']['fatigue_score'] for a in self.analysis_history]
        stress_scores = [a['voice']['stress_score'] for a in self.analysis_history]
        anxiety_scores = [a['voice']['anxiety_score'] for a in self.analysis_history]
        
        summary = {
            'duration_seconds': len(self.analysis_history) * 5,  # ~5 sec per analysis
            'num_samples': len(self.analysis_history),
            'average_concern': np.mean(concern_scores),
            'peak_concern': np.max(concern_scores),
            'average_fatigue': np.mean(fatigue_scores),
            'average_stress': np.mean(stress_scores),
            'average_anxiety': np.mean(anxiety_scores),
            'trend': self._analyze_trend(),
        }
        
        return summary
    
    def _analyze_trend(self):
        """
        Analyze whether overall wellbeing is improving or declining.
        
        Returns:
            str: 'improving', 'stable', or 'declining'
        """
        if len(self.analysis_history) < 2:
            return 'unknown'
        
        # Compare first half to second half
        mid = len(self.analysis_history) // 2
        first_half = [a['overall_concern_score'] for a in self.analysis_history[:mid]]
        second_half = [a['overall_concern_score'] for a in self.analysis_history[mid:]]
        
        first_avg = np.mean(first_half)
        second_avg = np.mean(second_half)
        
        # Calculate change percentage
        if first_avg == 0:
            return 'unknown'
        
        change = (second_avg - first_avg) / first_avg
        
        if change > 0.1:
            return '📈 declining'
        elif change < -0.1:
            return '📉 improving'
        else:
            return '➡️  stable'
    
    def reset(self):
        """Reset monitor state for a new session."""
        self.session_start_time = None
        self.analysis_history = []
        self.overall_concern_score = 0.0
        self.primary_concern = None
