# Silksong Motion Controller

Turn your Android phone into a wireless motion controller for Hollow Knight, Silksong, or any 2D platformer game! Use natural body movements like walking, jumping, and punching to control your character.

<div>
    <a href="https://www.loom.com/share/727b750b191f4f1abde98fd024e2e8de">
      <p>Silksong Demo - Body Controller (Android → UDP → Pynput) - Watch Video</p>
    </a>
    <a href="https://www.loom.com/share/727b750b191f4f1abde98fd024e2e8de">
      <img style="max-width:300px;" src="https://cdn.loom.com/sessions/thumbnails/727b750b191f4f1abde98fd024e2e8de-87d14dbf256e2fd6-full-play.gif">
    </a>
  </div>

## 🎮 What is this?

The Silksong Motion Controller transforms your Android phone's built-in sensors into game controls. Walk in place to move your character, jump to make them jump, punch to attack, and turn your body to change direction. It's like playing the game with your whole body!

**Key Features:**

- 🚶‍♂️ **Walk in place** → Character moves left/right
- 🦘 **Jump up** → Character jumps
- 👊 **Punch forward** → Character attacks
- 🔄 **Turn your body** → Change character direction
- 📱 **Wireless** → No cables needed, just Wi-Fi
- ⚙️ **Personalized** → Calibrates to your unique movements

## 🎥 Demo Videos

