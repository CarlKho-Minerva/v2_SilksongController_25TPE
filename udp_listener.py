import socket
import json
import time
import math
from pynput.keyboard import Controller, Key

# --- Keyboard Control Setup ---
keyboard = Controller()
# This variable will track the state to prevent constant key presses/releases
current_key_pressed = None

# --- Configuration ---
LISTEN_IP = "192.168.10.234"
LISTEN_PORT = 12345
TILT_THRESHOLD_DEGREES = 20.0 # How far (in degrees) you need to tilt

# --- NEW: Helper function to convert Quaternion to Euler Angles (specifically Roll) ---
# [Citation: Based on standard conversion formulas, e.g., https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles]
def quaternion_to_roll(x, y, z, w):
    """Converts a quaternion into a roll angle in degrees."""
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    return math.degrees(roll)

# --- NEW: Helper functions for stateful key presses ---
def press_key(key):
    global current_key_pressed
    if current_key_pressed != key:
        release_all_keys() # Ensure no other keys are stuck
        keyboard.press(key)
        current_key_pressed = key
        print(f"ACTION: Pressing '{key}'")

def release_all_keys():
    global current_key_pressed
    if current_key_pressed is not None:
        keyboard.release(current_key_pressed)
        print(f"ACTION: Releasing '{current_key_pressed}'")
        current_key_pressed = None

# --- Main Listener Logic ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"--- Silksong Tilt Controller v0.1 ---")
print(f"Listening on port {LISTEN_PORT}. Tilt your phone to press 'a' or 'd'.")
print("Open a text editor to see the output. Press Ctrl+C to exit.")
print("---------------------------------------")

try:
    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode()

        try:
            parsed_json = json.loads(message)

            # Extract quaternion values from the JSON
            vals = parsed_json['values']
            roll_degrees = quaternion_to_roll(vals['x'], vals['y'], vals['z'], vals['w'])

            # --- STATE LOGIC ---
            # Determine the state based on the roll angle
            if roll_degrees > TILT_THRESHOLD_DEGREES:
                state = "TILT_RIGHT"
                press_key('d')
            elif roll_degrees < -TILT_THRESHOLD_DEGREES:
                state = "TILT_LEFT"
                press_key('a')
            else:
                state = "CENTERED"
                release_all_keys()

            # Print the dashboard-style status
            print(f"\rState: {state.ljust(12)} | Roll: {roll_degrees:6.1f}°", end="")

        except (json.JSONDecodeError, KeyError):
            # If JSON is bad or keys are missing, just ignore the packet
            print("\rReceived malformed packet.                       ", end="")


except KeyboardInterrupt:
    print("\nController stopped.")
finally:
    release_all_keys() # Make sure to release keys on exit
    sock.close()