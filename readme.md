# Machine Whisperer: Predictive Machinery Maintenance via Acoustic Sensing

**Author:** Krishna Gorai (Roll No: 25f1100001)  
**Course:** IITM BS-ES Signal Processing Project  

---

## 🎯 Overview

Machine Whisperer is an advanced, real-time acoustic sensing platform designed for **Predictive Maintenance**. By listening to the acoustic signature (noise) of heavy machinery, the system utilizes Digital Signal Processing (DSP) to isolate mechanical frequencies and flag anomalies before catastrophic failure occurs.

In its current state, an ESP32 microcontroller with an INMP441 I2S microphone captures the audio at the edge. This raw PCM data is streamed wirelessly over Wi-Fi (TCP) to a Python dashboard that runs a live DSP pipeline and statistical anomaly detection.

![Dashboard Preview](./assets/video-demo.gif)

---

## ⚙️ Technical Specifications & Performance

Through optimization of the C++ network buffer and Python's PyQtGraph threading, this project achieves high-performance edge-to-server analytics:

* **Ultra-Low Latency:** The system can transmit audio with just **~30ms delay** in real-time over a standard Wi-Fi TCP connection.
* **Frequency Detection Accuracy:** The FFT binning algorithm can detect the exact dominant frequency coming from the ESP32 + microphone with an accuracy of **±5 Hz**.
* **Filter Precision:** The 8th-order Butterworth digital filter applies frequency cutoffs with a strict roll-off, filtering out-of-band signals with an accuracy of **±20 Hz**.
* **Operating Range:** Currently operates on standard Wi-Fi, providing a reliable indoor range of **100 to 150 feet (30 to 45 meters)** and an outdoor range of **~300 feet (90 meters)**.

---

## 🧮 Core DSP Formulas

The backend relies on three primary mathematical models to process the audio stream:

### 1. Root Mean Square (RMS) Energy
Used to track the overall vibration severity and energy of the machine.
$$ E_{rms} = \sqrt{\frac{1}{N}\sum_{n=0}^{N-1} x[n]^2} $$

### 2. Discrete Fourier Transform (FFT)
Used to convert the time-domain waveform into the frequency domain to isolate specific mechanical grinding or whining. We apply a Hanning window before the FFT to reduce spectral leakage.
$$ X[k] = \sum_{n=0}^{N-1} x[n] \cdot e^{-i 2\pi k n / N} $$

### 3. Butterworth Bandpass Filter
Used to isolate the frequencies (e.g., 80Hz - 3000Hz) where mechanical defects manifest, dropping low-end AC hum and high-end static.
$$ |H(\omega)|^2 = \frac{1}{1 + (\frac{\omega}{\omega_c})^{2n}} $$

---

## 🚀 How to Use (Hardware Setup)

> **Hardware Note:** This project was specifically developed using an **ESP32** and an **INMP441 I2S microphone**. However, it is fully generic and will work with *any* other microcontroller that has I2S communication (like STM32, Teensy) paired with any I2S-based mic. Just adapt the pin connections accordingly in the firmware! If you run into issues getting this to work on other devices, feel free to email me for help at: [krishnagoraioficial@gmail.com](mailto:krishnagoraioficial@gmail.com).

### 1. Wire the Hardware
Connect the INMP441 microphone to your ESP32 as follows:
* **VDD** -> 3.3V
* **GND** -> GND
* **L/R** -> GND (Selects the Left channel)
* **SCK** -> GPIO 26 (Serial Clock)
* **WS** -> GPIO 25 (Word Select / L/R Clock)
* **SD** -> GPIO 33 (Serial Data)

### 2. Start the Server
First, clone the repository and start the Python dashboard on your laptop. Make sure your laptop and ESP32 will be on the exact same Wi-Fi network.
```bash
# Clone the repository
git clone https://github.com/yourusername/machine-whisperer.git
cd machine-whisperer

# Create a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install numpy scipy pyqtgraph PyQt6

# Run the DSP server
python3 main_dsp.py
```

### 3. Flash the ESP32
Open `esp32_firmware/esp32_firmware.ino` in the Arduino IDE (or PlatformIO) and update the credentials:
```cpp
const char *ssid = "YOUR_WIFI_NAME";
const char *password = "YOUR_WIFI_PASSWORD";
const char *host = "192.168.x.x"; // Your laptop's local IP (find using 'ip a' or 'ipconfig')
```
Connect your ESP32 to your PC via USB and hit **Upload**. Once it boots, it will automatically connect to your Wi-Fi and stream data to the Python dashboard.

---

## 🧪 Demo Simulation (No Hardware Required)

If you are presenting this project and do not have the ESP32 hardware plugged in, you can run the included simulation script. It artificially generates a 16kHz audio stream simulating a motor and allows you to inject an "anomaly" (a high-pitched 1500Hz grinding noise) to demonstrate the dashboard's detection capabilities.

1. Start the dashboard: `python3 main_dsp.py`
2. In a new terminal, start the mock client: `python3 mock_esp32_client.py`
3. Click **"CALIBRATE BASELINE (10s)"** in the dashboard.
4. After 15 seconds, the mock script will automatically inject the anomaly. Watch the dashboard instantly flag the energy spike and turn red!

---

## 🔮 Future Scope & Improvements

While the current Wi-Fi TCP and statistical DSP threshold method is highly effective, the project can be extended significantly for commercial industrial use:

1. **Machine Learning Integration (Edge AI):** 
   Transitioning from statistical ratios to a deployed Isolation Forest or Autoencoder model (`machine_model.joblib`) for complex, multi-dimensional signature degradation tracking.
2. **Custom ASICs for Latency:** 
   Building a custom DSP silicon chip (ASIC) could handle the FFT and Filtering physically on the edge device, reducing the network payload and achieving sub-5ms latency communication with the server.
3. **Public Wireless Telemetry (No Range Limit):** 
   Escaping the 30-45m Wi-Fi restriction by replacing the ESP32 with a cellular IoT module (4G LTE-M / 5G / NB-IoT) or LoRaWAN. This would allow remote monitoring of oil rigs or offshore wind turbines from anywhere in the world.
4. **Predictive Failure Timeline:** 
   Adding a regression algorithm that not only detects the anomaly but predicts *how many days* until total mechanical failure.
5. **Multi-Sensor Fusion:** 
   Combining the acoustic I2S data with an MPU6050 accelerometer to correlate physical vibration with the acoustic noise, dramatically reducing false positives.