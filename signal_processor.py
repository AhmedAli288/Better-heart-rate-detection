import time
from collections import deque

class SignalProcessor:
    def __init__(self, window_size=600):
        # Data storage for the graph
        self.ecg_history = deque([2048]*window_size, maxlen=window_size)
        self.ppg_bpm_history = deque([0]*100, maxlen=100)
        
        # Current status
        self.current_ppg_bpm = 0
        self.current_confidence = 0
        self.ecg_calculated_bpm = 0
        
        # Filtering variables
        self.baseline = 2048
        self.ALPHA = 0.05 # Baseline filter strength
        self.last_peak_time = time.time()

    def update(self, line):
        try:
            # Parse CSV data: ECG_Raw, PPG_BPM, Confidence
            parts = line.split(",")
            if len(parts) >= 3:
                raw_ecg = int(parts[0])
                self.current_ppg_bpm = int(parts[1])
                self.current_confidence = int(parts[2])

                # 1. Baseline Wander Removal (High-Pass Filter)
                self.baseline = (1 - self.ALPHA) * self.baseline + self.ALPHA * raw_ecg
                clean_ecg = raw_ecg - self.baseline
                self.ecg_history.append(clean_ecg)

                # 2. R-Peak Detection for ECG BPM
                # If signal exceeds threshold, it's a heartbeat
                if clean_ecg > 600: 
                    now = time.time()
                    time_diff = now - self.last_peak_time
                    if time_diff > 0.5: # Max 120 BPM limit to ignore noise
                        self.ecg_calculated_bpm = int(60 / time_diff)
                        self.last_peak_time = now
                
                self.ppg_bpm_history.append(self.current_ppg_bpm)
        except Exception as e:
            pass # Ignore corrupted lines