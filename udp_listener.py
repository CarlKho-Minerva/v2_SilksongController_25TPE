import socket
import json # Import the JSON library

LISTEN_IP = "192.168.10.234"
LISTEN_PORT = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"--- UDP JSON Listener Running ---")
print(f"Listening for JSON packets on port {LISTEN_PORT}. Press Ctrl+C to exit.")
print("-------------------------------")

try:
    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode()

        # --- NEW: Try to parse the message as JSON ---
        try:
            parsed_json = json.loads(message)
            print(f"Received from {addr}:")
            # Pretty-print the JSON with an indent of 2 spaces
            print(json.dumps(parsed_json, indent=2))
        except json.JSONDecodeError:
            # If it's not valid JSON, just print the raw message
            print(f"Received non-JSON from {addr}: {message}")

except KeyboardInterrupt:
    print("\nListener stopped.")
finally:
    sock.close()