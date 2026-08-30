# Distributed Acoustic Sensing for Predictive Machinery Maintenance
### Project Codename: MachineWhisperer
**Author:** Krishna Gorai (Roll No: 25f1100001)  
**Course:** IITM BS-ES Signal Processing Project  

---

## 📌 Project Overview
MachineWhisperer is a real-time acoustic sensing and predictive maintenance platform. It actively monitors machinery noise, processes the audio using Digital Signal Processing (DSP) techniques, and visualizes the health of the equipment to detect potential mechanical failures before they become critical. 

Currently, the software utilizes PC/laptop microphones for real-time data capture and uses a baseline RMS threshold for anomaly detection. 

---

## 🛠️ Technology Stack

### Current Implementation (Phase 1 — Mid-Term)
* **Programming Language:** Python 3
* **Digital Signal Processing (DSP):** `NumPy` (FFT, buffering, RMS calculations), `SciPy` (Butterworth bandpass filtering, Welch's PSD estimation).
* **Audio Capture:** `sounddevice` (real-time low-latency microphone streaming).
* **Frontend UI & Visualization:** `PyQt6` (layout, QSS styling, event handling) and `PyQtGraph` (hardware-accelerated, lag-free dynamic graph rendering).

### Future Implementation (Phase 2)
* **Hardware Edge Nodes:** Transitioning to ESP32 microcontrollers paired with I2S Digital MEMS Microphones (e.g., INMP441) for remote, dedicated data acquisition.
* **Networking:** TCP/IP Wi-Fi sockets to wirelessly stream real-time, uncompressed audio payloads to the central processing hub.
* **Machine Learning:** Integrating anomaly classification models (e.g., `scikit-learn` or `TensorFlow Lite`) to classify specific mechanical faults (e.g., bearing wear vs. misalignment) using acoustic features, replacing the basic RMS threshold method.

---

## 🚀 Mid-Term Features
* **Acoustic Calibration:** Includes a standalone scanner that samples room acoustics for 20 seconds using Welch's method to suggest optimal Butterworth bandpass limits (with a hard floor of 80Hz to filter out 50Hz electrical mains hum).
* **Live DSP Pipeline:** Real-time audio filtering, FFT computation (utilizing a Hanning window to prevent edge leakage), and RMS power calculation.
* **Dynamic Visualizations:** A dark-themed GUI built with PyQtGraph featuring a continuous spectrogram for frequency activity, a live filtered acoustic waveform, and an RMS energy trend line.
* **KPI Tracking:** Tracks Machine Health, RMS Energy, Dominant Frequency, and System Status.

---

## 🖥️ Dashboard Architecture (What We Are Showing)

The SCADA-style dashboard provides a comprehensive real-time view of machinery health, structured into the following components:

1. **Telemetry Header:** Includes a dropdown to select different monitored machinery (ready for multi-node deployment) alongside a live data connection indicator.
2. **KPI Health Cards:** * **Machine Health & System Status:** High-level operational indicators indicating normal conditions or critical alerts.
   * **RMS Energy:** Real-time root-mean-square vibration energy calculations.
   * **Dominant Frequency:** Real-time peak frequency identification, pointing to the loudest mechanical component in the frequency spectrum.
3. **Anomaly Detection Panel & Controls:** Displays current alert status (triggering on RMS threshold breaches) and provides user input fields to adjust Low-Cut and High-Cut DSP filters on the fly.
4. **Continuous Spectrogram (Top Graph):** A rolling heatmap showing the intensity of all frequency bands over time, helping visually identify newly emerging mechanical noise.
5. **Live Acoustic Signal (Middle Graph):** A time-domain waveform showing the physical shape and amplitude of the currently filtered audio signal.
6. **Machine Health Trend (Bottom Graph):** A scrolling timeline explicitly tracking RMS energy, making it easy to spot sudden physical stress or degradation spikes over time.

### Dashboard Preview
![Anomaly Demo GIF](./assets/video-demo.gif)