package com.example.silksongmotioncontroller

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.Toast
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

// Implement the SensorEventListener interface to receive sensor updates
class MainActivity : AppCompatActivity(), SensorEventListener {

    // --- NEW: Sensor-related properties ---
    private lateinit var sensorManager: SensorManager
    private var rotationVectorSensor: Sensor? = null

    // IMPORTANT: REPLACE THIS WITH YOUR MAC'S ACTUAL IP ADDRESS
    private val MAC_IP_ADDRESS = "192.168.10.234"
    private val UDP_PORT = 12345

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val sendButton: Button = findViewById(R.id.btn_send_snapshot)

        // --- NEW: Initialize the SensorManager and the specific sensor ---
        // [Citation: https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview#identifying-sensors]
        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        rotationVectorSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)

        if (rotationVectorSensor == null) {
            Toast.makeText(this, "Rotation Vector Sensor not available!", Toast.LENGTH_LONG).show()
            sendButton.isEnabled = false
        }

        sendButton.setOnClickListener {
            // --- MODIFIED: Register the listener to get a value ---
            // We register the listener here, and it will call onSensorChanged() when it has data.
            // We use SENSOR_DELAY_GAME for high responsiveness.
            // [Citation: https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview#monitoring]
            rotationVectorSensor?.let {
                sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
            }
        }
    }

    // This method is required by SensorEventListener, but we won't use it for now.
    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    // --- NEW: This method is called by the system when the sensor has new data ---
    override fun onSensorChanged(event: SensorEvent?) {
        // We only care about the Rotation Vector sensor events
        if (event?.sensor?.type == Sensor.TYPE_ROTATION_VECTOR) {
            val values = event.values
            // Create a JSON string from the sensor data
            val jsonPayload = """
                {
                    "sensor": "rotation_vector",
                    "values": {
                        "x": ${values[0]},
                        "y": ${values[1]},
                        "z": ${values[2]},
                        "w": ${values.getOrNull(3) ?: 0.0}
                    }
                }
            """.trimIndent()

            // Send the JSON payload
            lifecycleScope.launch(Dispatchers.IO) {
                sendUdpMessage(jsonPayload)
            }

            // --- CRUCIAL: Unregister the listener immediately after sending ---
            // This makes our button a "one-shot" snapshot tool.
            // [Citation: https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview#best-practices]
            sensorManager.unregisterListener(this)

            // Update the UI thread to show confirmation
            runOnUiThread {
                Toast.makeText(this, "Sent Rotation Vector data!", Toast.LENGTH_SHORT).show()
            }
        }
    }

    // No changes to this function needed
    private fun sendUdpMessage(message: String) {
        try {
            val socket = DatagramSocket()
            val messageBytes = message.toByteArray()
            val serverAddress = InetAddress.getByName(MAC_IP_ADDRESS)
            val packet = DatagramPacket(messageBytes, messageBytes.size, serverAddress, UDP_PORT)
            socket.send(packet)
            socket.close()
        } catch (e: Exception) {
            Log.e("UDP_SENDER", "Error sending packet", e)
        }
    }

    // It's good practice to unregister listeners when the app is paused.
    override fun onPause() {
        super.onPause()
        sensorManager.unregisterListener(this)
    }
}