import socket

# Use the IP address you found in Step 1.
# Leaving it as "0.0.0.0" means it will listen on all available network interfaces.
LISTEN_IP = "192.168.10.234"
LISTEN_PORT = 12345  # An arbitrary port number. Must match the Android app.

# Create a UDP socket
# AF_INET specifies we're using IPv4.
# SOCK_DGRAM specifies that it is a UDP socket.
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the IP address and port
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"--- UDP Listener Running ---")
print(f"Listening for packets on port {LISTEN_PORT}. Press Ctrl+C to exit.")
print("--------------------------")

try:
    # Loop forever, waiting for data
    while True:
        # Wait to receive data. This is a blocking call.
        # 2048 is the buffer size - the max amount of data to receive at once.
        data, addr = sock.recvfrom(2048)

        # Decode the received bytes into a string and print it
        message = data.decode()
        print(f"Received message from {addr}: {message}")

except KeyboardInterrupt:
    print("\nListener stopped.")
finally:
    # Clean up the socket when the script is closed
    sock.close()
