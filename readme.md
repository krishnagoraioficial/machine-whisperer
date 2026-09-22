# Machine Whisperer
**Author:** Krishna Gorai (Roll No: 25f1100001)  
**Course:** IITM BS-ES Signal Processing Project  

---

## Overview
MachineWhisperer is a real-time acoustic sensing and predictive maintenance project. It listens to machinery noise, processes the audio using DSP, and visualizes the health of the equipment to detect potential mechanical failures.

In the current stage, we use an ESP32 microcontroller with an INMP441 I2S microphone to capture audio remotely. The audio data is streamed over Wi-Fi (TCP) to a laptop running a Python dashboard for real-time DSP analysis.

---

## Tech Stack

* **Hardware:** ESP32, INMP441 I2S MEMS Microphone.
* **Firmware:** C++ (Arduino Core for ESP32) with Wi-Fi TCP sockets.
* **DSP & Backend:** Python 3, `NumPy`, `SciPy` (Butterworth bandpass filtering, FFT).
* **Machine Learning:** `scikit-learn` (Isolation Forest) and `joblib` for anomaly detection.
* **UI & Dashboard:** `PyQt6` and `PyQtGraph` for real-time, lag-free data visualization.

---

## Features

* **Wireless Audio Streaming:** ESP32 captures audio and sends raw 16-bit PCM data over a Wi-Fi hotspot to the Python server.
* **Live DSP Pipeline:** Real-time audio filtering, FFT computation, and RMS power calculation.
* **Dashboard Visualizations:** A dark-themed GUI featuring a continuous spectrogram, a live filtered waveform, and an RMS energy trend line.
* **Machine Learning Anomaly Detection:** An unsupervised ML model (Isolation Forest) dynamically learns the acoustic baseline of the machinery (via a "Record Baseline" button) and automatically flags abnormal vibrations and signature deviations in real-time.

---

## Project Structure

* `esp32_firmware/esp32_firmware.ino` - The code running on the ESP32 to capture mic data and send it over Wi-Fi.
* `main_dsp.py` - The main Python script that runs the TCP server, processes incoming audio, and runs the dashboard.
* `ui_dashboard.py` - Contains the PyQt6 layout and styling for the dashboard.
* `environment_scanner.py` - A utility script for initial acoustic calibration.

---

### Dashboard Preview
![Anomaly Demo GIF](./assets/video-demo.gif)