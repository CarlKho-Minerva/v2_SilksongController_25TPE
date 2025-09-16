import socket
import json
import time
import math
import statistics  # For calculating mean and standard deviation
import sys  # For command line arguments


# --- NEW: A helper function to display instructions clearly ---
def show_instructions(message):
    """Prints a message and waits for the user to acknowledge."""
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50)
    input("Press [Enter] when you are ready to continue...")


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
    timeout = 10.0  # 10 second timeout
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            data, _ = sock.recvfrom(2048)
            parsed_json = json.loads(data.decode())
            if parsed_json.get("sensor") == "rotation_vector":
                vals = parsed_json["values"]
                # Convert quaternion to azimuth (yaw)
                # Yaw (z-axis rotation)
                siny_cosp = 2 * (vals["w"] * vals["z"] + vals["x"] * vals["y"])
                cosy_cosp = 1 - 2 * (vals["y"] ** 2 + vals["z"] ** 2)
                yaw = math.atan2(siny_cosp, cosy_cosp)
                return math.degrees(yaw)
        except (BlockingIOError, json.JSONDecodeError, KeyError):
            time.sleep(0.01)  # Small delay to prevent busy waiting

    # If we get here, we timed out
    print("\n  ERROR: No rotation_vector data received!")
    print("  Make sure your Android app is sending rotation_vector sensor data.")
    return None


def calibrate_punch(config, sock):
    """Guides the user through calibrating the punch gesture."""

    instruction_message = (
        "--- Calibrating PUNCH ---\n\n"
        "First, adopt your COMBAT STANCE.\n"
        "Most users hold the phone like a handle or sword grip, with the\n"
        "screen facing sideways (e.g., to your left if right-handed).\n\n"
        "We will record 3 sharp, forward PUNCH motions from this stance."
    )
    show_instructions(instruction_message)

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
    prev_threshold = config["thresholds"]["punch_threshold_xy_accel"]
    print(f"Previous Threshold: {prev_threshold}")
    print(f"New Recommended Threshold: {new_threshold:.2f}")

    config["thresholds"]["punch_threshold_xy_accel"] = new_threshold


def calibrate_jump(config, sock):
    """Guides the user through calibrating the jump gesture."""

    instruction_message = (
        "--- Calibrating JUMP ---\n\n"
        "For this, adopt a NEUTRAL STANCE.\n"
        "Hold the phone flat like a plate, with the screen facing UP.\n\n"
        "We will record 3 sharp, upward HOP motions from this stance."
    )
    show_instructions(instruction_message)

    peak_readings = []
    num_samples = 3

    for i in range(num_samples):
        prompt = (
            f"\nPress [Enter] when you are ready for Jump "
            f"{i + 1} of {num_samples}..."
        )
        input(prompt)
        print("Get ready...")
        time.sleep(1)
        print("GO!")

        peak = get_peak_z_accel(sock, 2.0)

        if peak < 5.0:
            print(
                f"  > Recorded a peak of {peak:.2f} m/s². "
                f"That seems low. Please try again with a sharper motion."
            )
            continue

        print(f"  > Recorded a peak of {peak:.2f} m/s². Good!")
        peak_readings.append(peak)

    # --- Analyze the results ---
    if len(peak_readings) < 2:
        print("\nNot enough valid samples to calibrate jump. " "Please try again.")
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
    prev_threshold = config["thresholds"]["jump_threshold_z_accel"]
    print(f"Previous Threshold: {prev_threshold}")
    print(f"New Recommended Threshold: {new_threshold:.2f}")

    config["thresholds"]["jump_threshold_z_accel"] = new_threshold


