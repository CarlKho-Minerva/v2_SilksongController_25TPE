import socket
import json
import time
import math
import threading
from pynput.keyboard import Controller, Key

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
# --- NEW: Separate thresholds for Jump (vertical) and Punch (horizontal) ---
PUNCH_THRESHOLD = 16.0  # m/s^2 on the X/Y plane
JUMP_THRESHOLD = 15.0  # m/s^2 on the Z axis


# --- Walker Thread (No changes here) ---
def walker_thread_func():
    global is_walking
    is_walking = True
    keyboard.press("w")
    stop_walking_event.wait()
    keyboard.release("w")
    is_walking = False


# --- Helper Functions (No changes here) ---
# ... (press_tilt_key, release_tilt_key, quaternion_to_roll) ...
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

print(f"--- Silksong Controller v0.5 ---")
print(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
print("---------------------------------------")

current_roll = 0.0
current_tilt_state = "CENTERED"
# --- NEW: Separate peak accel trackers for tuning ---
peak_z_accel = 0.0
peak_xy_accel = 0.0

try:
    while True:
        data, addr = sock.recvfrom(2048)

        if is_walking and time.time() - last_step_time > WALK_TIMEOUT:
            stop_walking_event.set()
            walking_thread.join()
            walking_thread = None

        try:
            parsed_json = json.loads(data.decode())
            sensor_type = parsed_json.get("sensor")

            if sensor_type == "rotation_vector":
                # ... Tilt logic is unchanged ...
                pass

            elif sensor_type == "step_detector":
                # ... Step logic is unchanged ...
                pass

            # --- REFACTORED: Acceleration logic now handles two actions ---
            elif sensor_type == "linear_acceleration":
                vals = parsed_json["values"]
                x, y, z = vals["x"], vals["y"], vals["z"]

                xy_magnitude = math.sqrt(x**2 + y**2)

                peak_z_accel = max(peak_z_accel, z)
                peak_xy_accel = max(peak_xy_accel, xy_magnitude)

                # Check for JUMP first (strong upward motion)
                if z > JUMP_THRESHOLD:
                    print("\n--- JUMP DETECTED! ---")
                    keyboard.press(Key.space)
                    time.sleep(0.1)
                    keyboard.release(Key.space)
                    # Reset peaks after an action
                    peak_z_accel, peak_xy_accel = 0.0, 0.0

                # If not a jump, check for a PUNCH (strong horizontal motion)
                elif xy_magnitude > PUNCH_THRESHOLD:
                    print("\n--- PUNCH DETECTED! ---")
                    keyboard.press("j")
                    time.sleep(0.1)
                    keyboard.release("j")
                    # Reset peaks after an action
                    peak_z_accel, peak_xy_accel = 0.0, 0.0

            walk_status = "WALKING" if is_walking else "IDLE"
            dashboard_string = f"\rT:{current_tilt_state[0]} | W:{walk_status[0]} | Z-Accel:{peak_z_accel:4.1f} | XY-Accel:{peak_xy_accel:4.1f}"
            print(dashboard_string, end="")

        except (json.JSONDecodeError, KeyError) as e:
            # Temporarily print errors to see if we have issues
            # print(f"Error processing packet: {e}")
            pass

except KeyboardInterrupt:
    print("\nController stopped.")
finally:
    if is_walking:
        stop_walking_event.set()
        walking_thread.join()
    release_tilt_key()
    sock.close()
