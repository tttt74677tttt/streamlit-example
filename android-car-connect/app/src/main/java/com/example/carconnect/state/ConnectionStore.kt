package com.example.carconnect.state

enum class ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED
}

/**
 * Simple in-memory connection state for the phone companion demo UI.
 * Real projection state is owned by the Android Auto host on the car display.
 */
object ConnectionStore {
    @Volatile
    var state: ConnectionState = ConnectionState.DISCONNECTED
}
