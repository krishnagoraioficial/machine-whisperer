# Distributed Acoustic Sensing for Predictive Machinery Maintenance
### Project Codename: MachineWhisperer
**Author:** Krishna Gorai (Roll No: 25f1100001)  
**Course:** IITM BS-ES Signal Processing Project  


## 📌 Project Overview
MachineWhisperer is a real-time acoustic sensing and predictive maintenance platform. It actively monitors machinery noise, processes the audio using Digital Signal Processing (DSP) techniques, and visualizes the health of the equipment to detect potential mechanical failures before they become critical. 

Currently, the software utilizes PC/laptop microphones for real-time data capture and uses a baseline RMS threshold for anomaly detection. 

## 🚀 Mid-Term Features & Dashboard
* **Acoustic Calibration:** Includes a standalone scanner that samples room acoustics for 20 seconds using Welch's method to suggest optimal Butterworth bandpass limits (with a hard floor of 80Hz to filter out 50Hz electrical mains hum).
* **Live DSP Pipeline:** Real-time audio filtering, FFT computation (utilizing a Hanning window to prevent edge leakage), and RMS power calculation.
* **Dynamic Visualizations:** A dark-themed GUI built with PyQtGraph featuring a continuous spectrogram for frequency activity, a live filtered acoustic waveform, and an RMS energy trend line.
* **KPI Tracking:** Tracks Machine Health, RMS Energy, Dominant Frequency, and System Status.

### Dashboard Preview
![Anomaly Demo GIF](./assets/video-demo.gif)