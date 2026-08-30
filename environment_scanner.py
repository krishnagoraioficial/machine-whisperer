# ---------------------------------------------------------
# FILE: environment_scanner.py
# AUTHOR: Krishna Gorai (Roll No: 25f1100001)
# PURPOSE: Standalone calibration script to sample room acoustics
#          and calculate the optimal Butterworth bandpass limits.
# ---------------------------------------------------------
import sys
import numpy as np
import scipy.signal as signal
import sounddevice as sd
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

# ==========================================
# 1. SETUP
# ==========================================
AUDIO_SAMPLE_RATE = 16000
DURATION_SEC = 20 # 20 seconds is enough to catch steady machine noise

print(f"Starting {DURATION_SEC}-second acoustic scan. Please let the machine run...")
print(f"Starting {DURATION_SEC}-second acoustic scan. Please let the machine run...")

# ==========================================
# 2. AUDIO RECORDING
# ==========================================
# blocking the terminal here so I get a clean 20s chunk
audio_data = sd.rec(int(DURATION_SEC * AUDIO_SAMPLE_RATE), samplerate=AUDIO_SAMPLE_RATE, channels=1, dtype='float32')
sd.wait()
audio_data = audio_data[:, 0]
print("Scan complete. Analyzing frequency spectrum...")

# ==========================================
# 3. PSD CALCULATION
# ==========================================
# using welch's method to average out random spikes and find the true mechanical frequencies
frequencies, power = signal.welch(audio_data, AUDIO_SAMPLE_RATE, nperseg=4096)

# find the absolute peak power
max_power = np.max(power)

# thresholding: I'm keeping any frequency band that has at least 5% of the max power
threshold = max_power * 0.05 
active_indices = np.where(power >= threshold)[0]

if len(active_indices) > 0:
    suggested_low = frequencies[active_indices[0]]
    suggested_high = frequencies[active_indices[-1]]
    
    # hard limit: never drop below 80Hz so I don't accidentally let 50Hz electrical mains hum into the pipeline
    if suggested_low < 80.0:
        suggested_low = 80.0
else:
    # failsafe if the mic is muted or room is dead silent
    suggested_low = 80.0
    suggested_high = 3000.0

print(f"\n===========================")
print(f"   CALIBRATION RESULTS     ")
print(f"===========================")
print(f"Optimal Low Cut:  {suggested_low:.0f} Hz")
print(f"Optimal High Cut: {suggested_high:.0f} Hz")
print(f"===========================\n")

# ==========================================
# 4. RESULTS UI
# ==========================================
app = QApplication(sys.argv)
win = pg.GraphicsLayoutWidget(show=True, title="Acoustic Environment Scan Results")
win.resize(800, 400)

# plotting the energy curve
plot = win.addPlot(title=f"Power Spectral Density (Suggested Band: {suggested_low:.0f}Hz - {suggested_high:.0f}Hz)")
plot.setLabel('bottom', "Frequency (Hz)")
plot.setLabel('left', "Signal Power")
plot.plot(frequencies, power, pen='y')

# drawing the suggested cutoffs so I can easily copy them into the main dashboard
low_line = pg.InfiniteLine(pos=suggested_low, angle=90, pen=pg.mkPen('g', width=2, style=pg.QtCore.Qt.PenStyle.DashLine))
high_line = pg.InfiniteLine(pos=suggested_high, angle=90, pen=pg.mkPen('r', width=2, style=pg.QtCore.Qt.PenStyle.DashLine))
plot.addItem(low_line)
plot.addItem(high_line)

sys.exit(app.exec())