package com.example.silksongmotioncontroller

import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.util.Log
import android.widget.Switch
import android.widget.Toast
import androidx.appcompat.widget.SwitchCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

class MainActivity : AppCompatActivity(), SensorEventListener {

    private lateinit var sensorManager: SensorManager
    private var rotationVectorSensor: Sensor? = null

    private val MAC_IP_ADDRESS = "192.168.10.234" // CHANGE THIS
    private val UDP_PORT = 12345

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val streamSwitch: SwitchCompat = findViewById(R.id.switch_stream)

        sensorManager = getSystemService(SENSOR_SERVICE) as SensorManager
        rotationVectorSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ROTATION_VECTOR)

        if (rotationVectorSensor == null) {
            Toast.makeText(this, "Rotation Vector Sensor not available!", Toast.LENGTH_LONG).show()
            streamSwitch.isEnabled = false
        }

        // --- MODIFIED: Logic is now tied to the switch's state change ---
        streamSwitch.setOnCheckedChangeListener { _, isChecked ->
            if (isChecked) {
                // When switch is ON, start listening to the sensor
                startStreaming()
            } else {
                // When switch is OFF, stop listening
                stopStreaming()
            }
        }
    }

    private fun startStreaming() {
        // [Citation: https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview#monitoring]
        rotationVectorSensor?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
            Toast.makeText(this, "Streaming ON", Toast.LENGTH_SHORT).show()
        }
    }

    private fun stopStreaming() {
        // [Citation: https://developer.android.com/develop/sensors-and-location/sensors/sensors_overview#best-practices]
        sensorManager.unregisterListener(this)
        Toast.makeText(this, "Streaming OFF", Toast.LENGTH_SHORT).show()
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) {}

    // --- MODIFIED: This now sends data for EVERY event, without unregistering ---
    override fun onSensorChanged(event: SensorEvent?) {
        if (event?.sensor?.type == Sensor.TYPE_ROTATION_VECTOR) {
            val values = event.values
            val jsonPayload = """
                {
                    "sensor": "rotation_vector",
                    "timestamp_ns": ${event.timestamp},
                    "values": {
                        "x": ${values[0]},
                        "y": ${values[1]},
                        "z": ${values[2]},
                        "w": ${values.getOrNull(3) ?: 0.0}
                    }
                }
            """.trimIndent()

            lifecycleScope.launch(Dispatchers.IO) {
                sendUdpMessage(jsonPayload)
            }
        }
    }

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

    // Ensure we stop streaming if the app is paused
    override fun onPause() {
        super.onPause()
        stopStreaming()
    }
}