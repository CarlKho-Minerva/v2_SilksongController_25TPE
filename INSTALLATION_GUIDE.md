# Installation Guide for Silksong Motion Controller

## For Distributors/Developers

### Creating a Release Package

1. **Prepare the Python Project**:
   ```bash
   # Clone or update the repository
   git clone https://github.com/CarlKho-Minerva/v2_SilksongController_25TPE.git
   cd v2_SilksongController_25TPE
   
   # Test that all dependencies install correctly
   pip install -r requirements.txt
   python3 -m py_compile udp_listener.py calibrate.py
   ```

2. **Build the Android APK**:
   - Open Android Studio
   - File → Open → Select the `Android/` folder
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
   - Wait for build completion
   - Click "locate" in the notification popup
   - Navigate to `app/build/outputs/apk/debug/`
   - Rename `app-debug.apk` to `SilksongController-v1.0.apk`

3. **Create Distribution Package**:
   ```bash
   # Create a clean distribution folder
   mkdir SilksongController-Distribution
   
   # Copy Python files
   cp udp_listener.py SilksongController-Distribution/
   cp calibrate.py SilksongController-Distribution/
   cp config_template.json SilksongController-Distribution/config.json
   cp requirements.txt SilksongController-Distribution/
   cp run_*.sh SilksongController-Distribution/
   cp run_*.bat SilksongController-Distribution/
   cp README.md SilksongController-Distribution/
   cp LOOM_VIDEO_SCRIPT.md SilksongController-Distribution/
   
   # Copy the built APK
   cp Android/app/build/outputs/apk/debug/app-debug.apk SilksongController-Distribution/SilksongController-v1.0.apk
   
   # Create ZIP file
   zip -r SilksongController-v1.0.zip SilksongController-Distribution/
   ```

4. **Create GitHub Release**:
   - Go to GitHub repository → Releases → "Create a new release"
   - Tag version: `v1.0`
   - Release title: `Silksong Motion Controller v1.0`
   - Description: Brief summary and changelog
   - Attach the ZIP file and APK file
   - Publish release

### Alternative Distribution Methods

**Option A: Simple File Sharing**
- Upload the ZIP file to Google Drive, Dropbox, or file sharing service
- Share the download link

**Option B: GitHub Repository** (Recommended)
- Fork or create public repository
- Upload all source files
- Users download via "Code" → "Download ZIP"
- APK available in Releases section

## For End Users

### Quick Installation (Most Users)

1. **Download the Package**:
   - Go to [Releases](https://github.com/CarlKho-Minerva/v2_SilksongController_25TPE/releases)
   - Download `SilksongController-v1.0.zip`
   - Extract to a folder like `SilksongController`

2. **Install Python Dependencies**:
   ```bash
   cd SilksongController
   pip install -r requirements.txt
   ```

3. **Install Android App**:
   - Download `SilksongController-v1.0.apk` from Releases
   - Enable "Unknown Sources" on Android
   - Install the APK
   - Disable "Unknown Sources" when done

4. **Follow the README**:
   - Read the complete setup guide in `README.md`
   - Run calibration first: `./run_calibration.sh` (or `.bat` on Windows)
   - Then run controller: `./run_controller.sh` (or `.bat` on Windows)

### From Source (Developers)

```bash
# Clone repository
git clone https://github.com/CarlKho-Minerva/v2_SilksongController_25TPE.git
cd v2_SilksongController_25TPE

# Install Python dependencies
pip install -r requirements.txt

# Build Android app (requires Android Studio)
cd Android
# Open in Android Studio and build APK

# Run directly
python3 calibrate.py    # First time setup
python3 udp_listener.py # Main controller
```

## Updating the Project

### For Users
1. Download the new release ZIP
2. Backup your `config.json` file (contains your calibration)
3. Extract new files, overwriting old ones
4. Restore your `config.json` file
5. Install any new dependencies: `pip install -r requirements.txt`

### For Developers
```bash
git pull origin main
pip install -r requirements.txt  # In case of new dependencies
# Rebuild Android APK if needed
```

## Platform-Specific Notes

### Windows
- May need to install `windows-curses`: `pip install windows-curses`
- Use `.bat` launcher scripts
- May need to allow Python through Windows Firewall

### macOS
- Use `.sh` launcher scripts
- Homebrew users: `brew install python3`
- May need to allow network access in Security preferences

### Linux
- Use `.sh` launcher scripts
- Install Python 3.7+: `sudo apt install python3 python3-pip`
- May need to install additional packages for X11 keyboard control

## Troubleshooting Distribution Issues

### "Python not found"
- Install Python from [python.org](https://python.org)
- Make sure Python is in system PATH
- Try `python` instead of `python3` on Windows

### "Permission denied" on launcher scripts
```bash
chmod +x run_calibration.sh run_controller.sh
```

### APK won't install
- Enable "Install unknown apps" for your file manager
- Try installing via ADB: `adb install SilksongController-v1.0.apk`
- Check Android version compatibility (API 21+)

### Missing dependencies
```bash
# Force reinstall all dependencies
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```