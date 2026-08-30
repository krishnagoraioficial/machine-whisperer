# ---------------------------------------------------------
# FILE: main_dsp.py
# AUTHOR: Krishna Gorai (Roll No: 25f1100001)
# PURPOSE: Core DSP backend. Handles Butterworth filtering, FFT, 
#          and RMS math. Currently uses a hardcoded threshold for 
#          anomalies. Phase 2 will replace this with a trained ML classifier.
# ---------------------------------------------------------
import sys
import numpy as np
import scipy.signal as signal
import sounddevice as sd
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

# Import the new industrial UI layout
from ui_dashboard import DashboardUI

# ==========================================
# 1. CONFIG & SETUP
# ==========================================
AUDIO_SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
WATERFALL_FRAMES = 100
FILTER_STEEPNESS = 4

audio_buffer = np.zeros(CHUNK_SIZE) 
spectrogram_data = np.zeros((WATERFALL_FRAMES, CHUNK_SIZE // 2))
rms_history = np.zeros(WATERFALL_FRAMES)

def create_digital_filter(low_hz, high_hz, rate, order):
    """Calculates the b, a coefficients for the Butterworth filter."""
    nyquist_limit = 0.5 * rate
    normalized_low = low_hz / nyquist_limit
    normalized_high = high_hz / nyquist_limit
    return signal.butter(order, [normalized_low, normalized_high], btype='bandpass')

# Set the default startup filter
filter_b, filter_a = create_digital_filter(80.0, 3000.0, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)

def capture_audio_callback(indata, frames, time, status):
    """Background thread to grab mic data into the buffer."""
    global audio_buffer 
    if status: print(f"Mic Warning: {status}")
    audio_buffer = indata[:, 0]

# ==========================================
# 2. APPLICATION BOOTSTRAP
# ==========================================
app = QApplication(sys.argv)
ui = DashboardUI()

def update_filter_preset():
    """Recalculates filter math when the user clicks Apply on the UI."""
    global filter_b, filter_a
    new_low = float(ui.lowcut_input.value())
    new_high = float(ui.highcut_input.value())
    
    # Safety check to prevent math crashes
    if new_low >= new_high: return 
    filter_b, filter_a = create_digital_filter(new_low, new_high, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)

ui.apply_btn.clicked.connect(update_filter_preset)

# ==========================================
# 3. DSP & UPDATE LOOP
# ==========================================
def update_dashboard():
    """Main loop: runs the math and pushes data to the UI class."""
    global spectrogram_data, rms_history
    
    # 1. Clean the audio wave
    filtered_audio = signal.lfilter(filter_b, filter_a, audio_buffer)
    ui.waveform_curve.setData(filtered_audio)

    # Auto-scale waveform Y-axis
    peak_amp = np.max(np.abs(filtered_audio))
    if peak_amp > 0.5:
        ui.waveform_plot.setYRange(-peak_amp * 1.1, peak_amp * 1.1)
    else:
        ui.waveform_plot.setYRange(-0.5, 0.5)

    # 2. FFT for the spectrogram (with Hanning window to prevent edge leakage)
    windowed_audio = filtered_audio * np.hanning(len(filtered_audio))
    fft_magnitude = np.abs(np.fft.rfft(windowed_audio))[:-1]
    fft_db = 20 * np.log10(fft_magnitude + 1e-6)
    
    spectrogram_data = np.roll(spectrogram_data, -1, axis=0)
    spectrogram_data[-1, :] = fft_db
    ui.image_item.setImage(spectrogram_data, autoLevels=False)

    # Auto-scale heatmap brightness
    peak_fft = np.max(fft_db)
    if peak_fft > 40:
        ui.image_item.setLevels((-30, peak_fft * 1.1))
    else:
        ui.image_item.setLevels((-30, 40))
        
    # 3. RMS power calculation
    current_rms = np.sqrt(np.mean(filtered_audio**2))
    rms_history = np.roll(rms_history, -1)
    rms_history[-1] = current_rms
    ui.rms_curve.setData(rms_history)

    # Auto-scale RMS graph Y-axis
    peak_rms = np.max(rms_history)
    if peak_rms > 0.2:
        ui.rms_plot.setYRange(0, peak_rms * 1.1)
    else:
        ui.rms_plot.setYRange(0, 0.2)

    # --- KPI & ANOMALY LOGIC ---
    # Find the loudest frequency in this specific audio chunk
    dom_freq_idx = np.argmax(fft_magnitude)
    dominant_frequency_hz = dom_freq_idx * (AUDIO_SAMPLE_RATE / CHUNK_SIZE)
    
    # PHASE 1 ANOMALY DETECTION: Hardcoded baseline threshold.
    # If the RMS spikes over 0.1, trigger the UI alarm.
    # ROADMAP: In Phase 2, this boolean will be replaced by a trained 
    # Machine Learning classifier analyzing the extracted acoustic features.
    is_anomaly = current_rms > 0.1
    
    # Push the numbers to the frontend UI
    ui.update_kpis(current_rms, dominant_frequency_hz, is_anomaly)

if __name__ == '__main__':
    ui.show()
    stream = sd.InputStream(samplerate=AUDIO_SAMPLE_RATE, channels=1, blocksize=CHUNK_SIZE, callback=capture_audio_callback)
    with stream:
        print("Microphone is active. Launching Machine-whisperer...")
        refresh_timer = pg.QtCore.QTimer()
        refresh_timer.timeout.connect(update_dashboard)
        refresh_timer.start(50) 
        sys.exit(app.exec())