import socket
import json
import time
import math
import statistics  # NEW: For calculating mean and standard deviation
import sys  # NEW: For command line arguments


def load_config():
    """Loads the configuration from the config.json file."""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found. Please create one.")
        exit()


def save_config(config_data):
    """Saves the updated configuration to the config.json file."""
    with open("config.json", "w") as f:
        json.dump(config_data, f, indent=4)
    print("\nConfiguration saved successfully!")


def get_peak_xy_accel(sock, duration_sec):
    """Listens for a set duration and returns the highest XY acceleration magnitude."""
    peak_accel = 0.0
    start_time = time.time()

    while time.time() - start_time < duration_sec:
        try:
            data, addr = sock.recvfrom(2048)
            parsed_json = json.loads(data.decode())

            if parsed_json.get("sensor") == "linear_acceleration":
                vals = parsed_json["values"]
                x, y = vals["x"], vals["y"]
                xy_magnitude = math.sqrt(x**2 + y**2)
                if xy_magnitude > peak_accel:
                    peak_accel = xy_magnitude
        except BlockingIOError:
            # No data available, just continue
            time.sleep(0.01)
        except (json.JSONDecodeError, KeyError):
            # Malformed packet, ignore
            pass

    return peak_accel


def get_peak_z_accel(sock, duration_sec):
    """Listens for a set duration and returns the highest positive Z accel."""
    peak_accel = 0.0
    start_time = time.time()

    while time.time() - start_time < duration_sec:
        try:
            data, _ = sock.recvfrom(2048)
            parsed_json = json.loads(data.decode())

            if parsed_json.get("sensor") == "linear_acceleration":
                vals = parsed_json["values"]
                z_accel = vals["z"]
                # We only care about positive Z-axis acceleration for jumps
                if z_accel > peak_accel:
                    peak_accel = z_accel
        except BlockingIOError:
            # No data available, just continue
            time.sleep(0.01)
        except (json.JSONDecodeError, KeyError):
            # Malformed packet, ignore
            pass

    return peak_accel


def get_stable_azimuth(sock):
    """Waits for a rotation_vector packet and returns the azimuth."""
    while True:
        try:
            data, _ = sock.recvfrom(2048)
            parsed_json = json.loads(data.decode())
            if parsed_json.get('sensor') == 'rotation_vector':
                vals = parsed_json['values']
                # Convert quaternion to azimuth (yaw)
                # Yaw (z-axis rotation)
                siny_cosp = 2 * (vals['w'] * vals['z'] + vals['x'] * vals['y'])
                cosy_cosp = 1 - 2 * (vals['y']**2 + vals['z']**2)
                yaw = math.atan2(siny_cosp, cosy_cosp)
                return math.degrees(yaw)
        except (BlockingIOError, json.JSONDecodeError, KeyError):
            pass  # Wait for a valid packet


def calibrate_punch(config, sock):
    """Guides the user through calibrating the punch gesture."""
    print("\n--- Calibrating PUNCH ---")
    print("You will be asked to perform 3 punches.")
    print("Please perform a sharp, forward shake or punch motion each time.")

    peak_readings = []
    num_samples = 3

    for i in range(num_samples):
        input(
            f"\nPress [Enter] when you are ready for Punch {i + 1} of {num_samples}..."
        )
        print("Get ready...")
        time.sleep(1)
        print("GO!")

        peak = get_peak_xy_accel(sock, 2.0)  # Record for 2 seconds

        if peak < 5.0:  # A basic sanity check
            print(
                f"Recorded a peak of {peak:.2f} m/s². That seems low. Please try again with a sharper motion."
            )
            continue  # Let the user redo this sample

        print(f"  > Recorded a peak of {peak:.2f} m/s². Good!")
        peak_readings.append(peak)

    # --- Analyze the results ---
    if len(peak_readings) < 2:
        print("\nNot enough valid samples to calibrate. Please try again.")
        return

    avg_peak = statistics.mean(peak_readings)
    std_dev = statistics.stdev(peak_readings)

    # Calculate the new threshold
    # We set it below the average to make it responsive
    new_threshold = avg_peak - (1.0 * std_dev)
    # Ensure the threshold isn't ridiculously low
    new_threshold = max(new_threshold, 8.0)

    print("\n--- Analysis Complete ---")
    print(f"Average Peak Punch: {avg_peak:.2f} m/s²")
    prev_threshold = config['thresholds']['punch_threshold_xy_accel']
    print(f"Previous Threshold: {prev_threshold}")
    print(f"New Recommended Threshold: {new_threshold:.2f}")

    config["thresholds"]["punch_threshold_xy_accel"] = new_threshold


def calibrate_jump(config, sock):
    """Guides the user through calibrating the jump gesture."""
    print("\n--- Calibrating JUMP ---")
    print("You will be asked to perform 3 jumps.")
    print("Please perform a sharp, upward 'hop' motion with the phone "
          "each time.")

    peak_readings = []
    num_samples = 3

    for i in range(num_samples):
        prompt = (f"\nPress [Enter] when you are ready for Jump "
                  f"{i + 1} of {num_samples}...")
        input(prompt)
        print("Get ready...")
        time.sleep(1)
        print("GO!")

        peak = get_peak_z_accel(sock, 2.0)

        if peak < 5.0:
            print(f"  > Recorded a peak of {peak:.2f} m/s². "
                  f"That seems low. Please try again with a sharper motion.")
            continue

        print(f"  > Recorded a peak of {peak:.2f} m/s². Good!")
        peak_readings.append(peak)

    # --- Analyze the results ---
    if len(peak_readings) < 2:
        print("\nNot enough valid samples to calibrate jump. "
              "Please try again.")
        return

    avg_peak = statistics.mean(peak_readings)
    std_dev = statistics.stdev(peak_readings)

    # Calculate the new threshold
    # We set it below the average to make it responsive
    new_threshold = avg_peak - (1.5 * std_dev)
    # Ensure the threshold isn't ridiculously low
    new_threshold = max(new_threshold, 8.0)

    print("\n--- Jump Analysis Complete ---")
    print(f"Average Peak Jump: {avg_peak:.2f} m/s²")
    prev_threshold = config['thresholds']['jump_threshold_z_accel']
    print(f"Previous Threshold: {prev_threshold}")
    print(f"New Recommended Threshold: {new_threshold:.2f}")

    config["thresholds"]["jump_threshold_z_accel"] = new_threshold


