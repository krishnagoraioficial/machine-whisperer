# main_dsp.py
# This is the main python script that runs on the laptop to process the incoming audio stream.
# It sets up a TCP server to listen to the ESP32, runs the digital signal processing (DSP) pipeline,
# and updates the PyQtGraph dashboard in real-time.
import sys
import numpy as np
import scipy.signal as signal
import socket
import threading
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

from ui_dashboard import DashboardUI

AUDIO_SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
WATERFALL_FRAMES = 100
FILTER_STEEPNESS = 8

audio_buffer = np.zeros(CHUNK_SIZE) 
spectrogram_data = np.zeros((WATERFALL_FRAMES, CHUNK_SIZE // 2))
rms_history = np.zeros(WATERFALL_FRAMES)

# Baseline calibration globals
is_calibrating = False
calibration_frames = []
baseline_spectrum = None
CALIBRATION_MAX_FRAMES = 200 # ~10.0 seconds at 50ms refresh

# Helper function to generate a Butterworth bandpass filter
# Using Butterworth because it gives a flat frequency response in the passband (good for our audio)
def create_digital_filter(low_hz, high_hz, rate, order):
    nyquist_limit = 0.5 * rate
    normalized_low = low_hz / nyquist_limit
    normalized_high = high_hz / nyquist_limit
    return signal.butter(order, [normalized_low, normalized_high], btype='bandpass')

# initial filter setup
filter_b, filter_a = create_digital_filter(80.0, 3000.0, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)

# This thread runs constantly in the background to grab audio bytes from the ESP32 over Wi-Fi
def tcp_server_thread():
    global audio_buffer
    HOST = '0.0.0.0'
    PORT = 5000
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT)) # 0.0.0.0 means we listen on all available network interfaces (generic)
    server_socket.listen(1)
    print(f"Server is listening on {HOST}:{PORT}. Waiting for ESP32 to connect...")
    
    while True:
        conn, addr = server_socket.accept()
        print(f"esp32 connected from {addr}")
        
        try:
            expected_bytes = CHUNK_SIZE * 2 # 1024 samples * 2 bytes
            accumulated_data = bytearray()
            
            while True:
                data = conn.recv(expected_bytes)
                if not data:
                    break 
                
                accumulated_data.extend(data)
                
                # wait until we have a full chunk
                while len(accumulated_data) >= expected_bytes:
                    chunk = accumulated_data[:expected_bytes]
                    del accumulated_data[:expected_bytes]
                    
                    raw_samples = np.frombuffer(chunk, dtype=np.int16)
                    # Convert raw 16-bit PCM (from -32768 to 32767) into float between -1.0 and 1.0
                    float_samples = raw_samples.astype(np.float32) / 32768.0
                    
                    if np.random.random() < 0.05:
                        print(f"raw max: {np.max(raw_samples)}, float max: {np.max(float_samples):.6f}")
                    
                    audio_buffer = float_samples
        except Exception as e:
            print(f"socket error: {e}")
        finally:
            conn.close()
            print("esp32 disconnected, waiting again...")

app = QApplication(sys.argv)
ui = DashboardUI()

# update filter when user clicks apply button
def update_filter_preset():
    global filter_b, filter_a
    new_low = float(ui.lowcut_input.value())
    new_high = float(ui.highcut_input.value())
    
    if new_low >= new_high: return 
    filter_b, filter_a = create_digital_filter(new_low, new_high, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)
    
    # Provide visual feedback that the filter was successfully applied
    ui.apply_btn.setText("APPLIED ✓")
    ui.apply_btn.setStyleSheet("background-color: #35D07F; color: #0B1117;")
    pg.QtCore.QTimer.singleShot(1500, lambda: ui.apply_btn.setText("APPLY FILTER"))
    pg.QtCore.QTimer.singleShot(1500, lambda: ui.apply_btn.setStyleSheet(""))

ui.apply_btn.clicked.connect(update_filter_preset)

def start_calibration():
    global is_calibrating, calibration_frames
    is_calibrating = True
    calibration_frames = []
    print("Starting baseline calibration...")
    ui.set_calibration_mode(True)

ui.calibrate_btn.clicked.connect(start_calibration)

