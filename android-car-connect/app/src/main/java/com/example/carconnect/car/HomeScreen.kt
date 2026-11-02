package com.example.carconnect.car

import androidx.car.app.CarContext
import androidx.car.app.Screen
import androidx.car.app.model.Action
import androidx.car.app.model.ItemList
import androidx.car.app.model.Metadata
import androidx.car.app.model.Place
import androidx.car.app.model.PlaceListMapTemplate
import androidx.car.app.model.PlaceMarker
import androidx.car.app.model.Row
import androidx.car.app.model.Template
import com.example.carconnect.R

/**
 * Driver-optimized home screen shown on the car display via Android Auto.
 */
class HomeScreen(carContext: CarContext) : Screen(carContext) {

    override fun onGetTemplate(): Template {
        val listBuilder = ItemList.Builder()

        DemoPlaces.all.forEach { place ->
            val row = Row.Builder()
                .setTitle(place.title)
                .addText("${place.distanceKm} km · ${place.address}")
                .setOnClickListener {
                    screenManager.push(PlaceDetailScreen(carContext, place))
                }
                .setMetadata(
                    Metadata.Builder()
                        .setPlace(
                            Place.Builder(place.location)
                                .setMarker(PlaceMarker.Builder().build())
                                .build()
                        )
                        .build()
                )
                .build()
            listBuilder.addItem(row)
        }

        return PlaceListMapTemplate.Builder()
            .setTitle(carContext.getString(R.string.car_home_title))
            .setHeaderAction(Action.APP_ICON)
            .setItemList(listBuilder.build())
            .setCurrentLocationEnabled(true)
            .build()
    }
}
