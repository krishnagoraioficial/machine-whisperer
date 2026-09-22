import socket
import time
import numpy as np

# Configuration
HOST = '127.0.0.1'
PORT = 5000
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

def generate_audio_chunk(time_offset, is_anomaly):
    """
    Generates synthetic 16-bit PCM audio.
    Simulates a motor spinning (normal) or grinding (anomaly).
    """
    # Create time array for this chunk
    t = np.linspace(time_offset, time_offset + (CHUNK_SIZE / SAMPLE_RATE), CHUNK_SIZE, endpoint=False)
    
    # Normal operation: 200 Hz base frequency + normal mechanical noise
    signal = 0.1 * np.sin(2 * np.pi * 200 * t) 
    signal += 0.05 * np.random.randn(CHUNK_SIZE) # Background noise
    
    # Introduce an anomaly (e.g. grinding bearing)
    if is_anomaly:
        # Sudden spike in energy and a high-pitched 1500 Hz frequency
        signal += 0.6 * np.sin(2 * np.pi * 1500 * t)
        signal += 0.3 * np.random.randn(CHUNK_SIZE) # More noise
        
    # Scale to 16-bit PCM range (-32768 to 32767)
    signal_int16 = np.int16(signal * 32767)
    return signal_int16.tobytes()

def run_simulation():
    print(f"Connecting to MachineWhisperer Dashboard at {HOST}:{PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((HOST, PORT))
        print("Connected successfully! Sending normal baseline data...")
    except ConnectionRefusedError:
        print("Error: Could not connect. Make sure you run 'python3 main_dsp.py' first!")
        return

    time_offset = 0.0
    start_time = time.time()
    
    try:
        while True:
            elapsed = time.time() - start_time
            
            # Switch to anomaly mode after 15 seconds for presentation demo
            is_anomaly = False
            if elapsed > 15.0 and elapsed < 20.0:
                is_anomaly = True
                if int(elapsed * 10) % 10 == 0:
                    print("⚠️ INJECTING ANOMALY DATA...")
            elif elapsed >= 20.0:
                print("Returning to normal baseline...")
                start_time = time.time() # Reset cycle
                
            # Generate and send fake audio chunk
            audio_bytes = generate_audio_chunk(time_offset, is_anomaly)
            s.sendall(audio_bytes)
            
            time_offset += (CHUNK_SIZE / SAMPLE_RATE)
            
            # Sleep slightly less than the chunk duration to simulate real-time stream
            time.sleep((CHUNK_SIZE / SAMPLE_RATE) * 0.9)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped.")
    except Exception as e:
        print(f"Connection lost: {e}")
    finally:
        s.close()

if __name__ == '__main__':
    run_simulation()
