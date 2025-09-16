import socket
import json
import time
import math
import statistics  # NEW: For calculating mean and standard deviation


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


def main():
    """Main function to run the entire calibrator wizard."""
    config = load_config()

    print("Welcome to the Silksong Controller Calibrator.")

    # Set up the socket once for all calibrations
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((config['network']['listen_ip'],
               config['network']['listen_port']))
    sock.setblocking(False)

    # Run both calibrations sequentially
    calibrate_punch(config, sock)
    calibrate_jump(config, sock)

    sock.close()  # Clean up the socket
    save_config(config)


if __name__ == "__main__":
    main()
