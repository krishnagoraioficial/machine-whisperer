#include <Arduino.h>
#include <WiFi.h>
#include <driver/i2s.h>

// ==========================================
// 1. CONFIG & SETUP
// ==========================================
// Replace with your Wi-Fi credentials
const char *ssid = "WIFI_SSID";
const char *password = "WIFI_PASSWORD";

// Replace with the IP address of the computer running main_dsp.py
const char *host = "LOCAL_IP_ADDRESS";
const uint16_t port = 5000;

// INMP441 I2S Pin Configuration
#define I2S_PORT I2S_NUM_0
#define I2S_WS 25
#define I2S_SCK 26
#define I2S_SD 33

#define SAMPLE_RATE 16000
#define I2S_BUFFER_SIZE 1024 // how many samples to read at once

WiFiClient client;

// ==========================================
// 2. I2S INITIALIZATION
// ==========================================
void setupI2S() {
  i2s_config_t i2s_config = {
      .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
      .sample_rate = SAMPLE_RATE,
      .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
      .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
      .communication_format =
          i2s_comm_format_t(I2S_COMM_FORMAT_I2S | I2S_COMM_FORMAT_I2S_MSB),
      .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
      .dma_buf_count = 8,
      .dma_buf_len = I2S_BUFFER_SIZE,
      .use_apll = false,
      .tx_desc_auto_clear = false,
      .fixed_mclk = 0};

  i2s_pin_config_t pin_config = {.bck_io_num = I2S_SCK,
                                 .ws_io_num = I2S_WS,
                                 .data_out_num = I2S_PIN_NO_CHANGE,
                                 .data_in_num = I2S_SD};

  i2s_driver_install(I2S_PORT, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_PORT, &pin_config);
  i2s_start(I2S_PORT);
}

// ==========================================
// 3. MAIN SETUP & LOOP
// ==========================================
void setup() {
  Serial.begin(115200);
  Serial.println("starting ESP32...");

  // Setup Wi-Fi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected.");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Setup I2S microphone
  setupI2S();
  Serial.println("I2S Microphone initialized.");
}

void loop() {
  // Reconnect to Python server if disconnected
  if (!client.connected()) {
    Serial.println("Connecting to TCP server...");
    if (client.connect(host, port)) {
      Serial.println("Connected to server.");
    } else {
      Serial.println("Connection failed. Retrying in 5 seconds...");
      delay(5000);
      return;
    }
  }

  int16_t i2s_read_buff[I2S_BUFFER_SIZE];
  size_t bytes_read = 0;

  // Read data from the microphone
  i2s_read(I2S_PORT, (void *)i2s_read_buff, sizeof(i2s_read_buff), &bytes_read,
           portMAX_DELAY);

  if (bytes_read > 0) {
    // send audio data over wifi
    client.write((const uint8_t *)i2s_read_buff, bytes_read);
  }
}