1. [Tilt UDP](https://www.loom.com/share/4a5a69b3820846b7800a381407183ba5)
2. [Walk Multithread](https://www.loom.com/share/52ec8495dde74669bcdd9998db55e3fc)
3. [Punch, Walk, and Jump like Toph Beifong](https://www.loom.com/share/24bf5e5834ae4b818021e7375de44549)
4. [IT WORKS](https://www.loom.com/share/4d72524a71874e30b9bc01b4dfbae1dd?sid=755d846f-a462-442d-81bf-3a65b9538e5a)

## ✅ What You Need

Before starting, make sure you have:

- [ ] **A computer** (Windows, Mac, or Linux) with Python 3.7+
- [ ] **An Android phone** (with sensors: accelerometer, gyroscope, step detector)
- [ ] **Wi-Fi network** (both devices on the same network)
- [ ] **A game to play** (Hollow Knight, or any game that uses arrow keys + Z/X)

## 🚀 Quick Start Guide

### Step 1: Computer Setup

1. **Install Python** (if not already installed):
   - **Windows/Mac**: Download from [python.org](https://www.python.org/downloads/)
   - **Linux**: Use your package manager (e.g., `sudo apt install python3 python3-pip`)

2. **Download this project**:
   - Click the green "Code" button → "Download ZIP"
   - Extract the ZIP file to a folder like `SilksongController`

3. **Open a terminal/command prompt** in the project folder:
   - **Windows**: Right-click in the folder → "Open in Terminal" (or Command Prompt)
   - **Mac**: Right-click in the folder → "Services" → "New Terminal at Folder"
   - **Linux**: Right-click in the folder → "Open in Terminal"

4. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   **Windows users**: If you get errors, try:

   ```bash
   pip install pynput windows-curses
   ```

### Step 2: Phone Setup

1. **Download the Android app**:
   - Go to the [Releases](../../releases) section
   - Download the latest `SilksongController-v1.0.apk` file

2. **Enable app installation**:
   - Go to Settings → Security → "Install unknown apps"
   - Find your file manager or browser
   - Enable "Allow from this source"
   - ⚠️ **Security Note**: Only enable this temporarily, and disable it after installation

3. **Install the app**:
   - Open the downloaded APK file
   - Tap "Install" → "Done"

### Step 3: Network Setup

**IMPORTANT**: Both your computer and phone must be on the same Wi-Fi network.

1. **Find your computer's IP address**:

   **Windows**:

   ```cmd
   ipconfig
   ```

   Look for "IPv4 Address" under your Wi-Fi adapter (e.g., `192.168.1.100`)

   **Mac**:

   ```bash
   ifconfig
   ```

   Look for "inet" under your Wi-Fi interface (e.g., `192.168.1.100`)

   **Linux**:

   ```bash
   ip addr show
   ```

   Look for your wireless interface's inet address

2. **Update the configuration**:
   - Open `config.json` in a text editor
   - Replace `"listen_ip": "0.0.0.0"` with your computer's IP address
   - Example: `"listen_ip": "192.168.1.100"`
   - Save the file

3. **Configure the Android app**:
   - Open the Silksong Controller app
   - Enter your computer's IP address (e.g., `192.168.1.100`)
   - The port should be `12345` (default)

### Step 4: Calibration (MANDATORY)

The controller needs to learn your unique movements. This step is essential!

**Easy way** (double-click the file):

- **Windows**: Double-click `run_calibration.bat`
- **Mac/Linux**: Double-click `run_calibration.sh`

**Command line way**:

```bash
python3 calibrate.py
```

Follow the on-screen instructions to calibrate:

1. **Punch calibration**: Hold phone like a sword, do 3 forward punches
2. **Jump calibration**: Hold phone naturally, do 3 upward hops
3. **Walking calibration**: Walk in place for 10 seconds
4. **Turn calibration**: Turn your body left and right

### Step 5: Playing the Game

1. **Start your game** (Hollow Knight, etc.) and make sure it's focused
2. **Start the controller**:
   - **Easy way**: Double-click `run_controller.bat` (Windows) or `run_controller.sh` (Mac/Linux)
   - **Command line**: `python3 udp_listener.py`
3. **Start streaming on your phone**: Open the app and flip the switch to "ON"
4. **Start moving!** The dashboard will show your movements in real-time

## 🎮 How to Play

Hold your phone naturally (like a TV remote) and:

- **Walk in place** → Character moves in the direction you're facing
- **Quick upward hop** → Character jumps (Z key)
- **Forward punch motion** → Character attacks (X key)
- **Turn your body left/right** → Changes character direction
- **Stop walking** → Character stops (after a short momentum delay)

## 🔧 Troubleshooting

### "Connection failed" / "No data received"

**Check your network**:

- Both devices on same Wi-Fi? (Not mobile data!)
- Correct IP address in `config.json`?
- Firewall blocking port 12345?

**Windows Firewall Fix**:

1. Windows Security → Firewall & network protection
2. "Allow an app through firewall"
3. Add Python.exe with both Private and Public checked

### "ModuleNotFoundError: No module named 'pynput'"

**Run the install command**:

```bash
pip install -r requirements.txt
```

**Windows users try**:

```bash
pip install pynput windows-curses
```

### "Permission denied" or "Could not bind to port"

**Port already in use**:

- Close any running `udp_listener.py` or `calibrate.py`
- Change port in `config.json` to something else (e.g., 12346)
- Update the Android app with the new port

### Controller feels unresponsive

**Re-run calibration**:

```bash
python3 calibrate.py
```

**Adjust sensitivity**:

- Edit `config.json` → lower the threshold values
- `punch_threshold_xy_accel`: Lower = more sensitive punches
- `jump_threshold_z_accel`: Lower = easier jumping

### Android app won't install

**Enable unknown sources**:

1. Settings → Apps → Menu → Special access
2. "Install unknown apps" → Your file manager → Allow

**Alternative method**:

1. Settings → Security → "Unknown sources" → Enable
2. Install the APK
3. **Important**: Disable "Unknown sources" afterward

## 🛠️ Building from Source

### Android App

1. **Install Android Studio** from [developer.android.com](https://developer.android.com/studio)
2. **Open the project**: File → Open → Select the `Android` folder
3. **Build APK**: Build menu → Build Bundle(s) / APK(s) → Build APK(s)
4. **Find the APK**: Click "locate" in the build notification

### Python Scripts

The Python scripts run directly - no building required! Just make sure dependencies are installed:

```bash
pip install -r requirements.txt
```

## 📁 Project Structure

```
SilksongController/
├── udp_listener.py          # Main controller script
├── calibrate.py             # Calibration wizard
├── config.json              # Your personal settings
├── config_template.json     # Default settings template
├── requirements.txt         # Python dependencies
├── run_controller.sh/.bat   # Easy launcher scripts
├── run_calibration.sh/.bat  # Easy calibration scripts
├── README.md                # This file
└── Android/                 # Android app source code
    ├── app/src/main/...     # Kotlin source files
    └── ...                  # Android Studio project files
```

## ⚙️ Advanced Configuration

Edit `config.json` to customize:

**Network Settings**:

- `listen_ip`: Your computer's IP address
- `listen_port`: Network port (default 12345)

**Sensitivity Settings** (lower = more sensitive):

- `punch_threshold_xy_accel`: Punch detection sensitivity
- `jump_threshold_z_accel`: Jump detection sensitivity
- `turn_threshold_degrees`: Body turn sensitivity

**Game Controls**:

- `left`/`right`: Movement keys (default: arrow keys)
- `jump`: Jump key (default: "z")
- `attack`: Attack key (default: "x")

**Walking Settings**:

- `fuel_added_per_step_sec`: How much movement each step provides
- `max_fuel_sec`: Maximum movement duration per step

## 🤝 Contributing

Want to improve the controller? Here's how:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b my-feature`
3. **Make your changes** and test them
4. **Submit a pull request**

**Ideas for contributions**:

- Support for more games
- Additional gesture recognition
- iOS app version
- GUI configuration tool
- New movement patterns

## 📄 License

This project is open source. Feel free to use, modify, and share!

## 🆘 Getting Help

**Having issues?**

1. Check the [Troubleshooting](#-troubleshooting) section above
2. Open an [Issue](../../issues) with details about your problem
3. Include your operating system, Python version, and error messages

**Questions about the technical details?**

- Check out the [demo videos](#-demo-videos) for a technical walkthrough
- Read through the source code - it's well-commented!

---

**Ready to play? Start with [Step 1: Computer Setup](#step-1-computer-setup)!** 🎮
