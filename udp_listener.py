import socket
import json
import time # Import the time library

LISTEN_IP = "192.168.10.234"
LISTEN_PORT = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"--- UDP Performance Listener Running ---")
print(f"Listening for JSON packets on port {LISTEN_PORT}. Press Ctrl+C to exit.")
print("------------------------------------")

# --- NEW: Variables for tracking packet rate ---
packet_count = 0
last_time = time.time()

try:
    while True:
        data, addr = sock.recvfrom(2048)
        packet_count += 1 # Increment counter for each packet received

        # --- NEW: PPS calculation logic ---
        current_time = time.time()
        if current_time - last_time >= 1.0: # If one second has passed
            print(f"Rate: {packet_count} packets/sec")
            packet_count = 0
            last_time = current_time

            # Optional: To avoid flooding, you can print a sample packet
            # message = data.decode()
            # print(f"Sample from {addr}: {message[:80]}...")


except KeyboardInterrupt:
    print("\nListener stopped.")
finally:
    sock.close()