# --- REWRITTEN: The entire turn calibration function ---
def calibrate_turn(config, sock):
    """Guides the user through calibrating the turn gesture by measuring max angular change."""
    instruction_message = (
        "--- Calibrating TURN ---\n\n"
        "This will measure a full 180-degree body turn.\n\n"
        "1. Adopt your TRAVEL STANCE (how you hold the phone when walking).\n"
        "2. When I say 'GO!', you will have 3 seconds to turn around completely.\n"
        "3. You can turn either left or right, whichever is comfortable."
    )
    show_instructions(instruction_message)

    turn_magnitudes = []
    num_samples = 3

    for i in range(num_samples):
        input(f"\nPress [Enter] when ready for Turn Sample {i + 1} of {num_samples}...")

        # Get a stable starting azimuth before the user moves
        print("  > Get ready... Don't move.")
        time.sleep(1)
        start_azimuth = None
        while start_azimuth is None:
            try:
                data, _ = sock.recvfrom(2048)
                parsed = json.loads(data.decode())
                if parsed.get("sensor") == "rotation_vector":
                    vals = parsed["values"]
                    siny_cosp = 2 * (vals["w"] * vals["z"] + vals["x"] * vals["y"])
                    cosy_cosp = 1 - 2 * (vals["y"] ** 2 + vals["z"] ** 2)
                    start_azimuth = math.degrees(math.atan2(siny_cosp, cosy_cosp))
            except (BlockingIOError, json.JSONDecodeError, KeyError):
                pass
        print(f"  > Starting direction locked ({start_azimuth:.1f}°). GO!")

        # --- Time-based recording window ---
        max_turn_diff = 0.0
        end_time = time.time() + 3.0  # 3 second window to perform the turn

        while time.time() < end_time:
            try:
                data, _ = sock.recvfrom(2048)
                parsed = json.loads(data.decode())
                if parsed.get("sensor") == "rotation_vector":
                    vals = parsed["values"]
                    siny_cosp = 2 * (vals["w"] * vals["z"] + vals["x"] * vals["y"])
                    cosy_cosp = 1 - 2 * (vals["y"] ** 2 + vals["z"] ** 2)
                    current_azimuth = math.degrees(math.atan2(siny_cosp, cosy_cosp))

                    # Calculate shortest angle difference from the start
                    diff = 180 - abs(abs(start_azimuth - current_azimuth) - 180)
                    max_turn_diff = max(max_turn_diff, diff)

            except (BlockingIOError, json.JSONDecodeError, KeyError):
                pass

        print(f"  > Recorded a maximum turn of {max_turn_diff:.1f}°. Good!")
        turn_magnitudes.append(max_turn_diff)

    if len(turn_magnitudes) < 2:
        print("\nNot enough valid samples. Aborting turn calibration.")
        return

    avg_turn = statistics.mean(turn_magnitudes)
    new_threshold = max(
        avg_turn * 0.75, 90.0
    )  # Set threshold to 75% of their turn, with a minimum of 90 degrees

    print("\n--- Turn Analysis Complete ---")
    print(f"Average Measured Turn: {avg_turn:.1f}°")
    print(f"New Recommended Turn Threshold: {new_threshold:.1f}°")

    config["thresholds"]["turn_threshold_degrees"] = new_threshold


