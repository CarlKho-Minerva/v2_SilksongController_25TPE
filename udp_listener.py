import socket
import json
import time
import math
import threading  # NEW: Import the threading library
from pynput.keyboard import Controller

# --- Keyboard Control Setup ---
keyboard = Controller()
# State variables for tilt control
current_tilt_key = None

# --- NEW: State variables for walking control ---
is_walking = False
last_step_time = 0
walking_thread = None
stop_walking_event = threading.Event()

# --- Configuration ---
LISTEN_IP = "192.168.10.234"
LISTEN_PORT = 12345
TILT_THRESHOLD_DEGREES = 20.0
WALK_TIMEOUT = 1.5  # Seconds of no steps before stopping
STEP_DEBOUNCE = 0.4  # Seconds to ignore new steps after one is registered


# --- NEW: The function that will run in a separate thread to handle walking ---
def walker_thread_func():
    """This function presses and holds 'w' until an event is set."""
    global is_walking
    is_walking = True
    keyboard.press("w")
    print("\nACTION: Started Walking (Holding 'w')")

    # This will wait until the main thread calls stop_walking_event.set()
    stop_walking_event.wait()

    keyboard.release("w")
    print("\nACTION: Stopped Walking (Released 'w')")
    is_walking = False


# --- Helper function for tilt control (minor change to variable name) ---
def press_tilt_key(key):
    global current_tilt_key
    if current_tilt_key != key:
        release_tilt_key()
        keyboard.press(key)
        current_tilt_key = key


def release_tilt_key():
    global current_tilt_key
    if current_tilt_key is not None:
        keyboard.release(current_tilt_key)
        current_tilt_key = None


def quaternion_to_roll(x, y, z, w):
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    return math.degrees(roll)


# --- Main Listener Logic ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print(f"--- Silksong Controller v0.3 ---")
print(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
print("---------------------------------------")

current_roll = 0.0
current_tilt_state = "CENTERED"

try:
    while True:
        data, addr = sock.recvfrom(2048)

        # --- NEW: Check for walk timeout in the main loop ---
        if is_walking and time.time() - last_step_time > WALK_TIMEOUT:
            stop_walking_event.set()  # Signal the thread to stop
            walking_thread.join()  # Wait for the thread to finish
            walking_thread = None

        try:
            parsed_json = json.loads(data.decode())
            sensor_type = parsed_json.get("sensor")

            if sensor_type == "rotation_vector":
                vals = parsed_json["values"]
                current_roll = quaternion_to_roll(
                    vals["x"], vals["y"], vals["z"], vals["w"]
                )

                if current_roll > TILT_THRESHOLD_DEGREES:
                    current_tilt_state = "TILT_RIGHT"
                    press_tilt_key("d")
                elif current_roll < -TILT_THRESHOLD_DEGREES:
                    current_tilt_state = "TILT_LEFT"
                    press_tilt_key("a")
                else:
                    current_tilt_state = "CENTERED"
                    release_tilt_key()

            elif sensor_type == "step_detector":
                now = time.time()
                # --- NEW: Debounce logic ---
                if now - last_step_time > STEP_DEBOUNCE:
                    last_step_time = now
                    # If not already walking, start a new walking thread
                    if not is_walking and walking_thread is None:
                        stop_walking_event.clear()  # Reset the event for the new thread
                        walking_thread = threading.Thread(target=walker_thread_func)
                        walking_thread.start()

            # --- NEW: Updated Dashboard ---
            walk_status = "WALKING" if is_walking else "IDLE"
            dashboard_string = f"\rTilt: {current_tilt_state.ljust(12)} | Walk: {walk_status.ljust(10)} | Roll: {current_roll:6.1f}°"
            print(dashboard_string, end="")

        except (json.JSONDecodeError, KeyError):
            pass

except KeyboardInterrupt:
    print("\nController stopped.")
finally:
    if is_walking:
        stop_walking_event.set()
        walking_thread.join()
    release_tilt_key()
    sock.close()
