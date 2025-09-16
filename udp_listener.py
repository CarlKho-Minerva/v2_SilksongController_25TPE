import socket
import json
import time
import math
from pynput.keyboard import Controller, Key

# --- Keyboard Control Setup ---
keyboard = Controller()
current_key_pressed = None

# --- Configuration ---
# NOTE: Using your specific IP now to bind the listener
LISTEN_IP = "192.168.10.234"
LISTEN_PORT = 12345
TILT_THRESHOLD_DEGREES = 20.0


# --- Helper Functions (No changes here) ---
def quaternion_to_roll(x, y, z, w):
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    return math.degrees(roll)


def press_key(key):
    global current_key_pressed
    if current_key_pressed != key:
        release_all_keys()
        keyboard.press(key)
        current_key_pressed = key


def release_all_keys():
    global current_key_pressed
    if current_key_pressed is not None:
        keyboard.release(current_key_pressed)
        current_key_pressed = None


# --- Main Listener Logic ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"--- Silksong Controller v0.2 ---")
print(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
print("Open a text editor to see the output. Press Ctrl+C to exit.")
print("---------------------------------------")

# --- NEW: Variables for dashboard ---
last_event_type = "None"
current_roll = 0.0
current_state = "CENTERED"

try:
    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode()

        try:
            parsed_json = json.loads(message)
            sensor_type = parsed_json.get("sensor")

            # --- ROUTING LOGIC based on sensor type ---
            if sensor_type == "rotation_vector":
                last_event_type = "ROTATION"
                vals = parsed_json["values"]
                current_roll = quaternion_to_roll(
                    vals["x"], vals["y"], vals["z"], vals["w"]
                )

                if current_roll > TILT_THRESHOLD_DEGREES:
                    current_state = "TILT_RIGHT"
                    press_key("d")
                elif current_roll < -TILT_THRESHOLD_DEGREES:
                    current_state = "TILT_LEFT"
                    press_key("a")
                else:
                    current_state = "CENTERED"
                    release_all_keys()

            elif sensor_type == "step_detector":
                last_event_type = "STEP ***"
                # For this step, we do a simple, short, blocking key press.
                # This is temporary to prove the event is received.
                keyboard.press("w")
                time.sleep(0.1)
                keyboard.release("w")

            # Update dashboard display
            print(
                f"\rState: {current_state.ljust(12)} | Roll: {current_roll:6.1f}° | Last Event: {last_event_type.ljust(12)}",
                end="",
            )

            # Reset the "STEP ***" indicator after printing it once
            if last_event_type == "STEP ***":
                last_event_type = "STEP"

        except (json.JSONDecodeError, KeyError):
            print("\rReceived malformed packet.                       ", end="")

except KeyboardInterrupt:
    print("\nController stopped.")
finally:
    release_all_keys()
    sock.close()