# This is the main loop that gets called every 50ms by the QTimer to refresh the UI and run the DSP math
def update_dashboard():
    global spectrogram_data, rms_history
    
    # copy buffer to avoid race conditions and remove DC offset
    local_audio = audio_buffer - np.mean(audio_buffer)

    # update raw audio
    ui.raw_waveform_curve.setData(local_audio)
    raw_peak = np.max(np.abs(local_audio))
    raw_y = max(raw_peak * 1.2, 0.05) # Increased minimum range to hide noise
    ui.raw_waveform_plot.setYRange(-raw_y, raw_y)

    # Apply the bandpass filter to isolate machine noise and drop background AC hum
    filtered_audio = signal.lfilter(filter_b, filter_a, local_audio)
    ui.waveform_curve.setData(filtered_audio)

    # auto-scale waveform
    peak_amp = np.max(np.abs(filtered_audio))
    filtered_y = max(peak_amp * 1.2, 0.05) # Increased minimum range to hide noise
    ui.waveform_plot.setYRange(-filtered_y, filtered_y)

    # Calculate FFT to see the frequency spectrum
    # We apply a Hanning window first to reduce spectral leakage at the edges of the chunk
    windowed_audio = filtered_audio * np.hanning(len(filtered_audio))
    fft_magnitude = np.abs(np.fft.rfft(windowed_audio))[:-1]
    
    # Convert amplitude to Decibels (dB) for the waterfall plot so we can actually see quiet sounds
    fft_db = 20 * np.log10(fft_magnitude + 1e-6)
    
    spectrogram_data = np.roll(spectrogram_data, -1, axis=0)
    spectrogram_data[-1, :] = fft_db
    ui.image_item.setImage(spectrogram_data, autoLevels=False)

    peak_fft = np.max(fft_db)
    # Set a constant 60dB dynamic range, but don't let the peak drop too low during silence
    upper_level = max(peak_fft, 10.0)
    ui.image_item.setLevels((upper_level - 60, upper_level))
        
    # Calculate Root Mean Square (RMS) Energy using the formula: sqrt(mean(x^2))
    # This acts as our baseline "vibration severity" indicator
    current_rms = np.sqrt(np.mean(filtered_audio**2))
    rms_history = np.roll(rms_history, -1)
    rms_history[-1] = current_rms
    ui.rms_curve.setData(rms_history)

    peak_rms = np.max(rms_history)
    if peak_rms > 0.2:
        ui.rms_plot.setYRange(0, peak_rms * 1.1)
    else:
        ui.rms_plot.setYRange(0, 0.2)

    # Find the dominant frequency by checking which FFT bin has the max energy
    # Bin index * (Sample_Rate / Chunk_Size) gives us the actual Hertz value
    dom_freq_idx = np.argmax(fft_magnitude)
    dominant_frequency_hz = dom_freq_idx * (AUDIO_SAMPLE_RATE / CHUNK_SIZE)
    
    # --- ANOMALY DETECTION LOGIC ---
    global is_calibrating, calibration_frames, baseline_spectrum
    
    is_anomaly = False
    health_score = 100
    status_text = "██████████░ NORMAL"
    sys_status = "● NORMAL"
    sys_desc = "No anomalies detected"
    
    if is_calibrating:
        calibration_frames.append(fft_magnitude)
        health_score = 99
        status_text = f"CALIBRATING... ({len(calibration_frames)}/{CALIBRATION_MAX_FRAMES})"
        sys_status = "● CALIBRATING"
        sys_desc = "Building spectral baseline profile"
        if len(calibration_frames) >= CALIBRATION_MAX_FRAMES:
            baseline_spectrum = np.mean(calibration_frames, axis=0)
            baseline_spectrum = np.maximum(baseline_spectrum, 1e-6) # prevent div/0
            is_calibrating = False
            print("Calibration complete.")
            ui.set_calibration_mode(False)
    elif baseline_spectrum is not None:
        energy_ratio = fft_magnitude / baseline_spectrum
        
        # Analyze specific bands based on filters, e.g. 80Hz to 3000Hz
        # (This is where the actual machine mechanical noise usually sits)
        start_bin = int(80 / (AUDIO_SAMPLE_RATE / CHUNK_SIZE))
        end_bin = int(3000 / (AUDIO_SAMPLE_RATE / CHUNK_SIZE))
        
        if start_bin < len(energy_ratio) and end_bin < len(energy_ratio):
            band_ratio = energy_ratio[start_bin:end_bin]
            peak_ratio = np.max(band_ratio)
            mean_ratio = np.mean(band_ratio)
            
            # Anomaly condition: mean energy 3x higher OR a specific peak is 8x higher than baseline
            if mean_ratio > 3.0 or peak_ratio > 8.0:
                is_anomaly = True
                
            if is_anomaly:
                health_score = max(0, 100 - int(peak_ratio * 5))
                status_text = f"⚠️ {peak_ratio:.1f}x BASELINE ENERGY SPIKE"
                sys_status = "🔴 CRITICAL"
                sys_desc = "Abnormal spectral energy detected"
            else:
                health_score = max(50, 100 - int((mean_ratio - 1.0) * 10)) if mean_ratio > 1 else 100
                status_text = "██████████░ NORMAL (Monitored)"
                sys_desc = f"Tracking normal. Peak ratio: {peak_ratio:.1f}x"
    else:
        status_text = "Awaiting Calibration"
        sys_status = "⚪ STANDBY"
        sys_desc = "Click 'Calibrate Baseline' to start"
        health_score = "--"
    
    ui.update_kpis(current_rms, dominant_frequency_hz, is_anomaly, health_score, status_text, sys_status, sys_desc)

if __name__ == '__main__':
    tcp_thread = threading.Thread(target=tcp_server_thread, daemon=True)
    tcp_thread.start()
    
    ui.show()
    print("starting dashboard...")
    refresh_timer = pg.QtCore.QTimer()
    refresh_timer.timeout.connect(update_dashboard)
    refresh_timer.start(50) 
    sys.exit(app.exec())