def calibrate_turn(config, sock):
    """Guides user through calibrating turn gesture based on azimuth change."""
    print("\n--- Calibrating TURN ---")
    print("This will measure how you perform a full 180-degree body turn.")

    turn_magnitudes = []
    num_samples = 3

    for i in range(num_samples):
        print(f"\n--- Turn Sample {i + 1} of {num_samples} ---")
        input("Face your starting direction and press [Enter]...")
        print("  > Reading starting direction...")
        start_azimuth = get_stable_azimuth(sock)
        print(f"  > Start direction captured ({start_azimuth:.1f}°).")

        input("Now, turn around completely (180°) and press [Enter]...")
        print("  > Reading ending direction...")
        end_azimuth = get_stable_azimuth(sock)
        print(f"  > End direction captured ({end_azimuth:.1f}°).")

        # Calculate the shortest angle difference
        angle_diff = abs(start_azimuth - end_azimuth)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        print(f"  > Calculated turn magnitude: {angle_diff:.1f}°")
        turn_magnitudes.append(angle_diff)

    if not turn_magnitudes:
        print("\nCould not capture any valid turns. Aborting.")
        return

    avg_turn = statistics.mean(turn_magnitudes)
    # The threshold is a percentage of their average 180-degree turn
    new_threshold = avg_turn * 0.75  # 75% of their average turn

    print("\n--- Turn Analysis Complete ---")
    print(f"Average Measured Turn: {avg_turn:.1f}°")
    print(f"New Recommended Turn Threshold: {new_threshold:.1f}°")

    # NEW/RENAMED config key for clarity
    config['thresholds']['turn_threshold_degrees'] = new_threshold
    # Remove the old, now unused key if it exists
    config['thresholds'].pop('turn_threshold_yaw_rate', None)


def calibrate_walking(config, sock):
    """Guides user through rhythm test to calibrate walking parameters."""
    print("\n--- Calibrating WALKING RHYTHM ---")
    input("Press [Enter] to begin a 10-second walking test...")

    print("Get ready to walk in place at a comfortable, natural pace.")
    time.sleep(1)
    print("GO!")

    step_timestamps = []
    end_time = time.time() + 10.0

    while time.time() < end_time:
        remaining = end_time - time.time()
        print(f"\r  > Recording... {remaining:.1f} seconds remaining.", end="")
        try:
            data, _ = sock.recvfrom(2048)
            parsed_json = json.loads(data.decode())
            if parsed_json.get('sensor') == 'step_detector':
                step_timestamps.append(time.time())
        except (BlockingIOError, json.JSONDecodeError, KeyError):
            pass

    print("\n  > Recording complete!")

    if len(step_timestamps) < 3:
        print("Not enough steps detected to calibrate. Please try again.")
        return

    # Calculate intervals between steps
    intervals = [step_timestamps[i] - step_timestamps[i-1]
                 for i in range(1, len(step_timestamps))]

    avg_interval = statistics.mean(intervals)

    # New debounce is a fraction of their average step time
    new_debounce = avg_interval * 0.75
    # New timeout is a multiple of their average step time
    new_timeout = avg_interval * 2.5

    print("\n--- Walking Analysis Complete ---")
    print(f"Detected {len(step_timestamps)} steps with an average time of "
          f"{avg_interval:.2f}s between steps.")

    prev_debounce = config['thresholds']['step_debounce_sec']
    prev_timeout = config['thresholds']['walk_timeout_sec']
    print(f"Previous Debounce: {prev_debounce:.2f}s | "
          f"New: {new_debounce:.2f}s")
    print(f"Previous Timeout:  {prev_timeout:.2f}s | "
          f"New: {new_timeout:.2f}s")

    config['thresholds']['step_debounce_sec'] = new_debounce
    config['thresholds']['walk_timeout_sec'] = new_timeout


def main():
    """Main function to run the calibrator wizard."""
    config = load_config()

    # Set up the socket once for all calibrations
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config['network']['listen_ip'],
               config['network']['listen_port']))
    sock.setblocking(False)

    # Check for command line arguments
    if len(sys.argv) > 1:
        gesture = sys.argv[1].lower()
        print(f"Calibrating specific gesture: {gesture}")

        if gesture == 'punch':
            calibrate_punch(config, sock)
        elif gesture == 'jump':
            calibrate_jump(config, sock)
        elif gesture == 'turn':
            calibrate_turn(config, sock)
        elif gesture == 'walking':
            calibrate_walking(config, sock)
        else:
            print(f"Unknown gesture: {gesture}")
            print("Valid options: punch, jump, turn, walking")
            sock.close()
            return
    else:
        print("Welcome to the Silksong Controller Calibrator.")
        print("Running full calibration suite...")
        # Run the full suite of calibrations sequentially
        calibrate_punch(config, sock)
        calibrate_jump(config, sock)
        calibrate_turn(config, sock)
        calibrate_walking(config, sock)

    sock.close()  # Clean up the socket
    save_config(config)
    print("Calibration complete! Updated config.json saved.")


if __name__ == "__main__":
    main()
