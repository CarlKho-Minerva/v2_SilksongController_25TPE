import socket
import json
import time
import math
import threading
from collections import deque
from pynput.keyboard import Controller, Key

# --- Global State ---
keyboard = Controller()
is_walking = False
last_step_time = 0
walking_thread = None
stop_walking_event = threading.Event()
# The core state for our character's direction
facing_direction = "right"
# A variable to store the phone's current orientation
last_known_orientation = {"x": 0, "y": 0, "z": 0, "w": 1}

# --- NEW: Walk Fuel System ---
walk_fuel_seconds = 0.0
last_frame_time = time.time()


# --- NEW: The core mathematical helper function ---
def rotate_vector_by_quaternion(vector, quat):
    """Rotates a 3D vector by a quaternion using standard quaternion rotation formula."""
    q_vec = [quat["x"], quat["y"], quat["z"]]
    q_scalar = quat["w"]

    # Standard formula for vector rotation by quaternion
    a = [
        2 * (q_vec[1] * vector[2] - q_vec[2] * vector[1]),
        2 * (q_vec[2] * vector[0] - q_vec[0] * vector[2]),
        2 * (q_vec[0] * vector[1] - q_vec[1] * vector[0]),
    ]

    b = [q_scalar * a[0], q_scalar * a[1], q_scalar * a[2]]

    c = [
        q_vec[1] * a[2] - q_vec[2] * a[1],
        q_vec[2] * a[0] - q_vec[0] * a[2],
        q_vec[0] * a[1] - q_vec[1] * a[0],
    ]

    rotated_vector = [
        vector[0] + b[0] + c[0],
        vector[1] + b[1] + c[1],
        vector[2] + b[2] + c[2],
    ]

    return rotated_vector


