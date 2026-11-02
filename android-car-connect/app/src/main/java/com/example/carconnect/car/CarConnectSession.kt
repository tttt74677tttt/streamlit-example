package com.example.carconnect.car

import android.content.Intent
import androidx.car.app.Screen
import androidx.car.app.Session

class CarConnectSession : Session() {
    override fun onCreateScreen(intent: Intent): Screen {
        return HomeScreen(carContext)
    }
}
