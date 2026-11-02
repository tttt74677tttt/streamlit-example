package com.example.carconnect.car

import androidx.car.app.CarContext
import androidx.car.app.Screen
import androidx.car.app.model.Action
import androidx.car.app.model.MessageTemplate
import androidx.car.app.model.Template

class MessageScreen(
    carContext: CarContext,
    private val title: String,
    private val body: String
) : Screen(carContext) {

    override fun onGetTemplate(): Template {
        return MessageTemplate.Builder(body)
            .setTitle(title)
            .setHeaderAction(Action.BACK)
            .addAction(
                Action.Builder()
                    .setTitle("OK")
                    .setOnClickListener { screenManager.pop() }
                    .build()
            )
            .build()
    }
}
