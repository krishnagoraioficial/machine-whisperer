# ---------------------------------------------------------
# FILE: dashboard_v1.py
# PURPOSE: Captures laptop microphone audio and displays 
#          a live waveform and continuous spectrogram.
# ---------------------------------------------------------

import sys
import numpy as np
import sounddevice as sd
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

# ==========================================
# 1. CONFIGURATION VARIABLES
# ==========================================
# Why these names? We use UPPERCASE for constants (values that don't change).
AUDIO_SAMPLE_RATE = 16000  # Number of audio samples taken per second (16kHz). Matches ESP32 later.
CHUNK_SIZE = 1024          # How many audio data points we process at one time. 
WATERFALL_FRAMES = 100     # The number of historical time steps shown on the spectrogram heatmap.

# ==========================================
# 2. DATA STORAGE (ARRAYS)
# ==========================================
# We use NumPy arrays because they are mathematically much faster than standard Python lists.
# 'audio_buffer' holds the raw audio wave we hear right now.
audio_buffer = np.zeros(CHUNK_SIZE) 

# 'spectrogram_data' is a 2D grid (matrix) holding the history of frequencies.
spectrogram_data = np.zeros((WATERFALL_FRAMES, CHUNK_SIZE // 2))

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

# Apply a professional color map to the spectrogram (viridis goes from dark purple to bright yellow)
colormap = pg.colormap.get('viridis')
image_item.setColorMap(colormap)
image_item.setLevels((0, 60)) # Sets the color contrast (min dB, max dB)

# ==========================================
# 5. SIGNAL PROCESSING & SCREEN REFRESH
# ==========================================
def update_dashboard():
    """
    This function is triggered by a timer. It takes the latest audio, 
    does the math, and redraws the screen.
    """
    global spectrogram_data
    
    # STEP A: Draw the raw audio wave
    waveform_curve.setData(audio_buffer)
    
    # STEP B: Digital Signal Processing (DSP)
    # 1. Windowing: Smooth the edges of the audio chunk to prevent artificial spikes (spectral leakage).
    windowed_audio = audio_buffer * np.hanning(len(audio_buffer))
    
    # 2. Fast Fourier Transform (FFT): Convert the audio wave (time) into frequencies (pitch).
    fft_magnitude = np.abs(np.fft.rfft(windowed_audio))[:-1] 
    
    # 3. Convert to Decibels (dB) so it is easier for our eyes to see the contrast on the screen.
    fft_db = 20 * np.log10(fft_magnitude + 1e-6)
    
    # STEP C: Update the Spectrogram image
    # Shift all old data down by 1 row, and put the brand new frequency data at the top.
    spectrogram_data = np.roll(spectrogram_data, -1, axis=0)
    spectrogram_data[-1, :] = fft_db
    
    # Draw the new heatmap matrix to the screen
    image_item.setImage(spectrogram_data, autoLevels=False)

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