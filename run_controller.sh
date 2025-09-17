#!/bin/bash
# Silksong Motion Controller - Main Controller Launcher
# This script runs the motion controller that listens for phone sensor data

echo "Starting Silksong Motion Controller..."
echo "Make sure you have:"
echo "1. Completed calibration (run ./run_calibration.sh first)"
echo "2. Your game is running and focused"
echo "3. Your Android phone app is ready to stream"
echo ""
echo "Press Ctrl+C to stop the controller"
echo ""

python3 udp_listener.py