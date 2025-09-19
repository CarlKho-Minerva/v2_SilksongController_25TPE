# Silksong Motion Controller - Technical Loom Video Script

## Pre-Recording Preparation Checklist

### 🖥️ Mac Setup - Have These Windows Open:

1. **Android Studio**:
   - Open the `Android/` project folder
   - Have `MainActivity.kt` file open and visible (main tab)
   - Have `activity_main.xml` layout file open in another tab
   - Have `AndroidManifest.xml` file open in another tab
   - Make sure the project builds successfully

2. **VS Code (or preferred text editor)**:
   - Open the main project folder (`v2_SilksongController_25TPE`)
   - Have `udp_listener.py` open and visible (main tab) - this will be the primary focus
   - Have `calibrate.py` open in another tab
   - Have `config.json` open in another tab
   - Have the new `README.md` open in another tab

3. **Terminal Window**:
   - Navigate to the project directory
   - Test that `python3 udp_listener.py` and `python3 calibrate.py` work
   - Have it ready to demonstrate the scripts running

4. **Text Editor/Target Window**:
   - Open TextEdit (Mac) or any simple text editor
   - Have it ready as the "target" for keyboard input demonstration
   - This will clearly show the controller sending keystrokes

5. **Android Phone**:
   - Install the Silksong Controller app
   - Have it open on the main screen
   - Ideally set up screen mirroring (QuickTime Player → New Movie Recording → select iPhone)
   - If no mirroring, be ready to show the phone to camera

6. **Optional - Simple Diagram**:
   - Have a simple drawing or diagram ready showing the data flow:
     ```
     Android Phone → Wi-Fi → Python Script → Keyboard Input → Game
     ```

### 📱 Phone Preparation:
- Charge the phone
- Connect to same Wi-Fi as Mac
- Have the app installed and working
- Test that it can connect to the Python script

---

## 🎬 Loom Video Script

**(Total estimated time: 15-20 minutes)**

---

### **Part 1: Introduction & Project Overview (2-3 minutes)**

**SCRIPT:**
"Hi everyone! Welcome to a complete technical deep dive into the Silksong Motion Controller project. I'm going to walk you through a real-world example of turning an Android phone into a wireless game controller using sensor data and network programming."

"This project demonstrates several key programming concepts: Android sensor APIs, UDP networking, real-time data processing, gesture recognition, and cross-platform communication. By the end of this video, you'll understand exactly how each component works and how they communicate with each other."

**ON-SCREEN:**
- Start with your face/introduction
- Show the high-level architecture (gesture between phone and computer)
- Briefly show the project folder structure in VS Code

**SCRIPT (continued):**
"The architecture is elegantly simple: The Android phone captures sensor data and streams it over Wi-Fi using UDP packets. The Python script receives this data, interprets it as game actions using mathematical transformations, and simulates keyboard input. Let's dive into each component."

---

### **Part 2: Android App Deep Dive (4-5 minutes)**

**SCRIPT:**
"Let's start with the Android application. This is built in Kotlin using Android Studio, and its primary job is sensor data acquisition and network transmission."

**ON-SCREEN:**
- Switch to Android Studio showing `MainActivity.kt`

**SCRIPT:**
"The heart of the app is the MainActivity class, which implements the SensorEventListener interface. This is the standard Android API for receiving sensor data in real-time."

**ON-SCREEN:**
- Scroll to the top of MainActivity.kt, highlight the class declaration and SensorEventListener

**SCRIPT:**
"In our onCreate method, we initialize references to four specific sensors that give us everything we need for motion control."

**ON-SCREEN:**
- Show the onCreate method, highlight each sensor initialization:
  - `sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)`
  - `sensorManager.getDefaultSensor(Sensor.TYPE_LINEAR_ACCELERATION)`
  - `sensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE)`
  - `sensorManager.getDefaultSensor(Sensor.TYPE_STEP_DETECTOR)`

**SCRIPT:**
"The Rotation Vector gives us the phone's orientation in 3D space, Linear Acceleration detects quick movements like jumps and punches, the Gyroscope provides precise rotation data, and Step Detector identifies walking patterns."

**SCRIPT:**
"When the user activates streaming, two critical things happen in our startStreaming function."

**ON-SCREEN:**
- Show the `startStreaming()` function
- Highlight `sensorManager.registerListener()` calls
- Highlight `window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)`

**SCRIPT:**
"First, we register our listener with each sensor, telling Android to start sending us data. Second, we add the KEEP_SCREEN_ON flag - this is crucial because if the phone sleeps during gameplay, we lose the connection."

**SCRIPT:**
"The real magic happens in onSensorChanged. This function is called by the Android OS every time any sensor has new data."

**ON-SCREEN:**
- Show the `onSensorChanged()` function
- Highlight the `when` statement that checks `event?.sensor?.type`

