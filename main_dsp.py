# main file for audio processing and dashboard
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

# function to create the bandpass filter
def create_digital_filter(low_hz, high_hz, rate, order):
    nyquist_limit = 0.5 * rate
    normalized_low = low_hz / nyquist_limit
    normalized_high = high_hz / nyquist_limit
    return signal.butter(order, [normalized_low, normalized_high], btype='bandpass')

# initial filter setup
filter_b, filter_a = create_digital_filter(80.0, 3000.0, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)

# thread to receive audio from esp32
def tcp_server_thread():
    global audio_buffer
    HOST = '0.0.0.0'
    PORT = 5000
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)
    print(f"listening on {HOST}:{PORT}. waiting for esp32...")
    
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

ui.apply_btn.clicked.connect(update_filter_preset)

# main loop to process audio and update UI
def update_dashboard():
    global spectrogram_data, rms_history
    
    # copy buffer to avoid race conditions and remove DC offset
    local_audio = audio_buffer - np.mean(audio_buffer)

    # update raw audio
    ui.raw_waveform_curve.setData(local_audio)
    raw_peak = np.max(np.abs(local_audio))
    raw_y = max(raw_peak * 1.2, 0.05) # Increased minimum range to hide noise
    ui.raw_waveform_plot.setYRange(-raw_y, raw_y)

    # filter the audio
    filtered_audio = signal.lfilter(filter_b, filter_a, local_audio)
    ui.waveform_curve.setData(filtered_audio)

    # auto-scale waveform
    peak_amp = np.max(np.abs(filtered_audio))
    filtered_y = max(peak_amp * 1.2, 0.05) # Increased minimum range to hide noise
    ui.waveform_plot.setYRange(-filtered_y, filtered_y)

    # calculate fft for spectrogram
    windowed_audio = filtered_audio * np.hanning(len(filtered_audio))
    fft_magnitude = np.abs(np.fft.rfft(windowed_audio))[:-1]
    fft_db = 20 * np.log10(fft_magnitude + 1e-6)
    
    spectrogram_data = np.roll(spectrogram_data, -1, axis=0)
    spectrogram_data[-1, :] = fft_db
    ui.image_item.setImage(spectrogram_data, autoLevels=False)

    peak_fft = np.max(fft_db)
    # Set a constant 60dB dynamic range, but don't let the peak drop too low during silence
    upper_level = max(peak_fft, 10.0)
    ui.image_item.setLevels((upper_level - 60, upper_level))
        
    # calculate rms power
    current_rms = np.sqrt(np.mean(filtered_audio**2))
    rms_history = np.roll(rms_history, -1)
    rms_history[-1] = current_rms
    ui.rms_curve.setData(rms_history)

    peak_rms = np.max(rms_history)
    if peak_rms > 0.2:
        ui.rms_plot.setYRange(0, peak_rms * 1.1)
    else:
        ui.rms_plot.setYRange(0, 0.2)

    # get the dominant frequency
    dom_freq_idx = np.argmax(fft_magnitude)
    dominant_frequency_hz = dom_freq_idx * (AUDIO_SAMPLE_RATE / CHUNK_SIZE)
    
    # basic anomaly detection using hardcoded threshold
    is_anomaly = current_rms > 0.1
    
    ui.update_kpis(current_rms, dominant_frequency_hz, is_anomaly)

if __name__ == '__main__':
    tcp_thread = threading.Thread(target=tcp_server_thread, daemon=True)
    tcp_thread.start()
    
    ui.show()
    print("starting dashboard...")
    refresh_timer = pg.QtCore.QTimer()
    refresh_timer.timeout.connect(update_dashboard)
    refresh_timer.start(50) 
    sys.exit(app.exec())