def calibrate_walking(config, sock):
    """Guides user through rhythm test to calibrate walking fuel parameters."""

    instruction_message = (
        "--- Calibrating WALKING FUEL SYSTEM ---\n\n"
        "Please remain in your TRAVEL STANCE.\n\n"
        "We will record your natural walking pace for 10 seconds.\n"
        "This will be used to calculate your personalized 'walk fuel' parameters.\n\n"
        "The new system works like a fuel tank:\n"
        "- Each step adds fuel to your walking 'tank'\n"
        "- Being idle slowly drains the fuel\n"
        "- Your character walks as long as there's fuel in the tank"
    )
    show_instructions(instruction_message)
    print("Get ready to walk in place at a comfortable, natural pace.")
    print(f"Listening on {config['network']['listen_ip']}:{config['network']['listen_port']}")
    print("Make sure your Android app is sending data to this address!")
    time.sleep(1)
    print("GO!")

    step_timestamps = []
    last_step_time = 0  # Track last step for minimal debouncing
    minimal_debounce = 0.05  # Even smaller debounce (50ms) to capture more steps
    end_time = time.time() + 10.0

    # Debug counters
    total_packets = 0
    step_packets = 0
    other_sensors = {}

    while time.time() < end_time:
        remaining = end_time - time.time()
        print(f"\r  > Recording... {remaining:.1f}s remaining. Steps: {len(step_timestamps)}", end="", flush=True)
        try:
            data, _ = sock.recvfrom(2048)
            parsed_json = json.loads(data.decode())
            sensor_type = parsed_json.get("sensor")
            total_packets += 1

            # Count all sensor types for debugging
            if sensor_type in other_sensors:
                other_sensors[sensor_type] += 1
            else:
                other_sensors[sensor_type] = 1

            if sensor_type == "step_detector":
                step_packets += 1
                now = time.time()
                # Use minimal debouncing to avoid sensor noise but capture natural rhythm
                if now - last_step_time > minimal_debounce:
                    step_timestamps.append(now)
                    last_step_time = now
                    print(f"\n  > Step {len(step_timestamps)} detected! (Total step packets: {step_packets})")
                else:
                    print(f"\n  > Step packet received but debounced ({now - last_step_time:.3f}s since last)")
        except (BlockingIOError, json.JSONDecodeError, KeyError):
            pass

    print("\n  > Recording complete!")
    print(f"  > Debug info: Received {total_packets} total packets")
    print(f"  > Sensor types received: {other_sensors}")
    print(f"  > Step detector packets: {step_packets}")

    if len(step_timestamps) < 3:
        print("Not enough steps detected to calibrate. Please try again.")
        return

    # Calculate intervals between steps
    intervals = [
        step_timestamps[i] - step_timestamps[i - 1]
        for i in range(1, len(step_timestamps))
    ]

    avg_interval = statistics.mean(intervals)

    # NEW FUEL MODEL CALCULATIONS:
    # Each step gives you fuel for longer than your natural step interval
    # This creates a comfortable buffer for natural rhythm variations
    fuel_added_per_step = avg_interval * 2.0  # Each step gives 2x your natural interval

    # Maximum fuel capacity prevents infinite accumulation but allows for bursts
    max_fuel_capacity = avg_interval * 3.0  # Tank can hold 3x your natural interval

    # Alternative: if you want to be more conservative, use smaller multipliers:
    # fuel_added_per_step = avg_interval * 1.5
    # max_fuel_capacity = avg_interval * 2.5

    print("\n--- Walking Fuel Analysis Complete ---")
    print(
        f"Detected {len(step_timestamps)} steps with an average time of "
        f"{avg_interval:.2f}s between steps."
    )
    print(f"\nNew Fuel System Parameters:")
    print(f"  Fuel added per step: {fuel_added_per_step:.2f}s")
    print(f"  Maximum fuel capacity: {max_fuel_capacity:.2f}s")
    print(f"\nThis means:")
    print(f"  - Each step gives you {fuel_added_per_step:.1f}s of walking time")
    print(f"  - You can accumulate up to {max_fuel_capacity:.1f}s of fuel")
    print(f"  - Natural rhythm variations will feel smooth and fluid")

    # Update config with new fuel parameters
    config["thresholds"]["fuel_added_per_step_sec"] = fuel_added_per_step
    config["thresholds"]["max_fuel_sec"] = max_fuel_capacity

    # Show comparison with old system if it existed
    try:
        if "step_debounce_sec" in config["thresholds"]:
            prev_debounce = config["thresholds"]["step_debounce_sec"]
            prev_timeout = config["thresholds"]["walk_timeout_sec"]
            print(f"\nReplaced old system:")
            print(f"  Old Debounce: {prev_debounce:.2f}s -> New Fuel System (no hard debounce)")
            print(f"  Old Timeout:  {prev_timeout:.2f}s -> New Fuel System (gradual depletion)")
    except KeyError:
        pass


def main():
    """Main function to run the calibrator wizard."""
    config = load_config()

    # Set up the socket once for all calibrations
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind((config["network"]["listen_ip"], config["network"]["listen_port"]))
        sock.setblocking(False)
    except OSError:
        print("\n" + "="*60)
        print("ERROR: Could not bind to the UDP port!")
        print("="*60)
        print(f"Port {config['network']['listen_port']} is likely already in use.")
        print("This usually happens when udp_listener.py is still running.")
        print("\nTo fix this:")
        print("1. Stop udp_listener.py (press Ctrl+C in its terminal)")
        print("2. Then run calibration again")
        print("3. After calibration, restart udp_listener.py")
        print("="*60)
        sock.close()
        return

    print("=" * 50)
    print(" Welcome to the Silksong Controller Calibrator")
    print("=" * 50)
    print("\nThis tool will personalize the controller to your unique movements.")
    print("Please follow the on-screen instructions carefully.")

    # Check for command line arguments
    if len(sys.argv) > 1:
        gesture = sys.argv[1].lower()
        print(f"Calibrating specific gesture: {gesture}")

        if gesture == "punch":
            calibrate_punch(config, sock)
        elif gesture == "jump":
            calibrate_jump(config, sock)
        elif gesture == "turn":
            calibrate_turn(config, sock)
        elif gesture == "walking":
            calibrate_walking(config, sock)
        else:
            print(f"Unknown gesture: {gesture}")
            print("Valid options: punch, jump, turn, walking")
            sock.close()
            return
    else:
        # Run the full suite of calibrations with clear instructions
        calibrate_punch(config, sock)
        calibrate_jump(config, sock)
        calibrate_walking(config, sock)
        calibrate_turn(config, sock)

    sock.close()  # Clean up the socket
    print("\n--- Calibration Complete! ---")
    save_config(config)


if __name__ == "__main__":
    main()