**SCRIPT:**
"We use a when statement to determine which sensor sent the data, then create a JSON payload with the sensor type, timestamp, and values. Here's a key architectural decision: all network operations are wrapped in a coroutine launched on the IO dispatcher."

**ON-SCREEN:**
- Highlight the `lifecycleScope.launch(Dispatchers.IO)` block
- Show the `sendData()` function call

**SCRIPT:**
"This ensures our main UI thread never blocks on network operations. The data is sent as UDP packets, which are fast and perfect for real-time gaming where occasional packet loss is acceptable."

---

### **Part 3: Python Controller - Core Logic (5-7 minutes)**

**SCRIPT:**
"Now let's examine the Python side - this is where the real intelligence lives. The controller script handles networking, state management, mathematical transformations, and keyboard simulation."

**ON-SCREEN:**
- Switch to VS Code showing `udp_listener.py`
- Show the imports at the top

**SCRIPT:**
"We're using several key libraries: socket for UDP networking, json for parsing the Android data, threading for simultaneous operations, and pynput for keyboard control. The curses library gives us that real-time dashboard you see when running the script."

**ON-SCREEN:**
- Show the main configuration loading section
- Show the `load_config()` function and the extracted variables

**SCRIPT:**
"One of the most important design patterns here is external configuration. All our tuning parameters - thresholds, network settings, and key mappings - are loaded from the config.json file. This means users can customize the controller without touching any code."

**ON-SCREEN:**
- Switch to `config.json` tab briefly to show the structure
- Return to `udp_listener.py`

**SCRIPT:**
"Let's look at a concrete example: the walking system. This demonstrates several advanced programming concepts working together."

**ON-SCREEN:**
- Find and highlight the `walk_fuel_seconds` variable
- Show the main loop where fuel is depleted
- Show the `elif sensor_type == 'step_detector'` block where fuel is added

**SCRIPT:**
"We implement what I call a 'fuel system.' There's a global variable tracking walk fuel in seconds. In every cycle of our main loop, we deplete a small amount of this fuel. When a step detector packet arrives from the phone, we add fuel to the tank. The walking thread only runs when there's fuel available."

**ON-SCREEN:**
- Show the `walker_thread_func()` function
- Highlight the simple `if walk_fuel_seconds > 0` logic that starts/stops the thread

**SCRIPT:**
"This creates natural, momentum-based movement that feels intuitive. You build up momentum by stepping, and it naturally decays when you stop."

**SCRIPT:**
"But the most technically sophisticated part is the gesture recognition system. Let me show you how we handle coordinate transformations."

**ON-SCREEN:**
- Find the `elif sensor_type == 'linear_acceleration'` block
- Show the call to `rotate_vector_by_quaternion()`

**SCRIPT:**
"When linear acceleration data arrives from the phone, we don't use the raw values directly. Instead, we use the most recent rotation data to transform the phone's local coordinate system into the world coordinate system."

**ON-SCREEN:**
- Show the `rotate_vector_by_quaternion()` function implementation

**SCRIPT:**
"This mathematical transformation is crucial. It means a 'jump' is always detected as upward acceleration in world coordinates, regardless of how the user is holding their phone. A punch is always horizontal movement in world space. This makes gesture detection incredibly robust."

**ON-SCREEN:**
- Show the jump detection: `if world_z > JUMP_THRESHOLD`
- Show the punch detection: `if world_xy_magnitude > PUNCH_THRESHOLD`

**SCRIPT:**
"After the coordinate transformation, gesture detection becomes simple threshold comparisons on the world-space acceleration values."

---

### **Part 4: Calibration System (3-4 minutes)**

**SCRIPT:**
"None of this would work reliably without personalization, which is handled by our calibration system."

**ON-SCREEN:**
- Switch to `calibrate.py` tab

**SCRIPT:**
"The calibration script is essentially a wizard that guides users through performing each gesture while we record and analyze their unique movement patterns."

**ON-SCREEN:**
- Show the `calibrate_punch()` function
- Highlight the instruction display and user prompts

**SCRIPT:**
"Let's trace through punch calibration as an example. First, we give explicit instructions about stance and phone holding. Then we open a time-based recording window."

**ON-SCREEN:**
- Show the time-based while loop in the calibration function
- Show the data collection and peak finding logic

**SCRIPT:**
"During the recording window, we capture all incoming acceleration data and find the maximum values the user generates. We repeat this for multiple samples, then use basic statistics - mean and standard deviation - to calculate a personalized threshold."

**ON-SCREEN:**
- Show the `statistics.mean()` calculation
- Show where the new threshold is saved back to the config file

**SCRIPT:**
"This same pattern - prompt, record, analyze, save - is used for every gesture type. The result is a controller perfectly tuned to each individual user's movement style and strength."

---

