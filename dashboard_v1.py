# ---------------------------------------------------------
# FILE: dashboard_v1.py
# PURPOSE: Live DSP Pipeline capturing laptop mic audio.
#UPDATE-1: Added Butterworth Band-pass filter to remove 
#          60Hz electrical noise, added RMS energy tracking,
#          and update spectrogram colormap to 'inferno'.
# ---------------------------------------------------------

import sys
import numpy as np
import scipy.signal as signal
import sounddevice as sd
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

# ==========================================
# 1. CONFIGURATION VARIABLES
# ==========================================
AUDIO_SAMPLE_RATE = 16000  # Number of audio samples taken per second (16kHz). Matches ESP32 later.
CHUNK_SIZE = 1024          # How many audio data points we process at one time. 
WATERFALL_FRAMES = 100     # The number of historical time steps shown on the spectrogram heatmap.

# FILTER SETTING 
#Low-Cutoff: 80Hz to block electrical noise.
#High-Cutoff: 3kHz to block pitched hissing.
LOWCUT_FREQ_HZ = 80.0
HIGHCUT_FREQ_HZ = 3000.0
FILTER_STEEPNESS = 4    # setting of 4 provides a smooth, reliable frequency cut-off

# ==========================================
# 2. DATA STORAGE (ARRAYS)
# ==========================================
# I use NumPy arrays because they are mathematically much faster than standard Python lists.
# 'audio_buffer' holds the raw audio wave we hear right now.
audio_buffer = np.zeros(CHUNK_SIZE) 

# 'spectrogram_data' is a 2D grid (matrix) holding the history of frequencies.
spectrogram_data = np.zeros((WATERFALL_FRAMES, CHUNK_SIZE // 2))
rms_history = np.zeros(WATERFALL_FRAMES) 

def create_digital_filter(low_hz, high_hz, rate, order):
    """
    Calculates the mathematical coefficients (b, a) for a Butterworth filter.
    Variables:
    - nyquist_limit: The absolute maximum frequency we can measure (half the sample rate).
    - b_coeff, a_coeff: The mathematical multipliers used later to clean the wave.
    """
    nyquist_limit = 0.5 * rate
    normalized_low = low_hz / nyquist_limit
    normalized_high = high_hz / nyquist_limit
    
    b_coeff, a_coeff = signal.butter(order, [normalized_low, normalized_high], btype='bandpass')
    return b_coeff, a_coeff

# Generate the filter math once before the program starts listening
filter_b, filter_a = create_digital_filter(LOWCUT_FREQ_HZ, HIGHCUT_FREQ_HZ, AUDIO_SAMPLE_RATE, FILTER_STEEPNESS)


# ==========================================
# 3. MICROPHONE CAPTURE FUNCTION
# ==========================================
def capture_audio_callback(indata, frames, time, status):
    """
    This function acts as an automatic background listener. 
    Every time the microphone hears a 'CHUNK_SIZE' of audio, this function is triggered.
    """
    global audio_buffer # Use the global array defined above
    
    if status:
        print(f"Mic Status/Error: {status}")
    
    # indata[:, 0] grabs just the Left channel (Mono) of the microphone audio
    audio_buffer = indata[:, 0] 

# ==========================================
# 4. USER INTERFACE (GUI) SETUP
# ==========================================
app = QApplication(sys.argv)
# Create the main window and give it your official project codename
window = pg.GraphicsLayoutWidget(show=True, title="MachineWhisperer V1.1")
window.resize(1000, 800) # Width, Height in pixels

# Create the top plot for the raw audio wave
waveform_plot = window.addPlot(title="Live Raw Audio Waveform", row=0, col=0)
waveform_plot.setYRange(-0.5, 0.5) # Lock the Y-axis so the wave doesn't jump around wildly
waveform_curve = waveform_plot.plot(pen='c') # 'c' makes the line Cyan colored

# Create the bottom plot for the scrolling spectrogram
spectrogram_plot = window.addPlot(title="Continuous Spectrogram (Frequency over Time)", row=1, col=0)
image_item = pg.ImageItem()
spectrogram_plot.addItem(image_item)
# Updated to 'inferno' for high contrast, and widened the sensitivity range (-30 to 40)
image_item.setColorMap(pg.colormap.get('inferno'))
image_item.setLevels((-30, 40))

# RMS Energy Plot
rms_plot = window.addPlot(title="RMS Energy Trend (Machine Health)", row=2, col=0)
rms_plot.setYRange(0, 0.2)
rms_curve = rms_plot.plot(pen='r', fillLevel=0, brush=(255, 0, 0, 50)) 

# ==========================================
# 5. SIGNAL PROCESSING & SCREEN REFRESH
# ==========================================
def update_dashboard():
    """
    This function is triggered by a timer. It takes the latest audio, 
    does the math, and redraws the screen.
    """
    global spectrogram_data, rms_history
    
    # STEP A: Apply the filter to remove 60Hz hum and high noise
    filtered_audio = signal.lfilter(filter_b, filter_a, audio_buffer)
    waveform_curve.setData(filtered_audio)
    
    # STEP B: Calculate Spectrogram
    windowed_audio = filtered_audio * np.hanning(len(filtered_audio))
    fft_magnitude = np.abs(np.fft.rfft(windowed_audio))[:-1]
    fft_db = 20 * np.log10(fft_magnitude + 1e-6)
    
    spectrogram_data = np.roll(spectrogram_data, -1, axis=0)
    spectrogram_data[-1, :] = fft_db
    image_item.setImage(spectrogram_data, autoLevels=False)
    
    # STEP C: Calculate RMS Energy (Root Mean Square)
    # This measures the overall power of the cleaned audio wave
    current_rms = np.sqrt(np.mean(filtered_audio**2))
    
    # Shift the old energy history to the left and add the new calculation
    rms_history = np.roll(rms_history, -1)
    rms_history[-1] = current_rms
    rms_curve.setData(rms_history)

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