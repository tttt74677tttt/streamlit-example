package com.example.carconnect.ui

import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.example.carconnect.R
import com.example.carconnect.databinding.ActivityMainBinding
import com.example.carconnect.state.ConnectionState
import com.example.carconnect.state.ConnectionStore

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        render(ConnectionStore.state)
        binding.btnSimulateConnect.setOnClickListener { toggleSimulation() }
        binding.btnWiredHelp.setOnClickListener {
            Toast.makeText(
                this,
                "Plug into a USB Android Auto port, unlock the phone, and allow the prompt.",
                Toast.LENGTH_LONG
            ).show()
        }
        binding.btnWirelessHelp.setOnClickListener {
            Toast.makeText(
                this,
                "Pair Bluetooth with the car, then enable Wireless Android Auto in the Android Auto app.",
                Toast.LENGTH_LONG
            ).show()
        }
    }

    private fun toggleSimulation() {
        when (ConnectionStore.state) {
            ConnectionState.DISCONNECTED -> {
                ConnectionStore.state = ConnectionState.CONNECTING
                render(ConnectionState.CONNECTING)
                handler.postDelayed({
                    ConnectionStore.state = ConnectionState.CONNECTED
                    render(ConnectionState.CONNECTED)
                }, 1600)
            }
            ConnectionState.CONNECTING -> Unit
            ConnectionState.CONNECTED -> {
                ConnectionStore.state = ConnectionState.DISCONNECTED
                render(ConnectionState.DISCONNECTED)
            }
        }
    }

    private fun render(state: ConnectionState) {
        val (label, colorRes, buttonLabel) = when (state) {
            ConnectionState.DISCONNECTED -> Triple(
                getString(R.string.status_disconnected),
                R.color.danger,
                getString(R.string.sim_connect)
            )
            ConnectionState.CONNECTING -> Triple(
                getString(R.string.status_connecting),
                R.color.amber,
                getString(R.string.status_connecting)
            )
            ConnectionState.CONNECTED -> Triple(
                getString(R.string.status_connected),
                R.color.signal,
                getString(R.string.sim_disconnect)
            )
        }

        binding.statusText.text = label
        binding.btnSimulateConnect.text = buttonLabel
        binding.btnSimulateConnect.isEnabled = state != ConnectionState.CONNECTING

        val dot = GradientDrawable().apply {
            shape = GradientDrawable.OVAL
            setColor(ContextCompat.getColor(this@MainActivity, colorRes))
        }
        binding.statusDot.background = dot
    }

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }
}