### **Part 5: Live Demonstration (3-4 minutes)**

**SCRIPT:**
"Let's see everything working together in real-time."

**ON-SCREEN:**
- Switch to Terminal
- Run `python3 udp_listener.py`
- Show the curses dashboard appearing

**SCRIPT:**
"When we start the controller, you can see the real-time dashboard showing all the system state. Now I'll activate the phone app."

**ON-SCREEN:**
- Show your phone (either via screen mirroring or hold it up to camera)
- Flip the streaming switch to ON
- Switch back to the computer to show the dashboard updating

**SCRIPT:**
"Perfect! Now we have live data flowing. Let me bring up a text editor as our target application so you can see the actual keyboard input being generated."

**ON-SCREEN:**
- Bring TextEdit or similar to the foreground
- Make sure it's focused and ready to receive keyboard input

**SCRIPT:**
"Watch the dashboard and the text editor as I perform different gestures. First, let me take a step..."

**ON-SCREEN:**
- Take a clear step
- Show the dashboard reflecting: walk fuel increasing, walk status changing
- Show the right arrow key being pressed in the text editor (cursor moving right)

**SCRIPT:**
"You can see the walk fuel filled up, the status changed to 'WALKING', and the right arrow key is being pressed continuously. When I stop stepping, watch the fuel deplete..."

**ON-SCREEN:**
- Stop stepping
- Show the fuel bar decreasing
- Show the key release when fuel hits zero

**SCRIPT:**
"Perfect! Now let me demonstrate direction changes. I'll turn my body to face left..."

**ON-SCREEN:**
- Perform a clear body turn
- Show the 'Facing' indicator change from RIGHT to LEFT
- Take another step
- Show the left arrow key being pressed instead

**SCRIPT:**
"Excellent! The system detected the direction change, and now my steps generate left movement instead of right."

**SCRIPT:**
"Let me show you the other gestures. Here's a jump..."

**ON-SCREEN:**
- Perform a clear upward hop
- Show the dashboard showing the Z-axis acceleration spike
- Show 'z' appearing in the text editor

**SCRIPT:**
"And here's a punch attack..."

**ON-SCREEN:**
- Perform a clear forward punch
- Show the XY acceleration spike on the dashboard
- Show 'x' appearing in the text editor

**SCRIPT:**
"Perfect! All gestures are being detected and translated into the correct keyboard inputs in real-time."

---

### **Part 6: Technical Architecture Summary & Conclusion (2-3 minutes)**

**SCRIPT:**
"So that's the complete technical architecture of the Silksong Motion Controller. Let me summarize the key engineering principles that make this work."

**ON-SCREEN:**
- Switch back to VS Code showing the project structure

**SCRIPT:**
"First, separation of concerns: the Android app only handles data acquisition, the Python script only handles processing and control, and calibration is a completely separate tool. This makes the system modular and maintainable."

"Second, external configuration: all tuning parameters live in JSON files, not code. This makes the system highly customizable without requiring programming knowledge."

"Third, mathematical robustness: by using quaternion-based coordinate transformations, the gesture recognition works regardless of phone orientation. This is what makes the controller feel natural to use."

"Fourth, real-time performance: UDP networking, non-blocking I/O, and efficient threading ensure minimal latency between movement and response."

**ON-SCREEN:**
- Show the README.md file briefly

**SCRIPT:**
"And finally, user experience: comprehensive documentation, easy-to-use launcher scripts, and detailed troubleshooting guides make this accessible to non-technical users."

**SCRIPT:**
"The complete source code, installation instructions, and pre-built Android APK are all available in the GitHub repository. Whether you're interested in motion control, sensor programming, networking, or just want to play games with your body, this project demonstrates real-world applications of all these technologies working together."

**SCRIPT:**
"Thanks for watching! Feel free to clone the repo, try it out, and let me know what you build with it."

**ON-SCREEN:**
- Show your face for closing
- Maybe show the GitHub repository page briefly

---

**(End Recording)**

---

## 📋 Post-Recording Checklist

After recording:

1. **Review the video** for any technical errors or unclear explanations
2. **Add timestamps** in the video description for easy navigation
3. **Include links** in the description:
   - GitHub repository
   - Python download link
   - Android Studio download link
4. **Test all demonstrated features** to ensure they work as shown
5. **Upload any additional resources** mentioned in the video

## 🎯 Key Technical Points Covered

- ✅ Android SensorEventListener API
- ✅ UDP networking and real-time data streaming
- ✅ Quaternion mathematics and coordinate transformations
- ✅ Multi-threading for concurrent operations
- ✅ Configuration-driven architecture
- ✅ Statistical analysis for personalization
- ✅ Cross-platform keyboard simulation
- ✅ Real-time dashboard development with curses
- ✅ JSON data serialization
- ✅ Error handling and user experience design