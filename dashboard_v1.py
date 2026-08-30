# ---------------------------------------------------------
# FILE: dashboard_v1.py
# AUTHOR: Krishna Gorai (Roll No: 25f1100001)
# PROJECT: Distributed Acoustic Sensing for Predictive Machinery Maintenance
# NOTES: Live laptop mic capture pipeline. Added Butterworth filter to block 
#        60Hz mains hum and implemented RMS tracking for the DSP requirements.
# ---------------------------------------------------------
import sys
import numpy as np
import scipy.signal as signal
import sounddevice as sd
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton
# ==========================================
# 1. CONFIG & SETUP
# ==========================================
AUDIO_SAMPLE_RATE = 16000  # 16kHz to match the ESP32 I2S output later
CHUNK_SIZE = 1024          # processing 1024 samples at a time to prevent UI lag
WATERFALL_FRAMES = 100     # length of the spectrogram history

# Default filter limits
LOWCUT_FREQ_HZ = 80.0
HIGHCUT_FREQ_HZ = 3000.0
FILTER_STEEPNESS = 4       # order 4 provides a stable cutoff

# ==========================================
# 2. DATA ARRAYS
# ==========================================
# Using numpy arrays because standard python lists are too slow for live audio buffers
audio_buffer = np.zeros(CHUNK_SIZE) 
spectrogram_data = np.zeros((WATERFALL_FRAMES, CHUNK_SIZE // 2))
rms_history = np.zeros(WATERFALL_FRAMES)

def create_digital_filter(low_hz, high_hz, rate, order):
    """Calculates the Butterworth filter coefficients (b, a)."""
    nyquist_limit = 0.5 * rate
    normalized_low = low_hz / nyquist_limit
    normalized_high = high_hz / nyquist_limit
    
    b_coeff, a_coeff = signal.butter(order, [normalized_low, normalized_high], btype='bandpass')
    return b_coeff, a_coeff

# Calculate initial filter math before the mic starts
filter_b, filter_a = create_digital_filter(LOWCUT_FREQ_HZ, HIGHCUT_FREQ_HZ, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)

# ==========================================
# 3. MICROPHONE CAPTURE
# ==========================================
def capture_audio_callback(indata, frames, time, status):
    """Background thread that constantly grabs mic data."""
    global audio_buffer 
    if status:
        print(f"Mic Warning: {status}")
    
    # Grab just the mono channel
    audio_buffer = indata[:, 0]

# ==========================================
# 4. USER INTERFACE (GUI) SETUP
# ==========================================
app = QApplication(sys.argv)

# 4a. Create the Main Application Window container
main_window = QWidget()
main_window.setWindowTitle("MachineWhisperer V1.3 - Dynamic Presets")
main_window.resize(1000, 900)
layout = QVBoxLayout()
main_window.setLayout(layout)

# 4b. Add the Manual Frequency Controls
controls_layout = QHBoxLayout()

controls_layout.addWidget(QLabel("Low Cut (Hz):"))
lowcut_input = QSpinBox()
lowcut_input.setRange(10, 7999)
lowcut_input.setValue(int(LOWCUT_FREQ_HZ))
controls_layout.addWidget(lowcut_input)

controls_layout.addWidget(QLabel("High Cut (Hz):"))
highcut_input = QSpinBox()
highcut_input.setRange(20, 8000)
highcut_input.setValue(int(HIGHCUT_FREQ_HZ))
controls_layout.addWidget(highcut_input)

apply_btn = QPushButton("Apply Custom Filter")
controls_layout.addWidget(apply_btn)

layout.addLayout(controls_layout)

# 4c. Add the PyQtGraph Dashboard below the dropdown
window = pg.GraphicsLayoutWidget()
layout.addWidget(window)

# --- RE-ADDING THE MISSING GRAPHS ---
# 1. Waveform Plot
waveform_plot = window.addPlot(title="Live Audio Waveform (Filtered)", row=0, col=0)
waveform_plot.setYRange(-0.5, 0.5)
waveform_curve = waveform_plot.plot(pen='c') 

# 2. Spectrogram Plot
spectrogram_plot = window.addPlot(title="Continuous Spectrogram", row=1, col=0)
image_item = pg.ImageItem()
spectrogram_plot.addItem(image_item)
image_item.setColorMap(pg.colormap.get('inferno'))
image_item.setLevels((-30, 40))

# 3. RMS Energy Plot
rms_plot = window.addPlot(title="RMS Energy Trend (Machine Health)", row=2, col=0)
rms_plot.setYRange(0, 0.2)
rms_curve = rms_plot.plot(pen='r', fillLevel=0, brush=(255, 0, 0, 50)) 
# ------------------------------------

main_window.show()

# 4d. Dynamic Filter Logic
def update_filter_preset():
    """Recalculates the filter limits based on manual UI inputs."""
    global filter_b, filter_a
    new_low = float(lowcut_input.value())
    new_high = float(highcut_input.value())
    
    # Safety check: prevent mathematical errors if the user sets Low higher than High
    if new_low >= new_high:
        return 
        
    filter_b, filter_a = create_digital_filter(new_low, new_high, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)

# Trigger the update only when the button is clicked
apply_btn.clicked.connect(update_filter_preset)
# ==========================================
# 5. DSP & DASHBOARD UPDATE LOOP
# ==========================================
def update_dashboard():
    """Timer loop to run the DSP math and redraw the graphs."""
    global spectrogram_data, rms_history
    
    # STEP A: Clean the audio (remove 60Hz hum and out-of-band noise)
    filtered_audio = signal.lfilter(filter_b, filter_a, audio_buffer)
    waveform_curve.setData(filtered_audio)

    # Dynamic Y-Axis: Waveform
    peak_amp = np.max(np.abs(filtered_audio))
    if peak_amp > 0.5:
        waveform_plot.setYRange(-peak_amp * 1.1, peak_amp * 1.1)
    else:
        waveform_plot.setYRange(-0.5, 0.5)

    # STEP B: FFT & Spectrogram
    # Apply a Hanning window so the FFT doesn't leak/spike artificially at the edges
    windowed_audio = filtered_audio * np.hanning(len(filtered_audio))
    fft_magnitude = np.abs(np.fft.rfft(windowed_audio))[:-1]
    fft_db = 20 * np.log10(fft_magnitude + 1e-6)
    
    # Shift array down and put new FFT data at the top
    spectrogram_data = np.roll(spectrogram_data, -1, axis=0)
    spectrogram_data[-1, :] = fft_db

    image_item.setImage(spectrogram_data, autoLevels=False)

    # Dynamic Color/Sensitivity: Spectrogram
    peak_fft = np.max(fft_db)
    if peak_fft > 40:
        image_item.setLevels((-30, peak_fft * 1.1))
    else:
        image_item.setLevels((-30, 40))
        
    # STEP C: RMS Energy Calculation
    # Calculate the square root of the mean of squares for signal power
    current_rms = np.sqrt(np.mean(filtered_audio**2))
    
    rms_history = np.roll(rms_history, -1)
    rms_history[-1] = current_rms
    rms_curve.setData(rms_history)

    # Dynamic Y-Axis: RMS Energy
    peak_rms = np.max(rms_history)
    if peak_rms > 0.2:
        rms_plot.setYRange(0, peak_rms * 1.1)
    else:
        rms_plot.setYRange(0, 0.2)

# ==========================================
# 6. MAIN EXECUTION LOOP
# ==========================================
if __name__ == '__main__':
    # Turn on the microphone and tell it to send data to our 'capture_audio_callback' function
    stream = sd.InputStream(samplerate=AUDIO_SAMPLE_RATE, channels=1, blocksize=CHUNK_SIZE, callback=capture_audio_callback)
    
    with stream:
        print("Microphone is active. Launching MachineWhisperer...")
        
        # Create a visual metronome (Timer) that updates the screen every 50 milliseconds
        refresh_timer = pg.QtCore.QTimer()
        refresh_timer.timeout.connect(update_dashboard)
        refresh_timer.start(50) 
        
        # Keep the window open until the user clicks the 'X' button
        sys.exit(app.exec())