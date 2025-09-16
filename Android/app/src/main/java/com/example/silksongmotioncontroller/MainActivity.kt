package com.example.silksongmotioncontroller

import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.widget.Button
import android.widget.Toast
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress

class MainActivity : AppCompatActivity() {

    // IMPORTANT: REPLACE THIS WITH YOUR MAC'S ACTUAL IP ADDRESS
    private val MAC_IP_ADDRESS = "192.168.10.234"
    private val UDP_PORT = 12345 // Must match the Python script

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val sendButton: Button = findViewById(R.id.btn_send_packet)

        sendButton.setOnClickListener {
            // The message we want to send
            val message = "Hello, Mac! The UDP bridge is working."

            // Network operations cannot be on the main UI thread.
            // We use a coroutine on the IO dispatcher for background network tasks.
            // [Citation: https://developer.android.com/kotlin/coroutines/coroutines-adv#main-safety]
            lifecycleScope.launch(Dispatchers.IO) {
                sendUdpMessage(message)
            }

            // Show a toast message to the user for immediate feedback
            Toast.makeText(this, "Test packet sent!", Toast.LENGTH_SHORT).show()
        }
    }

    private fun sendUdpMessage(message: String) {
        try {
            // Create a UDP socket
            val socket = DatagramSocket()
            socket.broadcast = false // We are sending to a specific IP

            val messageBytes = message.toByteArray()
            val serverAddress = InetAddress.getByName(MAC_IP_ADDRESS)

            // Create the UDP packet
            val packet = DatagramPacket(messageBytes, messageBytes.size, serverAddress, UDP_PORT)

            // Send the packet
            socket.send(packet)

            // Close the socket
            socket.close()

            // Note: In a real app, you might see logs here for success/failure

        } catch (e: Exception) {
            // Handle exceptions, e.g., print to logcat for debugging
            e.printStackTrace()
        }
    }
}