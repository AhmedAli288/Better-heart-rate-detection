import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class Visualizer:
    def __init__(self, processor):
        self.processor = processor
        
        # Setup Figure
        plt.style.use('dark_background')
        self.fig, (self.ax_ecg, self.ax_ppg) = plt.subplots(2, 1, figsize=(10, 8))
        plt.subplots_adjust(hspace=0.4)

        # ECG Plot (Top)
        self.line_ecg, = self.ax_ecg.plot([], [], color='#00FF00', lw=1.5)
        self.ax_ecg.set_ylim(-1000, 1000)
        self.ax_ecg.set_xlim(0, 600)
        self.ecg_text = self.ax_ecg.text(0.02, 0.9, '', transform=self.ax_ecg.transAxes, color='lime', fontweight='bold')

        # PPG Plot (Bottom)
        self.line_ppg, = self.ax_ppg.plot([], [], color='#FF9900', lw=2)
        self.ax_ppg.set_ylim(40, 160)
        self.ax_ppg.set_xlim(0, 100)
        self.ppg_text = self.ax_ppg.text(0.02, 0.9, '', transform=self.ax_ppg.transAxes, color='orange', fontweight='bold')

    def update_plot(self, frame):
        # Update ECG graph data
        self.line_ecg.set_data(range(len(self.processor.ecg_history)), list(self.processor.ecg_history))
        
        # FIXED: Using the correct variable name from signal_processor.py
        self.ecg_text.set_text(f"ECG BPM: {self.processor.ecg_calculated_bpm}") 

        # Update PPG graph data
        self.line_ppg.set_data(range(len(self.processor.ppg_bpm_history)), list(self.processor.ppg_bpm_history))
        
        # Update PPG text
        conf = self.processor.current_confidence
        bpm = self.processor.current_ppg_bpm
        self.ppg_text.set_text(f"Watch BPM: {bpm} (Confidence: {conf}%)")
        
        # Set titles
        self.ax_ecg.set_title(f"ECG Signal - Live Monitoring")
        self.ax_ppg.set_title(f"PPG Signal - Watch Feedback")
        
        return self.line_ecg, self.line_ppg, self.ecg_text, self.ppg_text

    def start(self):
        # Added cache_frame_data=False to fix the UserWarning
        ani = FuncAnimation(self.fig, self.update_plot, interval=50, blit=False, cache_frame_data=False)
        plt.show()