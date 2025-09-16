import socket
import json
import time
import math
import threading
from pynput.keyboard import Controller

# --- Keyboard Control Setup & State ---
keyboard = Controller()
current_tilt_key = None
is_walking = False
last_step_time = 0
walking_thread = None
stop_walking_event = threading.Event()

# --- Configuration ---
LISTEN_IP = "192.168.10.234"
LISTEN_PORT = 12345
TILT_THRESHOLD_DEGREES = 20.0
WALK_TIMEOUT = 1.5
STEP_DEBOUNCE = 0.4
# --- NEW: Threshold for punch detection (in m/s^2). A brisk shake is ~15-20.
PUNCH_THRESHOLD = 18.0


# --- Walker Thread (No changes here) ---
def walker_thread_func():
    global is_walking
    is_walking = True
    keyboard.press("w")
    stop_walking_event.wait()
    keyboard.release("w")
    is_walking = False


# --- Helper Functions (No changes here) ---
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

print(f"--- Silksong Controller v0.4 ---")
print(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
print("---------------------------------------")

current_roll = 0.0
current_tilt_state = "CENTERED"
peak_accel = 0.0

try:
    while True:
        data, addr = sock.recvfrom(2048)

        if is_walking and time.time() - last_step_time > WALK_TIMEOUT:
            stop_walking_event.set()
            walking_thread.join()
            walking_thread = None

        try:
            # CORRECTED: Using data.decode() directly, as you pointed out.
            parsed_json = json.loads(data.decode())
            sensor_type = parsed_json.get("sensor")

            if sensor_type == "rotation_vector":
                vals = parsed_json["values"]
                current_roll = quaternion_to_roll(
                    vals["x"], vals["y"], vals["z"], vals["w"]
                )
                # Tilt logic remains the same...
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
                if now - last_step_time > STEP_DEBOUNCE:
                    last_step_time = now
                    if not is_walking and walking_thread is None:
                        stop_walking_event.clear()
                        walking_thread = threading.Thread(target=walker_thread_func)
                        walking_thread.start()

            # --- NEW: Punch detection logic ---
            elif sensor_type == "linear_acceleration":
                vals = parsed_json["values"]
                # Calculate the magnitude of the acceleration
                accel_magnitude = math.sqrt(
                    vals["x"] ** 2 + vals["y"] ** 2 + vals["z"] ** 2
                )
                peak_accel = max(peak_accel, accel_magnitude)  # Keep track of peak

                if accel_magnitude > PUNCH_THRESHOLD:
                    print("\n--- PUNCH DETECTED! ---")
                    keyboard.press("j")
                    time.sleep(0.1)
                    keyboard.release("j")
                    peak_accel = 0.0  # Reset peak after a punch

            walk_status = "WALKING" if is_walking else "IDLE"
            dashboard_string = f"\rTilt: {current_tilt_state.ljust(12)} | Walk: {walk_status.ljust(10)} | Accel: {peak_accel:4.1f} m/s^2"
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
