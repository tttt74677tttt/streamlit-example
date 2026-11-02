package com.example.carconnect.car

import androidx.car.app.CarContext
import androidx.car.app.Screen
import androidx.car.app.model.Action
import androidx.car.app.model.CarColor
import androidx.car.app.model.MessageTemplate
import androidx.car.app.model.ParkedOnlyOnClickListener
import androidx.car.app.model.Template
import com.example.carconnect.R

class PlaceDetailScreen(
    carContext: CarContext,
    private val place: DemoPlace
) : Screen(carContext) {

    override fun onGetTemplate(): Template {
        val navigate = Action.Builder()
            .setTitle(carContext.getString(R.string.place_navigate))
            .setBackgroundColor(CarColor.GREEN)
            .setOnClickListener {
                screenManager.push(
                    MessageScreen(
                        carContext,
                        carContext.getString(R.string.toast_navigate),
                        "${place.title}\n${place.address}"
                    )
                )
            }
            .build()

        val call = Action.Builder()
            .setTitle(carContext.getString(R.string.place_call))
            .setOnClickListener(
                ParkedOnlyOnClickListener.create {
                    screenManager.push(
                        MessageScreen(
                            carContext,
                            carContext.getString(R.string.toast_call),
                            place.phone
                        )
                    )
                }
            )
            .build()

        return MessageTemplate.Builder("${place.address}\n${place.distanceKm} km away")
            .setTitle(place.title)
            .setHeaderAction(Action.BACK)
            .addAction(navigate)
            .addAction(call)
            .build()
    }
}
