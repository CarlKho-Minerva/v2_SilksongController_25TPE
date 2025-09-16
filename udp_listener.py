import socket
import json
import time
import math
import threading
from pynput.keyboard import Controller, Key

# --- Global State ---
keyboard = Controller()
current_tilt_key = None
is_walking = False
last_step_time = 0
walking_thread = None
stop_walking_event = threading.Event()
# NEW: The core state for our character's direction
facing_direction = 'right'

# --- Configuration Loading ---
def load_config():
    """Load configuration from config.json file"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found! Please create the configuration file.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config.json: {e}")
        exit(1)

# Load configuration at startup
config = load_config()

# Extract configuration values
LISTEN_IP = config['network']['listen_ip']
LISTEN_PORT = config['network']['listen_port']
TILT_THRESHOLD_DEGREES = config['thresholds']['tilt_threshold_degrees']
WALK_TIMEOUT = config['thresholds']['walk_timeout_sec']
STEP_DEBOUNCE = config['thresholds']['step_debounce_sec']
PUNCH_THRESHOLD = config['thresholds']['punch_threshold_xy_accel']
JUMP_THRESHOLD = config['thresholds']['jump_threshold_z_accel']
TURN_THRESHOLD = config['thresholds']['turn_threshold_yaw_rate']

# Extract keyboard mappings
KEY_WALK = config['keyboard_mappings']['walk_forward']
KEY_TILT_LEFT = config['keyboard_mappings']['tilt_left']
KEY_TILT_RIGHT = config['keyboard_mappings']['tilt_right']
KEY_JUMP = config['keyboard_mappings']['jump']
KEY_PUNCH = config['keyboard_mappings']['punch']
KEY_TURN = config['keyboard_mappings']['turn']

# Helper function to get the correct key object
def get_key(key_name):
    """Convert key name to appropriate key object for pynput"""
    if key_name == "space":
        return Key.space
    elif key_name == "enter":
        return Key.enter
    elif key_name == "tab":
        return Key.tab
    elif key_name == "shift":
        return Key.shift
    elif key_name == "ctrl":
        return Key.ctrl
    elif key_name == "alt":
        return Key.alt
    else:
        return key_name  # Regular character keys


# --- Walker Thread ---
def walker_thread_func():
    global is_walking
    is_walking = True

    # Press the key corresponding to the current facing direction
    if facing_direction == 'right':
        key_to_press = get_key(KEY_TILT_RIGHT)
    else:
        key_to_press = get_key(KEY_TILT_LEFT)
    keyboard.press(key_to_press)

    stop_walking_event.wait()

    keyboard.release(key_to_press)
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

print("--- Silksong Controller v0.7 (Configurable) ---")
print(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
print("Keyboard mappings loaded from config.json:")
print(f"  Walk: {KEY_WALK} | Tilt L/R: {KEY_TILT_LEFT}/{KEY_TILT_RIGHT}")
print(f"  Jump: {KEY_JUMP} | Punch: {KEY_PUNCH} | Turn: {KEY_TURN}")
print("---------------------------------------")

current_roll = 0.0
current_tilt_state = "CENTERED"
# --- NEW: Separate peak accel trackers for tuning ---
peak_z_accel = 0.0
peak_xy_accel = 0.0
peak_yaw_rate = 0.0  # NEW: for tuning the turn

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

            # TEMPORARILY DISABLED: Tilt-to-strafe logic is replaced by face-and-walk
            # if sensor_type == "rotation_vector":
            #     vals = parsed_json["values"]
            #     current_roll = quaternion_to_roll(
            #         vals["x"], vals["y"], vals["z"], vals["w"]
            #     )
            #     # Tilt logic with configurable keys
            #     if current_roll > TILT_THRESHOLD_DEGREES:
            #         current_tilt_state = "TILT_RIGHT"
            #         press_tilt_key(get_key(KEY_TILT_RIGHT))
            #     elif current_roll < -TILT_THRESHOLD_DEGREES:
            #         current_tilt_state = "TILT_LEFT"
            #         press_tilt_key(get_key(KEY_TILT_LEFT))
            #     else:
            #         current_tilt_state = "CENTERED"
            #         release_tilt_key()

            if sensor_type == "step_detector":
                now = time.time()
                if now - last_step_time > STEP_DEBOUNCE:
                    last_step_time = now
                    if not is_walking and walking_thread is None:
                        stop_walking_event.clear()
                        walking_thread = threading.Thread(target=walker_thread_func)
                        walking_thread.start()

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
                    keyboard.press(get_key(KEY_JUMP))
                    time.sleep(0.1)
                    keyboard.release(get_key(KEY_JUMP))
                    # Reset peaks after an action
                    peak_z_accel, peak_xy_accel = 0.0, 0.0

                # If not a jump, check for a PUNCH (strong horizontal motion)
                elif xy_magnitude > PUNCH_THRESHOLD:
                    print("\n--- PUNCH DETECTED! ---")
                    keyboard.press(get_key(KEY_PUNCH))
                    time.sleep(0.1)
                    keyboard.release(get_key(KEY_PUNCH))
                    # Reset peaks after an action
                    peak_z_accel, peak_xy_accel = 0.0, 0.0

            # --- MODIFIED: Turn detection logic now flips facing_direction ---
            elif sensor_type == 'gyroscope':
                vals = parsed_json['values']
                yaw_rate = vals['z']
                # Track peak for tuning
                peak_yaw_rate = max(peak_yaw_rate, abs(yaw_rate))

                if abs(yaw_rate) > TURN_THRESHOLD:
                    # Flip the direction
                    if facing_direction == 'right':
                        facing_direction = 'left'
                    else:
                        facing_direction = 'right'
                    print(f"\n--- TURN DETECTED! Now facing "
                          f"{facing_direction.upper()} ---")
                    # Add a small cooldown to prevent multiple flips
                    time.sleep(0.5)
                    peak_yaw_rate = 0.0  # Reset after action

            walk_status = "WALKING" if is_walking else "IDLE"
            # Updated dashboard to show facing direction instead of tilt
            dashboard_string = (
                f"\rFacing: {facing_direction.upper().ljust(7)} | "
                f"Walk: {walk_status.ljust(10)} | "
                f"Z-A:{peak_z_accel:4.1f} | "
                f"XY-A:{peak_xy_accel:4.1f} | "
                f"Yaw:{peak_yaw_rate:3.1f}"
            )
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
