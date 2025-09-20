"""
Network utilities for automatic IP address detection and configuration management.
"""

import socket
import json
import sys


def get_local_ip():
    """
    Automatically detect the local IP address that would be used for UDP communication.
    Returns the IP address as a string.
    """
    try:
        # Create a dummy socket to find the local IP that would be used
        # to reach a remote address (doesn't actually connect)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Use a dummy IP that doesn't need to be reachable
            # This technique gets the IP of the interface that would be used
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception as e:
        print(f"Warning: Could not auto-detect IP address: {e}")
        print("Falling back to localhost")
        return "127.0.0.1"


def update_config_ip(config_file="config.json", auto_detect=True, manual_ip=None):
    """
    Update the IP address in the config file.

    Args:
        config_file (str): Path to the config.json file
        auto_detect (bool): If True, automatically detect local IP
        manual_ip (str): If provided and auto_detect is False, use this IP

    Returns:
        str: The IP address that was set
    """
    try:
        # Load existing config
        with open(config_file, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"Error: {config_file} not found!")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {config_file}: {e}")
        return None

    # Determine which IP to use
    if auto_detect:
        new_ip = get_local_ip()
        print(f"Auto-detected IP address: {new_ip}")
    elif manual_ip:
        new_ip = manual_ip
        print(f"Using manual IP address: {new_ip}")
    else:
        print("Error: No IP address provided")
        return None

    # Update the config
    old_ip = config.get("network", {}).get("listen_ip", "unknown")
    config["network"]["listen_ip"] = new_ip

    # Save the updated config
    try:
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)

        print(f"✓ Updated {config_file}")
        print(f"  Old IP: {old_ip}")
        print(f"  New IP: {new_ip}")

        return new_ip

    except Exception as e:
        print(f"Error saving config: {e}")
        return None


def verify_ip_accessible(ip, port=12345):
    """
    Verify that we can bind to the specified IP and port.

    Args:
        ip (str): IP address to test
        port (int): Port number to test

    Returns:
        bool: True if IP/port is accessible, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((ip, port))
            return True
    except Exception as e:
        print(f"Warning: Cannot bind to {ip}:{port} - {e}")
        return False


def main():
    """
    Command-line interface for network utilities.
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "--detect":
            ip = get_local_ip()
            print(f"Detected IP: {ip}")
        elif sys.argv[1] == "--update":
            update_config_ip()
        elif sys.argv[1] == "--set" and len(sys.argv) > 2:
            manual_ip = sys.argv[2]
            update_config_ip(auto_detect=False, manual_ip=manual_ip)
        else:
            print("Usage:")
            print("  python network_utils.py --detect     # Show detected IP")
            print("  python network_utils.py --update     # Auto-update config.json")
            print("  python network_utils.py --set <IP>   # Set specific IP in config.json")
    else:
        # Default behavior: auto-update
        update_config_ip()


if __name__ == "__main__":
    main()