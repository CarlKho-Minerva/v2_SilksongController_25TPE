@echo off
REM Silksong Motion Controller - Calibration Launcher (Windows)
REM This script runs the calibration wizard for personalizing your controller

echo Starting Silksong Motion Controller Calibration...
echo Make sure your Android phone is connected to the same Wi-Fi network!
echo.

python ../calibrate.py
pause