# --- Configuration Loading ---
def load_config():
    """Load configuration from config.json file"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: config.json not found! Please create the configuration file.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config.json: {e}")
        exit(1)


def get_key(key_string):
    """Converts a string from config to a pynput Key object if needed."""
    if key_string.startswith("Key."):
        key_name = key_string.split(".")[-1]
        if hasattr(Key, key_name):
            return getattr(Key, key_name)
    return key_string


# Load configuration at startup
config = load_config()

# Extract configuration values
LISTEN_IP = config["network"]["listen_ip"]
LISTEN_PORT = config["network"]["listen_port"]
FUEL_ADDED_PER_STEP = config["thresholds"]["fuel_added_per_step_sec"]
MAX_FUEL_CAPACITY = config["thresholds"]["max_fuel_sec"]
PUNCH_THRESHOLD = config["thresholds"]["punch_threshold_xy_accel"]
JUMP_THRESHOLD = config["thresholds"]["jump_threshold_z_accel"]
TURN_THRESHOLD = config["thresholds"]["turn_threshold_degrees"]
# NEW: Hardcoded stability threshold for pitch/roll stability check
STABILITY_THRESHOLD_DEGREES = 40.0

# Load key mappings from config
KEY_MAP = {
    "left": get_key(config["keyboard_mappings"]["left"]),
    "right": get_key(config["keyboard_mappings"]["right"]),
    "jump": get_key(config["keyboard_mappings"]["jump"]),
    "attack": get_key(config["keyboard_mappings"]["attack"]),
}


# --- Walker Thread ---
def walker_thread_func():
    global is_walking
    is_walking = True

    # Press left or right arrow based on facing direction
    key_to_press = KEY_MAP["right"] if facing_direction == "right" else KEY_MAP["left"]
    keyboard.press(key_to_press)

    stop_walking_event.wait()

    keyboard.release(key_to_press)
    is_walking = False


# --- Helper Functions ---
def quaternion_to_roll(qx, qy, qz, qw):
    """Convert quaternion to roll angle in degrees."""
    # Roll (x-axis rotation)
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)
    return math.degrees(roll)


def quaternion_to_euler(q):
    """Converts a quaternion dict into yaw, pitch, roll in degrees."""
    x, y, z, w = q['x'], q['y'], q['z'], q['w']

    # Roll (x-axis rotation)
    sinr_cosp = 2 * (w * x + y * z)
    cosr_cosp = 1 - 2 * (x * x + y * y)
    roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

    # Pitch (y-axis rotation)
    sinp = 2 * (w * y - z * x)
    if abs(sinp) >= 1:
        pitch = math.degrees(math.copysign(math.pi / 2, sinp))
    else:
        pitch = math.degrees(math.asin(sinp))

    # Yaw (z-axis rotation) - This is our Azimuth
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

    return yaw, pitch, roll


# --- Main Listener Logic ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((LISTEN_IP, LISTEN_PORT))

print("--- Silksong Controller v1.0 (Final) ---")
print(f"Listening on {LISTEN_IP}:{LISTEN_PORT}")
print("Official Hollow Knight/Silksong key mappings:")
print(
    f"  Movement: {config['keyboard_mappings']['left']}/{config['keyboard_mappings']['right']} (direction-based)"
)
print(
    f"  Jump: {config['keyboard_mappings']['jump']} | Attack: {config['keyboard_mappings']['attack']}"
)
print("---------------------------------------")

current_roll = 0.0
current_tilt_state = "CENTERED"
# --- NEW: Separate peak accel trackers for tuning ---
peak_z_accel = 0.0
peak_xy_accel = 0.0
peak_yaw_rate = 0.0  # NEW: for tuning the turn
# NEW: A buffer to store recent orientation history for turn detection
# We'll store ~0.5 seconds of data (at 50Hz, that's 25 samples)
# Modified to store full orientation tuples (yaw, pitch, roll)
orientation_history = deque(maxlen=25)

try:
    while True:
        data, addr = sock.recvfrom(2048)

        # --- NEW: Walk Fuel System Logic ---
        current_time = time.time()
        delta_time = current_time - last_frame_time
        last_frame_time = current_time

        # Deplete fuel over time
        walk_fuel_seconds = max(0.0, walk_fuel_seconds - delta_time)

        # Start walking if we have fuel and aren't already walking
        if walk_fuel_seconds > 0 and not is_walking and walking_thread is None:
            stop_walking_event.clear()
            walking_thread = threading.Thread(target=walker_thread_func)
            walking_thread.start()

        # Stop walking if we're out of fuel
        elif walk_fuel_seconds <= 0 and is_walking:
            stop_walking_event.set()
            if walking_thread is not None:
                walking_thread.join()
                walking_thread = None

        try:
            parsed_json = json.loads(data.decode())
            sensor_type = parsed_json.get("sensor")

            # NEW: Rotation vector now used for turn detection with stability check
            if sensor_type == "rotation_vector":
                vals = parsed_json["values"]

                # Store the orientation for world coordinate transformation
                last_known_orientation.update(vals)

                # Convert quaternion to all three Euler angles
                yaw, pitch, roll = quaternion_to_euler(vals)

                # Add current orientation to our history
                orientation_history.append({'yaw': yaw, 'pitch': pitch, 'roll': roll})

                # Check for a turn only if our history buffer is full
                if len(orientation_history) == orientation_history.maxlen:
                    oldest_orientation = orientation_history[0]
                    current_orientation = orientation_history[-1]

                    # Calculate change in all three angles
                    yaw_diff = 180 - abs(abs(current_orientation['yaw'] - oldest_orientation['yaw']) - 180)
                    pitch_diff = abs(current_orientation['pitch'] - oldest_orientation['pitch'])
                    roll_diff = abs(current_orientation['roll'] - oldest_orientation['roll'])

                    # NEW: The Stability Check
                    is_stable = (pitch_diff < STABILITY_THRESHOLD_DEGREES) and (roll_diff < STABILITY_THRESHOLD_DEGREES)

                    if yaw_diff > TURN_THRESHOLD and is_stable:
                        print("\n--- STABLE TURN DETECTED! ---")
                        if facing_direction == "right":
                            facing_direction = "left"
                        else:
                            facing_direction = "right"
                        print(f"Now facing {facing_direction.upper()}")

                         # --- NEW: Deplete walk fuel for a sharp turn ---
                        walk_fuel_seconds = 0.2
                        # Clear to prevent multiple triggers
                        orientation_history.clear()

            elif sensor_type == "step_detector":
                # --- NEW: Simple fuel addition system ---
                # Add fuel to the tank, capping at maximum capacity
                new_fuel = walk_fuel_seconds + FUEL_ADDED_PER_STEP
                walk_fuel_seconds = min(MAX_FUEL_CAPACITY, new_fuel)
                # Note: Walking start/stop logic is now handled in main loop

            # --- REFACTORED: Acceleration logic now uses world coordinates ---
            elif sensor_type == "linear_acceleration":
                vals = parsed_json["values"]
                accel_vector = [vals["x"], vals["y"], vals["z"]]

                # Perform the transformation to world coordinates
                world_accel = rotate_vector_by_quaternion(
                    accel_vector, last_known_orientation
                )
                world_x, world_y, world_z = (
                    world_accel[0],
                    world_accel[1],
                    world_accel[2],
                )

                # In standard East-North-Up frame, XY plane is horizontal, Z is up
                world_xy_magnitude = math.sqrt(world_x**2 + world_y**2)

                # Update dashboard peaks with world coordinates
                peak_z_accel = max(peak_z_accel, world_z)
                peak_xy_accel = max(peak_xy_accel, world_xy_magnitude)

                # Detection logic uses the new world values
                if world_z > JUMP_THRESHOLD:
                    print("\n--- JUMP DETECTED! ---")
                    keyboard.press(KEY_MAP["jump"])
                    time.sleep(0.1)
                    keyboard.release(KEY_MAP["jump"])
                    # Reset peaks after an action
                    peak_z_accel, peak_xy_accel = 0.0, 0.0

                # If not a jump, check for an ATTACK (strong horizontal motion)
                elif world_xy_magnitude > PUNCH_THRESHOLD:
                    print("\n--- ATTACK DETECTED! ---")
                    keyboard.press(KEY_MAP["attack"])
                    time.sleep(0.1)
                    keyboard.release(KEY_MAP["attack"])
                    # Reset peaks after an action
                    peak_z_accel, peak_xy_accel = 0.0, 0.0

            # OLD: Gyroscope-based turn detection (replaced with rotation_vector)
            # elif sensor_type == 'gyroscope':
            #     vals = parsed_json['values']
            #     yaw_rate = vals['z']
            #     # Track peak for tuning
            #     peak_yaw_rate = max(peak_yaw_rate, abs(yaw_rate))
            #
            #     if abs(yaw_rate) > TURN_THRESHOLD:
            #         # Flip the direction
            #         if facing_direction == 'right':
            #             facing_direction = 'left'
            #         else:
            #             facing_direction = 'right'
            #         print(f"\n--- TURN DETECTED! Now facing "
            #               f"{facing_direction.upper()} ---")
            #         # Add a small cooldown to prevent multiple flips
            #         time.sleep(0.5)
            #         peak_yaw_rate = 0.0  # Reset after action

            walk_status = "WALKING" if is_walking else "IDLE"

            # Create walk fuel bar visualization
            fuel_percentage = walk_fuel_seconds / MAX_FUEL_CAPACITY
            fuel_bar_length = 8
            filled_bars = int(fuel_percentage * fuel_bar_length)
            empty_bars = fuel_bar_length - filled_bars
            fuel_bar = "[" + "#" * filled_bars + "-" * empty_bars + "]"

            # Updated dashboard to show world coordinates and walk fuel
            dashboard_string = (
                f"\rFacing: {facing_direction.upper().ljust(7)} | "
                f"Walk: {walk_status.ljust(7)} | "
                f"Fuel: {fuel_bar} {walk_fuel_seconds:.1f}s | "
                f"World Z-A:{peak_z_accel:4.1f} | "
                f"World XY-A:{peak_xy_accel:4.1f} | "
                f"Yaw:{peak_yaw_rate:3.1f}"
            )
            print(dashboard_string, end="")

        except (json.JSONDecodeError, KeyError):
            # Temporarily print errors to see if we have issues
            # print(f"Error processing packet: {e}")
            pass

except KeyboardInterrupt:
    print("\nController stopped.")
finally:
    if is_walking and walking_thread is not None:
        stop_walking_event.set()
        walking_thread.join()
    sock.close()
